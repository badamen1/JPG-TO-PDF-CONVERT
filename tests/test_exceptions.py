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
