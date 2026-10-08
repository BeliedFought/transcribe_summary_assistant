# Стандарт деплоя Python-проекта как системного инструмента. Версия 4.16.0

Документ описывает общие (OS-agnostic) правила установки Python-проекта как системного CLI-инструмента. Является дополнением к `doc/standards/project_standards.md` и применяется поверх него. Все требования основного стандарта остаются в силе, кроме случаев, явно описанных в данном документе.

OS-специфика (пути к данным, поток установки, команды оболочки) вынесена в overlay-документы:

- `deploy_lin_standards.md` - установка на Linux
- `deploy_win_standards.md` - установка на Windows

При деплое применять этот документ вместе с релевантным overlay.

---

## Оглавление

**01. Условия и сборка:** 01.01 Обязательные условия к проекту - 01.02 Структура pyproject.toml - 01.03 Упаковка non-Python файлов (01.03.01 MANIFEST.in - 01.03.02 package-data в pyproject.toml - 01.03.03 Доступ к data-файлам в коде - 01.03.04 Правила)

**02. Разделение кода и данных:** 02.01 Подмена PROJECT_ROOT в config.py - 02.02 Построение путей от PROJECT_ROOT

**03. Установочные скрипты:** 03.01 Установочные скрипты - общие правила - 03.02 Блок диагностики для ИИ-агента - 03.03 Эталон install.py - 03.04 Эталон update.py

**04. Имя и версия:** 04.01 Версия приложения и миграция конфигурации при обновлении

**05. Правила сопровождения:** 05.01 Точка входа - 05.02 Режим разработчика - 05.03 Удаление - 05.04 Чек-лист перед релизом

**06. Связь и версионирование:** 06.01 Связь с другими документами - 06.02 Версионирование

---

## 01.01. Обязательные условия к проекту

*Обязательно.*

До начала установки проект должен соответствовать следующим требованиям:

1. **Корневой модуль с точкой входа** - функция `main()` в файле (например `main.py` или `cli.py`). Функция должна вызываться через `if __name__ == "__main__": main()` и не содержать побочных эффектов на уровне модуля. Функция `main()` не должна содержать логику напрямую - разобрать аргументы, инициализировать конфигурацию, делегировать выполнение (в соответствии с основным стандартом).
2. **Все импорты через пакеты** - `from src.xxx import ...`. Запрещены хаки с `sys.path`, относительные импорты за пределами пакета, динамическое формирование путей импорта. Импорт-пакет `src` един для обоих режимов (упаковка - раздел 01.02): в режиме разработки код лежит в `src/` репозитория, в установленном - в `site-packages/src/` изолированного venv инструмента.
3. **`__init__.py`** в каждом каталоге, который импортируется как пакет. Пустой файл, без кода инициализации.
4. **Все зависимости зафиксированы** в `requirements.txt` с точными версиями (`==`).

---

## 01.02. Структура pyproject.toml

*Обязательно.*

Файл `pyproject.toml` размещается в корне проекта. Это единственный файл конфигурации сборки.

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "tool-name"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "requests==2.32.3",
]

[project.scripts]
tool-name = "main:main"

