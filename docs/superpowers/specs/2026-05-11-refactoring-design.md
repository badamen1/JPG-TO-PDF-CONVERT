# Spec: Refactorización del proyecto JPG TO PDF CONVERT

**Fecha:** 2026-05-11  
**Estado:** Aprobado

---

## Objetivo

Refactorizar el proyecto de scripts planos a un paquete Python organizado, aplicando:
- Principios de responsabilidad única (SRP) y no repetición (DRY)
- Logging estructurado y consistente en todos los módulos
- Manejo de excepciones con jerarquía personalizada donde el dominio lo justifica

---

## Estructura de archivos resultante

```
JPG TO PDF CONVERT/
├── contratos/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_converter.py
│   │   ├── pdf_corrector.py
│   │   ├── drive_client.py
│   │   └── duplicates.py
│   └── cli/
│       ├── __init__.py
│       ├── subir_contratos.py
│       ├── subir_semana.py
│       ├── pipeline.py
│       └── limpiar.py
├── gui.py
└── requirements.txt
```

Los scripts originales en la raíz quedan obsoletos tras la migración. Se eliminan al finalizar.

---

## Logging (`contratos/logger.py`)

### Diseño

Un único módulo centralizado que expone `get_logger(name: str) -> logging.Logger`. Cada módulo lo invoca con `get_logger(__name__)`.

### Formato de salida (solo consola, stdout)

```
2026-05-11 14:32:01 [INFO   ] contratos.core.drive_client: Autenticando con Google Drive...
2026-05-11 14:32:03 [WARNING] contratos.cli.subir_contratos: Sin carpeta destino para código 009812
2026-05-11 14:32:07 [ERROR  ] contratos.core.drive_client: Falló la subida de 'Contrato Nº 001253.pdf'
```

### Implementación

```python
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

### Regla de migración

Todo `print()` y `print(..., file=sys.stderr)` del proyecto se reemplaza por la llamada correspondiente al logger del módulo:
- Información normal → `logger.info(...)`
- Advertencias recuperables → `logger.warning(...)`
- Errores → `logger.error(...)`

---

## Excepciones (`contratos/exceptions.py`)

### Jerarquía

```python
class ContratosError(Exception):
    """Base para todos los errores del proyecto."""

class DriveAuthError(ContratosError):
    """Falla al autenticar con Google Drive."""

class DriveUploadError(ContratosError):
    """Falla al subir un archivo a Google Drive."""

class PdfProcessingError(ContratosError):
    """Falla al procesar o corregir un PDF con PyMuPDF."""
```

### Mapa de uso

| Excepción | Módulo que la lanza | Situación |
|---|---|---|
| `DriveAuthError` | `core/drive_client.py` | credentials no encontrado, token inválido, refresh fallido |
| `DriveUploadError` | `core/drive_client.py` | falla en `upload_file()` |
| `PdfProcessingError` | `core/pdf_corrector.py` | falla al abrir o guardar PDF con PyMuPDF |
| `FileNotFoundError` | `core/pdf_corrector.py`, CLIs | carpeta o archivo local no existe |
| `ValueError` | CLIs | argumentos inválidos de entrada |

### Patrón en CLIs

```python
def main() -> None:
    args = parse_args()
    try:
        run(args)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except ContratosError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario.")
        sys.exit(0)
