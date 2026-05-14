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

    with patch("contratos.core.pdf_corrector.fitz.open", return_value=mock_doc):
        procesados, modificados = corregir_contratos(str(tmp_path))

    assert procesados == 1
    assert modificados == 0
