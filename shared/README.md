# shared — infraestrutura comum das skills `agile-*`

Tudo que as skills `agile-*` deste repositório compartilham vive aqui:

- **`azdo/client.py`** — cliente REST do Azure DevOps (autenticação por PAT,
  `get`/`post`/`patch`, constantes de fluxo). **Stdlib pura, sem dependências.**
- **`.env.example`** — template do `.env` **único** da família, instalado em
  `~/.config/agile/.env`.
- **este README** — os pré-requisitos **comuns** (PAT + `.env`). Os
  pré-requisitos específicos de cada skill ficam no `references/setup.md` dela.

> **Regra de prefixo:** toda skill que usa este `shared/` **deve** ter o prefixo
> `agile-` (ex.: `agile-report-bugs`, `agile-flow-health`). O prefixo sinaliza
> "compartilha credencial e cliente AzDO".

---

## 1. Personal Access Token (Azure DevOps)

Você precisa de **um** PAT (leitura). Crie o de **escrita** só se for usar uma
skill que cria/edita work items.

1. Acesse `https://dev.azure.com/<SUA_ORG>`.
2. Canto superior direito → ícone de usuário → **Personal access tokens**.
3. **+ New Token** e preencha:
   - **Name:** `agile-skills` (ou um por escopo: `agile-read` / `agile-write`).
   - **Organization:** sua organização.
   - **Expiration:** 90 ou 180 dias (anote para renovar; quando expirar, as
     skills falham com `ERRO HTTP 401/203` — gere outro e atualize o `.env`).
   - **Scopes:** *Custom defined* → **Work Items**:
     - **Read** → vai em `AZDO_PAT` (basta isto para skills de leitura).
     - **Read & Write** → vai em `AZDO_PAT_WRITE` (só skills de escrita).
4. **Create** e copie o token na hora (não é exibido de novo).

> **Menor privilégio:** mantenha `AZDO_PAT` como Read. Só gere o `AZDO_PAT_WRITE`
> quando realmente for rodar uma skill de escrita — assim o token poderoso fica
> isolado e opcional.

## 2. Instalar o `.env` compartilhado

```bash
mkdir -p ~/.config/agile
cp shared/.env.example ~/.config/agile/.env
chmod 600 ~/.config/agile/.env
$EDITOR ~/.config/agile/.env   # preencha AZDO_PAT, AZDO_ORG, AZDO_PROJECT
```

Toda skill `agile-*` carrega este mesmo arquivo antes de rodar:

```bash
set -a; source ~/.config/agile/.env; set +a
```

## 3. Dependências

O cliente `azdo/client.py` é **stdlib pura** — não precisa instalar nada para
ele. Cada skill declara suas próprias deps pesadas no `requirements.txt` dela
(ex.: `agile-report-bugs` usa `reportlab` + libs do Google):

```bash
pip install -r skills/<nome-da-skill>/requirements.txt
```

## 4. Como o cliente é importado

As skills resolvem o `shared/` automaticamente (bootstrap de `sys.path` relativo
ao arquivo), então funcionam de qualquer diretório **sem** configurar nada:

```python
# dentro de skills/<algo>/scripts/*.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from azdo.client import post, get, patch, require_env, API_VERSION, FINALIZED_STATES
```

Para uso **interativo** (REPL, scripts soltos), defina o `PYTHONPATH` opcional
documentado no `.env.example`.

---

## Criar uma nova skill `agile-*`

1. `skills/agile-<nome>/` com `SKILL.md`, `README.md` e `scripts/`.
2. Nos scripts, use o bootstrap acima e `from azdo.client import ...` — **não
   reescreva autenticação nem chamadas REST.**
3. Adicione só as variáveis NOVAS ao `shared/.env.example` (e oriente o usuário
   a colocá-las no mesmo `~/.config/agile/.env`).
4. Pré-requisitos comuns (PAT/`.env`): **aponte para este README**, não duplique.
   Documente em `references/setup.md` só o que for específico da skill.
5. Registre a skill no `README.md` da raiz e no `CHANGELOG.md` (onde + porquê).
