---
id: sync_standards
description: Синхронизирует файлы из doc/standards/ и doc/skills/ текущего проекта во все соседние проекты. Применять при запросах обновить, скопировать или синхронизировать стандарты и навыки в соседние проекты
auto_apply: false
---

# Навык: Синхронизация стандартов и навыков проекта

## Описание

Копирует все файлы из папок `doc/standards/` и `doc/skills/` текущего проекта в одноименные папки соседних проектов (находящихся на одном уровне вложенности в родительском каталоге). По итогам выдает отчет: какие проекты затронуты и как изменились версии каждого скопированного файла.

## Когда использовать

- Пользователь просит обновить, скопировать или синхронизировать стандарты и/или навыки во все остальные проекты
- Пользователь просит разнести актуальные версии `doc/standards/*.md` и `doc/skills/*.md` по соседним репозиториям
- Пользователь тегает навык через `@doc/skills/sync_standards.md`

## Предусловия

- Текущая рабочая директория - корень проекта-источника
- В текущем проекте присутствует хотя бы одна из папок: `doc/standards/` или `doc/skills/` с файлами `.md`
- Соседние проекты расположены в том же родительском каталоге

## Инструкция по применению

1. Запустить скрипт синхронизации из корня текущего проекта - либо сохранив его во временный файл, либо выполнив код напрямую.
2. Скрипт обрабатывает две исходные папки: `doc/standards/` и `doc/skills/`. В каждом проекте-приемнике гарантируется наличие целевых папок `doc/standards/` и `doc/skills/` (создаются при отсутствии). Все файлы из источника копируются в приемник: существующие замещаются актуальной версией, отсутствующие создаются.
3. Вывод скрипта передать пользователю в чат как отчет: список затронутых проектов и переход версий по каждому файлу в обеих папках.

## Скрипт синхронизации (Python)

```python
#!/usr/bin/env python3
import shutil
import re
from pathlib import Path

SOURCE_DIRS = ["doc/standards", "doc/skills"]


def get_version(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for _ in range(5):
                line = f.readline()
                if not line:
                    break
                match = re.search(r"Версия\s+(\d+\.\d+(?:\.\d+)?)", line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return "нет версии"


def collect_source_files(current_project: Path) -> dict[Path, list[Path]]:
    sources: dict[Path, list[Path]] = {}
    for rel in SOURCE_DIRS:
        source_dir = current_project / rel
        if source_dir.exists():
            files = sorted(source_dir.glob("*.md"))
            if files:
                sources[source_dir] = files
    return sources


def main() -> None:
    current_project = Path.cwd().resolve()
    sources = collect_source_files(current_project)

    if not sources:
        print("Ошибка: Не найдены исходные папки doc/standards/ и doc/skills/ с файлами .md")
        return

    print(f"Исходные файлы ({current_project.name}):")
    for source_dir, files in sources.items():
        rel = source_dir.relative_to(current_project)
        print(f"  [{rel}]")
        for sf in files:
            v = get_version(sf)
            print(f"    {sf.name} - {v}")
    print()

    parent_dir = current_project.parent
    print("Отчет о синхронизации:")
    print("-" * 50)

    found_any = False

    for item in sorted(parent_dir.iterdir()):
        if not item.is_dir() or item == current_project:
            continue

        if not (item / "doc").exists():
            continue

        project_touched = False
        project_lines: list[str] = []

        for source_dir, files in sources.items():
            rel = source_dir.relative_to(current_project)
            target_dir = item / rel
            if not target_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)

            for sf in files:
                target_file = target_dir / sf.name
                if not target_file.exists():
                    project_touched = True
                    new_version = get_version(sf)
                    try:
                        shutil.copy2(sf, target_file)
                        project_lines.append(f"  [{rel}] {sf.name} - создан ({new_version})")
                    except Exception as e:
                        project_lines.append(f"  [{rel}] {sf.name} - Ошибка создания: {e}")
                    continue
                project_touched = True
                old_version = get_version(target_file)
                new_version = get_version(sf)
                try:
                    shutil.copy2(sf, target_file)
                    project_lines.append(f"  [{rel}] {sf.name} - {old_version} -> {new_version}")
                except Exception as e:
                    project_lines.append(f"  [{rel}] {sf.name} - Ошибка копирования: {e}")

        if project_touched:
            found_any = True
            print(f"Проект: {item.name}")
            for line in project_lines:
                print(line)
            print()

    if not found_any:
        print("Соседние проекты с целевыми папками doc/standards/ или doc/skills/ не найдены.")


if __name__ == "__main__":
    main()
```

## Критерии завершения

- Скрипт выполнен без ошибок, либо пользователь уведомлен о причине сбоя
- В чат выдан отчет с затронутыми проектами: переход версий замещенных файлов и список созданных файлов
- Соседние каталоги без папки `doc/` пропущены (не считаются проектами)

## Примеры

1. Пользователь: «синхронизируй стандарты и навыки во все проекты» -> агент запускает скрипт, выдает отчет по каждому соседнему проекту с переходом версий файлов из обеих папок.
2. Пользователь: «обнови стандарты везде» -> то же действие, после выполнения агент кратко резюмирует сколько проектов и файлов обновлено.

## Ограничения

- Копировать только из папок `doc/standards/` и `doc/skills/`, никакие другие каталоги не затрагивать
- Замещать существующие файлы и создавать отсутствующие - итоговый набор файлов в приемнике совпадает с источником
- Обрабатывать только соседние каталоги с папкой `doc/` (проекты); прочие каталоги пропускать
- Не запускать скрипт не из корня проекта-источника
- Не модифицировать содержимое самих файлов - побайтовое копирование через `shutil.copy2`
