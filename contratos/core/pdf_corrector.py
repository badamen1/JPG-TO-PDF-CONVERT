from __future__ import annotations

import glob
import os
import time
from typing import Tuple

import fitz  # PyMuPDF

from contratos.exceptions import PdfProcessingError
from contratos.logger import get_logger

logger = get_logger(__name__)

PATRONES_ESPECIFICO = ["No. 4 de 2025", "No. 3 de 2025", "No. 2 de 2023"]
PATRONES_INTERADMINISTRATIVO = ["No. 1203 de 2023"]


def _aplicar_reemplazo(page, patron_original: str, texto_nuevo: str) -> bool:
    """Redacta patron_original y escribe texto_nuevo. Retorna True si modificó."""
    instances = page.search_for(patron_original)
    if not instances:
        return False

    for inst in instances:
        page.add_redact_annot(fitz.Rect(inst.x0 - 1, inst.y0 - 1, inst.x1 + 1, inst.y1 + 1))
    page.apply_redactions()

    for inst in instances:
        page.draw_rect(
            fitz.Rect(inst.x0 - 2, inst.y0 - 2, inst.x1 + 2, inst.y1 + 2),
            color=None,
            fill=(1, 1, 1),
        )
        page.insert_text(
            point=fitz.Point(inst.x0, inst.y1 - (inst.height * 0.2)),
            text=texto_nuevo,
            fontsize=inst.height * 0.85,
            fontname="times-roman",
            color=(0, 0, 0),
        )
    return True


def corregir_contratos(input_folder: str, delete_old: bool = False) -> Tuple[int, int]:
    """Corrige patrones de texto en los PDFs de input_folder.

    Returns:
        (procesados, modificados)

    Raises:
        FileNotFoundError: si input_folder no existe.
        PdfProcessingError: si PyMuPDF no puede abrir un archivo PDF.
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"La carpeta de origen '{input_folder}' no existe.")

    if not delete_old:
        output_folder = os.path.join(input_folder, "contratos_corregidos")
        os.makedirs(output_folder, exist_ok=True)

    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    if not pdf_files:
        logger.info("No se encontraron archivos PDF en '%s'.", input_folder)
        return 0, 0

    procesados = 0
    modificados = 0
    logger.info("Iniciando procesamiento de %d contratos...", len(pdf_files))

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise PdfProcessingError(f"No se pudo abrir '{filename}': {e}") from e

        try:
            is_modified = False

            for page_num in range(len(doc)):
                page = doc[page_num]

                for patron in PATRONES_ESPECIFICO:
                    if page.search_for(f"Acuerdo Específico {patron}"):
                        if _aplicar_reemplazo(page, patron, "No. 4 de 2024"):
                            is_modified = True
                        break

                for patron in PATRONES_INTERADMINISTRATIVO:
                    if page.search_for(f"Contrato Interadministrativo {patron}"):
                        if _aplicar_reemplazo(page, patron, "No. 1465 de 2024"):
                            is_modified = True
                        break

            if is_modified:
                if delete_old:
                    temp_path = pdf_path + ".tmp"
                    doc.save(temp_path, garbage=4, deflate=True)
                    doc.close()
                    time.sleep(0.5)
                    for intento in range(3):
                        try:
                            os.replace(temp_path, pdf_path)
                            logger.info("[REEMPLAZADO] %s", filename)
                            break
                        except PermissionError:
                            if intento < 2:
                                time.sleep(1)
                            else:
                                logger.error(
                                    "No se pudo reemplazar '%s' tras 3 intentos.", filename
                                )
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                else:
                    output_path = os.path.join(
                        input_folder, "contratos_corregidos", filename
                    )
                    doc.save(output_path, garbage=4, deflate=True)
                    doc.close()
                    logger.info("[MODIFICADO] %s", filename)

                modificados += 1
            else:
                doc.close()
                logger.info("[SIN CAMBIOS] %s", filename)

            procesados += 1

        except Exception as e:
            doc.close()
            logger.error("Falló el procesamiento de '%s': %s", filename, e)
            procesados += 1

    logger.info(
        "Proceso completado. Revisados: %d | Modificados: %d", procesados, modificados
    )
    return procesados, modificados
