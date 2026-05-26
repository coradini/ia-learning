# agentes-agilidade

Skills de **gestão de fluxo ágil** sobre o **Azure DevOps** — inspeção de
upstream (épicos, user stories), downstream e métricas de fluxo. Construídas
para rodar no Claude Code, de forma interativa ou agendada.

## Estrutura

```
agentes-agilidade/
├── shared/                  # infra COMUM a todas as skills agile-*
│   ├── azdo/client.py       # cliente REST do Azure DevOps (auth PAT, get/post/patch)
│   ├── .env.example         # template do .env único da família
│   └── README.md            # pré-requisitos comuns (PAT + .env)
└── skills/
    ├── agile-report-bugs/   # bugs abertos → PDF → Google Drive → Google Chat
    ├── agile-upstream/      # saúde dos épicos (cor por movimentação) → PDF (por time) → Drive → Chat
    └── agile-postmortem/    # transcrição de war room → Google Doc → Chat/Teams
```

## Convenção: prefixo `agile-`

**Toda skill que compartilha a infra de `shared/` usa o prefixo `agile-`**
(ex.: `agile-report-bugs`, `agile-flow-health`, `agile-upstream-tree`). O
prefixo é o contrato visível de que a skill:

- importa o cliente `shared/azdo/client.py` (não reescreve autenticação/REST);
- lê o `.env` compartilhado em `~/.config/agile/.env`.

Cada skill continua **documentada e executável de forma independente** (tem seu
`SKILL.md`, `README.md` e `references/`), mas a família AzDO divide um cliente e
um `.env` comuns. O prefixo `agile-` indica, no mínimo, que a skill **compartilha
o `.env`** da família (`~/.config/agile/.env`); a maioria também usa o cliente
`shared/azdo/`. Exceção: [`agile-postmortem`](skills/agile-postmortem/) leva o
prefixo por compartilhar as credenciais de entrega Google (Drive/Chat), mas **não
usa Azure DevOps** — seu insumo é a transcrição de uma reunião, não work items.

## Skills

| Skill | O que faz | Motor |
|-------|-----------|-------|
| [`agile-report-bugs`](skills/agile-report-bugs/) | Compila bugs abertos do Azure DevOps em PDF (por time, com flags de SLA), arquiva no Google Drive e posta o link num espaço do Google Chat. | REST + PAT (agendável) |
| [`agile-upstream`](skills/agile-upstream/) | Visão gerencial da saúde dos épicos por time, em PDF, classificando cada épico por cor de movimentação (verde/laranja/vermelho/roxo) — Drive + Chat; roda agendada ou avulsa. | REST + PAT (agendável) |
| [`agile-postmortem`](skills/agile-postmortem/) | Transforma a transcrição de uma reunião de war room em post mortem de incidente no padrão visual, salva como Google Doc nativo no Drive e notifica Chat/Teams. | Interativo (Node + Drive API) |

## Como começar

1. Pré-requisitos comuns (criar PAT, instalar o `.env`):
   **[`shared/README.md`](shared/README.md)**.
2. Pré-requisitos específicos + uso de cada skill: o `README.md` e o
   `references/setup.md` da skill. Comece por
   [`skills/agile-report-bugs/README.md`](skills/agile-report-bugs/README.md).

## Segurança

Este repositório é projetado para ser **público**. Nenhum segredo é versionado:

- Credenciais ficam num `.env` **compartilhado fora do repo**
  (`~/.config/agile/.env`), criado por cada usuário a partir de
  `shared/.env.example`.
- Chaves (Service Account, tokens) e PDFs gerados (que contêm dados reais) são
  bloqueados pelo `.gitignore`.
- Os guias ensinam o leitor a gerar **as próprias credenciais**, isoladamente.
- O PAT usa escopo mínimo: **Read** por padrão; **Read & Write** só quando uma
  skill de escrita exigir.

## Changelog

Mudanças relevantes ficam em [`CHANGELOG.md`](CHANGELOG.md)
([Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) +
[Semantic Versioning](https://semver.org/lang/pt-BR/)). **Toda mudança recebe
uma nota explicando onde foi feita e por quê** — o "o quê" fica no diff.
