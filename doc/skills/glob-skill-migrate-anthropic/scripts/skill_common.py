#!/usr/bin/env python3
"""Общие константы и помощники чекеров навыков (check_all_skills.py, check_package.py).

Единая точка правды для таксономии типов, префиксов имени, справочника
категорий и разбора frontmatter. Дублирование этих правил между чекерами -
источник расхождения проверок, поэтому они вынесены в общий модуль. Модуль
только предоставляет константы и чистые функции, сам проверок не выполняет.
"""

import re
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

VALID_SLUGS = ("hub_loc", "hub_glob", "pr_glob", "pr_loc")
LOCAL_SLUG = "pr_loc"
FLAT_PREFIX_TO_SLUG = {"hub_": "hub_loc", "glob_": "hub_glob", "pg_": "pr_glob", "pl_": "pr_loc"}
DIR_PREFIX_TO_SLUG = {"hub-": "hub_loc", "glob-": "hub_glob", "pg-": "pr_glob", "pl-": "pr_loc"}
CATEGORY_NAMES = {
    "sync": "Синхронизация",
    "update": "Актуализация",
    "audit": "Аудит",
    "skill": "Навыки",
    "cfg": "Конфигурация",
    "rules": "Правила агентов",
    "agent": "Правила работы с агентом",
    "shell": "Настройки терминала",
    "alias": "Системные алиасы",
    "git": "Настройки GIT",
    "ssh": "Настройки SSH",
}


def stamp() -> str:
    """Метка времени в формате строгого режима логгера (04.04.01)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fail(message: str) -> None:
    print(f"{stamp()} [!] {message}")


def info(message: str) -> None:
    print(f"{stamp()} [i] {message}")


def file_text(path: Path) -> str:
    """Прочитать файл; при ошибке чтения вернуть пустую строку."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontmatter_bounds(text: str) -> tuple[int, int] | None:
    """Индексы строк-разделителей frontmatter (открывающий, закрывающий) или None.

    Разделитель - отдельная строка из трех дефисов; открывающий ищется только
    в начале файла. Дефисы внутри строк (таблицы, ASCII-разделители, вложенные
    блоки) разделителями не считаются.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip().lstrip("\ufeff") != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return 0, index
    return None


def frontmatter_block(text: str) -> str:
    """Вернуть текст frontmatter (между строками-разделителями ---) или пустую строку."""
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return ""
    return "\n".join(text.splitlines()[bounds[0] + 1:bounds[1]])


def body_text(text: str) -> str:
    """Вернуть тело документа (текст после frontmatter) или весь текст, если его нет."""
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return text
    return "\n".join(text.splitlines()[bounds[1] + 1:])


def flat_value(fm: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(\S.*)$", fm, re.MULTILINE)
    return match.group(1).strip() if match else ""


def metadata_value(fm: str, key: str) -> str:
    match = re.search(rf"^\s+{key}:\s*(\S.*)$", fm, re.MULTILINE)
    return match.group(1).strip() if match else ""


def has_top_level_type(fm: str) -> bool:
    return bool(re.search(r"^type:\s*\S", fm, re.MULTILINE))


def name_category(name: str, prefix: str) -> str:
    """Второй сегмент имени после типового префикса (без расширения)."""
    return re.split(r"[_\-]", name[len(prefix):], maxsplit=1)[0]


def is_index_name(name: str) -> bool:
    """Индексный файл каталога навыков (навыком не является, в проверку не входит)."""
    return name.startswith("_index")


def is_prefix_optional(mtype: str) -> bool:
    """Для локального навыка (pr_loc) типовой префикс имени опционален."""
    return mtype == LOCAL_SLUG
