import sys
import logging
from logging import StreamHandler

from contratos.logger import get_logger


def test_get_logger_returns_logger_with_correct_name():
    logger = get_logger("contratos.test.nombre")
    assert logger.name == "contratos.test.nombre"
    assert isinstance(logger, logging.Logger)


def test_get_logger_has_stdout_handler():
    logger = get_logger("contratos.test.handler")
    assert any(
        isinstance(h, StreamHandler) and h.stream is sys.stdout
        for h in logger.handlers
    )


def test_get_logger_no_duplicate_handlers():
    get_logger("contratos.test.idempotent")
    logger = get_logger("contratos.test.idempotent")
    assert len(logger.handlers) == 1


def test_get_logger_level_is_info():
    logger = get_logger("contratos.test.level")
    assert logger.level == logging.INFO
