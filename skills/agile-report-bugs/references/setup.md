# agile-report-bugs — Configuração ESPECÍFICA desta skill

> Os pré-requisitos **comuns** à família `agile-*` (criar o Personal Access
> Token do Azure DevOps, instalar o `.env` compartilhado em
> `~/.config/agile/.env`, dependências Python) estão em
> [`../../../shared/README.md`](../../../shared/README.md). **Comece por lá.**
>
> Este guia cobre só o que é exclusivo do `agile-report-bugs`: a entrega no
> **Google Chat** e no **Google Drive**. Todas as variáveis abaixo vão no
> MESMO arquivo `~/.config/agile/.env`.

As variáveis específicas desta skill:

```dotenv
GCHAT_WEBHOOK_URL=<URL do Incoming Webhook do seu espaço no Google Chat>
GDRIVE_SA_JSON=$HOME/.config/agile/sa-key.json
GDRIVE_FOLDER_ID=<ID da pasta no seu Drive Compartilhado>
# Opcional:
# REPORT_OUT_DIR=$HOME/Documents/Reports
```

---

## A) Incoming Webhook (Google Chat)

1. Abra o Google Chat (web) e entre no **espaço** de destino.
2. Nome do espaço (topo) → seta para baixo → **Apps e integrações**.
3. **Gerenciar webhooks** (ou **Adicionar webhooks**).
4. Nome: `Report Bugs` → **Salvar**.
5. Copie a URL gerada e cole em `GCHAT_WEBHOOK_URL` no `.env`.

> Se "Gerenciar webhooks" não aparecer, o admin do Workspace desativou webhooks
> de entrada nesse espaço. Peça liberação ou troque o canal de entrega.

## B) Service Account + Drive Compartilhado (Google Drive)

O upload é headless, feito por `scripts/deliver.py` com uma **Service Account**.

### B.1 Criar a Service Account

1. https://console.cloud.google.com/ → selecione/crie um projeto.
2. **APIs & Services → Library** → habilite a **Google Drive API**.
3. **APIs & Services → Credentials → Create credentials → Service account**.
   - Nome: `report-bugs-uploader` → **Done**.
4. Abra a service account → aba **Keys** → **Add key → Create new key → JSON**
   → baixe.
5. Salve em `~/.config/agile/sa-key.json` e
   `chmod 600 ~/.config/agile/sa-key.json`.
6. Anote o **e-mail da service account**
   (`...@<projeto>.iam.gserviceaccount.com`).

### B.2 Cota: usar um Drive Compartilhado

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

## Teste rápido (só a etapa Azure DevOps → PDF)

```bash
set -a; source ~/.config/agile/.env; set +a
python3 scripts/build_report.py --out-dir /tmp
```

Sucesso = um PDF em `/tmp/Relatorio_Bugs_<projeto>_<data>.pdf` e uma linha JSON
de resumo no stdout. Para o fluxo completo (Drive + Chat), siga os 3 passos do
`SKILL.md`.
