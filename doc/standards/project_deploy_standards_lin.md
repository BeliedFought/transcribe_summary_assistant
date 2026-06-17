# Требования к установке Python-проекта как системного инструмента (Linux). Версия 2.11.0. 2026-06-14

Документ является дополнением к `doc/standards/project_standards.md` и применяется поверх него для проектов, которые планируется устанавливать как системные инструменты. Все требования основного стандарта остаются в силе, кроме случаев, явно описанных в данном документе.

---

## 1. Обязательные условия к проекту

До начала установки проект должен соответствовать следующим требованиям:

1. **Корневой модуль с точкой входа** - функция `main()` в файле (например `main.py` или `cli.py`). Функция должна вызываться через `if __name__ == "__main__": main()` и не содержать побочных эффектов на уровне модуля. Функция `main()` не должна содержать логику напрямую - разобрать аргументы, инициализировать конфигурацию, делегировать выполнение (в соответствии с основным стандартом).
2. **Все импорты через пакеты** - `from src.xxx import ...`. Запрещены хаки с `sys.path`, относительные импорты за пределами пакета, динамическое формирование путей импорта.
3. **`__init__.py`** в каждом каталоге, который импортируется как пакет. Пустой файл, без кода инициализации.
4. **Все зависимости зафиксированы** в `requirements.txt` с точными версиями (`==`).

---

## 2. Структура pyproject.toml

Файл `pyproject.toml` размещается в корне проекта. Это единственный файл конфигурации сборки.

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "tool-name"
version = "1.0.0"
requires-python = ">=3.14"
dependencies = [
    "requests==2.32.3",
]

[project.scripts]
command = "module:function"

[tool.setuptools]
py-modules = ["main"]

