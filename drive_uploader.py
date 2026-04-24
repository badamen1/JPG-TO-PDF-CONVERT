#!/usr/bin/env python3
"""Módulo de integración con Google Drive API usando PyDrive2.

Provee funciones para autenticar, crear carpetas y subir archivos a Drive.
"""
from __future__ import annotations

import os
import sys

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def authenticate(credentials_path: str = "credentials.json",
                 token_path: str = "token.json") -> GoogleDrive:
    """Autentica con Google Drive API vía OAuth2.

    En la primera ejecución abre el navegador para autorizar.
    Guarda el token para sesiones futuras.

    Args:
        credentials_path: Ruta al archivo credentials.json de Google Cloud.
        token_path: Ruta donde se guarda/lee el token de sesión.

    Returns:
        Instancia autenticada de GoogleDrive.
    """
    if not os.path.exists(credentials_path):
        print(
            f"❌ No se encontró '{credentials_path}'.\n"
            "   Descárgalo desde Google Cloud Console → APIs y Servicios → Credenciales.\n"
            "   Consulta el README.md para instrucciones detalladas.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Configurar PyDrive2 para usar nuestros archivos
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
            except Exception:
                # Si el refresh falla (token revocado o expirado), limpiar y re-autenticar
                if os.path.exists(token_path):
                    os.remove(token_path)
                gauth.credentials = None
                gauth.LocalWebserverAuth()
        else:
            gauth.Authorize()
    else:
        gauth.LocalWebserverAuth()

    gauth.SaveCredentialsFile(token_path)
    return GoogleDrive(gauth)


def find_folder(drive: GoogleDrive, name: str, parent_id: str) -> str | None:
    """Busca una carpeta por nombre dentro de un folder padre en Drive.

    Args:
        drive: Instancia autenticada de GoogleDrive.
        name: Nombre de la carpeta a buscar.
        parent_id: ID de la carpeta padre en Drive.

    Returns:
        ID de la carpeta si existe, None si no existe.
    """
    safe_name = name.replace("'", "\\'")
    query = (
        f"title='{safe_name}' and "
        f"'{parent_id}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    result = drive.ListFile({"q": query}).GetList()
    return result[0]["id"] if result else None


def create_folder(drive: GoogleDrive, name: str, parent_id: str) -> str:
    """Crea una carpeta en Google Drive dentro de un folder padre.

    Args:
        drive: Instancia autenticada de GoogleDrive.
        name: Nombre de la carpeta a crear.
        parent_id: ID de la carpeta padre en Drive.

    Returns:
        ID de la carpeta creada.
    """
    folder_metadata = {
        "title": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [{"id": parent_id}],
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder["id"]


def upload_file(drive: GoogleDrive, file_path: str, parent_id: str) -> str:
    """Sube un archivo a una carpeta específica de Google Drive.

    Args:
        drive: Instancia autenticada de GoogleDrive.
        file_path: Ruta local del archivo a subir.
        parent_id: ID de la carpeta destino en Drive.

    Returns:
        ID del archivo subido.
    """
    file_name = os.path.basename(file_path)
    file_metadata = {
        "title": file_name,
        "parents": [{"id": parent_id}],
    }
    gfile = drive.CreateFile(file_metadata)
    gfile.SetContentFile(file_path)
    gfile.Upload()
    return gfile["id"]
