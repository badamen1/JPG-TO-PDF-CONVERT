# Refactoring: Paquete `contratos/` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar los scripts planos del proyecto a un paquete Python `contratos/` con separación `core/` + `cli/`, logging estructurado centralizado y jerarquía de excepciones personalizadas.

**Architecture:** El paquete `contratos/` contiene: `logger.py` (función `get_logger`), `exceptions.py` (jerarquía de excepciones), `core/` (lógica de negocio pura sin `sys.exit`) y `cli/` (entry points delgados que parsean args, llaman a `core/` y manejan excepciones). Los scripts originales en la raíz se eliminan al final.

**Tech Stack:** Python 3.13, Pillow, PyMuPDF (fitz), PyDrive2, pytest 8+

---

## Mapa de archivos

| Archivo nuevo | Origen | Acción |
|---|---|---|
| `contratos/__init__.py` | — | Crear (vacío) |
| `contratos/exceptions.py` | — | Crear |
| `contratos/logger.py` | — | Crear |
| `contratos/core/__init__.py` | — | Crear (vacío) |
| `contratos/core/drive_client.py` | `drive_uploader.py` | Crear (refactorizado) |
| `contratos/core/pdf_converter.py` | `convert_images_to_pdf.py` + helpers de `subir_semana.py` | Crear (refactorizado) |
| `contratos/core/pdf_corrector.py` | `corregir_contratos_pdf.py` | Crear (refactorizado) |
| `contratos/core/duplicates.py` | `limpiar_duplicados_drive.py` (lógica) | Crear (refactorizado) |
| `contratos/cli/__init__.py` | — | Crear (vacío) |
| `contratos/cli/subir_contratos.py` | `subir_contratos_drive.py` | Crear (refactorizado) |
| `contratos/cli/limpiar.py` | `limpiar_duplicados_drive.py` (CLI) | Crear (refactorizado) |
| `contratos/cli/subir_semana.py` | `subir_semana.py` | Crear (refactorizado) |
| `contratos/cli/pipeline.py` | `pipeline_contratos.py` | Crear (refactorizado) |
| `contratos/cli/explorar.py` | `explorar_drive.py` | Crear (refactorizado) |
| `gui.py` | `gui.py` | Modificar (actualizar imports) |
| `requirements-dev.txt` | — | Crear |
| Todos los `.py` originales en raíz | — | Eliminar (Task 10) |

---

## Task 1: Package skeleton, excepciones y logger

**Files:**
- Create: `contratos/__init__.py`
- Create: `contratos/core/__init__.py`
- Create: `contratos/cli/__init__.py`
- Create: `contratos/exceptions.py`
- Create: `contratos/logger.py`
- Create: `tests/__init__.py`
- Create: `tests/core/__init__.py`
- Create: `tests/cli/__init__.py`
- Create: `tests/test_exceptions.py`
- Create: `tests/test_logger.py`
- Create: `requirements-dev.txt`

- [ ] **Step 1: Crear directorios y archivos `__init__.py` vacíos**

```
contratos/
contratos/core/
contratos/cli/
tests/
tests/core/
tests/cli/
```

Crear cada `__init__.py` con contenido vacío (solo un salto de línea). En Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force contratos, contratos\core, contratos\cli, tests, tests\core, tests\cli
"" | Out-File -Encoding utf8 contratos\__init__.py
"" | Out-File -Encoding utf8 contratos\core\__init__.py
"" | Out-File -Encoding utf8 contratos\cli\__init__.py
"" | Out-File -Encoding utf8 tests\__init__.py
"" | Out-File -Encoding utf8 tests\core\__init__.py
"" | Out-File -Encoding utf8 tests\cli\__init__.py
```

- [ ] **Step 2: Crear `requirements-dev.txt`**

```
pytest>=8.0.0
```

Instalar: `pip install pytest`

- [ ] **Step 3: Escribir el test de excepciones**

Crear `tests/test_exceptions.py`:

```python
from contratos.exceptions import (
    ContratosError,
    DriveAuthError,
    DriveUploadError,
    PdfProcessingError,
)


def test_drive_auth_error_is_contratos_error():
    assert isinstance(DriveAuthError("test"), ContratosError)


def test_drive_upload_error_is_contratos_error():
    assert isinstance(DriveUploadError("test"), ContratosError)


def test_pdf_processing_error_is_contratos_error():
    assert isinstance(PdfProcessingError("test"), ContratosError)


def test_exceptions_preserve_message():
    assert str(DriveAuthError("no credentials")) == "no credentials"
    assert str(DriveUploadError("network fail")) == "network fail"
    assert str(PdfProcessingError("bad pdf")) == "bad pdf"
```

- [ ] **Step 4: Ejecutar test — debe fallar (módulo no existe aún)**

```
python -m pytest tests/test_exceptions.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'contratos'`

- [ ] **Step 5: Crear `contratos/exceptions.py`**

```python
class ContratosError(Exception):
    """Base para todos los errores del proyecto."""


class DriveAuthError(ContratosError):
    """Falla al autenticar con Google Drive."""


class DriveUploadError(ContratosError):
    """Falla al subir un archivo a Google Drive."""


class PdfProcessingError(ContratosError):
    """Falla al procesar o corregir un PDF."""
```

- [ ] **Step 6: Ejecutar test de excepciones — debe pasar**

```
python -m pytest tests/test_exceptions.py -v
```

Resultado esperado: `4 passed`

- [ ] **Step 7: Escribir el test del logger**

Crear `tests/test_logger.py`:

```python
import logging
from contratos.logger import get_logger


def test_get_logger_returns_logger_with_correct_name():
    logger = get_logger("contratos.test.nombre")
    assert logger.name == "contratos.test.nombre"
    assert isinstance(logger, logging.Logger)


def test_get_logger_has_stdout_handler():
    logger = get_logger("contratos.test.handler")
    assert len(logger.handlers) >= 1


def test_get_logger_no_duplicate_handlers():
    get_logger("contratos.test.idempotent")
    logger = get_logger("contratos.test.idempotent")
    assert len(logger.handlers) == 1


def test_get_logger_level_is_info():
    logger = get_logger("contratos.test.level")
    assert logger.level == logging.INFO
```

- [ ] **Step 8: Ejecutar test del logger — debe fallar**

```
python -m pytest tests/test_logger.py -v
```

Resultado esperado: `ImportError` (logger no existe aún)

- [ ] **Step 9: Crear `contratos/logger.py`**

```python
from __future__ import annotations

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

- [ ] **Step 10: Ejecutar todos los tests — deben pasar**

```
python -m pytest tests/ -v
```

Resultado esperado: `8 passed`

- [ ] **Step 11: Commit**

```bash
git add contratos/ tests/ requirements-dev.txt
git commit -m "feat(contratos): add package skeleton, exceptions and logger"
```

---

## Task 2: `core/drive_client.py`

**Files:**
- Create: `contratos/core/drive_client.py`
- Test: `tests/core/test_drive_client.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/core/test_drive_client.py`:

