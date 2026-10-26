#!/usr/bin/env python3
"""Проверка пакета навыка формата Anthropic после сборки или миграции.

Проверяет структуру пакета, поле name в frontmatter, тип навыка
(metadata.type - валидный слаг, соответствие префиксу имени), категорию
(metadata.category / metadata.category_name - по закрытому справочнику,
соответствие второму сегменту имени каталога, заполнение парой), исполнимость
и shebang скриптов, компилирует scripts/*.py (артефакты __pycache__ удаляет)
и предупреждает об исполняемых fenced-блоках в теле SKILL.md без вызова
скриптов пакета. Кроме удаления __pycache__ ничего не меняет.

Использование:
    check_package.py <skill-dir>
"""

import compileall
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # не создавать __pycache__ в пакете: проверка ничего не меняет

from skill_common import (
    CATEGORY_NAMES,
    DIR_PREFIX_TO_SLUG,
    EXIT_FAIL,
    EXIT_OK,
    EXIT_USAGE,
    body_text,
    fail,
    frontmatter_block,
    is_prefix_optional,
    metadata_value,
    name_category,
    stamp,
)

EXECUTABLE_LANGS = {"bash", "sh", "shell", "python", "python3", "py"}
SCRIPT_SUFFIXES = {".py", ".sh", ".bash"}
FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
FENCE_CLOSE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")


def check_category(fm: str, skill_dir: Path) -> int:
    """Проверить категорию: metadata.category / category_name по справочнику и имени каталога."""
    errors = 0
    category = metadata_value(fm, "category")
    category_name = metadata_value(fm, "category_name")
    if not category and not category_name:
        return 0
    if not category or not category_name:
        fail("frontmatter: category и category_name заполняются только парой")
        return 1
    if category not in CATEGORY_NAMES:
        fail(f"metadata.category ({category}) не из справочника - допустимы: {', '.join(CATEGORY_NAMES)}")
        errors += 1
    elif CATEGORY_NAMES[category] != category_name:
        fail(f"metadata.category_name ({category_name}) не соответствует справочнику для {category} ({CATEGORY_NAMES[category]})")
        errors += 1
    prefix = next((p for p in DIR_PREFIX_TO_SLUG if skill_dir.name.startswith(p)), "")
    if prefix:
        segment = name_category(skill_dir.name, prefix)
        if segment != category:
            fail(f"второй сегмент имени каталога ({segment}) не совпадает с metadata.category ({category})")
            errors += 1
    return errors


def check_type(fm: str, skill_dir: Path) -> int:
    """Проверить тип навыка: metadata.type - валидный слаг, соответствует префиксу."""
    errors = 0
    if re.search(r"^type:\s*\S", fm, re.MULTILINE):
        fail("frontmatter: верхнеуровневое поле type недопустимо - тип в metadata.type")
        errors += 1
    match_type = re.search(r"^\s+type:\s*(\S+)", fm, re.MULTILINE)
    if not match_type:
        fail("frontmatter: metadata.type не найден - поле типа обязательно (hub_loc, hub_glob, pr_glob, pr_loc)")
        return errors + 1
    mtype = match_type.group(1)
    valid = ", ".join(DIR_PREFIX_TO_SLUG.values())
    if mtype not in DIR_PREFIX_TO_SLUG.values():
        fail(f"metadata.type ({mtype}) невалиден - допустимы: {valid}")
        return errors + 1
    prefix_slug = next(
        (slug for prefix, slug in DIR_PREFIX_TO_SLUG.items() if skill_dir.name.startswith(prefix)),
        "",
    )
    if not prefix_slug:
        if not is_prefix_optional(mtype):  # для локальных навыков (pr_loc) префикс опционален
            fail(f"имя каталога без типового префикса ({', '.join(DIR_PREFIX_TO_SLUG)})")
            errors += 1
    elif prefix_slug != mtype:
        fail(f"префикс имени ({prefix_slug}) не соответствует metadata.type ({mtype})")
        errors += 1
    return errors


