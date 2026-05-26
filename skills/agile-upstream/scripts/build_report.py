#!/usr/bin/env python3
"""
build_report.py — Saúde dos ÉPICOS por time no Azure DevOps (REST API + PAT),
classificada por MOVIMENTAÇÃO, para o Product Owner de cada time (AreaPath).

Usa o cliente compartilhado `azdo.client` (../../../shared) para autenticação e
chamadas REST — nenhuma lógica de auth vive aqui.

Status único por épico (faixa mais alta vence), por COR:
  🟢 Saudável       movimentação nos últimos {QUESTIONAVEL} dias
  🟠 Questionável   sem movimentação há mais de {QUESTIONAVEL} dias
  🔴 Agarrado       sem movimentação há mais de {AGARRADO} dias
  🟣 Para descarte  sem movimentação há mais de {DESCARTE} dias

"Movimentação" = dias desde a última mudança de estado
(Microsoft.VSTS.Common.StateChangeDate). A skill separa o FUNIL (backlog cru —
estados em FUNNEL_STATES, default 'Idea', que por natureza não se movem) do
FLUXO (épicos que já entraram na entrega):
  - EM FLUXO: a cor mede a MOVIMENTAÇÃO (dias sem mudança de estado).
  - FUNIL:    a cor mede a IDADE (dias desde a criação) — o Roxo do funil é o
              candidato a limpar do backlog.

Fluxo (2 chamadas REST, sem fan-out):
  1. WIQL  -> IDs de épicos em estados não-finalizados (terminais por categoria)
  2. workitemsbatch (lotes de 200) -> campos de cada épico
  3. Gera PDF (A4 paisagem) e imprime um resumo JSON no stdout

Saída:
  - PDF: <out_dir>/Relatorio_Upstream_<projeto>_<YYYY-MM-DD>.pdf
  - stdout (última linha): JSON
    {"pdf_path","project","date","total","fluxo","funil",
     "saudavel","questionavel","agarrado","descarte","funil_descarte"}
    (as contagens por cor referem-se aos épicos EM FLUXO; funil_descarte =
     épicos de funil em Roxo por idade.)

Variáveis de ambiente (carregue de ~/.config/agile/.env — ver shared/README.md):
  AZDO_PAT          (obrigatório)  Personal Access Token, escopo Work Items (Read)
  AZDO_ORG          (obrigatório)  nome da organização no Azure DevOps
  AZDO_PROJECT      (obrigatório)  nome do projeto no Azure DevOps
  EPIC_WORKITEM_TYPE(opcional)     tipo do "épico" (default 'Epic_')
  REPORT_OUT_DIR    (opcional)     diretório de saída (default: diretório atual)

Uso:
  python3 build_report.py [--out-dir DIR]

  Relatório AVULSO (sob demanda, sem Drive/Chat): rode só este script.
  Rotina AGENDADA (entrega completa): use scripts/run_weekly.sh.
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# Bootstrap: torna o cliente compartilhado importável mesmo sem PYTHONPATH.
# scripts -> agile-upstream -> skills -> <repo>/shared
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from azdo.client import API_VERSION, finalized_states_for, post, require_env  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)

# ─────────────────────── Escala de movimentação ───────────────────────
# Fonte única do comportamento. Faixa mais alta vence. Não são parâmetros de
# runtime (mesma política do report-bugs): ajuste aqui se a cadência mudar.
QUESTIONAVEL = 60   # > 60 dias sem movimentação → Questionável (laranja)
AGARRADO = 90       # > 90 dias → Agarrado (vermelho)
DESCARTE = 180      # > 180 dias → Para descarte (roxo)

STATECHANGE_FIELD = "Microsoft.VSTS.Common.StateChangeDate"

# Tipo de work item que representa "épico" neste processo. O processo do
# projeto-alvo usa o tipo CUSTOMIZADO 'Epic_' (o 'Epic' padrão fica vazio).
EPIC_TYPE = os.environ.get("EPIC_WORKITEM_TYPE", "Epic_")

# Estados de "funil" (backlog cru, ainda não entrou no fluxo de entrega). Um
# épico de funil é colorido pela IDADE (não pela movimentação, que por natureza
# não acontece). Ajuste se quiser incluir Refinement/Validation no funil.
FUNNEL_STATES = ("Idea",)

COR_VERDE = colors.HexColor("#388E3C")
COR_LARANJA = colors.HexColor("#EF6C00")
COR_VERMELHA = colors.HexColor("#D32F2F")
COR_ROXA = colors.HexColor("#6A1B9A")

# (limiar_exclusivo, label, cor, emoji) — avaliado do mais alto para o mais baixo
STATUS_BANDS = [
    (DESCARTE, "Para descarte", COR_ROXA, "🟣"),
    (AGARRADO, "Agarrado", COR_VERMELHA, "🔴"),
    (QUESTIONAVEL, "Questionável", COR_LARANJA, "🟠"),
    (-1, "Saudável", COR_VERDE, "🟢"),
]


def classify(dias: int):
    """Retorna (label, cor, emoji) para um nº de dias, faixa mais alta vencendo."""
    for limiar, label, cor, emoji in STATUS_BANDS:
        if dias > limiar:
            return label, cor, emoji
    return STATUS_BANDS[-1][1:]


def _d10(iso: str) -> str:
    return iso[:10] if iso else ""


def fetch_epics(org: str, project: str, pat: str, finalized: list[str]) -> list[dict]:
    """Épicos em estados não-finalizados, com os campos para a classificação."""
    not_in = ", ".join(f"'{s}'" for s in finalized)
    wiql = (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.TeamProject] = '{project}' "
        f"AND [System.WorkItemType] = '{EPIC_TYPE}' "
        f"AND [System.State] NOT IN ({not_in})"
    )
    wiql_url = (
        f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql"
        f"?api-version={API_VERSION}"
    )
    result = post(wiql_url, {"query": wiql}, pat)
    ids = [w["id"] for w in result.get("workItems", [])]
    if not ids:
        return []

    fields = [
        "System.Id",
        "System.Title",
        "System.State",
        "System.AreaPath",
        "System.AssignedTo",
        "System.CreatedDate",
        STATECHANGE_FIELD,
    ]
    batch_url = (
        f"https://dev.azure.com/{org}/_apis/wit/workitemsbatch"
        f"?api-version={API_VERSION}"
    )
    epics = []
    for i in range(0, len(ids), 200):  # API aceita no máximo 200 ids por chamada
        chunk = ids[i : i + 200]
        resp = post(batch_url, {"ids": chunk, "fields": fields}, pat)
        for wi in resp.get("value", []):
            f = wi["fields"]
            assigned = f.get("System.AssignedTo")
            po = assigned.get("displayName", "—") if isinstance(assigned, dict) else "—"
            epics.append(
                {
                    "id": f.get("System.Id"),
                    "title": f.get("System.Title", "").strip(),
                    "state": f.get("System.State", ""),
                    "area": f.get("System.AreaPath", ""),
                    "po": po,
                    "created": _d10(f.get("System.CreatedDate", "")),
                    "state_change": _d10(f.get(STATECHANGE_FIELD, ""))
                    or _d10(f.get("System.CreatedDate", "")),
                }
            )
    return epics


def area_label(area_path: str) -> str:
    """'Projeto\\Plataforma\\Integracoes' -> 'Plataforma \\ Integracoes'."""
    if not area_path:
        return "(raiz - sem time)"
    parts = [p for p in area_path.split("\\") if p]
    if len(parts) <= 1:
        return "(raiz - sem time)"
    rest = parts[1:]
    return " \\ ".join(rest[-2:]) if len(rest) > 2 else " \\ ".join(rest)


def dias_desde(iso: str, ref: date) -> int:
    if not iso:
        return 0
    y, m, d = map(int, iso.split("-"))
    return (ref - date(y, m, d)).days


def classify_epic(e: dict, ref: date) -> dict:
    """Anota o épico: funil vs fluxo, métrica de dias e status (label/cor)."""
    is_funnel = e["state"] in FUNNEL_STATES
    # Em fluxo: dias sem movimentação. Funil: idade (não há movimentação útil).
    dias = dias_desde(e["created"] if is_funnel else e["state_change"], ref)
    label, cor, emoji = classify(dias)
    e["is_funnel"] = is_funnel
    e["dias"] = dias
    e["status"] = label
    e["cor"] = cor
    e["emoji"] = emoji
    return e


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_") or "Projeto"


# Estilos e helpers de tabela ------------------------------------------------

def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontSize=22, leading=26, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=14, leading=18,
                              spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#0B3D91")),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=12, leading=15,
                             spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#0B3D91")),
        "body": ParagraphStyle("b", parent=base["BodyText"], fontSize=9.5, leading=12),
        "small": ParagraphStyle("s", parent=base["BodyText"], fontSize=8, leading=10,
                                textColor=colors.HexColor("#555555")),
        "cell": ParagraphStyle("c", parent=base["BodyText"], fontSize=8.5, leading=11),
        "status": ParagraphStyle("st", parent=base["BodyText"], fontSize=8.5, leading=11,
                                 alignment=TA_CENTER),
        "link": ParagraphStyle("lk", parent=base["BodyText"], fontSize=8.5, leading=11,
                               alignment=TA_CENTER, textColor=colors.HexColor("#0B5FFF")),
    }


def _count_by_status(items: list[dict]) -> dict:
    out = {"Saudável": 0, "Questionável": 0, "Agarrado": 0, "Para descarte": 0}
    for x in items:
        out[x["status"]] += 1
    return out


def _cab_counts(items: list[dict]) -> str:
    """Linha de contagens por status, com cor (para o cabeçalho de cada time)."""
    c = _count_by_status(items)
    return (
        f"<font size=9 color='#555555'>— total: {len(items)}  ·  </font>"
        f"<font size=9 color='#388E3C'>Saudável {c['Saudável']}</font>"
        f"<font size=9 color='#555555'>  ·  </font>"
        f"<font size=9 color='#EF6C00'>Questionável {c['Questionável']}</font>"
        f"<font size=9 color='#555555'>  ·  </font>"
        f"<font size=9 color='#D32F2F'>Agarrado {c['Agarrado']}</font>"
        f"<font size=9 color='#555555'>  ·  </font>"
        f"<font size=9 color='#6A1B9A'>Para descarte {c['Para descarte']}</font>"
    )


def _detail_table(items: list[dict], st: dict, base_url: str, metric_header: str):
    data = [["Status", "ID", "Estado", metric_header, "Resp. (PO)", "Título"]]
    row_cor = []
    for idx, e in enumerate(sorted(items, key=lambda x: -x["dias"]), start=1):
        url = f"{base_url}/{e['id']}"
        cor_hex = f"#{e['cor'].hexval()[2:]}"
        data.append([
            Paragraph(f"<font color='{cor_hex}'><b>{e['status']}</b></font>", st["status"]),
            Paragraph(f'<link href="{url}"><u>{e["id"]}</u></link>', st["link"]),
            e["state"],
            f'{e["dias"]}d',
            Paragraph(e["po"], st["cell"]),
            Paragraph(e["title"], st["cell"]),
        ])
        row_cor.append((idx, e["cor"]))
    t = Table(
        data,
        colWidths=[34 * mm, 16 * mm, 26 * mm, 20 * mm, 43 * mm, 134 * mm],
        repeatRows=1,
    )
    ts = TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (3, -1), "CENTER"),
        ("ALIGN", (4, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#BBBBBB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
    ])
    for idx, cor in row_cor:
        ts.add("LINEBEFORE", (0, idx), (0, idx), 3, cor)
    t.setStyle(ts)
    return t


def _sumario_por_time(times, st, metric_header):
    head = ["Time / AreaPath", "Total", "Saudável", "Questionável",
            "Agarrado", "Para descarte"]
    data = [head]
    tot = {"Saudável": 0, "Questionável": 0, "Agarrado": 0, "Para descarte": 0}
    grand = 0
    for area, items in times:
        c = _count_by_status(items)
        for k in tot:
            tot[k] += c[k]
        grand += len(items)
        data.append([area, str(len(items)), str(c["Saudável"]),
                     str(c["Questionável"]), str(c["Agarrado"]), str(c["Para descarte"])])
    data.append(["TOTAL", str(grand), str(tot["Saudável"]), str(tot["Questionável"]),
                 str(tot["Agarrado"]), str(tot["Para descarte"])])
    t = Table(data, colWidths=[96 * mm, 22 * mm, 30 * mm, 34 * mm, 28 * mm, 34 * mm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9.5),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 10),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EAF6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F5F7FA")]),
        ("TEXTCOLOR", (3, 1), (3, -2), COR_LARANJA),
        ("TEXTCOLOR", (4, 1), (4, -2), COR_VERMELHA),
        ("TEXTCOLOR", (5, 1), (5, -2), COR_ROXA),
        ("FONT", (2, 1), (5, -2), "Helvetica-Bold", 9.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _group_by_team(items):
    por_time = {}
    for e in items:
        por_time.setdefault(area_label(e["area"]), []).append(e)
    # ordena por mais "doente" primeiro (agarrados + descarte), depois alfabético
    return sorted(
        por_time.items(),
        key=lambda kv: (-sum(1 for x in kv[1] if x["status"] in ("Agarrado", "Para descarte")),
                        kv[0]),
    )


def montar_pdf(epics: list[dict], saida: str, ref: date, org: str, project: str,
               finalized: list[str]) -> dict:
    doc = SimpleDocTemplate(
        saida,
        pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Saúde dos Épicos por Time — {project}",
        author=f"{project} - Azure DevOps",
    )
    st = _styles()
    base_url = f"https://dev.azure.com/{org}/{project}/_workitems/edit"

    fluxo = [e for e in epics if not e["is_funnel"]]
    funil = [e for e in epics if e["is_funnel"]]
    cf = _count_by_status(fluxo)
    cu = _count_by_status(funil)
    total = len(epics)

    story = []
    story.append(Paragraph(f"Saúde dos Épicos por Time — {project}", st["title"]))
    story.append(Paragraph(
        f"Data de corte: <b>{ref.strftime('%d/%m/%Y')}</b> &nbsp;·&nbsp; "
        f"Fonte: Azure DevOps (organização {org}, projeto {project})", st["body"]))
    story.append(Paragraph(
        f"Escopo: épicos (tipo {EPIC_TYPE}) em estados não-finalizados "
        f"(exclui {', '.join(finalized)}), agrupados por time (AreaPath).",
        st["small"]))
    story.append(Spacer(1, 8))

    # Legenda da escala
    legenda = Table(
        [["Escala:",
          f"Saudável  (movim. até {QUESTIONAVEL}d)",
          f"Questionável  (> {QUESTIONAVEL}d)",
          f"Agarrado  (> {AGARRADO}d)",
          f"Para descarte  (> {DESCARTE}d)"]],
        colWidths=[18 * mm, 62 * mm, 48 * mm, 48 * mm, 56 * mm],
    )
    legenda.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica-Bold", 9),
        ("BACKGROUND", (1, 0), (1, 0), COR_VERDE),
        ("BACKGROUND", (2, 0), (2, 0), COR_LARANJA),
        ("BACKGROUND", (3, 0), (3, 0), COR_VERMELHA),
        ("BACKGROUND", (4, 0), (4, 0), COR_ROXA),
        ("TEXTCOLOR", (1, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (1, 0), (-1, -1), 0.25, colors.grey),
        ("INNERGRID", (1, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(legenda)
    story.append(Spacer(1, 8))

    # Visão geral
    story.append(Paragraph("Visão geral", st["h2"]))
    resumo = Table(
        [["", "Total", "Saudável", "Questionável", "Agarrado", "Para descarte"],
         ["Em fluxo", str(len(fluxo)), str(cf["Saudável"]), str(cf["Questionável"]),
          str(cf["Agarrado"]), str(cf["Para descarte"])],
         ["Funil (por idade)", str(len(funil)), str(cu["Saudável"]), str(cu["Questionável"]),
          str(cu["Agarrado"]), str(cu["Para descarte"])]],
        colWidths=[44 * mm, 24 * mm, 32 * mm, 36 * mm, 30 * mm, 36 * mm],
    )
    resumo.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 10),
        ("FONT", (1, 1), (-1, -1), "Helvetica-Bold", 13),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (3, 1), (3, -1), COR_LARANJA),
        ("TEXTCOLOR", (4, 1), (4, -1), COR_VERMELHA),
        ("TEXTCOLOR", (5, 1), (5, -1), COR_ROXA),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(resumo)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<b>Como ler:</b> cada épico tem <b>uma cor</b>. <b>Em fluxo</b> a cor "
        f"mede a movimentação (dias desde a última mudança de estado). O "
        f"<b>funil</b> (estados {', '.join(FUNNEL_STATES)}) não se move por "
        f"natureza, então é colorido pela <b>idade</b> — o item "
        f"<font color='#6A1B9A'><b>Para descarte</b></font> do funil é o "
        f"candidato a limpar do backlog.", st["small"]))

    # ── Seção EM FLUXO ──
    story.append(Paragraph("Épicos em fluxo — por time", st["h2"]))
    if fluxo:
        times_fluxo = _group_by_team(fluxo)
        story.append(_sumario_por_time(times_fluxo, st, "Dias s/ movim."))
        story.append(Spacer(1, 8))
        for area, items in times_fluxo:
            header = Paragraph(f"{area} &nbsp;{_cab_counts(items)}", st["h3"])
            t = _detail_table(items, st, base_url, "Dias s/ movim.")
            story.append(KeepTogether([header, t, Spacer(1, 6)]))
    else:
        story.append(Paragraph("Nenhum épico em fluxo.", st["body"]))

    # ── Seção FUNIL ──
    if funil:
        story.append(PageBreak())
        story.append(Paragraph(
            f"Funil ({', '.join(FUNNEL_STATES)}) — por time (cor por idade)", st["h2"]))
        story.append(Paragraph(
            "Backlog cru, ainda não puxado para o fluxo. A cor mede a idade; "
            "os <font color='#6A1B9A'><b>Para descarte</b></font> (mais de 180 "
            "dias) são os candidatos a limpar.", st["small"]))
        story.append(Spacer(1, 6))
        times_funil = _group_by_team(funil)
        story.append(_sumario_por_time(times_funil, st, "Idade"))
        story.append(Spacer(1, 8))
        for area, items in times_funil:
            header = Paragraph(f"{area} &nbsp;{_cab_counts(items)}", st["h3"])
            t = _detail_table(items, st, base_url, "Idade")
            story.append(KeepTogether([header, t, Spacer(1, 6)]))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<i>Critérios:</i> status único por cor, faixa mais alta vence — "
        f"<font color='#388E3C'>Saudável (até {QUESTIONAVEL}d)</font> · "
        f"<font color='#EF6C00'>Questionável (>{QUESTIONAVEL}d)</font> · "
        f"<font color='#D32F2F'>Agarrado (>{AGARRADO}d)</font> · "
        f"<font color='#6A1B9A'>Para descarte (>{DESCARTE}d)</font>. "
        f"Em fluxo conta dias desde {STATECHANGE_FIELD}; no funil "
        f"({', '.join(FUNNEL_STATES)}) conta a idade desde a criação. "
        f"Dias contados até a data de corte.", st["small"]))

    doc.build(story)
    return {
        "total": total,
        "fluxo": len(fluxo),
        "funil": len(funil),
        "saudavel": cf["Saudável"],
        "questionavel": cf["Questionável"],
        "agarrado": cf["Agarrado"],
        "descarte": cf["Para descarte"],
        "funil_descarte": cu["Para descarte"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.environ.get("REPORT_OUT_DIR", "."))
    args = ap.parse_args()

    pat = require_env("AZDO_PAT")
    org = require_env("AZDO_ORG")
    project = require_env("AZDO_PROJECT")

    ref = date.today()
    finalized = finalized_states_for(org, project, EPIC_TYPE, pat)
    epics = fetch_epics(org, project, pat, finalized)
    if not epics:
        raise SystemExit("Nenhum épico ativo retornado pela query — nada a gerar.")

    for e in epics:
        classify_epic(e, ref)

    os.makedirs(args.out_dir, exist_ok=True)
    pdf_path = os.path.join(
        args.out_dir, f"Relatorio_Upstream_{_slug(project)}_{ref.isoformat()}.pdf"
    )
    counts = montar_pdf(epics, pdf_path, ref, org, project, finalized)

    summary = {
        "pdf_path": os.path.abspath(pdf_path),
        "project": project,
        "date": ref.isoformat(),
        **counts,
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