```python
from unittest.mock import MagicMock, patch
import pytest
from contratos.core.drive_client import (
    authenticate,
    get_folder_map,
    upload_file,
    upload_client_to_drive,
)
from contratos.exceptions import DriveAuthError, DriveUploadError


def test_authenticate_raises_when_credentials_missing():
    with pytest.raises(DriveAuthError, match="No se encontró"):
        authenticate(credentials_path="/ruta/que/no/existe.json")


def test_get_folder_map_extracts_6_digit_codes():
    drive = MagicMock()
    drive.ListFile.return_value.GetList.return_value = [
        {"title": "Cliente 001253", "id": "id_001"},
        {"title": "Cliente 009812", "id": "id_002"},
        {"title": "Sin código numérico", "id": "id_003"},
    ]
    result = get_folder_map(drive, "parent_id")
    assert result == {"001253": "id_001", "009812": "id_002"}


def test_get_folder_map_returns_empty_when_no_folders():
    drive = MagicMock()
    drive.ListFile.return_value.GetList.return_value = []
    result = get_folder_map(drive, "parent_id")
    assert result == {}


def test_upload_file_raises_drive_upload_error_on_failure(tmp_path):
    fake_file = tmp_path / "test.pdf"
    fake_file.write_bytes(b"pdf content")

    drive = MagicMock()
    gfile = MagicMock()
    gfile.Upload.side_effect = Exception("network error")
    drive.CreateFile.return_value = gfile

    with pytest.raises(DriveUploadError, match="test.pdf"):
        upload_file(drive, str(fake_file), "parent_id")


def test_upload_client_to_drive_returns_omitido_when_folder_exists():
    drive = MagicMock()
    drive.ListFile.return_value.GetList.return_value = [{"id": "existing_id"}]
    result = upload_client_to_drive(drive, "Cliente ABC", [], "parent_id")
    assert result == "omitido"


def test_upload_client_to_drive_returns_ok_and_creates_folder(tmp_path):
    fake_pdf = tmp_path / "contrato.pdf"
    fake_pdf.write_bytes(b"pdf")

    drive = MagicMock()
    drive.ListFile.return_value.GetList.return_value = []
    folder_mock = MagicMock()
    folder_mock.__getitem__ = MagicMock(return_value="new_folder_id")
    drive.CreateFile.return_value = folder_mock

    result = upload_client_to_drive(drive, "Cliente XYZ", [str(fake_pdf)], "parent_id")
    assert result == "ok"
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/core/test_drive_client.py -v
```

Resultado esperado: `ImportError` (módulo no existe aún)

- [ ] **Step 3: Crear `contratos/core/drive_client.py`**

```python
from __future__ import annotations

import os
import re

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from contratos.exceptions import DriveAuthError, DriveUploadError
from contratos.logger import get_logger

logger = get_logger(__name__)


def authenticate(
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
) -> GoogleDrive:
    if not os.path.exists(credentials_path):
        raise DriveAuthError(
            f"No se encontró '{credentials_path}'. "
            "Descárgalo desde Google Cloud Console → APIs y Servicios → Credenciales."
        )

    settings = {
        "client_config_backend": "file",
        "client_config_file": credentials_path,
        "save_credentials": True,
        "save_credentials_backend": "file",
        "save_credentials_file": token_path,
        "get_refresh_token": True,
    }

    gauth = GoogleAuth(settings=settings)

    if os.path.exists(token_path):
        gauth.LoadCredentialsFile(token_path)
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            try:
                gauth.Refresh()
            except Exception as e:
                if os.path.exists(token_path):
                    os.remove(token_path)
                gauth.credentials = None
                try:
                    gauth.LocalWebserverAuth()
                except Exception as e2:
                    raise DriveAuthError(
                        "No se pudo renovar ni re-autenticar con Google Drive."
                    ) from e2
        else:
            gauth.Authorize()
    else:
        gauth.LocalWebserverAuth()

    gauth.SaveCredentialsFile(token_path)
    return GoogleDrive(gauth)


def get_folder_map(drive: GoogleDrive, parent_id: str) -> dict[str, str]:
    """Retorna mapa {código_6_dígitos: folder_id} de subcarpetas de parent_id."""
    query = (
        f"'{parent_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    folder_list = drive.ListFile({"q": query, "maxResults": 1000}).GetList()

    mapa: dict[str, str] = {}
    for folder in folder_list:
        title = folder["title"].strip()
        match = re.search(r"(\d{6})", title)
        if match:
            mapa[match.group(1)] = folder["id"]

    logger.info("%d carpetas de clientes encontradas en Drive.", len(mapa))
    return mapa


def find_folder(drive: GoogleDrive, name: str, parent_id: str) -> str | None:
    safe_name = name.replace("'", "\\'")
    query = (
        f"title='{safe_name}' and "
        f"'{parent_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    result = drive.ListFile({"q": query}).GetList()
    return result[0]["id"] if result else None


def create_folder(drive: GoogleDrive, name: str, parent_id: str) -> str:
    folder_metadata = {
        "title": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [{"id": parent_id}],
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder["id"]


def upload_file(drive: GoogleDrive, file_path: str, parent_id: str) -> str:
    file_name = os.path.basename(file_path)
    file_metadata = {
        "title": file_name,
        "parents": [{"id": parent_id}],
    }
    gfile = drive.CreateFile(file_metadata)
    gfile.SetContentFile(file_path)
    try:
        gfile.Upload()
    except Exception as e:
        raise DriveUploadError(f"Falla al subir '{file_name}': {e}") from e
    return gfile["id"]


def upload_client_to_drive(
    drive: GoogleDrive,
    client_name: str,
    pdfs: list[str],
    parent_folder_id: str,
) -> str:
    """Crea carpeta del cliente en Drive y sube sus PDFs.

    Returns:
        'ok' si subió exitosamente, 'omitido' si ya existía, 'error' si falló.
    """
    try:
        existing_id = find_folder(drive, client_name, parent_folder_id)
        if existing_id:
            logger.info("Ya existe en Drive, se omite: %s", client_name)
            return "omitido"

        folder_id = create_folder(drive, client_name, parent_folder_id)
        logger.info("Carpeta creada en Drive: %s", client_name)

        for pdf_path in pdfs:
            upload_file(drive, pdf_path, folder_id)
            logger.info("Subido: %s", os.path.basename(pdf_path))

        return "ok"
    except Exception as e:
        logger.error("Error subiendo '%s': %s", client_name, e)
        return "error"
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/core/test_drive_client.py -v
```

Resultado esperado: `6 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `14 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/core/drive_client.py tests/core/test_drive_client.py
git commit -m "feat(core): add drive_client with DriveAuthError and DriveUploadError"
```

---

## Task 3: `core/pdf_converter.py`

**Files:**
- Create: `contratos/core/pdf_converter.py`
- Test: `tests/core/test_pdf_converter.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/core/test_pdf_converter.py`:

```python
import os
import pytest
from contratos.core.pdf_converter import (
    is_allowed_file,
    is_cedula,
    collect_images,
    separate_images,
)


