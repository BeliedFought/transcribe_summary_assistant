# Деплой Python-проекта на Linux (overlay). Версия 4.9.0. 2026-07-21

OS-overlay к `deploy_standards.md` (общее ядро). Применяется вместе с ядром и `project_standards.md` для установки проекта как системного инструмента на Linux. Документ содержит только Linux-специфику; общие правила деплоя - в ядре.

Установка выполняется напрямую на целевой Linux-машине: `uv tool install .` из корня репозитория. Агент имеет полный доступ к репозиторию и целевой машине.

---

## Оглавление

**1. Поток и пути:** 1.01 Поток установки - 1.02 PROJECT_ROOT установленного режима

**2. Установочные скрипты:** 2.01 Скрипты run/deploy - 2.02 Блок диагностики для ИИ-агента - 2.03 install.py - 2.04 update.py - 2.05 Логика install.py - 2.06 Логика update.py

**3. Платформа:** 3.01 uv - 3.02 Shell completion - 3.03 Дополнения к .gitignore - 3.04 Итоговая структура - 3.05 Синхронизация версии и параметров - 3.06 Чек-лист OS-специфичных пунктов

---

## 1.01. Поток установки

Установка выполняется на целевой Linux-машине из корня репозитория:

```bash
uv tool install .
```

Флаг `--force` применяется только при обновлении (раздел 2.06). Сборка wheel выполняется `uv` автоматически из `pyproject.toml`.

---

## 1.02. PROJECT_ROOT установленного режима

В установленном режиме `PROJECT_ROOT` указывает на каталог данных пользователя по XDG: `XDG_CONFIG_HOME / "tool-name"` (по умолчанию `~/.config/tool-name/`).

Полный пример `src/config.py` для установки на Linux:

