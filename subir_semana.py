#!/usr/bin/env python3
"""Sube una semana completa de clientes a Google Drive.

Uso:
  python subir_semana.py --ruta_local "C:/Proyecto/Yoro/Semana 8" --drive_folder_id "ID_CARPETA"

Para cada carpeta de cliente encontrada:
  1. Une imágenes CC1/CC2 (cédula) en un solo PDF.
  2. Convierte el resto de imágenes a PDFs individuales.
  3. Guarda los PDFs en _pdfs/ dentro de la carpeta del cliente.
  4. Crea una carpeta con el nombre del cliente en Drive.
  5. Sube todos los PDFs generados.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import List, Tuple

# Reusar funciones existentes del módulo de conversión (DRY)
from convert_images_to_pdf import (
    collect_images as _collect_all_images,
    merge_images_to_pdf,
    convert_image_to_pdf,
)
from drive_uploader import authenticate, create_folder, find_folder, upload_file

# ─────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────
CC_PATTERN = re.compile(r"cc[12]", re.IGNORECASE)
PDF_SUBFOLDER = "_pdfs"


# ─────────────────────────────────────────────────────────────
# Funciones auxiliares
# ─────────────────────────────────────────────────────────────
def is_cedula(filename: str) -> bool:
    """Detecta si el nombre del archivo corresponde a una cédula (CC1/CC2)."""
    name_only = os.path.splitext(filename)[0]
    return bool(CC_PATTERN.search(name_only))


def separate_images(folder: str) -> Tuple[List[str], List[str]]:
    """Recopila imágenes de una carpeta separando cédulas del resto.

    Usa collect_images del módulo existente y luego filtra.

    Returns:
        (cedula_images, other_images)
    """
    all_images = _collect_all_images([folder])
    cedula: List[str] = []
    other: List[str] = []

    for img_path in all_images:
        if is_cedula(os.path.basename(img_path)):
            cedula.append(img_path)
        else:
            other.append(img_path)

    return cedula, other


# ─────────────────────────────────────────────────────────────
# Procesamiento de un cliente
# ─────────────────────────────────────────────────────────────
def process_client(client_folder: str) -> List[str]:
    """Procesa una carpeta de cliente: genera PDFs y recoge los existentes.

    Returns:
        Lista de rutas a PDFs (generados + ya existentes en la carpeta).
    """
    client_name = os.path.basename(client_folder)
    pdf_dir = os.path.join(client_folder, PDF_SUBFOLDER)
    os.makedirs(pdf_dir, exist_ok=True)

    cedula_imgs, other_imgs = separate_images(client_folder)
    pdfs: List[str] = []

    # 1. Recoger PDFs que ya existen directamente en la carpeta del cliente
    for entry in sorted(os.listdir(client_folder)):
        fp = os.path.join(client_folder, entry)
        if os.path.isfile(fp) and entry.lower().endswith(".pdf"):
            pdfs.append(fp)
            print(f"    📎 PDF existente: {entry}")

    # 2. Unir cédulas en un solo PDF (reusar merge_images_to_pdf)
    if cedula_imgs:
        cedula_pdf_name = f"CEDULA_{client_name}"
        ok, cedula_path = merge_images_to_pdf(cedula_imgs, pdf_dir, cedula_pdf_name)
        if ok and cedula_path:
            pdfs.append(cedula_path)
            print(f"    📄 {cedula_pdf_name}.pdf ({len(cedula_imgs)} imágenes)")
        else:
            print(f"    ⚠ No se pudo crear PDF de cédula", file=sys.stderr)

    # 3. Convertir el resto de imágenes a PDFs individuales (reusar convert_image_to_pdf)
    for img in other_imgs:
        ok, pdf_path = convert_image_to_pdf(img, pdf_dir)
        if ok and pdf_path:
            pdfs.append(pdf_path)
            print(f"    📄 {os.path.basename(pdf_path)}")

    return pdfs


# ─────────────────────────────────────────────────────────────
# Subida a Drive
# ─────────────────────────────────────────────────────────────
SKIPPED = "omitido"  # sentinel para clientes ignorados


def upload_client_to_drive(drive, client_name: str, pdfs: List[str],
                           parent_folder_id: str) -> str:
    """Crea carpeta del cliente en Drive y sube sus PDFs.

    Verifica si la carpeta ya existe en Drive antes de subir.

    Returns:
        'ok'      → subida exitosa
        'omitido' → carpeta ya existía en Drive (se omite)
        'error'   → ocurrió un error
    """
    try:
        existing_id = find_folder(drive, client_name, parent_folder_id)
        if existing_id:
            print(f"    ⏭  Ya existe en Drive, se omite: {client_name}")
            return SKIPPED

        folder_id = create_folder(drive, client_name, parent_folder_id)
        print(f"    📁 Carpeta creada en Drive: {client_name}")

        for pdf_path in pdfs:
            upload_file(drive, pdf_path, folder_id)
            print(f"    ☁️  Subido: {os.path.basename(pdf_path)}")

        return "ok"
    except Exception as e:
        print(f"    ❌ Error subiendo '{client_name}': {e}", file=sys.stderr)
        return "error"


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="subir_semana",
        description="Sube una semana completa de clientes a Google Drive.",
        epilog="Ejemplo:\n"
               '  python subir_semana.py --ruta_local "C:/Proyecto/Yoro/Semana 8" '
               '--drive_folder_id "1ABCxyz..."',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ruta_local", required=True,
        help="Ruta a la carpeta de la semana (contiene subcarpetas de clientes)",
    )
    parser.add_argument(
        "--drive_folder_id", required=True,
        help="ID de la carpeta destino en Google Drive (ya debe existir)",
    )
    parser.add_argument(
        "--credentials", default="credentials.json",
        help="Ruta al archivo credentials.json (default: credentials.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    ruta_local = os.path.abspath(args.ruta_local)
    if not os.path.isdir(ruta_local):
        print(f"❌ La ruta no existe o no es una carpeta: {ruta_local}",
              file=sys.stderr)
        sys.exit(1)

    # Listar subcarpetas (clientes), ignorar carpetas con prefijo _
    client_folders = sorted([
        os.path.join(ruta_local, d)
        for d in os.listdir(ruta_local)
        if os.path.isdir(os.path.join(ruta_local, d)) and not d.startswith("_")
    ])

    if not client_folders:
        print("❌ No se encontraron carpetas de clientes.", file=sys.stderr)
        sys.exit(1)

    semana_name = os.path.basename(ruta_local)
    print(f"\n{'='*60}")
    print(f"  📂 Semana: {semana_name}")
    print(f"  👥 Clientes encontrados: {len(client_folders)}")
    print(f"  🎯 Drive folder ID: {args.drive_folder_id}")
    print(f"{'='*60}\n")

    # Autenticar con Drive
    print("🔐 Autenticando con Google Drive...")
    credentials_file = os.path.abspath(args.credentials)
    token_file = os.path.join(os.path.dirname(credentials_file), "token.json")
    drive = authenticate(credentials_file, token_file)
    print("✅ Autenticación exitosa.\n")

    # Procesar cada cliente
    start_time = time.time()
    results = []  # (client_name, num_pdfs, status: 'ok'|'omitido'|'error'|'sin_archivos')

    for i, client_folder in enumerate(client_folders, 1):
        client_name = os.path.basename(client_folder)
        print(f"[{i}/{len(client_folders)}] 👤 {client_name}")
        print(f"  {'─'*40}")

        # Generar/recoger PDFs
        print("  📝 Revisando archivos...")
        pdfs = process_client(client_folder)

        if not pdfs:
            print(f"  ⚠ Sin archivos para procesar.")
            results.append((client_name, 0, "sin_archivos"))
            print()
            continue

        # Subir a Drive (verifica si ya existe)
        print(f"  ☁️  Procesando en Drive ({len(pdfs)} archivo(s))...")
        status = upload_client_to_drive(
            drive, client_name, pdfs, args.drive_folder_id
        )
        results.append((client_name, len(pdfs), status))
        print()

    # ─── Resumen Final ───
    elapsed = time.time() - start_time
    total = len(results)
    n_ok      = sum(1 for _, _, s in results if s == "ok")
    n_skip    = sum(1 for _, _, s in results if s == SKIPPED)
    n_fail    = sum(1 for _, _, s in results if s == "error")
    n_empty   = sum(1 for _, _, s in results if s == "sin_archivos")
    total_pdfs = sum(n for _, n, _ in results)

    print(f"\n{'='*60}")
    print(f"  📊 RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  ⏱  Tiempo total: {elapsed:.1f} segundos")
    print(f"  👥 Clientes encontrados: {total}")
    print(f"  ✅ Subidos: {n_ok}")
    if n_skip:
        print(f"  ⏭  Omitidos (ya en Drive): {n_skip}")
    if n_empty:
        print(f"  ⚠  Sin archivos: {n_empty}")
    if n_fail:
        print(f"  ❌ Fallidos: {n_fail}")
    print(f"  📄 Total archivos procesados: {total_pdfs}")
    print()

    # Detalle por cliente
    estado_icon = {"ok": "✅", SKIPPED: "⏭ ", "error": "❌", "sin_archivos": "⚠ "}
    print(f"  {'Cliente':<30} {'Archivos':>8}  {'Estado':>10}")
    print(f"  {'─'*30} {'─'*8}  {'─'*10}")
    for name, num, st in results:
        icon = estado_icon.get(st, "❓")
        print(f"  {name:<30} {num:>8}  {icon:>10}")

    print(f"\n{'='*60}")

    if n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
