# Schema do conteúdo (JSON consumido por build_postmortem.js)

Um exemplo completo e válido está em `scripts/content.example.json`. Campos:

```
{
  "titulo": "POST MORTEM — <título breve>",            // string (vira H1)

  "cabecalho": {                                         // qualquer campo vazio é omitido
    "appsAfetados": "...",
    "dataIncidente": "...",
    "janelaImpacto": "...",                              // janela sentida pelo usuário
    "indisponibilidade": "...",                          // janela do serviço (se diferente)
    "timeResponsavel": "...",
    "squadLead": "email ou nome",                        // e-mail vira link mailto
    "gestor": "nome (email)",
    "participantes": "...",
    "linkTranscricao": "https://..."                     // link da ata/transcrição (vira hyperlink)
  },

  "resumo": ["parágrafo 1", "parágrafo 2"],              // array de parágrafos
  "evidenciasResumo": "descrição da evidência",          // opcional; sai em itálico cinza

  "impactos":  [ item, ... ],                            // ver "item" abaixo
  "timeline":  [ { "dia": "Dia 1 — dd/mm",
                   "linhas": [ { "hora": "~hh:mm", "texto": "..." }, ... ] }, ... ],
  "causaRaiz": [ item, ... ],                            // gatilho + causa raiz como bullets
  "acoesContorno": [ item, ... ],
  "licoes":    [ item, ... ],

  "plano": [ { "tarefa": "...", "descricao": "...",
               "responsavel": "email ou nome", "backlog": "url ou [pendente]" }, ... ],

  "notas": [ item, ... ]                                 // opcional; seção 8 só aparece se houver notas
}
```

## "item" (em impactos, causaRaiz, acoesContorno, licoes, notas)
Pode ser:
- uma **string** → vira um bullet de nível 0; ou
- um **objeto** `{ "texto": "...", "sub": ["...", "..."] }` → bullet com sub-bullets (nível 1).

## Conversões automáticas
- E-mails (`alguem@dominio`) → hyperlink `mailto:`.
- Valores que começam com `http(s)://` → hyperlink.
- `hora` na timeline pode ser `"—"` quando não houver horário.

## Regras de preenchimento
- O que a transcrição não permitir afirmar entra como `"[preencher]"` ou como item em `notas`.
- Timeline sempre cronológica; agrupar por `dia` quando o incidente cruza mais de um dia.
- Não inventar responsáveis, horários ou causa raiz.
