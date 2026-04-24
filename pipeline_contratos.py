#!/usr/bin/env python3
"""Pipeline unificado: Corregir contratos → Subir a Drive → Limpiar duplicados.

Uso:
    python pipeline_contratos.py <CARPETA_LOCAL> <DRIVE_FOLDER_ID>

Ejemplo:
    python pipeline_contratos.py "C:\\Users\\bayro\\Desktop\\Contratos" 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs
"""
from __future__ import annotations

import argparse
import os
import sys
import glob
import re
from collections import defaultdict
from datetime import datetime

# Importar funciones de los módulos existentes
from corregir_contratos_pdf import corregir_contratos
from drive_uploader import authenticate, upload_file
from limpiar_duplicados_drive import (
    buscar_duplicados_recursivo,
    formatear_fecha,
    formatear_tamanio,
)


def paso_1_corregir(carpeta_local: str) -> str | None:
    """Paso 1: Corregir los PDFs y guardarlos en contratos_corregidos/.

    Returns:
        Ruta a la carpeta de contratos corregidos, o None si falló.
    """
    print("=" * 60)
    print("📝 PASO 1: CORRECCIÓN DE CONTRATOS")
    print("=" * 60)
    print()

    # Busca tanto "No. 4 de 2025" como "No. 3 de 2025" y los reemplaza por "No. 4 de 2024"
    # (La lógica multi-patrón está implementada en corregir_contratos_pdf.py)
    corregir_contratos(
        carpeta_local,
        text_to_find="No. 4 de 2025 / No. 3 de 2025",
        text_to_replace="No. 4 de 2024",
        delete_old=False,
    )

    carpeta_corregidos = os.path.join(carpeta_local, "contratos_corregidos")

    if not os.path.exists(carpeta_corregidos):
        print("⚠️  No se creó la carpeta 'contratos_corregidos'. Puede que no hubo archivos que corregir.")
        return None

    pdf_corregidos = glob.glob(os.path.join(carpeta_corregidos, "*.pdf"))
    if not pdf_corregidos:
        print("⚠️  La carpeta 'contratos_corregidos' está vacía.")
        return None

    print(f"\n✅ Paso 1 completado. {len(pdf_corregidos)} contratos corregidos en:")
    print(f"   {carpeta_corregidos}\n")
    return carpeta_corregidos


def paso_2_subir(drive, carpeta_corregidos: str, drive_folder_id: str) -> None:
    """Paso 2: Subir los contratos corregidos a sus carpetas en Drive."""
    print("=" * 60)
    print("☁️  PASO 2: SUBIDA A GOOGLE DRIVE")
    print("=" * 60)
    print()

    print("🔍 Obteniendo la lista de carpetas en Google Drive...")

    query = f"'{drive_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_list = drive.ListFile({"q": query, "maxResults": 1000}).GetList()

    if not folder_list:
        print("❌ No se encontraron carpetas dentro del ID de Drive proporcionado.")
        return

    # Crear mapa: código de 6 dígitos → ID de carpeta en Drive
    mapa_carpetas = {}
    for folder in folder_list:
        title = folder["title"].strip()
        match = re.search(r"(\d{6})", title)
        if match:
            mapa_carpetas[match.group(1)] = folder["id"]

    print(f"📁 {len(mapa_carpetas)} carpetas de clientes encontradas en Drive.\n")

    pdf_files = glob.glob(os.path.join(carpeta_corregidos, "*.pdf"))

    subidos = 0
    no_encontrados = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        name_only = os.path.splitext(filename)[0]
        match_pdf = re.search(r"(\d{6})", name_only)

        if not match_pdf:
            print(f"⏭️  [OMITIDO] Sin código de 6 dígitos: '{filename}'")
            no_encontrados += 1
            continue

        codigo = match_pdf.group(1)

        if codigo in mapa_carpetas:
            try:
                upload_file(drive, pdf_path, mapa_carpetas[codigo])
                print(f"✅ [SUBIDO] '{filename}' → carpeta {codigo}")
                subidos += 1
            except Exception as e:
                print(f"❌ [ERROR] Falló la subida de '{filename}': {e}")
        else:
            print(f"❓ [SIN CARPETA] '{filename}': No hay carpeta para código {codigo}")
            no_encontrados += 1

    print(f"\n✅ Paso 2 completado. Subidos: {subidos} | Sin destino: {no_encontrados}\n")


