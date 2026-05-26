# Guia de construção de skills `agile-*`

> **Para que serve este arquivo.** É o briefing autocontido para construir as
> skills deste repositório **uma de cada vez, em janelas de contexto separadas**.
> Numa janela nova, dentro desta pasta, diga algo como:
>
> > "Leia `SKILL-BUILD-GUIDE.md` e construa a skill **`agile-flow-health`**
> > seguindo o guia. Pare para eu validar antes de criar a próxima."
>
> A janela nova não terá o histórico desta conversa — este documento é a única
> fonte de contexto. Construa **uma skill por janela** para não estourar
> contexto e manter cada PR/entrega revisável.

---

## 1. O que é este repositório

Família de skills **`agile-*`** para **gestão de fluxo ágil sobre o Azure
DevOps** — inspeção de upstream (épicos, user stories), downstream e métricas
de fluxo. Roda no **Claude Code** (decisão fechada: **não** Cowork, pois o
consumidor é técnico). Arquitetura **híbrida**:

- **Motor MCP** (`azureDevOps`) → skills **interativas/ad-hoc** (navegar árvore,
  inspecionar dependências). Menos código; o modelo dirige as chamadas.
- **Motor REST+PAT** → skills **agendadas/recorrentes** que produzem artefato
  (PDF, post em Chat). Scripts Python headless usando o cliente compartilhado.

A skill `agile-report-bugs` (já pronta) é o **modelo de referência** do motor
REST+PAT. Leia os arquivos dela antes de construir uma irmã do mesmo tipo.

## 2. Mapa do repositório

```
agentes-agilidade/
├── README.md                # visão geral + convenção de prefixo
├── CHANGELOG.md             # política: toda mudança vira nota (onde + porquê)
├── .gitignore               # bloqueia .env, *-key.json, *.pdf
├── SKILL-BUILD-GUIDE.md     # ◄ este arquivo
├── shared/
│   ├── azdo/client.py       # cliente REST AzDO (auth + get/post/patch + constantes)
│   ├── .env.example         # template do .env ÚNICO da família
│   └── README.md            # pré-requisitos COMUNS (PAT, instalar .env)
└── skills/
    └── agile-report-bugs/   # referência do motor REST+PAT
        ├── SKILL.md         # frontmatter (name/description) + fluxo
        ├── README.md        # tutorial da skill
        ├── requirements.txt # deps pesadas (reportlab, google libs)
        ├── scripts/         # build_report.py, deliver.py, post_gchat.py, run_weekly.sh
        └── references/setup.md  # só credenciais ESPECÍFICAS da skill
```

## 3. Regras inegociáveis

1. **Prefixo `agile-`** para toda skill que usa `shared/`. O prefixo é o
   contrato de "compartilha cliente + `.env`".
2. **Não reescrever autenticação nem chamadas REST** — importe de
   `shared/azdo/client.py`.
3. **Zero segredo no repo** (ele é projetado para ser público). Credenciais só
   em `~/.config/agile/.env` (fora do repo). Nunca peça segredo no chat, nunca
   escreva valores reais em `.env.example`. Não commitar PDFs gerados (têm dados
   reais) — já cobertos pelo `.gitignore`.
4. **Menor privilégio**: leitura usa `AZDO_PAT` (Work Items: Read). Só skills
   que **criam/editam** work items usam `AZDO_PAT_WRITE` (Read & Write). As 6
   skills do catálogo abaixo são **todas de leitura** → não precisam de write.
5. **Fonte única de "estados de fluxo"**: `FINALIZED_STATES` vive no
   `client.py`. Não redefina por skill.
6. **CHANGELOG**: toda skill nova/alterada recebe nota em `CHANGELOG.md`
   dizendo **onde** e **por quê** (bump SemVer).
7. **Validar antes de concluir**: rode a skill de verdade (ver §7). Não declare
   pronto sem ver a saída real.

## 4. API do cliente compartilhado (`azdo.client`)

Stdlib pura, sem dependências. Importe com este bootstrap no topo de cada
script (torna o `shared/` importável de qualquer diretório, sem `PYTHONPATH`):

```python
import sys
from pathlib import Path
# scripts -> agile-<skill> -> skills -> <repo>/shared
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from azdo.client import get, post, patch, require_env, API_VERSION, FINALIZED_STATES
```

Superfície:

| Símbolo | Assinatura | Uso |
|---|---|---|
| `require_env(name)` | `(str) -> str` | Lê env obrigatória ou aborta com instrução clara. |
| `get(url, pat)` | `-> dict` | GET autenticado (ex.: `workItems/{id}/updates`, relations). |
| `post(url, payload, pat)` | `-> dict` | POST JSON (ex.: WIQL, `workitemsbatch`). |
| `patch(url, ops, pat)` | `-> dict` | PATCH `json-patch` (criar/editar work item — só skills de escrita). |
| `API_VERSION` | `"7.1"` | Use na querystring `?api-version=`. |
| `FINALIZED_STATES` | `list[str]` | `Closed, Resolved, Done, Removed, Discarded, Canceled`. |

