
#!/usr/bin/env python3
"""Convertir imágenes (PNG/JPG/JPEG) a PDFs desde CLI.

Uso:
  python convert_images_to_pdf.py ruta1 ruta2 carpeta1 -o salida
  python convert_images_to_pdf.py ruta1 ruta2 -m -n documento_combinado

Soporta múltiples archivos y carpetas:
  - Por defecto: Para cada imagen genera un PDF con el mismo nombre.
  - Con --merge: Combina todas las imágenes en un único PDF.
"""
from __future__ import annotations
import argparse
import os
import sys
from typing import List, Tuple

from PIL import Image, UnidentifiedImageError

ALLOWED_EXT = {"png", "jpg", "jpeg"}


def is_allowed_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    return ext in ALLOWED_EXT


def collect_images(paths: List[str]) -> List[str]:
    images: List[str] = []
    for p in paths:
        if os.path.isdir(p):
            try:
                for entry in sorted(os.listdir(p)):  # Ordenar alfabéticamente
                    fp = os.path.join(p, entry)
                    if os.path.isfile(fp) and is_allowed_file(fp):
                        images.append(fp)
            except Exception as e:
                print(f"Error leyendo carpeta '{p}': {e}", file=sys.stderr)
        elif os.path.isfile(p):
            if is_allowed_file(p):
                images.append(p)
            else:
                print(f"Omitido (extensión no permitida): {p}", file=sys.stderr)
        else:
            print(f"Omitido (no existe): {p}", file=sys.stderr)
    return images


def convert_image_to_pdf(img_path: str, out_dir: str | None = None) -> Tuple[bool, str | None]:
    try:
        with Image.open(img_path) as im:
            rgb = im.convert('RGB')
            base = os.path.splitext(os.path.basename(img_path))[0]
            pdf_name = f"{base}.pdf"
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, pdf_name)
            else:
                out_path = os.path.join(os.path.dirname(img_path), pdf_name)
            rgb.save(out_path, "PDF", resolution=100.0)
            print(f"Convertido: '{img_path}' → '{out_path}'")
            return True, out_path
    except UnidentifiedImageError:
        print(f"Error: '{img_path}' no es una imagen válida o está corrupta.", file=sys.stderr)
    except Exception as e:
        print(f"Error procesando '{img_path}': {e}", file=sys.stderr)
    return False, None


def merge_images_to_pdf(image_paths: List[str], out_dir: str | None = None, 
                         pdf_name: str = "combined") -> Tuple[bool, str | None]:
    """Combina múltiples imágenes en un solo PDF."""
    if not image_paths:
        print("Error: No hay imágenes para combinar.", file=sys.stderr)
        return False, None
    
    try:
        # Cargar todas las imágenes y convertirlas a RGB
        images_rgb: List[Image.Image] = []
        for img_path in image_paths:
            try:
                im = Image.open(img_path)
                images_rgb.append(im.convert('RGB'))
                print(f"Añadido al PDF: '{img_path}'")
            except UnidentifiedImageError:
                print(f"Error: '{img_path}' no es una imagen válida o está corrupta.", file=sys.stderr)
            except Exception as e:
                print(f"Error cargando '{img_path}': {e}", file=sys.stderr)
        
        if not images_rgb:
            print("Error: No se pudieron cargar imágenes válidas para combinar.", file=sys.stderr)
            return False, None
        
        # Definir ruta de salida
        if not pdf_name.endswith('.pdf'):
            pdf_name = f"{pdf_name}.pdf"
        
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, pdf_name)
        else:
            # Usar el directorio de la primera imagen
            out_path = os.path.join(os.path.dirname(image_paths[0]) or '.', pdf_name)
        
        # Guardar el PDF con la primera imagen y añadir el resto
        first_image = images_rgb[0]
        rest_images = images_rgb[1:] if len(images_rgb) > 1 else []
        
        first_image.save(
            out_path, 
            "PDF", 
            resolution=100.0,
            save_all=True,
            append_images=rest_images
        )
        
        # Cerrar todas las imágenes
        for im in images_rgb:
            im.close()
        
        print(f"\n✓ PDF combinado creado: '{out_path}'")
        print(f"  Total de páginas: {len(images_rgb)}")
        return True, out_path
        
    except Exception as e:
        print(f"Error creando PDF combinado: {e}", file=sys.stderr)
        return False, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="convert_images_to_pdf",
        description="Convierte imágenes PNG/JPG/JPEG a PDFs. Puede crear PDFs individuales o combinar múltiples imágenes en uno solo.",
        epilog="Ejemplos:\n"
               "  python convert_images_to_pdf.py imagen1.jpg imagen2.jpg\n"
               "  python convert_images_to_pdf.py *.jpg -m -n documento\n"
               "  python convert_images_to_pdf.py carpeta/ -m -o salida -n reporte",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'paths', nargs='+', help='Rutas a archivos de imagen o carpetas que contienen imágenes'
    )
    parser.add_argument('-o', '--out', help='Directorio de salida para los PDFs (opcional)')
    parser.add_argument('-d', '--delete-original', action='store_true', 
                       help='Borrar la imagen original después de convertirla (solo si la conversión fue exitosa)')
    parser.add_argument('-m', '--merge', action='store_true',
                       help='Combinar todas las imágenes en un único PDF')
    parser.add_argument('-n', '--name', default='combined',
                       help='Nombre del PDF combinado (solo con --merge). Por defecto: "combined"')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    images = collect_images(args.paths)
    if not images:
        print('No se encontraron imágenes válidas para procesar.', file=sys.stderr)
        sys.exit(1)

    total = len(images)
    
    # Modo combinación: todas las imágenes en un solo PDF
    if args.merge:
        print(f"Modo combinación: {total} imágenes serán unidas en un solo PDF.\n")
        ok, out_path = merge_images_to_pdf(images, args.out, args.name)
        if ok and args.delete_original:
            for img in images:
                try:
                    os.remove(img)
                    print(f"Eliminado original: '{img}'")
                except Exception as e:
                    print(f"Error al eliminar '{img}': {e}", file=sys.stderr)
        if not ok:
            sys.exit(1)
        return
    
    # Modo individual: un PDF por cada imagen
    success = 0
    fail = 0
    for img in images:
        ok, out_path = convert_image_to_pdf(img, args.out)
        if ok:
            success += 1
            if args.delete_original:
                try:
                    os.remove(img)
                    print(f"Eliminado original: '{img}'")
                except Exception as e:
                    print(f"Error al eliminar '{img}': {e}", file=sys.stderr)
        else:
            fail += 1

    print(f"\nResumen: {success} convertidos, {fail} fallidos, de {total} procesados.")


if __name__ == '__main__':
    main()
