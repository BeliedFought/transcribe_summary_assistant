# Требования к установке Python-проекта как системного инструмента (Windows). Версия 2.6.0. 2026-06-14

Документ является дополнением к `doc/standards/project_standards.md` и применяется поверх него для проектов, которые планируется устанавливать как системные инструменты на Windows. Все требования основного стандарта остаются в силе, кроме случаев, явно описанных в данном документе.

Документ применим для Windows 10/11 и Windows Server 2016+. Версия Windows не имеет значения - все используемые механизмы (PowerShell 5.1+, pathlib, uv) работают идентично.

**Принципиальное отличие от Linux-деплоя:** прямой доступ агента к Windows-машине отсутствует. Установка состоит из двух фаз:

1. **Подготовка на Linux (машина агента)** - сборка wheel, создание установочного ZIP-архива с инструкциями, конфигами-шаблонами и установочным скриптом. Выполняется агентом с полным доступом к репозиторию.
2. **Установка на Windows (целевая машина)** - пользователь (и администратор) распаковывают архив и выполняют инструкции. Роль агента - только подготовить пакет, максимально автоматизировать установку и снабдить пользователя понятными инструкциями.

Цель - выполнить максимум подготовительных действий на Linux-машине, чтобы на Windows-стороне требовалось минимальное количество ручных шагов.

---

## 1. Требования к окружению Windows

Инструкции из этого раздела включаются в архив как `README.txt` (см. раздел 5). Пользователь и администратор выполняют их на целевой Windows-машине.

Пользователь без административных прав может установить и использовать инструмент полностью самостоятельно. Администратор нужен только для установки базового ПО на машину.

### 1.1. Разделение ответственности

| Компонент | Кто устанавливает | Почему |
|-----------|-------------------|--------|
| Python 3.14+ | **Администратор** | Системный пакет, требует записи в Program Files и PATH |
| Git 2.30+ | **Администратор** | Системный пакет, требует запись в Program Files и PATH |
| uv | **Пользователь** | Устанавливается в профиль пользователя, админ не нужен |
| Кодировка UTF-8 | **Администратор** (опционально) | Изменение реестра для системной кодировки |
| Проект (tool-name) | **Пользователь** | Устанавливается из архива через `python install.py` |

**Итого:** пользователю нужно обратиться к администратору один раз - для установки Python и Git на машину. Все остальное пользователь делает сам из установочного архива.

### 1.2. Текст обращения к администратору

Пользователь отправляет администратору следующий текст без изменений (заменить `TOOL-NAME` на имя проекта):

---

> **Тема: Запрос на установку ПО для работы с Python-проектом**
>
> Для работы нужен Python-проект (TOOL-NAME). Сам проект я установлю самостоятельно.
> Прошу установить на мою машину два компонента:
>
> **1. Python 3.14 или новее**
>
> Скачать: https://www.python.org/downloads/
>
> При установке обязательно отметить галочку **"Add Python to PATH"**.
>
> Или из командной строки (тихая установка для всех пользователей):
> ```powershell
> Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.14.0/python-3.14.0-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"
> Start-Process -Wait -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1"
> Remove-Item "$env:TEMP\python-installer.exe"
> ```
>
> **2. Git 2.30 или новее**
>
> Скачать: https://git-scm.com/download/win
>
> Или через winget:
> ```powershell
> winget install Git.Git
> ```
>
> **После установки прошу подтвердить**, что команды работают:
> ```powershell
> python --version
> git --version
> ```
> Обе команды должны вывести версию без ошибок.
>
> Больше ничего устанавливать не нужно - остальное я сделаю сам.

---

### 1.3. Что пользователь делает сам

После подтверждения администратора пользователь устанавливает `uv`:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Альтернативные способы (если PowerShell-скрипт не работает):

- **pip**: `pip install uv` (если Python установлен и доступен)
- **winget**: `winget install astral-sh.uv` (Windows 10+, не работает на Server)

Проверить:

```powershell
uv --version
```

