from __future__ import annotations

import argparse
import glob
import os
import re
import sys

from contratos.core.drive_client import authenticate, get_folder_map, upload_file
from contratos.core.duplicates import (
    buscar_duplicados_recursivo,
    formatear_fecha,
    formatear_tamanio,
)
from contratos.core.pdf_corrector import corregir_contratos
from contratos.exceptions import ContratosError, DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)


def paso_1_corregir(carpeta_local: str) -> str | None:
    logger.info("PASO 1: CORRECCIÓN DE CONTRATOS")
    try:
        procesados, modificados = corregir_contratos(carpeta_local, delete_old=False)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return None

    carpeta_corregidos = os.path.join(carpeta_local, "contratos_corregidos")
    if not os.path.exists(carpeta_corregidos):
        logger.warning("No se creó 'contratos_corregidos'. Sin archivos que corregir.")
        return None

    pdf_corregidos = glob.glob(os.path.join(carpeta_corregidos, "*.pdf"))
    if not pdf_corregidos:
        logger.warning("La carpeta 'contratos_corregidos' está vacía.")
        return None

    logger.info("Paso 1 completado. %d contratos corregidos.", len(pdf_corregidos))
    return carpeta_corregidos


def paso_2_subir(drive, carpeta_corregidos: str, drive_folder_id: str) -> None:
    logger.info("PASO 2: SUBIDA A GOOGLE DRIVE")
    mapa = get_folder_map(drive, drive_folder_id)
    if not mapa:
        logger.error("No se encontraron carpetas en el ID de Drive proporcionado.")
        return

    pdf_files = glob.glob(os.path.join(carpeta_corregidos, "*.pdf"))
    subidos = 0
    no_encontrados = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        name_only = os.path.splitext(filename)[0]
        match = re.search(r"(\d{6})", name_only)

        if not match:
            logger.warning("[OMITIDO] Sin código de 6 dígitos: '%s'", filename)
            no_encontrados += 1
            continue

        codigo = match.group(1)
        if codigo in mapa:
            try:
                upload_file(drive, pdf_path, mapa[codigo])
                logger.info("[SUBIDO] '%s' -> carpeta %s", filename, codigo)
                subidos += 1
            except Exception as e:
                logger.error("[ERROR] Falló la subida de '%s': %s", filename, e)
        else:
            logger.warning("[SIN CARPETA] '%s': No hay carpeta para código %s", filename, codigo)
            no_encontrados += 1

    logger.info("Paso 2 completado. Subidos: %d | Sin destino: %d", subidos, no_encontrados)


def paso_3_limpiar(drive, drive_folder_id: str) -> None:
    logger.info("PASO 3: LIMPIEZA DE DUPLICADOS")
    duplicados = buscar_duplicados_recursivo(drive, drive_folder_id)

    if not duplicados:
        logger.info("No se encontraron contratos duplicados.")
        return

    logger.warning("Se encontraron %d grupos de duplicados.", len(duplicados))

    for item in duplicados:
        print(f"\nCarpeta: {item['ruta']}")
        print(f"  Archivo: {item['nombre']}")
        cons = item["conservar"]
        print(f"  CONSERVAR: [ID: {cons['id']}]")
        print(f"    Fecha: {formatear_fecha(cons['modifiedDate'])} | "
              f"Tamaño: {formatear_tamanio(cons.get('fileSize'))}")
        for elim in item["eliminar"]:
            print(f"  ELIMINAR: [ID: {elim['id']}]")
            print(f"    Fecha: {formatear_fecha(elim['modifiedDate'])} | "
                  f"Tamaño: {formatear_tamanio(elim.get('fileSize'))}")
        print("-" * 50)

    total_a_eliminar = sum(len(item["eliminar"]) for item in duplicados)
    print(f"\nResumen: Se conservarán {len(duplicados)} y se moverán {total_a_eliminar} a papelera.")

    confirmar = input("\n¿Deseas proceder con la limpieza? (s/n): ").lower().strip()
    if confirmar != "s":
        logger.info("Limpieza omitida por el usuario.")
        return

    exitos = 0
    errores = 0
    for item in duplicados:
        for elim in item["eliminar"]:
            try:
                archivo = drive.CreateFile({"id": elim["id"]})
                archivo.Trash()
                exitos += 1
                logger.info("Movido a papelera: %s (%s)", item["nombre"], elim["id"])
            except Exception as e:
                errores += 1
                logger.error("Error con %s: %s", elim["id"], e)

    logger.info("Paso 3 completado. Exitos: %d | Errores: %d", exitos, errores)


def run(carpeta_local: str, drive_folder_id: str, pasos: list[int]) -> None:
    logger.info("PIPELINE DE CONTRATOS | Pasos: %s", pasos)

    carpeta_corregidos = os.path.join(carpeta_local, "contratos_corregidos")

    if 1 in pasos:
        resultado = paso_1_corregir(carpeta_local)
        if resultado is None and 2 in pasos:
            logger.warning("El paso 1 no generó archivos. Deteniendo paso 2.")
            pasos = [p for p in pasos if p != 2]
        elif resultado:
            carpeta_corregidos = resultado

    drive = None
    if 2 in pasos or 3 in pasos:
        logger.info("Autenticando con Google Drive...")
        drive = authenticate()
        logger.info("Autenticación exitosa.")

    if 2 in pasos:
        if not os.path.exists(carpeta_corregidos):
            logger.error("La carpeta '%s' no existe. Omitiendo paso 2.", carpeta_corregidos)
        else:
            paso_2_subir(drive, carpeta_corregidos, drive_folder_id)

    if 3 in pasos:
        paso_3_limpiar(drive, drive_folder_id)

    logger.info("PIPELINE FINALIZADO")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline: Corregir contratos -> Subir a Drive -> Limpiar duplicados."
    )
    parser.add_argument("carpeta_local", help="Ruta local de la carpeta con los PDFs originales.")
    parser.add_argument("drive_folder_id", help="ID de la carpeta principal en Google Drive.")
    parser.add_argument(
        "--pasos", nargs="+", type=int, choices=[1, 2, 3],
        help="Pasos a ejecutar (ej. --pasos 2 3). Por defecto: todos.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pasos = args.pasos if args.pasos else [1, 2, 3]
    try:
        run(args.carpeta_local, args.drive_folder_id, pasos)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except ContratosError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Pipeline interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
