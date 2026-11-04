#!/usr/bin/env python3
"""Shared constants and helpers for skill checkers (check_all_skills.py, check_package.py).

A single source of truth for the type taxonomy, name prefixes, category
reference, and frontmatter parsing. Duplicating these rules between checkers is
a source of check drift, so they are moved into a shared module. The module
only provides constants and pure functions; it performs no checks itself.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True

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
    "shell": "Настройки терминала",
    "git": "Настройки GIT",
    "ssh": "Настройки SSH",
    "mine": "Добыча знаний",
}
CATEGORY_NAMES_EN = {
    "sync": "Sync",
    "update": "Update",
    "audit": "Audit",
    "skill": "Skills",
    "cfg": "Configuration",
    "rules": "Agent Rules",
    "shell": "Terminal Settings",
    "git": "Git Settings",
    "ssh": "SSH Settings",
    "mine": "Knowledge Mining",
}


def stamp() -> str:
    """Timestamp in the logger strict-mode format (04.04.01)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fail(message: str) -> None:
    print(f"{stamp()} [!] {message}")


def info(message: str) -> None:
    print(f"{stamp()} [i] {message}")


def file_text(path: Path) -> str:
    """Read the file; return an empty string on a read error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontmatter_bounds(text: str) -> tuple[int, int] | None:
    """Indices of frontmatter separator lines (opening, closing) or None.

    A separator is a standalone line of three hyphens; the opening one is looked
    for only at the start of the file. Hyphens inside lines (tables, ASCII
    separators, nested blocks) do not count as separators.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip().lstrip("\ufeff") != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return 0, index
    return None


def frontmatter_block(text: str) -> str:
    """Return the frontmatter text (between --- separator lines) or an empty string."""
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return ""
    return "\n".join(text.splitlines()[bounds[0] + 1:bounds[1]])


def body_text(text: str) -> str:
    """Return the document body (text after frontmatter) or the whole text when absent."""
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
    """Second name segment after the type prefix (without extension)."""
    return re.split(r"[_\-]", name[len(prefix):], maxsplit=1)[0]


def is_index_name(name: str) -> bool:
    """Skills directory index file (not a skill, excluded from the check)."""
    return name.startswith("_index")


def is_prefix_optional(mtype: str) -> bool:
    """For a local skill (pr_loc) the type name prefix is optional."""
    return mtype == LOCAL_SLUG
