#!/usr/bin/env python3
"""Check an Anthropic-format skill package after assembly or migration.

Checks the package structure, the name field in frontmatter, the skill type
(metadata.type - a valid slug, conformance to the name prefix), the category
(metadata.category / metadata.category_name - against the closed reference,
conformance to the second segment of the directory name, filled as a pair),
script executability and shebang, compiles scripts/*.py (removes __pycache__
artifacts), and warns about executable fenced blocks in the SKILL.md body
without calls to package scripts. Changes nothing except removing __pycache__.

Usage:
    check_package.py <skill-dir>
"""

import compileall
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # do not create __pycache__ in the package: the check changes nothing

from skill_common import (
    CATEGORY_NAMES,
    CATEGORY_NAMES_EN,
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
    """Check the category: metadata.category / category_name against the reference and directory name."""
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
    elif category_name not in (CATEGORY_NAMES[category], CATEGORY_NAMES_EN[category]):
        fail(
            f"metadata.category_name ({category_name}) не соответствует справочнику для {category} "
            f"({CATEGORY_NAMES_EN[category]} / {CATEGORY_NAMES[category]})"
        )
        errors += 1
    prefix = next((p for p in DIR_PREFIX_TO_SLUG if skill_dir.name.startswith(p)), "")
    if prefix:
        segment = name_category(skill_dir.name, prefix)
        if segment != category:
            fail(f"второй сегмент имени каталога ({segment}) не совпадает с metadata.category ({category})")
            errors += 1
    return errors


def check_type(fm: str, skill_dir: Path) -> int:
    """Check the skill type: metadata.type - a valid slug matching the prefix."""
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
        if not is_prefix_optional(mtype):  # for local skills (pr_loc) the prefix is optional
            fail(f"имя каталога без типового префикса ({', '.join(DIR_PREFIX_TO_SLUG)})")
            errors += 1
    elif prefix_slug != mtype:
        fail(f"префикс имени ({prefix_slug}) не соответствует metadata.type ({mtype})")
        errors += 1
    return errors


def check_name(skill_dir: Path) -> tuple[int, str]:
    """Check SKILL.md: name, type; return errors and text."""
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
    """Warn about executable fenced blocks in the body without package script calls.

    The body is taken after frontmatter; the fence is tracked line by line by
    character and length (``` or ~~~); only a line of the same character at
    least as long as the opening one counts as a close. Hyphens in tables and
    ASCII separators do not affect parsing.
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
    """Check scripts/: executability, shebang, python compilation; return errors and warnings."""
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