def paso_3_limpiar(drive, drive_folder_id: str) -> None:
    """Paso 3: Buscar y mover a papelera los contratos duplicados más antiguos."""
    print("=" * 60)
    print("🗑️  PASO 3: LIMPIEZA DE DUPLICADOS")
    print("=" * 60)
    print()

    duplicados = buscar_duplicados_recursivo(drive, drive_folder_id)

    if not duplicados:
        print("\n✅ ¡No se encontraron contratos duplicados! Todo limpio.")
        return

    print(f"\n⚠️  SE ENCONTRARON {len(duplicados)} GRUPOS DE DUPLICADOS:\n")

    for item in duplicados:
        print(f"📂 Carpeta: {item['ruta']}")
        print(f"   📄 Archivo: {item['nombre']}")

        cons = item['conservar']
        print(f"   ✅ CONSERVAR: [ID: {cons['id']}]")
        print(f"      Fecha: {formatear_fecha(cons['modifiedDate'])} | Tamaño: {formatear_tamanio(cons.get('fileSize'))}")

        for elim in item['eliminar']:
            print(f"   🗑️  ELIMINAR: [ID: {elim['id']}]")
            print(f"      Fecha: {formatear_fecha(elim['modifiedDate'])} | Tamaño: {formatear_tamanio(elim.get('fileSize'))}")
        print("-" * 50)

    total_a_eliminar = sum(len(item['eliminar']) for item in duplicados)
    print(f"\nResumen: Se conservarán {len(duplicados)} archivos y se moverán {total_a_eliminar} a la PAPELERA.")

    confirmar = input("\n¿Deseas proceder con la limpieza? (s/n): ").lower().strip()

    if confirmar == 's':
        print("\n🗑️  Moviendo archivos a la papelera...")
        exitos = 0
        errores = 0

        for item in duplicados:
            for elim in item['eliminar']:
                try:
                    archivo_drive = drive.CreateFile({'id': elim['id']})
                    archivo_drive.Trash()
                    exitos += 1
                    print(f"   ✅ Movido a papelera: {item['nombre']} ({elim['id']})")
                except Exception as e:
                    errores += 1
                    print(f"   ❌ Error con {elim['id']}: {e}")

        print(f"\n✅ Paso 3 completado. Éxitos: {exitos} | Errores: {errores}")
    else:
        print("\n⏭️  Limpieza omitida por el usuario.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline completo: Corregir contratos → Subir a Drive → Limpiar duplicados.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("carpeta_local", help="Ruta local de la carpeta con los PDFs originales.")
    parser.add_argument("drive_folder_id", help="ID de la carpeta principal en Google Drive.")
    parser.add_argument("--pasos", nargs="+", type=int, choices=[1, 2, 3],
                        help="Especifica qué pasos ejecutar separados por espacio (ej. --pasos 2 3). Si se omite, ejecuta todos.")
    args = parser.parse_args()

    print()
    print("🚀 PIPELINE DE CONTRATOS")
    print("   1. Corregir PDFs  →  2. Subir a Drive  →  3. Limpiar duplicados")
    print()

    pasos_ejecutar = args.pasos if args.pasos else [1, 2, 3]

    # Carpeta por defecto si omitimos el paso 1
    carpeta_corregidos = os.path.join(args.carpeta_local, "contratos_corregidos")

    # ── PASO 1: Corregir (local, no requiere Drive) ──
    if 1 in pasos_ejecutar:
        resultado = paso_1_corregir(args.carpeta_local)
        if resultado is None and 2 in pasos_ejecutar:
            print("⛔ El paso 1 no generó archivos. Deteniendo paso 2.")
            pasos_ejecutar.remove(2)

    # ── Autenticación única con Google Drive (solo necesaria para paso 2 y 3) ──
    if 2 in pasos_ejecutar or 3 in pasos_ejecutar:
        print("🔐 Autenticando con Google Drive...")
        try:
            drive = authenticate("credentials.json", "token.json")
        except Exception as e:
            print(f"❌ Error de autenticación: {e}")
            sys.exit(1)
        print("✅ Autenticación exitosa.\n")

    # ── PASO 2: Subir contratos corregidos ──
    if 2 in pasos_ejecutar:
        if not os.path.exists(carpeta_corregidos):
            print(f"❌ La carpeta '{carpeta_corregidos}' no existe. Omitiendo paso 2.")
        else:
            paso_2_subir(drive, carpeta_corregidos, args.drive_folder_id)

    # ── PASO 3: Limpiar duplicados ──
    if 3 in pasos_ejecutar:
        paso_3_limpiar(drive, args.drive_folder_id)

    print()
    print("=" * 60)
    print("🏁 PIPELINE FINALIZADO")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrumpido por el usuario.")
        sys.exit(0)
