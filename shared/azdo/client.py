#!/usr/bin/env python3
"""
azdo.client — Cliente REST compartilhado para o Azure DevOps, usado por TODAS
as skills com prefixo `agile-` deste repositório.

Stdlib pura (urllib + base64), sem dependências de terceiros. Centraliza:
  - autenticação por PAT (Basic Auth)
  - chamadas GET / POST / PATCH com tratamento de erro consistente
  - constantes de fluxo (estados finalizados) — FONTE ÚNICA DA VERDADE

Toda credencial vem de variáveis de ambiente (ver shared/.env.example):
  AZDO_PAT        leitura  — escopo Work Items (Read)
  AZDO_PAT_WRITE  escrita  — escopo Work Items (Read & Write); só skills de escrita
  AZDO_ORG, AZDO_PROJECT

Exemplos:
  from azdo.client import post, get, patch, require_env, API_VERSION, FINALIZED_STATES
  org = require_env("AZDO_ORG"); pat = require_env("AZDO_PAT")
  url = f"https://dev.azure.com/{org}/_apis/wit/workitemsbatch?api-version={API_VERSION}"
  data = post(url, {"ids": [1, 2], "fields": ["System.Title"]}, pat)
"""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_VERSION = "7.1"

# Estados considerados "finalizados" — excluídos das visões de fluxo aberto.
# Fonte única ESTÁTICA: fallback para o processo padrão (Agile/Scrum/CMMI). Em
# processos CUSTOMIZADOS os estados terminais podem ter outros nomes (ex.:
# 'Completed'); nesses casos use `finalized_states_for(...)`, que descobre os
# estados terminais pela CATEGORIA real do tipo no processo — fonte única
# dinâmica, correta por processo (ver guia §9).
FINALIZED_STATES = ["Closed", "Resolved", "Done", "Removed", "Discarded", "Canceled"]

# Categorias de metaestado do Azure DevOps consideradas "fora do fluxo".
# (Proposed/InProgress = em fluxo; Resolved = ainda aberto; Completed/Removed
# = terminal.)
TERMINAL_STATE_CATEGORIES = ("Completed", "Removed")


def require_env(name: str) -> str:
    """Lê uma variável de ambiente obrigatória ou aborta com instrução clara."""
    val = os.environ.get(name)
    if not val:
        raise SystemExit(
            f"{name} não definido. Configure ~/.config/agile/.env "
            "(ver shared/README.md)."
        )
    return val


def auth_header(pat: str) -> str:
    """Cabeçalho Basic Auth do Azure DevOps: usuário vazio + PAT."""
    token = base64.b64encode(f":{pat}".encode()).decode()
    return f"Basic {token}"


def _send(url: str, method: str, pat: str, payload=None,
          content_type: str = "application/json") -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", content_type)
    req.add_header("Authorization", auth_header(pat))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(
            f"ERRO HTTP {e.code} em {url}\n{body}\n"
            "Verifique se o PAT é válido e tem o escopo correto (Read para "
            "leitura, Read & Write para escrita) e se AZDO_ORG/AZDO_PROJECT "
            "estão certos. PAT expirado costuma aparecer como 401/203."
        )


def get(url: str, pat: str) -> dict:
    """GET autenticado (ex.: revisões/relations de um work item)."""
    return _send(url, "GET", pat)


def post(url: str, payload: dict, pat: str) -> dict:
    """POST JSON autenticado (ex.: WIQL, workitemsbatch)."""
    return _send(url, "POST", pat, payload)


def state_categories(org: str, project: str, wit_type: str, pat: str) -> dict:
    """Mapa {nome_do_estado: categoria} para um tipo de work item no processo."""
    t = urllib.parse.quote(wit_type, safe="")
    url = (
        f"https://dev.azure.com/{org}/{project}/_apis/wit/workitemtypes/{t}/states"
        f"?api-version={API_VERSION}"
    )
    data = get(url, pat)
    return {s.get("name"): s.get("category", "") for s in data.get("value", [])}


def finalized_states_for(org: str, project: str, wit_type: str, pat: str) -> list:
    """
    Estados terminais (fora do fluxo) do `wit_type`, descobertos pela CATEGORIA
    real no processo — robusto para processos customizados. Cai para
    FINALIZED_STATES se a API não retornar estados.
    """
    cats = state_categories(org, project, wit_type, pat)
    finalized = [n for n, c in cats.items() if c in TERMINAL_STATE_CATEGORIES]
    return finalized or FINALIZED_STATES


def patch(url: str, ops: list, pat: str) -> dict:
    """
    PATCH em json-patch — formato exigido pelo Azure DevOps para criar/editar
    work items. `ops` é uma lista de operações, ex.:
      [{"op": "add", "path": "/fields/System.Title", "value": "..."}]
    """
    return _send(url, "PATCH", pat, ops, content_type="application/json-patch+json")
