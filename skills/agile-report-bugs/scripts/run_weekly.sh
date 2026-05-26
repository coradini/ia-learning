#!/bin/bash
# run_weekly.sh — Orquestra a rotina semanal de relatório de bugs de ponta a
# ponta (Azure DevOps → PDF → Google Drive → Google Chat), pensado para rodar
# sem supervisão via launchd. Em qualquer falha, posta um alerta no Chat e sai
# com código != 0 (sem postar relatório incompleto).

set -euo pipefail

PY=/usr/bin/python3
ENV_FILE="$HOME/.config/agile/.env"          # .env COMPARTILHADO da família agile-*
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)" # auto-localiza a pasta da skill
LOG_DIR="$HOME/.config/agile/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/agile-report-bugs_$(date +%Y-%m-%d).log"

# Tudo (stdout+stderr) também vai pro log datado.
exec > >(tee -a "$LOG_FILE") 2>&1
echo "===== início: $(date '+%Y-%m-%d %H:%M:%S') ====="

if [ ! -f "$ENV_FILE" ]; then
  echo "ERRO: $ENV_FILE não encontrado." >&2
  exit 1
fi
set -a; source "$ENV_FILE"; set +a
cd "$SKILL_DIR"

# Em qualquer erro, tenta avisar no Chat antes de morrer.
notify_failure() {
  local step="$1"
  if [ -n "${GCHAT_WEBHOOK_URL:-}" ]; then
    curl -s -X POST -H 'Content-Type: application/json' \
      -d "{\"text\":\"⚠️ *Rotina de relatório de bugs falhou* na etapa: ${step}. Log: ${LOG_FILE}\"}" \
      "$GCHAT_WEBHOOK_URL" >/dev/null 2>&1 || true
  fi
  echo "ERRO na etapa: ${step}. Veja o log acima." >&2
}

# 1. Gerar PDF a partir do Azure DevOps.
trap 'notify_failure "1/3 build_report (Azure DevOps → PDF)"' ERR
SUMMARY=$("$PY" scripts/build_report.py --out-dir "${REPORT_OUT_DIR:-$SKILL_DIR}" | tail -n1)
PDF=$("$PY" -c "import sys,json; print(json.loads(sys.argv[1])['pdf_path'])" "$SUMMARY")

# 2. Arquivar no Google Drive.
trap 'notify_failure "2/3 deliver (upload Google Drive)"' ERR
DELIVER=$("$PY" scripts/deliver.py --pdf "$PDF" | tail -n1)
LINK=$("$PY" -c "import sys,json; print(json.loads(sys.argv[1])['drive_link'])" "$DELIVER")

# 3. Postar no Google Chat.
trap 'notify_failure "3/3 post_gchat (mensagem no Chat)"' ERR
"$PY" scripts/post_gchat.py --link "$LINK" --summary-json "$SUMMARY"

trap - ERR
echo "===== fim OK: $(date '+%Y-%m-%d %H:%M:%S') ====="
