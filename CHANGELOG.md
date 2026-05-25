# Changelog

Todas as mudanças relevantes deste repositório são documentadas aqui — **um
único changelog global**, cobrindo qualquer parte do repo (skills, raiz,
automações, documentação, configuração).

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e
este repositório adere a [Semantic Versioning](https://semver.org/lang/pt-BR/).

## Política de registro

**Toda mudança no repositório — seja onde for — recebe uma nota neste
changelog.** Cada nota deve deixar claro:

- **Onde**: qual skill, arquivo ou área foi afetada (ex.: `skills/report-bugs/`,
  raiz, `README.md`).
- **Por quê**: a motivação da mudança, não só o que mudou — o "o quê" o diff já
  conta; o changelog guarda o "porquê".

As entradas são agrupadas por versão semântica e por tipo (`Added`, `Changed`,
`Fixed`, `Removed`, `Security`, `Deprecated`).

## [1.1.0] - 2026-05-25

### Added

- **`CHANGELOG.md` (raiz)**: changelog global do repositório, no formato Keep a
  Changelog + Semantic Versioning. *Onde:* raiz do repo. *Por quê:* o repositório
  hospeda múltiplas skills e automações; um histórico único e versionado torna
  rastreável o que mudou, onde e com que motivação, sem depender de ler o
  `git log`.
- **Política de registro de mudanças**: convenção de que qualquer alteração no
  repo gera uma nota no changelog explicando onde e por quê. *Onde:* documentada
  na seção "Política de registro" deste arquivo e referenciada no `README.md`.
  *Por quê:* fixar a premissa como regra do repositório para que o changelog
  continue completo e útil ao longo do tempo.

## [1.0.0] - 2026-05-18

### Added

- **Skill `report-bugs`**: relatório de bugs abertos do **Azure DevOps** de
  ponta a ponta — **Azure DevOps → PDF → Google Drive → Google Chat**. *Onde:*
  `skills/report-bugs/`. *Por quê:* automatizar a compilação semanal do status
  de bugs (antes feita manualmente, item a item) e entregá-la pronta no canal do
  time.
  - `scripts/build_report.py`: coleta via REST em **2 chamadas** (WIQL +
    `workitemsbatch`, sem fan-out) e gera PDF A4 paisagem com sumário geral,
    quebra por time (AreaPath), IDs clicáveis e flags de tempo aberto
    (🔴 ALTA > 60d · 🟡 MÉDIA 30–60d · 🟢 BAIXA < 30d). Imprime um JSON de
    resumo na última linha do stdout.
  - `scripts/deliver.py`: upload headless do PDF para um Drive Compartilhado via
    Service Account, com link público de leitura.
  - `scripts/post_gchat.py`: posta resumo + link clicável num espaço do Google
    Chat via Incoming Webhook.
  - `references/setup.md`, `requirements.txt`, `.env.example`: guia de
    credenciais, dependências e template de configuração.

### Security

- Nenhuma credencial é versionada — cada usuário gera as suas isoladamente; o
  `.env` e a chave da Service Account ficam fora do repo (`.gitignore`). O PAT
  usa escopo mínimo (**Work Items: Read**).

[1.1.0]: https://github.com/coradini/aprendizados-ia/compare/b7bcb22d555f284973f19e7671c25b6a2d771a2e...main
[1.0.0]: https://github.com/coradini/aprendizados-ia/commit/b7bcb22d555f284973f19e7671c25b6a2d771a2e
