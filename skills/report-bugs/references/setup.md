# report-bugs — Configuração de pré-requisitos

> Este guia ensina você a criar **suas próprias credenciais**. Nenhum segredo
> deste projeto é distribuído — cada usuário gera as suas, isoladamente.
> **Nunca** faça commit do `.env` nem da chave da Service Account.

A skill depende de credenciais que ficam num arquivo de ambiente **fora do
repositório**. Local recomendado:

```
~/.config/report-bugs/.env
```

Copie o template e preencha com os SEUS valores:

```bash
mkdir -p ~/.config/report-bugs
cp .env.example ~/.config/report-bugs/.env
chmod 600 ~/.config/report-bugs/.env
$EDITOR ~/.config/report-bugs/.env
```

Variáveis:

```dotenv
AZDO_PAT=<seu Personal Access Token>
AZDO_ORG=<sua organização no Azure DevOps>
AZDO_PROJECT=<seu projeto no Azure DevOps>
GCHAT_WEBHOOK_URL=<URL do Incoming Webhook do seu espaço no Google Chat>
GDRIVE_SA_JSON=$HOME/.config/report-bugs/sa-key.json
GDRIVE_FOLDER_ID=<ID da pasta no seu Drive Compartilhado>
# Opcional:
# REPORT_OUT_DIR=$HOME/Documents/Reports
```

---

## A) Personal Access Token (Azure DevOps)

1. Acesse `https://dev.azure.com/<SUA_ORG>`.
2. Canto superior direito → ícone de usuário → **Personal access tokens**.
3. **+ New Token**.
4. Preencha:
   - **Name:** `report-bugs`
   - **Organization:** sua organização
   - **Expiration:** 90 ou 180 dias (anote para renovar; quando expirar a skill
     falha com `ERRO HTTP 401/203` — gere outro e atualize o `.env`).
   - **Scopes:** *Custom defined* → **Work Items** → **Read** (somente isso).
5. **Create** e copie o token na hora (não é exibido novamente).
6. Preencha `AZDO_PAT`, `AZDO_ORG` e `AZDO_PROJECT` no `.env`.

## B) Incoming Webhook (Google Chat)

1. Abra o Google Chat (web) e entre no **espaço** de destino.
2. Nome do espaço (topo) → seta para baixo → **Apps e integrações**.
3. **Gerenciar webhooks** (ou **Adicionar webhooks**).
4. Nome: `Report Bugs` → **Salvar**.
5. Copie a URL gerada e cole em `GCHAT_WEBHOOK_URL` no `.env`.

> Se "Gerenciar webhooks" não aparecer, o admin do Workspace desativou webhooks
> de entrada nesse espaço. Peça liberação ou troque o canal de entrega.

## C) Service Account + Drive Compartilhado (Google Drive)

O upload é headless, feito por `scripts/deliver.py` com uma **Service Account**.

### C.1 Criar a Service Account

1. https://console.cloud.google.com/ → selecione/crie um projeto.
2. **APIs & Services → Library** → habilite a **Google Drive API**.
3. **APIs & Services → Credentials → Create credentials → Service account**.
   - Nome: `report-bugs-uploader` → **Done**.
4. Abra a service account → aba **Keys** → **Add key → Create new key → JSON**
   → baixe.
5. Salve em `~/.config/report-bugs/sa-key.json` e
   `chmod 600 ~/.config/report-bugs/sa-key.json`.
6. Anote o **e-mail da service account**
   (`...@<projeto>.iam.gserviceaccount.com`).

### C.2 Cota: usar um Drive Compartilhado

Uma Service Account **não tem cota de armazenamento própria**. Se a pasta
estiver no "Meu Drive", o upload falha com `storageQuotaExceeded`.

**Caminho recomendado — Drive Compartilhado (Shared Drive):**
1. Google Drive → **Drives compartilhados → Novo** → ex.: `Relatórios`.
2. Crie a pasta de destino dentro dele.
3. Adicione o **e-mail da service account** como membro do Drive
   Compartilhado, papel **Colaborador de conteúdo** (ou superior).
4. Atualize `GDRIVE_FOLDER_ID` no `.env` com o ID dessa pasta
   (parte final da URL `/folders/<ID>`).

> Alternativa (sem Shared Drive): delegação em todo o domínio impersonando um
> usuário — exige admin do Google Workspace.

O `deliver.py` define o compartilhamento "qualquer pessoa com o link → leitor"
automaticamente após o upload.

---

## Dependências Python

```bash
pip install -r requirements.txt
```

## Teste rápido

```bash
set -a; source ~/.config/report-bugs/.env; set +a
python3 scripts/build_report.py --out-dir /tmp
```

Sucesso = um PDF em `/tmp/Relatorio_Bugs_<projeto>_<data>.pdf` e uma linha JSON
de resumo no stdout. Erros de credencial vêm com mensagem explicando o ajuste.

Para o fluxo completo (Drive + Chat), siga os 3 passos descritos no `SKILL.md`.
