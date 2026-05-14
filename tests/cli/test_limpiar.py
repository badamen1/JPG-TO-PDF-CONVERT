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
