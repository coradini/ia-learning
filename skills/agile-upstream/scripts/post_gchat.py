#!/usr/bin/env python3
"""
post_gchat.py — Posta a mensagem da Saúde dos Épicos por Time num espaço do
Google Chat via Incoming Webhook.

A mensagem leva o link do PDF (já no Google Drive) e o resumo por cor, para
cada Product Owner decidir se abre o relatório completo da sua seção (time).

Variáveis de ambiente:
  GCHAT_WEBHOOK_URL  (obrigatório)  URL do Incoming Webhook do espaço

Uso:
  python3 post_gchat.py --link <DRIVE_URL> --summary-json '<JSON do build_report>'

  O JSON do summary é exatamente a última linha impressa por build_report.py:
  {"pdf_path":...,"project":"MeuProjeto","date":"2026-05-26",
   "total":140,"fluxo":50,"funil":90,"saudavel":2,"questionavel":10,
   "agarrado":18,"descarte":20,"funil_descarte":69}
"""
import argparse
import json
import os
import urllib.error
import urllib.request


def post(webhook: str, text: str) -> None:
    data = json.dumps({"text": text}).encode()
    req = urllib.request.Request(webhook, data=data, method="POST")
    req.add_header("Content-Type", "application/json; charset=UTF-8")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"ERRO HTTP {e.code} ao postar no GChat:\n{body}")


def build_message(link: str, s: dict) -> str:
    # Google Chat (texto): negrito com *asteriscos*, link clicável <url|rótulo>.
    project = s.get("project", "")
    titulo = f"Saúde dos Épicos por Time — {project}".rstrip(" —")
    return (
        f"*{titulo}* ({s.get('date','')})\n"
        f"Épicos ativos: *{s.get('total','?')}*  "
        f"(em fluxo: *{s.get('fluxo','?')}*  •  funil: *{s.get('funil','?')}*)\n"
        f"*Em fluxo:*  🟢 Saudável: *{s.get('saudavel','?')}*  •  "
        f"🟠 Questionável: *{s.get('questionavel','?')}*  •  "
        f"🔴 Agarrado: *{s.get('agarrado','?')}*  •  "
        f"🟣 Para descarte: *{s.get('descarte','?')}*\n"
        f"🟣 Funil para descarte (idade > 180d): *{s.get('funil_descarte','?')}*\n"
        f"\n---\n\n"
        f"*POs, atenção ao seu time!* Cada seção do PDF é o seu time (AreaPath). "
        f"Priorize os épicos 🔴 *Agarrados* e avalie *descartar* os 🟣 "
        f"*Para descarte* (em fluxo e no funil) para manter o flow saudável.\n"
        f"\n"
        f"<{link}|📄 Abrir relatório completo com detalhe por time (PDF)>"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", required=True, help="URL do PDF no Google Drive")
    ap.add_argument("--summary-json", required=True,
                    help="JSON de resumo impresso por build_report.py")
    args = ap.parse_args()

    webhook = os.environ.get("GCHAT_WEBHOOK_URL")
    if not webhook:
        raise SystemExit(
            "GCHAT_WEBHOOK_URL não definido. Configure ~/.config/agile/.env "
            "(ver references/setup.md)."
        )

    try:
        summary = json.loads(args.summary_json)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--summary-json inválido: {e}")

    post(webhook, build_message(args.link, summary))
    print("Mensagem postada no Google Chat com sucesso.")


if __name__ == "__main__":
    main()