```python
"""
Общий модуль загрузки конфигурации проекта.

Загружает config/config.ini и .env относительно PROJECT_ROOT.
В режиме разработки PROJECT_ROOT - корень репозитория.
В установленном режиме - ~/.config/tool-name/.
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
        # expanduser() нужен только для дефолта "~/.config";
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

Заменить `tool-name` на фактическое имя инструмента.

---

## 2.01. Скрипты run/deploy

| Скрипт | Назначение |
|--------|------------|
| `run/deploy/install.py` | Первичная установка инструмента |
| `run/deploy/update.py` | Обновление установленного инструмента |

---

## 2.02. Блок диагностики для ИИ-агента

Каждый скрипт начинается с блока комментариев-инструкций (правила - в ядре, раздел 3.02).

**Шаблон блока для install.py** (заменить `tool-name` на имя инструмента, `package-name` на имя пакета из `pyproject.toml`):

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

**Шаблон блока для update.py** (заменить `tool-name` и список файлов):

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

---

## 2.03. install.py

Файл `run/deploy/install.py`. В начале разместить блок диагностики из раздела 2.02, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 2.02 ...

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

---

## 2.04. update.py

Файл `run/deploy/update.py`. В начале разместить блок диагностики из раздела 2.02, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 2.02 ...

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

---

## 2.05. Логика install.py - первая установка

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, не установлен ли уже пакет. Если установлен - сообщить и завершить (для обновления использовать `run/deploy/update.py`).
3. Установить пакет (`uv tool install .`).
4. Создать каталог данных (`~/.config/tool-name/`) с подкаталогами `config/` и `log/`.
5. Скопировать шаблон конфига - только если файл отсутствует.
6. Скопировать `.env` - только если файл отсутствует.
7. Проверить, что команда доступна в PATH.

---

## 2.06. Логика update.py - обновление

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, что пакет установлен. Если не установлен - сообщить и завершить (для установки использовать `run/deploy/install.py`).
3. Очистить кэш: `uv cache clean tool-name`. Без этого при неизменной версии в `pyproject.toml` команда `uv tool install . --force` установит кэшированный wheel вместо пересборки из текущих исходников - изменения кода не попадут в установленный пакет.
4. Синхронизировать версию между `pyproject.toml` и `config/config.ini` (dev-конфиг): прочитать `version` из обоих источников, сравнить по SemVer и привести к более высокому значению (раздел 3.05).
5. Переустановить пакет: `uv tool install . --force`.
6. Синхронизировать параметры приложения: прочитать `name` и `version` из секции `[app]` dev-конфига и prod-конфига; если отличаются - обновить в prod и вывести в консоль старое и новое значение для каждого измененного параметра. Другие параметры конфига не затрагиваются.

---

## 3.01. uv

`uv` - единственный инструмент для установки. Он устанавливает пакет в изолированный venv, не затрагивая систему. Команда `uv tool install .` использует `pyproject.toml` в корне проекта.

**Установка uv:**

```bash
sudo pacman -S uv
```

Установочные скрипты проверяют наличие `uv` до начала работы и завершаются с сообщением об установке, если `uv` не найден.

---

## 3.02. Shell completion

*Опционально - для CLI с большим количеством команд и аргументов.*

Для CLI-инструментов с большим количеством команд и аргументов рекомендуется добавить генерацию автодополнения для оболочки. Если используется `argparse`, завершения генерируются через встроенную поддержку Python (требуется Python >= 3.13, доступно в 3.14+) или через пакет `argcomplete` (для Python >= 3.12). Пример регистрации:

```bash
eval "$(register-python-argcomplete tool-name)"
```

Для bash добавить в `~/.bashrc`. Документировать в README проекта.

---

## 3.03. Дополнения к .gitignore

При подготовке проекта к деплою добавить в `.gitignore`:

```
*.egg-info/
dist/
build/
```

Это артефакты сборки, которые создает setuptools при установке. Они не должны попадать в репозиторий.

---

## 3.04. Итоговая структура после установки

```
Код:        site-packages/tool_name/   (или изолированный venv через uv)
Команда:    ~/.local/bin/command
Конфиг:     ~/.config/tool-name/config/config.ini
Секреты:    ~/.config/tool-name/.env
Логи:       ~/.config/tool-name/log/
```

Исходный репозиторий становится независимым от установленного инструмента - его можно удалять, перезаписывать, клонировать заново.

---

## 3.05. Синхронизация версии и параметров при обновлении

Скрипт `update.py` выполняет два этапа синхронизации (раздел 2.06):

**Этап 1 - синхронизация версии в репозитории (до установки).** Устраняет расхождение между двумя источниками версии внутри репозитория: `pyproject.toml` (поле `version`) и `config/config.ini` (параметр `version` секции `[app]`). Сравнивает значения по SemVer, берет более высокое и записывает в тот источник, где версия ниже. Выполняется до `uv tool install --force`, чтобы метаданные пакета и runtime-конфиг были согласованы с момента установки.

**Этап 2 - синхронизация параметров приложения (после установки).** Переносит `name` и `version` из dev-конфига репозитория в prod-конфиг пользователя (`~/.config/tool-name/config/config.ini`).

**Правила:**

- Синхронизируются параметры `name` и `version` в секции `[app]` - никаких других изменений в конфиге
- Пользовательские настройки никогда не перезаписываются
- Для добавления новых секций и параметров пользователь обновляет prod-конфиг вручную или через агента
- Для `.env` изменений не производится - новые переменные пользователь добавляет вручную

---

## 3.06. Чек-лист OS-специфичных пунктов (Linux)

К общему чек-листу (ядро, раздел 5.04) добавить:

1. Установочные скрипты (`run/deploy/install.py`, `run/deploy/update.py`) используют корректное `TOOL_NAME`.
2. `.gitignore` содержит `*.egg-info/`, `dist/`, `build/`.
3. Тестовая установка и запуск на чистой машине прошли успешно.
4. Подмена `PROJECT_ROOT` использует корректное имя инструмента и XDG-путь.