def test_is_allowed_file_accepts_jpg():
    assert is_allowed_file("foto.jpg") is True


def test_is_allowed_file_accepts_jpeg_uppercase():
    assert is_allowed_file("foto.JPEG") is True


def test_is_allowed_file_accepts_png():
    assert is_allowed_file("imagen.PNG") is True


def test_is_allowed_file_rejects_pdf():
    assert is_allowed_file("doc.pdf") is False


def test_is_allowed_file_rejects_txt():
    assert is_allowed_file("file.txt") is False


def test_is_cedula_detects_cc1():
    assert is_cedula("CC1_foto.jpg") is True


def test_is_cedula_detects_cc2_lowercase():
    assert is_cedula("cc2_foto.jpg") is True


def test_is_cedula_rejects_non_cedula():
    assert is_cedula("contrato.jpg") is False


def test_collect_images_from_dir(tmp_path):
    (tmp_path / "foto.jpg").write_bytes(b"fake")
    (tmp_path / "imagen.PNG").write_bytes(b"fake")
    (tmp_path / "doc.pdf").write_bytes(b"fake")

    result = collect_images([str(tmp_path)])
    basenames = [os.path.basename(p) for p in result]
    assert "foto.jpg" in basenames
    assert "imagen.PNG" in basenames
    assert "doc.pdf" not in basenames


def test_collect_images_from_file(tmp_path):
    img = tmp_path / "foto.jpg"
    img.write_bytes(b"fake")
    result = collect_images([str(img)])
    assert len(result) == 1


def test_collect_images_skips_nonexistent():
    result = collect_images(["/ruta/que/no/existe.jpg"])
    assert result == []


def test_separate_images_splits_cedulas(tmp_path):
    (tmp_path / "CC1_foto.jpg").write_bytes(b"fake")
    (tmp_path / "CC2_foto.jpg").write_bytes(b"fake")
    (tmp_path / "contrato.jpg").write_bytes(b"fake")

    cedulas, others = separate_images(str(tmp_path))
    cedula_names = [os.path.basename(p) for p in cedulas]
    other_names = [os.path.basename(p) for p in others]

    assert "CC1_foto.jpg" in cedula_names
    assert "CC2_foto.jpg" in cedula_names
    assert "contrato.jpg" in other_names
    assert "contrato.jpg" not in cedula_names
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/core/test_pdf_converter.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/core/pdf_converter.py`**

```python
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
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/core/test_pdf_converter.py -v
```

Resultado esperado: `11 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `25 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/core/pdf_converter.py tests/core/test_pdf_converter.py
git commit -m "feat(core): add pdf_converter with image collection and merge functions"
```

---

## Task 4: `core/pdf_corrector.py`

**Files:**
- Create: `contratos/core/pdf_corrector.py`
- Test: `tests/core/test_pdf_corrector.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/core/test_pdf_corrector.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from contratos.core.pdf_corrector import corregir_contratos
from contratos.exceptions import PdfProcessingError


def test_raises_file_not_found_when_folder_missing():
    with pytest.raises(FileNotFoundError, match="no existe"):
        corregir_contratos("/ruta/que/no/existe/jamas")


def test_returns_zero_zero_when_no_pdfs(tmp_path):
    procesados, modificados = corregir_contratos(str(tmp_path))
    assert procesados == 0
    assert modificados == 0


def test_raises_pdf_processing_error_when_fitz_cannot_open(tmp_path):
    fake_pdf = tmp_path / "contrato.pdf"
    fake_pdf.write_bytes(b"not a real pdf")

    with patch("contratos.core.pdf_corrector.fitz.open", side_effect=Exception("fitz error")):
        with pytest.raises(PdfProcessingError, match="contrato.pdf"):
            corregir_contratos(str(tmp_path))


def test_processes_pdf_with_no_matching_patterns(tmp_path):
    fake_pdf = tmp_path / "contrato.pdf"
    fake_pdf.write_bytes(b"fake")

    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.search_for.return_value = []
    mock_doc.__len__ = MagicMock(return_value=1)
    mock_doc.__getitem__ = MagicMock(return_value=mock_page)
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

    with patch("contratos.core.pdf_corrector.fitz.open", return_value=mock_doc):
        procesados, modificados = corregir_contratos(str(tmp_path))

    assert procesados == 1
    assert modificados == 0
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/core/test_pdf_corrector.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/core/pdf_corrector.py`**

```python
from __future__ import annotations

import glob
import os
import time
from typing import Tuple

import fitz  # PyMuPDF

from contratos.exceptions import PdfProcessingError
from contratos.logger import get_logger

logger = get_logger(__name__)

PATRONES_ESPECIFICO = ["No. 4 de 2025", "No. 3 de 2025", "No. 2 de 2023"]
PATRONES_INTERADMINISTRATIVO = ["No. 1203 de 2023"]


def _aplicar_reemplazo(page, patron_original: str, texto_nuevo: str) -> bool:
    """Redacta patron_original y escribe texto_nuevo. Retorna True si modificó."""
    instances = page.search_for(patron_original)
    if not instances:
        return False

    for inst in instances:
        page.add_redact_annot(fitz.Rect(inst.x0 - 1, inst.y0 - 1, inst.x1 + 1, inst.y1 + 1))
    page.apply_redactions()

    for inst in instances:
        page.draw_rect(
            fitz.Rect(inst.x0 - 2, inst.y0 - 2, inst.x1 + 2, inst.y1 + 2),
            color=None,
            fill=(1, 1, 1),
        )
        page.insert_text(
            point=fitz.Point(inst.x0, inst.y1 - (inst.height * 0.2)),
            text=texto_nuevo,
            fontsize=inst.height * 0.85,
            fontname="times-roman",
            color=(0, 0, 0),
        )
    return True


def corregir_contratos(input_folder: str, delete_old: bool = False) -> Tuple[int, int]:
    """Corrige patrones de texto en los PDFs de input_folder.

    Returns:
        (procesados, modificados)

    Raises:
        FileNotFoundError: si input_folder no existe.
        PdfProcessingError: si PyMuPDF no puede abrir un archivo PDF.
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"La carpeta de origen '{input_folder}' no existe.")

    if not delete_old:
        output_folder = os.path.join(input_folder, "contratos_corregidos")
        os.makedirs(output_folder, exist_ok=True)

    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    if not pdf_files:
        logger.info("No se encontraron archivos PDF en '%s'.", input_folder)
        return 0, 0

    procesados = 0
    modificados = 0
    logger.info("Iniciando procesamiento de %d contratos...", len(pdf_files))

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise PdfProcessingError(f"No se pudo abrir '{filename}': {e}") from e

        try:
            is_modified = False

            for page_num in range(len(doc)):
                page = doc[page_num]

                for patron in PATRONES_ESPECIFICO:
                    if page.search_for(f"Acuerdo Específico {patron}"):
                        if _aplicar_reemplazo(page, patron, "No. 4 de 2024"):
                            is_modified = True
                        break

                for patron in PATRONES_INTERADMINISTRATIVO:
                    if page.search_for(f"Contrato Interadministrativo {patron}"):
                        if _aplicar_reemplazo(page, patron, "No. 1465 de 2024"):
                            is_modified = True
                        break

            if is_modified:
                if delete_old:
                    temp_path = pdf_path + ".tmp"
                    doc.save(temp_path, garbage=4, deflate=True)
                    doc.close()
                    time.sleep(0.5)
                    for intento in range(3):
                        try:
                            os.replace(temp_path, pdf_path)
                            logger.info("[REEMPLAZADO] %s", filename)
                            break
                        except PermissionError:
                            if intento < 2:
                                time.sleep(1)
                            else:
                                logger.error(
                                    "No se pudo reemplazar '%s' tras 3 intentos.", filename
                                )
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                else:
                    output_path = os.path.join(
                        input_folder, "contratos_corregidos", filename
                    )
                    doc.save(output_path, garbage=4, deflate=True)
                    doc.close()
                    logger.info("[MODIFICADO] %s", filename)

                modificados += 1
            else:
                doc.close()
                logger.info("[SIN CAMBIOS] %s", filename)

            procesados += 1

        except Exception as e:
            doc.close()
            logger.error("Falló el procesamiento de '%s': %s", filename, e)
            procesados += 1

    logger.info(
        "Proceso completado. Revisados: %d | Modificados: %d", procesados, modificados
    )
    return procesados, modificados
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/core/test_pdf_corrector.py -v
```

