"""
Project localization module for user-facing UI and console output.

Loads translations from config/translations.json (sections: meta, translations).
Fallback chain: active language -> default_lang -> !KEY!.

Usage:
    from src.localization import t

    print(t("msg.items_found", count=5))
"""

import json
import locale
import os
import threading
from typing import Any

from src.config import PROJECT_ROOT, config

_LOCK = threading.Lock()
# Global translation cache; access only via t(), init(), and reload()
_CACHE: dict[str, str] = {}
_DEFAULT_LANG = "en"
_LANG = _DEFAULT_LANG


def _detect_language() -> str:
    """Detect active language: config.ini [app] language -> LANGUAGE env -> locale -> en."""
    value = config.get("app", "language", fallback="").strip().lower()
    if value:
        return value
    env = os.environ.get("LANGUAGE", "").split(":")[0].lower()
    if env:
        return env[:2]
    try:
        code = locale.getlocale()[0] or ""
    except ValueError:
        code = ""
    return code[:2].lower() or _DEFAULT_LANG


def _load(language: str) -> None:
    """Load translation dictionary into cache with fallback to default_lang."""
    path = PROJECT_ROOT / "config" / "translations.json"
    data: dict[str, Any] = {}
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    table = data.get("translations", {})
    default_lang = data.get("meta", {}).get("default_lang", _DEFAULT_LANG)
    with _LOCK:
        global _CACHE, _LANG
        _CACHE = {
            key: value.get(language) or value.get(default_lang) or f"!{key}!"
            for key, value in table.items()
        }
        _LANG = language


def _plural_suffix(count: int) -> str:
    """Select plural form suffix ('one', 'few', 'many') for the active language."""
    if _LANG == "ru":
        if count % 10 == 1 and count % 100 != 11:
            return "one"
        if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
            return "few"
        return "many"
    return "one" if count == 1 else "many"


def t(key: str, *, count: int | None = None, **kwargs: object) -> str:
    """Return translated string for key with optional pluralization and interpolation."""
    if count is not None:
        if count == 0 and f"{key}.zero" in _CACHE:
            key = f"{key}.zero"
        else:
            plural_key = f"{key}.{_plural_suffix(count)}"
            if plural_key in _CACHE:
                key = plural_key
        kwargs.setdefault("count", count)
    text = _CACHE.get(key, f"!{key}!")
    return text.format(**kwargs) if kwargs else text


def init(language: str | None = None) -> None:
    """Initialize localization cache (called automatically on module import)."""
    _load(language or _detect_language())


def reload(language: str | None = None) -> None:
    """Reload translation cache (allows runtime language switching without restart)."""
    _load(language or _detect_language())


init()
