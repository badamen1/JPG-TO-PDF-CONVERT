# Convertir imágenes a PDF (CLI)

Script de línea de comandos para convertir imágenes PNG/JPG/JPEG a PDFs. Soporta conversión individual o combinar múltiples imágenes en un único PDF.

## Instalación

1. Crear y activar un entorno virtual (opcional pero recomendado):

```bash
python -m venv .venv
.venv\Scripts\activate    # en Windows PowerShell/Command Prompt
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Desde la terminal, pasar archivos y/o carpetas.

### Conversión Individual (un PDF por imagen)

```bash
# Convertir archivos individuales
python convert_images_to_pdf.py imagen1.png imagen2.jpg

# Convertir todas las imágenes dentro de una carpeta
python convert_images_to_pdf.py C:\ruta\a\carpeta

# Guardar los PDFs generados en un directorio de salida
python convert_images_to_pdf.py imagen1.png imagen2.jpg -o C:\ruta\salida

# Convertir y eliminar las imágenes originales (usar con precaución)
python convert_images_to_pdf.py imagen1.png imagen2.jpg -d
```

### Combinar Imágenes en un Solo PDF

Usa la opción `-m` o `--merge` para unir todas las imágenes en un único PDF multipágina:

```bash
# Combinar varias imágenes en un PDF llamado "combined.pdf"
python convert_images_to_pdf.py imagen1.jpg imagen2.jpg imagen3.jpg -m

# Combinar imágenes con un nombre personalizado
python convert_images_to_pdf.py imagen1.jpg imagen2.jpg -m -n mi_documento

# Combinar todas las imágenes de una carpeta en un PDF
python convert_images_to_pdf.py C:\ruta\a\carpeta -m -n reporte_completo

# Combinar y guardar en un directorio específico
python convert_images_to_pdf.py *.jpg -m -o C:\salida -n documento_final
```

## Opciones Disponibles

| Opción | Descripción |
|--------|-------------|
| `-o`, `--out` | Directorio de salida para los PDFs |
| `-d`, `--delete-original` | Eliminar imágenes originales después de la conversión exitosa |
| `-m`, `--merge` | Combinar todas las imágenes en un único PDF |
| `-n`, `--name` | Nombre del PDF combinado (solo con `--merge`, por defecto: "combined") |

## Comportamiento

- **Modo individual** (por defecto): Cada imagen se convierte a un PDF independiente con el mismo nombre base.
- **Modo combinación** (`--merge`): Todas las imágenes se unen en un único PDF multipágina, manteniendo el orden alfabético.
- Soporta extensiones: PNG, JPG, JPEG.
- Si una imagen falla, se muestra un mensaje de error y el proceso continúa con las demás.
- Con `-d/--delete-original`, las imágenes originales se eliminan solo si la conversión fue exitosa. 
