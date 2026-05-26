# Skill: agile-report-bugs

Relatório de bugs abertos do **Azure DevOps**, ponta a ponta:

```
Azure DevOps  ──►  PDF (por time, flags)  ──►  Google Drive  ──►  Google Chat
```

- **PDF** em A4 paisagem: sumário geral, quebra por time (AreaPath), flag de
  tempo aberto (🔴 ALTA > 60d · 🟡 MÉDIA 30–60d · 🟢 BAIXA < 30d), IDs
  clicáveis para o work item.
- **Coleta rápida**: 2 chamadas REST (WIQL + `workitemsbatch`) via o cliente
  compartilhado `azdo.client`, sem percorrer item a item.
- **Entrega**: arquiva o PDF num Drive Compartilhado (link público de leitura)
  e posta um resumo + link num espaço do Google Chat.

Faz parte da família **`agile-*`** — todas as skills aqui compartilham o
cliente `shared/azdo/` e o `.env` em `~/.config/agile/.env`.

## Estrutura

```
agile-report-bugs/
├── SKILL.md                 # definição da skill + fluxo de orquestração
├── README.md                # este arquivo
├── requirements.txt         # dependências Python (reportlab, google libs)
├── scripts/
│   ├── build_report.py      # Azure DevOps REST → PDF (usa shared/azdo/client.py)
│   ├── deliver.py           # PDF → Google Drive (Service Account, headless)
│   ├── post_gchat.py        # resumo + link → Google Chat (webhook)
│   └── run_weekly.sh        # orquestra as 3 etapas (p/ launchd/cron)
└── references/
    └── setup.md             # credenciais ESPECÍFICAS desta skill (Chat + Drive)
```

> A autenticação e as chamadas REST do Azure DevOps **não vivem aqui** — ficam
> no cliente compartilhado [`../../shared/azdo/client.py`](../../shared/azdo/client.py).

## Quickstart

```bash
# 1. dependências
pip install -r requirements.txt

# 2. credenciais
#    a) comuns (PAT, org, projeto): ver ../../shared/README.md
#    b) específicas desta skill (Google Chat + Drive): ver references/setup.md
#    Tudo no MESMO arquivo compartilhado ~/.config/agile/.env

# 3. rodar
set -a; source ~/.config/agile/.env; set +a
python3 scripts/build_report.py --out-dir /tmp        # gera o PDF
# depois: deliver.py (Drive) e post_gchat.py (Chat) — ver SKILL.md
```

## Pré-requisitos

| Credencial | Onde documentar | Arquivo |
|---|---|---|
| PAT, organização, projeto (Azure DevOps) | **comum à família agile** | [`../../shared/README.md`](../../shared/README.md) |
| Incoming Webhook do Google Chat | específico desta skill | [`references/setup.md`](references/setup.md) |
| Service Account + Drive Compartilhado | específico desta skill | [`references/setup.md`](references/setup.md) |

## Segurança

- Nenhuma credencial é distribuída. **Cada usuário gera as suas**, isoladamente.
- O `.env` e a chave da Service Account ficam **fora do repositório**
  (`~/.config/agile/`) e são bloqueados pelo `.gitignore` da raiz.
- O PAT usa escopo mínimo (**Work Items: Read**).

## Configuração

Tudo é parametrizável por ambiente: `AZDO_ORG`, `AZDO_PROJECT`, `AZDO_PAT`,
`GCHAT_WEBHOOK_URL`, `GDRIVE_SA_JSON`, `GDRIVE_FOLDER_ID`. Nada da organização
de origem está embutido no código.
