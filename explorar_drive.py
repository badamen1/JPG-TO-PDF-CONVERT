#!/usr/bin/env python3
"""Explora y muestra el árbol de carpetas de Google Drive.

Uso:
    python explorar_drive.py <FOLDER_ID>

Ejemplo:
    python explorar_drive.py 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms

El FOLDER_ID es el código que aparece en la URL de Google Drive:
    https://drive.google.com/drive/folders/<FOLDER_ID>
"""
from __future__ import annotations

import argparse
import sys

from drive_uploader import authenticate


def listar_contenido(drive, folder_id: str, nombre: str, prefijo: str = "", es_ultimo: bool = True) -> None:
    """Recorre recursivamente las carpetas y muestra la cantidad de archivos.

    Args:
        drive: Instancia autenticada de GoogleDrive.
        folder_id: ID de la carpeta actual a explorar.
        nombre: Nombre de la carpeta actual.
        prefijo: Prefijo de indentación.
        es_ultimo: Si es el último elemento del nivel actual.
    """
    # 1. Consultar subcarpetas
    query_carpetas = (
        f"'{folder_id}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )
    
    # 2. Consultar cantidad de archivos (solo para contar)
    query_archivos = (
        f"'{folder_id}' in parents and "
        f"mimeType != 'application/vnd.google-apps.folder' and "
        f"trashed=false"
    )

    try:
        subcarpetas = drive.ListFile({"q": query_carpetas, "maxResults": 1000}).GetList()
        # Para archivos solo necesitamos el total, optimizamos pidiendo solo el ID
        archivos_list = drive.ListFile({"q": query_archivos, "maxResults": 1000, "fields": "items(id)"}).GetList()
        num_archivos = len(archivos_list)
    except Exception as e:
        print(f"{prefijo}{'└── ' if es_ultimo else '├── '}📁 {nombre} ❌ Error: {e}")
        return

    # Imprimir la carpeta actual con el conteo de archivos
    info_archivos = f" ({num_archivos} archivos)" if num_archivos > 0 else " (vacía)"
    conector = "└── " if es_ultimo else "├── "
    print(f"{prefijo}{conector}📁 {nombre}{info_archivos}")

    prefijo_hijo = prefijo + ("    " if es_ultimo else "│   ")

    # Ordenar subcarpetas alfabéticamente
    subcarpetas = sorted(subcarpetas, key=lambda f: f["title"].lower())

    for i, carpeta in enumerate(subcarpetas):
        es_ultima_sub = (i == len(subcarpetas) - 1)
        listar_contenido(
            drive,
            folder_id=carpeta["id"],
            nombre=carpeta["title"],
            prefijo=prefijo_hijo,
            es_ultimo=es_ultima_sub,
        )


def obtener_nombre_carpeta(drive, folder_id: str) -> str:
    """Obtiene el nombre de una carpeta dado su ID.

    Args:
        drive: Instancia autenticada de GoogleDrive.
        folder_id: ID de la carpeta en Drive.

    Returns:
        El título de la carpeta o el folder_id si no se puede obtener.
    """
    try:
        carpeta = drive.CreateFile({"id": folder_id})
        carpeta.FetchMetadata(fields="title")
        return carpeta["title"]
    except Exception:
        return folder_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Explora y muestra el árbol de carpetas y archivos de una dirección de Google Drive.\n\n"
            "El FOLDER_ID está en la URL de Drive:\n"
            "  https://drive.google.com/drive/folders/<FOLDER_ID>"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "folder_id",
        help="ID (código) de la carpeta raíz en Google Drive.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    folder_id = args.folder_id.strip()

    print("🔐 Autenticando con Google Drive...")
    try:
        drive = authenticate("credentials.json", "token.json")
    except SystemExit:
        raise
    except Exception as e:
        print(f"❌ Error al autenticar: {e}", file=sys.stderr)
        sys.exit(1)

    print("✅ Autenticación exitosa.\n")

    # Obtener el nombre real de la carpeta raíz
    nombre_raiz = obtener_nombre_carpeta(drive, folder_id)

    print(f"📂 Explorando dirección: {nombre_raiz}")
    print(f"   ID: {folder_id}\n")
    print(f"🌲 Árbol de contenido:\n")

    # Iniciar recorrido recursivo
    # Simplemente llamamos a listar_contenido para la raíz, pero manejando el prefijo
    # para que no parezca una subcarpeta de sí misma
    
    # Primero listamos la raíz manualmente
    print(f"📁 {nombre_raiz} (raíz)")
    
    # Luego sus hijos (carpetas y archivos)
    query_carpetas = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    query_archivos = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed=false"
    
    try:
        carpetas_raiz = drive.ListFile({"q": query_carpetas, "maxResults": 1000}).GetList()
        archivos_raiz = drive.ListFile({"q": query_archivos, "maxResults": 1000}).GetList()
    except Exception as e:
        print(f"❌ Error al leer la carpeta raíz: {e}", file=sys.stderr)
        sys.exit(1)

    carpetas_raiz = sorted(carpetas_raiz, key=lambda f: f["title"].lower())
    archivos_raiz = sorted(archivos_raiz, key=lambda f: f["title"].lower())

    if not carpetas_raiz and not archivos_raiz:
        print("    (vacía)")
    else:
        # Carpetas raíz
        for i, carpeta in enumerate(carpetas_raiz):
            es_ultimo = (i == len(carpetas_raiz) - 1) and (len(archivos_raiz) == 0)
            listar_contenido(drive, carpeta["id"], carpeta["title"], "", es_ultimo)
        
        # Archivos raíz
        for i, archivo in enumerate(archivos_raiz):
            es_ultimo = (i == len(archivos_raiz) - 1)
            conector = "└── " if es_ultimo else "├── "
            print(f"{conector}{archivo['title']}")

    print(f"\n✅ Exploración completada.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Exploración interrumpida por el usuario.")
        sys.exit(0)
