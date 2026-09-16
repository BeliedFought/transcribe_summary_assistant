#!/usr/bin/env python3
"""Пересборка локальных индексов репозитория: doc/skills/_index_skills_repo.md,
doc/specs/_index_specs.md и data/skills/_index_skills_pl.md
по канону index_nav_standards.md (скелет индекса).

Использование (запуск из корня репозитория):
    update_indexes.py

Скрипт формирует полный канонический скелет: интро с указателем на 07.06,
обязательность применения, реестры, карту маршрутизации (первичное заполнение)
и раздел автоактуализации. Индекс локальных навыков собирается при наличии
data/skills/ в любом репозитории, включая хаб: в хабе project_standards два
прочих индекса не трогаются (причина выводится в лог).
"""

import re
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = Path("doc/skills")
SKILLS_INDEX = SKILLS_DIR / "_index_skills_repo.md"
SPECS_DIR = Path("doc/specs")
SPECS_INDEX = SPECS_DIR / "_index_specs.md"
LOCAL_SKILLS_DIR = Path("data/skills")
LOCAL_SKILLS_INDEX = LOCAL_SKILLS_DIR / "_index_skills_pl.md"

EXIT_OK = 0

SKILLS_APPLY = """## Обязательность применения

Тегание этого файла означает обязательное применение релевантных навыков, а не просто ознакомление. Агент:

1. Определяет релевантные навыки по карте маршрутизации
2. Загружает указанные файлы навыков и выполняет их инструкции
3. Применяет правила навыков при наличии соответствующей задачи, независимо от явного тегирования"""

SKILLS_MAP_NOTE = """Карта связывает тип задачи с навыком. Агент открывает указанный навык и выполняет инструкцию. Темы - первичные, из описаний навыков: доработать формулировки по канону `index_nav_standards.md` (раздел 04) - от лица задачи пользователя, с синонимами-триггерами.

| Тема задачи | Навык |
|-------------|-------|"""

SKILLS_AUTO = """## Автоактуализация индекса

При любом изменении состава `doc/skills/` (добавление, удаление, переименование, изменение frontmatter навыка) пересобрать индекс навыком `glob-update-indexes`; заполнить назначения и доработать карту маршрутизации по канону `index_nav_standards.md` (разделы 03.03, 04). Вывести отчет: что добавлено, изменено, удалено.
"""

SPECS_APPLY = """## Обязательность применения

Тегание этого файла означает обязательное использование индекса при работе со спецификациями. Агент:

1. Определяет релевантные файлы по реестру и карте маршрутизации
2. Открывает только релевантные файлы, а не каталог целиком
3. При любом изменении состава `doc/specs/` обновляет этот индекс

Индекс применяется при любой работе со спецификациями независимо от явного тегирования."""

SPECS_MAP_TOPICS = {
    "init_spec.txt": "Исходные требования проекта, свободная форма",
    "final_spec.md": "Итоговая спецификация компактного проекта",
    "ui_spec.html": "UI-эталон: карта меню, кадры, клавиши, макет лога",
    "overrides.md": "Проектные оверрайды стандарта",
}

SPECS_MAP_NOTE = """Карта связывает тип задачи с файлом спецификаций. Агент находит в индексе нужный файл и читает его.

| Тема задачи | Файл |
|-------------|------|"""

SPECS_AUTO = """## Автоактуализация индекса

При любом изменении состава `doc/specs/` (добавление, удаление, переименование, изменение назначения файла) пересобрать индекс навыком `glob-update-indexes`; заполнить назначения (для `ui_spec.html` указать SemVer макета) и дополнить карту маршрутизации по канону `index_nav_standards.md` (разделы 03.03, 04). Вывести отчет: что добавлено, изменено, удалено.
"""

PL_APPLY = """## Обязательность применения

Тегание этого файла означает обязательное применение релевантных локальных навыков, а не просто ознакомление. Агент:

1. Определяет релевантные навыки по карте маршрутизации
2. Загружает указанные файлы навыков и выполняет их инструкции
3. Применяет правила навыков при наличии соответствующей задачи, независимо от явного тегирования"""

