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