[tool.setuptools]
packages = ["src"]
py-modules = ["main"]
```

**Пояснения к секциям:**

- **`[build-system]`** - определяет инструмент сборки и его зависимости. Явное указание гарантирует одинаковое поведение на всех машинах независимо от версии pip/setuptools.
- **`[project.scripts]`** - создает CLI-команду. Формат: `имя_команды = "модуль:функция"`; модуль записывается так, как он импортируется после установки: корневой оркестратор `main` или модуль пакета `src.xxx`. После установки wrapper-скрипт попадает в каталог пользователя. Пример: `tool-name = "main:main"` создаст команду `tool-name`, которая вызывает `main()` из корневого `main.py`.
- **`[tool.setuptools]`** - упаковка плоской структуры основного стандарта: `packages = ["src"]` упаковывает каталог `src/` целиком как импорт-пакет `src`, `py-modules = ["main"]` - корневой оркестратор `main.py`. После установки в site-packages попадают `src/` и `main.py`; импорты `from src.xxx import ...` работают в обоих режимах без изменений кода.
- Имя дистрибутива (`name`) на имена импортов не влияет: это метаданные пакета для pip/uv. Импорт-пакет называется `src` и в репозитории, и в site-packages; коллизия общего имени исключена - инструмент ставится в изолированный venv (`uv tool install`, раздел 05.02).

**Правила:**

- `pyproject.toml.version` - источник метаданных пакета (pip/uv); отображаемая версия приложения - `config.ini [app].version` (раздел 04.01). Синхронность версий - ответственность агента при коммите.
- Имя дистрибутива (`name`) - только строчные латинские буквы, цифры, дефисы. Без подчеркиваний; в имени wheel-файла дефисы нормализуются в подчеркивания (`tool_name-1.0.0-*.whl`).
- Имя CLI-команды (`[project.scripts]`) совпадает с именем дистрибутива: установочные скрипты overlay-стандартов используют одно `TOOL_NAME` для имени команды, дистрибутива и записи `uv tool` (`deploy_lin_standards.md`, 02.03; `deploy_win_standards.md`, 04.04).
- `requires-python` - указывать минимальную версию, с которой реально тестировался проект.
- Версии **runtime-зависимостей** (секция `[project] dependencies`) фиксируются с `==`, аналогично `requirements.txt`. Build-зависимости (`[build-system] requires`) указываются с `>=` - это корректно, правило фиксации версий к ним не применяется.
- Локфайл `uv.lock` коммитится и актуален: перед релизом `uv lock --check` без расхождений (раздел 05.04). Ограничение: `uv tool install` собирает окружение инструмента по `pyproject.toml`, локфайл проекта в установке не участвует - локфайл обеспечивает воспроизводимость пересборки и аудита дерева, а не самой установки; деплой со строгой воспроизводимостью набора пакетов - через `uv sync --frozen` из проекта (применяется в `web_standards.md`)
- `requirements.txt` и `pyproject.toml` должны быть синхронизированы: одинаковые пакеты и версии в обеих файлах. Рекомендуется проверять синхронизацию перед каждым коммитом: сравнить список зависимостей из обоих файлов и убедиться, что каждая строка из `requirements.txt` имеет соответствующую строку в `dependencies` в `pyproject.toml`.

---

## 01.03. Упаковка non-Python файлов

*Опционально - только если проект содержит SQL, шаблоны или иные данные, не являющиеся Python-модулями.*

Если проект содержит SQL-файлы, шаблоны или другие данные, не являющиеся Python-модулями, их нужно явно включить в дистрибутив. По умолчанию setuptools упаковывает только `.py` файлы.

Рекомендуемый подход - рантайм-активы внутри пакета: секция `[tool.setuptools.package-data]` для включения файлов в wheel + `MANIFEST.in` для контроля содержимого sdist.

### 01.03.01. MANIFEST.in

*Обязательно при упаковке non-Python файлов.*

Файл `MANIFEST.in` размещается в корне проекта рядом с `pyproject.toml`. Он определяет, какие дополнительные файлы попадают в sdist (исходный дистрибутив). Без него non-Python файлы будут отсутствовать в sdist, и при установке из него возникнут ошибки.

Пример `MANIFEST.in` для проекта с SQL-файлами:

```
recursive-include src/sql *.sql
recursive-include config *.example
```

**Директивы:**

- `include` - включает файлы по glob-шаблону относительно корня проекта
- `recursive-include dir pattern` - рекурсивно включает файлы из каталога
- `exclude` / `recursive-exclude` - исключает файлы
- `global-include` / `global-exclude` - применяет шаблон ко всему дереву

Подробнее: https://packaging.python.org/en/latest/guides/using-manifest-in/

### 01.03.02. package-data в pyproject.toml

*Обязательно при упаковке non-Python файлов.*

Рантайм-активы, читаемые установленным инструментом (SQL-файлы по `project_standards.md`, раздел 03.02), размещаются внутри импорт-пакета `src`: `src/sql/`. Для проектов с деплоем это размещение перекрывает корневую папку `sql/` из `project_standards.md` (раздел 01.01): в режиме разработки пакет лежит в `src/` репозитория, в установленном режиме - в site-packages изолированного venv, код читает файлы одним и тем же способом.

Секция `[tool.setuptools.package-data]` включает файлы внутри пакета в wheel (при конфигурации через pyproject.toml `include-package-data = true` по умолчанию):

```toml
[tool.setuptools.package-data]
src = [
    "sql/ddl/*.sql",
    "sql/queries/*.sql",
    "sql/dml/*.sql",
    "sql/_index_sql.md",
]
```

Условие попадания файла в wheel (документация setuptools): файл выбран секцией `package-data` или выбран `MANIFEST.in` при `include-package-data = true`, и не исключен `exclude-package-data`.

Секция `[tool.setuptools.data-files]` (файлы вне пакета, относительно префикса установки, например `share/tool-name/`) не используется: после установки из wheel нет поддерживаемого способа надежного получения таких файлов - рекомендация setuptools/PyPA - рантайм-данные внутри пакета.

Шаблоны, используемые установочными скриптами overlay-стандартов (`config/config.ini.example`, `config/translations.json`), остаются в корневой папке `config/`: их копируют скрипты установки и обновления из репозитория или архива, это не рантайм-активы wheel.

### 01.03.03. Доступ к data-файлам в коде

*Обязательно при упаковке non-Python файлов.*

Доступ к активам пакета - через `importlib.resources`; путь одинаков для режима разработки и установленного режима:

```python
from importlib.resources import files

