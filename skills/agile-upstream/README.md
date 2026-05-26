# agile-upstream

Visão gerencial da **saúde dos épicos** do Azure DevOps, em PDF agrupado por
**time (AreaPath)** e pensada para o **Product Owner de cada time**. O objetivo
é duplo: **ajudar** o PO a ver o que precisa de atenção e **alertar** sobre itens
velhos que deveriam ser descartados.

Parte da família **`agile-*`** — compartilha o cliente REST `azdo.client` e o
`.env` (`~/.config/agile/.env`). Motor **REST+PAT** (mesma espinha do
`agile-report-bugs`): roda agendada de ponta a ponta e também avulsa sob demanda.

## O que ela sinaliza

Cada épico recebe **uma cor** (status único por movimentação, faixa mais alta
vence):

| Cor | Status | Critério |
|---|---|---|
| 🟢 | **Saudável** | movimentação nos últimos 60 dias |
| 🟠 | **Questionável** | sem movimentação há mais de 60 dias |
| 🔴 | **Agarrado** | sem movimentação há mais de 90 dias |
| 🟣 | **Para descarte** | sem movimentação há mais de 180 dias |

A skill separa **funil** (backlog cru — default estado `Idea`, que não se move)
de **fluxo** (épicos que já entraram na entrega): em fluxo a cor mede a
**movimentação** (dias desde a última mudança de estado); no funil mede a
**idade** — o item Roxo do funil é o candidato a limpar do backlog.

O PDF traz uma visão geral (composição fluxo × funil + quebra por cor), uma seção
**Em fluxo** e uma seção **Funil**, cada uma com sumário e detalhamento por time
(épicos ordenados pelo mais crítico, com responsável/PO e dias). As cores
aparecem como barra + texto colorido (reportlab não renderiza emoji). Limiares
(60/90/180), `EPIC_TYPE` (default `Epic_`) e `FUNNEL_STATES` (default `Idea`) são
constantes no topo de `scripts/build_report.py`.

## Quickstart

```bash
# 1. Pré-requisitos comuns (PAT + .env): ../../shared/README.md
# 2. Entrega (Chat/Drive): references/setup.md  (igual ao agile-report-bugs)
pip install -r requirements.txt
set -a; source ~/.config/agile/.env; set +a

# Avulso (sob demanda, só PDF local — NÃO posta no Chat):
python3 scripts/build_report.py --out-dir /tmp

# Agendado (ponta a ponta: PDF → Drive → Chat):
bash scripts/run_weekly.sh
```

## Pré-requisitos

| Item | Onde |
|---|---|
| PAT (Work Items: Read) + `.env` compartilhado | [`../../shared/README.md`](../../shared/README.md) |
| `AZDO_PAT`, `AZDO_ORG`, `AZDO_PROJECT` | idem (comuns à família) |
| `GCHAT_WEBHOOK_URL`, `GDRIVE_SA_JSON`, `GDRIVE_FOLDER_ID` | [`references/setup.md`](references/setup.md) |
| `reportlab`, libs Google | `requirements.txt` |

Não há variável nova além das já usadas pelo `agile-report-bugs`.

## Instalação para o Claude Code carregar

```bash
ln -sfn "<repo>/skills/agile-upstream" ~/.claude/skills/agile-upstream
```

## Limitações conhecidas

- Escopo é **só Épicos** (tipo `Epic_`), agrupados por **AreaPath**. Recortes
  (por PO, por iteração) ou incluir Features/US são evolução, não parâmetro de
  runtime.
- A cor mede **uma** dimensão (movimentação em fluxo, idade no funil). Não há
  sinal separado de impedimento/bloqueio nesta versão — a leitura é puramente
  por tempo sem movimento.
- "Movimentação" depende de `Microsoft.VSTS.Common.StateChangeDate`; se um
  processo não preencher esse campo, cai para a data de criação.
