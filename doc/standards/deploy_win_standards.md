# Деплой Python-проекта на Windows (overlay). Версия 4.9.0. 2026-07-21

OS-overlay к `deploy_standards.md` (общее ядро). Применяется вместе с ядром и `project_standards.md` для установки проекта как системного инструмента на Windows. Документ содержит только Windows-специфику; общие правила деплоя - в ядре.

Документ применим для Windows 10/11 и Windows Server 2016+. Версия Windows не имеет значения - все используемые механизмы (PowerShell 5.1+, pathlib, uv) работают идентично.

**Принципиальное отличие от Linux-деплоя:** прямой доступ агента к Windows-машине отсутствует. Установка состоит из двух фаз:

1. **Подготовка на Linux (машина агента)** - сборка wheel, создание установочного ZIP-архива с инструкциями, конфигами-шаблонами и установочным скриптом. Выполняется агентом с полным доступом к репозиторию.
2. **Установка на Windows (целевая машина)** - пользователь (и администратор) распаковывают архив и выполняют инструкции. Роль агента - только подготовить пакет, максимально автоматизировать установку и снабдить пользователя понятными инструкциями.

Цель - выполнить максимум подготовительных действий на Linux-машине, чтобы на Windows-стороне требовалось минимальное количество ручных шагов.

---

## Оглавление

**1. Окружение Windows:** 1.01 Разделение ответственности - 1.02 Обращение к администратору - 1.03 Действия пользователя - 1.04 Проверка готовности - 1.05 Кодировка UTF-8

**2. Поток и пути:** 2.01 Поток установки - 2.02 PROJECT_ROOT установленного режима

**3. Подготовка пакета на Linux:** 3.01 Сборка wheel - 3.02 Структура архива - 3.03 Содержание README.txt - 3.04 Создание архива

**4. Установочные скрипты:** 4.01 Скрипты run/deploy - 4.02 Блок диагностики для ИИ-агента - 4.03 package.py - 4.04 install.py - 4.05 update.py - 4.06 Логика package.py - 4.07 Логика install.py - 4.08 Логика update.py

**5. Платформа:** 5.01 uv - 5.02 Shell completion - 5.03 Дополнения к .gitignore - 5.04 Итоговая структура - 5.05 Синхронизация параметров - 5.06 Чек-лист OS-специфичных пунктов

---

## 1.01. Разделение ответственности

Инструкции из этого раздела включаются в архив как `README.txt` (см. раздел 3.03). Пользователь и администратор выполняют их на целевой Windows-машине.

Пользователь без административных прав может установить и использовать инструмент полностью самостоятельно. Администратор нужен только для установки базового ПО на машину.

| Компонент | Кто устанавливает | Почему |
|-----------|-------------------|--------|
| Python 3.14+ | Администратор | Системный пакет, требует записи в Program Files и PATH |
| Git 2.30+ | Администратор | Системный пакет, требует запись в Program Files и PATH |
| uv | Пользователь | Устанавливается в профиль пользователя, админ не нужен |
| Кодировка UTF-8 | Администратор (опционально) | Изменение реестра для системной кодировки |
| Проект (tool-name) | Пользователь | Устанавливается из архива через `python install.py` |

Итого: пользователю нужно обратиться к администратору один раз - для установки Python и Git на машину. Все остальное пользователь делает сам из установочного архива.

---

## 1.02. Обращение к администратору

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

### 1.02.01. Опционально: кодировка UTF-8

Если в выводе программ вместо русских букв появляются символы "??????" или искажения - попросить администратора включить UTF-8 системно (добавить в текст обращения из 1.02):

> **Опционально: кодировка UTF-8**
>
> Включить UTF-8 системно:
> ```powershell
> Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage" -Name "OEMCP" -Value "65001"
> Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage" -Name "ACP" -Value "65001"
> ```
> После применения перезагрузить машину.

---

## 1.03. Действия пользователя

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

---

## 1.04. Проверка готовности окружения

Пользователь выполняет:

```powershell
python --version
uv --version
git --version
```

Все три команды должны возвращать версию без ошибок. После этого можно устанавливать проект: распаковать архив и выполнить `python install.py`.

---

## 1.05. Кодировка UTF-8

Для корректной работы с кириллицей в логах и выводе:

