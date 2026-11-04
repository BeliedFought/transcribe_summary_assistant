#!/usr/bin/env python3
"""Completeness check: all repository skills against the standard requirements.

Compares skills of both formats in all canonical storage locations with the
requirements of skill_anthropic_standards.md and skill_anthropic_standards.md:
required frontmatter fields, a valid type slug, application area category
(slug and name from the closed reference, the second name segment
matches the slug, fields come as a pair), prefix conformance
of the name to type and location (for local data/skills/ skills - both formats,
the prefix is optional), no references to concrete skills of other
repositories (ext/<repo-name>/ paths instead of placeholders), no
Cyrillic placeholders in angle and square brackets.
Changes nothing - report only.

Usage:
    check_all_skills.py [repo-root]
"""

import re
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
    FLAT_PREFIX_TO_SLUG,
    VALID_SLUGS,
    fail,
    file_text,
    flat_value,
    frontmatter_block,
    has_top_level_type,
    info,
    is_index_name,
    is_prefix_optional,
    metadata_value,
    name_category,
    stamp,
)

FLAT_SLUG_TO_LOCATION = {
    "hub_loc": "корень doc/skills/",
    "hub_glob": "корень doc/skills/",
    "pr_glob": "doc/skills/<repo-name>/",
}
CONCRETE_EXT_RE = re.compile(r"ext/(?!<)(?!\{)[A-Za-z0-9_][A-Za-z0-9_-]*")
CYRILLIC_PLACEHOLDER_RE = re.compile(
    r"<[^>]*[А-Яа-яЁё][^>]*>"  # angle brackets: <repo-name>, <dir-name>
    r"|\[[^\[\]]*[А-Яа-яЁё][^\[\]]*\](?!\s*[(:\[])"  # square brackets: [marker], [marker]; not a markdown link
)


def check_category(fm: str, name: str, prefix: str, anthropic: bool, rel: Path) -> int:
    """Check the application area category against the closed reference and the name.

    The category is optional; when present - both fields, slug and name from the
    reference, the slug matches the second name segment. Without a category the second
    name segment must not match a reference slug (unambiguous parsing).
    """
    if anthropic:
        category = metadata_value(fm, "category")
        category_name = metadata_value(fm, "category_name")
    else:
        category = flat_value(fm, "category")
        category_name = flat_value(fm, "category_name")
    if not category and not category_name:
        if prefix and name_category(name, prefix) in CATEGORY_NAMES:
            fail(f"{rel}: категория не задана, но второй сегмент имени совпадает со слагом "
                 f"справочника ({name_category(name, prefix)}) - указать category / category_name или переименовать")
            return 1
        return 0
    if not category or not category_name:
        fail(f"{rel}: category и category_name заполняются только парой")
        return 1
    errors = 0
    if category not in CATEGORY_NAMES:
        fail(f"{rel}: категория ({category}) не из справочника - допустимы: {', '.join(CATEGORY_NAMES)}")
        errors += 1
    elif category_name not in (CATEGORY_NAMES[category], CATEGORY_NAMES_EN[category]):
        fail(f"{rel}: category_name ({category_name}) не соответствует справочнику для {category} "
             f"({CATEGORY_NAMES_EN[category]} / {CATEGORY_NAMES[category]})")
        errors += 1
    if prefix:
        segment = name_category(name, prefix)
        if segment != category:
            fail(f"{rel}: второй сегмент имени ({segment}) не совпадает с категорией ({category})")
            errors += 1
    return errors


def check_concrete_ext_refs(path: Path, rel: Path) -> int:
    """Forbid references to concrete skills of other repositories (ext/<repo-name>/ paths)."""
    errors = 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    for match in CONCRETE_EXT_RE.finditer(text):
        fail(f"{rel}: упоминание конкретного навыка чужого репозитория ({match.group(0)}...) - заменить плейсхолдерами (<repo-name>, <name>)")
        errors += 1
    for match in CYRILLIC_PLACEHOLDER_RE.finditer(text):
        fail(f"{rel}: кириллический плейсхолдер ({match.group(0)}) - только латиница (<repo-name>, <name>, <dir-name>, [repo-root])")
        errors += 1
    return errors


