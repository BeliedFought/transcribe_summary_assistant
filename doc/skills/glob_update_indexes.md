---
id: glob_update_indexes
description: Актуализирует локальные индексы репозитория - индекс навыков _index_skills_repo.md из состава doc/skills/ и индекс спецификаций doc/specs/_index_specs.md из состава doc/specs/. Применять при запросах обновить локальные индексы, актуализировать список навыков или спецификаций
auto_apply: true
version: 1.1.1
---

# Навык: Актуализация локальных индексов репозитория

> Глобальный навык (префикс `glob_`), раздается во все репозитории. Работает только по локальному репозиторию, кросс-репо ничего не знает. В хабе `project_standards` не применяется: сводный индекс навыков `_index_skills_hub.md` ведет `hub_sync_indexes`, а `doc/specs/_index_specs.md` хаба - эталонный шаблон, который не перезаписывается.

## Описание

Навык перечитывает локальные каталоги и пересобирает два индекса репозитория: `doc/skills/_index_skills_repo.md` - точку входа в каталог навыков (корневые `doc/skills/*.md`: общие `glob_*` и собственные проектные) и `doc/specs/_index_specs.md` - реестр корневых файлов спецификаций со сводкой подпапок `doc/specs/<project>/`. Индексные файлы (`_index_*.md`) в перечень навыков не включаются. Навык правит только эти два индекса и не трогает сами навыки, спецификации, стандарты и их индексы.

## Когда использовать

- Пользователь просит обновить/актуализировать локальные индексы репозитория (навыков или спецификаций)
- Добавлен, удален или переименован навык в корне `doc/skills/` либо файл в `doc/specs/`
- Изменен frontmatter навыка (id, description, auto_apply, version)
- Пользователь тегнул `@doc/skills/_index_skills_repo.md` или `@doc/specs/_index_specs.md` без конкретной задачи
- Триггер-слова: обнови индексы, актуализируй список навыков, актуализируй индекс спецификаций

## Предусловия

- Запуск из корня репозитория (не из хаба `project_standards`)
- Существует хотя бы одна из папок: `doc/skills/`, `doc/specs/`

## Инструкция

1. Запустить скрипт из раздела "Скрипт" из корня репозитория.
2. Скрипт пересобирает два локальных индекса:
   - `doc/skills/_index_skills_repo.md`: корневые `doc/skills/*.md` (кроме `_index_*.md`), извлекает frontmatter, формирует реестр (класс, автоприменение, версия) с кратким описанием;
   - `doc/specs/_index_specs.md`: корневые файлы `doc/specs/` (кроме самого индекса и `.gitkeep`) с типом каждого файла и сводка подпапок `doc/specs/<project>/` (перечень файлов подпапки).
3. Скрипт сохраняет ранее заполненные значения колонки «Назначение» индекса спецификаций; новым файлам и подпапкам ставится `-`. После запуска заполнить назначения вручную (для `ui_spec.html` указать SemVer макета по `console_ui_standards.md`).
4. В хабе `project_standards` скрипт ничего не меняет и сообщает причину.
5. Вывод передать пользователю: что попало в каждый индекс, пути к обновленным файлам.

## Скрипт

```python
#!/usr/bin/env python3
import re
from pathlib import Path

SKILLS_DIR = Path("doc/skills")
SKILLS_INDEX = SKILLS_DIR / "_index_skills_repo.md"
SPECS_DIR = Path("doc/specs")
SPECS_INDEX = SPECS_DIR / "_index_specs.md"


def frontmatter(path: Path) -> dict:
    meta = {"id": None, "description": None, "auto_apply": None, "version": None}
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


def rebuild_skills_index(root: Path) -> None:
    if not SKILLS_DIR.exists():
        print(f"Пропуск индекса навыков: не найдена папка {SKILLS_DIR}")
        return
    skills = [p for p in sorted(SKILLS_DIR.glob("*.md")) if not p.name.startswith("_index")]
    lines = [
        f"# Индекс навыков репозитория {root.name}",
        "",
        "Локальный индекс навыков этого репозитория. Формируется автоматически навыком `glob_update_indexes` из состава `doc/skills/`. Перечисляет общие (`glob_*`) и проектные навыки репо. Порядок принятия решений агента при отсутствии нормы - `project_standards.md`, раздел 07.06.",
        "",
        "| Навык | Класс | Автоприменение | Версия | Назначение |",
        "|-------|-------|----------------|--------|-----------|",
    ]
    for p in skills:
        m = frontmatter(p)
        cls = "общий" if p.name.startswith("glob_") else "проектный"
        ident = m["id"] or p.stem
        desc = (m["description"] or "").split(". ")[0]
        lines.append(f"| `{ident}` | {cls} | {m['auto_apply'] or '-'} | {m['version'] or '-'} | {desc} |")
    lines.append("")
    SKILLS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"Обновлен {SKILLS_INDEX} - навыков: {len(skills)}")
    for p in skills:
        print(f"  {p.name}")


def rebuild_specs_index(root: Path) -> None:
    if not SPECS_DIR.exists():
        print(f"Пропуск индекса спецификаций: не найдена папка {SPECS_DIR}")
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
        "Реестр файлов спецификаций этого репозитория. Формируется автоматически навыком `glob_update_indexes` из состава `doc/specs/`: корневые файлы и сводка подпапок проектов. Порядок принятия решений агента при отсутствии нормы - `project_standards.md`, раздел 07.06.",
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
    SPECS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"Обновлен {SPECS_INDEX} - корневых файлов: {len(root_files)}, подпапок: {len(subdirs)}")
    for p in root_files:
        print(f"  {p.name}")
    for d in subdirs:
        print(f"  {d.name}/")


def main() -> None:
    root = Path.cwd().resolve()
    if root.name == "project_standards":
        print("Пропуск: в хабе сводный индекс _index_skills_hub.md ведет hub_sync_indexes, "
              "а doc/specs/_index_specs.md - эталонный шаблон и не перезаписывается")
        return
    rebuild_skills_index(root)
    rebuild_specs_index(root)


if __name__ == "__main__":
    main()
```

## Критерии завершения

- `doc/skills/_index_skills_repo.md` соответствует фактическому составу корневых навыков; индексные файлы (`_index_*.md`) в перечень не включены
- `doc/specs/_index_specs.md` соответствует фактическому составу `doc/specs/`: корневые файлы с типами и сводка подпапок
- Назначения новых файлов и подпапок спецификаций заполнены вручную после пересборки
- В хабе навык не изменяет файлы и сообщает об этом
- Пользователю выдан отчет по обоим индексам

## Примеры

1. Пользователь: «обнови индексы» -> агент запускает скрипт, пересобирает `_index_skills_repo.md` и `_index_specs.md`, выдает отчет.
2. В `doc/specs/` добавлена спецификация `spec_export.md` -> агент перегенерирует индекс спецификаций, в реестре появляется строка с типом «Спецификация задачи», назначение заполняется вручную.

## Ограничения

- Не запускать в хабе `project_standards`: сводный индекс навыков ведет `hub_sync_indexes`, а `doc/specs/_index_specs.md` в хабе - эталонный шаблон
- Редактировать только `doc/skills/_index_skills_repo.md` и `doc/specs/_index_specs.md`; не менять сами навыки, спецификации, стандарты и их индексы
- Кросс-репо синхронизации не выполняет - только локальный репозиторий