[tool.setuptools.packages.find]
include = ["src*"]
```

**Пояснения к секциям:**

- **`[build-system]`** - определяет инструмент сборки и его зависимости. Явное указание гарантирует одинаковое поведение на всех машинах независимо от версии pip/setuptools.
- **`[project.scripts]`** - создает CLI-команду. Формат: `имя_команды = "путь.до.модуля:функция"`. После установки wrapper-скрипт попадает в `~/.local/bin/`. Пример: `ghupd = "main:main"` создаст команду `ghupd`, которая вызывает `main.main()`.
- **`py-modules`** - для файлов в корне проекта (не внутри пакета). Без этого `main.py` не попадет в wheel. Если точка входа внутри пакета - секция не нужна.
- **`[tool.setuptools.packages.find]`** - указывает, какие каталоги являются пакетами. `include = ["src*"]` включает `src` и все его подкаталоги.

**Правила:**

- Поле `version` в `pyproject.toml` - единый источник правды о версии. Не дублировать версию в коде.
- Имя пакета (`name`) - только строчные латинские буквы, цифры, дефисы. Без подчеркиваний.
- `requires-python` - указывать минимальную версию, с которой реально тестировался проект.
- Версии **runtime-зависимостей** (секция `[project] dependencies`) фиксируются с `==`, аналогично `requirements.txt`. Build-зависимости (`[build-system] requires`) указываются с `>=` - это корректно, правило фиксации версий к ним не применяется.
- `requirements.txt` и `pyproject.toml` должны быть синхронизированы: одинаковые пакеты и версии в обеих файлах. Рекомендуется проверять синхронизацию перед каждым коммитом: сравнить список зависимостей из обоих файлов и убедиться, что каждая строка из `requirements.txt` имеет соответствующую строку в `dependencies` в `pyproject.toml`.

### 2.1. Упаковка non-Python файлов

Если проект содержит SQL-файлы, шаблоны или другие данные, не являющиеся Python-модулями, их нужно явно включить в дистрибутив. По умолчанию setuptools упаковывает только `.py` файлы.

Рекомендуемый подход - `MANIFEST.in` для контроля содержимого sdist + `[tool.setuptools.data-files]` для размещения файлов при установке.

#### 2.1.1. MANIFEST.in

Файл `MANIFEST.in` размещается в корне проекта рядом с `pyproject.toml`. Он определяет, какие дополнительные файлы попадают в sdist (исходный дистрибутив). Без него non-Python файлы будут отсутствовать в sdist, и при установке из него возникнут ошибки.

Пример `MANIFEST.in` для проекта с SQL-файлами:

```
include sql/*.sql
recursive-include config *.example
```

**Директивы:**

- `include` - включает файлы по glob-шаблону относительно корня проекта
- `recursive-include dir pattern` - рекурсивно включает файлы из каталога
- `exclude` / `recursive-exclude` - исключает файлы
- `global-include` / `global-exclude` - применяет шаблон ко всему дереву

Подробнее: https://packaging.python.org/en/latest/guides/using-manifest-in/

#### 2.1.2. data-files в pyproject.toml

Секция `[tool.setuptools.data-files]` указывает, куда файлы будут установлены относительно `prefix` (обычно `~/.local/`). Это работает и для wheel, и для sdist.

```toml
[tool.setuptools.data-files]
"share/tool-name/sql" = ["sql/*.sql"]
"share/tool-name/config" = ["config/config.ini.example"]
```

После установки через `uv tool install` файлы размещаются внутри изолированного venv. Доступ к ним в коде - через `sys.prefix` (см. раздел 2.1.3):
- `{sys.prefix}/share/tool-name/sql/query.sql`
- `{sys.prefix}/share/tool-name/config/config.ini.example`

При установке через `uv tool install` изолированный venv находится в `~/.local/share/uv/tools/tool-name/`. Путь `sys.prefix` внутри этого venv указывает на корень venv, поэтому `data-files` размещаются по пути `~/.local/share/uv/tools/tool-name/share/tool-name/`.

#### 2.1.3. Доступ к data-файлам в коде

Для файлов, установленных через `data-files`, использовать `sys.prefix` для определения базового пути:

```python
import sys
from pathlib import Path

data_dir = Path(sys.prefix) / "share" / "tool-name"
sql_content = (data_dir / "sql" / "query.sql").read_text(encoding="utf-8")
```

Альтернатива для файлов внутри пакета (внутри `src/`):

```toml
[tool.setuptools.package-data]
src = ["templates/*.sql"]
```

В этом случае доступ через `importlib.resources`:

```python
from importlib.resources import files

sql_content = files("src").joinpath("templates/query.sql").read_text(encoding="utf-8")
```

**Рекомендация:** отдавать предпочтение `data-files` + `MANIFEST.in` для файлов вне пакета (SQL, конфиги-шаблоны) и `package-data` для файлов внутри пакета.

#### 2.1.4. Правила

- Data-файлы, которые нужны только в режиме разработки (примеры, тестовые данные) - не упаковывать. Только те, что требуются для работы установленного инструмента.
- Проверять доступность data-файлов после `uv tool install .` - содержимое wheel можно посмотреть командой `uv tool dir tool-name`.
- Не использовать относительные пути с `..` в `package-data` и `importlib.resources` - поведение зависит от версии setuptools и формата архива.
- При добавлении новых типов data-файлов обновлять `MANIFEST.in` и соответствующую секцию в `pyproject.toml`.

---

## 3. Разделение кода и данных

После установки код лежит в `site-packages/`, а конфиги, логи и секреты должны быть доступны пользователю. Решение - подмена `PROJECT_ROOT` в `src/config.py` в зависимости от режима запуска.

### 3.1. Подмена PROJECT_ROOT в config.py

Шаблон `templates/src/config.py` из основного стандарта не меняется. При подготовке конкретного проекта к установке в `src/config.py` добавляется проверка режима и подмена `PROJECT_ROOT`:

- **Режим разработки** (запуск из репозитория): `PROJECT_ROOT = Path(__file__).resolve().parents[1]` - как в основном стандарте, не меняется.
- **Установленный режим** (пакет установлен через `uv tool install`): `PROJECT_ROOT = XDG_CONFIG_HOME / "tool-name"` (по умолчанию `~/.config/tool-name/`).

Маркер режима - наличие каталога `.git/` рядом с `src/`. Если каталог существует - это клон репозитория, активируется режим разработки. Если нет (код выполняется из `site-packages/` после установки) - установленный режим.

Достаточно одной проверки `.git/`, без использования `importlib.metadata`:

- При `uv tool install` код выполняется из изолированного venv в `~/.local/share/uv/tools/tool-name/`, где нет `.git/` - установленный режим.
- При запуске из репозитория (независимо от того, установлен ли пакет в системе) `.git/` существует - режим разработки.
- При `uv pip install -e .` код выполняется из репозитория, `.git/` на месте - режим разработки.
- При CI/CD из репозитория `.git/` существует - режим разработки, что корректно для запуска тестов.

Это покрывает все сценарии:
- запуск из репозитория без установки (`.git` есть) - разработка
- запуск из репозитория при установленном в системе пакете (`.git` есть) - разработка
- `uv pip install -e .` (`.git` есть) - разработка
- `uv tool install .` (`.git` нет) - установленный режим

Полный пример `src/config.py` для установки:

```python
"""
Общий модуль загрузки конфигурации проекта.

Загружает config/config.ini и .env относительно PROJECT_ROOT.
В режиме разработки PROJECT_ROOT - корень репозитория.
В установленном режиме - ~/.config/tool-name/.

Использование:
    from src.config import config, PROJECT_ROOT, APP_NAME, APP_VERSION
    db_server = config.get("db", "server")
    api_key = config.get("api", "key")  # значение из .env
    output_dir = Path(config.get("paths", "output_folder"))  # пути - всегда через Path()
"""

import configparser
import os
from pathlib import Path

from dotenv import load_dotenv

_repo_root = Path(__file__).resolve().parents[1]

if (_repo_root / ".git").exists():
    PROJECT_ROOT: Path = _repo_root
else:
    PROJECT_ROOT = (
        # expandhome() нужен только для дефолта "~/.config";
        # если XDG_CONFIG_HOME задана, путь уже абсолютный
        Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
        / "tool-name"
    )

_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)

config = configparser.ConfigParser()
_config_file = PROJECT_ROOT / "config" / "config.ini"
if _config_file.exists():
    config.read(_config_file, encoding="utf-8")

APP_NAME: str = config.get("app", "name", fallback="tool-name")
APP_VERSION: str = config.get("app", "version", fallback="dev")
```

Заменить `"tool-name"` на фактическое имя инструмента. Вся остальная логика `config.py` (загрузка `.env`, чтение `config.ini`) остается без изменений - она работает с `PROJECT_ROOT`, который уже указывает на нужный каталог.

### 3.2. Построение путей от PROJECT_ROOT

Все пути в коде строятся от `PROJECT_ROOT` (как в основном стандарте):

```python
from src.config import PROJECT_ROOT

config_path = PROJECT_ROOT / "config" / "config.ini"
log_dir = PROJECT_ROOT / "log"
env_path = PROJECT_ROOT / ".env"
```

В режиме разработки `PROJECT_ROOT` указывает на корень репозитория. В установленном режиме `PROJECT_ROOT` указывает на `~/.config/tool-name/`. Код, использующий `PROJECT_ROOT / "config" / "config.ini"` и `PROJECT_ROOT / "log"`, работает без изменений в обоих режимах.

**Правила:**

- Не использовать `Path.cwd()` или `os.getcwd()` для определения путей к данным.
- Не хардкодить абсолютные пути.
- Использовать `pathlib.Path` для всех операций с путями.
- При первом запуске в установленном режиме - создавать каталоги через `path.mkdir(parents=True, exist_ok=True)`.

---

## 4. Установочные скрипты

Скрипты размещаются в `run/deploy/`:

| Скрипт | Назначение |
|--------|------------|
| `run/deploy/install.py` | Первичная установка инструмента |
| `run/deploy/update.py` | Обновление установленного инструмента |

Каждый скрипт выполняет только одну задачу, без аргументов командной строки и подкоманд.

Скрипты не зависят от других модулей проекта - не импортируют из `src/` и не используют логгер. Вывод реализован через `print()` как исключение из общего правила. Строки вывода не должны начинаться с маркеров уровня в квадратных скобках (`[i]`, `[!]`, `[*]`).

### 4.1. Блок диагностики для ИИ-агента

Каждый скрипт в `run/deploy/` выполняет двойную роль: исполняемый скрипт для пользователя и skill для ИИ-агента. Если пользователь тегает файл без пояснений (например, `@run/deploy/install.py`), агент должен самостоятельно диагностировать состояние, выполнить нужные действия и сообщить результат.

Скрипт должен начинаться с блока комментариев-инструкций для ИИ-агента. Блок описывает проверку состояния и действия по результатам.

**Структура блока:**

1. **Условие активации** - когда ИИ-агент должен выполнять проверку (обычно - пользователь ссылается на файл без пояснений).
2. **Проверка состояния установки** - установлен ли пакет, совпадают ли исходники.
3. **Действия по результатам** - установить, обновить или сообщить об актуальности.

#### Шаблон блока для install.py

Заменить `tool-name` на фактическое имя инструмента, `package-name` на имя пакета из `pyproject.toml` (поле `name`, с заменой дефиса на подчеркивание для пути в `site-packages`):

```python
#!/usr/bin/env python3
# ИИ-агент:
# Если пользователь указывает @install.py без дополнительных пояснений -
# выполнить диагностику и установку самостоятельно:
#
# 1. Проверить что запуск выполнен из репозитория (рядом есть pyproject.toml и .git/).
#    Проверить что pyproject.toml содержит [build-system] и версии зависимостей с ==.
#
# 2. Проверить состояние установки:
# which tool-name
#
# 3. Если пакет не установлен:
# python run/deploy/install.py
# После установки сообщить пользователю путь к команде и расположение конфигурации.
#
# 4. Если пакет установлен:
# - Сообщить пользователю: пакет уже установлен, путь к команде.
# - Предложить обновление через @run/deploy/update.py
```

#### Шаблон блока для update.py

Заменить `tool-name` на фактическое имя инструмента и список файлов для сравнения:

```python
#!/usr/bin/env python3
# ИИ-агент:
# Если пользователь указывает @update.py без дополнительных пояснений -
# выполнить диагностику и обновление самостоятельно:
#
# 1. Проверить что запуск выполнен из репозитория (рядом есть pyproject.toml и .git/).
#
# 2. Проверить состояние установки:
# which tool-name
#
# 3. Если пакет не установлен:
# - Сообщить пользователю: пакет не установлен.
# - Предложить установку через @run/deploy/install.py
#
# 4. Если пакет установлен - сравнить исходники в uv-venv с репозиторием:
# diff <file> ~/.local/share/uv/tools/tool-name/lib/python*/site-packages/<file>
#
# Проверить как минимум: main.py, src/config.py, src/logger.py и все ключевые
# модули из src/ и run/
#
# 5. Если исходники отличаются:
# python run/deploy/update.py
# После обновления сообщить пользователю синхронизированные параметры.
#
# 6. Если исходники совпадают:
# - Сообщить пользователю: пакет установлен и актуален, действия не требуются
```

**Правила для блоков:**

- Список файлов для проверки через `diff` должен включать все ключевые модули проекта - `main.py`, `src/config.py`, `src/logger.py` и все файлы из `src/` и `run/`, которые влияют на работу инструмента.
- Команды выносить на отдельные строки - агент должен иметь возможность скопировать их дословно.
- Заменять `tool-name` на фактическое имя инструмента.
- Не включать в блок логику скрипта - только инструкции по проверке.
- Агент должен принимать решения сам, не спрашивая пользователя о дальнейших шагах.

### 4.2. Полный шаблон install.py

Файл `run/deploy/install.py`. В начале разместить блок диагностики из раздела 4.1, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 4.1 ...

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
XDG_CONFIG = Path.home() / ".config"
APP_DIR = XDG_CONFIG / TOOL_NAME


def _check_uv() -> None:
    if not shutil.which("uv"):
        print("uv не найден. Установите: sudo pacman -S uv")
        sys.exit(1)


def _check_pyproject() -> None:
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        print("pyproject.toml не найден в корне проекта")
        sys.exit(1)


def _ensure_data_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "config").mkdir(exist_ok=True)
    (APP_DIR / "log").mkdir(exist_ok=True)


def _copy_if_missing(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    if not src.exists():
        print(f"Шаблон не найден: {src}")
        return
    shutil.copy2(src, dst)


def main() -> None:
    _check_pyproject()
    _check_uv()
    if shutil.which(TOOL_NAME):
        print(f"Пакет '{TOOL_NAME}' уже установлен. Для обновления: python run/deploy/update.py")
        return
    try:
        subprocess.run(["uv", "tool", "install", "."], cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки пакета: {e}")
        sys.exit(1)
    _ensure_data_dirs()
    _copy_if_missing(
        PROJECT_ROOT / "config" / "config.ini.example",
        APP_DIR / "config" / "config.ini",
    )
    _copy_if_missing(
        PROJECT_ROOT / ".env.example",
        APP_DIR / ".env",
    )
    cmd_path = shutil.which(TOOL_NAME)
    if cmd_path:
        print(f"Команда '{TOOL_NAME}' доступна: {cmd_path}")
    else:
        print("Команда установлена, но не найдена в PATH.")
        print("Добавьте ~/.local/bin в PATH или перезапустите оболочку.")


if __name__ == "__main__":
    main()
```

