"""
Стартовая проверка окружения для entry-point скриптов.

Обеспечивает fail-fast: проверяет наличие базовых файлов проекта
(config/config.ini) до основной логики. Используется всеми run/ скриптами.
"""

import sys
from typing import Any

from src.config import PROJECT_ROOT
from src.localization import t


def validate_startup(logger: Any) -> None:
    """
    Проверить базовое окружение перед основной логикой скрипта.

    :param logger: настроенный логгер скрипта для вывода проблем
    """
    config_file = PROJECT_ROOT / "config" / "config.ini"
    if not config_file.exists():
        logger.error(t("error.config_not_found", path=str(config_file)))
        sys.exit(1)