Resultado esperado: `4 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `29 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/core/pdf_corrector.py tests/core/test_pdf_corrector.py
git commit -m "feat(core): add pdf_corrector with PdfProcessingError on open failure"
```

---

## Task 5: `core/duplicates.py`

**Files:**
- Create: `contratos/core/duplicates.py`
- Test: `tests/core/test_duplicates.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/core/test_duplicates.py`:

```python
from unittest.mock import MagicMock
from contratos.core.duplicates import (
    buscar_duplicados_recursivo,
    formatear_fecha,
    formatear_tamanio,
)


def test_formatear_fecha_valid_iso():
    assert formatear_fecha("2024-03-15T10:30:00.000Z") == "2024-03-15 10:30:00"


def test_formatear_fecha_invalid_returns_original():
    assert formatear_fecha("not-a-date") == "not-a-date"


def test_formatear_tamanio_bytes():
    assert formatear_tamanio("500") == "500 B"


def test_formatear_tamanio_kb():
    assert formatear_tamanio("2048") == "2.00 KB"


def test_formatear_tamanio_mb():
    assert formatear_tamanio("2097152") == "2.00 MB"


def test_formatear_tamanio_none():
    assert formatear_tamanio(None) == "0 B"


def _make_drive_mock(items: list) -> MagicMock:
    drive = MagicMock()
    folder_meta = MagicMock()
    folder_meta.__getitem__ = MagicMock(return_value="Raíz")
    drive.CreateFile.return_value = folder_meta
    drive.ListFile.return_value.GetList.return_value = items
    return drive


def test_buscar_duplicados_finds_duplicates():
    drive = _make_drive_mock([
        {
            "id": "f1",
            "title": "Contrato Nº 001253.pdf",
            "mimeType": "application/pdf",
            "modifiedDate": "2024-03-15T10:00:00.000Z",
            "fileSize": "1024",
        },
        {
            "id": "f2",
            "title": "Contrato Nº 001253.pdf",
            "mimeType": "application/pdf",
            "modifiedDate": "2024-03-10T10:00:00.000Z",
            "fileSize": "1024",
        },
    ])
    result = buscar_duplicados_recursivo(drive, "root_id")
    assert len(result) == 1
    assert result[0]["conservar"]["id"] == "f1"
    assert result[0]["eliminar"][0]["id"] == "f2"


def test_buscar_duplicados_no_duplicates():
    drive = _make_drive_mock([
        {
            "id": "f1",
            "title": "Contrato Nº 001253.pdf",
            "mimeType": "application/pdf",
            "modifiedDate": "2024-03-15T10:00:00.000Z",
            "fileSize": "1024",
        },
    ])
    result = buscar_duplicados_recursivo(drive, "root_id")
    assert result == []


def test_buscar_duplicados_ignores_non_contrato_files():
    drive = _make_drive_mock([
        {
            "id": "f1",
            "title": "factura.pdf",
            "mimeType": "application/pdf",
            "modifiedDate": "2024-03-15T10:00:00.000Z",
            "fileSize": "1024",
        },
        {
            "id": "f2",
            "title": "factura.pdf",
            "mimeType": "application/pdf",
            "modifiedDate": "2024-03-10T10:00:00.000Z",
            "fileSize": "1024",
        },
    ])
    result = buscar_duplicados_recursivo(drive, "root_id")
    assert result == []
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/core/test_duplicates.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/core/duplicates.py`**

```python
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
        return iso_date


def formatear_tamanio(bytes_str: str | None) -> str:
    if not bytes_str:
        return "0 B"
    b = int(bytes_str)
    if b < 1024:
        return f"{b} B"
    if b < 1024 * 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b / (1024 * 1024):.2f} MB"
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/core/test_duplicates.py -v
```

Resultado esperado: `9 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `38 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/core/duplicates.py tests/core/test_duplicates.py
git commit -m "feat(core): add duplicates module with Drive duplicate detection"
```

---

## Task 6: `cli/subir_contratos.py`

**Files:**
- Create: `contratos/cli/subir_contratos.py`
- Test: `tests/cli/test_subir_contratos.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/cli/test_subir_contratos.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from contratos.cli.subir_contratos import run
from contratos.exceptions import ContratosError


def test_run_raises_file_not_found_when_folder_missing():
    with pytest.raises(FileNotFoundError):
        run("/no/existe", "drive_id")


def test_run_raises_contratos_error_when_no_drive_folders(tmp_path):
    with patch("contratos.cli.subir_contratos.authenticate"), \
         patch("contratos.cli.subir_contratos.get_folder_map", return_value={}):
        with pytest.raises(ContratosError, match="No se encontraron carpetas"):
            run(str(tmp_path), "drive_id")


def test_run_warns_and_returns_when_no_pdfs(tmp_path):
    with patch("contratos.cli.subir_contratos.authenticate"), \
         patch("contratos.cli.subir_contratos.get_folder_map", return_value={"001253": "id1"}):
        run(str(tmp_path), "drive_id")  # no debe lanzar excepción


def test_run_uploads_matching_pdf(tmp_path):
    fake_pdf = tmp_path / "Contrato Nº 001253.pdf"
    fake_pdf.write_bytes(b"pdf")

    mock_upload = MagicMock()
    with patch("contratos.cli.subir_contratos.authenticate"), \
         patch("contratos.cli.subir_contratos.get_folder_map", return_value={"001253": "folder1"}), \
         patch("contratos.cli.subir_contratos.upload_file", mock_upload):
        run(str(tmp_path), "drive_id")
        mock_upload.assert_called_once()


def test_run_skips_pdf_without_code(tmp_path):
    fake_pdf = tmp_path / "sin_codigo.pdf"
    fake_pdf.write_bytes(b"pdf")

    mock_upload = MagicMock()
    with patch("contratos.cli.subir_contratos.authenticate"), \
         patch("contratos.cli.subir_contratos.get_folder_map", return_value={"001253": "folder1"}), \
         patch("contratos.cli.subir_contratos.upload_file", mock_upload):
        run(str(tmp_path), "drive_id")
        mock_upload.assert_not_called()
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/cli/test_subir_contratos.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/cli/subir_contratos.py`**

