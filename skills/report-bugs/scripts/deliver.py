#!/usr/bin/env python3
"""
deliver.py — Sobe o PDF para o Google Drive via Service Account e devolve um
link público de leitura. 100% headless (sem modelo no meio), próprio para a
rotina semanal.

O que faz:
  1. Autentica com a Service Account (JSON key) no escopo Drive.
  2. Faz upload do PDF para a pasta GDRIVE_FOLDER_ID (suporta Shared Drives).
  3. Define permissão "anyone with link → reader".
  4. Imprime no stdout (última linha) um JSON: {"drive_link","file_id"}.

Variáveis de ambiente:
  GDRIVE_SA_JSON    (obrigatório)  caminho do JSON da Service Account
  GDRIVE_FOLDER_ID  (obrigatório)  ID da pasta de destino

Uso:
  python3 deliver.py --pdf /caminho/Relatorio_Bugs_<projeto>_2026-05-18.pdf

Nota sobre cota: uma Service Account não tem cota de armazenamento própria. Se
a pasta destino estiver no "Meu Drive" de um usuário, o upload falha com
"storageQuotaExceeded". Soluções (ver references/setup.md): usar uma pasta em
um Drive Compartilhado (recomendado) ou delegação em todo o domínio.
"""
import argparse
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="Caminho do PDF a enviar")
    args = ap.parse_args()

    sa_json = os.environ.get("GDRIVE_SA_JSON")
    folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not sa_json or not os.path.isfile(sa_json):
        raise SystemExit(
            "GDRIVE_SA_JSON não definido ou arquivo inexistente. "
            "Ver references/setup.md (seção Service Account)."
        )
    if not folder_id:
        raise SystemExit("GDRIVE_FOLDER_ID não definido no .env.")
    if not os.path.isfile(args.pdf):
        raise SystemExit(f"PDF não encontrado: {args.pdf}")

    creds = service_account.Credentials.from_service_account_file(
        sa_json, scopes=SCOPES
    )
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    file_metadata = {
        "name": os.path.basename(args.pdf),
        "parents": [folder_id],
    }
    media = MediaFileUpload(args.pdf, mimetype="application/pdf", resumable=True)

    try:
        created = (
            drive.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        msg = str(e)
        if "accessNotConfigured" in msg or "has not been used in project" in msg:
            raise SystemExit(
                "A Google Drive API não está habilitada no projeto do Google "
                "Cloud da Service Account.\n"
                "Habilite em: APIs & Services → Library → 'Google Drive API' → "
                "Enable, e aguarde ~3 min.\n"
                "Ver references/setup.md (seção C.1)."
            )
        if "storageQuotaExceeded" in msg or "storage quota" in msg.lower():
            raise SystemExit(
                "Upload falhou: a Service Account não tem cota de armazenamento.\n"
                "A pasta de destino precisa estar em um DRIVE COMPARTILHADO "
                "(Shared Drive), ou usar delegação de domínio.\n"
                "Passos em references/setup.md (seção C.2)."
            )
        if "File not found" in msg or "notFound" in msg:
            raise SystemExit(
                "Pasta de destino não encontrada ou a Service Account não é "
                "membro dela.\n"
                "Confirme o GDRIVE_FOLDER_ID e adicione o e-mail da Service "
                "Account como membro do Drive Compartilhado (Colaborador de "
                "conteúdo). Ver references/setup.md (seção C.2)."
            )
        raise SystemExit(f"Erro ao subir para o Drive:\n{msg}")

    file_id = created["id"]

    # Permissão: qualquer pessoa com o link pode visualizar.
    try:
        drive.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            supportsAllDrives=True,
        ).execute()
    except HttpError as e:
        raise SystemExit(
            f"Arquivo subiu (id={file_id}) mas falhou ao tornar público:\n{e}"
        )

    link = created.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
    print(json.dumps({"drive_link": link, "file_id": file_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
