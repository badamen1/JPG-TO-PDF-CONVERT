from __future__ import annotations

import argparse
import os
import sys
import time

from contratos.core.drive_client import authenticate, upload_client_to_drive
from contratos.core.pdf_converter import process_client
from contratos.exceptions import ContratosError, DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)

SKIPPED = "omitido"


def run(
    ruta_local: str,
    drive_folder_id: str,
    credentials: str = "credentials.json",
) -> None:
    ruta_local = os.path.abspath(ruta_local)
    if not os.path.isdir(ruta_local):
        raise FileNotFoundError(f"La ruta no existe o no es una carpeta: {ruta_local}")

    client_folders = sorted([
        os.path.join(ruta_local, d)
        for d in os.listdir(ruta_local)
        if os.path.isdir(os.path.join(ruta_local, d)) and not d.startswith("_")
    ])

    if not client_folders:
        raise ContratosError("No se encontraron carpetas de clientes.")

    semana_name = os.path.basename(ruta_local)
    logger.info(
        "Semana: %s | Clientes: %d | Drive: %s",
        semana_name, len(client_folders), drive_folder_id,
    )

    credentials_file = os.path.abspath(credentials)
    token_file = os.path.join(os.path.dirname(credentials_file), "token.json")

    logger.info("Autenticando con Google Drive...")
    drive = authenticate(credentials_file, token_file)
    logger.info("Autenticación exitosa.")

    start_time = time.time()
    results = []

    for i, client_folder in enumerate(client_folders, 1):
        client_name = os.path.basename(client_folder)
        logger.info("[%d/%d] Procesando: %s", i, len(client_folders), client_name)

        pdfs = process_client(client_folder)
        if not pdfs:
            logger.warning("Sin archivos para procesar: %s", client_name)
            results.append((client_name, 0, "sin_archivos"))
            continue

        status = upload_client_to_drive(drive, client_name, pdfs, drive_folder_id)
        results.append((client_name, len(pdfs), status))

    elapsed = time.time() - start_time
    n_ok = sum(1 for _, _, s in results if s == "ok")
    n_skip = sum(1 for _, _, s in results if s == SKIPPED)
    n_fail = sum(1 for _, _, s in results if s == "error")
    n_empty = sum(1 for _, _, s in results if s == "sin_archivos")
    total_pdfs = sum(n for _, n, _ in results)

    logger.info(
        "RESUMEN | Tiempo: %.1fs | Clientes: %d | Subidos: %d | "
        "Omitidos: %d | Sin archivos: %d | Fallidos: %d | Archivos totales: %d",
        elapsed, len(results), n_ok, n_skip, n_empty, n_fail, total_pdfs,
    )

    if n_fail:
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="subir_semana",
        description="Sube una semana completa de clientes a Google Drive.",
    )
    parser.add_argument("--ruta_local", required=True, help="Ruta a la carpeta de la semana")
    parser.add_argument("--drive_folder_id", required=True, help="ID de la carpeta destino en Google Drive")
    parser.add_argument("--credentials", default="credentials.json", help="Ruta al archivo credentials.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.ruta_local, args.drive_folder_id, args.credentials)
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
