#!/usr/bin/env python3
"""Проверка полноты: все навыки репозитория на соответствие требованиям стандартов.

Сверяет навыки обоих форматов во всех канонических местах хранения с
требованиями skill_standards.md и skill_anthropic_standards.md:
обязательные поля frontmatter, валидный слаг типа, соответствие префикса
имени типу и расположению, запрет ссылок на конкретные навыки чужих
репозиториев (пути ext/<repo-name>/ вместо плейсхолдеров). Ничего не меняет -
только отчет.

Использование:
    check_all_skills.py [корень-репозитория]
"""

import re
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

VALID_SLUGS = ("hub_loc", "hub_glob", "pr_glob", "pr_loc")
FLAT_PREFIX_TO_SLUG = {"hub_": "hub_loc", "glob_": "hub_glob", "pg_": "pr_glob"}
DIR_PREFIX_TO_SLUG = {"hub-": "hub_loc", "glob-": "hub_glob", "pg-": "pr_glob", "pl-": "pr_loc"}
FLAT_SLUG_TO_LOCATION = {
    "hub_loc": "корень doc/skills/",
    "hub_glob": "корень doc/skills/",
    "pr_glob": "doc/skills/<repo-name>/",
}
CONCRETE_EXT_RE = re.compile(r"ext/(?!<)(?!\{)[A-Za-z0-9_][A-Za-z0-9_-]*")
CYRILLIC_PLACEHOLDER_RE = re.compile(r"<[^>]*[А-Яа-яЁё][^>]*>")


def stamp() -> str:
    """Метка времени в формате строгого режима логгера (04.04.01)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fail(message: str) -> None:
    print(f"{stamp()} [!] {message}")


def info(message: str) -> None:
    print(f"{stamp()} [i] {message}")


def frontmatter_block(path: Path) -> str:
    """Вернуть текст frontmatter (между двумя --- в начале файла) или пустую строку."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    parts = text.split("---")
    return parts[1] if len(parts) >= 3 else ""