sql_content = (
    files("src")
    .joinpath("sql", "ddl", "create_users.sql")
    .read_text(encoding="utf-8")
)
```

Не собирать пути активов через `sys.prefix`, `__file__` соседних модулей или текущую рабочую директорию.

**Подход:** рантайм-активы установленного инструмента (SQL, DDL, шаблоны запросов) - внутри пакета через `package-data` + `MANIFEST.in`; шаблоны конфигурации - корневая папка `config/`, их устанавливают скрипты overlay-стандартов. Секцию `[tool.setuptools.data-files]` не использовать.

### 01.03.04. Правила

*Обязательно при упаковке non-Python файлов.*

- Data-файлы, которые нужны только в режиме разработки (примеры, тестовые данные) - не упаковывать. Только те, что требуются для работы установленного инструмента
- Проверять доступность data-файлов после `uv tool install .`: содержимое wheel смотреть командой `unzip -l dist/<tool_name>-<version>-*.whl` - файлы должны лежать внутри пути пакета (`src/sql/`)
- Не использовать относительные пути с `..` в `package-data` и `importlib.resources` - поведение зависит от версии setuptools и формата архива
- При добавлении новых типов data-файлов обновлять `MANIFEST.in` и секцию `[tool.setuptools.package-data]` в `pyproject.toml`
- Не использовать `[tool.setuptools.data-files]`: файлы вне пакета после установки из wheel не имеют поддерживаемого способа надежного получения

---

## 02.01. Подмена PROJECT_ROOT в config.py

*Обязательно.*

После установки код лежит в `site-packages/`, а конфиги, логи и секреты должны быть доступны пользователю. Решение - подмена `PROJECT_ROOT` в `src/config.py` в зависимости от режима запуска. В обоих режимах файл лежит в импорт-пакете `src` (`<repo>/src/config.py` или `site-packages/src/config.py`), поэтому `parents[1]` - корень соответствующего дерева.

Эталонная реализация `src/config.py` (раздел 01.04 основного стандарта) не меняется. При подготовке конкретного проекта к установке в `src/config.py` добавляется проверка режима и подмена `PROJECT_ROOT`:

- **Режим разработки** (запуск из репозитория): `PROJECT_ROOT = Path(__file__).resolve().parents[1]` - как в основном стандарте, не меняется.
- **Установленный режим** (пакет установлен через `uv tool install`): `PROJECT_ROOT = <OS-CONFIG-ROOT> / "tool-name"`. Конкретный корень зависит от ОС:
  - Linux: `XDG_CONFIG_HOME / "tool-name"` (по умолчанию `~/.config/tool-name/`) - см. `deploy_lin_standards.md`
  - Windows: `APPDATA / "tool-name"` (обычно `C:\Users\<user>\AppData\Roaming\tool-name\`) - см. `deploy_win_standards.md`

Маркер режима - наличие каталога `.git/` рядом с `src/`. Если каталог существует - это клон репозитория, активируется режим разработки. Если нет (код выполняется из `site-packages/` после установки) - установленный режим.

Достаточно одной проверки `.git/`, без использования `importlib.metadata`:

- При `uv tool install` код выполняется из изолированного venv, где нет `.git/` - установленный режим.
- При запуске из репозитория (независимо от того, установлен ли пакет в системе) `.git/` существует - режим разработки.
- При `uv pip install -e .` код выполняется из репозитория, `.git/` на месте - режим разработки.
- При CI/CD из репозитория `.git/` существует - режим разработки, что корректно для запуска тестов.

Полный пример `src/config.py` для установки - в overlay-документе под целевую ОС (`_lin.md` / `_win.md`), поскольку различается корень установленного режима. Скелет подмены:

```python
import os
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]

if (_repo_root / ".git").exists():
    PROJECT_ROOT: Path = _repo_root
else:
    # корень установленного режима - по ОС (см. overlay _lin.md / _win.md)
    PROJECT_ROOT = Path(os.environ.get("<OS_CONFIG_ENV>", "<OS_CONFIG_DEFAULT>")) / "tool-name"
```

Заменить `tool-name` на фактическое имя инструмента. Вся остальная логика `config.py` (загрузка `.env`, чтение `config.ini`) остается без изменений - она работает с `PROJECT_ROOT`, который уже указывает на нужный каталог.

---

## 02.02. Построение путей от PROJECT_ROOT

*Обязательно.*

Все пути в коде строятся от `PROJECT_ROOT` (как в основном стандарте):

```python
from src.config import PROJECT_ROOT