```python
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

from contratos.core.drive_client import authenticate, get_folder_map, upload_file
from contratos.exceptions import ContratosError, DriveAuthError, DriveUploadError
from contratos.logger import get_logger

logger = get_logger(__name__)


def run(carpeta_local: str, drive_folder_id: str) -> None:
    if not os.path.exists(carpeta_local):
        raise FileNotFoundError(f"La carpeta local '{carpeta_local}' no existe.")

    logger.info("Autenticando con Google Drive...")
    drive = authenticate()
    logger.info("Autenticación exitosa.")

    mapa = get_folder_map(drive, drive_folder_id)
    if not mapa:
        raise ContratosError("No se encontraron carpetas en el ID de Drive proporcionado.")

    pdf_files = glob.glob(os.path.join(carpeta_local, "*.pdf"))
    if not pdf_files:
        logger.warning("No hay archivos PDF en '%s'.", carpeta_local)
        return

    logger.info("Iniciando subida de %d contratos...", len(pdf_files))
    subidos = 0
    no_encontrados = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        name_only = os.path.splitext(filename)[0]
        match = re.search(r"(\d{6})", name_only)

        if not match:
            logger.warning("Sin código de 6 dígitos: '%s'", filename)
            no_encontrados += 1
            continue

        codigo = match.group(1)
        if codigo in mapa:
            try:
                upload_file(drive, pdf_path, mapa[codigo])
                logger.info("[SUBIDO] '%s' -> carpeta %s", filename, codigo)
                subidos += 1
            except DriveUploadError as e:
                logger.error("[ERROR] Falló la subida de '%s': %s", filename, e)
        else:
            logger.warning("[SIN CARPETA] '%s': No hay carpeta para código %s", filename, codigo)
            no_encontrados += 1

    logger.info(
        "RESUMEN | Total: %d | Subidos: %d | Sin carpeta: %d",
        len(pdf_files), subidos, no_encontrados,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube contratos corregidos a sus respectivas subcarpetas en Google Drive."
    )
    parser.add_argument("carpeta_local", help="Ruta local donde están los PDFs")
    parser.add_argument("drive_folder_id", help="ID de la carpeta principal en Google Drive")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.carpeta_local, args.drive_folder_id)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except (ContratosError, FileNotFoundError) as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/cli/test_subir_contratos.py -v
```

Resultado esperado: `5 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `43 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/cli/subir_contratos.py tests/cli/test_subir_contratos.py
git commit -m "feat(cli): add subir_contratos CLI entry point"
```

---

## Task 7: `cli/limpiar.py`

**Files:**
- Create: `contratos/cli/limpiar.py`
- Test: `tests/cli/test_limpiar.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/cli/test_limpiar.py`:

```python
from unittest.mock import patch, MagicMock
from contratos.cli.limpiar import run


def test_run_logs_when_no_duplicates():
    with patch("contratos.cli.limpiar.authenticate"), \
         patch("contratos.cli.limpiar.buscar_duplicados_recursivo", return_value=[]):
        run("folder_id")  # no debe lanzar excepción


def test_run_cancels_when_user_says_no():
    duplicado = {
        "ruta": "Raíz/Cliente",
        "nombre": "Contrato Nº 001253.pdf",
        "conservar": {
            "id": "f1",
            "modifiedDate": "2024-03-15T10:00:00.000Z",
            "fileSize": "1024",
        },
        "eliminar": [{
            "id": "f2",
            "modifiedDate": "2024-03-10T10:00:00.000Z",
            "fileSize": "1024",
        }],
    }
    mock_drive = MagicMock()
    with patch("contratos.cli.limpiar.authenticate", return_value=mock_drive), \
         patch("contratos.cli.limpiar.buscar_duplicados_recursivo", return_value=[duplicado]), \
         patch("builtins.input", return_value="n"):
        run("folder_id")
        mock_drive.CreateFile.assert_not_called()
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/cli/test_limpiar.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/cli/limpiar.py`**

```python
from __future__ import annotations

import argparse
import sys

from contratos.core.drive_client import authenticate
from contratos.core.duplicates import (
    buscar_duplicados_recursivo,
    formatear_fecha,
    formatear_tamanio,
)
from contratos.exceptions import ContratosError, DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)