def flat_value(fm: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(\S.*)$", fm, re.MULTILINE)
    return match.group(1).strip() if match else ""


def metadata_value(fm: str, key: str) -> str:
    match = re.search(rf"^\s+{key}:\s*(\S.*)$", fm, re.MULTILINE)
    return match.group(1).strip() if match else ""


def has_top_level_type(fm: str) -> bool:
    return bool(re.search(r"^type:\s*\S", fm, re.MULTILINE))


def check_concrete_ext_refs(path: Path, rel: Path) -> int:
    """Запрет ссылок на конкретные навыки чужих репозиториев (пути ext/<repo-name>/)."""
    errors = 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    for match in CONCRETE_EXT_RE.finditer(text):
        fail(f"{rel}: упоминание конкретного навыка чужого репозитория ({match.group(0)}...) - заменить плейсхолдерами (<repo-name>, <name>)")
        errors += 1
    for match in CYRILLIC_PLACEHOLDER_RE.finditer(text):
        fail(f"{rel}: кириллический плейсхолдер ({match.group(0)}) - только латиница (<repo-name>, <name>, <dir-name>)")
        errors += 1
    return errors


def check_internal(path: Path, root: Path, in_repo_subfolder: bool) -> int:
    """Проверить плоский навык внутреннего формата; вернуть число ошибок."""
    rel = path.relative_to(root)
    errors = 0
    errors += check_concrete_ext_refs(path, rel)
    fm = frontmatter_block(path)
    if not fm:
        fail(f"{rel}: frontmatter отсутствует")
        return 1

    fid = flat_value(fm, "id")
    if not fid:
        fail(f"{rel}: поле id не найдено")
        errors += 1
    elif fid != path.stem:
        fail(f"{rel}: id ({fid}) не совпадает с именем файла ({path.stem})")
        errors += 1

    if not flat_value(fm, "description"):
        fail(f"{rel}: поле description не найдено")
        errors += 1
    if not flat_value(fm, "auto_apply"):
        fail(f"{rel}: поле auto_apply не найдено")
        errors += 1

    ftype = flat_value(fm, "type")
    if not ftype:
        fail(f"{rel}: поле type не найдено - слаг типа обязателен ({', '.join(VALID_SLUGS)})")
        errors += 1
        return errors
    if ftype not in VALID_SLUGS:
        fail(f"{rel}: type ({ftype}) невалиден - допустимы: {', '.join(VALID_SLUGS)}")
        errors += 1
        return errors

    prefix_slug = next((slug for prefix, slug in FLAT_PREFIX_TO_SLUG.items() if path.name.startswith(prefix)), "")
    if not prefix_slug:
        fail(f"{rel}: нет типового префикса (hub_, glob_, pg_) - переименовать в pg_{path.stem}")
        errors += 1
        return errors
    if prefix_slug != ftype:
        fail(f"{rel}: префикс имени ({prefix_slug}) не соответствует type ({ftype})")
        errors += 1

    if ftype in ("hub_loc", "hub_glob") and in_repo_subfolder:
        fail(f"{rel}: навык типа {ftype} должен лежать в корне doc/skills/")
        errors += 1
    if ftype == "pr_glob" and not in_repo_subfolder:
        fail(f"{rel}: проектный внутренний навык должен лежать в doc/skills/<repo-name>/")
        errors += 1
    return errors


def check_anthropic(skill_dir: Path, root: Path, place: str) -> int:
    """Проверить пакет формата Anthropic; вернуть число ошибок."""
    rel = skill_dir.relative_to(root)
    errors = 0
    errors += check_concrete_ext_refs(skill_dir / "SKILL.md", rel)
    skill_md = skill_dir / "SKILL.md"
    fm = frontmatter_block(skill_md)
    if not fm:
        fail(f"{rel}: SKILL.md без frontmatter или отсутствует")
        return 1

    fname = flat_value(fm, "name")
    if not fname:
        fail(f"{rel}: поле name не найдено")
        errors += 1
    elif fname != skill_dir.name:
        fail(f"{rel}: name ({fname}) не совпадает с именем каталога ({skill_dir.name})")
        errors += 1
    if not flat_value(fm, "description"):
        fail(f"{rel}: поле description не найдено")
        errors += 1
    if has_top_level_type(fm):
        fail(f"{rel}: верхнеуровневое поле type недопустимо - тип в metadata.type")
        errors += 1

    mtype = metadata_value(fm, "type")
    if not mtype:
        fail(f"{rel}: metadata.type не найден - слаг типа обязателен ({', '.join(VALID_SLUGS)})")
        errors += 1
        return errors
    if mtype not in VALID_SLUGS:
        fail(f"{rel}: metadata.type ({mtype}) невалиден - допустимы: {', '.join(VALID_SLUGS)}")
        errors += 1
        return errors

    prefix_slug = next((slug for prefix, slug in DIR_PREFIX_TO_SLUG.items() if skill_dir.name.startswith(prefix)), "")
    if not prefix_slug:
        target = "pl-" if place == "data/skills" else "pg-"
        fail(f"{rel}: нет типового префикса ({', '.join(DIR_PREFIX_TO_SLUG)}) - переименовать в {target}{skill_dir.name}/")
        errors += 1
        return errors
    if prefix_slug != mtype:
        fail(f"{rel}: префикс имени ({prefix_slug}) не соответствует metadata.type ({mtype})")
        errors += 1

    if mtype == "pr_loc" and place != "data/skills":
        fail(f"{rel}: локальный навык (pl-) должен лежать в data/skills/")
        errors += 1
    if mtype != "pr_loc" and place == "data/skills":
        fail(f"{rel}: в data/skills/ допустимы только локальные навыки (pl-)")
        errors += 1
    return errors


def walk_skills(root: Path) -> tuple[int, int]:
    """Обойти канонические места и проверить все навыки; вернуть (проверено, ошибок)."""
    checked = 0
    errors = 0

    doc_skills = root / "doc" / "skills"
    if doc_skills.is_dir():
        for entry in sorted(doc_skills.iterdir()):
            if entry.name.startswith("_index"):
                continue
            if entry.is_file() and entry.suffix == ".md":
                checked += 1
                errors += check_internal(entry, root, in_repo_subfolder=False)
            elif entry.is_dir() and (entry / "SKILL.md").is_file():
                checked += 1
                errors += check_anthropic(entry, root, place="doc/skills")
            elif entry.is_dir():
                if entry.name == "ext":
                    info("doc/skills/ext - агрегат синхронизации, пропущен (проверяется в репо-источниках)")
                    continue
                for skill_md in sorted(entry.rglob("SKILL.md")):
                    checked += 1
                    errors += check_anthropic(skill_md.parent, root, place="doc/skills")
                for md in sorted(entry.rglob("*.md")):
                    if md.name == "SKILL.md" or "/templates/" in md.as_posix():
                        continue
                    checked += 1
                    errors += check_internal(md, root, in_repo_subfolder=True)

    data_skills = root / "data" / "skills"
    if data_skills.is_dir():
        for entry in sorted(data_skills.iterdir()):
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                checked += 1
                errors += check_anthropic(entry, root, place="data/skills")
            elif entry.is_file() and entry.suffix == ".md":
                fail(f"{entry.relative_to(root)}: внутренний формат в data/skills не используется - только pl-<name>/SKILL.md")
                errors += 1
    return checked, errors


def main() -> int:
    if len(sys.argv) > 2:
        print(f"{stamp()} [!] Использование: {Path(sys.argv[0]).name} [корень-репозитория]", file=sys.stderr)
        return EXIT_USAGE

    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path.cwd().resolve()
    if not (root / "doc" / "skills").is_dir():
        fail(f"каталог навыков не найден: {root / 'doc' / 'skills'}")
        return EXIT_FAIL

    info(f"Проверка полноты навыков: {root}")
    checked, errors = walk_skills(root)
    if not checked:
        info("навыки не найдены")
        return EXIT_OK
    if errors:
        fail(f"проверка не пройдена: проверено - {checked}, ошибок - {errors}")
        return EXIT_FAIL
    info(f"проверка пройдена: проверено - {checked}, ошибок нет")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