config_path = PROJECT_ROOT / "config" / "config.ini"
log_dir = PROJECT_ROOT / "log"
env_path = PROJECT_ROOT / ".env"
```

В режиме разработки `PROJECT_ROOT` указывает на корень репозитория. В установленном режиме - на каталог данных пользователя (по ОС). Код, использующий `PROJECT_ROOT / "config" / "config.ini"` и `PROJECT_ROOT / "log"`, работает без изменений в обоих режимах.

**Правила:**

- Не использовать `Path.cwd()` или `os.getcwd()` для определения путей к данным.
- Не хардкодить абсолютные пути.
- Использовать `pathlib.Path` для всех операций с путями.
- При первом запуске в установленном режиме - создавать каталоги через `path.mkdir(parents=True, exist_ok=True)`.

---

## 03.01. Установочные скрипты - общие правила

*Обязательно.*

Установочные скрипты размещаются в `run/deploy/`. Набор скриптов зависит от платформы (см. overlay-документ). Общие правила для всех скриптов:

- Каждый скрипт выполняет только одну задачу, без аргументов командной строки и подкоманд.
- Скрипты не зависят от других модулей проекта - не импортируют из `src/` и не используют логгер.
- Вывод реализован через `print()` как исключение из общего правила.
- Строки вывода не должны начинаться с маркеров уровня в квадратных скобках (`[i]`, `[!]`, `[*]`).
- Каждый скрипт начинается с блока диагностики для ИИ-агента (раздел 03.02).

---

## 03.02. Блок диагностики для ИИ-агента

*Обязательно.*

Каждый скрипт в `run/deploy/` выполняет двойную роль: исполняемый скрипт для пользователя и skill для ИИ-агента. Если пользователь тегает файл без пояснений (например `@run/deploy/install.py`), агент должен самостоятельно диагностировать состояние, выполнить нужные действия и сообщить результат.

Скрипт должен начинаться с блока комментариев-инструкций для ИИ-агента.

**Структура блока:**

1. **Условие активации** - когда ИИ-агент должен выполнять проверку (обычно - пользователь ссылается на файл без пояснений).
2. **Проверка состояния установки** - установлен ли пакет, совпадают ли исходники.
3. **Действия по результатам** - установить, обновить или сообщить об актуальности.

Конкретные шаблоны блоков (с командами под ОС) - в overlay-документах `_lin.md` / `_win.md`.

**Правила для блоков:**

- Список файлов для проверки через `diff` / `fc` должен включать все ключевые модули проекта - `main.py`, `src/config.py`, `src/logger.py` и все файлы из `src/` и `run/`, которые влияют на работу инструмента.
- Команды выносить на отдельные строки - агент (и пользователь) должен иметь возможность скопировать их дословно.
- Заменять `tool-name` на фактическое имя инструмента.
- Не включать в блок логику скрипта - только инструкции по проверке.
- Агент должен принимать решения сам, не спрашивая пользователя о дальнейших шагах.
- Для Windows-специфики: команды помечать явно - агент не имеет прямого доступа к Windows-машине, эти команды выполняет пользователь.

---

## 03.03. Эталон install.py

*Обязательно.*

Эталон кода первичной установки. Платформенные отличия - только в значениях констант (`APP_DIR`, подсказки по оболочке, каталог команды); порядок действий и код процедуры общие для Linux и Windows. Значения констант задает overlay-документ (`_lin.md` / `_win.md`, таблица платформенных подстановок). Скрипт изолирован (раздел 03.01), вывод через `print(..., flush=True)`.

**Порядок действий (первая установка):**

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, не установлен ли уже пакет. Если установлен - сообщить и завершить (для обновления использовать `run/deploy/update.py`).
3. Установить пакет (`uv tool install .`).
4. Создать каталог данных `APP_DIR` с подкаталогами `config/` и `log/`.
5. Скопировать шаблон `config.ini.example` в `config.ini` - только если файл отсутствует.
6. Скопировать `.env.example` в `.env` - только если файл отсутствует; установить права `0600`.
7. Скопировать `translations.json` в каталог данных (всегда из источника установки).
8. Проверить, что команда доступна в PATH.

**Код:**

```python
#!/usr/bin/env python3
# ... блок диагностики из раздела 03.02 ...

import os
import shutil
import subprocess
import sys
from pathlib import Path

# значения APP_DIR и команд - по overlay-документу (lin/win), таблицы подстановок
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
# <OS_CONFIG_ENV> / <OS_CONFIG_DEFAULT> - по overlay-документу (lin/win)
APP_DIR = (
    Path(os.environ.get("<OS_CONFIG_ENV>", "<OS_CONFIG_DEFAULT>")).expanduser()
    / TOOL_NAME
)
# <UV_INSTALL_HINT> / <PATH_HINT> - по overlay-документу (lin/win)
UV_INSTALL_HINT = "<UV_INSTALL_HINT>"
PATH_HINT = "<PATH_HINT>"


def _check_uv() -> None:
    if not shutil.which("uv"):
        print(f"uv не найден. {UV_INSTALL_HINT}", flush=True)
        sys.exit(1)


def _check_pyproject() -> None:
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        print("pyproject.toml не найден в корне проекта", flush=True)
        sys.exit(1)


def _ensure_data_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "config").mkdir(exist_ok=True)
    (APP_DIR / "log").mkdir(exist_ok=True)


