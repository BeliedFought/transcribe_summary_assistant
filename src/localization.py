"""
Мультиязычность (i18n).

Все выводы приложения проходят через функцию t(key, **kwargs).
Строковые литералы на естественном языке в коде запрещены.

Хранилище: таблица translations в SQLite (key + lang composite PK).
Fallback: текущии язык -> язык по умолчанию -> en -> !KEY!.

Именование ключей: иерархическое с точкой-разделителем.
Пространства: msg.*, error.*, prompt.*, label.*, menu.*, title.*, help.*.

Плюрализация: суффиксы .zero, .one, .few, .many.
Выбор формы по правилам языка при указании count.

Определение языка (приоритет):
1. config.ini [app] language
2. Переменная окружения LANGUAGE
3. Системная локаль
4. en по умолчанию

Использование:
    from src.localization import init, t
    init()
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))
"""

import locale
import os
import sqlite3
from pathlib import Path

_translations: dict[str, str] = {}
_current_lang: str = "ru"
_default_lang: str = "ru"
_db_path: Path | None = None

_PLURAL_FORMS_RU: dict[int, str] = {
    0: "zero",
    1: "one",
    2: "few",
    5: "many",
}

_PLURAL_FORMS_EN: dict[int, str] = {
    0: "zero",
    1: "one",
    2: "many",
}


def _get_plural_form(lang: str, count: int) -> str:
    """Определить форму плюрализации для числа в зависимости от языка."""
    if lang == "ru":
        n = abs(count) % 100
        if n % 10 == 1 and n % 100 != 11:
            return _PLURAL_FORMS_RU[1]
        if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return _PLURAL_FORMS_RU[2]
        if n % 10 == 0 or n % 100 >= 5 and n % 100 <= 20:
            return _PLURAL_FORMS_RU[5]
        return _PLURAL_FORMS_RU[5]
    else:
        if count == 0:
            return _PLURAL_FORMS_EN[0]
        if count == 1:
            return _PLURAL_FORMS_EN[1]
        return _PLURAL_FORMS_EN[2]


def _detect_language() -> str:
    """Определить язык интерфейса."""
    try:
        from src.config import config as _cfg
        lang = _cfg.get("app", "language", fallback="")
        if lang:
            return lang
    except (ImportError, Exception):
        pass

    env_lang = os.environ.get("LANGUAGE", "")
    if env_lang:
        return env_lang[:2].lower()

    try:
        sys_locale = locale.getdefaultlocale()[0]
        if sys_locale:
            return sys_locale[:2].lower()
    except (ValueError, Exception):
        pass

    return "en"


def _load_from_db() -> dict[str, str]:
    """Загрузить переводы из SQLite."""
    if _db_path is None or not _db_path.exists():
        return {}

    result: dict[str, str] = {}
    try:
        conn = sqlite3.connect(str(_db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value FROM translations WHERE lang = ?",
            (_current_lang,),
        )
        for row in cursor.fetchall():
            result[row[0]] = row[1]
        conn.close()
    except sqlite3.Error:
        return {}

    if _current_lang != _default_lang:
        try:
            conn = sqlite3.connect(str(_db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, value FROM translations WHERE lang = ?",
                (_default_lang,),
            )
            for row in cursor.fetchall():
                key = row[0]
                if key not in result:
                    result[key] = row[1]
            conn.close()
        except sqlite3.Error:
            pass

    if _current_lang != "en" and _default_lang != "en":
        try:
            conn = sqlite3.connect(str(_db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, value FROM translations WHERE lang = 'en'",
            )
            for row in cursor.fetchall():
                key = row[0]
                if key not in result:
                    result[key] = row[1]
            conn.close()
        except sqlite3.Error:
            pass

    return result


def init(language: str | None = None, db_path: Path | None = None) -> None:
    """
    Инициализировать модуль локализации.

    :param language: код языка (если None - автоопределение)
    :param db_path: путь к SQLite с таблицей translations
    """
    global _current_lang, _translations, _db_path

    if language is not None:
        _current_lang = language[:2].lower()
    else:
        _current_lang = _detect_language()

    if db_path is not None:
        _db_path = db_path
    else:
        try:
            from src.config import PROJECT_ROOT
            _db_path = PROJECT_ROOT / "data" / "sessions.db"
        except (ImportError, Exception):
            _db_path = Path("data") / "sessions.db"

    _translations = _load_from_db()


def t(key: str, *, count: int | None = None, **kwargs: object) -> str:
    """
    Получить перевод по ключу.

    :param key: ключ перевода (иерархический, с точкой-разделителем)
    :param count: количество для плюрализации
    :param kwargs: параметры для интерполяции
    :return: строка перевода
    """
    if count is not None:
        form = _get_plural_form(_current_lang, count)
        plural_key = f"{key}.{form}"
        if plural_key in _translations:
            key = plural_key
        else:
            default_form = _get_plural_form(_default_lang, count)
            default_plural_key = f"{key}.{default_form}"
            if default_plural_key in _translations:
                key = default_plural_key

    text = _translations.get(key)
    if text is None:
        text = f"!{key}!"

    fmt_kwargs = {k: ("" if v is None else v) for k, v in kwargs.items()}
    if count is not None and "count" not in fmt_kwargs:
        fmt_kwargs["count"] = count

    try:
        return text.format(**fmt_kwargs)
    except (KeyError, ValueError, IndexError):
        return text


def reload(language: str | None = None, db_path: Path | None = None) -> None:
    """
    Перезагрузить словарь переводов.

    :param language: новый код языка (если None - без изменений)
    :param db_path: новый путь к БД (если None - без изменений)
    """
    init(language=language or _current_lang, db_path=db_path or _db_path)
