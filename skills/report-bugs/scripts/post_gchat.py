#!/usr/bin/env python3
"""
post_gchat.py — Posta a mensagem do relatório num espaço do Google Chat via
Incoming Webhook.

A mensagem leva o link do PDF (já hospedado no Google Drive) e um resumo
dos números-chave, para a pessoa decidir se abre o relatório completo.

Variáveis de ambiente:
  GCHAT_WEBHOOK_URL  (obrigatório)  URL do Incoming Webhook do espaço

Uso:
  python3 post_gchat.py --link <DRIVE_URL> --summary-json '<JSON do build_report>'

  O JSON do summary é exatamente a última linha impressa por build_report.py:
  {"pdf_path":...,"project":"MeuProjeto","date":"2026-05-18",
   "total":59,"alta":34,"media":7,"baixa":18}
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
    titulo = f"Relatório de Bugs Abertos — {project}".rstrip(" —")
    return (
        f"*{titulo}* ({s.get('date','')})\n"
        f"Total: *{s.get('total','?')}*  •  "
        f"🔴 ALTA (>60d): *{s.get('alta','?')}*  •  "
        f"🟡 MÉDIA (30–60d): *{s.get('media','?')}*  •  "
        f"🟢 BAIXA (<30d): *{s.get('baixa','?')}*\n"
        f"\n---\n\n"
        f"*Atenção SLs!* Bugs classificados com prioridade alta e média devem "
        f"receber sua atenção. Gentileza priorizar e/ou descartar para manter "
        f"o flow saudável do time.\n"
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
            "GCHAT_WEBHOOK_URL não definido. Configure seu arquivo .env "
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