def _copy_if_missing(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    if not src.exists():
        print(f"Шаблон не найден: {src}", flush=True)
        return
    shutil.copy2(src, dst)


def _copy_translations() -> None:
    src = PROJECT_ROOT / "config" / "translations.json"
    if not src.exists():
        print(f"Шаблон не найден: {src}", flush=True)
        return
    shutil.copy2(src, APP_DIR / "config" / "translations.json")


def _is_tool_installed() -> bool:
    result = subprocess.run(
        ["uv", "tool", "list"], capture_output=True, text=True, check=False
    )
    return TOOL_NAME in result.stdout


def main() -> None:
    _check_pyproject()
    _check_uv()
    if _is_tool_installed():
        print(f"Пакет '{TOOL_NAME}' уже установлен. Для обновления: python run/deploy/update.py", flush=True)
        return
    try:
        subprocess.run(["uv", "tool", "install", "."], cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки пакета: {e}", flush=True)
        sys.exit(1)
    _ensure_data_dirs()
    _copy_if_missing(
        PROJECT_ROOT / "config" / "config.ini.example",
        APP_DIR / "config" / "config.ini",
    )
    _copy_if_missing(PROJECT_ROOT / ".env.example", APP_DIR / ".env")
    # права 0600 на .env - при создании и после каждой записи (project_standards.md, раздел 05.01)
    env_file = APP_DIR / ".env"
    if env_file.exists():
        env_file.chmod(0o600)
    _copy_translations()
    cmd_path = shutil.which(TOOL_NAME)
    if cmd_path:
        print(f"Команда '{TOOL_NAME}' доступна: {cmd_path}", flush=True)
    else:
        print(f"Команда установлена, но не найдена в PATH. Добавьте {PATH_HINT} в PATH или перезапустите оболочку.", flush=True)


if __name__ == "__main__":
    main()
```

---

## 03.04. Эталон update.py

*Обязательно.*

Эталон кода обновления. Платформенные отличия - только в значениях констант (`APP_DIR`, подсказки по оболочке, каталог команды, источник шаблонов); порядок действий и код процедуры общие для Linux и Windows. Значения констант задает overlay-документ (`_lin.md` / `_win.md`, таблица платформенных подстановок). Скрипт изолирован (раздел 03.01), вывод через `print(..., flush=True)`.

**Порядок действий (обновление):**

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, что пакет установлен. Если не установлен - сообщить и завершить (для установки использовать `run/deploy/install.py`).
3. Создать dev-конфиг `config/config.ini` из `config.ini.example`, если он отсутствует, с подстановкой `name`/`version` из `pyproject.toml` (канон - раздел 04.01, этап 0).
4. Синхронизировать версию между `pyproject.toml`, `config/config.ini` и `config/config.ini.example` по SemVer - привести все три к максимальному значению (канон - раздел 04.01, этап 0). Нечисловые версии (`dev` и т.п.) - пропустить с сообщением.
5. Очистить кэш: `uv cache clean tool-name`. Без этого при неизменной версии в `pyproject.toml` команда `uv tool install . --force` поставит кэшированный wheel вместо пересборки из текущих исходников - изменения кода не попадут в установленный пакет.
6. Переустановить пакет: `uv tool install . --force`.
7. Обновить `translations.json` в каталоге данных (всегда копировать из источника установки).
8. Мигрировать prod-`config.ini` и prod-`.env` по алгоритму раздела 04.01 (сравнение структур, резервные копии, перенос значений).
9. Кратко проверить установку (`uv tool list`, команда в PATH) и сообщить итог.

**Код:**

```python
#!/usr/bin/env python3
# ... блок диагностики из раздела 03.02 ...

import configparser
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# значения APP_DIR и команд - по overlay-документу (lin/win), таблицы подстановок
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
# <OS_CONFIG_ENV> / <OS_CONFIG_DEFAULT> - по overlay-документу (lin/win)
APP_DIR = (
    Path(os.environ.get("<OS_CONFIG_ENV>", "<OS_CONFIG_DEFAULT>")).expanduser()
    / TOOL_NAME
)
# <UV_INSTALL_HINT> / <PATH_HINT> - по overlay-документу (lin/win)
UV_INSTALL_HINT = "<UV_INSTALL_HINT>"
PATH_HINT = "<PATH_HINT>"

_BAK_STAMP = "%Y-%m-%d_%H-%M"
_SECTION_RE = re.compile(r"^\[(.+)\]\s*$")
_INI_KEY_RE = re.compile(r"^([^#;=\s][^=]*?)\s*=(.*)$")
_ENV_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def _check_uv() -> None:
    if not shutil.which("uv"):
        print(f"uv не найден. {UV_INSTALL_HINT}", flush=True)
        sys.exit(1)


def _check_pyproject() -> None:
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        print("pyproject.toml не найден в корне проекта", flush=True)
        sys.exit(1)


def _ensure_data_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "config").mkdir(exist_ok=True)
    (APP_DIR / "log").mkdir(exist_ok=True)


def _copy_translations() -> None:
    src = PROJECT_ROOT / "config" / "translations.json"
    if not src.exists():
        print(f"Шаблон не найден: {src}", flush=True)
        return
    shutil.copy2(src, APP_DIR / "config" / "translations.json")


def _is_tool_installed() -> bool:
    result = subprocess.run(
        ["uv", "tool", "list"], capture_output=True, text=True, check=False
    )
    return TOOL_NAME in result.stdout


def _pyproject_version() -> str:
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "dev"


def _semver_key(value: str) -> tuple[int, ...] | None:
    parts = value.strip().split(".")
    if not parts or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _with_app_values(text: str, name: str, version: str) -> str:
    """Вернуть текст конфига с подставленными app.name и app.version."""
    out: list[str] = []
    section = ""
    for line in text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1)
            out.append(line)
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section == "app":
            key = key_match.group(1).strip()
            if key == "name":
                out.append(f"name = {name}")
                continue
            if key == "version":
                out.append(f"version = {version}")
                continue
        out.append(line)
    return "\n".join(out) + "\n"


def _read_app_info() -> tuple[str, str]:
    parser = configparser.ConfigParser()
    for candidate in (
        PROJECT_ROOT / "config" / "config.ini",
        PROJECT_ROOT / "config" / "config.ini.example",
    ):
        if candidate.exists():
            parser.read(candidate, encoding="utf-8")
            if parser.has_section("app"):
                return (
                    parser.get("app", "name", fallback=TOOL_NAME),
                    parser.get("app", "version", fallback="dev"),
                )
    return TOOL_NAME, "dev"


