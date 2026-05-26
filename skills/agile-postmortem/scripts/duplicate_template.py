#!/usr/bin/env python3
"""Duplica o Google Doc template do post mortem e o renomeia (passo 1).

Faz `files.copy` na API do Drive: copia o Doc template (PM_TEMPLATE_DOC_ID) para a
pasta compartilhada de post mortems (PM_DRIVE_FOLDER_ID), com o nome
"POST MORTEM - <título>". Devolve o link (webViewLink) para o usuário abrir no
Drive já a partir do passo 1 — esse mesmo Doc é o documento de trabalho, e seu
conteúdo é preenchido depois (passo 5) com `upload_gdoc.py --update <id>`,
mantendo a mesma URL.

Uso:
    set -a; source ~/.config/agile/.env; set +a
    python3 duplicate_template.py "<título>" [template_doc_id] [folder_id]

Credenciais (mesmo .env compartilhado da família agile-*):
    GDRIVE_SA_JSON      -> JSON da Service Account (ou GOOGLE_APPLICATION_CREDENTIALS)
    PM_TEMPLATE_DOC_ID  -> ID do Google Doc template (ou passe como 2º arg)
    PM_DRIVE_FOLDER_ID  -> ID da pasta de destino (ou passe como 3º arg)
A Service Account precisa ter acesso de LEITURA ao template e ser MEMBRO
(Content manager/Contribuidor) do Drive compartilhado de destino.
"""
import os
import sys

GDOC_MIME = "application/vnd.google-apps.document"


def main() -> int:
    if len(sys.argv) < 2:
        print('uso: duplicate_template.py "<título>" [template_doc_id] [folder_id]', file=sys.stderr)
        return 2

    title = sys.argv[1]
    template_id = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("PM_TEMPLATE_DOC_ID")
    folder_id = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("PM_DRIVE_FOLDER_ID")

    if not template_id:
        print("erro: defina PM_TEMPLATE_DOC_ID no ~/.config/agile/.env (ou passe como 2º argumento)", file=sys.stderr)
        return 1
    if not folder_id:
        print("erro: defina PM_DRIVE_FOLDER_ID no ~/.config/agile/.env (ou passe como 3º argumento)", file=sys.stderr)
        return 1

    sa_json = os.environ.get("GDRIVE_SA_JSON") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not sa_json or not os.path.isfile(sa_json):
        print("erro: defina GDRIVE_SA_JSON (ou GOOGLE_APPLICATION_CREDENTIALS) apontando para o JSON da Service Account", file=sys.stderr)
        return 1

    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"]
    )
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    body = {"name": title, "parents": [folder_id]}
    f = drive.files().copy(
        fileId=template_id,
        body=body,
        fields="id,name,mimeType,webViewLink",
        supportsAllDrives=True,
    ).execute()

    print("OK — template duplicado:")
    print("  id:        ", f.get("id"))
    print("  nome:      ", f.get("name"))
    print("  mimeType:  ", f.get("mimeType"))
    print("  link:      ", f.get("webViewLink"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