Erros HTTP já viram `SystemExit` com mensagem orientando o ajuste (PAT/escopo).

### Endpoints AzDO úteis (org=`AZDO_ORG`, project=`AZDO_PROJECT`)

- **WIQL** (consulta por IDs): `POST https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.1`
  com `{"query": "<WIQL>"}`.
- **Batch de campos** (≤200 ids): `POST https://dev.azure.com/{org}/_apis/wit/workitemsbatch?api-version=7.1`
  com `{"ids":[...], "fields":[...]}`.
- **Item único + relações**: `GET .../_apis/wit/workitems/{id}?$expand=relations&api-version=7.1`.
- **Histórico de transições**: `GET .../_apis/wit/workItems/{id}/updates?api-version=7.1`.
- **Boards/colunas**: `GET .../{project}/{team}/_apis/work/boards/{board}?api-version=7.1`.

### Motor MCP (alternativa para skills interativas)

Quando a skill é interativa, o `SKILL.md` pode instruir o modelo a usar
diretamente as ferramentas do MCP `azureDevOps` (ex.: `list_work_items`,
`get_work_item`, `search_work_items`, `manage_work_item_link`,
`list_pull_requests`) — sem escrever scripts. Use o cliente REST quando a skill
precisar rodar **headless/agendada**; use o MCP quando o **modelo** dirige a
análise ao vivo.

## 5. Anatomia de uma skill

**Skill de motor REST+PAT** (agendável) — espelha `agile-report-bugs`:
```
skills/agile-<nome>/
├── SKILL.md            # frontmatter name+description; fluxo de execução
├── README.md           # o que faz + quickstart + tabela de pré-requisitos
├── requirements.txt    # só deps pesadas (vazio se for stdlib pura)
├── scripts/*.py        # bootstrap + from azdo.client import ...
└── references/setup.md  # só credenciais específicas (aponta shared/README p/ PAT)
```

**Skill de motor MCP** (interativa) — pode dispensar `scripts/`:
```
skills/agile-<nome>/
├── SKILL.md            # frontmatter + passos que orquestram tools do MCP azureDevOps
├── README.md           # o que faz + exemplos de invocação
└── references/setup.md  # (se houver algo além do PAT comum)
```

### Frontmatter do `SKILL.md` (obrigatório)
```yaml
---
name: agile-<nome>
description: >-
  <1 frase do que faz> + gatilhos em PT ("...", "...") que o usuário usaria.
---
```
A `description` é o que decide o disparo da skill — seja específico nos gatilhos.

### Instalação para o Claude Code carregar
Cada skill é carregada de `~/.claude/skills/<name>/`. O repo é a fonte da
verdade; instale via symlink:
```bash
ln -sfn "<repo>/skills/agile-<nome>" ~/.claude/skills/agile-<nome>
```
(O caminho do repo tem espaços — sempre entre aspas.)

## 6. Receita passo a passo (numa janela nova)

1. **Escolha UMA skill** do catálogo (§8). Confirme com o usuário se há dúvida
   de escopo.
2. **Releia a referência**: `shared/README.md`, `shared/azdo/client.py` e, se
   for motor REST+PAT, os `scripts/` de `agile-report-bugs`.
3. **Crie a pasta** `skills/agile-<nome>/` com a anatomia da §5.
4. **Implemente**:
   - REST+PAT → scripts com bootstrap + `azdo.client`; saída com **JSON na
     última linha do stdout** (contrato de composição entre etapas).
   - MCP → `SKILL.md` que orquestra as tools; formate a saída de forma legível.
5. **Variáveis novas** (se houver) → acrescente ao `shared/.env.example` com
   placeholder e documente em `references/setup.md`. Nenhuma das skills do
   catálogo precisa de variável nova além das já existentes.
6. **Docs**: `README.md` da skill + `references/setup.md` (só o específico;
   aponte para `shared/README.md` para o PAT).
7. **Instale** o symlink (§5) e **valide** (§7).
8. **CHANGELOG**: adicione a nota (onde + porquê) e bump SemVer.
9. **Pare e peça validação** do usuário antes da próxima skill.

## 7. Definição de pronto (validação real)

- O script/▶ a skill roda com `set -a; source ~/.config/agile/.env; set +a` e
  produz a saída esperada contra o Azure DevOps real (read-only é seguro).
- REST+PAT: imprime o JSON-resumo na última linha; artefato gerado.
- MCP: as tools retornam dados e a saída final está formatada e correta.
- Sem segredo versionado; `.gitignore` cobre o que a skill gera.
- `SKILL.md` tem frontmatter válido e gatilhos claros.
- Nota no `CHANGELOG.md`.

## 8. Catálogo de skills a construir