def _ensure_dev_config() -> None:
    dst = PROJECT_ROOT / "config" / "config.ini"
    src = PROJECT_ROOT / "config" / "config.ini.example"
    if dst.exists() or not src.exists():
        return
    # канон подстановки name/version - deploy_standards.md, раздел 04.01 (этап 0)
    text = src.read_text(encoding="utf-8")
    dst.write_text(
        _with_app_values(text, TOOL_NAME, _pyproject_version()), encoding="utf-8"
    )
    print(f"Создан dev-конфиг: {dst}", flush=True)


def _sync_version() -> None:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    ini_paths = [
        PROJECT_ROOT / "config" / "config.ini",
        PROJECT_ROOT / "config" / "config.ini.example",
    ]
    versions: dict[str, str] = {}
    if pyproject.exists():
        versions["pyproject"] = _pyproject_version()
    for path in ini_paths:
        if path.exists():
            parser = configparser.ConfigParser()
            parser.read(path, encoding="utf-8")
            if parser.has_section("app"):
                versions[str(path)] = parser.get("app", "version", fallback="dev")
    numeric = {key: value for key, value in versions.items() if _semver_key(value) is not None}
    if not numeric:
        print("Версии нечисловые - синхронизация пропущена", flush=True)
        return
    target = max(numeric.values(), key=lambda value: _semver_key(value) or ())
    # привести все три файла к максимальному значению (канон - раздел 04.01, этап 0)
    if pyproject.exists() and versions.get("pyproject") != target:
        text = pyproject.read_text(encoding="utf-8")
        text = re.sub(
            r'^(version\s*=\s*")[^"]+(")',
            rf"\g<1>{target}\g<2>",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        pyproject.write_text(text, encoding="utf-8")
    for path in ini_paths:
        if not path.exists():
            continue
        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")
        name = parser.get("app", "name", fallback=TOOL_NAME)
        path.write_text(
            _with_app_values(path.read_text(encoding="utf-8"), name, target),
            encoding="utf-8",
        )
    print(f"Версия синхронизирована: {target}", flush=True)


def _ini_structure(text: str) -> dict[str, set[str]]:
    structure: dict[str, set[str]] = {}
    section = ""
    for line in text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1)
            structure.setdefault(section, set())
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section:
            structure[section].add(key_match.group(1).strip())
    return structure


def _env_keys(text: str) -> list[str]:
    keys: list[str] = []
    for line in text.splitlines():
        key_match = _ENV_KEY_RE.match(line.strip())
        if key_match:
            keys.append(key_match.group(1))
    return keys


def _rebuild_ini(example_text: str, old_text: str, name: str, version: str) -> str:
    old_values: dict[str, dict[str, str]] = {}
    section = ""
    for line in old_text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1)
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section:
            old_values.setdefault(section, {})[key_match.group(1).strip()] = (
                key_match.group(2).strip()
            )
    out: list[str] = []
    section = ""
    for line in example_text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1)
            out.append(line)
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section:
            key = key_match.group(1).strip()
            if section == "app" and key in ("name", "version"):
                value = name if key == "name" else version
            elif key in old_values.get(section, {}):
                value = old_values[section][key]
            else:
                value = key_match.group(2).strip()
            out.append(f"{key} = {value}")
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def _rebuild_env(example_text: str, old_text: str) -> str:
    old_values: dict[str, str] = {}
    for line in old_text.splitlines():
        key_match = _ENV_KEY_RE.match(line.strip())
        if key_match:
            old_values[key_match.group(1)] = key_match.group(2).strip()
    out: list[str] = []
    for line in example_text.splitlines():
        key_match = _ENV_KEY_RE.match(line.strip())
        if key_match and key_match.group(1) in old_values:
            out.append(f"{key_match.group(1)}={old_values[key_match.group(1)]}")
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def _backup(path: Path) -> Path:
    stamp = datetime.now().strftime(_BAK_STAMP)
    backup = path.with_name(f"{path.name}.bak_{stamp}")
    if backup.exists():
        backup = path.with_name(f"{path.name}.bak_{stamp}-{datetime.now():%S}")
    path.rename(backup)
    return backup


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _migrate_config() -> None:
    prod = APP_DIR / "config" / "config.ini"
    example = PROJECT_ROOT / "config" / "config.ini.example"
    if not example.exists():
        return
    example_text = example.read_text(encoding="utf-8")
    parser = configparser.ConfigParser()
    parser.read_string(example_text)
    name = parser.get("app", "name", fallback=TOOL_NAME)
    version = parser.get("app", "version", fallback="dev")
    if not prod.exists():
        _atomic_write(prod, _with_app_values(example_text, name, version))
        return
    old_text = prod.read_text(encoding="utf-8")
    if _ini_structure(old_text) == _ini_structure(example_text):
        # структуры совпадают - обновить только app.name / app.version (раздел 04.01)
        new_text = _with_app_values(old_text, name, version)
        if new_text != old_text:
            _atomic_write(prod, new_text)
        return
    backup = _backup(prod)
    # алгоритм миграции - deploy_standards.md, раздел 04.01
    _atomic_write(prod, _rebuild_ini(example_text, old_text, name, version))
    print(f"Конфиг мигрирован, резервная копия: {backup.name}", flush=True)


