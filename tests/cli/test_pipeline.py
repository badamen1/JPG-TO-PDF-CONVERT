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
