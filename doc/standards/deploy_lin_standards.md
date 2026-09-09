# Деплой Python-проекта на Linux (overlay). Версия 4.10.0

OS-overlay к `deploy_standards.md` (общее ядро). Применяется вместе с ядром и `project_standards.md` для установки проекта как системного инструмента на Linux. Документ содержит только Linux-специфику; общие правила деплоя - в ядре.

Установка выполняется напрямую на целевой Linux-машине: `uv tool install .` из корня репозитория. Агент имеет полный доступ к репозиторию и целевой машине.

---

## Оглавление

**01. Поток и пути:** 01.01 Поток установки - 01.02 PROJECT_ROOT установленного режима

**02. Установочные скрипты:** 02.01 Скрипты run/deploy - 02.02 Блок диагностики для ИИ-агента - 02.03 install.py - 02.04 update.py - 02.05 Логика install.py - первая установка - 02.06 Логика update.py - обновление

**03. Платформа:** 03.01 uv - 03.02 Shell completion - 03.03 Дополнения к .gitignore - 03.04 Итоговая структура после установки - 03.05 Синхронизация версии, конфига и .env при обновлении - 03.06 Чек-лист OS-специфичных пунктов (Linux)

**04. Связь и версионирование:** 04.01 Связь с другими документами - 04.02 Версионирование

---

## 01.01. Поток установки

*Обязательно.*

Установка выполняется на целевой Linux-машине из корня репозитория:

```bash
uv tool install .
```

Флаг `--force` применяется только при обновлении (раздел 02.06). Сборка wheel выполняется `uv` автоматически из `pyproject.toml`.

---

## 01.02. PROJECT_ROOT установленного режима

*Обязательно.*

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

## 02.01. Скрипты run/deploy

*Обязательно.*

| Скрипт | Назначение |
|--------|------------|
| `run/deploy/install.py` | Первичная установка инструмента |
| `run/deploy/update.py` | Обновление установленного инструмента |

---

## 02.02. Блок диагностики для ИИ-агента

*Обязательно.*

Каждый скрипт начинается с блока комментариев-инструкций (правила - `deploy_standards.md`, раздел 03.02).

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
# После обновления сообщить пользователю синхронизированные параметры
# и факт миграции config.ini / .env (если была).
#
# 6. Если исходники совпадают:
# - Сообщить пользователю: пакет установлен и актуален, действия не требуются
#
# Миграция конфига/.env при отличии структуры от example - алгоритм: `deploy_standards.md` (раздел 04.01)
```

---

## 02.03. install.py

*Обязательно.*

Файл `run/deploy/install.py`. В начале разместить блок диагностики из раздела 02.02, затем код:

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 02.02 ...

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
APP_DIR = XDG_CONFIG / TOOL_NAME


def _check_uv() -> None:
    if not shutil.which("uv"):
        print("uv не найден. Установите: sudo pacman -S uv (Arch) или curl -LsSf https://astral.sh/uv/install.sh | sh")
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


def _copy_translations() -> None:
    src = PROJECT_ROOT / "config" / "translations.json"
    if not src.exists():
        print(f"Шаблон не найден: {src}")
        return
    shutil.copy2(src, APP_DIR / "config" / "translations.json")


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
    _copy_translations()
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

## 02.04. update.py

*Обязательно.*

Файл `run/deploy/update.py`. В начале разместить блок диагностики из раздела 02.02.

Скрипт изолирован (`deploy_standards.md`, раздел 03.01): не импортирует из `src/`, вывод через `print(..., flush=True)`.

Обязательный порядок действий - раздел 02.06. Алгоритм миграции `config.ini` и `.env` - раздел 03.05.

Каркас (имена helpers ориентировочные; полная реализация должна покрывать раздел 02.06):

```python
#!/usr/bin/env python3
# ... блок комментариев из раздела 02.02 ...

# PROJECT_ROOT, TOOL_NAME
# XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
# APP_DIR = XDG_CONFIG / TOOL_NAME

def main() -> None:
    name, version = _read_app_info()
    print(f"{name} v{version}", flush=True)
    _check_pyproject()
    _check_uv()
    if not _is_tool_installed():
        print(f"Пакет {TOOL_NAME} не установлен. Для установки: python run/deploy/install.py", flush=True)
        return
    _ensure_dev_config()          # config.ini из example, если нет
    _sync_version()               # pyproject <-> config.ini, SemVer
    subprocess.run(["uv", "cache", "clean", TOOL_NAME], check=False)
    subprocess.run(["uv", "tool", "install", ".", "--force"], cwd=PROJECT_ROOT, check=True)
    _ensure_data_dirs()
    _copy_translations()
    _migrate_config()             # структура vs example; .bak_YYYY-MM-DD_HH-MM
    _migrate_env()                # ключи vs .env.example; .bak_YYYY-MM-DD_HH-MM
    _verify_install()
    print("Обновление завершено", flush=True)
