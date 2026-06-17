"""
Проверка соединения с SQLite.

Создает data/sessions.db если не существует,
выполняет SELECT 1 для проверки работоспособности.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import PROJECT_ROOT, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t

logger = get_logger("db_check_connection", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    db_path = PROJECT_ROOT / "data" / "sessions.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")
        conn.close()
        logger.info(t("msg.connection_db_ok"))
    except sqlite3.Error as e:
        logger.error(t("error.connection_failed", detail=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
