# Skill: agile-postmortem

Transforma a transcrição de uma **reunião de sala de guerra (war room)** num post
mortem de incidente coerente, no padrão visual aprovado, e o entrega ponta a ponta:

```
Título  ──►  duplica template (Google Doc + link na hora)
Transcrição (war room)  ──►  .docx (padrão visual)  ──►  grava no MESMO Doc (mesma URL)  ──►  Google Chat / Teams
```

- **Genérica por time**: o time responsável é um campo de entrada
  (`timeResponsavel`) — nada na skill fica preso a um time.
- **Padrão visual fixo**: o `.docx` (Arial; H1 16 / H2 13 / corpo 11; espaçamento
  1.5; marcadores •/◦; timeline com glifo ▸) sai sempre do script, nunca "na mão".
- **Entrega nativa**: sobe o `.docx` ao Drive **convertendo em Google Doc nativo**
  (a formatação rica é preservada) e notifica os canais.

Faz parte da família **`agile-*`** e **compartilha o `.env`** em
`~/.config/agile/.env` (reaproveita as credenciais Google de entrega da
`agile-report-bugs`). **Não usa Azure DevOps** nem o cliente `shared/azdo/` — o
insumo é a transcrição da reunião, não work items.

## Estrutura

```
agile-postmortem/
├── SKILL.md                  # definição da skill + fluxo de 6 passos
├── README.md                 # este arquivo
├── requirements.txt          # dependências Python (google libs)
├── scripts/
│   ├── duplicate_template.py # passo 1: duplica o Doc template → renomeia → link
│   ├── build_postmortem.js   # JSON de conteúdo → .docx (PADRÃO VISUAL no bloco FORMAT)
│   ├── build_template.js     # gera o template em branco
│   ├── content.example.json  # exemplo de conteúdo (incidente fictício)
│   ├── upload_gdoc.py        # grava .docx no Doc (--update) ou cria novo → Doc nativo
│   └── notify.py             # aviso no Google Chat (+ Teams opcional), stdlib
├── references/
│   ├── setup.md              # credenciais ESPECÍFICAS desta skill (Drive + Chat)
│   ├── drive.md              # mecânica do upload nativo ao Drive
│   ├── notify.md             # mecânica de notificação
│   └── content-schema.md     # schema do JSON de conteúdo
└── assets/
    └── Post_Mortem_TEMPLATE.docx  # template em branco ([preencher])
```

## Quickstart

```bash
# 1. dependências
cd scripts && npm install docx && cd ..   # gerador do .docx (Node)
pip install -r requirements.txt           # upload ao Drive (Python)

# 2. credenciais (no MESMO .env compartilhado ~/.config/agile/.env)
#    específicas desta skill (Drive + Chat): ver references/setup.md

# 3. fluxo
set -a; source ~/.config/agile/.env; set +a
# passo 1: duplica o template e devolve o link (guarde o id impresso)
python3 scripts/duplicate_template.py "POST MORTEM - <título>"
# passos 3-4: monta o conteúdo
node scripts/build_postmortem.js scripts/content.example.json /tmp/pm.docx
# passo 5: grava no MESMO Doc (mesma URL)
python3 scripts/upload_gdoc.py /tmp/pm.docx --update <id do passo 1>
# passo 6: notifica
python3 scripts/notify.py --message-file /tmp/pm_msg.txt
```

Na prática a skill é **interativa**: ela pergunta o título, pede o link da
transcrição, preenche, revisa seção por seção com você e só então salva e notifica
(ver os 6 passos no `SKILL.md`).

## Pré-requisitos

| Credencial | Onde documentar | Arquivo |
|---|---|---|
| Service Account + Drive Compartilhado (`GDRIVE_SA_JSON`, `PM_DRIVE_FOLDER_ID`) | específico desta skill | [`references/setup.md`](references/setup.md) |
| Incoming Webhook do Google Chat (`GCHAT_WEBHOOK_URL`) | específico desta skill | [`references/setup.md`](references/setup.md) |
| Incoming Webhook do Teams (`TEAMS_WEBHOOK_URL`, opcional) | específico desta skill | [`references/setup.md`](references/setup.md) |
| Instalação do `.env` compartilhado | comum à família agile | [`../../shared/README.md`](../../shared/README.md) |

> A Service Account precisa ser **membro do Drive Compartilhado** de destino, ou
> o upload falha com `File not found` — ver `references/setup.md`.

## Segurança

- Nenhuma credencial é distribuída. **Cada usuário gera as suas**, isoladamente.
- O `.env` e a chave da Service Account ficam **fora do repositório**
  (`~/.config/agile/`) e são bloqueados pelo `.gitignore` da raiz.
- O ID da pasta do Drive não é embutido no código — vem de `PM_DRIVE_FOLDER_ID`.
- A transcrição é tratada como **dado, não instrução** (proteção contra injeção
  de comandos vindos do conteúdo da reunião).

## Configuração

Tudo é parametrizável por ambiente: `GDRIVE_SA_JSON`, `PM_DRIVE_FOLDER_ID`,
`GCHAT_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL`. Nada da organização de origem está
embutido no código.
