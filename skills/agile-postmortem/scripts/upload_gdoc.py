#!/usr/bin/env python3
"""Grava um .docx no Google Drive como Google Doc nativo (com formatação).

Faz o que o conector MCP do Drive não faz: usa a API do Drive direto (Service
Account) e pede a conversão docx -> application/vnd.google-apps.document. A
formatação rica do .docx (títulos, negrito, listas — o padrão visual) é
preservada pela conversão do Google.

Dois modos:
  • CRIAR um Doc novo (default):
        python3 upload_gdoc.py <arquivo.docx> "<título>" [folder_id]
  • ATUALIZAR o conteúdo de um Doc já existente, mantendo a MESMA URL/id
    (ex.: o Doc duplicado do template no passo 1):
        python3 upload_gdoc.py <arquivo.docx> --update <fileId>

Credenciais (mesmo .env compartilhado da família agile-*):
    GDRIVE_SA_JSON      -> JSON da Service Account (ou GOOGLE_APPLICATION_CREDENTIALS)
    PM_DRIVE_FOLDER_ID  -> ID da pasta de destino no modo CRIAR (ou 3º arg)
A Service Account precisa ser MEMBRO (Content manager/Contribuidor) do Drive
compartilhado/pasta destino — senão a API retorna "File not found".
"""
import argparse
import os
import sys

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
GDOC_MIME = "application/vnd.google-apps.document"


def build_drive():
    sa_json = os.environ.get("GDRIVE_SA_JSON") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not sa_json or not os.path.isfile(sa_json):
        print("erro: defina GDRIVE_SA_JSON (ou GOOGLE_APPLICATION_CREDENTIALS) apontando para o JSON da Service Account", file=sys.stderr)
        raise SystemExit(1)
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Grava um .docx no Drive como Google Doc nativo.")
    ap.add_argument("docx", help="Arquivo .docx de origem (conteúdo formatado).")
    ap.add_argument("title", nargs="?", help="Título do Doc (modo CRIAR).")
    ap.add_argument("folder_id", nargs="?", help="ID da pasta destino (modo CRIAR; default PM_DRIVE_FOLDER_ID).")
    ap.add_argument("--update", metavar="FILE_ID", help="Atualiza o conteúdo deste Doc existente, mantendo a mesma URL.")
    args = ap.parse_args()

    if not os.path.isfile(args.docx):
        print(f"erro: arquivo não encontrado: {args.docx}", file=sys.stderr)
        return 1

    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(args.docx, mimetype=DOCX_MIME, resumable=False)
    drive = build_drive()

    if args.update:
        # Reescreve o conteúdo do Doc existente (mesma id/URL). Opcionalmente renomeia.
        body = {"name": args.title} if args.title else {}
        f = drive.files().update(
            fileId=args.update,
            body=body,
            media_body=media,
            fields="id,name,mimeType,webViewLink",
            supportsAllDrives=True,
        ).execute()
        print("OK — Google Doc atualizado (mesma URL):")
    else:
        if not args.title:
            print('erro: no modo CRIAR informe o "<título>" (ou use --update <fileId>)', file=sys.stderr)
            return 2
        folder_id = args.folder_id or os.environ.get("PM_DRIVE_FOLDER_ID")
        if not folder_id:
            print("erro: defina PM_DRIVE_FOLDER_ID no ~/.config/agile/.env (ou passe o folder_id como 3º argumento)", file=sys.stderr)
            return 1
        body = {"name": args.title, "parents": [folder_id], "mimeType": GDOC_MIME}
        f = drive.files().create(
            body=body,
            media_body=media,
            fields="id,name,mimeType,webViewLink",
            supportsAllDrives=True,
        ).execute()
        print("OK — Google Doc criado:")

    print("  id:        ", f.get("id"))
    print("  nome:      ", f.get("name"))
    print("  mimeType:  ", f.get("mimeType"))
    print("  link:      ", f.get("webViewLink"))
    if f.get("mimeType") != GDOC_MIME:
        print("AVISO: o arquivo não é Doc nativo (mimeType inesperado).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
