# Salvar o post mortem no Google Drive (passos 1 e 5)

Objetivo: o usuário recebe o **link do documento já no passo 1** (cópia do
template) e o conteúdo formatado é gravado **no mesmo Doc** no passo 5 — uma única
URL do começo ao fim, como Google Doc nativo com a formatação preservada.

## Modelo: duplicar (passo 1) → atualizar (passo 5)
1. **Passo 1 — `duplicate_template.py`**: faz `files.copy` do Doc template
   (`PM_TEMPLATE_DOC_ID`) para a pasta (`PM_DRIVE_FOLDER_ID`), com o nome
   `POST MORTEM - <título>`. Devolve o `id` e o `link` — entregue o link ao usuário.
2. **Passo 5 — `upload_gdoc.py --update <id>`**: faz `files.update` gravando o
   `.docx` formatado **no mesmo Doc** (mesma id/URL), convertendo para Doc nativo.

> Alternativa (modo CRIAR, sem duplicação prévia): `upload_gdoc.py <docx>
> "<título>" [folder_id]` faz `files.create` e gera um Doc novo.

## Pasta de destino e template (configuráveis por env)
- **Pasta**: `PM_DRIVE_FOLDER_ID` no `.env` compartilhado (`~/.config/agile/.env`)
  — ou argumento do script (precedência). É a pasta única de post mortems.
- **Template**: `PM_TEMPLATE_DOC_ID` — ou 2º argumento do `duplicate_template.py`.
- Nada é embutido no código (o repo é público).

## Por que um script, e não o conector MCP
O conector MCP do Google Drive **só auto-converte `text/plain`→Doc e
`text/csv`→planilha**. Testado: `.docx`, `text/html`, `text/markdown` e
`application/rtf` **não** são convertidos — ficam no formato original. Logo, para
um Google Doc nativo *com* a formatação rica do padrão, não dá para usar o
`create_file` do conector.

A solução é o script `scripts/upload_gdoc.py`, que chama a **API do Drive direto**
e faz `files.create` com `mimeType: application/vnd.google-apps.document` + a mídia
`.docx`. O Google converte o `.docx` em Doc nativo preservando títulos (`H1`/`H2`),
negrito e listas — exatamente o que o "Salvar como Documentos Google" faz, só que
automatizado.

## Credenciais (Service Account)
O script usa uma **Service Account do Google**, cujo JSON fica na variável
`GDRIVE_SA_JSON` do `.env` compartilhado (a mesma SA usada pela
`agile-report-bugs`). Aceita também `GOOGLE_APPLICATION_CREDENTIALS`. Como criar:
ver `setup.md`.

> **Requisito de acesso:** a Service Account precisa ser **MEMBRO (Content
> manager/Contribuidor) do Drive compartilhado** que contém a pasta. Se não for, a
> API retorna `File not found: <folder_id>` (o Drive nem aparece para a SA). Peça
> ao dono do Drive para adicionar o e-mail da SA como membro.

## Como rodar
```bash
set -a; source ~/.config/agile/.env; set +a       # carrega GDRIVE_SA_JSON + PM_DRIVE_FOLDER_ID
python3 scripts/upload_gdoc.py <saida.docx> "POST MORTEM - <título>" [folder_id]
```
- `folder_id` (3º arg) é opcional; o default é a env `PM_DRIVE_FOLDER_ID`.
- O nome do arquivo segue sempre o padrão `POST MORTEM - <título>` (passo 1).
- A saída imprime `id`, `mimeType` (deve ser `application/vnd.google-apps.document`)
  e o `webViewLink` → use esse link na notificação (passo 6).

## Antes de gravar
Gravar afeta um espaço compartilhado. Confirme com a pessoa o **nome final** do
documento e que o destino é a pasta correta antes de subir.

## Fallback (SA sem acesso ao Drive)
Se o script falhar com `File not found` (SA não é membro do Drive), enquanto o
acesso não é concedido:
1. suba o `.docx` pelo conector MCP: `create_file(parentId="<folder_id>", title="POST MORTEM - <título>", contentMimeType=<docx>, base64Content=<...>)`;
2. converta manualmente: abrir com Google Docs → Arquivo → Salvar como Documentos Google.
Avise que falta adicionar a Service Account como membro do Drive para o salvamento
voltar a ser automático e já no formato nativo.