def _migrate_env() -> None:
    prod = APP_DIR / ".env"
    example = PROJECT_ROOT / ".env.example"
    if not example.exists():
        return
    example_text = example.read_text(encoding="utf-8")
    if not prod.exists():
        _atomic_write(prod, example_text)
        prod.chmod(0o600)
        return
    old_text = prod.read_text(encoding="utf-8")
    old_keys = _env_keys(old_text)
    example_keys = _env_keys(example_text)
    if old_keys == example_keys:
        return
    backup = _backup(prod)
    # алгоритм миграции - deploy_standards.md, раздел 04.01
    _atomic_write(prod, _rebuild_env(example_text, old_text))
    prod.chmod(0o600)
    added = [key for key in example_keys if key not in old_keys]
    removed = [key for key in old_keys if key not in example_keys]
    print(f".env мигрирован, резервная копия: {backup.name}", flush=True)
    if added:
        print(f"Новые ключи: {', '.join(added)}", flush=True)
    if removed:
        print(f"Ключи только в старом файле: {', '.join(removed)}", flush=True)


def _verify_install() -> None:
    result = subprocess.run(
        ["uv", "tool", "list"], capture_output=True, text=True, check=False
    )
    if TOOL_NAME not in result.stdout:
        print(f"Пакет {TOOL_NAME} не найден после установки", flush=True)
        sys.exit(1)
    if not shutil.which(TOOL_NAME):
        print(f"Команда не найдена в PATH. Добавьте {PATH_HINT} в PATH", flush=True)


def main() -> None:
    name, version = _read_app_info()
    print(f"{name} v{version}", flush=True)
    _check_pyproject()
    _check_uv()
    if not _is_tool_installed():
        print(f"Пакет {TOOL_NAME} не установлен. Для установки: python run/deploy/install.py", flush=True)
        return
    _ensure_dev_config()
    _sync_version()
    subprocess.run(["uv", "cache", "clean", TOOL_NAME], check=False)
    subprocess.run(
        ["uv", "tool", "install", ".", "--force"], cwd=PROJECT_ROOT, check=True
    )
    _ensure_data_dirs()
    _copy_translations()
    _migrate_config()
    _migrate_env()
    _verify_install()
    print("Обновление завершено", flush=True)


if __name__ == "__main__":
    main()
```

Новый `config.ini` и `.env` собираются по тексту example с подстановкой значений (порядок секций, ключей и комментарии шаблона сохраняются); `ConfigParser.write()` не используется как единственный способ записи.

---

## 04.01. Версия приложения и миграция конфигурации при обновлении

*Обязательно.*

Название и версия приложения для отображения пользователю (в логах, консоли) хранятся в `config/config.ini` в секции `[app]` (параметры `name` и `version`). Это единый источник для всех режимов - разработки и установленного.

Версия в `pyproject.toml` (поле `version`) предназначена только для метаданных пакета (pip/uv) и не используется для отображения. Синхронность версий в `pyproject.toml` и `config.ini` - ответственность агента; агент предлагает обновить обе при коммите (см. основной стандарт, раздел 01.03).

```python
from src.config import APP_NAME, APP_VERSION
```

Установочный скрипт `update.py` при обновлении выполняет единый алгоритм миграции. **Канон алгоритма - этот раздел**; overlay-документы (`deploy_lin_standards.md`, раздел 03.05; `deploy_win_standards.md`, раздел 05.05) содержат только платформенные пути, источник шаблонов и команды.

**Этап 0 - синхронизация версии в репозитории (только прямой деплой из репозитория).** Версии в `config/config.ini` (параметр `version` секции `[app]`), `pyproject.toml` (поле `version`) и `config/config.ini.example` сравниваются по SemVer; максимальное значение записывается во все три файла. Нечисловые версии (`dev` и т.п.) - пропустить с сообщением. Точка входа алгоритма миграции далее - dev-конфиг `config/config.ini`. При его отсутствии - сначала создать из `config/config.ini.example`, проставив `name`/`version` из `pyproject.toml`. При деплое через архив этап отсутствует: версия зафиксирована в wheel на машине сборки.

**Этап 1 - миграция prod-`config.ini`.** Источник новой структуры - `config.ini.example`.

Сравнение: только набор секций и ключей (значения пользователя на решение о миграции не влияют).

Если структуры совпадают:
- без переименования обновить только `app.name` и `app.version` из источника, если отличаются

Если структуры отличаются:
1. Переименовать текущий файл в `config.ini.bak_YYYY-MM-DD_HH-MM` (история накапливается; при коллизии имени - суффикс с секундами)
2. Создать новый `config.ini` по тексту example (порядок секций/ключей и комментарии шаблона сохраняются)
3. Для совпадающих ключей подставить значения из старого файла
4. Для новых ключей (есть в example, нет в старом) - значение из example
5. `app.name` и `app.version` всегда из источника, не из старого файла
6. Ключи, которые были только в старом конфиге и отсутствуют в example - не переносить (остаются в `.bak`)
7. В консоль: имя резервной копии, перенесенные и добавленные ключи (без секретов)

Если prod-конфига еще нет - создать его копированием example (значения `name`/`version` - из example).

**Этап 2 - миграция prod-`.env`.** Источник новой структуры - `.env.example`.

Сравнение: только набор ключей (значения/секреты не сравниваются и не печатаются).

Если наборы ключей совпадают - файл не трогать.

Если отличаются:
1. Переименовать текущий файл в `.env.bak_YYYY-MM-DD_HH-MM`
2. Создать новый `.env` по ключам example
3. Для совпадающих ключей перенести старые значения
4. Для новых ключей - значение из example (часто пустое)
5. Ключи, которые были только в старом `.env` - не переносить (остаются в `.bak`); сообщить список имен ключей без значений

Если prod-`.env` еще нет - скопировать example.

**Этап 3 - `translations.json`.** Обновлять всегда копированием из источника установки.

**Правила:**

- Пользовательские значения совпадающих ключей при миграции сохраняются; новая структура всегда берется из example
- Резервные копии не удаляются скриптом
- Запись нового файла - по шаблону example с подстановкой значений, без «голого» `ConfigParser.write()` как единственного способа сборки
- Критичные файлы (`config.ini`, `.env`) записывать атомарно: во временный файл, затем `rename` поверх целевого (`project_standards.md`, раздел 03.01) - прерванная запись не оставляет поврежденный файл
- Сравнение только по множеству ключей: переименование ключа = старый остается в `.bak`, новый берется из example; правка только комментариев в example миграцию не запускает

---

## 05.01. Точка входа

*Обязательно.*

Функция `main()` не должна содержать логику напрямую. Ее задача - разобрать аргументы, инициализировать конфигурацию и делегировать выполнение:

```python
from src.config import PROJECT_ROOT, APP_NAME, APP_VERSION
from src.localization import t
from pathlib import Path

