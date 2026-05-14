from __future__ import annotations

import os
import re

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from contratos.exceptions import DriveAuthError, DriveUploadError
from contratos.logger import get_logger

logger = get_logger(__name__)


def authenticate(
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
) -> GoogleDrive:
    if not os.path.exists(credentials_path):
        raise DriveAuthError(
            f"No se encontró '{credentials_path}'. "
            "Descárgalo desde Google Cloud Console → APIs y Servicios → Credenciales."
        )

    settings = {
        "client_config_backend": "file",
        "client_config_file": credentials_path,
        "save_credentials": True,
        "save_credentials_backend": "file",
        "save_credentials_file": token_path,
        "get_refresh_token": True,
    }

    gauth = GoogleAuth(settings=settings)

    if os.path.exists(token_path):
        gauth.LoadCredentialsFile(token_path)
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            try:
                gauth.Refresh()
            except Exception as e:
                if os.path.exists(token_path):
                    os.remove(token_path)
                gauth.credentials = None
                try:
                    gauth.LocalWebserverAuth()
                except Exception as e2:
                    raise DriveAuthError(
                        "No se pudo renovar ni re-autenticar con Google Drive."
                    ) from e2
        else:
            gauth.Authorize()
    else:
        gauth.LocalWebserverAuth()

    gauth.SaveCredentialsFile(token_path)
    return GoogleDrive(gauth)


def get_folder_map(drive: GoogleDrive, parent_id: str) -> dict[str, str]:
    """Retorna mapa {código_6_dígitos: folder_id} de subcarpetas de parent_id."""
    query = (
        f"'{parent_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    folder_list = drive.ListFile({"q": query, "maxResults": 1000}).GetList()

    mapa: dict[str, str] = {}
    for folder in folder_list:
        title = folder["title"].strip()
        match = re.search(r"(\d{6})", title)
        if match:
            mapa[match.group(1)] = folder["id"]

    logger.info("%d carpetas de clientes encontradas en Drive.", len(mapa))
    return mapa


def find_folder(drive: GoogleDrive, name: str, parent_id: str) -> str | None:
    safe_name = name.replace("'", "\\'")
    query = (
        f"title='{safe_name}' and "
        f"'{parent_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    result = drive.ListFile({"q": query}).GetList()
    return result[0]["id"] if result else None


def create_folder(drive: GoogleDrive, name: str, parent_id: str) -> str:
    folder_metadata = {
        "title": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [{"id": parent_id}],
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder["id"]


def upload_file(drive: GoogleDrive, file_path: str, parent_id: str) -> str:
    file_name = os.path.basename(file_path)
    file_metadata = {
        "title": file_name,
        "parents": [{"id": parent_id}],
    }
    gfile = drive.CreateFile(file_metadata)
    gfile.SetContentFile(file_path)
    try:
        gfile.Upload()
    except Exception as e:
        raise DriveUploadError(f"Falla al subir '{file_name}': {e}") from e
    return gfile["id"]


def upload_client_to_drive(
    drive: GoogleDrive,
    client_name: str,
    pdfs: list[str],
    parent_folder_id: str,
) -> str:
    """Crea carpeta del cliente en Drive y sube sus PDFs.

    Returns:
        'ok' si subió exitosamente, 'omitido' si ya existía, 'error' si falló.
    """
    try:
        existing_id = find_folder(drive, client_name, parent_folder_id)
        if existing_id:
            logger.info("Ya existe en Drive, se omite: %s", client_name)
            return "omitido"

        folder_id = create_folder(drive, client_name, parent_folder_id)
        logger.info("Carpeta creada en Drive: %s", client_name)

        for pdf_path in pdfs:
            upload_file(drive, pdf_path, folder_id)
            logger.info("Subido: %s", os.path.basename(pdf_path))

        return "ok"
    except Exception as e:
        logger.error("Error subiendo '%s': %s", client_name, e)
        return "error"
