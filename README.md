# aprendizados-ia

Repositório de aprendizados gerais com Inteligência Artificial — experimentos,
automações e **skills** reutilizáveis construídas ao longo do caminho.

## Estrutura

```
aprendizados-ia/
└── skills/                  # cada skill isolada na sua própria pasta
    └── report-bugs/         # relatório de bugs Azure DevOps → Drive → GChat
```

Cada subpasta de `skills/` é autocontida: tem seu próprio `SKILL.md`,
scripts, dependências (`requirements.txt`), template de configuração
(`.env.example`) e guia de setup (`references/`). Novas habilidades entram
como novas pastas em `skills/`, sem acoplar umas às outras.

## Skills

| Skill | O que faz |
|-------|-----------|
| [`report-bugs`](skills/report-bugs/) | Compila bugs abertos do Azure DevOps em PDF (por time, com flags de SLA), arquiva no Google Drive e posta o link num espaço do Google Chat. |

## Segurança

Este repositório é **público**. Nenhum segredo é versionado:

- Credenciais ficam em arquivos `.env` **fora do repo**, criados por cada
  usuário a partir dos templates `.env.example`.
- Chaves (Service Account, tokens) são bloqueadas pelo `.gitignore`.
- Os guias em `references/` ensinam o leitor a gerar **as próprias
  credenciais**, isoladamente — nada aqui depende de segredos de terceiros.

## Como usar uma skill

Entre na pasta da skill e siga o `README.md` + `references/setup.md` dela.
Comece por [`skills/report-bugs/README.md`](skills/report-bugs/README.md).

## Changelog

O repositório mantém um changelog global em [`CHANGELOG.md`](CHANGELOG.md)
(formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) +
[Semantic Versioning](https://semver.org/lang/pt-BR/)).

**Premissa do repositório:** toda mudança — seja onde for (skills, raiz,
automações, docs, configuração) — recebe uma nota no changelog explicando
**onde** foi feita e **por quê**. O "o quê" fica no diff; o changelog guarda a
motivação.
