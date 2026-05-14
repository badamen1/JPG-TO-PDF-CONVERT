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
