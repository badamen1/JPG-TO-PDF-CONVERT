class ContratosError(Exception):
    """Base para todos los errores del proyecto."""


class DriveAuthError(ContratosError):
    """Falla al autenticar con Google Drive."""


class DriveUploadError(ContratosError):
    """Falla al subir un archivo a Google Drive."""


class PdfProcessingError(ContratosError):
    """Falla al procesar o corregir un PDF."""
