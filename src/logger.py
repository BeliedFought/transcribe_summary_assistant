"""
Модуль логирования проекта.

Использование:
    from src.logger import get_logger
    logger = get_logger(__name__, log_dir=PROJECT_ROOT / "log")
    logger.info("Сообщение")
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


class _MarkerFormatter(logging.Formatter):
    """Форматтер с маркерами [!], [i], [*] вместо стандартных уровней."""

    MARKERS: dict[int, str] = {
        logging.ERROR: "[!]",
        logging.CRITICAL: "[!]",
        logging.WARNING: "[*]",
        logging.INFO: "[i]",
        logging.DEBUG: "[i]",
    }

    def __init__(self, menu_mode: bool = False) -> None:
        super().__init__()
        self._menu_mode = menu_mode

    def format(self, record: logging.LogRecord) -> str:
        if self._menu_mode:
            return record.getMessage()
        marker = self.MARKERS.get(record.levelno, "[i]")
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} {marker} {record.getMessage()}"


def get_logger(name: str, log_dir: Path, menu_mode: bool = False) -> logging.Logger:
    """
    Создать и вернуть логгер с выводом в консоль и в файл.

    :param name: имя скрипта (используется в имени лог-файла)
    :param log_dir: путь к папке log/ (объект Path)
    :param menu_mode: если True - без timestamp и маркеров
    :return: настроенный logging.Logger
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    script_name = name.replace(".", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"log_{script_name}_{timestamp}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = _MarkerFormatter(menu_mode=menu_mode)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