### 4.3. Полный шаблон update.py

Файл `run/deploy/update.py`. В начале разместить блок диагностики из раздела 4.1, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 4.1 ...

import configparser
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
XDG_CONFIG = Path.home() / ".config"
APP_DIR = XDG_CONFIG / TOOL_NAME


def _check_uv() -> None:
    if not shutil.which("uv"):
        print("uv не найден. Установите: sudo pacman -S uv")
        sys.exit(1)


def _check_pyproject() -> None:
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        print("pyproject.toml не найден в корне проекта")
        sys.exit(1)


def _sync_pyproject_version() -> None:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    dev_config = PROJECT_ROOT / "config" / "config.ini"
    if not pyproject.exists() or not dev_config.exists():
        return
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    py_ver: str | None = data.get("project", {}).get("version")
    if not py_ver:
        return
    dev_cfg = configparser.ConfigParser()
    dev_cfg.read(dev_config, encoding="utf-8")
    cfg_ver: str | None = dev_cfg.get("app", "version", fallback=None)
    if not cfg_ver:
        return
    py_parts = tuple(int(x) for x in py_ver.split("."))
    cfg_parts = tuple(int(x) for x in cfg_ver.split("."))
    if py_parts == cfg_parts:
        return
    higher = py_ver if py_parts > cfg_parts else cfg_ver
    if py_parts < cfg_parts:
        content = pyproject.read_text(encoding="utf-8")
        content = content.replace(f'version = "{py_ver}"', f'version = "{cfg_ver}"')
        pyproject.write_text(content, encoding="utf-8")
        print(f"pyproject.toml version: {py_ver} -> {cfg_ver}")
    else:
        dev_cfg.set("app", "version", higher)
        with open(dev_config, "w", encoding="utf-8") as f:
            dev_cfg.write(f)
        print(f"config.ini [app] version: {cfg_ver} -> {py_ver}")


