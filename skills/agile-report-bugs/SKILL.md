---
name: agile-report-bugs
description: >-
  Gera um relatório de bugs abertos do Azure DevOps em PDF (agrupado por time,
  com flag de tempo aberto), arquiva no Google Drive e posta o link num espaço
  do Google Chat. Use sempre que o usuário pedir "relatório de bugs",
  "report-bugs", "agile-report-bugs", "relatório semanal de bugs", "manda o
  status dos bugs no chat", "gera o PDF de bugs" ou qualquer variação que
  envolva compilar/enviar a situação dos bugs abertos de um projeto Azure
  DevOps — mesmo que não diga explicitamente "PDF" ou "Google Chat". É o
  caminho rápido e padronizado (REST API, ~2 chamadas) que substitui a coleta
  manual item a item. Projeto e organização são configuráveis por variáveis de
  ambiente.
---

# agile-report-bugs

Compila e entrega um relatório de bugs abertos de ponta a ponta:
**Azure DevOps → PDF → Google Drive → mensagem no Google Chat**.

Faz parte da família de skills **`agile-*`** deste repositório, que compartilham
o cliente REST `azdo.client` (em `shared/`) e o mesmo `.env`
(`~/.config/agile/.env`).

Escopo: todos os bugs em estados não-finalizados, agrupados por time
(AreaPath), com flag de tempo aberto (ALTA > 60 dias, MÉDIA 30–60, BAIXA < 30)
e IDs clicáveis apontando para o work item.

## Pré-requisitos (uma vez)

As credenciais ficam num `.env` **compartilhado** entre as skills `agile-*`,
**fora deste repositório**: `~/.config/agile/.env` (`chmod 600`). Se faltar o
arquivo ou alguma variável, **pare e oriente o usuário a seguir
`../../shared/README.md`** (criação do PAT e instalação do `.env`) e, para o
que é específico desta skill (Google Chat + Drive), `references/setup.md`.
Nunca peça segredos no chat nem os escreva no repo.

Variáveis necessárias: `AZDO_PAT`, `AZDO_ORG`, `AZDO_PROJECT` (comuns, ver
`shared/README.md`) + `GCHAT_WEBHOOK_URL`, `GDRIVE_SA_JSON`, `GDRIVE_FOLDER_ID`
(específicas desta skill, ver `references/setup.md`).

Dependências: `pip install -r requirements.txt`.

Carregue o `.env` antes de rodar os scripts:

```bash
set -a; source ~/.config/agile/.env; set +a
```

## Fluxo de execução

Execute na ordem. Uma falha em qualquer etapa deve interromper o fluxo com
mensagem clara — postar relatório incompleto ou link quebrado é pior do que
não postar.

### 1. Gerar o PDF a partir do Azure DevOps

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/build_report.py --out-dir "${REPORT_OUT_DIR:-.}"
```

Faz a query WIQL + `workitemsbatch` (2 chamadas REST via `azdo.client`, sem
fan-out), gera o PDF datado e imprime **na última linha do stdout** um JSON de
resumo:

```json
{"pdf_path":"/.../Relatorio_Bugs_<projeto>_<data>.pdf","project":"<projeto>","date":"<data>","total":0,"alta":0,"media":0,"baixa":0}
```

Guarde esse JSON inteiro e o `pdf_path` — as próximas etapas dependem deles.

### 2. Arquivar o PDF no Google Drive

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/deliver.py --pdf "<pdf_path do passo 1>"
```

`deliver.py` usa a Service Account (`GDRIVE_SA_JSON`) para subir o PDF na pasta
`GDRIVE_FOLDER_ID`, define "qualquer pessoa com o link → leitor" e imprime
**na última linha** um JSON: `{"drive_link":"...","file_id":"..."}`.

É headless de propósito — nenhum binário passa pelo modelo. Se falhar com erro
de cota da Service Account, a pasta precisa estar em um **Drive Compartilhado**
(ver `references/setup.md`). Nesse caso **não prossiga para o Chat**.

### 3. Postar o link no Google Chat

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/post_gchat.py --link "<drive_link>" --summary-json '<JSON do passo 1>'
```

### 4. Confirmar ao usuário

Responda com: total de bugs e a quebra por flag, o link do Drive e a
confirmação de que a mensagem foi postada no espaço do Chat.

## Notas de manutenção

- **Estados finalizados** vivem em `shared/azdo/client.py` (`FINALIZED_STATES`)
  — fonte única compartilhada por toda a família `agile-*`. **Critérios de
  tempo** (60/30 dias) estão em `scripts/build_report.py` (`flag_for`).
- **Autenticação e chamadas REST** vivem em `shared/azdo/client.py`; este skill
  só monta queries e o PDF.
- **PAT expirado** aparece como `ERRO HTTP 401/203` no passo 1: gerar novo
  token e atualizar o `.env` (ver `shared/README.md`).
- **Texto da mensagem** do Chat: função `build_message` em
  `scripts/post_gchat.py`.
- O escopo é fixo (sem filtros por time/ano). Recortes são evolução da skill,
  não parâmetro de runtime — confirme antes de mudar o comportamento padrão.
- Automação (agendar via `launchd`/cron) usa `scripts/run_weekly.sh`, que já
  aponta para o `.env` compartilhado e se auto-localiza. É um passo separado.