PL_AUTO = """## Автоактуализация индекса

При любом изменении состава `data/skills/` (добавление, удаление, переименование, изменение frontmatter навыка) пересобрать индекс навыком `glob-update-indexes`; заполнить назначения и доработать карту маршрутизации по канону `index_nav_standards.md` (разделы 03.03, 04). Вывести отчет: что добавлено, изменено, удалено.
"""


def now() -> str:
    """Метка времени в формате строгого режима логгера (04.04.01)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def info(message: str) -> None:
    print(f"{now()} [i] {message}")


def warn(message: str) -> None:
    print(f"{now()} [*] {message}")


def first_clause(description: str) -> str:
    """Первое предложение описания - первичная тема строки карты маршрутизации."""
    return (description or "").split(". ")[0]


TYPE_CLASS = {
    "hub_glob": "общий",
    "pr_glob": "проектный",
    "hub_loc": "хаб",
    "pr_loc": "локальный",
}

PREFIX_TYPE = {
    "hub": "hub_loc",
    "glob": "hub_glob",
    "pg": "pr_glob",
    "pl": "pr_loc",
}


def type_slug(name: str, declared: str | None) -> str | None:
    """Слаг типа навыка: из frontmatter, иначе по префиксу имени."""
    if declared:
        return declared
    parts = re.split(r"[_\-]", name)
    return PREFIX_TYPE.get(parts[0]) if parts else None


def class_of(name: str, declared: str | None) -> str:
    """Класс навыка по слагу типа."""
    return TYPE_CLASS.get(type_slug(name, declared) or "", "проектный")


def area_value(category: str | None, category_name: str | None) -> str:
    """Значение колонки области применения: название (слаг) или прочерк."""
    if category and category_name:
        return f"{category_name} (`{category}`)"
    return "-"


def frontmatter(path: Path) -> dict:
    meta: dict[str, str | None] = {
        "id": None, "description": None, "auto_apply": None, "version": None, "type": None,
        "category": None, "category_name": None,
    }
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        fm = text[3:end] if end > 0 else ""
        for key in meta:
            m = re.search(rf"^{key}:\s*(.+)$", fm, re.MULTILINE)
            if m:
                meta[key] = m.group(1).strip()
    return meta


def spec_type(name: str) -> str:
    known = {
        "init_spec.txt": "Требования",
        "final_spec.md": "Спецификация",
        "ui_spec.html": "UI-эталон",
        "overrides.md": "Оверрайды",
    }
    if name in known:
        return known[name]
    if re.fullmatch(r"spec_.+\.md", name):
        return "Спецификация задачи или модуля"
    return "Прочее"


def old_purposes(path: Path) -> dict:
    purposes = {}
    if not path.exists():
        return purposes
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if m:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            purposes[m.group(1)] = cells[-1] if len(cells) >= 2 else "-"
    return purposes


def anthropic_meta(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta = {"name": "", "description": "", "version": "", "type": "", "category": "", "category_name": ""}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    fm = text[3:end] if end > 0 else ""
    for key in ("name", "description"):
        m = re.search(rf"^{key}:\s*(.+)$", fm, re.MULTILINE)
        if m:
            meta[key] = m.group(1).strip()
    for key in ("version", "type", "category", "category_name"):
        m = re.search(rf"^\s+{key}:\s*(\S.*)$", fm, re.MULTILINE)
        if m:
            meta[key] = m.group(1).strip()
    return meta


def rebuild_skills_index(root: Path) -> None:
    if not SKILLS_DIR.exists():
        warn(f"Пропуск индекса навыков: не найдена папка {SKILLS_DIR}")
        return
    skills = [p for p in sorted(SKILLS_DIR.glob("*.md")) if not p.name.startswith("_index")]
    sub_skills = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if d.is_dir() and not (d / "SKILL.md").is_file() and not d.name.startswith("_index"):
            sub_skills.extend(sorted(d.glob("pg_*.md")))
    lines = [
        f"# Индекс навыков репозитория {root.name}",
        "",
        "Локальный индекс навыков этого репозитория. Точка входа в каталог `doc/skills/`: перечисляет общие (`glob-*`, `glob_*`) и проектные (`pg-*` в корне, `pg_*.md` в подпапке `<repo-name>/`) навыки обоих форматов. Агент загружает индекс, а не каталог целиком, и по карте маршрутизации находит нужные навыки. Формируется автоматически навыком `glob-update-indexes`. Порядок принятия решений агентом при отсутствии нормы - `project_standards.md`, раздел 07.06.",
        "",
        "---",
        "",
        SKILLS_APPLY,
        "",
        "---",
        "",
        "## Реестр навыков",
        "",
        "| Навык | Класс | Область | Автоприменение | Версия | Назначение |",
        "|-------|-------|---------|----------------|--------|-----------|",
    ]
    map_rows = []
    for p in skills + sub_skills:
        m = frontmatter(p)
        cls = class_of(p.stem, m["type"])
        ident = m["id"] or p.stem
        desc = m["description"] or ""
        lines.append(f"| `{ident}` | {cls} | {area_value(m['category'], m['category_name'])} | {m['auto_apply'] or '-'} | {m['version'] or '-'} | {first_clause(desc)} |")
        map_rows.append(f"| {first_clause(desc)} | `{ident}` |")
    lines.append("")
    anthropic = [
        d
        for d in sorted(SKILLS_DIR.rglob("SKILL.md"))
        if "/templates/" not in d.as_posix()
    ]
    if anthropic:
        lines += [
            "## Навыки формата Anthropic Agent Skills (SKILL.md)",
            "",
            "| Навык (каталог) | Класс | Область | Версия | Назначение |",
            "|-----------------|-------|---------|--------|-----------|",
        ]
        for d in anthropic:
            m = anthropic_meta(d)
            name = d.parent.relative_to(SKILLS_DIR).as_posix()
            cls = class_of(name, m["type"])
            lines.append(f"| `{name}` | {cls} | {area_value(m['category'], m['category_name'])} | {m['version'] or '-'} | {first_clause(m['description'])} |")
            map_rows.append(f"| {first_clause(m['description'])} | `{name}` |")
        lines.append("")
    lines += [
        "---",
        "",
        "## Карта маршрутизации",
        "",
        SKILLS_MAP_NOTE,
        *map_rows,
        "",
        "---",
        "",
        SKILLS_AUTO,
    ]
    SKILLS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    info(f"Обновлен {SKILLS_INDEX} - навыков: {len(skills) + len(sub_skills)}, каталогов SKILL.md - {len(anthropic)}")
    for p in skills:
        info(f"- {p.name}")


def rebuild_local_skills_index(root: Path) -> None:
    if not LOCAL_SKILLS_DIR.exists():
        warn(f"Пропуск индекса локальных навыков: не найдена папка {LOCAL_SKILLS_DIR}")
        return
    purposes = old_purposes(LOCAL_SKILLS_INDEX)
    flat = [p for p in sorted(LOCAL_SKILLS_DIR.glob("*.md")) if not p.name.startswith("_index")]
    dirs = [d for d in sorted(LOCAL_SKILLS_DIR.iterdir()) if d.is_dir() and (d / "SKILL.md").is_file()]
    lines = [
        f"# Индекс локальных навыков репозитория {root.name}",
        "",
        "Точка входа в каталог `data/skills/`: перечисляет локальные навыки (слаг `pr_loc`) - плоские файлы и каталоги формата Anthropic. Локальные навыки в сводные индексы `_index_skills_hub.md` и `_index_skills_repo.md` не входят - они отражены здесь. Агент загружает индекс, а не каталог целиком, и по карте маршрутизации находит нужные навыки. Формируется автоматически навыком `glob-update-indexes`. Порядок принятия решений агентом при отсутствии нормы - `project_standards.md`, раздел 07.06.",
        "",
        "---",
        "",
        PL_APPLY,
        "",
        "---",
        "",
        "## Реестр навыков",
        "",
        "| Навык | Класс | Область | Автоприменение | Версия | Назначение |",
        "|-------|-------|---------|----------------|--------|-----------|",
    ]
    map_rows = []
    for p in flat:
        m = frontmatter(p)
        ident = m["id"] or p.stem
        desc = m["description"] or ""
        purpose = first_clause(desc) if desc else purposes.get(ident, "-")
        lines.append(f"| `{ident}` | локальный | {area_value(m['category'], m['category_name'])} | {m['auto_apply'] or '-'} | {m['version'] or '-'} | {purpose} |")
        map_rows.append(f"| {purpose} | `{ident}` |")
    lines.append("")
    if dirs:
        lines += [
            "## Навыки формата Anthropic Agent Skills (SKILL.md)",
            "",
            "| Навык (каталог) | Класс | Область | Версия | Назначение |",
            "|-----------------|-------|---------|--------|-----------|",
        ]
        for d in dirs:
            m = anthropic_meta(d / "SKILL.md")
            purpose = first_clause(m["description"]) or purposes.get(d.name, "-")
            lines.append(f"| `{d.name}` | локальный | {area_value(m['category'], m['category_name'])} | {m['version'] or '-'} | {purpose} |")
            map_rows.append(f"| {purpose} | `{d.name}` |")
        lines.append("")
    lines += [
        "---",
        "",
        "## Карта маршрутизации",
        "",
        SKILLS_MAP_NOTE,
        *map_rows,
        "",
        "---",
        "",
        PL_AUTO,
    ]
    LOCAL_SKILLS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    info(f"Обновлен {LOCAL_SKILLS_INDEX} - навыков: {len(flat)}, каталогов SKILL.md - {len(dirs)}")
    for p in flat:
        info(f"- {p.name}")
    for d in dirs:
        info(f"- {d.name}/")


def spec_map_row(name: str) -> str | None:
    if name in SPECS_MAP_TOPICS:
        return f"| {SPECS_MAP_TOPICS[name]} | `{name}` |"
    if re.fullmatch(r"spec_.+\.md", name):
        return f"| Спецификация задачи или модуля `{name}` | `{name}` |"
    return None


def rebuild_specs_index(root: Path) -> None:
    if not SPECS_DIR.exists():
        warn(f"Пропуск индекса спецификаций: не найдена папка {SPECS_DIR}")
        return
    purposes = old_purposes(SPECS_INDEX)
    root_files = sorted(
        p for p in SPECS_DIR.iterdir()
        if p.is_file() and p.name not in ("_index_specs.md", ".gitkeep")
    )
    subdirs = sorted(d for d in SPECS_DIR.iterdir() if d.is_dir())
    lines = [
        f"# Индекс спецификаций репозитория {root.name}",
        "",
        "Точка входа в каталог спецификаций этого репозитория. Агент загружает индекс, а не каталог целиком, и по реестру и карте маршрутизации открывает только релевантные файлы. Формируется автоматически навыком `glob-update-indexes` из состава `doc/specs/`: корневые файлы и сводка подпапок проектов. Порядок принятия решений агентом при отсутствии нормы - `project_standards.md`, раздел 07.06.",
        "",
        "---",
        "",
        SPECS_APPLY,
        "",
        "---",
        "",
        "## Реестр корневых файлов",
        "",
        "| Файл | Тип | Назначение |",
        "|------|-----|-----------|",
    ]
    for p in root_files:
        lines.append(f"| `{p.name}` | {spec_type(p.name)} | {purposes.get(p.name, '-')} |")
    lines.append("")
    if subdirs:
        lines += [
            "## Подпапки проектов",
            "",
            "| Папка | Файлы | Назначение |",
            "|-------|-------|-----------|",
        ]
        for d in subdirs:
            names = [f.name for f in sorted(d.iterdir()) if f.is_file()]
            key = f"{d.name}/"
            lines.append(f"| `{key}` | {', '.join(names) or '-'} | {purposes.get(key, '-')} |")
        lines.append("")
    map_rows = [row for row in (spec_map_row(p.name) for p in root_files) if row]
    lines += [
        "---",
        "",
        "## Карта маршрутизации",
        "",
        SPECS_MAP_NOTE,
        *map_rows,
        "",
        "---",
        "",
        SPECS_AUTO,
    ]
    SPECS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    info(f"Обновлен {SPECS_INDEX} - корневых файлов: {len(root_files)}, подпапок: {len(subdirs)}")
    for p in root_files:
        info(f"- {p.name}")
    for d in subdirs:
        info(f"- {d.name}/")


def main() -> int:
    root = Path.cwd().resolve()
    if root.name == "project_standards":
        warn("Хаб project_standards: сводный индекс _index_skills_hub.md ведет hub-sync-indexes, "
             "doc/specs/_index_specs.md - эталонный шаблон; пересобирается только "
             "data/skills/_index_skills_pl.md")
    else:
        rebuild_skills_index(root)
        rebuild_specs_index(root)
    rebuild_local_skills_index(root)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
