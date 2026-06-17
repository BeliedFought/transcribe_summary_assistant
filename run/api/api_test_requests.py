"""
Отправка тестового запроса к DeepSeek API.

Выполняет POST /chat/completions с простым промптом
и выводит ответ модели.
"""

import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import PROJECT_ROOT, config, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t

logger = get_logger("api_test_requests", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        logger.error(t("error.api_key_missing", key="DEEPSEEK_API_KEY"))
        sys.exit(1)

    api_url = config.get("deepseek", "api_url", fallback="https://api.deepseek.com/v1")
    model = config.get("deepseek", "model", fallback="deepseek-chat")
    timeout = config.getint("deepseek", "timeout", fallback=60)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Ответь одним словом: Ок"},
        ],
        "temperature": 0.3,
        "max_tokens": 16,
    }

    try:
        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            logger.info(t("msg.api_test_prompt", text="Ответь одним словом: Ок"))
            logger.info(t("msg.api_test_answer", text=answer))
            logger.info(t("msg.api_test_ok"))
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
