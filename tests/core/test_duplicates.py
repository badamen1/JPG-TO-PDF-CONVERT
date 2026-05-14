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
