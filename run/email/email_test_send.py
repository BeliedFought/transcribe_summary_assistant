"""
Тест отправки саммари на email.

Отправляет тестовое письмо с демонстрационным текстом, используя параметры
секции [email] config.ini и учетные данные из .env (SMTP_USER, SMTP_PASSWORD).

Если в config.ini адреса from/to не заполнены или содержат заглушку
(your@yandex.ru), они автоматически берутся из SMTP_USER (рассылка себе).

Запуск: python run/email/email_test_send.py
"""

import os
import sys
from datetime import datetime

from src.config import PROJECT_ROOT, config, APP_NAME, APP_VERSION
from src.email_sender import send_summary
from src.logger import get_logger
from src.localization import init as i18n_init, t
from src.startup import validate_startup

logger = get_logger("email_test_send", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")
validate_startup(logger)

PLACEHOLDER_ADDR = "your@yandex.ru"


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    smtp_from = os.environ.get("SMTP_FROM", "").strip()
    smtp_to = os.environ.get("SMTP_TO", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    if smtp_from:
        config.set("email", "from", smtp_from)
    elif smtp_user:
        from_addr = config.get("email", "from", fallback="").strip()
        if not from_addr or from_addr == PLACEHOLDER_ADDR:
            config.set("email", "from", smtp_user)
    if smtp_to:
        config.set("email", "to", smtp_to)
    elif smtp_user:
        to_addr = config.get("email", "to", fallback="").strip()
        if not to_addr or to_addr == PLACEHOLDER_ADDR:
            config.set("email", "to", smtp_user)

    test_text = t("msg.email_test_body", ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        send_summary(test_text, t("msg.email_test_subject"), "", config)
    except Exception as e:
        logger.error(t("error.email_send_failed", detail=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
