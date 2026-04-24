import fitz  # PyMuPDF
import os
import sys
import argparse
import glob
import traceback
import time


def corregir_contratos(input_folder, text_to_find, text_to_replace, delete_old=False):
    """
    Busca y reemplaza un texto específico en los PDFs de una carpeta.
    Si delete_old=True, sobreescribe los archivos originales.
    Si delete_old=False, los guarda en una subcarpeta 'contratos_corregidos'.
    """
    # 1. Verificar que la carpeta de entrada exista
    if not os.path.exists(input_folder):
        print(f"[ERROR] La carpeta de origen '{input_folder}' no existe.")
        return

    # 2. Crear la carpeta de salida si no estamos en modo "reemplazar"
    if not delete_old:
        output_folder = os.path.join(input_folder, "contratos_corregidos")
        os.makedirs(output_folder, exist_ok=True)

    # 3. Buscar todos los archivos PDF en la carpeta
    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))

    if not pdf_files:
        print(f"[INFO] No se encontraron archivos PDF en '{input_folder}'.")
        return

    procesados = 0
    modificados = 0
    print(f"Iniciando el procesamiento de {len(pdf_files)} contratos...\n")

    # 4. Procesar cada archivo PDF
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)

        try:
            doc = fitz.open(pdf_path)
            is_modified = False

            # Recorrer cada página del contrato
            for page_num in range(len(doc)):
                page = doc[page_num]

                # -------------------------------------------------------
                # BLOQUE 1: Acuerdo Específico
                # -------------------------------------------------------
                PATRONES_ESPECIFICO = ["No. 4 de 2025", "No. 3 de 2025", "No. 2 de 2023"]

                context_found = False
                patron_encontrado = None

                for patron in PATRONES_ESPECIFICO:
                    if page.search_for(f"Acuerdo Específico {patron}"):
                        context_found = True
                        patron_encontrado = patron
                        break

                if context_found:
                    number_instances = page.search_for(patron_encontrado)

                    if number_instances:
                        is_modified = True

                        for inst in number_instances:
                            redact_rect = fitz.Rect(
                                inst.x0 - 1, inst.y0 - 1,
                                inst.x1 + 1, inst.y1 + 1
                            )
                            page.add_redact_annot(redact_rect)

                        page.apply_redactions()

                        for inst in number_instances:
                            # Pintar un rect blanco para tapar completamente el texto viejo
                            cover_rect = fitz.Rect(
                                inst.x0 - 2, inst.y0 - 2,
                                inst.x1 + 2, inst.y1 + 2
                            )
                            page.draw_rect(cover_rect, color=None, fill=(1, 1, 1))

                            fontsize = inst.height * 0.85
                            text_origin = fitz.Point(inst.x0, inst.y1 - (inst.height * 0.2))
                            page.insert_text(
                                point=text_origin,
                                text="No. 4 de 2024",
                                fontsize=fontsize,
                                fontname="times-roman",
                                color=(0, 0, 0)
                            )

                # -------------------------------------------------------
                # BLOQUE 2: Contrato Interadministrativo  ← BUG CORREGIDO
                # (ahora está dentro del for page_num y con indentación correcta)
                # -------------------------------------------------------
                PATRONES_INTERADMINISTRATIVO = ["No. 1203 de 2023"]

                context_found = False
                patron_encontrado = None

                for patron in PATRONES_INTERADMINISTRATIVO:
                    if page.search_for(f"Contrato Interadministrativo {patron}"):
                        context_found = True
                        patron_encontrado = patron
                        break

                if context_found:
                    number_instances = page.search_for(patron_encontrado)

                    if number_instances:
                        is_modified = True

                        for inst in number_instances:
                            redact_rect = fitz.Rect(
                                inst.x0 - 1, inst.y0 - 1,
                                inst.x1 + 1, inst.y1 + 1
                            )
                            page.add_redact_annot(redact_rect)

                        page.apply_redactions()

                        for inst in number_instances:
                            # Pintar un rect blanco para tapar completamente el texto viejo
                            cover_rect = fitz.Rect(
                                inst.x0 - 2, inst.y0 - 2,
                                inst.x1 + 2, inst.y1 + 2
                            )
                            page.draw_rect(cover_rect, color=None, fill=(1, 1, 1))

                            fontsize = inst.height * 0.85
                            text_origin = fitz.Point(inst.x0, inst.y1 - (inst.height * 0.2))
                            page.insert_text(
                                point=text_origin,
                                text="No. 1465 de 2024",
                                fontsize=fontsize,
                                fontname="times-roman",
                                color=(0, 0, 0)
                            )

            # 5. Guardar el archivo solo si tuvo modificaciones
            if is_modified:
                if delete_old:
                    temp_path = pdf_path + ".tmp"
                    doc.save(temp_path, garbage=4, deflate=True)

                    # Cerrar explícitamente para liberar el candado en Windows
                    doc.close()

                    # Pequeña pausa para que Windows registre que el archivo fue soltado
                    time.sleep(0.5)

                    # Reintentos por si un antivirus tiene el archivo bloqueado
                    for intento in range(3):
                        try:
                            os.replace(temp_path, pdf_path)
                            print(f"✅ [REEMPLAZADO Y BORRADO EL VIEJO] {filename}")
                            break
                        except PermissionError:
                            if intento < 2:
                                time.sleep(1)
                            else:
                                print(f"❌ [ERROR] No se pudo reemplazar '{filename}' tras 3 intentos.")
                                # Limpiar el temporal huérfano
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                else:
                    output_path = os.path.join(input_folder, "contratos_corregidos", filename)
                    doc.save(output_path, garbage=4, deflate=True)
                    doc.close()
                    print(f"✅ [MODIFICADO] {filename}")

                modificados += 1

            else:
                doc.close()
                print(f"⚠️  [SIN CAMBIOS] {filename} (No se encontró el texto exacto)")

            procesados += 1

        except Exception as e:
            print(f"❌ [ERROR] Falló el procesamiento de '{filename}'.")
            print(f"Detalle: {str(e)}")
            traceback.print_exc()

    # 6. Mostrar el resumen en la consola
    print(f"\n--- RESUMEN ---")
    print(f"Contratos revisados: {procesados}")
    print(f"Contratos modificados y guardados: {modificados}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corrige el texto de contratos en formato PDF.")
    parser.add_argument("carpeta", help="Ruta de la carpeta que contiene los contratos a corregir")
    parser.add_argument(
        "-d", "--delete",
        action="store_true",
        help="Reemplaza los archivos modificados y borra los originales"
    )
    args = parser.parse_args()

    CARPETA_ORIGEN = args.carpeta
    DELETE_OLD = args.delete

    TEXTO_BUSCAR = "No. 4 de 2025 / No. 3 de 2025"
    TEXTO_REEMPLAZO = "No. 4 de 2024"

    corregir_contratos(CARPETA_ORIGEN, TEXTO_BUSCAR, TEXTO_REEMPLAZO, delete_old=DELETE_OLD)