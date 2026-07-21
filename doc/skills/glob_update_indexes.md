---
id: glob_update_indexes
description: Актуализирует локальный индекс навыков репозитория `_index_skills_repo.md` из фактического состава `doc/skills/` этого репо. Применять при запросах обновить локальный индекс навыков, актуализировать список навыков репозитория
auto_apply: true
version: 1.0.0
---

# Навык: Актуализация локального индекса навыков репозитория

> Глобальный навык (префикс `glob_`), раздаётся во все репозитории. Работает только по локальному репозиторию, кросс-репо ничего не знает. В хабе `project_standards` не применяется - там сводный индекс `_index_skills_hub.md` ведёт `hub_sync_indexes`.

## Описание

Навык перечитывает корневые навыки `doc/skills/*.md` текущего репозитория (общие `glob_*` и собственные проектные навыки) и пересобирает локальный индекс `doc/skills/_index_skills_repo.md` - точку входа в каталог навыков этого репо. Индексные файлы (`_index_*.md`) в перечень не включаются. Навык правит только `_index_skills_repo.md` и не трогает сами навыки, стандарты и их индекс.

## Когда использовать

- Пользователь просит обновить/актуализировать локальный индекс навыков репозитория
- Добавлен, удалён или переименован навык в корне `doc/skills/` репозитория
- Изменён frontmatter навыка (id, description, auto_apply, version)
- Пользователь тегнул `@doc/skills/_index_skills_repo.md` без конкретной задачи
- Триггер-слова: обнови индекс навыков, актуализируй список навыков, go

## Предусловия

- Запуск из корня репозитория (не из хаба `project_standards`)
- Существует папка `doc/skills/` с навыками

## Инструкция

1. Запустить скрипт из раздела "Скрипт" из корня репозитория.
2. Скрипт собирает корневые `doc/skills/*.md` (кроме `_index_*.md`), извлекает frontmatter и пересобирает `doc/skills/_index_skills_repo.md`: заголовок, реестр навыков (класс, автоприменение, версия), краткое описание.
3. В хабе `project_standards` скрипт ничего не делает и сообщает, что сводный индекс ведёт `hub_sync_indexes`.
4. Вывод передать пользователю: какие навыки попали в индекс, путь к обновлённому файлу.

## Скрипт

```python
#!/usr/bin/env python3
import re
from datetime import date
from pathlib import Path

SKILLS_DIR = Path("doc/skills")
INDEX_FILE = SKILLS_DIR / "_index_skills_repo.md"


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


def main() -> None:
    root = Path.cwd().resolve()
    if root.name == "project_standards":
        print("Пропуск: в хабе сводный индекс _index_skills_hub.md ведёт hub_sync_indexes")
        return
    if not SKILLS_DIR.exists():
        print(f"Ошибка: не найдена папка {SKILLS_DIR}")
        return

    skills = [p for p in sorted(SKILLS_DIR.glob("*.md")) if not p.name.startswith("_index")]

    lines = [
        f"# Индекс навыков репозитория {root.name}. {date.today().isoformat()}",
        "",
        "Локальный индекс навыков этого репозитория. Формируется автоматически навыком `glob_update_indexes` из состава `doc/skills/`. Перечисляет общие (`glob_*`) и проектные навыки репо.",
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

    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Обновлён {INDEX_FILE} - навыков: {len(skills)}")
    for p in skills:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
```

## Критерии завершения

- `doc/skills/_index_skills_repo.md` соответствует фактическому составу корневых навыков репозитория
- Индексные файлы (`_index_*.md`) в перечень не включены
- В хабе навык не изменяет файлы и сообщает об этом
- Пользователю выдан отчёт со списком навыков и путём к файлу

## Примеры

1. Пользователь: «обнови индекс навыков» -> агент запускает скрипт, пересобирает `_index_skills_repo.md`, выдаёт список навыков.
2. В репозиторий добавлен проектный навык `db_migrate.md` -> агент перегенерирует индекс, в реестре появляется строка `db_migrate` класса «проектный».

## Ограничения

- Не запускать в хабе `project_standards` (там сводный индекс ведёт `hub_sync_indexes`)
- Редактировать только `doc/skills/_index_skills_repo.md`; не менять сами навыки, стандарты и их индексы
- Кросс-репо синхронизации не выполняет - только локальный репозиторий