def run(folder_id: str) -> None:
    logger.info("Autenticando con Google Drive...")
    drive = authenticate()

    logger.info("Iniciando búsqueda de duplicados...")
    duplicados = buscar_duplicados_recursivo(drive, folder_id)

    if not duplicados:
        logger.info("No se encontraron contratos duplicados.")
        return

    logger.warning("Se encontraron %d grupos de duplicados:", len(duplicados))

    for item in duplicados:
        print(f"\nCarpeta: {item['ruta']}")
        print(f"  Archivo: {item['nombre']}")
        cons = item["conservar"]
        print(f"  CONSERVAR: [ID: {cons['id']}]")
        print(f"    Fecha: {formatear_fecha(cons['modifiedDate'])} | "
              f"Tamaño: {formatear_tamanio(cons.get('fileSize'))}")
        for elim in item["eliminar"]:
            print(f"  ELIMINAR: [ID: {elim['id']}]")
            print(f"    Fecha: {formatear_fecha(elim['modifiedDate'])} | "
                  f"Tamaño: {formatear_tamanio(elim.get('fileSize'))}")
        print("-" * 50)

    total_a_eliminar = sum(len(item["eliminar"]) for item in duplicados)
    print(f"\nResumen: Se conservarán {len(duplicados)} y se moverán {total_a_eliminar} a papelera.")

    confirmar = input("\n¿Deseas proceder con la limpieza? (s/n): ").lower().strip()
    if confirmar != "s":
        logger.info("Operación cancelada por el usuario.")
        return

    logger.info("Moviendo archivos a la papelera...")
    exitos = 0
    errores = 0
    for item in duplicados:
        for elim in item["eliminar"]:
            try:
                archivo = drive.CreateFile({"id": elim["id"]})
                archivo.Trash()
                exitos += 1
                logger.info("Movido a papelera: %s (%s)", item["nombre"], elim["id"])
            except Exception as e:
                errores += 1
                logger.error("Error con %s: %s", elim["id"], e)

    logger.info("Proceso finalizado. Exitos: %d | Errores: %d", exitos, errores)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Limpia contratos duplicados en Drive.")
    parser.add_argument("folder_id", help="ID de la carpeta raíz en Google Drive.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.folder_id)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except ContratosError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/cli/test_limpiar.py -v
```

Resultado esperado: `2 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `45 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/cli/limpiar.py tests/cli/test_limpiar.py
git commit -m "feat(cli): add limpiar CLI entry point"
```

---

## Task 8: `cli/subir_semana.py`

**Files:**
- Create: `contratos/cli/subir_semana.py`
- Test: `tests/cli/test_subir_semana.py`

- [ ] **Step 1: Escribir los tests**

Crear `tests/cli/test_subir_semana.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from contratos.cli.subir_semana import run
from contratos.exceptions import ContratosError


def test_run_raises_file_not_found_when_folder_missing():
    with pytest.raises(FileNotFoundError):
        run("/no/existe", "drive_id")


def test_run_raises_contratos_error_when_no_client_folders(tmp_path):
    with pytest.raises(ContratosError, match="No se encontraron"):
        run(str(tmp_path), "drive_id")


def test_run_ignores_underscore_folders(tmp_path):
    (tmp_path / "_pdfs").mkdir()
    with pytest.raises(ContratosError, match="No se encontraron"):
        run(str(tmp_path), "drive_id")


def test_run_processes_client_folders(tmp_path):
    (tmp_path / "JUAN PEREZ").mkdir()

    with patch("contratos.cli.subir_semana.authenticate"), \
         patch("contratos.cli.subir_semana.process_client", return_value=[]), \
         patch("contratos.cli.subir_semana.upload_client_to_drive", return_value="ok"):
        run(str(tmp_path), "drive_id")
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/cli/test_subir_semana.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/cli/subir_semana.py`**

```python
from __future__ import annotations

import argparse
import os
import sys
import time

from contratos.core.drive_client import authenticate, upload_client_to_drive
from contratos.core.pdf_converter import process_client
from contratos.exceptions import ContratosError, DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)

SKIPPED = "omitido"


def run(
    ruta_local: str,
    drive_folder_id: str,
    credentials: str = "credentials.json",
) -> None:
    ruta_local = os.path.abspath(ruta_local)
    if not os.path.isdir(ruta_local):
        raise FileNotFoundError(f"La ruta no existe o no es una carpeta: {ruta_local}")

    client_folders = sorted([
        os.path.join(ruta_local, d)
        for d in os.listdir(ruta_local)
        if os.path.isdir(os.path.join(ruta_local, d)) and not d.startswith("_")
    ])

    if not client_folders:
        raise ContratosError("No se encontraron carpetas de clientes.")

    semana_name = os.path.basename(ruta_local)
    logger.info(
        "Semana: %s | Clientes: %d | Drive: %s",
        semana_name, len(client_folders), drive_folder_id,
    )

    credentials_file = os.path.abspath(credentials)
    token_file = os.path.join(os.path.dirname(credentials_file), "token.json")

    logger.info("Autenticando con Google Drive...")
    drive = authenticate(credentials_file, token_file)
    logger.info("Autenticación exitosa.")

    start_time = time.time()
    results = []

    for i, client_folder in enumerate(client_folders, 1):
        client_name = os.path.basename(client_folder)
        logger.info("[%d/%d] Procesando: %s", i, len(client_folders), client_name)

        pdfs = process_client(client_folder)
        if not pdfs:
            logger.warning("Sin archivos para procesar: %s", client_name)
            results.append((client_name, 0, "sin_archivos"))
            continue

        status = upload_client_to_drive(drive, client_name, pdfs, drive_folder_id)
        results.append((client_name, len(pdfs), status))

    elapsed = time.time() - start_time
    n_ok = sum(1 for _, _, s in results if s == "ok")
    n_skip = sum(1 for _, _, s in results if s == SKIPPED)
    n_fail = sum(1 for _, _, s in results if s == "error")
    n_empty = sum(1 for _, _, s in results if s == "sin_archivos")
    total_pdfs = sum(n for _, n, _ in results)

    logger.info(
        "RESUMEN | Tiempo: %.1fs | Clientes: %d | Subidos: %d | "
        "Omitidos: %d | Sin archivos: %d | Fallidos: %d | Archivos totales: %d",
        elapsed, len(results), n_ok, n_skip, n_empty, n_fail, total_pdfs,
    )

    if n_fail:
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="subir_semana",
        description="Sube una semana completa de clientes a Google Drive.",
    )
    parser.add_argument("--ruta_local", required=True, help="Ruta a la carpeta de la semana")
    parser.add_argument("--drive_folder_id", required=True, help="ID de la carpeta destino en Google Drive")
    parser.add_argument("--credentials", default="credentials.json", help="Ruta al archivo credentials.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.ruta_local, args.drive_folder_id, args.credentials)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except (ContratosError, FileNotFoundError) as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Ejecutar tests — deben pasar**

```
python -m pytest tests/cli/test_subir_semana.py -v
```

Resultado esperado: `4 passed`

- [ ] **Step 5: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `49 passed`

- [ ] **Step 6: Commit**

```bash
git add contratos/cli/subir_semana.py tests/cli/test_subir_semana.py
git commit -m "feat(cli): add subir_semana CLI entry point"
```

---

## Task 9: `cli/pipeline.py` y `cli/explorar.py`

**Files:**
- Create: `contratos/cli/pipeline.py`
- Create: `contratos/cli/explorar.py`
- Test: `tests/cli/test_pipeline.py`

- [ ] **Step 1: Escribir los tests del pipeline**

Crear `tests/cli/test_pipeline.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from contratos.cli.pipeline import run, paso_1_corregir


def test_paso_1_returns_none_when_no_pdfs_corrected(tmp_path):
    with patch("contratos.cli.pipeline.corregir_contratos", return_value=(0, 0)):
        result = paso_1_corregir(str(tmp_path))
        assert result is None


def test_paso_1_returns_path_when_pdfs_corrected(tmp_path):
    corregidos_dir = tmp_path / "contratos_corregidos"
    corregidos_dir.mkdir()
    (corregidos_dir / "contrato.pdf").write_bytes(b"pdf")

    with patch("contratos.cli.pipeline.corregir_contratos", return_value=(1, 1)):
        result = paso_1_corregir(str(tmp_path))
        assert result == str(corregidos_dir)


def test_run_only_step_1_does_not_call_authenticate(tmp_path):
    mock_auth = MagicMock()
    with patch("contratos.cli.pipeline.authenticate", mock_auth), \
         patch("contratos.cli.pipeline.corregir_contratos", return_value=(0, 0)):
        run(str(tmp_path), "drive_id", pasos=[1])
        mock_auth.assert_not_called()


def test_run_skips_step_2_if_step_1_returns_none(tmp_path):
    mock_paso2 = MagicMock()
    with patch("contratos.cli.pipeline.authenticate"), \
         patch("contratos.cli.pipeline.corregir_contratos", return_value=(0, 0)), \
         patch("contratos.cli.pipeline.paso_2_subir", mock_paso2):
        run(str(tmp_path), "drive_id", pasos=[1, 2])
        mock_paso2.assert_not_called()
```

- [ ] **Step 2: Ejecutar tests — deben fallar**

```
python -m pytest tests/cli/test_pipeline.py -v
```

Resultado esperado: `ImportError`

- [ ] **Step 3: Crear `contratos/cli/pipeline.py`**

```python
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

from contratos.core.drive_client import authenticate, get_folder_map, upload_file
from contratos.core.duplicates import (
    buscar_duplicados_recursivo,
    formatear_fecha,
    formatear_tamanio,
)
from contratos.core.pdf_corrector import corregir_contratos
from contratos.exceptions import ContratosError, DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)


