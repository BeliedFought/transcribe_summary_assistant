"""
Саммаризация и генерация статьи из транскрипции через DeepSeek API.

Поддерживает map-reduce для длинных текстов (>6000 токенов).
Формирует два вида документов:
- саммари: структурированный разбор разговора (общий контекст + по ролям);
- статья: краткое изложение, готовое к публикации в Telegram или на сайте.

Использование:
    from src.summarizer import summarize_deepseek, generate_article_deepseek
    summary_text = summarize_deepseek(transcription_with_roles, config)
    article_text = generate_article_deepseek(transcription_with_roles, config)
"""

import json
import logging
from configparser import ConfigParser
from typing import Any

import requests

from src.localization import t
from src.retry import retry, NON_RETRYABLE_HTTP_CODES

MAX_CHUNK_TOKENS: int = 6000
_CHARS_PER_TOKEN: float = 2.5


def _estimate_tokens(text: str) -> int:
    """Примерная оценка количества токенов."""
    return int(len(text) / _CHARS_PER_TOKEN)


def _build_messages(system_prompt: str, user_text: str) -> list[dict[str, str]]:
    """Собрать список сообщении для API."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]


def _call_deepseek_api(
    messages: list[dict[str, str]],
    config: ConfigParser,
) -> tuple[str, dict[str, int]]:
    """Вызвать DeepSeek API с retry. Возвращает (текст, usage)."""
    api_url = config.get("deepseek", "api_url", fallback="https://api.deepseek.com/v1")
    model = config.get("deepseek", "model", fallback="deepseek-chat")
    temperature = config.getfloat("deepseek", "temperature", fallback=0.3)
    max_tokens = config.getint("deepseek", "max_tokens", fallback=4096)
    timeout = config.getint("deepseek", "timeout", fallback=60)

    import os
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    def _request() -> tuple[str, dict[str, int]]:
        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        if response.status_code in NON_RETRYABLE_HTTP_CODES:
            raise requests.HTTPError(
                f"DeepSeek API error {response.status_code}: {response.text}",
                response=response,
            )
        response.raise_for_status()
        data = response.json()
        usage = data.get("usage", {})
        usage_dict: dict[str, int] = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        return data["choices"][0]["message"]["content"], usage_dict

    return retry(
        _request,
        config,
        (requests.Timeout, requests.ConnectionError, requests.HTTPError),
    )


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """Разбить текст на чанки примерно по max_chars."""
    if _estimate_tokens(text) <= MAX_CHUNK_TOKENS:
        return [text]

    lines = text.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line)
        if current_len + line_len > max_chars and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len + 1

    if current:
        chunks.append("\n".join(current))

    return chunks


SUMMARY_SYSTEM_PROMPT: str = (
    "Ты - помощник для саммаризации разговоров. "
    "Проанализируй транскрипцию диалога и составь структурированное саммари на языке исходного текста. "
    "Начинай сразу с содержания, без вводных и пояснительных фраз. "
    "Саммари должно включать:\n"
    "1. Общий контекст: тема разговора, ключевые моменты, итоговый смысл.\n"
    "2. По ролям: для каждого диктора - его ключевые тезисы и аргументы.\n"
    "3. Ключевые моменты: нумерованный список.\n"
    "4. Посыл разговора: 2-3 предложения. Ответь на вопросы: какую мысль автор хочет донести до зрителя? К каким действиям или выводам он подталкивает аудиторию? Чего он добивается этим разговором?\n"
    "Формат вывода - Markdown с заголовками ## и ###."
)

ARTICLE_SYSTEM_PROMPT: str = (
    "Ты - редактор, превращающий транскрипцию разговора в готовую к публикации статью на русском языке. "
    "Напиши краткую структурированную статью на основе транскрипции.\n"
    "Требования:\n"
    "1. Начни с заголовка первого уровня (#), отражающего главную тему содержания.\n"
    "2. Объем - краткое изложение, без воды и повторов.\n"
    "3. Структурируй текст подзаголовками (##) и короткими абзацами.\n"
    "4. Пиши связным публицистическим стилем, готовым к публикации в Telegram или на сайте.\n"
    "5. Излагай содержание от третьего лица, не используй термины диктор, спикер, транскрипция.\n"
    "6. Не добавляй метаданные, технические пометки и временные метки.\n"
    "7. Не указывай источники, ссылки и любые упоминания оригинала.\n"
    "8. Выводи только текст статьи без пояснений и вступительных фраз.\n"
    "Формат вывода - Markdown."
)


def summarize_deepseek(transcription_with_roles: str, config: ConfigParser) -> tuple[str, dict[str, int]]:
    """
    Саммаризировать транскрипцию через DeepSeek API.

    :param transcription_with_roles: полный текст транскрипции с ролями
    :param config: ConfigParser с секцией [deepseek]
    :return: (текст саммари в формате Markdown, usage статистика)
    """
    return _generate_deepseek(transcription_with_roles, config, SUMMARY_SYSTEM_PROMPT)


def generate_article_deepseek(transcription_with_roles: str, config: ConfigParser) -> tuple[str, dict[str, int]]:
    """
    Сгенерировать статью для публикации из транскрипции через DeepSeek API.

    Статья - краткое структурированное изложение на русском языке, готовое
    к публикации в Telegram или на сайте, без метаданных и указания источников.

    :param transcription_with_roles: полный текст транскрипции с ролями
    :param config: ConfigParser с секцией [deepseek]
    :return: (текст статьи в формате Markdown, usage статистика)
    """
    return _generate_deepseek(transcription_with_roles, config, ARTICLE_SYSTEM_PROMPT)


def _generate_deepseek(
    transcription_with_roles: str,
    config: ConfigParser,
    system_prompt: str,
) -> tuple[str, dict[str, int]]:
    """
    Общее ядро генерации документа через DeepSeek API с map-reduce.

    :param transcription_with_roles: полный текст транскрипции с ролями
    :param config: ConfigParser с секцией [deepseek]
    :param system_prompt: системный промпт, задающий формат результата
    :return: (текст документа в формате Markdown, usage статистика)
    """
    logger = logging.getLogger(__name__)

    if _estimate_tokens(transcription_with_roles) <= MAX_CHUNK_TOKENS:
        messages = _build_messages(system_prompt, transcription_with_roles)
        content, usage = _call_deepseek_api(messages, config)
        return content, usage

    max_chars = int(MAX_CHUNK_TOKENS * _CHARS_PER_TOKEN * 0.7)
    chunks = _chunk_text(transcription_with_roles, max_chars)

    logger.info(t("msg.summarizing_map_reduce", chunks=len(chunks)))

    chunk_results: list[str] = []
    total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for i, chunk in enumerate(chunks):
        logger.info(t("msg.summarizing_chunk", current=i + 1, total=len(chunks)))
        chunk_prompt = system_prompt + "\n\n" + t("msg.summarizer_chunk_prefix", current=i + 1, total=len(chunks))
        messages = _build_messages(chunk_prompt, chunk)
        result, usage = _call_deepseek_api(messages, config)
        chunk_results.append(result)
        for k in total_usage:
            total_usage[k] += usage.get(k, 0)

    combined = "\n\n---\n\n".join(chunk_results)
    final_prompt = (
        system_prompt
        + "\n\nНиже приведены саммари отдельных частей разговора. Составь итоговый документ, "
        "объединив их в единый связный текст. "
        "Не добавляй вводных фраз и не подписывай результат как итоговое саммари или статья. "
        "Начинай сразу с содержания и заголовков, без префиксов вроде 'Итоговое саммари:'."
    )
    messages = _build_messages(final_prompt, combined)
    result_final, usage_final = _call_deepseek_api(messages, config)
    for k in total_usage:
        total_usage[k] += usage_final.get(k, 0)
    return result_final, total_usage
