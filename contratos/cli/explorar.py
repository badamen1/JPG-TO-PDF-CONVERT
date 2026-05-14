from __future__ import annotations

import argparse
import sys

from contratos.core.drive_client import authenticate
from contratos.exceptions import DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)


def obtener_nombre_carpeta(drive, folder_id: str) -> str:
    try:
        carpeta = drive.CreateFile({"id": folder_id})
        carpeta.FetchMetadata(fields="title")
        return carpeta["title"]
    except Exception:
        return folder_id


def listar_contenido(
    drive, folder_id: str, nombre: str, prefijo: str = "", es_ultimo: bool = True
) -> None:
    query_carpetas = (
        f"'{folder_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    query_archivos = (
        f"'{folder_id}' in parents and "
        "mimeType != 'application/vnd.google-apps.folder' and trashed=false"
    )

    try:
        subcarpetas = drive.ListFile({"q": query_carpetas, "maxResults": 1000}).GetList()
        archivos_list = drive.ListFile(
            {"q": query_archivos, "maxResults": 1000, "fields": "items(id)"}
        ).GetList()
        num_archivos = len(archivos_list)
    except Exception as e:
        conector = "└── " if es_ultimo else "├── "
        print(f"{prefijo}{conector}[CARPETA] {nombre} — Error: {e}")
        return

    info_archivos = f" ({num_archivos} archivos)" if num_archivos > 0 else " (vacía)"
    conector = "└── " if es_ultimo else "├── "
    print(f"{prefijo}{conector}[CARPETA] {nombre}{info_archivos}")

    prefijo_hijo = prefijo + ("    " if es_ultimo else "|   ")
    subcarpetas = sorted(subcarpetas, key=lambda f: f["title"].lower())

    for i, carpeta in enumerate(subcarpetas):
        listar_contenido(
            drive,
            folder_id=carpeta["id"],
            nombre=carpeta["title"],
            prefijo=prefijo_hijo,
            es_ultimo=(i == len(subcarpetas) - 1),
        )


def run(folder_id: str) -> None:
    logger.info("Autenticando con Google Drive...")
    drive = authenticate()
    logger.info("Autenticación exitosa.")

    nombre_raiz = obtener_nombre_carpeta(drive, folder_id)
    print(f"\n[CARPETA] {nombre_raiz} (raíz)")
    print(f"ID: {folder_id}\n")

    query_carpetas = (
        f"'{folder_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    query_archivos = (
        f"'{folder_id}' in parents and "
        "mimeType != 'application/vnd.google-apps.folder' and trashed=false"
    )

    try:
        carpetas_raiz = drive.ListFile({"q": query_carpetas, "maxResults": 1000}).GetList()
        archivos_raiz = drive.ListFile({"q": query_archivos, "maxResults": 1000}).GetList()
    except Exception as e:
        logger.error("Error al leer la carpeta raíz: %s", e)
        sys.exit(1)

    carpetas_raiz = sorted(carpetas_raiz, key=lambda f: f["title"].lower())
    archivos_raiz = sorted(archivos_raiz, key=lambda f: f["title"].lower())

    if not carpetas_raiz and not archivos_raiz:
        print("    (vacía)")
        return

    for i, carpeta in enumerate(carpetas_raiz):
        es_ultimo = (i == len(carpetas_raiz) - 1) and (len(archivos_raiz) == 0)
        listar_contenido(drive, carpeta["id"], carpeta["title"], "", es_ultimo)

    for i, archivo in enumerate(archivos_raiz):
        conector = "└── " if (i == len(archivos_raiz) - 1) else "├── "
        print(f"{conector}{archivo['title']}")

    logger.info("Exploración completada.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explora y muestra el árbol de carpetas de Google Drive.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("folder_id", help="ID de la carpeta raíz en Google Drive.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.folder_id.strip())
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Exploración interrumpida por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