def paso_1_corregir(carpeta_local: str) -> str | None:
    logger.info("PASO 1: CORRECCIÓN DE CONTRATOS")
    try:
        procesados, modificados = corregir_contratos(carpeta_local, delete_old=False)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return None

    carpeta_corregidos = os.path.join(carpeta_local, "contratos_corregidos")
    if not os.path.exists(carpeta_corregidos):
        logger.warning("No se creó 'contratos_corregidos'. Sin archivos que corregir.")
        return None

    pdf_corregidos = glob.glob(os.path.join(carpeta_corregidos, "*.pdf"))
    if not pdf_corregidos:
        logger.warning("La carpeta 'contratos_corregidos' está vacía.")
        return None

    logger.info("Paso 1 completado. %d contratos corregidos.", len(pdf_corregidos))
    return carpeta_corregidos


def paso_2_subir(drive, carpeta_corregidos: str, drive_folder_id: str) -> None:
    logger.info("PASO 2: SUBIDA A GOOGLE DRIVE")
    mapa = get_folder_map(drive, drive_folder_id)
    if not mapa:
        logger.error("No se encontraron carpetas en el ID de Drive proporcionado.")
        return

    pdf_files = glob.glob(os.path.join(carpeta_corregidos, "*.pdf"))
    subidos = 0
    no_encontrados = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        name_only = os.path.splitext(filename)[0]
        match = re.search(r"(\d{6})", name_only)

        if not match:
            logger.warning("[OMITIDO] Sin código de 6 dígitos: '%s'", filename)
            no_encontrados += 1
            continue

        codigo = match.group(1)
        if codigo in mapa:
            try:
                upload_file(drive, pdf_path, mapa[codigo])
                logger.info("[SUBIDO] '%s' -> carpeta %s", filename, codigo)
                subidos += 1
            except Exception as e:
                logger.error("[ERROR] Falló la subida de '%s': %s", filename, e)
        else:
            logger.warning("[SIN CARPETA] '%s': No hay carpeta para código %s", filename, codigo)
            no_encontrados += 1

    logger.info("Paso 2 completado. Subidos: %d | Sin destino: %d", subidos, no_encontrados)


def paso_3_limpiar(drive, drive_folder_id: str) -> None:
    logger.info("PASO 3: LIMPIEZA DE DUPLICADOS")
    duplicados = buscar_duplicados_recursivo(drive, drive_folder_id)

    if not duplicados:
        logger.info("No se encontraron contratos duplicados.")
        return

    logger.warning("Se encontraron %d grupos de duplicados.", len(duplicados))

    for item in duplicados:
        print(f"\nCarpeta: {item['ruta']}")
        print(f"  Archivo: {item['nombre']}")
        cons = item["conservar"]
        print(f"  CONSERVAR: [ID: {cons['id']}]")
        print(f"    Fecha: {formatear_fecha(cons['modifiedDate'])} | "
              f"Tamaño: {formatear_tamanio(cons.get('fileSize'))}")
        for elim in item["eliminar"]:
            print(f"  ELIMINAR: [ID: {elim['id']}]")
            print(f"    Fecha: {formatear_fecha(elim['modifiedDate'])} | "
                  f"Tamaño: {formatear_tamanio(elim.get('fileSize'))}")
        print("-" * 50)

    total_a_eliminar = sum(len(item["eliminar"]) for item in duplicados)
    print(f"\nResumen: Se conservarán {len(duplicados)} y se moverán {total_a_eliminar} a papelera.")

    confirmar = input("\n¿Deseas proceder con la limpieza? (s/n): ").lower().strip()
    if confirmar != "s":
        logger.info("Limpieza omitida por el usuario.")
        return

    exitos = 0
    errores = 0
    for item in duplicados:
        for elim in item["eliminar"]:
            try:
                archivo = drive.CreateFile({"id": elim["id"]})
                archivo.Trash()
                exitos += 1
                logger.info("Movido a papelera: %s (%s)", item["nombre"], elim["id"])
            except Exception as e:
                errores += 1
                logger.error("Error con %s: %s", elim["id"], e)

    logger.info("Paso 3 completado. Exitos: %d | Errores: %d", exitos, errores)


