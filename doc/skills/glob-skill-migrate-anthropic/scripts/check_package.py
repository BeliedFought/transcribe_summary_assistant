#!/usr/bin/env python3
"""Проверка пакета навыка формата Anthropic после сборки или миграции.

Проверяет структуру пакета, поле name в frontmatter, исполнимость и shebang
скриптов, компилирует scripts/*.py (артефакты __pycache__ удаляет) и
предупреждает об исполняемых fenced-блоках в теле SKILL.md без вызова
скриптов пакета. Кроме удаления __pycache__ ничего не меняет.

Использование:
    check_package.py <skill-dir>
"""

import compileall
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

EXECUTABLE_LANGS = {"bash", "sh", "shell", "python", "python3", "py"}
SCRIPT_SUFFIXES = {".py", ".sh", ".bash"}

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def stamp() -> str:
    """Метка времени в формате строгого режима логгера (04.04.01)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fail(message: str) -> None:
    print(f"{stamp()} [!] {message}")


def check_name(skill_dir: Path) -> tuple[int, str]:
    """Проверить SKILL.md и совпадение name с именем каталога; вернуть ошибки и текст."""
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
    return errors, text


def check_fenced_blocks(text: str) -> int:
    """Предупредить об исполняемых fenced-блоках в теле без вызова скриптов пакета."""
    parts = text.split("---")
    body = parts[-1] if len(parts) >= 3 else text
    warnings = 0
    lang = None
    lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if lang is None and stripped.startswith("```"):
            lang = stripped[3:].strip().lower() or "text"
            lines = []
            continue
        if lang is not None and stripped == "```":
            content = "\n".join(lines)
            if lang in EXECUTABLE_LANGS and content.strip() and "${CLAUDE_SKILL_DIR}" not in content:
                preview = next((item for item in lines if item.strip()), "")
                print(f"{stamp()} [*] тело: блок {lang} без вызова скрипта пакета - проверить: {preview.strip()}")
                warnings += 1
            lang = None
            continue
        if lang is not None:
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