def check_internal(path: Path, root: Path, in_repo_subfolder: bool, place: str = "doc/skills") -> int:
    """Check a plain-format flat skill; return the number of errors."""
    rel = path.relative_to(root)
    errors = 0
    errors += check_concrete_ext_refs(path, rel)
    fm = frontmatter_block(file_text(path))
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

    if ftype == "pr_loc" and place != "data/skills":
        fail(f"{rel}: локальный навык (pr_loc) должен лежать в data/skills/")
        errors += 1
        return errors
    if ftype != "pr_loc" and place == "data/skills":
        fail(f"{rel}: в data/skills/ допустимы только локальные навыки (pr_loc)")
        errors += 1
        return errors

    prefix = next((p for p in FLAT_PREFIX_TO_SLUG if path.name.startswith(p)), "")
    prefix_slug = FLAT_PREFIX_TO_SLUG.get(prefix, "")
    if not prefix_slug:
        if not is_prefix_optional(ftype):  # for local skills (pr_loc) the prefix is optional
            fail(f"{rel}: нет типового префикса (hub_, glob_, pg_, pl_) - переименовать в pg_{path.stem}")
            errors += 1
            return errors
    elif prefix_slug != ftype:
        fail(f"{rel}: префикс имени ({prefix_slug}) не соответствует type ({ftype})")
        errors += 1

    errors += check_category(fm, path.name, prefix, anthropic=False, rel=rel)

    if ftype in ("hub_loc", "hub_glob") and in_repo_subfolder:
        fail(f"{rel}: навык типа {ftype} должен лежать в корне doc/skills/")
        errors += 1
    if ftype == "pr_glob" and not in_repo_subfolder:
        fail(f"{rel}: проектный внутренний навык должен лежать в doc/skills/<repo-name>/")
        errors += 1
    return errors


def check_anthropic(skill_dir: Path, root: Path, place: str) -> int:
    """Check an Anthropic-format package; return the number of errors."""
    rel = skill_dir.relative_to(root)
    errors = 0
    errors += check_concrete_ext_refs(skill_dir / "SKILL.md", rel)
    skill_md = skill_dir / "SKILL.md"
    fm = frontmatter_block(file_text(skill_md))
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

    prefix = next((p for p in DIR_PREFIX_TO_SLUG if skill_dir.name.startswith(p)), "")
    prefix_slug = DIR_PREFIX_TO_SLUG.get(prefix, "")
    if not prefix_slug:
        if not is_prefix_optional(mtype):  # for local skills (pr_loc) the prefix is optional
            fail(f"{rel}: нет типового префикса ({', '.join(DIR_PREFIX_TO_SLUG)}) - переименовать в pg-{skill_dir.name}/")
            errors += 1
            return errors
    elif prefix_slug != mtype:
        fail(f"{rel}: префикс имени ({prefix_slug}) не соответствует metadata.type ({mtype})")
        errors += 1

    errors += check_category(fm, skill_dir.name, prefix, anthropic=True, rel=rel)

    if mtype == "pr_loc" and place != "data/skills":
        fail(f"{rel}: локальный навык (pl-) должен лежать в data/skills/")
        errors += 1
    if mtype != "pr_loc" and place == "data/skills":
        fail(f"{rel}: в data/skills/ допустимы только локальные навыки (pl-)")
        errors += 1
    return errors


def walk_skills(root: Path) -> tuple[int, int]:
    """Walk the canonical locations and check every skill; return (checked, errors)."""
    checked = 0
    errors = 0

    doc_skills = root / "doc" / "skills"
    if doc_skills.is_dir():
        for entry in sorted(doc_skills.iterdir()):
            if is_index_name(entry.name):
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
                    if md.name == "SKILL.md" or "/templates/" in md.as_posix() or is_index_name(md.name):
                        continue
                    checked += 1
                    errors += check_internal(md, root, in_repo_subfolder=True)

    data_skills = root / "data" / "skills"
    if data_skills.is_dir():
        for entry in sorted(data_skills.iterdir()):
            if is_index_name(entry.name):
                continue
            if entry.is_dir() and (entry / "SKILL.md").is_file():
                checked += 1
                errors += check_anthropic(entry, root, place="data/skills")
            elif entry.is_file() and entry.suffix == ".md":
                checked += 1
                errors += check_internal(entry, root, in_repo_subfolder=False, place="data/skills")
    return checked, errors


def main() -> int:
    if len(sys.argv) > 2:
        print(f"{stamp()} [!] Использование: {Path(sys.argv[0]).name} [repo-root]", file=sys.stderr)
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
