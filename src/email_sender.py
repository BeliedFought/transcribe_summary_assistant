"""
Отправка саммари на email через SMTP.

Использование:
    from src.email_sender import send_summary, is_email_enabled
    if is_email_enabled(config):
        send_summary(summary_text, source_name, config)

Параметры подключения - в секции [email] config.ini.
Учетные данные (логин, пароль приложения) - в .env:
    SMTP_USER, SMTP_PASSWORD
"""

import logging
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from configparser import ConfigParser

import markdown

from src.localization import t
from src.logger import get_logger
from src.config import PROJECT_ROOT

_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    """Создать логгер при первом использовании (lazy)."""
    global _logger
    if _logger is None:
        _logger = get_logger("email_sender", log_dir=PROJECT_ROOT / "log")
    return _logger


def is_email_enabled(config: ConfigParser) -> bool:
    """Включена ли отправка email в конфигурации."""
    return config.getboolean("email", "enabled", fallback=False)


def _read_credentials(config: ConfigParser) -> tuple[str, str]:
    user = os.environ.get("SMTP_USER", "").strip()
    if not user:
        user = config.get("email", "from", fallback="").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    return user, password


def _markdown_to_html(markdown_text: str) -> str:
    """
    Сконвертировать markdown в HTML-письмо с базовым оформлением.

    :param markdown_text: текст саммари в markdown
    :return: строка HTML для тела письма
    """
    html_body = markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.6;
    color: #1a1a1a;
    margin: 0;
    padding: 24px;
    background-color: #f4f4f5;
  }}
  .container {{
    max-width: 720px;
    margin: 0 auto;
    background-color: #ffffff;
    padding: 32px;
    border-radius: 8px;
  }}
  h1, h2, h3, h4 {{
    color: #18181b;
    line-height: 1.3;
  }}
  h1 {{ font-size: 1.5em; border-bottom: 1px solid #e4e4e7; padding-bottom: 8px; }}
  h2 {{ font-size: 1.25em; }}
  h3 {{ font-size: 1.1em; }}
  a {{ color: #2563eb; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
  }}
  th, td {{
    border: 1px solid #d4d4d8;
    padding: 8px 12px;
    text-align: left;
  }}
  th {{ background-color: #f4f4f5; }}
  code {{
    background-color: #f4f4f5;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 0.9em;
  }}
  pre {{
    background-color: #18181b;
    color: #f4f4f5;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
  }}
  pre code {{
    background-color: transparent;
    padding: 0;
    color: inherit;
  }}
  blockquote {{
    border-left: 4px solid #d4d4d8;
    margin: 16px 0;
    padding: 8px 16px;
    color: #52525b;
  }}
  hr {{ border: none; border-top: 1px solid #e4e4e7; margin: 24px 0; }}
  ul, ol {{ padding-left: 24px; }}
</style>
</head>
<body>
<div class="container">
{body}
</div>
</body>
</html>""".format(body=html_body)


def send_summary(summary_text: str, title: str, channel: str, config: ConfigParser) -> None:
    """
    Отправить саммари на email в формате multipart: plain text (markdown) и HTML.

    Тема формируется из шаблона [email] subject_summary с плейсхолдерами
    {title} (название ролика/файла) и {channel} (имя канала). Если канал
    пуст, соответствующая часть опускается.

    :param summary_text: текст саммари (markdown)
    :param title: название ролика или имя файла для подстановки в тему
    :param channel: имя канала (пусто для источников без канала)
    :param config: ConfigParser с секцией [email]
    :raises RuntimeError: при ошибке подключения или отправки
    """
    subject_template = config.get("email", "subject_summary", fallback="Краткий пересказ - {channel} - {title}")
    _get_logger().info(t("msg.email_sending", to=config.get("email", "to", fallback="")))
    _send_document(summary_text, subject_template, title, channel, config)


def send_article(article_text: str, title: str, channel: str, config: ConfigParser) -> None:
    """
    Отправить статью отдельным письмом в формате multipart: plain text (markdown) и HTML.

    :param article_text: текст статьи (markdown)
    :param title: название ролика или имя файла для подстановки в тему
    :param channel: имя канала (пусто для источников без канала)
    :param config: ConfigParser с секцией [email]
    :raises RuntimeError: при ошибке подключения или отправки
    """
    subject_template = config.get("email", "subject_article", fallback="Статья: {title}")
    _get_logger().info(t("msg.email_sending_article", to=config.get("email", "to", fallback="")))
    _send_document(article_text, subject_template, title, channel, config)


def _format_subject(template: str, title: str, channel: str) -> str:
    """
    Собрать тему письма из шаблона с плейсхолдерами {title} и {channel}.

    При пустом канале висячие разделители вокруг него схлопываются, чтобы
    тема оставалась корректной (например, для аудио/видео-файлов).
    """
    subject = template.replace("{title}", title.strip()).replace("{channel}", channel.strip())
    subject = re.sub(r"\s*-\s*-\s*", " - ", subject)
    subject = re.sub(r"^\s*-\s*|\s*-\s*$", "", subject)
    return subject.strip()


def _send_document(
    text: str,
    subject_template: str,
    title: str,
    channel: str,
    config: ConfigParser,
) -> None:
    """
    Общее ядро отправки документа на email.

    :param text: текст документа (markdown)
    :param subject_template: шаблон темы с плейсхолдерами {title}/{channel}
    :param title: название ролика или имя файла
    :param channel: имя канала (пусто для источников без канала)
    :param config: ConfigParser с секцией [email]
    :raises RuntimeError: при ошибке подключения или отправки
    """
    smtp_host = config.get("email", "smtp_host", fallback="smtp.yandex.ru")
    smtp_port = config.getint("email", "smtp_port", fallback=465)
    smtp_security = config.get("email", "smtp_security", fallback="ssl").strip().lower()
    sender = os.environ.get("SMTP_FROM", "").strip() or config.get("email", "from", fallback="").strip()
    recipient = os.environ.get("SMTP_TO", "").strip() or config.get("email", "to", fallback="").strip()

    if not sender:
        raise RuntimeError(t("error.email_from_missing"))
    if not recipient:
        raise RuntimeError(t("error.email_to_missing"))

    user, password = _read_credentials(config)
    if not user or not password:
        raise RuntimeError(t("error.email_credentials_missing"))

    subject = _format_subject(subject_template, title, channel)

    html_body = _markdown_to_html(text)

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html_body, subtype="html")

    if smtp_security == "ssl":
        _send_ssl(message, smtp_host, smtp_port, user, password)
    elif smtp_security == "starttls":
        _send_starttls(message, smtp_host, smtp_port, user, password)
    elif smtp_security == "none":
        _send_plain(message, smtp_host, smtp_port, user, password)
    else:
        raise RuntimeError(t("error.unknown_smtp_security", value=smtp_security))

    _get_logger().info(t("msg.email_sent", to=recipient))


def _send_ssl(
    message: EmailMessage,
    host: str,
    port: int,
    user: str,
    password: str,
) -> None:
    """Отправить через SMTP_SSL."""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
        server.login(user, password)
        server.send_message(message)


def _send_starttls(
    message: EmailMessage,
    host: str,
    port: int,
    user: str,
    password: str,
) -> None:
    """Отправить через SMTP с STARTTLS."""
    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(user, password)
        server.send_message(message)


def _send_plain(
    message: EmailMessage,
    host: str,
    port: int,
    user: str,
    password: str,
) -> None:
    """Отправить через SMTP без шифрования."""
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.login(user, password)
        server.send_message(message)