Todas **somente leitura** (não precisam de `AZDO_PAT_WRITE`). Ordem sugerida:
comece por uma de cada motor para validar os dois caminhos —
**`agile-upstream-tree`** (MCP) e **`agile-flow-health`** (REST+PAT).

---

### `agile-upstream-tree`  — motor: MCP (interativo)
**Pergunta:** Dado um épico/feature, como está a árvore épico→feature→US?
Quanto está decomposto? Há US órfãs (sem parent) ou épicos sem quebra?
**Dados:** hierarquia via links `System.LinkTypes.Hierarchy-Forward` (filhos) /
`-Reverse` (pai). Via MCP: `get_work_item` com relations, `list_work_items`;
ou WIQL `WorkItemLinks` (`SELECT ... FROM WorkItemLinks WHERE ... MODE (Recursive)`).
**Entrada:** ID de épico/feature (ou área/iteração).
**Saída:** árvore em markdown + métricas (% decomposto, contagem por nível, US
órfãs, épicos sem filhos).
**Notas:** começar interativo via MCP; sem artefato/entrega.

### `agile-upstream-readiness`  — motor: MCP (interativo)
**Pergunta:** Quais features/épicos estão **prontos para puxar** (refinados, com
US filhas, estimados, com critério de aceite) vs não-prontos? (Definition of Ready)
**Dados:** features em estados de entrada; contagem de US filhas; estimativa
(`Microsoft.VSTS.Scheduling.StoryPoints` ou `Microsoft.VSTS.Scheduling.Effort`);
critério de aceite (`Microsoft.VSTS.Common.AcceptanceCriteria`).
**Saída:** duas listas (pronto / não-pronto) com o motivo de cada bloqueio.
**Notas:** os critérios de "pronto" são regra de negócio — confirme com o
usuário e centralize-os no topo da skill.

### `agile-flow-health`  — motor: REST+PAT (agendável) — **clone de report-bugs**
**Pergunta:** Qual o WIP atual por estado/coluna? Há violação de limite de WIP?
Como está a distribuição?
**Dados:** WIQL contando itens em estados não-finalizados por `System.State` e
por tipo; opcionalmente colunas do board (`_apis/work/boards`).
**Saída:** PDF (reaproveite o layout de `build_report.py`) + opcional entrega
Drive/Chat (reuse `deliver.py`/`post_gchat.py`).
**Notas:** maior reuso do report-bugs; ótimo para validar o motor agendado.

### `agile-aging-wip`  — motor: híbrido (REST+PAT + ad-hoc)
**Pergunta:** Quais itens **em progresso** estão parados há muito tempo
("zumbis")? Onde está o gargalo (por coluna/estado)?
**Dados:** itens em estados de WIP + data da última mudança de estado
(`Microsoft.VSTS.Common.StateChangeDate`); dias parado = hoje − StateChangeDate.
Reaproveite a lógica de flag de tempo do `build_report.py` (60/30 dias), mas
aplicada a in-progress.
**Saída:** lista priorizada por tempo parado, agrupada por estado/time.

### `agile-cycle-lead-time`  — motor: REST+PAT (agendável)
**Pergunta:** Lead time e cycle time por time e por tipo; itens fora de SLA;
tendência.
**Dados:** **histórico de transições** — `GET .../workItems/{id}/updates`
(reconstruir entradas/saídas de estado) **ou** Analytics OData do AzDO
(agregado, mais rápido). **Decida cedo** qual fonte: updates dá controle fino e
é mais REST; OData é mais leve para agregação.
**Saída:** métricas por time/tipo + itens fora de SLA. Possível PDF/entrega.
**Notas:** mais pesada que as 2 chamadas do report-bugs — planeje paginação.

### `agile-downstream-deps`  — motor: MCP (interativo)
**Pergunta:** Quais dependências existem (links Predecessor/Successor/Related)?
O que está bloqueado e quem bloqueia quem?
**Dados:** links `System.LinkTypes.Dependency-Forward/-Reverse` e
`System.LinkTypes.Related`. Via MCP: `get_work_item` (+relations),
`manage_work_item_link` (somente leitura aqui).
**Saída:** grafo/lista de dependências + itens bloqueados com a cadeia
bloqueadora.

---

## 9. Convenções de "estados de fluxo" (importante)

Lead/cycle/aging/flow-health compartilham a definição de **início** e **fim** do
fluxo. Se cada skill definir por conta, divergem. Quando construir a primeira
skill que precise distinguir "estados de WIP" (provavelmente `agile-flow-health`
ou `agile-aging-wip`), **adicione essas constantes ao `shared/azdo/client.py`**
(ex.: `IN_PROGRESS_STATES`, `START_STATES`, `DONE_STATES`) como fonte única, ao
lado de `FINALIZED_STATES` — e faça as skills seguintes derivarem dali.
Confirme a lista de estados reais do board com o usuário (variam por processo:
Agile, Scrum, CMMI ou custom).
