#!/usr/bin/env python3
"""Пересборка локальных индексов репозитория: doc/skills/_index_skills_repo.md
и doc/specs/_index_specs.md по канону index_nav_standards.md (скелет индекса).

Использование (запуск из корня репозитория):
    update_indexes.py

Скрипт формирует полный канонический скелет: интро с указателем на 07.06,
обязательность применения, реестры, карту маршрутизации (первичное заполнение)
и раздел автоактуализации. В хабе project_standards скрипт ничего не меняет
и сообщает причину.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = Path("doc/skills")
SKILLS_INDEX = SKILLS_DIR / "_index_skills_repo.md"
SPECS_DIR = Path("doc/specs")
SPECS_INDEX = SPECS_DIR / "_index_specs.md"

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


def frontmatter(path: Path) -> dict:
    meta: dict[str, str | None] = {"id": None, "description": None, "auto_apply": None, "version": None}
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
    meta = {"name": "", "description": "", "version": ""}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    fm = text[3:end] if end > 0 else ""
    for key in ("name", "description"):
        m = re.search(rf"^{key}:\s*(.+)$", fm, re.MULTILINE)
        if m:
            meta[key] = m.group(1).strip()
    v = re.search(r"^\s+version:\s*(\S+)", fm, re.MULTILINE)
    if v:
        meta["version"] = v.group(1)
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
        "Локальный индекс навыков этого репозитория. Точка входа в каталог `doc/skills/`: перечисляет общие (`glob_*`), проектные (`pg_*` в корне и в подпапке `<repo-name>/`) навыки репо и каталоги формата Anthropic. Агент загружает индекс, а не каталог целиком, и по карте маршрутизации находит нужные навыки. Формируется автоматически навыком `glob-update-indexes`. Порядок принятия решений агентом при отсутствии нормы - `project_standards.md`, раздел 07.06.",
        "",
        "---",
        "",
        SKILLS_APPLY,
        "",
        "---",
        "",
        "## Реестр навыков",
        "",
        "| Навык | Класс | Автоприменение | Версия | Назначение |",
        "|-------|-------|----------------|--------|-----------|",
    ]
    map_rows = []
    for p in skills + sub_skills:
        m = frontmatter(p)
        cls = "общий" if p.name.startswith("glob_") else "проектный"
        ident = m["id"] or p.stem
        desc = m["description"] or ""
        lines.append(f"| `{ident}` | {cls} | {m['auto_apply'] or '-'} | {m['version'] or '-'} | {first_clause(desc)} |")
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
            "| Навык (каталог) | Класс | Версия | Назначение |",
            "|-----------------|-------|--------|-----------|",
        ]
        for d in anthropic:
            m = anthropic_meta(d)
            name = d.parent.relative_to(SKILLS_DIR).as_posix()
            cls = "общий" if name.startswith("glob-") else "проектный"
            lines.append(f"| `{name}` | {cls} | {m['version'] or '-'} | {first_clause(m['description'])} |")
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
        warn("Пропуск: в хабе сводный индекс _index_skills_hub.md ведет hub-sync-indexes, "
             "а doc/specs/_index_specs.md - эталонный шаблон и не перезаписывается")
        return EXIT_OK
    rebuild_skills_index(root)
    rebuild_specs_index(root)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