def _sync_app_info() -> None:
    dev_config = PROJECT_ROOT / "config" / "config.ini"
    prod_config = APP_DIR / "config" / "config.ini"
    if not dev_config.exists() or not prod_config.exists():
        return
    dev_cfg = configparser.ConfigParser()
    dev_cfg.read(dev_config, encoding="utf-8")
    prod_cfg = configparser.ConfigParser()
    prod_cfg.read(prod_config, encoding="utf-8")
    if not dev_cfg.has_section("app"):
        return
    if not prod_cfg.has_section("app"):
        prod_cfg.add_section("app")
    changed = False
    for key in ("name", "version"):
        dev_val = dev_cfg.get("app", key, fallback=None)
        prod_val = prod_cfg.get("app", key, fallback=None)
        if dev_val and dev_val != prod_val:
            prod_cfg.set("app", key, dev_val)
            print(f"{key}: {prod_val or 'не задан'} -> {dev_val}")
            changed = True
    if changed:
        with open(prod_config, "w", encoding="utf-8") as f:
            prod_cfg.write(f)


def main() -> None:
    _check_pyproject()
    _check_uv()
    if not shutil.which(TOOL_NAME):
        print(f"Пакет '{TOOL_NAME}' не установлен. Для установки: python run/deploy/install.py")
        return
    subprocess.run(["uv", "cache", "clean", TOOL_NAME], check=False)
    _sync_pyproject_version()
    try:
        subprocess.run(
            ["uv", "tool", "install", ".", "--force"],
            cwd=PROJECT_ROOT,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Ошибка обновления пакета: {e}")
        sys.exit(1)
    _sync_app_info()
    print("Обновление завершено")


if __name__ == "__main__":
    main()
```

### 4.4. Скрипт install.py - первая установка

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, не установлен ли уже пакет. Если установлен - сообщить и завершить (для обновления использовать `run/deploy/update.py`).
3. Установить пакет (`uv tool install .`).
4. Создать каталог данных (`~/.config/tool-name/`) с подкаталогами `config/` и `log/`.
5. Скопировать шаблон конфига - только если файл отсутствует.
6. Скопировать `.env` - только если файл отсутствует.
7. Проверить, что команда доступна в PATH.

### 4.5. Скрипт update.py - обновление

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, что пакет установлен. Если не установлен - сообщить и завершить (для установки использовать `run/deploy/install.py`).
3. Очистить кэш: `uv cache clean tool-name`. Без этого при неизменной версии в `pyproject.toml` команда `uv tool install . --force` установит кэшированный wheel вместо пересборки из текущих исходников - изменения кода не попадут в установленный пакет.
4. Синхронизировать версию между `pyproject.toml` и `config/config.ini` (dev-конфиг): прочитать `version` из обоих источников, сравнить по SemVer и привести к более высокому значению - обновить тот источник, где версия ниже. Это гарантирует, что метаданные пакета (поле `version` в `pyproject.toml`) и runtime-конфиг (параметр `version` секции `[app]` в `config/config.ini`) совпадают при следующем запуске - `uv tool list` и `APP_VERSION` в коде покажут одинаковую версию.
5. Переустановить пакет: `uv tool install . --force`.
6. Синхронизировать параметры приложения: прочитать `name` и `version` из секции `[app]` dev-конфига и prod-конфига; если отличаются - обновить в prod и вывести в консоль старое и новое значение для каждого измененного параметра. Другие параметры конфига не затрагиваются.

---

## 5. Требование к uv

`uv` - единственный инструмент для установки. Он устанавливает пакет в изолированный venv, не затрагивая систему. Команда `uv tool install .` использует `pyproject.toml` в корне проекта. Флаг `--force` применяется только при обновлении.

**Установка uv:**

```bash
sudo pacman -S uv
```

Установочные скрипты проверяют наличие `uv` до начала работы и завершаются с сообщением об установке, если `uv` не найден.

---

## 6. Дополнения к .gitignore

При подготовке проекта к деплою добавить в `.gitignore`:

```
*.egg-info/
dist/
build/
```

Это артефакты сборки, которые создает setuptools при установке. Они не должны попадать в репозиторий.

---

## 7. Итоговая структура после установки

```
Код:        site-packages/tool_name/   (или изолированный venv через uv)
Команда:    ~/.local/bin/command
Конфиг:     ~/.config/tool-name/config/config.ini
Секреты:    ~/.config/tool-name/.env
Логи:       ~/.config/tool-name/log/
```

Исходный репозиторий становится независимым от установленного инструмента - его можно удалять, перезаписывать, клонировать заново.

---

## 8. Рекомендации

### 8.1. Точка входа

Функция `main()` не должна содержать логику напрямую. Ее задача - разобрать аргументы, инициализировать конфигурацию и делегировать выполнение:

```python
def main() -> None:
    logger = get_logger(__name__, log_dir=PROJECT_ROOT / "log")
    logger.info(f"{APP_NAME} v{APP_VERSION}")
    args = parse_args()
    init_config()
    run(args)


if __name__ == "__main__":
    main()
```

### 8.2. Единый источник имени и версии

Название и версия приложения для отображения пользователю (в логах, консоли) хранятся в `config/config.ini` в секции `[app]` (параметры `name` и `version`). Это единый источник для всех режимов - разработки и установленного.

Версия в `pyproject.toml` (поле `version`) предназначена только для метаданных пакета (pip/uv) и не используется для отображения. Синхронность версий в `pyproject.toml` и `config.ini` - ответственность агента; агент предлагает обновить обе при коммите (см. основной стандарт, раздел 01.07).

```python
from src.config import APP_NAME, APP_VERSION
```

Установочный скрипт `update.py` автоматически синхронизирует `name` и `version` из репо-конфига в прод-конфиг при обновлении (раздел 8.8).

### 8.3. Режим разработчика

Для отладки без установки использовать `uv` в editable-режиме. Требуется активный venv:

```bash
source .venv/bin/activate
uv pip install -e .
```

Устанавливает пакет в "editable" режиме - изменения в коде отражаются сразу без переустановки. Код выполняется из репозитория (`.git/` на месте), поэтому `PROJECT_ROOT` указывает на корень репозитория (режим разработки). Это позволяет отлаживать инструмент с путями репозитория без отдельной установки.

**Разница между режимами `uv`:**

- `uv tool install .` - изолированная установка CLI-команды для повседневного использования. Пакет попадает в отдельный venv, команда доступна глобально.
- `uv pip install -e .` - установка в текущий venv для разработки. Требует активированный venv, изменения в коде применяются сразу.

### 8.4. Удаление

```bash
uv tool uninstall tool-name
```

Каталог данных `~/.config/tool-name/` при удалении пакета не затрагивается - пользователь удаляет его вручную при необходимости.

### 8.5. Чек-лист перед релизом

1. Все зависимости указаны в `pyproject.toml` с точными версиями (`==`).
2. `requirements.txt` и `pyproject.toml` синхронизированы (одинаковые пакеты и версии).
3. Версия в `pyproject.toml` обновлена.
4. Секция `[app]` в `config.ini` содержит корректные `name` и `version`.
5. `__init__.py` есть во всех импортируемых пакетах.
6. Подмена `PROJECT_ROOT` в `config.py` использует корректное имя инструмента.
7. Установочные скрипты (`run/deploy/install.py`, `run/deploy/update.py`) используют корректное имя инструмента.
8. `.gitignore` содержит `*.egg-info/`, `dist/`, `build/`.
9. Тестовая установка и запуск на чистой машине прошли успешно.
10. Data-файлы (SQL, шаблоны) доступны после установки.

### 8.6. Тестирование установки

После сборки проверить:

```bash
python run/deploy/install.py && команда --help
```

Убедиться, что:
- Команда доступна в PATH.
- Конфиг создается в `~/.config/tool-name/`.
- Логи пишутся в `~/.config/tool-name/log/`.
- Повторный запуск `install.py` не перезаписывает существующий конфиг и сообщает об установленном пакете.
- `update.py` не затрагивает данные пользователя.

### 8.7. Shell completion

Для CLI-инструментов с большим количеством команд и аргументов рекомендуется добавить генерацию автодополнения для оболочки. Если используется `argparse`, завершения генерируются через встроенную поддержку Python (требуется Python >= 3.13, доступно в 3.14+) или через пакет `argcomplete` (для Python >= 3.12). Пример регистрации:

```bash
eval "$(register-python-argcomplete tool-name)"
```

Для bash добавить в `~/.bashrc`. Документировать в README проекта.

### 8.8. Синхронизация версии и параметров при обновлении

Скрипт `update.py` выполняет два этапа синхронизации (раздел 4.5):

**Этап 1 - синхронизация версии в репозитории (до установки).** Устраняет расхождение между двумя источниками версии внутри репозитория: `pyproject.toml` (поле `version`) и `config/config.ini` (параметр `version` секции `[app]`). Сравнивает значения по SemVer, берет более высокое и записывает в тот источник, где версия ниже. Выполняется до `uv tool install --force`, чтобы метаданные пакета и runtime-конфиг были согласованы с момента установки.

**Этап 2 - синхронизация параметров приложения (после установки).** Переносит `name` и `version` из dev-конфига репозитория в prod-конфиг пользователя (`~/.config/tool-name/config/config.ini`).

**Правила:**
- Синхронизируются параметры `name` и `version` в секции `[app]` - никаких других изменений в конфиге
- Пользовательские настройки никогда не перезаписываются
- Для добавления новых секций и параметров пользователь обновляет prod-конфиг вручную или через агента
- Для `.env` изменений не производится - новые переменные пользователь добавляет вручную