def check_name(skill_dir: Path) -> tuple[int, str]:
    """Проверить SKILL.md: name, тип; вернуть ошибки и текст."""
    errors = 0
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        fail("SKILL.md отсутствует в корне пакета")
        return 1, ""
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(\S+)", text, re.MULTILINE)
    if not match:
        fail("frontmatter: поле name не найдено")
        errors += 1
    elif match.group(1) != skill_dir.name:
        fail(f"frontmatter name ({match.group(1)}) не совпадает с именем каталога ({skill_dir.name})")
        errors += 1
    fm = frontmatter_block(text)
    errors += check_type(fm, skill_dir)
    errors += check_category(fm, skill_dir)
    return errors, text


def check_fenced_blocks(text: str) -> int:
    """Предупредить об исполняемых fenced-блоках в теле без вызова скриптов пакета.

    Тело берется после frontmatter; ограждение отслеживается построчно по литере
    и длине (``` или ~~~), закрытием считается только строка из той же литеры
    длиной не меньше открывающей. Дефисы в таблицах и ASCII-разделителях на
    разбор не влияют.
    """
    warnings = 0
    fence = ""
    fence_len = 0
    lang = None
    lines: list[str] = []
    for line in body_text(text).splitlines():
        if lang is None:
            match = FENCE_OPEN_RE.match(line)
            if not match:
                continue
            fence = match.group(1)[0]
            fence_len = len(match.group(1))
            lang = match.group(2).lower() or "text"
            lines = []
            continue
        match = FENCE_CLOSE_RE.match(line)
        if match and match.group(1)[0] == fence and len(match.group(1)) >= fence_len:
            content = "\n".join(lines)
            if lang in EXECUTABLE_LANGS and content.strip() and "${CLAUDE_SKILL_DIR}" not in content:
                preview = next((item for item in lines if item.strip()), "")
                print(f"{stamp()} [*] тело: блок {lang} без вызова скрипта пакета - проверить: {preview.strip()}")
                warnings += 1
            lang = None
            continue
        lines.append(line)
    return warnings


def check_scripts(skill_dir: Path) -> tuple[int, int]:
    """Проверить scripts/: исполнимость, shebang, компиляция python; вернуть ошибки и предупреждения."""
    errors = 0
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return 0, 0
    py_files: list[Path] = []
    for path in sorted(scripts_dir.iterdir()):
        if not path.is_file() or path.suffix not in SCRIPT_SUFFIXES:
            continue
        if path.suffix == ".py":
            py_files.append(path)
        if not path.stat().st_mode & 0o111:
            fail(f"скрипт не исполняемый: scripts/{path.name} (chmod +x)")
            errors += 1
        first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        if not first_line or not first_line[0].startswith("#!"):
            fail(f"скрипт без shebang: scripts/{path.name}")
            errors += 1
    for path in py_files:
        if not compileall.compile_file(str(path), quiet=2):
            fail(f"ошибка компиляции: scripts/{path.name}")
            errors += 1
    cache = scripts_dir / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache)
    return errors, 0


def main() -> int:
    if len(sys.argv) != 2:
        print(f"{stamp()} [!] Использование: {Path(sys.argv[0]).name} <skill-dir>", file=sys.stderr)
        return EXIT_USAGE

    skill_dir = Path(sys.argv[1])
    if not skill_dir.is_dir():
        fail(f"каталог пакета не найден: {skill_dir}")
        return EXIT_FAIL

    errors, text = check_name(skill_dir)
    if text:
        warnings = check_fenced_blocks(text)
        if warnings:
            print(f"{stamp()} [*] предупреждений по телу SKILL.md - {warnings}")
    script_errors, _ = check_scripts(skill_dir)
    errors += script_errors

    if errors:
        fail(f"проверка не пройдена: ошибок - {errors}")
        return EXIT_FAIL
    print(f"{stamp()} [i] пакет проверен: ошибок нет")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