```

---

## Módulos `core/`

### `core/drive_client.py`

Origen: `drive_uploader.py`

**Funciones:**

| Firma | Cambios respecto al original |
|---|---|
| `authenticate(credentials_path, token_path) -> GoogleDrive` | Lanza `DriveAuthError` en vez de `sys.exit(1)` |
| `get_folder_map(drive, parent_id) -> dict[str, str]` | **Nueva.** Extrae mapa `código_6_dígitos → folder_id`. Elimina la duplicación entre `subir_contratos_drive.py` y `pipeline_contratos.py` |
| `find_folder(drive, name, parent_id) -> str | None` | Sin cambios de lógica |
| `create_folder(drive, name, parent_id) -> str` | Sin cambios de lógica |
| `upload_file(drive, file_path, parent_id) -> str` | Lanza `DriveUploadError` en falla en vez de propagar excepción genérica |
| `upload_client_to_drive(drive, client_name, pdfs, parent_folder_id) -> str` | **Movida desde `subir_semana.py`.** Crea carpeta del cliente en Drive y sube sus PDFs. Retorna `'ok'`, `'omitido'` o `'error'` |

---

### `core/pdf_converter.py`

Origen: `convert_images_to_pdf.py` + helpers de `subir_semana.py`

**Funciones:**

| Firma | Origen |
|---|---|
| `collect_images(paths) -> list[str]` | `convert_images_to_pdf.py` |
| `convert_image_to_pdf(img_path, out_dir) -> tuple[bool, str | None]` | `convert_images_to_pdf.py` |
| `merge_images_to_pdf(image_paths, out_dir, pdf_name) -> tuple[bool, str | None]` | `convert_images_to_pdf.py` |
| `is_cedula(filename) -> bool` | `subir_semana.py` |
| `separate_images(folder) -> tuple[list[str], list[str]]` | `subir_semana.py` |
| `process_client(client_folder) -> list[str]` | `subir_semana.py` — genera PDFs de un cliente y retorna sus rutas |

Sin cambios de lógica. Reemplaza `print()` por `logger`.

---

### `core/pdf_corrector.py`

Origen: `corregir_contratos_pdf.py`

**Función principal:**

```python
def corregir_contratos(input_folder: str, delete_old: bool = False) -> tuple[int, int]:
    """Retorna (procesados, modificados)."""
```

**Cambios:**
- Elimina los parámetros `text_to_find` y `text_to_replace` de la firma — el original los recibía pero los ignoraba completamente (los patrones de corrección estaban hardcodeados internamente).
- Lanza `FileNotFoundError` si `input_folder` no existe (en vez de imprimir y retornar silenciosamente).
- Lanza `PdfProcessingError` si PyMuPDF no puede abrir un archivo (en vez de imprimir y continuar con `traceback.print_exc()`).
- Reemplaza `print()` por `logger`.

---

### `core/duplicates.py`

Origen: `limpiar_duplicados_drive.py` (lógica de negocio)

**Funciones:** `buscar_duplicados_recursivo()`, `formatear_fecha()`, `formatear_tamanio()`

**Cambios:**
- Reemplaza `except:` sin tipo por `except Exception as e:` con log del error.
- Reemplaza `print()` por `logger`.

---

## Módulos `cli/`

Cada CLI es una capa delgada: parsea args, llama al `core/` y maneja excepciones en `main()`.

| CLI | Origen | Comando de ejecución |
|---|---|---|
| `cli/subir_contratos.py` | `subir_contratos_drive.py` | `python -m contratos.cli.subir_contratos <carpeta> <drive_id>` |
| `cli/subir_semana.py` | `subir_semana.py` | `python -m contratos.cli.subir_semana --ruta_local <ruta> --drive_folder_id <id>` |
| `cli/pipeline.py` | `pipeline_contratos.py` | `python -m contratos.cli.pipeline <carpeta> <drive_id> [--pasos 1 2 3]` |
| `cli/limpiar.py` | `limpiar_duplicados_drive.py` (CLI) | `python -m contratos.cli.limpiar <folder_id>` |

**Flujos por CLI:**

- **subir_contratos:** autentica → `get_folder_map()` → itera PDFs → `upload_file()` → resumen
- **subir_semana:** lista clientes → `process_client()` por cada uno → `upload_client_to_drive()` → resumen
- **pipeline:** paso 1 `corregir_contratos()` → paso 2 `get_folder_map()` + `upload_file()` → paso 3 `buscar_duplicados_recursivo()` + confirmación interactiva
- **limpiar:** autentica → `buscar_duplicados_recursivo()` → reporte → confirmación interactiva → mueve a papelera

---

## Problemas que resuelve esta refactorización

| Problema actual | Solución |
|---|---|
| Logging inconsistente (mix de `print`, `sys.stderr`, `logging`) | `get_logger(__name__)` en todos los módulos |
| `sys.exit(1)` dentro de `drive_uploader.authenticate()` | Lanza `DriveAuthError`, el CLI decide si hace `sys.exit` |
| Lógica de `mapa_carpetas` duplicada en dos scripts | Consolidada en `get_folder_map()` en `drive_client.py` |
| `bare except:` en `limpiar_duplicados_drive.py` | Reemplazado por `except Exception as e:` con log |
| Parámetros `text_to_find`/`text_to_replace` en `corregir_contratos()` que no se usan | Eliminados de la firma |
| Scripts mezclados sin jerarquía en la raíz | Separados en `core/` (lógica) y `cli/` (entrada) |
