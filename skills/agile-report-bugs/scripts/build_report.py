#!/usr/bin/env python3
"""
build_report.py — Busca bugs abertos do Azure DevOps (REST API + PAT) e gera
um relatório em PDF agrupado por time (AreaPath), com flag de tempo aberto.

Usa o cliente compartilhado `azdo.client` (../../../shared) para autenticação e
chamadas REST — nenhuma lógica de auth vive aqui.

Fluxo:
  1. WIQL  -> IDs de bugs em estados não-finalizados
  2. workitemsbatch (lotes de 200) -> Id, Title, State, AreaPath, CreatedDate
  3. Computa dias aberto + flag (ALTA/MÉDIA/BAIXA)
  4. Gera PDF (A4 paisagem) e imprime um resumo JSON no stdout

Saída:
  - PDF: <out_dir>/Relatorio_Bugs_<projeto>_<YYYY-MM-DD>.pdf
  - stdout (última linha): JSON
    {"pdf_path","project","date","total","alta","media","baixa"}

Variáveis de ambiente (carregue de ~/.config/agile/.env — ver shared/README.md):
  AZDO_PAT       (obrigatório)  Personal Access Token, escopo Work Items (Read)
  AZDO_ORG       (obrigatório)  nome da organização no Azure DevOps
  AZDO_PROJECT   (obrigatório)  nome do projeto no Azure DevOps
  REPORT_OUT_DIR (opcional)     diretório de saída (default: diretório atual)

Uso:
  python3 build_report.py [--out-dir DIR]
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# Bootstrap: torna o cliente compartilhado importável mesmo sem PYTHONPATH.
# scripts -> agile-report-bugs -> skills -> <repo>/shared
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from azdo.client import API_VERSION, FINALIZED_STATES, post, require_env  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)

COR_VERMELHA = colors.HexColor("#D32F2F")
COR_AMARELA = colors.HexColor("#F9A825")
COR_VERDE = colors.HexColor("#388E3C")


def fetch_open_bugs(org: str, project: str, pat: str) -> list[dict]:
    """Retorna lista de dicts: {id, title, state, area, created (YYYY-MM-DD)}."""
    not_in = ", ".join(f"'{s}'" for s in FINALIZED_STATES)
    wiql = (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.TeamProject] = '{project}' "
        "AND [System.WorkItemType] = 'Bug' "
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
        "System.CreatedDate",
    ]
    batch_url = (
        f"https://dev.azure.com/{org}/_apis/wit/workitemsbatch"
        f"?api-version={API_VERSION}"
    )
    bugs = []
    for i in range(0, len(ids), 200):  # API aceita no máximo 200 ids por chamada
        chunk = ids[i : i + 200]
        resp = post(batch_url, {"ids": chunk, "fields": fields}, pat)
        for wi in resp.get("value", []):
            f = wi["fields"]
            created_raw = f.get("System.CreatedDate", "")
            created = created_raw[:10] if created_raw else ""
            bugs.append(
                {
                    "id": f.get("System.Id"),
                    "title": f.get("System.Title", "").strip(),
                    "state": f.get("System.State", ""),
                    "area": f.get("System.AreaPath", ""),
                    "created": created,
                }
            )
    return bugs


def area_label(area_path: str) -> str:
    """
    Converte 'Projeto\\Plataforma\\Integracoes' -> 'Plataforma \\ Integracoes'.
    Remove o primeiro segmento (nome do projeto) e mantém os 2 últimos níveis,
    deixando o relatório agrupado por time de forma legível.
    """
    if not area_path:
        return "(raiz - sem time)"
    parts = [p for p in area_path.split("\\") if p]
    if len(parts) <= 1:
        return "(raiz - sem time)"
    rest = parts[1:]  # remove o prefixo do projeto
    return " \\ ".join(rest[-2:]) if len(rest) > 2 else " \\ ".join(rest)


def dias_aberto(created_iso: str, ref: date) -> int:
    y, m, d = map(int, created_iso.split("-"))
    return (ref - date(y, m, d)).days


def flag_for(dias: int):
    """ALTA > 60 dias | MÉDIA 30–60 (inclusive) | BAIXA < 30 dias."""
    if dias > 60:
        return "ALTA", COR_VERMELHA
    if dias >= 30:
        return "MÉDIA", COR_AMARELA
    return "BAIXA", COR_VERDE


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_") or "Projeto"


def montar_pdf(bugs: list[dict], saida: str, ref: date, org: str, project: str):
    doc = SimpleDocTemplate(
        saida,
        pagesize=landscape(A4),
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Relatório de Bugs Abertos - {project}",
        author=f"{project} - Azure DevOps",
    )
    styles = getSampleStyleSheet()
    s_title = ParagraphStyle("t", parent=styles["Title"], fontSize=22, leading=26, spaceAfter=6)
    s_h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, leading=18,
                           spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#0B3D91"))
    s_h3 = ParagraphStyle("h3", parent=styles["Heading3"], fontSize=12, leading=15,
                           spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#0B3D91"))
    s_body = ParagraphStyle("b", parent=styles["BodyText"], fontSize=9.5, leading=12)
    s_small = ParagraphStyle("s", parent=styles["BodyText"], fontSize=8, leading=10,
                              textColor=colors.HexColor("#555555"))
    s_cell = ParagraphStyle("c", parent=styles["BodyText"], fontSize=8.5, leading=11)
    s_link = ParagraphStyle("lk", parent=styles["BodyText"], fontSize=8.5, leading=11,
                             alignment=TA_CENTER, textColor=colors.HexColor("#0B5FFF"))

    base_url = f"https://dev.azure.com/{org}/{project}/_workitems/edit"

    story = []
    story.append(Paragraph(f"Relatório de Bugs Abertos — {project}", s_title))
    story.append(Paragraph(
        f"Data de corte: <b>{ref.strftime('%d/%m/%Y')}</b> &nbsp;·&nbsp; "
        f"Fonte: Azure DevOps (organização {org}, projeto {project})", s_body))
    story.append(Paragraph(
        "Escopo: bugs em estados não-finalizados "
        "(exclui Closed, Resolved, Done, Removed, Discarded, Canceled).", s_small))
    story.append(Spacer(1, 6))

    legenda = Table(
        [["Legenda de tempo aberto:", "ALTA  (> 60 dias)",
          "MÉDIA  (30–60 dias)", "BAIXA  (< 30 dias)"]],
        colWidths=[42 * mm, 45 * mm, 45 * mm, 45 * mm],
    )
    legenda.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica-Bold", 9),
        ("BACKGROUND", (1, 0), (1, 0), COR_VERMELHA),
        ("BACKGROUND", (2, 0), (2, 0), COR_AMARELA),
        ("BACKGROUND", (3, 0), (3, 0), COR_VERDE),
        ("TEXTCOLOR", (1, 0), (3, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (1, 0), (-1, -1), 0.25, colors.grey),
        ("INNERGRID", (1, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(legenda)
    story.append(Spacer(1, 10))

    total = len(bugs)
    c_alta = sum(1 for b in bugs if dias_aberto(b["created"], ref) > 60)
    c_med = sum(1 for b in bugs if 30 <= dias_aberto(b["created"], ref) <= 60)
    c_bx = sum(1 for b in bugs if dias_aberto(b["created"], ref) < 30)

    story.append(Paragraph("Visão geral", s_h2))
    resumo = Table(
        [["Total de bugs abertos", "ALTA (>60d)", "MÉDIA (30–60d)", "BAIXA (<30d)"],
         [str(total), str(c_alta), str(c_med), str(c_bx)]],
        colWidths=[60 * mm, 50 * mm, 50 * mm, 50 * mm],
    )
    resumo.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, 1), (-1, 1), "Helvetica-Bold", 16),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (1, 1), (1, 1), COR_VERMELHA),
        ("BACKGROUND", (2, 1), (2, 1), COR_AMARELA),
        ("BACKGROUND", (3, 1), (3, 1), COR_VERDE),
        ("TEXTCOLOR", (1, 1), (3, 1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(resumo)
    story.append(Spacer(1, 12))

    por_time: dict[str, list[dict]] = {}
    for b in bugs:
        por_time.setdefault(area_label(b["area"]), []).append(b)
    times = sorted(por_time.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    story.append(Paragraph("Sumário por time (AreaPath)", s_h2))
    sum_data = [["Time / AreaPath", "Total", "ALTA", "MÉDIA", "BAIXA"]]
    for area, bs in times:
        a = sum(1 for x in bs if dias_aberto(x["created"], ref) > 60)
        m = sum(1 for x in bs if 30 <= dias_aberto(x["created"], ref) <= 60)
        bx = sum(1 for x in bs if dias_aberto(x["created"], ref) < 30)
        sum_data.append([area, str(len(bs)), str(a), str(m), str(bx)])
    sum_data.append(["TOTAL", str(total), str(c_alta), str(c_med), str(c_bx)])

    sum_tbl = Table(sum_data, colWidths=[110 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm],
                    repeatRows=1)
    sum_tbl.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
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
        ("TEXTCOLOR", (2, 1), (2, -2), COR_VERMELHA),
        ("TEXTCOLOR", (3, 1), (3, -2), colors.HexColor("#B8860B")),
        ("TEXTCOLOR", (4, 1), (4, -2), COR_VERDE),
        ("FONT", (2, 1), (4, -2), "Helvetica-Bold", 9.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sum_tbl)
    story.append(PageBreak())

    story.append(Paragraph("Detalhamento por time", s_h2))
    for area, bs in times:
        bs_sorted = sorted(bs, key=lambda b: -dias_aberto(b["created"], ref))
        a = sum(1 for x in bs if dias_aberto(x["created"], ref) > 60)
        m = sum(1 for x in bs if 30 <= dias_aberto(x["created"], ref) <= 60)
        bx = sum(1 for x in bs if dias_aberto(x["created"], ref) < 30)
        cab = (f"{area} &nbsp;<font size=9 color='#555555'>— total: {len(bs)}  ·  "
               f"ALTA: {a}  ·  MÉDIA: {m}  ·  BAIXA: {bx}</font>")
        header = Paragraph(cab, s_h3)

        data = [["Flag", "ID", "Estado", "Aberto em", "Dias", "Título"]]
        row_colors = []
        for idx, b in enumerate(bs_sorted, start=1):
            d = dias_aberto(b["created"], ref)
            label, cor = flag_for(d)
            url = f"{base_url}/{b['id']}"
            id_link = Paragraph(f'<link href="{url}"><u>{b["id"]}</u></link>', s_link)
            data.append([label, id_link, b["state"], b["created"], str(d),
                         Paragraph(b["title"], s_cell)])
            row_colors.append((idx, cor))

        t = Table(data, colWidths=[18 * mm, 16 * mm, 26 * mm, 22 * mm, 14 * mm, 174 * mm],
                  repeatRows=1)
        ts = TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (4, -1), "CENTER"),
            ("ALIGN", (5, 0), (5, -1), "LEFT"),
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
        for idx, cor in row_colors:
            ts.add("BACKGROUND", (0, idx), (0, idx), cor)
            ts.add("TEXTCOLOR", (0, idx), (0, idx), colors.white)
            ts.add("FONT", (0, idx), (0, idx), "Helvetica-Bold", 8.5)
        t.setStyle(ts)
        story.append(KeepTogether([header, t, Spacer(1, 6)]))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<i>Critérios:</i> <b>ALTA</b> = aberto há mais de 60 dias; "
        "<b>MÉDIA</b> = entre 30 e 60 dias (inclusive); "
        "<b>BAIXA</b> = aberto há menos de 30 dias. "
        "Dias contados de System.CreatedDate até a data de corte.", s_small))

    doc.build(story)
    return {"total": total, "alta": c_alta, "media": c_med, "baixa": c_bx}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.environ.get("REPORT_OUT_DIR", "."))
    args = ap.parse_args()

    pat = require_env("AZDO_PAT")
    org = require_env("AZDO_ORG")
    project = require_env("AZDO_PROJECT")

    ref = date.today()
    bugs = fetch_open_bugs(org, project, pat)
    if not bugs:
        raise SystemExit("Nenhum bug aberto retornado pela query — nada a gerar.")

    os.makedirs(args.out_dir, exist_ok=True)
    pdf_path = os.path.join(
        args.out_dir, f"Relatorio_Bugs_{_slug(project)}_{ref.isoformat()}.pdf"
    )
    counts = montar_pdf(bugs, pdf_path, ref, org, project)

    summary = {
        "pdf_path": os.path.abspath(pdf_path),
        "project": project,
        "date": ref.isoformat(),
        **counts,
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
