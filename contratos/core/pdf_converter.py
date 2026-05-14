from __future__ import annotations

import os
import re
from typing import List, Tuple

from PIL import Image, UnidentifiedImageError

from contratos.logger import get_logger

logger = get_logger(__name__)

ALLOWED_EXT = {"png", "jpg", "jpeg"}
CC_PATTERN = re.compile(r"cc[12]", re.IGNORECASE)
PDF_SUBFOLDER = "_pdfs"


def is_allowed_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    return ext in ALLOWED_EXT


def is_cedula(filename: str) -> bool:
    name_only = os.path.splitext(filename)[0]
    return bool(CC_PATTERN.search(name_only))


def collect_images(paths: List[str]) -> List[str]:
    images: List[str] = []
    for p in paths:
        if os.path.isdir(p):
            try:
                for entry in sorted(os.listdir(p)):
                    fp = os.path.join(p, entry)
                    if os.path.isfile(fp) and is_allowed_file(fp):
                        images.append(fp)
            except Exception as e:
                logger.error("Error leyendo carpeta '%s': %s", p, e)
        elif os.path.isfile(p):
            if is_allowed_file(p):
                images.append(p)
            else:
                logger.warning("Omitido (extensión no permitida): %s", p)
        else:
            logger.warning("Omitido (no existe): %s", p)
    return images


def separate_images(folder: str) -> Tuple[List[str], List[str]]:
    all_images = collect_images([folder])
    cedula: List[str] = []
    other: List[str] = []
    for img_path in all_images:
        if is_cedula(os.path.basename(img_path)):
            cedula.append(img_path)
        else:
            other.append(img_path)
    return cedula, other


def convert_image_to_pdf(
    img_path: str, out_dir: str | None = None
) -> Tuple[bool, str | None]:
    try:
        with Image.open(img_path) as im:
            rgb = im.convert("RGB")
            base = os.path.splitext(os.path.basename(img_path))[0]
            pdf_name = f"{base}.pdf"
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, pdf_name)
            else:
                out_path = os.path.join(os.path.dirname(img_path), pdf_name)
            rgb.save(out_path, "PDF", resolution=100.0)
            logger.info("Convertido: '%s' -> '%s'", img_path, out_path)
            return True, out_path
    except UnidentifiedImageError:
        logger.error("'%s' no es una imagen válida o está corrupta.", img_path)
    except Exception as e:
        logger.error("Error procesando '%s': %s", img_path, e)
    return False, None


def merge_images_to_pdf(
    image_paths: List[str],
    out_dir: str | None = None,
    pdf_name: str = "combined",
) -> Tuple[bool, str | None]:
    if not image_paths:
        logger.error("No hay imágenes para combinar.")
        return False, None

    images_rgb: List[Image.Image] = []
    try:
        for img_path in image_paths:
            try:
                im = Image.open(img_path)
                images_rgb.append(im.convert("RGB"))
                logger.info("Añadido al PDF: '%s'", img_path)
            except UnidentifiedImageError:
                logger.error("'%s' no es una imagen válida o está corrupta.", img_path)
            except Exception as e:
                logger.error("Error cargando '%s': %s", img_path, e)

        if not images_rgb:
            logger.error("No se pudieron cargar imágenes válidas para combinar.")
            return False, None

        if not pdf_name.endswith(".pdf"):
            pdf_name = f"{pdf_name}.pdf"

        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, pdf_name)
        else:
            out_path = os.path.join(os.path.dirname(image_paths[0]) or ".", pdf_name)

        first_image = images_rgb[0]
        rest_images = images_rgb[1:]

        first_image.save(
            out_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=rest_images,
        )
        logger.info("PDF combinado creado: '%s' (%d páginas)", out_path, len(images_rgb))
        return True, out_path

    except Exception as e:
        logger.error("Error creando PDF combinado: %s", e)
        return False, None
    finally:
        for im in images_rgb:
            im.close()


def process_client(client_folder: str) -> List[str]:
    """Genera PDFs de un cliente y retorna sus rutas (generados + ya existentes)."""
    client_name = os.path.basename(client_folder)
    pdf_dir = os.path.join(client_folder, PDF_SUBFOLDER)
    os.makedirs(pdf_dir, exist_ok=True)

    cedula_imgs, other_imgs = separate_images(client_folder)
    pdfs: List[str] = []

    for entry in sorted(os.listdir(client_folder)):
        fp = os.path.join(client_folder, entry)
        if os.path.isfile(fp) and entry.lower().endswith(".pdf"):
            pdfs.append(fp)
            logger.info("PDF existente: %s", entry)

    if cedula_imgs:
        cedula_pdf_name = f"CEDULA_{client_name}"
        ok, cedula_path = merge_images_to_pdf(cedula_imgs, pdf_dir, cedula_pdf_name)
        if ok and cedula_path:
            pdfs.append(cedula_path)

    for img in other_imgs:
        ok, pdf_path = convert_image_to_pdf(img, pdf_dir)
        if ok and pdf_path:
            pdfs.append(pdf_path)

    return pdfs
