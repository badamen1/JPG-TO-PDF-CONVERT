#!/usr/bin/env python3
"""Limpia contratos duplicados en Google Drive de forma recursiva.

Busca archivos con el mismo nombre que sigan el patrón 'Contrato Nº *',
compara sus fechas de modificación y mueve los más antiguos a la papelera.

Uso:
    python limpiar_duplicados_drive.py <FOLDER_ID>
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime

from drive_uploader import authenticate


def obtener_ruta_carpeta(drive, folder_id: str) -> str:
    """Intenta obtener la ruta legible de una carpeta (solo para fines de reporte)."""
    try:
        file = drive.CreateFile({'id': folder_id})
        file.FetchMetadata(fields='title')
        return file['title']
    except:
        return folder_id


def buscar_duplicados_recursivo(drive, folder_id: str, ruta_actual: str = "") -> list[dict]:
    """Recorre carpetas y encuentra grupos de duplicados."""
    resultados = []
    nombre_carpeta = obtener_ruta_carpeta(drive, folder_id)
    ruta_completa = f"{ruta_actual}/{nombre_carpeta}" if ruta_actual else nombre_carpeta
    
    print(f"🔍 Analizando: {ruta_completa} ...")

    # 1. Obtener archivos y subcarpetas en una sola pasada (o dos queries simples)
    query = f"'{folder_id}' in parents and trashed=false"
    items = drive.ListFile({"q": query, "fields": "items(id, title, mimeType, modifiedDate, fileSize)"}).GetList()

    carpetas = [i for i in items if i['mimeType'] == 'application/vnd.google-apps.folder']
    archivos = [i for i in items if i['mimeType'] != 'application/vnd.google-apps.folder']

    # 2. Agrupar archivos por nombre
    grupos = defaultdict(list)
    for f in archivos:
        if f['title'].startswith("Contrato Nº"):
            grupos[f['title']].append(f)

    # 3. Identificar duplicados reales (mismo nombre, >= 2 archivos)
    for nombre, lista_archivos in grupos.items():
        if len(lista_archivos) > 1:
            # Ordenar por fecha de modificación descendente (más nuevo primero)
            lista_ordenada = sorted(
                lista_archivos, 
                key=lambda x: x['modifiedDate'], 
                reverse=True
            )
            #aqui
            a_conservar = lista_ordenada[0]
            a_eliminar = lista_ordenada[1:]
            
            resultados.append({
                "ruta": ruta_completa,
                "nombre": nombre,
                "conservar": a_conservar,
                "eliminar": a_eliminar
            })

    # 4. Recursión
    for carpeta in carpetas:
        resultados.extend(buscar_duplicados_recursivo(drive, carpeta['id'], ruta_completa))
    
    return resultados


def formatear_fecha(iso_date: str) -> str:
    """Convierte fecha ISO de Drive a formato legible."""
    try:
        dt = datetime.strptime(iso_date.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_date


def formatear_tamanio(bytes_str: str | None) -> str:
    """Formatea el tamaño en bytes a KB/MB."""
    if not bytes_str: return "0 B"
    b = int(bytes_str)
    if b < 1024: return f"{b} B"
    if b < 1024*1024: return f"{b/1024:.2f} KB"
    return f"{b/(1024*1024):.2f} MB"


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpia contratos duplicados en Drive.")
    parser.add_argument("folder_id", help="ID de la carpeta raíz en Google Drive.")
    args = parser.parse_args()

    print("🔐 Autenticando con Google Drive...")
    try:
        drive = authenticate("credentials.json", "token.json")
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        sys.exit(1)

    print("\n🚀 Iniciando búsqueda de duplicados (esto puede tardar según el tamaño)...")
    duplicados = buscar_duplicados_recursivo(drive, args.folder_id)

    if not duplicados:
        print("\n✅ ¡No se encontraron contratos duplicados!")
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
        
        print(f"\n✨ Proceso finalizado. Exitos: {exitos}, Errores: {errores}.")
        print("Los archivos están ahora en tu papelera de Drive.")
    else:
        print("\n❌ Operación cancelada por el usuario.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido.")
        sys.exit(0)
