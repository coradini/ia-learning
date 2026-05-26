---
name: agile-upstream
description: >-
  Visão gerencial da SAÚDE DOS ÉPICOS do Azure DevOps por time (AreaPath), em
  PDF, para o Product Owner de cada time. Classifica cada épico por uma cor de
  MOVIMENTAÇÃO: verde (saudável), laranja (questionável), vermelho (agarrado),
  roxo (para descarte). Roda AGENDADA de ponta a ponta (PDF → Google Drive →
  Google Chat) e também AVULSA sob demanda (gera o PDF sem postar no Chat). Use
  quando o usuário pedir "saúde dos épicos", "épicos agarrados", "agile-upstream",
  "visão de épicos", "épicos parados/sem movimentação", "o que está agarrado no
  upstream", "épicos para descartar/limpar do backlog" ou variações sobre a
  situação dos épicos por time. É o caminho rápido e padronizado (REST API, 2
  chamadas) que substitui a varredura manual do backlog de épicos.
---

# agile-upstream

Compila a **visão gerencial da saúde dos épicos por time** e a entrega:
**Azure DevOps → PDF → Google Drive → mensagem no Google Chat**.

Faz parte da família de skills **`agile-*`** deste repositório, que compartilham
o cliente REST `azdo.client` (em `shared/`) e o mesmo `.env`
(`~/.config/agile/.env`).

Escopo: todos os **épicos** em estados não-finalizados, agrupados por time
(AreaPath). Cada épico recebe **uma cor** (status único, faixa mais alta vence):

| Cor | Status | Critério |
|---|---|---|
| 🟢 | **Saudável** | movimentação nos últimos 60 dias |
| 🟠 | **Questionável** | sem movimentação há mais de 60 dias |
| 🔴 | **Agarrado** | sem movimentação há mais de 90 dias |
| 🟣 | **Para descarte** | sem movimentação há mais de 180 dias |

"Movimentação" = dias desde a última mudança de estado
(`Microsoft.VSTS.Common.StateChangeDate`). A skill separa **funil** (backlog
cru — estados em `FUNNEL_STATES`, default `Idea`, que por natureza não se movem)
do **fluxo** (épicos que já entraram na entrega):

- **Em fluxo**: a cor mede a **movimentação** (dias sem mudança de estado).
- **Funil**: a cor mede a **idade** (dias desde a criação) — o item Roxo do
  funil é o candidato a limpar do backlog.

Os limiares (60/90/180), `FUNNEL_STATES` e `EPIC_TYPE` são **constantes** no
topo de `scripts/build_report.py` (não são parâmetros de runtime — mesma política
do `agile-report-bugs`). Os estados finalizados são descobertos dinamicamente
por **categoria** (`finalized_states_for` em `shared/azdo/client.py`), robusto
para processos customizados (este projeto usa o tipo `Epic_` com terminal
`Completed`). No PDF as cores aparecem como barra colorida + texto colorido (as
fontes do reportlab não renderizam emoji); os emojis ficam só na mensagem do
Chat.

## Pré-requisitos (uma vez)

Credenciais ficam num `.env` **compartilhado** entre as skills `agile-*`, **fora
deste repositório**: `~/.config/agile/.env` (`chmod 600`). Se faltar o arquivo
ou alguma variável, **pare e oriente o usuário a seguir
`../../shared/README.md`** (criação do PAT e instalação do `.env`) e, para o que
é específico desta skill (Google Chat + Drive), `references/setup.md`. Nunca
peça segredos no chat nem os escreva no repo.

Variáveis necessárias: `AZDO_PAT`, `AZDO_ORG`, `AZDO_PROJECT` (comuns) +
`GCHAT_WEBHOOK_URL`, `GDRIVE_SA_JSON`, `GDRIVE_FOLDER_ID` (entrega — idênticas às
do `agile-report-bugs`; ver `references/setup.md`).

Dependências: `pip install -r requirements.txt`.

Carregue o `.env` antes de rodar os scripts:

```bash
set -a; source ~/.config/agile/.env; set +a
```

## Modo AVULSO (sob demanda, sem postar no Chat)

