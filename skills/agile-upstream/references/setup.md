# agile-upstream — Configuração ESPECÍFICA desta skill

> Os pré-requisitos **comuns** à família `agile-*` (criar o PAT do Azure DevOps,
> instalar o `.env` compartilhado em `~/.config/agile/.env`, dependências
> Python) estão em [`../../../shared/README.md`](../../../shared/README.md).
> **Comece por lá.**
>
> A entrega (**Google Chat** + **Google Drive**) é **idêntica** à do
> `agile-report-bugs` e usa as **mesmas** variáveis no mesmo
> `~/.config/agile/.env`. Se você já configurou aquela skill, **não há nada novo
> a fazer aqui** — esta skill funciona com a configuração existente.

Variáveis usadas por esta skill (todas no `~/.config/agile/.env`):

```dotenv
# Comuns (ver ../../../shared/README.md)
AZDO_PAT=<PAT com escopo Work Items: Read>
AZDO_ORG=<organização>
AZDO_PROJECT=<projeto>

# Entrega — idênticas às do agile-report-bugs
GCHAT_WEBHOOK_URL=<URL do Incoming Webhook do seu espaço no Google Chat>
GDRIVE_SA_JSON=$HOME/.config/agile/sa-key.json
GDRIVE_FOLDER_ID=<ID da pasta no seu Drive Compartilhado>
# Opcional:
# REPORT_OUT_DIR=$HOME/Documents/Reports
```

## Setup do Google Chat e Google Drive

O passo a passo completo (Incoming Webhook, Service Account, Drive Compartilhado
e cota) está documentado uma única vez em
[`../../agile-report-bugs/references/setup.md`](../../agile-report-bugs/references/setup.md).
Siga aquele guia — vale igual para esta skill, pois `deliver.py` e a entrega são
os mesmos.

## Teste rápido (só a etapa Azure DevOps → PDF)

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/build_report.py --out-dir /tmp
```

Sucesso = um PDF em `/tmp/Relatorio_Upstream_<projeto>_<data>.pdf` e uma linha
JSON de resumo no stdout. Esse é exatamente o **modo avulso** (sem Drive/Chat).
Para o fluxo completo, siga os 3 passos do `SKILL.md` ou rode
`scripts/run_weekly.sh`.

## Notas de processo (Azure DevOps)

- **Impedimento** é lido do campo `Microsoft.VSTS.CMMI.Blocked` (valor `Yes`).
  Confirme que seu processo expõe esse campo nos épicos. Se o bloqueio for
  registrado por **tag** ou por um **estado** próprio, ajuste `BLOCKED_FIELD` e
  `fetch_blocked_since` em `scripts/build_report.py`.
- **Tempo parado** usa `Microsoft.VSTS.Common.StateChangeDate`; se ausente, cai
  para `System.CreatedDate`.
- **Responsável (PO)** vem de `System.AssignedTo`.
