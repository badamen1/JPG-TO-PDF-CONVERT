from __future__ import annotations

import argparse
import sys

from contratos.core.drive_client import authenticate
from contratos.core.duplicates import (
    buscar_duplicados_recursivo,
    formatear_fecha,
    formatear_tamanio,
)
from contratos.exceptions import ContratosError, DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)


def run(folder_id: str) -> None:
    logger.info("Autenticando con Google Drive...")
    drive = authenticate()

    logger.info("Iniciando búsqueda de duplicados...")
    duplicados = buscar_duplicados_recursivo(drive, folder_id)

    if not duplicados:
        logger.info("No se encontraron contratos duplicados.")
        return

    logger.warning("Se encontraron %d grupos de duplicados:", len(duplicados))

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
        logger.info("Operación cancelada por el usuario.")
        return

    logger.info("Moviendo archivos a la papelera...")
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

    logger.info("Proceso finalizado. Exitos: %d | Errores: %d", exitos, errores)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Limpia contratos duplicados en Drive.")
    parser.add_argument("folder_id", help="ID de la carpeta raíz en Google Drive.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.folder_id)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except ContratosError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
