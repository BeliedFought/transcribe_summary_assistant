"""
Проверка соединения с Ollama.

Если ollama.enabled=false - завершается без действий.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import PROJECT_ROOT, config, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t

logger = get_logger("ai_ollama_check", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    if not config.getboolean("ollama", "enabled", fallback=False):
        logger.info(t("msg.ollama_disabled"))
        return

    import requests

    base_url = config.get("ollama", "base_url", fallback="http://localhost:11434")
    timeout = config.getint("ollama", "timeout", fallback=60)

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            logger.info(t("msg.ollama_ok"))
        else:
            logger.error(
                t("error.connection_failed", detail=f"HTTP {response.status_code}")
            )
            sys.exit(1)
    except requests.RequestException as e:
        logger.error(t("error.connection_failed", detail=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
