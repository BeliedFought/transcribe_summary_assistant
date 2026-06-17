"""
Проверка соединения с DeepSeek API.

Выполняет GET-запрос к базовому URL для проверки доступности.
"""

import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import PROJECT_ROOT, config, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t

logger = get_logger("api_check_connection", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        logger.error(t("error.api_key_missing", key="DEEPSEEK_API_KEY"))
        sys.exit(1)

    api_url = config.get("deepseek", "api_url", fallback="https://api.deepseek.com/v1")
    timeout = config.getint("deepseek", "timeout", fallback=60)

    try:
        response = requests.get(
            api_url + "/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
        if response.status_code == 200:
            logger.info(t("msg.api_deepseek_ok"))
        else:
            logger.error(
                t("error.connection_failed", detail=f"HTTP {response.status_code}: {response.text}")
            )
            sys.exit(1)
    except requests.RequestException as e:
        logger.error(t("error.connection_failed", detail=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
