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
