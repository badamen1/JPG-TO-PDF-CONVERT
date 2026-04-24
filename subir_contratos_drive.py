import os
import sys
import glob
import re
import argparse

# Importamos las funciones de tu módulo existente que ya tienes configurado
from drive_uploader import authenticate, upload_file

def subir_contratos_a_drive(carpeta_local, drive_folder_id):
    """
    Sube los contratos en PDF desde una carpeta local a las subcarpetas 
    correspondientes en Google Drive basándose en las últimas 6 cifras.
    """
    if not os.path.exists(carpeta_local):
        print(f"❌ [ERROR] La carpeta local '{carpeta_local}' no existe.")
        return

    print("🔐 Autenticando con Google Drive...")
    try:
        # Usamos tu función authenticate de drive_uploader.py
        drive = authenticate("credentials.json", "token.json")
    except Exception as e:
        print(f"❌ Error al autenticar: {e}")
        return

    print("✅ Autenticación exitosa.\n")
    print("🔍 Obteniendo la lista de carpetas en Google Drive...")
    
    # 1. Obtener todas las subcarpetas dentro de la carpeta padre en Drive
    query = f"'{drive_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_list = drive.ListFile({"q": query, "maxResults": 1000}).GetList()
    
    if not folder_list:
        print("❌ No se encontraron carpetas dentro del ID de Drive proporcionado.")
        return

    # 2. Crear un catálogo en vivo donde la llave es el número de contrato y el valor es el ID de la carpeta en Drive
    mapa_carpetas = {}
    for folder in folder_list:
        title = folder["title"].strip()
        
        # Buscar el bloque de código de contrato usando expresiones regulares (6 dígitos consecutivos al final o cerca del final)
        match = re.search(r"(\d{6})", title)
        if match:
            numero_contrato = match.group(1)
            # Guardamos el ID de esta carpeta en el diccionario usando su número como llave (ejemplo: '001253' -> '1Azx...')
            mapa_carpetas[numero_contrato] = folder["id"]

    print(f"📁 Encontramos {len(mapa_carpetas)} carpetas de clientes registradas en Drive con un código numérico.")
    
    # 3. Leer los PDFs que queremos subir
    pdf_files = glob.glob(os.path.join(carpeta_local, "*.pdf"))
    
    if not pdf_files:
        print(f"⚠️ No hay archivos PDF en la carpeta '{carpeta_local}'.")
        return

    print(f"\n🚀 Iniciando subida de {len(pdf_files)} contratos...\n")

    subidos = 0
    no_encontrados = 0

    # 4. Procesar y subir cada PDF
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        
        # Extraemos el nombre del archivo sin la extensión .pdf
        name_only = os.path.splitext(filename)[0]
        
        # Extraemos el código del PDF (asumiendo formato "Contrato Nº 001253") buscando directamente sus 6 números
        match_pdf = re.search(r"(\d{6})", name_only)
        
        if not match_pdf:
            print(f"⏭️  [OMITIDO] No se pudo detectar un código de 6 dígitos en: '{filename}'")
            no_encontrados += 1
            continue
            
        codigo_pdf = match_pdf.group(1)
        
        # 5. Verificamos si encontramos una carpeta que coincida
        if codigo_pdf in mapa_carpetas:
            folder_id_destino = mapa_carpetas[codigo_pdf]
            
            try:
                # Usamos tu función upload_file de drive_uploader.py
                upload_file(drive, pdf_path, folder_id_destino)
                print(f"✅ [SUBIDO] '{filename}' -> a la carpeta con código {codigo_pdf}")
                subidos += 1
            except Exception as e:
                print(f"❌ [ERROR] Falló la subida de '{filename}': {e}")
                
        else:
            print(f"❓ [SIN CARPETA] '{filename}': No hay ninguna carpeta en Drive para el código {codigo_pdf}")
            no_encontrados += 1

    # 6. Mostrar el resumen en la consola
    print(f"\n{'='*40}")
    print(f"📊 RESUMEN FINAL")
    print(f"{'='*40}")
    print(f"Total PDFs analizados: {len(pdf_files)}")
    print(f"✅ PDFs subidos con éxito: {subidos}")
    print(f"⚠️  PDFs sin carpeta destino en Drive: {no_encontrados}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sube contratos corregidos a sus respectivas subcarpetas en Google Drive.")
    parser.add_argument("carpeta_local", help="Ruta local donde están los PDFs (ej. 'C:\\Contratos')")
    parser.add_argument("drive_folder_id", help="El ID de la carpeta principal en Google Drive que contiene las subcarpetas de los usuarios.")
    
    args = parser.parse_args()

    subir_contratos_a_drive(args.carpeta_local, args.drive_folder_id)
