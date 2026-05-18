# Skill: report-bugs

Relatório de bugs abertos do **Azure DevOps**, ponta a ponta:

```
Azure DevOps  ──►  PDF (por time, flags)  ──►  Google Drive  ──►  Google Chat
```

- **PDF** em A4 paisagem: sumário geral, quebra por time (AreaPath), flag de
  tempo aberto (🔴 ALTA > 60d · 🟡 MÉDIA 30–60d · 🟢 BAIXA < 30d), IDs
  clicáveis para o work item.
- **Coleta rápida**: 2 chamadas REST (WIQL + `workitemsbatch`), sem percorrer
  item a item.
- **Entrega**: arquiva o PDF num Drive Compartilhado (link público de leitura)
  e posta um resumo + link num espaço do Google Chat.

## Estrutura

```
report-bugs/
├── SKILL.md                 # definição da skill + fluxo de orquestração
├── README.md                # este arquivo
├── requirements.txt         # dependências Python
├── .env.example             # template de credenciais (copie p/ fora do repo)
├── scripts/
│   ├── build_report.py      # Azure DevOps REST → PDF (+ resumo JSON)
│   ├── deliver.py           # PDF → Google Drive (Service Account, headless)
│   └── post_gchat.py        # resumo + link → Google Chat (webhook)
└── references/
    └── setup.md             # passo a passo p/ criar SUAS credenciais
```

## Quickstart

```bash
# 1. dependências
pip install -r requirements.txt

# 2. credenciais (você cria as suas — ver references/setup.md)
mkdir -p ~/.config/report-bugs
cp .env.example ~/.config/report-bugs/.env
chmod 600 ~/.config/report-bugs/.env
$EDITOR ~/.config/report-bugs/.env

# 3. rodar
set -a; source ~/.config/report-bugs/.env; set +a
python3 scripts/build_report.py --out-dir /tmp        # gera o PDF
# depois: deliver.py (Drive) e post_gchat.py (Chat) — ver SKILL.md
```

## Segurança

- Nenhuma credencial é distribuída. **Cada usuário gera as suas**, isoladamente
  (ver `references/setup.md`).
- O `.env` e a chave da Service Account ficam **fora do repositório** e são
  bloqueados pelo `.gitignore` da raiz.
- O PAT usa escopo mínimo (**Work Items: Read**).

## Configuração

Tudo é parametrizável por ambiente: `AZDO_ORG`, `AZDO_PROJECT`, `AZDO_PAT`,
`GCHAT_WEBHOOK_URL`, `GDRIVE_SA_JSON`, `GDRIVE_FOLDER_ID`. Nada da organização
de origem está embutido no código.
