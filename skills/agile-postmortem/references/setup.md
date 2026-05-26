# agile-postmortem — Configuração ESPECÍFICA desta skill

> A instalação do **`.env` compartilhado** da família `agile-*`
> (`~/.config/agile/.env`, `chmod 600`) está em
> [`../../../shared/README.md`](../../../shared/README.md). **Comece por lá** —
> mesmo que você não use as variáveis de Azure DevOps, é o mesmo arquivo.
>
> Este guia cobre só o que é exclusivo do `agile-postmortem`: a entrega no
> **Google Drive** (como Doc nativo) e a notificação no **Google Chat/Teams**.
> Todas as variáveis abaixo vão no MESMO arquivo `~/.config/agile/.env`.
>
> Esta skill **não usa Azure DevOps**, então `AZDO_PAT`/`AZDO_ORG`/`AZDO_PROJECT`
> não são necessários para rodá-la.

As variáveis específicas desta skill:

```dotenv
GDRIVE_SA_JSON=$HOME/.config/agile/sa-key.json
PM_TEMPLATE_DOC_ID=<ID do Google Doc template a ser duplicado>
PM_DRIVE_FOLDER_ID=<ID da pasta compartilhada de post mortems no seu Drive>
GCHAT_WEBHOOK_URL=<URL do Incoming Webhook do seu espaço no Google Chat>
# Opcional:
# TEAMS_WEBHOOK_URL=<URL do Incoming Webhook de um canal do Teams>
```

> `GDRIVE_SA_JSON` e `GCHAT_WEBHOOK_URL` são as **mesmas** usadas pela
> `agile-report-bugs` — se você já configurou aquela skill, só falta adicionar
> `PM_DRIVE_FOLDER_ID` (e, opcionalmente, `TEAMS_WEBHOOK_URL`).

> **Configuração única.** `PM_TEMPLATE_DOC_ID` e `PM_DRIVE_FOLDER_ID` são **fixos**
> (o template é sempre o mesmo Doc; a pasta de destino é sempre a mesma). Preencha
> uma vez no `~/.config/agile/.env` e a skill **não pergunta mais** — vai direto do
> título do post mortem ao link do Doc duplicado. O `shared/.env.example` já lista
> as duas variáveis como placeholders; os **valores reais** ficam só no seu
> `~/.config/agile/.env` e **nunca** são commitados.

---

## A) Dependências

```bash
# Gerador do .docx (Node)
cd scripts && npm install docx && cd ..
# Upload ao Drive (Python)
pip install -r requirements.txt
```

## B) Service Account + Drive Compartilhado (Google Drive)

O upload é headless, feito por `scripts/upload_gdoc.py` com uma **Service
Account**, que converte o `.docx` em Google Doc nativo na pasta de destino.

### B.1 Criar a Service Account

1. https://console.cloud.google.com/ → selecione/crie um projeto.
2. **APIs & Services → Library** → habilite a **Google Drive API**.
3. **APIs & Services → Credentials → Create credentials → Service account**.
   - Nome: ex. `postmortem-uploader` → **Done**.
4. Abra a service account → aba **Keys** → **Add key → Create new key → JSON** →
   baixe.
5. Salve em `~/.config/agile/sa-key.json` e `chmod 600 ~/.config/agile/sa-key.json`.
6. Anote o **e-mail da service account** (`...@<projeto>.iam.gserviceaccount.com`).

### B.2 Pasta de destino num Drive Compartilhado

Uma Service Account **não tem cota própria**. Se a pasta estiver no "Meu Drive",
o upload falha com `storageQuotaExceeded`.

1. Google Drive → **Drives compartilhados → Novo** → ex.: `Post Mortems`.
2. Crie (ou escolha) a pasta de destino dentro dele.
3. Adicione o **e-mail da service account** como membro do Drive Compartilhado,
   papel **Colaborador de conteúdo** (ou superior). **Sem isso a API retorna
   `File not found` na pasta** — o Drive nem aparece para a SA.
4. Pegue o ID da pasta (parte final da URL `/folders/<ID>`) e coloque em
   `PM_DRIVE_FOLDER_ID` no `.env`.

> Você também pode passar o `folder_id` como argumento dos scripts, que tem
> precedência sobre `PM_DRIVE_FOLDER_ID`.

### B.3 Google Doc template (duplicado no passo 1)

A skill **duplica** um Google Doc template a cada post mortem (em vez de gerar do
zero), para o usuário receber o link na hora. Prepare-o uma vez:

1. Crie o Doc template no Drive — pode gerar o `.docx` em branco com
   `node scripts/build_template.js /tmp/tpl.docx` e subi-lo convertendo em Doc
   nativo: `python3 scripts/upload_gdoc.py /tmp/tpl.docx "Post Mortem - TEMPLATE"`.
2. Guarde o **ID** do Doc (parte final da URL `/document/d/<ID>/edit`) em
   `PM_TEMPLATE_DOC_ID` no `.env`.
3. A **Service Account precisa ter acesso de leitura ao template** — se ele estiver
   na pasta/Drive compartilhado a que a SA já pertence, isso já está coberto.

> Pode passar `template_doc_id` como **2º argumento** do `duplicate_template.py`,
> com precedência sobre `PM_TEMPLATE_DOC_ID`.

## C) Incoming Webhook (Google Chat)

1. Abra o Google Chat (web) e entre no **espaço** de destino.
2. Nome do espaço (topo) → seta para baixo → **Apps e integrações**.
3. **Gerenciar webhooks** (ou **Adicionar webhooks**).
4. Nome: ex. `Post Mortems` → **Salvar**.
5. Copie a URL gerada e cole em `GCHAT_WEBHOOK_URL` no `.env`.

> Se "Gerenciar webhooks" não aparecer, o admin do Workspace desativou webhooks de
> entrada nesse espaço. Peça liberação ou troque o canal de entrega.

## D) Teams (opcional)

Não há conector de envio para o Teams. Para notificar um canal do Teams, crie um
**Incoming Webhook** do canal e coloque a URL em `TEAMS_WEBHOOK_URL`. Sem ela, o
`notify.py` simplesmente pula o Teams.

---

## Teste rápido (só a geração do .docx, sem credenciais)

```bash
cd scripts && npm install docx && cd ..
node scripts/build_postmortem.js scripts/content.example.json /tmp/pm.docx
```

Sucesso = um `.docx` em `/tmp/pm.docx`. Para o fluxo completo (Drive + Chat), siga
os passos 5 e 6 do `SKILL.md` com o `.env` carregado.
