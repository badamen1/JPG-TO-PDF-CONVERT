from __future__ import annotations

import argparse
import glob
import os
import re
import sys

from contratos.core.drive_client import authenticate, get_folder_map, upload_file
from contratos.exceptions import ContratosError, DriveAuthError, DriveUploadError
from contratos.logger import get_logger

logger = get_logger(__name__)


def run(carpeta_local: str, drive_folder_id: str) -> None:
    if not os.path.exists(carpeta_local):
        raise FileNotFoundError(f"La carpeta local '{carpeta_local}' no existe.")

    logger.info("Autenticando con Google Drive...")
    drive = authenticate()
    logger.info("Autenticación exitosa.")

    mapa = get_folder_map(drive, drive_folder_id)
    if not mapa:
        raise ContratosError("No se encontraron carpetas en el ID de Drive proporcionado.")

    pdf_files = glob.glob(os.path.join(carpeta_local, "*.pdf"))
    if not pdf_files:
        logger.warning("No hay archivos PDF en '%s'.", carpeta_local)
        return

    logger.info("Iniciando subida de %d contratos...", len(pdf_files))
    subidos = 0
    no_encontrados = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        name_only = os.path.splitext(filename)[0]
        match = re.search(r"(\d{6})", name_only)

        if not match:
            logger.warning("Sin código de 6 dígitos: '%s'", filename)
            no_encontrados += 1
            continue

        codigo = match.group(1)
        if codigo in mapa:
            try:
                upload_file(drive, pdf_path, mapa[codigo])
                logger.info("[SUBIDO] '%s' -> carpeta %s", filename, codigo)
                subidos += 1
            except DriveUploadError as e:
                logger.error("[ERROR] Falló la subida de '%s': %s", filename, e)
        else:
            logger.warning("[SIN CARPETA] '%s': No hay carpeta para código %s", filename, codigo)
            no_encontrados += 1

    logger.info(
        "RESUMEN | Total: %d | Subidos: %d | Sin carpeta: %d",
        len(pdf_files), subidos, no_encontrados,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube contratos corregidos a sus respectivas subcarpetas en Google Drive."
    )
    parser.add_argument("carpeta_local", help="Ruta local donde están los PDFs")
    parser.add_argument("drive_folder_id", help="ID de la carpeta principal en Google Drive")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.carpeta_local, args.drive_folder_id)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except (ContratosError, FileNotFoundError) as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