from src.logger import get_logger

def main() -> None:
    logger = get_logger(Path(__file__).stem, log_dir=PROJECT_ROOT / "log")
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))
    args = parse_args()
    init_config()
    run(args)


if __name__ == "__main__":
    main()
```

---

## 05.02. Режим разработчика

*Опционально - для отладки без установки.*

Для отладки без установки использовать `uv` в editable-режиме. Требуется активный venv. Команда активации venv зависит от ОС (см. overlay-документ):

```bash
# активация venv (Linux: source .venv/bin/activate; Windows: .venv\Scripts\activate)
uv pip install -e .
```

Устанавливает пакет в "editable" режиме - изменения в коде отражаются сразу без переустановки. Код выполняется из репозитория (`.git/` на месте), поэтому `PROJECT_ROOT` указывает на корень репозитория (режим разработки).

**Разница между режимами `uv`:**

- `uv tool install .` - изолированная установка CLI-команды для повседневного использования. Пакет попадает в отдельный venv, команда доступна глобально.
- `uv pip install -e .` - установка в текущий venv для разработки. Требует активированный venv, изменения в коде применяются сразу.

---

## 05.03. Удаление

*Опционально.*

```bash
uv tool uninstall tool-name
```

Каталог данных пользователя при удалении пакета не затрагивается - пользователь удаляет его вручную при необходимости. Конкретный путь каталога данных - по ОС (см. overlay-документ).

---

## 05.04. Чек-лист перед релизом

*Обязательно.*

Общие пункты (OS-специфичные пункты - в overlay-документе под целевую ОС):

1. Все зависимости указаны в `pyproject.toml` с точными версиями (`==`).
2. `requirements.txt` и `pyproject.toml` синхронизированы (одинаковые пакеты и версии).
3. Версия в `pyproject.toml` обновлена.
4. Секция `[app]` в `config.ini` содержит корректные `name` и `version`.
5. `__init__.py` есть во всех импортируемых пакетах.
6. Подмена `PROJECT_ROOT` в `config.py` использует корректное имя инструмента.
7. Установочные скрипты используют корректное имя инструмента (`TOOL_NAME`).
8. `.gitignore` содержит артефакты сборки (`*.egg-info/`, `dist/`, `build/`).
9. Data-файлы (SQL, шаблоны) доступны после установки.
10. Локфайл актуален: `uv lock --check` выполняется без расхождений.

---

## 06.01. Связь с другими документами

| Документ | Связь |
|----------|-------|
| `doc/standards/project_standards.md` | Основной стандарт; настоящий документ применяется поверх него (структура проекта, конфигурация, код) |
| `deploy_lin_standards.md` / `deploy_win_standards.md` | OS-overlay: платформенные пути, установочные скрипты и команды; применяются вместе с настоящим ядром |
| `deploy_docker_standards.md` | Смежный стандарт: инфраструктура Docker (сеть, тома, публикация портов); применяется при контейнерном развертывании вместо настоящего ядра |
| `web_standards.md` | Смежный стандарт: веб-приложения (FastAPI + nginx); настоящее ядро к веб-приложениям не применяется (граница - `web_standards.md`, раздел 12.02) |
| `doc/standards/_index_standards.md` | Реестр пакета стандартов и карта маршрутизации |

---

## 06.02. Версионирование

Версионирование пакета стандартов - единое для всех документов пакета. Политика версионирования, реестр и карта маршрутизации - в `doc/standards/_index_standards.md`. Bump версии пакета - только по явному запросу пользователя (см. _index_standards.md).