```

Новый ini/`.env` собирать по тексту example с подстановкой значений (сохранять порядок и комментарии шаблона). Не полагаться на `ConfigParser.write()` как на единственный способ записи нового файла.

---

## 02.05. Логика install.py - первая установка

*Обязательно.*

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, не установлен ли уже пакет. Если установлен - сообщить и завершить (для обновления использовать `run/deploy/update.py`).
3. Установить пакет (`uv tool install .`).
4. Создать каталог данных (`~/.config/tool-name/`) с подкаталогами `config/` и `log/`.
5. Скопировать шаблон конфига - только если файл отсутствует.
6. Скопировать `.env` - только если файл отсутствует.
7. Скопировать `translations.json` в каталог данных (всегда из репозитория).
8. Проверить, что команда доступна в PATH.

---

## 02.06. Логика update.py - обновление

*Обязательно.*

1. Проверить наличие `pyproject.toml` и `uv`.
2. Проверить, что пакет установлен. Если не установлен - сообщить и завершить (для установки использовать `run/deploy/install.py`).
3. Если в репозитории нет `config/config.ini` - создать его копированием из `config/config.ini.example`.
4. Синхронизировать версию между `pyproject.toml` и `config/config.ini` (dev-конфиг): прочитать `version` из обоих источников, сравнить по SemVer и привести к более высокому значению (раздел 03.05). Нечисловые версии (`dev` и т.п.) - пропустить с сообщением.
5. Очистить кэш: `uv cache clean tool-name`. Без этого при неизменной версии в `pyproject.toml` команда `uv tool install . --force` установит кэшированный wheel вместо пересборки из текущих исходников - изменения кода не попадут в установленный пакет.
6. Переустановить пакет: `uv tool install . --force`.
7. Обновить `translations.json` в каталоге данных (всегда копировать из репозитория).
8. Мигрировать prod-конфиг относительно `config/config.ini.example` (раздел 03.05): сравнение по структуре (секции и ключи); при отличии - резервная копия и новый файл; при совпадении - только `app.name` / `app.version`.
9. Мигрировать prod-`.env` относительно `.env.example` (раздел 03.05): сравнение по набору ключей; при отличии - резервная копия и новый файл; при совпадении - ничего не делать.
10. Кратко проверить установку (`uv tool list`, наличие в PATH) и сообщить итог.

Вывод баннера и сообщений - через `print(..., flush=True)`, чтобы строки не перемешивались с выводом `uv`.

---

## 03.01. uv

*Обязательно.*

`uv` - единственный инструмент для установки. Он устанавливает пакет в изолированный venv, не затрагивая систему. Команда `uv tool install .` использует `pyproject.toml` в корне проекта.

**Установка uv:**

Arch Linux:

```bash
sudo pacman -S uv
```

Прочие дистрибутивы (официальный установщик uv):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Установочные скрипты проверяют наличие `uv` до начала работы и завершаются с сообщением об установке, если `uv` не найден.

---

## 03.02. Shell completion

*Опционально - для CLI с большим количеством команд и аргументов.*

Для CLI-инструментов с большим количеством команд и аргументов рекомендуется добавить генерацию автодополнения для оболочки. Если используется `argparse`, завершения генерируются через встроенную поддержку Python (требуется Python >= 3.13, доступно в 3.14+) или через пакет `argcomplete` (для Python >= 3.12). Пример регистрации:

```bash
eval "$(register-python-argcomplete tool-name)"
```

Для bash добавить в `~/.bashrc`. Документировать в README проекта.

---

## 03.03. Дополнения к .gitignore

*Обязательно.*

При подготовке проекта к деплою добавить в `.gitignore`:

```
*.egg-info/
dist/
build/
```

Это артефакты сборки, которые создает setuptools при установке. Они не должны попадать в репозиторий.

---

## 03.04. Итоговая структура после установки

```
Код:        ~/.local/share/uv/tools/tool-name/lib/python*/site-packages/tool_name/
Команда:    ~/.local/bin/tool-name
Конфиг:     ~/.config/tool-name/config/config.ini
Секреты:    ~/.config/tool-name/.env
Логи:       ~/.config/tool-name/log/
```

Исходный репозиторий становится независимым от установленного инструмента - его можно удалять, перезаписывать, клонировать заново.

---

## 03.05. Синхронизация версии, конфига и .env при обновлении

*Обязательно.*

Канон алгоритма миграции (сравнение структур, резервные копии, перенос значений, правила) - ядро `deploy_standards.md`, раздел 04.01; здесь только платформенная специфика Linux:

- Скрипт - `run/deploy/update.py` (разделы 02.04, 02.06)
- **Этап 0 - синхронизация версии в репозитории (до установки):** выполняется перед `uv tool install --force`; сравнивает `pyproject.toml` (поле `version`) и `config/config.ini` (параметр `version` секции `[app]`) по SemVer, большее значение записывается в источник с меньшим; при отсутствии `config/config.ini` - сначала создать из `config/config.ini.example`
- Источник структуры example - репозиторий (установка выполняется из его корня)
- Prod-файлы - `XDG_CONFIG_HOME/tool-name/` (по умолчанию `~/.config/tool-name/`): `config/config.ini`, `.env`
- Резервные копии и перезапись - по канону ядра (`deploy_standards.md`, раздел 04.01)

---

## 03.06. Чек-лист OS-специфичных пунктов (Linux)

*Обязательно.*

К общему чек-листу (ядро - `deploy_standards.md`, раздел 05.04) добавить:

1. Установочные скрипты (`run/deploy/install.py`, `run/deploy/update.py`) используют корректное `TOOL_NAME`.
2. `.gitignore` содержит `*.egg-info/`, `dist/`, `build/`.
3. Тестовая установка и запуск на чистой машине прошли успешно.
4. Подмена `PROJECT_ROOT` использует корректное имя инструмента и XDG-путь.

---

## 04.01. Связь с другими документами

| Документ | Связь |
|----------|-------|
| `deploy_standards.md` | Общее ядро деплоя; настоящий документ - OS-overlay, применяется вместе с ним |
| `deploy_win_standards.md` | Парный OS-overlay для Windows (та же структура скриптов, платформенная специфика) |
| `doc/standards/project_standards.md` | Основной стандарт |

---

## 04.02. Версионирование

Версионирование пакета стандартов - единое для всех документов пакета. Политика версионирования, реестр и карта маршрутизации - в `doc/standards/_index_standards.md`. Bump версии пакета - только по явному запросу пользователя (см. _index_standards.md).