Quando o usuário pede um relatório agora, gere **só o PDF** (sem Drive/Chat):

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/build_report.py --out-dir /tmp
```

Devolva ao usuário o caminho do PDF e o resumo (a última linha JSON do stdout).
Se ele quiser um link compartilhável sem postar no Chat, rode também o passo 2
(Drive) e entregue o `drive_link` — **sem** o passo 3.

## Modo AGENDADO (rotina completa)

Execute na ordem. Uma falha em qualquer etapa interrompe o fluxo com mensagem
clara — postar relatório incompleto ou link quebrado é pior do que não postar.
A automação (launchd/cron) usa `scripts/run_weekly.sh`, que já carrega o `.env`
compartilhado, se auto-localiza e avisa no Chat em caso de falha.

### 1. Gerar o PDF a partir do Azure DevOps

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/build_report.py --out-dir "${REPORT_OUT_DIR:-.}"
```

Faz a WIQL de épicos + `workitemsbatch` (2 chamadas REST, sem fan-out),
classifica cada épico por cor e gera o PDF datado, imprimindo **na última linha
do stdout** o resumo:

```json
{"pdf_path":"/.../Relatorio_Upstream_<projeto>_<data>.pdf","project":"<projeto>","date":"<data>","total":0,"fluxo":0,"funil":0,"saudavel":0,"questionavel":0,"agarrado":0,"descarte":0,"funil_descarte":0}
```

Guarde esse JSON inteiro e o `pdf_path` — as próximas etapas dependem deles.

### 2. Arquivar o PDF no Google Drive

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/deliver.py --pdf "<pdf_path do passo 1>"
```

`deliver.py` (idêntico ao do `agile-report-bugs`) sobe o PDF via Service Account
para a pasta `GDRIVE_FOLDER_ID`, define "qualquer pessoa com o link → leitor" e
imprime **na última linha** `{"drive_link":"...","file_id":"..."}`. Se falhar
com erro de cota, a pasta precisa estar em um **Drive Compartilhado** (ver
`references/setup.md`); nesse caso **não prossiga para o Chat**.

### 3. Postar o link no Google Chat

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/post_gchat.py --link "<drive_link>" --summary-json '<JSON do passo 1>'
```

### 4. Confirmar ao usuário

Responda com: total de épicos ativos, a composição fluxo × funil e a quebra por
cor em fluxo (saudável/questionável/agarrado/para descarte), o link do Drive e a
confirmação de que a mensagem foi postada no espaço do Chat.

## Notas de manutenção

- **Estados finalizados** são descobertos por categoria via
  `finalized_states_for()` em `shared/azdo/client.py` (não a lista estática
  `FINALIZED_STATES`, que não cobre este processo customizado). **Tipo de épico**
  = `EPIC_TYPE` (default `Epic_`, override por env `EPIC_WORKITEM_TYPE`).
  **Funil vs fluxo** = `FUNNEL_STATES` (default `Idea`). **Limiares de cor**
  (60/90/180 dias) — tudo no topo de `scripts/build_report.py`.
- **Movimentação** = dias desde `Microsoft.VSTS.Common.StateChangeDate` (cai
  para `System.CreatedDate` se ausente). No funil, a cor usa a idade
  (`System.CreatedDate`).
- **Responsável (PO)** vem de `System.AssignedTo`. Se o PO do time for outro
  campo (custom) ou o dono da AreaPath, ajuste o mapeamento em `fetch_epics`.
- **Emojis no PDF**: as fontes do reportlab (Helvetica/WinAnsi) não têm glyph de
  emoji nem de `≤`; por isso o PDF usa barra colorida + texto colorido, e o
  `post_gchat.py` usa emoji só na mensagem do Chat. Não reintroduza emoji nas
  strings do PDF.
- **Autenticação e chamadas REST** vivem em `shared/azdo/client.py`; esta skill
  só monta queries e o PDF.
- **PAT expirado** aparece como `ERRO HTTP 401/203` no passo 1: gerar novo token
  e atualizar o `.env` (ver `shared/README.md`).
- **Texto da mensagem** do Chat: função `build_message` em
  `scripts/post_gchat.py`.
