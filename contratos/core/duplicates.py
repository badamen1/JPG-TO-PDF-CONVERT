from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from contratos.logger import get_logger

logger = get_logger(__name__)


def obtener_ruta_carpeta(drive, folder_id: str) -> str:
    try:
        file = drive.CreateFile({"id": folder_id})
        file.FetchMetadata(fields="title")
        return file["title"]
    except Exception as e:
        logger.warning("No se pudo obtener nombre de carpeta %s: %s", folder_id, e)
        return folder_id


def buscar_duplicados_recursivo(
    drive, folder_id: str, ruta_actual: str = ""
) -> list[dict]:
    resultados = []
    nombre_carpeta = obtener_ruta_carpeta(drive, folder_id)
    ruta_completa = f"{ruta_actual}/{nombre_carpeta}" if ruta_actual else nombre_carpeta

    logger.info("Analizando: %s ...", ruta_completa)

    query = f"'{folder_id}' in parents and trashed=false"
    items = drive.ListFile(
        {"q": query, "fields": "items(id, title, mimeType, modifiedDate, fileSize)"}
    ).GetList()

    carpetas = [i for i in items if i["mimeType"] == "application/vnd.google-apps.folder"]
    archivos = [i for i in items if i["mimeType"] != "application/vnd.google-apps.folder"]

    grupos: dict[str, list] = defaultdict(list)
    for f in archivos:
        if f["title"].startswith("Contrato Nº"):
            grupos[f["title"]].append(f)

    for nombre, lista_archivos in grupos.items():
        if len(lista_archivos) > 1:
            lista_ordenada = sorted(
                lista_archivos, key=lambda x: x["modifiedDate"], reverse=True
            )
            resultados.append({
                "ruta": ruta_completa,
                "nombre": nombre,
                "conservar": lista_ordenada[0],
                "eliminar": lista_ordenada[1:],
            })

    for carpeta in carpetas:
        resultados.extend(
            buscar_duplicados_recursivo(drive, carpeta["id"], ruta_completa)
        )

    return resultados


def formatear_fecha(iso_date: str) -> str:
    try:
        dt = datetime.strptime(iso_date.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        logger.debug("No se pudo parsear fecha '%s', se devuelve original.", iso_date)
        return iso_date


def formatear_tamanio(bytes_str: str | None) -> str:
    if not bytes_str:
        return "0 B"
    try:
        b = int(bytes_str)
    except ValueError:
        logger.warning("fileSize no es numérico: %s", bytes_str)
        return "0 B"
    if b < 1024:
        return f"{b} B"
    if b < 1024 * 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b / (1024 * 1024):.2f} MB"
