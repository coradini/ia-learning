#!/usr/bin/env python3
"""
notify.py — posta o aviso de "novo post mortem pronto" no Google Chat e (opcional) no Teams.

Usa o MESMO canal da família agile-*: o envio ao Google Chat é um incoming webhook,
lido da variável de ambiente GCHAT_WEBHOOK_URL do .env compartilhado
(~/.config/agile/.env) — a mesma usada pela agile-report-bugs. Nenhuma URL/segredo
é embutido aqui.

Uso:
    # carregue o .env compartilhado (mesma webhook = mesmo espaço do Chat)
    set -a; source ~/.config/agile/.env; set +a
    # (opcional) defina um webhook de canal do Teams (TEAMS_WEBHOOK_URL no .env)

    python3 notify.py --message-file msg.txt
    python3 notify.py --message "📄 Novo post mortem pronto: ..."

    python3 notify.py --message-file msg.txt
    python3 notify.py --message "📄 Novo post mortem pronto: ..."

Confirme o texto e os destinos com a pessoa ANTES de rodar — enviar mensagem é irreversível.
Só usa a biblioteca padrão (sem dependências).
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def post(url: str, payload: dict) -> tuple[bool, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return 200 <= resp.status < 300, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Notifica GChat + Teams sobre novo post mortem.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--message", help="Texto da mensagem.")
    g.add_argument("--message-file", help="Arquivo com o texto da mensagem.")
    ap.add_argument("--gchat-only", action="store_true", help="Não tentar o Teams.")
    args = ap.parse_args()

    msg = args.message if args.message else open(args.message_file, encoding="utf-8").read().strip()

    gchat = os.environ.get("GCHAT_WEBHOOK_URL")
    teams = os.environ.get("TEAMS_WEBHOOK_URL")

    results = []

    # Google Chat — mesmo webhook/canal da família agile-*
    if gchat:
        ok, info = post(gchat, {"text": msg})
        results.append(("Google Chat", ok, info))
    else:
        results.append(("Google Chat", False, "GCHAT_WEBHOOK_URL não definida (carregue ~/.config/agile/.env)"))

    # Teams — opcional (não há conector; usa incoming webhook próprio)
    if not args.gchat_only:
        if teams:
            ok, info = post(teams, {"text": msg})  # MessageCard simples aceita "text"
            results.append(("Microsoft Teams", ok, info))
        else:
            results.append(("Microsoft Teams", None, "TEAMS_WEBHOOK_URL não definida (pulando)"))

    print("Resultado da notificação:")
    rc = 0
    for canal, ok, info in results:
        mark = "✅" if ok else ("➖" if ok is None else "❌")
        print(f"  {mark} {canal}: {info}")
        if ok is False:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