def run(carpeta_local: str, drive_folder_id: str, pasos: list[int]) -> None:
    logger.info("PIPELINE DE CONTRATOS | Pasos: %s", pasos)

    carpeta_corregidos = os.path.join(carpeta_local, "contratos_corregidos")

    if 1 in pasos:
        resultado = paso_1_corregir(carpeta_local)
        if resultado is None and 2 in pasos:
            logger.warning("El paso 1 no generó archivos. Deteniendo paso 2.")
            pasos = [p for p in pasos if p != 2]
        elif resultado:
            carpeta_corregidos = resultado

    drive = None
    if 2 in pasos or 3 in pasos:
        logger.info("Autenticando con Google Drive...")
        drive = authenticate()
        logger.info("Autenticación exitosa.")

    if 2 in pasos:
        if not os.path.exists(carpeta_corregidos):
            logger.error("La carpeta '%s' no existe. Omitiendo paso 2.", carpeta_corregidos)
        else:
            paso_2_subir(drive, carpeta_corregidos, drive_folder_id)

    if 3 in pasos:
        paso_3_limpiar(drive, drive_folder_id)

    logger.info("PIPELINE FINALIZADO")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline: Corregir contratos -> Subir a Drive -> Limpiar duplicados."
    )
    parser.add_argument("carpeta_local", help="Ruta local de la carpeta con los PDFs originales.")
    parser.add_argument("drive_folder_id", help="ID de la carpeta principal en Google Drive.")
    parser.add_argument(
        "--pasos", nargs="+", type=int, choices=[1, 2, 3],
        help="Pasos a ejecutar (ej. --pasos 2 3). Por defecto: todos.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pasos = args.pasos if args.pasos else [1, 2, 3]
    try:
        run(args.carpeta_local, args.drive_folder_id, pasos)
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except ContratosError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Pipeline interrumpido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Crear `contratos/cli/explorar.py`**

```python
from __future__ import annotations

import argparse
import sys

from contratos.core.drive_client import authenticate
from contratos.exceptions import DriveAuthError
from contratos.logger import get_logger

logger = get_logger(__name__)


def obtener_nombre_carpeta(drive, folder_id: str) -> str:
    try:
        carpeta = drive.CreateFile({"id": folder_id})
        carpeta.FetchMetadata(fields="title")
        return carpeta["title"]
    except Exception:
        return folder_id


def listar_contenido(
    drive, folder_id: str, nombre: str, prefijo: str = "", es_ultimo: bool = True
) -> None:
    query_carpetas = (
        f"'{folder_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    query_archivos = (
        f"'{folder_id}' in parents and "
        "mimeType != 'application/vnd.google-apps.folder' and trashed=false"
    )

    try:
        subcarpetas = drive.ListFile({"q": query_carpetas, "maxResults": 1000}).GetList()
        archivos_list = drive.ListFile(
            {"q": query_archivos, "maxResults": 1000, "fields": "items(id)"}
        ).GetList()
        num_archivos = len(archivos_list)
    except Exception as e:
        conector = "└── " if es_ultimo else "├── "
        print(f"{prefijo}{conector}[CARPETA] {nombre} — Error: {e}")
        return

    info_archivos = f" ({num_archivos} archivos)" if num_archivos > 0 else " (vacía)"
    conector = "└── " if es_ultimo else "├── "
    print(f"{prefijo}{conector}[CARPETA] {nombre}{info_archivos}")

    prefijo_hijo = prefijo + ("    " if es_ultimo else "|   ")
    subcarpetas = sorted(subcarpetas, key=lambda f: f["title"].lower())

    for i, carpeta in enumerate(subcarpetas):
        listar_contenido(
            drive,
            folder_id=carpeta["id"],
            nombre=carpeta["title"],
            prefijo=prefijo_hijo,
            es_ultimo=(i == len(subcarpetas) - 1),
        )


def run(folder_id: str) -> None:
    logger.info("Autenticando con Google Drive...")
    drive = authenticate()
    logger.info("Autenticación exitosa.")

    nombre_raiz = obtener_nombre_carpeta(drive, folder_id)
    print(f"\n[CARPETA] {nombre_raiz} (raíz)")
    print(f"ID: {folder_id}\n")

    query_carpetas = (
        f"'{folder_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    query_archivos = (
        f"'{folder_id}' in parents and "
        "mimeType != 'application/vnd.google-apps.folder' and trashed=false"
    )

    try:
        carpetas_raiz = drive.ListFile({"q": query_carpetas, "maxResults": 1000}).GetList()
        archivos_raiz = drive.ListFile({"q": query_archivos, "maxResults": 1000}).GetList()
    except Exception as e:
        logger.error("Error al leer la carpeta raíz: %s", e)
        sys.exit(1)

    carpetas_raiz = sorted(carpetas_raiz, key=lambda f: f["title"].lower())
    archivos_raiz = sorted(archivos_raiz, key=lambda f: f["title"].lower())

    if not carpetas_raiz and not archivos_raiz:
        print("    (vacía)")
        return

    for i, carpeta in enumerate(carpetas_raiz):
        es_ultimo = (i == len(carpetas_raiz) - 1) and (len(archivos_raiz) == 0)
        listar_contenido(drive, carpeta["id"], carpeta["title"], "", es_ultimo)

    for i, archivo in enumerate(archivos_raiz):
        conector = "└── " if (i == len(archivos_raiz) - 1) else "├── "
        print(f"{conector}{archivo['title']}")

    logger.info("Exploración completada.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explora y muestra el árbol de carpetas de Google Drive.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("folder_id", help="ID de la carpeta raíz en Google Drive.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run(args.folder_id.strip())
    except DriveAuthError as e:
        logger.error("Error de autenticación: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Exploración interrumpida por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Ejecutar tests del pipeline — deben pasar**

```
python -m pytest tests/cli/test_pipeline.py -v
```

Resultado esperado: `4 passed`

- [ ] **Step 6: Ejecutar suite completa — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `53 passed`

- [ ] **Step 7: Commit**

```bash
git add contratos/cli/pipeline.py contratos/cli/explorar.py tests/cli/test_pipeline.py
git commit -m "feat(cli): add pipeline and explorar CLI entry points"
```

---

## Task 10: Cleanup — actualizar `gui.py` y eliminar scripts originales

**Files:**
- Modify: `gui.py` (actualizar import)
- Delete: `convert_images_to_pdf.py`, `corregir_contratos_pdf.py`, `drive_uploader.py`, `explorar_drive.py`, `limpiar_duplicados_drive.py`, `pipeline_contratos.py`, `subir_contratos_drive.py`, `subir_semana.py`

- [ ] **Step 1: Actualizar el import en `gui.py`**

En `gui.py` línea 5, cambiar:

```python
# ANTES
from convert_images_to_pdf import collect_images, convert_image_to_pdf, merge_images_to_pdf
```

```python
# DESPUÉS
from contratos.core.pdf_converter import collect_images, convert_image_to_pdf, merge_images_to_pdf
```

- [ ] **Step 2: Verificar que `gui.py` arranca sin errores de importación**

```
python -c "import gui"
```

Resultado esperado: sin errores (puede fallar con tkinter si no hay display, pero no con ImportError)

- [ ] **Step 3: Ejecutar suite completa una última vez antes de borrar**

```
python -m pytest tests/ -v
```

Resultado esperado: `53 passed`

- [ ] **Step 4: Eliminar los scripts originales**

```powershell
Remove-Item convert_images_to_pdf.py, corregir_contratos_pdf.py, drive_uploader.py, explorar_drive.py, limpiar_duplicados_drive.py, pipeline_contratos.py, subir_contratos_drive.py, subir_semana.py
```

- [ ] **Step 5: Ejecutar suite completa una vez más — sin regresiones**

```
python -m pytest tests/ -v
```

Resultado esperado: `53 passed`

- [ ] **Step 6: Commit final**

```bash
git add -A
git commit -m "refactor: migrate to contratos/ package, remove legacy root scripts"
```

---

## Referencia rápida de comandos

| Tarea | Comando |
|---|---|
| Subir contratos | `python -m contratos.cli.subir_contratos <carpeta> <drive_id>` |
| Subir semana | `python -m contratos.cli.subir_semana --ruta_local <ruta> --drive_folder_id <id>` |
| Pipeline completo | `python -m contratos.cli.pipeline <carpeta> <drive_id>` |
| Solo pasos 2 y 3 | `python -m contratos.cli.pipeline <carpeta> <drive_id> --pasos 2 3` |
| Limpiar duplicados | `python -m contratos.cli.limpiar <drive_id>` |
| Explorar Drive | `python -m contratos.cli.explorar <drive_id>` |
| GUI | `python gui.py` |
| Tests | `python -m pytest tests/ -v` |
