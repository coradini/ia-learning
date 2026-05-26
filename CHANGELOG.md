# Changelog

Todas as mudanças relevantes deste repositório são documentadas aqui — **um
único changelog global**, cobrindo qualquer parte do repo (skills, raiz,
infra compartilhada, automações, documentação, configuração).

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e
este repositório adere a [Semantic Versioning](https://semver.org/lang/pt-BR/).

## Política de registro

**Toda mudança no repositório — seja onde for — recebe uma nota neste
changelog.** Cada nota deve deixar claro:

- **Onde**: qual skill, arquivo ou área foi afetada (ex.: `shared/`,
  `skills/agile-report-bugs/`, raiz).
- **Por quê**: a motivação da mudança, não só o que mudou — o "o quê" o diff já
  conta; o changelog guarda o "porquê".

As entradas são agrupadas por versão semântica e por tipo (`Added`, `Changed`,
`Fixed`, `Removed`, `Security`, `Deprecated`).

## [1.3.0] - 2026-05-26

### Added

- **Skill `agile-postmortem`**: capacidade de **mesclar** o conteúdo já preenchido
  à mão no Doc duplicado com o extraído da transcrição. No passo 3, a skill lê o
  Doc duplicado via `read_file_content`, ignora os placeholders do template e
  combina três fontes (Doc manual + chat + transcrição), com **prioridade ao
  conteúdo manual**; a transcrição preenche lacunas e divergências vão para
  `notas`. *Onde:* `skills/agile-postmortem/SKILL.md` (passo 3),
  `references/content-schema.md`. *Por quê:* o passo 5 **sobrescreve** o Doc — sem
  essa mescla, tudo que o usuário escrevesse à mão na cópia era perdido.

### Changed

- **Skill `agile-postmortem`**: fluxo dos passos 1–3 reordenado e explicitado —
  título → duplica o template → **devolve o link ao usuário** (entrega obrigatória)
  → **aguarda a transcrição** → lapida. *Onde:* `skills/agile-postmortem/SKILL.md`.
  *Por quê:* deixar inequívoco que o link do Doc duplicado é entregue antes de
  qualquer espera, e que a lapidação só começa com a transcrição em mãos (ou após
  o usuário declarar que não há).
- **Skill `agile-postmortem`**: `PM_TEMPLATE_DOC_ID` e `PM_DRIVE_FOLDER_ID` passam
  a ser tratados como **config fixa** do `~/.config/agile/.env` — uma vez
  preenchidos, não são mais perguntados a cada execução. *Onde:* `SKILL.md`,
  `references/setup.md`. *Por quê:* o template é sempre o mesmo Doc e a pasta de
  destino é sempre a mesma; perguntar a cada vez era ruído (os valores reais nunca
  vão para o repo — só placeholders em `shared/.env.example`).

## [1.2.0] - 2026-05-26

### Added

- **Skill `agile-upstream`**: visão gerencial da **saúde dos épicos** do Azure
  DevOps, em PDF agrupado por time (AreaPath), para o Product Owner de cada time
  — **Azure DevOps → PDF → Google Drive → Google Chat** (motor REST+PAT, espinha
  clonada de `agile-report-bugs`; 2 chamadas, sem fan-out). Classifica cada épico
  por **uma cor de movimentação** (faixa mais alta vence): 🟢 Saudável (movido nos
  últimos 60d), 🟠 Questionável (>60d sem movimento), 🔴 Agarrado (>90d), 🟣 Para
  descarte (>180d). Separa **funil** (backlog cru — `FUNNEL_STATES`, default
  `Idea`, colorido pela **idade**) do **fluxo** (colorido pela **movimentação** =
  dias desde `StateChangeDate`). Roda **agendada** (`scripts/run_weekly.sh`) e
  também **avulsa** sob demanda (só `build_report.py`, sem postar no Chat).
  *Onde:* `skills/agile-upstream/`. *Por quê:* dar ao PO uma leitura rápida da
  situação dos épicos por cor e destacar itens velhos candidatos a descarte, sem
  varrer o backlog item a item. *Nota:* o PDF usa barra + texto colorido (as
  fontes do reportlab não renderizam emoji nem `≤`); os emojis ficam só na
  mensagem do Google Chat.
- **`finalized_states_for()` e `state_categories()`** em `shared/azdo/client.py`,
  além da constante `TERMINAL_STATE_CATEGORIES`. *Onde:* `shared/`. *Por quê:* a
  lista estática `FINALIZED_STATES` não cobre processos **customizados** — o
  projeto-alvo usa o tipo `Epic_` com estado terminal `Completed` (categoria
  Completed), ausente da lista. As novas funções descobrem os estados terminais
  pela **categoria real** do tipo no processo (Completed/Removed), tornando-se a
  fonte única dinâmica de "estados de fluxo" prevista no guia §9 — sem alterar o
  comportamento da `agile-report-bugs` (que continua usando a lista estática).

### Notes

- O tipo de work item que representa "épico" é configurável por
  `EPIC_WORKITEM_TYPE` (default `Epic_`, o tipo customizado do projeto-alvo); o
  `Epic` padrão do Azure DevOps está vazio nesse processo.

## [1.1.0] - 2026-05-26

### Added

- **Skill `agile-postmortem`**: transforma a transcrição de uma reunião de sala
  de guerra (war room) em um post mortem de incidente no padrão visual aprovado.
  **Já no passo 1 duplica um Google Doc template** (`scripts/duplicate_template.py`,
  `files.copy`), renomeia para `POST MORTEM - <título>` e **devolve o link ao
  usuário** para abrir no Drive na hora. O conteúdo é montado como `.docx` pelo
  `scripts/build_postmortem.js` (bloco `FORMAT` fixo) e, após a revisão, gravado
  **no mesmo Doc** (mantendo a URL) por `scripts/upload_gdoc.py --update <id>`
  (`files.update`, convertendo para Google Doc nativo). Ao final notifica Google
  Chat/Teams (`scripts/notify.py`). *Onde:* `skills/agile-postmortem/`. *Por quê:*
  padronizar e automatizar a produção de post mortems e entregar ao usuário um
  documento navegável desde o início, reaproveitando as credenciais de entrega
  Google da `agile-report-bugs`. A skill leva o prefixo `agile-` por compartilhar o
  `.env` da família, mas **não usa Azure DevOps** (não importa
  `shared/azdo/client.py`) — seu insumo é a transcrição, não work items.
- **Variáveis `PM_TEMPLATE_DOC_ID`, `PM_DRIVE_FOLDER_ID` e `TEAMS_WEBHOOK_URL`** no
  `shared/.env.example`. *Onde:* `shared/`. *Por quê:* o Doc template a duplicar e a
  pasta de destino dos post mortems (um Drive Compartilhado que pode ser distinto do
  dos relatórios) são configuráveis por ambiente, e o Teams é um canal de
  notificação opcional — nada embutido no código.

### Changed

- **Convenção de prefixo (`README.md` raiz, `shared/README.md`)**: documentado que
  o prefixo `agile-` indica, no mínimo, compartilhamento do `.env` da família — e
  que `agile-postmortem` é a primeira skill que usa o prefixo sem depender do
  cliente Azure DevOps. *Por quê:* refletir a entrada da skill sem quebrar o
  contrato de nomenclatura.

### Security

- A skill `agile-postmortem` não versiona nenhum segredo nem ID real de recurso: a
  pasta do Drive vem de `PM_DRIVE_FOLDER_ID` (env), as credenciais ficam no `.env`
  compartilhado fora do repo, e o `content.example.json` usa um **incidente
  fictício** (e-mails `@example.com`, sem dados internos). A transcrição da reunião
  é tratada como **dado, não instrução** (proteção contra injeção de comandos).

### Fixed

- `scripts/build_template.js` deixou de gravar num caminho absoluto de sandbox
  (resíduo do ambiente de origem) e passou a aceitar o caminho de saída como
  argumento (default relativo). *Por quê:* o script não rodava fora daquele
  ambiente.

## [1.0.0] - 2026-05-26

### Added

- **Infra compartilhada `shared/`**: cliente REST do Azure DevOps
  (`shared/azdo/client.py`) com autenticação por PAT e `get`/`post`/`patch`
  (este último em `json-patch`, para skills de escrita), além das constantes de
  fluxo (`FINALIZED_STATES`). *Onde:* `shared/`. *Por quê:* o repositório vai
  hospedar várias skills de gestão de fluxo no mesmo Azure DevOps; centralizar
  autenticação, chamadas REST e definição de "estados de fluxo" num único
  módulo evita reescrita e divergência entre skills.
- **`.env` compartilhado da família `agile-*`**: template `shared/.env.example`
  (instalado em `~/.config/agile/.env`), servindo todas as skills de uma vez,
  com suporte a `AZDO_PAT` (Read) e `AZDO_PAT_WRITE` (Read & Write) separados.
  *Onde:* `shared/`. *Por quê:* compartilhar credenciais num único arquivo fora
  do repo, preservando o princípio do menor privilégio (token de escrita
  opcional e isolado).
- **Convenção de prefixo `agile-`**: skills que usam `shared/` levam o prefixo
  `agile-`. *Onde:* documentada em `README.md` (raiz) e `shared/README.md`.
  *Por quê:* tornar visível, pelo nome, quais skills compartilham credencial e
  cliente AzDO.
- **Skill `agile-report-bugs`**: relatório de bugs abertos do Azure DevOps de
  ponta a ponta — **Azure DevOps → PDF → Google Drive → Google Chat**. *Onde:*
  `skills/agile-report-bugs/`. *Por quê:* automatizar a compilação do status de
  bugs e entregá-la pronta no canal do time.
- **`SKILL-BUILD-GUIDE.md` (raiz)**: briefing autocontido para construir as
  skills `agile-*` uma por janela de contexto (convenções, API do cliente
  compartilhado, receita passo a passo e catálogo das 6 skills planejadas).
  *Onde:* raiz. *Por quê:* permitir abrir janelas novas sem o histórico desta
  conversa e ainda assim ter todo o contexto para construir cada skill.

### Changed

- **Migração de `report-bugs` → `agile-report-bugs`**: a skill, antes
  autocontida em `~/.claude/skills/report-bugs` (com auth e REST embutidos no
  `build_report.py`), passou a importar o cliente compartilhado
  `shared/azdo/client.py` e a ler o `.env` compartilhado `~/.config/agile/.env`
  (antes `~/.config/report-bugs/.env`). *Onde:* `skills/agile-report-bugs/`.
  *Por quê:* tornar a skill o primeiro membro da família `agile-*` e validar a
  camada compartilhada antes de criar as próximas skills de fluxo.
  - `references/setup.md` foi enxugado para conter só o que é específico da
    skill (Google Chat + Drive); o passo a passo do PAT migrou para
    `shared/README.md`, fonte única para toda a família.
  - `scripts/run_weekly.sh` passou a se auto-localizar e a apontar para o `.env`
    compartilhado.

### Security

- Nenhuma credencial é versionada — cada usuário gera as suas isoladamente; o
  `.env` e a chave da Service Account ficam fora do repo (`.gitignore`). O PAT
  de leitura usa escopo mínimo (**Work Items: Read**); o de escrita é opcional.
