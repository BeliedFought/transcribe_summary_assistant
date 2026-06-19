"""
Загрузка моделей Ollama из конфига.

Если ollama.enabled=false - завершается без действий.
"""

import sys

from src.config import PROJECT_ROOT, config, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t
from src.startup import validate_startup

logger = get_logger("ai_ollama_pull_models", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")
validate_startup(logger)


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    if not config.getboolean("ollama", "enabled", fallback=False):
        logger.info(t("msg.ollama_disabled"))
        return

    import requests

    base_url = config.get("ollama", "base_url", fallback="http://localhost:11434")
    models_str = config.get("ollama", "model", fallback="")
    timeout = config.getint("ollama", "timeout", fallback=60)

    if not models_str:
        logger.warning(t("msg.ollama_models_not_configured"))
        return

    models = [m.strip() for m in models_str.split(",") if m.strip()]

    for model in models:
        try:
            logger.info(t("msg.ollama_downloading_model", model=model))
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model},
                timeout=timeout,
            )
            if response.status_code == 200:
                logger.info(t("msg.ollama_model_downloaded", model=model))
            else:
                logger.error(
                    t("msg.ollama_model_download_error", model=model, detail=f"HTTP {response.status_code}")
                )
                sys.exit(1)
        except requests.RequestException as e:
            logger.error(t("msg.ollama_model_download_error", model=model, detail=str(e)))
            sys.exit(1)


if __name__ == "__main__":
    main()