- **Windows Terminal** - UTF-8 поддерживается нативно, дополнительных действий не требуется
- **PowerShell** - в PowerShell 7+ UTF-8 по умолчанию. В PowerShell 5.1 при необходимости:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
  ```
- **cmd** - выполнить `chcp 65001` для переключения на UTF-8

Рекомендуется использовать Windows Terminal как основную оболочку - в нем UTF-8 работает без дополнительных настроек.

---

## 2.01. Поток установки

Установка на Windows - двухфазная (см. введение). На Linux-машине агент собирает wheel и упаковывает установочный ZIP-архив (`python run/deploy/package.py`). На Windows-машине пользователь распаковывает архив и выполняет `python install.py` (или `python update.py` для обновления). Установка из wheel: `uv tool install <wheel>`.

---

## 2.02. PROJECT_ROOT установленного режима

В установленном режиме `PROJECT_ROOT` указывает на каталог данных пользователя: `APPDATA / "tool-name"` (обычно `C:\Users\<user>\AppData\Roaming\tool-name\`).

Полный пример `src/config.py` для установки на Windows:

```python
"""
Общий модуль загрузки конфигурации проекта.

Загружает config/config.ini и .env относительно PROJECT_ROOT.
В режиме разработки PROJECT_ROOT - корень репозитория.
В установленном режиме - %APPDATA%/tool-name/.
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

Заменить `tool-name` на фактическое имя инструмента.

---

## 3.01. Сборка wheel

Из корня репозитория (на Linux-машине):

```bash
uv build
```

Команда создает wheel-файл в `dist/` (например `dist/tool_name-1.0.0-py3-none-any.whl`). Wheel содержит весь код проекта и metadata из `pyproject.toml`.

---

## 3.02. Структура архива

Архив именуется `tool-name-1.0.0-install.zip`. Внутри - каталог с плоской структурой:

```
tool-name-1.0.0-install/
├── install.py               # Установка (раздел 4.04)
├── update.py                # Обновление (раздел 4.05)
├── dist/
│   └── tool_name-1.0.0-py3-none-any.whl
├── config/
│   └── config.ini.example
├── .env.example
└── README.txt               # Инструкции (раздел 1)
```

| Файл | Источник в репозитории | Назначение |
|------|----------------------|------------|
| `install.py` | `run/deploy/install.py` | Установка из архива (Windows) |
| `update.py` | `run/deploy/update.py` | Обновление из архива (Windows) |
| `dist/*.whl` | Собирается `uv build` | Готовый пакет |
| `config/config.ini.example` | `config/config.ini.example` | Шаблон конфигурации |
| `.env.example` | `.env.example` | Шаблон секретов |
| `README.txt` | Генерируется скриптом | Инструкции для администратора и пользователя |

---

## 3.03. Содержание README.txt

Файл `README.txt` генерируется скриптом `package.py` при сборке архива. Содержит:

1. **Обращение к администратору** - текст из раздела 1.02 (установка Python, Git, опционально UTF-8)
2. **Действия пользователя** - установка uv (раздел 1.03), распаковка архива, запуск `python install.py`
3. **Проверка установки** - `tool-name --help`

Текст README генерируется из шаблона в коде `package.py`. Это гарантирует, что инструкции всегда соответствуют текущей версии проекта.

---

## 3.04. Создание архива

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

## 4.01. Скрипты run/deploy

| Скрипт | Где выполняется | Назначение |
|--------|----------------|------------|
| `run/deploy/package.py` | Linux (из репозитория) | Сборка wheel и создание ZIP-архива |
| `run/deploy/install.py` | Windows (из архива) | Первая установка из wheel |
| `run/deploy/update.py` | Windows (из архива) | Обновление из нового wheel |

Каждый скрипт выполняет только одну задачу, без аргументов командной строки и подкоманд. Скрипты `install.py` и `update.py` копируются в корень архива без изменений.

---

## 4.02. Блок диагностики для ИИ-агента

Каждый скрипт начинается с блока комментариев-инструкций (правила - в ядре, раздел 3.02).

**Шаблон блока для package.py** (заменить `tool-name`):

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

**Шаблон блока для install.py** (заменить `tool-name` и список файлов; агент не имеет прямого доступа к Windows):

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

**Шаблон блока для update.py** (заменить `tool-name` и список файлов):

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

---

## 4.03. package.py

Файл `run/deploy/package.py`. Запускается на Linux из репозитория. В начале разместить блок диагностики из раздела 4.02, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 4.02 ...

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

---

## 4.04. install.py

Файл `run/deploy/install.py`. Запускается на Windows из архива. В начале разместить блок диагностики из раздела 4.02, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 4.02 ...

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

---

## 4.05. update.py

Файл `run/deploy/update.py`. Запускается на Windows из архива. В начале разместить блок диагностики из раздела 4.02, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 4.02 ...

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

---

## 4.06. Логика package.py - сборка архива (Linux)

1. Проверить наличие `pyproject.toml` и `uv`.
2. Выполнить `uv build` - собрать wheel в `dist/`.
3. Создать временную директорию `tool-name-1.0.0-install/`.
4. Скопировать в нее: `install.py`, `update.py`, wheel из `dist/`, `config/config.ini.example`, `.env.example`.
5. Сгенерировать `README.txt` с инструкциями (текст из раздела 1).
6. Упаковать в ZIP-архив `tool-name-1.0.0-install.zip`.
7. Удалить временную директорию.
8. Архив размещается в корне репозитория.

---

## 4.07. Логика install.py - первая установка (Windows)

1. Проверить наличие `uv`.
2. Проверить, не установлен ли уже пакет. Если установлен - сообщить и завершить (для обновления использовать `update.py`).
3. Найти wheel-файл в `dist/` рядом со скриптом.
4. Установить пакет: `uv tool install <wheel>`.
5. Создать каталог данных (`$env:APPDATA\tool-name\`) с подкаталогами `config\` и `log\`.
6. Скопировать шаблон конфига - только если файл отсутствует.
7. Скопировать `.env` - только если файл отсутствует.
8. Проверить, что команда доступна в PATH.

---

## 4.08. Логика update.py - обновление (Windows)

1. Проверить наличие `uv`.
2. Проверить, что пакет установлен. Если не установлен - сообщить и завершить (для установки использовать `install.py`).
3. Очистить кэш: `uv cache clean tool-name`.
4. Найти wheel-файл в `dist/` и переустановить: `uv tool install <wheel> --force`.
5. Синхронизировать параметры приложения: прочитать `name` и `version` из секции `[app]` dev-конфига (из архива) и prod-конфига; если отличаются - обновить в prod и вывести в консоль старое и новое значение для каждого измененного параметра. Другие параметры конфига не затрагиваются.

---

## 5.01. uv

`uv` - единственный инструмент для установки. На Linux используется для сборки wheel (`uv build`). На Windows - для установки из wheel-файла: `uv tool install <wheel>`. Флаг `--force` применяется только при обновлении.

**Установка uv на Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Установочные скрипты проверяют наличие `uv` до начала работы и завершаются с сообщением об установке, если `uv` не найден.

---

## 5.02. Shell completion

*Опционально - для CLI с большим количеством команд и аргументов.*

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

---

## 5.03. Дополнения к .gitignore

При подготовке проекта к деплою добавить в `.gitignore`:

```
*.egg-info/
dist/
build/
*-install.zip
```

Артефакты сборки (setuptools) и готовые установочные архивы не должны попадать в репозиторий.

---

## 5.04. Итоговая структура после установки

```
Код:        $env:LOCALAPPDATA\uv\tools\tool-name\lib\python*\site-packages\
Команда:    $env:LOCALAPPDATA\uv\tools\tool-name\Scripts\tool-name.exe
Конфиг:     $env:APPDATA\tool-name\config\config.ini
Секреты:    $env:APPDATA\tool-name\.env
Логи:       $env:APPDATA\tool-name\log\
```

Исходный репозиторий и установочный архив не нужны для работы инструмента после установки.

---

## 5.05. Синхронизация параметров приложения при обновлении

Скрипт `update.py` автоматически синхронизирует параметры приложения при обновлении (раздел 4.08). Остальные параметры конфига не затрагиваются.

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

---

## 5.06. Чек-лист OS-специфичных пунктов (Windows)

К общему чек-листу (ядро, раздел 5.04) добавить:

1. Установочные скрипты (`run/deploy/install.py`, `run/deploy/update.py`, `run/deploy/package.py`) используют корректное `TOOL_NAME` и версию (`TOOL_VERSION` для `package.py`).
2. `.gitignore` содержит `*.egg-info/`, `dist/`, `build/`, `*-install.zip`.
3. Тестовая сборка архива (`python run/deploy/package.py`) выполнена успешно.
4. Тестовая установка из архива на целевой Windows-машине прошла успешно.
5. Подмена `PROJECT_ROOT` использует корректное имя инструмента и APPDATA-путь.