Если команда не найдена - перезапустить оболочку. `uv` устанавливается в профиль пользователя (`%USERPROFILE%\.local\bin\` или `%USERPROFILE%\.cargo\bin\`), административные права не требуются.

### 1.4. Проверка готовности окружения

Пользователь выполняет:

```powershell
python --version
uv --version
git --version
```

Все три команды должны возвращать версию без ошибок. После этого можно устанавливать проект: распаковать архив и выполнить `python install.py`.

### 1.5. Кодировка UTF-8

Для корректной работы с кириллицей в логах и выводе:

- **Windows Terminal** - UTF-8 поддерживается нативно, дополнительных действий не требуется
- **PowerShell** - в PowerShell 7+ UTF-8 по умолчанию. В PowerShell 5.1 при необходимости:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
  ```
- **cmd** - выполнить `chcp 65001` для переключения на UTF-8

Если кириллица отображается некорректно, можно попросить администратора включить UTF-8 на уровне системы (добавить в текст обращения из раздела 1.2):

> **Опционально: кодировка UTF-8**
>
> Если в выводе программ вместо русских букв появляются символы "??????" или "кракозябры" - включить UTF-8 системно:
> ```powershell
> Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage" -Name "OEMCP" -Value "65001"
> Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage" -Name "ACP" -Value "65001"
> ```
> После применения перезагрузить машину.

Рекомендуется использовать Windows Terminal как основную оболочку - в нем UTF-8 работает без дополнительных настроек.

---

## 2. Обязательные условия к проекту

До начала установки проект должен соответствовать следующим требованиям:

1. **Корневой модуль с точкой входа** - функция `main()` в файле (например `main.py` или `cli.py`). Функция должна вызываться через `if __name__ == "__main__": main()` и не содержать побочных эффектов на уровне модуля. Функция `main()` не должна содержать логику напрямую - разобрать аргументы, инициализировать конфигурацию, делегировать выполнение (в соответствии с основным стандартом).
2. **Все импорты через пакеты** - `from src.xxx import ...`. Запрещены хаки с `sys.path`, относительные импорты за пределами пакета, динамическое формирование путей импорта.
3. **`__init__.py`** в каждом каталоге, который импортируется как пакет. Пустой файл, без кода инициализации.
4. **Все зависимости зафиксированы** в `requirements.txt` с точными версиями (`==`).

---

## 3. Структура pyproject.toml

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
- **`[project.scripts]`** - создает CLI-команду. Формат: `имя_команды = "путь.до.модуля:функция"`. После установки wrapper-скрипт попадает в каталог пользователя. На Windows создается `.exe`-файл. Пример: `ghupd = "main:main"` создаст команду `ghupd.exe`, которая вызывает `main.main()`.
- **`py-modules`** - для файлов в корне проекта (не внутри пакета). Без этого `main.py` не попадет в wheel. Если точка входа внутри пакета - секция не нужна.
- **`[tool.setuptools.packages.find]`** - указывает, какие каталоги являются пакетами. `include = ["src*"]` включает `src` и все его подкаталоги.

**Правила:**

- Поле `version` в `pyproject.toml` - единый источник правды о версии. Не дублировать версию в коде.
- Имя пакета (`name`) - только строчные латинские буквы, цифры, дефисы. Без подчеркиваний.
- `requires-python` - указывать минимальную версию, с которой реально тестировался проект.
- Версии **runtime-зависимостей** (секция `[project] dependencies`) фиксируются с `==`, аналогично `requirements.txt`. Build-зависимости (`[build-system] requires`) указываются с `>=` - это корректно, правило фиксации версий к ним не применяется.
- `requirements.txt` и `pyproject.toml` должны быть синхронизированы: одинаковые пакеты и версии в обеих файлах. Рекомендуется проверять синхронизацию перед каждым коммитом: сравнить список зависимостей из обоих файлов и убедиться, что каждая строка из `requirements.txt` имеет соответствующую строку в `dependencies` в `pyproject.toml`.

### 3.1. Упаковка non-Python файлов

Если проект содержит SQL-файлы, шаблоны или другие данные, не являющиеся Python-модулями, их нужно явно включить в дистрибутив. По умолчанию setuptools упаковывает только `.py` файлы.

Рекомендуемый подход - `MANIFEST.in` для контроля содержимого sdist + `[tool.setuptools.data-files]` для размещения файлов при установке.

#### 3.1.1. MANIFEST.in

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

#### 3.1.2. data-files в pyproject.toml

Секция `[tool.setuptools.data-files]` указывает, куда файлы будут установлены относительно `prefix`. На Windows `prefix` совпадает с `sys.prefix` внутри изолированного venv.

```toml
[tool.setuptools.data-files]
"share/tool-name/sql" = ["sql/*.sql"]
"share/tool-name/config" = ["config/config.ini.example"]
```

После установки через `uv tool install` файлы размещаются внутри изолированного venv. Доступ к ним в коде - через `sys.prefix` (см. раздел 3.1.3):

- `{sys.prefix}/share/tool-name/sql/query.sql`
- `{sys.prefix}/share/tool-name/config/config.ini.example`

При установке через `uv tool install` изолированный venv находится в `%LOCALAPPDATA%\uv\tools\tool-name\`. Путь `sys.prefix` внутри этого venv указывает на корень venv, поэтому `data-files` размещаются по пути `%LOCALAPPDATA%\uv\tools\tool-name\share\tool-name\`.

#### 3.1.3. Доступ к data-файлам в коде

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

#### 3.1.4. Правила

- Data-файлы, которые нужны только в режиме разработки (примеры, тестовые данные) - не упаковывать. Только те, что требуются для работы установленного инструмента.
- Проверять доступность data-файлов после `uv tool install .` - содержимое wheel можно посмотреть командой `uv tool dir tool-name`.
- Не использовать относительные пути с `..` в `package-data` и `importlib.resources` - поведение зависит от версии setuptools и формата архива.
- При добавлении новых типов data-файлов обновлять `MANIFEST.in` и соответствующую секцию в `pyproject.toml`.

---

## 4. Разделение кода и данных

После установки код лежит в `site-packages/`, а конфиги, логи и секреты должны быть доступны пользователю. Решение - подмена `PROJECT_ROOT` в `src/config.py` в зависимости от режима запуска.

### 4.1. Подмена PROJECT_ROOT в config.py

Шаблон `templates/src/config.py` из основного стандарта не меняется. При подготовке конкретного проекта к установке в `src/config.py` добавляется проверка режима и подмена `PROJECT_ROOT`:

- **Режим разработки** (запуск из репозитория): `PROJECT_ROOT = Path(__file__).resolve().parents[1]` - как в основном стандарте, не меняется.
- **Установленный режим** (пакет установлен через `uv tool install`): `PROJECT_ROOT = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "tool-name"` (обычно `C:\Users\<user>\AppData\Roaming\tool-name\`).

Маркер режима - наличие каталога `.git/` рядом с `src/`. Если каталог существует - это клон репозитория, активируется режим разработки. Если нет (код выполняется из `site-packages/` после установки) - установленный режим.

Достаточно одной проверки `.git/`, без использования `importlib.metadata`:

- При `uv tool install` код выполняется из изолированного venv в `%LOCALAPPDATA%\uv\tools\tool-name\`, где нет `.git/` - установленный режим.
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
В установленном режиме - %APPDATA%/tool-name/.

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
    PROJECT_ROOT = Path(
        os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    ) / "tool-name"

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

### 4.2. Построение путей от PROJECT_ROOT

Все пути в коде строятся от `PROJECT_ROOT` (как в основном стандарте):

```python
from src.config import PROJECT_ROOT

config_path = PROJECT_ROOT / "config" / "config.ini"
log_dir = PROJECT_ROOT / "log"
env_path = PROJECT_ROOT / ".env"
```

В режиме разработки `PROJECT_ROOT` указывает на корень репозитория. В установленном режиме `PROJECT_ROOT` указывает на `%APPDATA%\tool-name\`. Код, использующий `PROJECT_ROOT / "config" / "config.ini"` и `PROJECT_ROOT / "log"`, работает без изменений в обоих режимах.

**Правила:**

- Не использовать `Path.cwd()` или `os.getcwd()` для определения путей к данным.
- Не хардкодить абсолютные пути.
- Использовать `pathlib.Path` для всех операций с путями.
- При первом запуске в установленном режиме - создавать каталоги через `path.mkdir(parents=True, exist_ok=True)`.

---

## 5. Подготовка установочного пакета на Linux

Агент выполняет все подготовительные действия на Linux-машине. Результат - ZIP-архив, который передается на Windows-машину любым доступным способом (флешка, сетевой диск, почта).

### 5.1. Сборка wheel

Из корня репозитория:

```bash
uv build
```

Команда создает wheel-файл в `dist/` (например, `dist/tool_name-1.0.0-py3-none-any.whl`). Wheel содержит весь код проекта и metadata из `pyproject.toml`.

### 5.2. Структура архива

Архив именуется `tool-name-1.0.0-install.zip`. Внутри - каталог с плоской структурой:

```
tool-name-1.0.0-install/
├── install.py               # Установка (раздел 6)
├── update.py                # Обновление (раздел 6)
├── dist/
│   └── tool_name-1.0.0-py3-none-any.whl
├── config/
│   └── config.ini.example
├── .env.example
└── README.txt               # Инструкции (раздел 1)
```

**Содержимое архива:**

| Файл | Источник в репозитории | Назначение |
|------|----------------------|------------|
| `install.py` | `run/deploy/install.py` | Установка из архива (Windows) |
| `update.py` | `run/deploy/update.py` | Обновление из архива (Windows) |
| `dist/*.whl` | Собирается `uv build` | Готовый пакет |
| `config/config.ini.example` | `config/config.ini.example` | Шаблон конфигурации |
| `.env.example` | `.env.example` | Шаблон секретов |
| `README.txt` | Генерируется скриптом | Инструкции для администратора и пользователя |

### 5.3. Содержание README.txt

Файл `README.txt` генерируется скриптом `package.py` при сборке архива. Содержит:

1. **Обращение к администратору** - текст из раздела 1.2 (установка Python, Git, опционально UTF-8)
2. **Действия пользователя** - установка uv (раздел 1.3), распаковка архива, запуск `python install.py`
3. **Проверка установки** - `tool-name --help`

Текст README генерируется из шаблона в коде `package.py`. Это гарантирует, что инструкции всегда соответствуют текущей версии проекта.

### 5.4. Создание архива

Сборка архива выполняется командой из корня репозитория:

```bash
python run/deploy/package.py
```

Скрипт:
1. Проверяет наличие `pyproject.toml` и `uv`
2. Выполняет `uv build` для сборки wheel
3. Создает временную директорию с содержимым архива
4. Копирует: wheel из `dist/`, `config/config.ini.example`, `.env.example`, `install.py`, `update.py`
5. Генерирует `README.txt` на основе шаблона (с подстановкой имени и версии проекта)
6. Упаковывает в ZIP-архив: `tool-name-1.0.0-install.zip`
7. Размещает архив в корне проекта

Архив готов к передаче на Windows-машину. Исходный репозиторий не нужен на Windows.

---

## 6. Установочные скрипты

Скрипты размещаются в `run/deploy/` репозитория:

| Скрипт | Где выполняется | Назначение |
|--------|----------------|------------|
| `run/deploy/package.py` | Linux (из репозитория) | Сборка wheel и создание ZIP-архива |
| `run/deploy/install.py` | Windows (из архива) | Первая установка из wheel |
| `run/deploy/update.py` | Windows (из архива) | Обновление из нового wheel |

Каждый скрипт выполняет только одну задачу, без аргументов командной строки и подкоманд. Скрипты `install.py` и `update.py` копируются в корень архива без изменений.

Скрипты не зависят от других модулей проекта - не импортируют из `src/` и не используют логгер. Вывод реализован через `print()` как исключение из общего правила. Строки вывода не должны начинаться с маркеров уровня в квадратных скобках (`[i]`, `[!]`, `[*]`).

### 6.1. Блок диагностики для ИИ-агента

Каждый скрипт в `run/deploy/` выполняет двойную роль: исполняемый скрипт для пользователя и skill для ИИ-агента. Если пользователь тегает файл без пояснений, агент должен самостоятельно диагностировать ситуацию и действовать.

Скрипт должен начинаться с блока комментариев-инструкций для ИИ-агента.

#### Шаблон блока для package.py

Заменить `tool-name` на фактическое имя инструмента:

```python
#!/usr/bin/env python3
# ИИ-агент:
# Если пользователь указывает @package.py без дополнительных пояснений -
# подготовить установочный ZIP-архив для Windows:
#
# 1. Проверить что запуск выполнен из репозитория (рядом есть pyproject.toml и .git/).
#    Проверить что pyproject.toml содержит [build-system] и версии зависимостей с ==.
#
# 2. Собрать архив:
# python run/deploy/package.py
#
# 3. Сообщить пользователю путь к созданному ZIP-архиву.
#    Архив передается на Windows-машину любым способом (флешка, сеть, почта).
```

#### Шаблон блока для install.py

Заменить `tool-name` и список файлов. Особенность: агент не имеет прямого доступа к Windows-машине:

```python
#!/usr/bin/env python3
# ИИ-агент:
# Если пользователь указывает @install.py без дополнительных пояснений:
#
# 1. Если запуск из репозитория Linux (рядом есть pyproject.toml и .git/):
#    - Проверить состояние установки на Linux: which tool-name
#    - Если не установлен: python run/deploy/install.py
#    - Если установлен: сообщить, предложить @run/deploy/update.py
#
# 2. Если пользователь сообщает о проблемах на Windows-машине:
#    Установлен ли пакет (на Windows, выполняет пользователь):
# where.exe tool-name
#
# 3. Если пакет не установлен на Windows:
#    - Пересобрать архив: python run/deploy/package.py
#    - Передать архив на Windows, пользователь распаковывает и выполняет:
# python install.py
#
# 4. Если пакет установлен и исходники совпадают:
#    - Сообщить пользователю: пакет установлен и актуален
```

#### Шаблон блока для update.py

Заменить `tool-name` и список файлов:

```python
#!/usr/bin/env python3
# ИИ-агент:
# Если пользователь указывает @update.py без дополнительных пояснений:
#
# 1. Если запуск из репозитория Linux (рядом есть pyproject.toml и .git/):
#    - Проверить что пакет установлен: which tool-name
#    - Если не установлен: сообщить, предложить @run/deploy/install.py
#    - Сравнить исходники в uv-venv с репозиторием:
#      diff <file> ~/.local/share/uv/tools/tool-name/lib/python*/site-packages/<file>
#      Проверить как минимум: main.py, src/config.py, src/logger.py и все
#      ключевые модули из src/ и run/
#    - Если отличаются: python run/deploy/update.py
#    - Если совпадают: сообщить об актуальности
#
# 2. Если пользователь сообщает о проблемах на Windows-машине:
#    Сравнить исходники в uv-venv с репозиторием (выполняет пользователь):
# fc <file> $env:LOCALAPPDATA\uv\tools\tool-name\lib\python*\site-packages\<file>
#    Проверить как минимум: main.py, src/config.py, src/logger.py и все
#    ключевые модули из src/ и run/
#
# 3. Если исходники отличаются:
#    - Пересобрать архив: python run/deploy/package.py
#    - Передать архив на Windows, пользователь распаковывает и выполняет:
# python update.py
#
# 4. Если пакет установлен и исходники совпадают:
#    - Сообщить пользователю: пакет установлен и актуален
```

**Правила для блоков:**

- Команды для Windows помечать явно - агент не имеет прямого доступа к Windows-машине, эти команды выполняет пользователь
- Команды выносить на отдельные строки - пользователь должен иметь возможность скопировать их дословно
- Заменять `tool-name` на фактическое имя инструмента
- Не включать в блок логику скрипта - только инструкции по проверке
- Агент должен принимать решения сам, не спрашивая пользователя о дальнейших шагах

### 6.2. Полный шаблон package.py

Файл `run/deploy/package.py`. Запускается на Linux из репозитория. В начале разместить блок диагностики из раздела 6.1, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 6.1 ...

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
TOOL_VERSION = "1.0.0"
DEPLOY_DIR = Path(__file__).resolve().parent

_README_TEMPLATE = """\
Установка {tool_name} v{tool_version}
{separator}

ШАГ 1. Обратиться к администратору (если Python и Git еще не установлены)
{sub_separator}

Отправить администратору следующий текст:

---

Тема: Запрос на установку ПО для работы с Python-проектом

Для работы нужен Python-проект ({tool_name}).
Сам проект я установлю самостоятельно.
Прошу установить на мою машину два компонента:

1. Python 3.14 или новее
   Скачать: https://www.python.org/downloads/
   При установке обязательно отметить галочку "Add Python to PATH".

2. Git 2.30 или новее
   Скачать: https://git-scm.com/download/win

После установки прошу подтвердить, что команды работают:
   python --version
   git --version
Обе команды должны вывести версию без ошибок.

Больше ничего устанавливать не нужно - остальное я сделаю сам.

---

ШАГ 2. Установить uv
{sub_separator}

Открыть PowerShell и выполнить:

   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Проверить:
   uv --version

Если команда не найдена - перезапустить PowerShell.

ШАГ 3. Установить {tool_name}
{sub_separator}

Распаковать этот архив в любую папку.
Открыть PowerShell в папке архива и выполнить:

   python install.py

Скрипт установит {tool_name} и подготовит конфигурацию.

ШАГ 4. Настроить конфигурацию
{sub_separator}

Заполнить настройки в файлах:
   - config.ini - в папке, которую укажет скрипт после установки
   - .env - секреты (токены, пароли)

Проверка установки
{sub_separator}

Выполнить: {tool_name} --help

Для обновления: распаковать новый архив и выполнить:
   python update.py
"""


def _check_uv() -> None:
    if not shutil.which("uv"):
        print("uv не найден. Установите: sudo pacman -S uv")
        sys.exit(1)


def _check_pyproject() -> None:
    if not (REPO_ROOT / "pyproject.toml").exists():
        print("pyproject.toml не найден. Скрипт package.py запускается из репозитория.")
        sys.exit(1)


def _generate_readme() -> str:
    return _README_TEMPLATE.format(
        tool_name=TOOL_NAME,
        tool_version=TOOL_VERSION,
        separator="=" * 40,
        sub_separator="-" * 40,
    )


def main() -> None:
    _check_pyproject()
    _check_uv()
    subprocess.run(["uv", "build"], cwd=REPO_ROOT, check=True)

    archive_name = f"{TOOL_NAME}-{TOOL_VERSION}-install"
    archive_dir = REPO_ROOT / archive_name

    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    archive_dir.mkdir()

    shutil.copy2(DEPLOY_DIR / "install.py", archive_dir / "install.py")
    shutil.copy2(DEPLOY_DIR / "update.py", archive_dir / "update.py")

    dist_dst = archive_dir / "dist"
    dist_dst.mkdir()
    for whl in (REPO_ROOT / "dist").glob("*.whl"):
        shutil.copy2(whl, dist_dst / whl.name)

    config_dst = archive_dir / "config"
    config_dst.mkdir()
    src = REPO_ROOT / "config" / "config.ini.example"
    if src.exists():
        shutil.copy2(src, config_dst / "config.ini.example")

    env_src = REPO_ROOT / ".env.example"
    if env_src.exists():
        shutil.copy2(env_src, archive_dir / ".env.example")

    (archive_dir / "README.txt").write_text(
        _generate_readme(), encoding="utf-8"
    )

    zip_path = REPO_ROOT / f"{archive_name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in archive_dir.rglob("*"):
            if fp.is_file():
                zf.write(fp, fp.relative_to(REPO_ROOT))

    shutil.rmtree(archive_dir)
    print(f"Архив создан: {zip_path}")


if __name__ == "__main__":
    main()
```

### 6.3. Полный шаблон install.py

Файл `run/deploy/install.py`. Запускается на Windows из архива. В начале разместить блок диагностики из раздела 6.1, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 6.1 ...

import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TOOL_NAME = "tool-name"
APP_DIR = Path(
    os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
) / TOOL_NAME


def _find_wheel() -> Path | None:
    wheels = list((SCRIPT_DIR / "dist").glob("*.whl"))
    return wheels[0] if wheels else None


def _check_uv() -> None:
    if not shutil.which("uv"):
        print(
            "uv не найден. Установите: "
            'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
        )
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
    _check_uv()
    if shutil.which(TOOL_NAME):
        print(
            f"Пакет '{TOOL_NAME}' уже установлен. "
            "Для обновления: python update.py"
        )
        return
    wheel = _find_wheel()
    if not wheel:
        print("wheel-файл не найден в dist/")
        sys.exit(1)
    try:
        subprocess.run(["uv", "tool", "install", str(wheel)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки пакета: {e}")
        sys.exit(1)
    _ensure_data_dirs()
    _copy_if_missing(
        SCRIPT_DIR / "config" / "config.ini.example",
        APP_DIR / "config" / "config.ini",
    )
    _copy_if_missing(
        SCRIPT_DIR / ".env.example",
        APP_DIR / ".env",
    )
    cmd_path = shutil.which(TOOL_NAME)
    if cmd_path:
        print(f"Команда '{TOOL_NAME}' доступна: {cmd_path}")
        print(f"Конфигурация: {APP_DIR}")
    else:
        print("Команда установлена, но не найдена в PATH.")
        print("Перезапустите PowerShell или проверьте PATH.")


if __name__ == "__main__":
    main()
```

### 6.4. Полный шаблон update.py

Файл `run/deploy/update.py`. Запускается на Windows из архива. В начале разместить блок диагностики из раздела 6.1, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 6.1 ...

import configparser
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TOOL_NAME = "tool-name"
APP_DIR = Path(
    os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
) / TOOL_NAME


def _find_wheel() -> Path | None:
    wheels = list((SCRIPT_DIR / "dist").glob("*.whl"))
    return wheels[0] if wheels else None


def _check_uv() -> None:
    if not shutil.which("uv"):
        print(
            "uv не найден. Установите: "
            'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
        )
        sys.exit(1)


def _sync_app_info() -> None:
    dev_config = None
    for name in ("config.ini", "config.ini.example"):
        candidate = SCRIPT_DIR / "config" / name
        if candidate.exists():
            dev_config = candidate
            break
    if not dev_config:
        return
    prod_config = APP_DIR / "config" / "config.ini"
    if not prod_config.exists():
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
    _check_uv()
    if not shutil.which(TOOL_NAME):
        print(f"Пакет '{TOOL_NAME}' не установлен. Для установки: python install.py")
        return
    wheel = _find_wheel()
    if not wheel:
        print("wheel-файл не найден в dist/")
        sys.exit(1)
    subprocess.run(["uv", "cache", "clean", TOOL_NAME], check=False)
    try:
        subprocess.run(
            ["uv", "tool", "install", str(wheel), "--force"],
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

### 6.5. Скрипт package.py - сборка архива (Linux)

1. Проверить наличие `pyproject.toml` и `uv`.
2. Выполнить `uv build` - собрать wheel в `dist/`.
3. Создать временную директорию `tool-name-1.0.0-install/`.
4. Скопировать в нее: `install.py`, `update.py`, wheel из `dist/`, `config/config.ini.example`, `.env.example`.
5. Сгенерировать `README.txt` с инструкциями (текст из раздела 1).
6. Упаковать в ZIP-архив `tool-name-1.0.0-install.zip`.
7. Удалить временную директорию.
8. Архив размещается в корне репозитория.

### 6.6. Скрипт install.py - первая установка (Windows)

1. Проверить наличие `uv`.
2. Проверить, не установлен ли уже пакет. Если установлен - сообщить и завершить (для обновления использовать `update.py`).
3. Найти wheel-файл в `dist/` рядом со скриптом.
4. Установить пакет: `uv tool install <wheel>`.
5. Создать каталог данных (`$env:APPDATA\tool-name\`) с подкаталогами `config\` и `log\`.
6. Скопировать шаблон конфига - только если файл отсутствует.
7. Скопировать `.env` - только если файл отсутствует.
8. Проверить, что команда доступна в PATH.

### 6.7. Скрипт update.py - обновление (Windows)

1. Проверить наличие `uv`.
2. Проверить, что пакет установлен. Если не установлен - сообщить и завершить (для установки использовать `install.py`).
3. Очистить кэш: `uv cache clean tool-name`.
4. Найти wheel-файл в `dist/` и переустановить: `uv tool install <wheel> --force`.
5. Синхронизировать параметры приложения: прочитать `name` и `version` из секции `[app]` dev-конфига (из архива) и prod-конфига; если отличаются - обновить в prod и вывести в консоль старое и новое значение для каждого измененного параметра. Другие параметры конфига не затрагиваются.

---

## 7. Требование к uv

`uv` - единственный инструмент для установки. На Linux используется для сборки wheel (`uv build`). На Windows - для установки из wheel-файла: `uv tool install <wheel>`. Флаг `--force` применяется только при обновлении.

**Установка uv на Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Установочные скрипты проверяют наличие `uv` до начала работы и завершаются с сообщением об установке, если `uv` не найден.

---

## 8. Дополнения к .gitignore

При подготовке проекта к деплою добавить в `.gitignore`:

```
*.egg-info/
dist/
build/
*-install.zip
```

Артефакты сборки (setuptools) и готовые установочные архивы не должны попадать в репозиторий.

---

## 9. Итоговая структура после установки

```
Код:        $env:LOCALAPPDATA\uv\tools\tool-name\lib\python*\site-packages\
Команда:    $env:LOCALAPPDATA\uv\tools\tool-name\Scripts\tool-name.exe
Конфиг:     $env:APPDATA\tool-name\config\config.ini
Секреты:    $env:APPDATA\tool-name\.env
Логи:       $env:APPDATA\tool-name\log\
```

Исходный репозиторий и установочный архив не нужны для работы инструмента после установки.

---

## 10. Рекомендации

### 10.1. Точка входа

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

### 10.2. Единый источник имени и версии

Название и версия приложения для отображения пользователю (в логах, консоли) хранятся в `config/config.ini` в секции `[app]` (параметры `name` и `version`). Это единый источник для всех режимов - разработки и установленного.

Версия в `pyproject.toml` (поле `version`) предназначена только для метаданных пакета (pip/uv) и не используется для отображения. Синхронность версий в `pyproject.toml` и `config.ini` - ответственность агента; агент предлагает обновить обе при коммите (см. основной стандарт, раздел 01.07).

```python
from src.config import APP_NAME, APP_VERSION
```

Скрипт `update.py` автоматически синхронизирует `name` и `version` из репо-конфига в прод-конфиг при обновлении (раздел 10.8).

### 10.3. Режим разработчика

Для отладки без установки использовать `uv` в editable-режиме. Требуется активный venv:

```powershell
.venv\Scripts\activate
uv pip install -e .
```

Устанавливает пакет в "editable" режиме - изменения в коде отражаются сразу без переустановки. Код выполняется из репозитория (`.git/` на месте), поэтому `PROJECT_ROOT` указывает на корень репозитория (режим разработки). Это позволяет отлаживать инструмент с путями репозитория без отдельной установки.

**Разница между режимами `uv`:**

- `uv tool install .` - изолированная установка CLI-команды для повседневного использования. Пакет попадает в отдельный venv, команда доступна глобально.
- `uv pip install -e .` - установка в текущий venv для разработки. Требует активированный venv, изменения в коде применяются сразу.

### 10.4. Удаление

```powershell
uv tool uninstall tool-name
```

Каталог данных `$env:APPDATA\tool-name\` при удалении пакета не затрагивается - пользователь удаляет его вручную при необходимости.

### 10.5. Чек-лист перед релизом

1. Все зависимости указаны в `pyproject.toml` с точными версиями (`==`).
2. `requirements.txt` и `pyproject.toml` синхронизированы (одинаковые пакеты и версии).
3. Версия в `pyproject.toml` обновлена.
4. Секция `[app]` в `config.ini` содержит корректные `name` и `version`.
5. `__init__.py` есть во всех импортируемых пакетах.
6. Подмена `PROJECT_ROOT` в `config.py` использует корректное имя инструмента.
7. Установочные скрипты (`run/deploy/install.py`, `run/deploy/update.py`, `run/deploy/package.py`) используют корректное имя инструмента (`TOOL_NAME`) и версию (`TOOL_VERSION` для `package.py`).
8. `.gitignore` содержит `*.egg-info/`, `dist/`, `build/`, `*-install.zip`.
9. Тестовая сборка архива (`python run/deploy/package.py`) выполнена успешно.
10. Тестовая установка из архива на целевой Windows-машине прошла успешно.
11. Data-файлы (SQL, шаблоны) доступны после установки.

### 10.6. Тестирование установки

После сборки архива на Linux:

```bash
python run/deploy/package.py
```

Передать архив на Windows-машину и проверить:

```powershell
python install.py
tool-name --help
```

Убедиться, что:
- Команда доступна в PATH (после перезапуска оболочки при необходимости).
- Конфиг создается в `$env:APPDATA\tool-name\`.
- Логи пишутся в `$env:APPDATA\tool-name\log\`.
- Повторный запуск `install.py` сообщает об установленном пакете и не перезаписывает существующий конфиг.
- `update.py` не затрагивает данные пользователя.

### 10.7. Shell completion

Для CLI-инструментов с большим количеством команд и аргументов рекомендуется добавить генерацию автодополнения для оболочки.

**PowerShell** - через `Register-ArgumentCompleter`. Если используется `argparse`, завершения генерируются через встроенную поддержку Python (требуется Python >= 3.13) или через пакет `argcomplete` (для Python >= 3.12). Пример регистрации:

```powershell
Register-ArgumentCompleter -CommandName tool-name -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    # логика автодополнения
}
```

Для постоянного использования добавить в PowerShell profile:

```powershell
Add-Content -Path $PROFILE -Value "Register-ArgumentCompleter -CommandName tool-name -ScriptBlock { }"
```

**cmd** - автодополнение через `argcomplete` не поддерживается нативно.

### 10.8. Синхронизация параметров приложения при обновлении

Скрипт `update.py` автоматически синхронизирует параметры приложения при обновлении (раздел 6.7). Остальные параметры конфига не затрагиваются.

**Алгоритм:**

1. Прочитать `name` и `version` из dev-конфига (секция `[app]`, файл `config/config.ini` или `config/config.ini.example` в архиве/репозитории)
2. Прочитать `name` и `version` из prod-конфига (секция `[app]`, файл `$env:APPDATA\tool-name\config\config.ini`)
3. Для каждого параметра: если значения отличаются - обновить в prod и вывести в консоль старое и новое значение
4. Если все значения совпадают - ничего не делать

**Правила:**

- Синхронизируются параметры `name` и `version` в секции `[app]` - никаких других изменений в конфиге
- Пользовательские настройки никогда не перезаписываются
- Для добавления новых секций и параметров пользователь обновляет prod-конфиг вручную или через агента
- Для `.env` изменений не производится - новые переменные пользователь добавляет вручную
