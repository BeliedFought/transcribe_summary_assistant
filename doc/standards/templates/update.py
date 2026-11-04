#!/usr/bin/env python3
"""
Package update and configuration migration script (run/deploy/update.py).

Synchronizes SemVer across pyproject.toml, config/config.ini, and
config/config.ini.example; cleans the uv cache for the package; reinstalls
the package via `uv tool install . --force`; updates translations.json; and
migrates production config.ini and .env while preserving user values and
creating timestamped backups.

Substitute platform-specific constants (<OS_CONFIG_ENV>, <OS_CONFIG_DEFAULT>,
<UV_INSTALL_HINT>, <PATH_HINT>, and TOOL_NAME) according to the target OS
overlay standard (deploy_lin_standards.md or deploy_win_standards.md).
"""

import configparser
import os
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path

# AI-AGENT DIAGNOSTIC BLOCK (standard deploy_standards.md, 03.02)
# Activation: the user tags this file without explanation.
# Check: `uv tool list` contains TOOL_NAME in the first column; installed sources match the repository.
# Result: update when stale, install when missing, report "up to date" otherwise.
# Concrete platform commands: deploy_lin_standards.md / deploy_win_standards.md.

# Platform constants: replace placeholders using the target OS overlay table
SCRIPT_DIR = Path(__file__).resolve().parent
# Repository deploy (run/deploy/update.py): repo root is two levels up.
# Windows archive scenario: the script sits in the archive root; set PROJECT_ROOT = SCRIPT_DIR.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
APP_DIR = (
    Path(os.environ.get("<OS_CONFIG_ENV>", "<OS_CONFIG_DEFAULT>")).expanduser()
    / TOOL_NAME
)
UV_INSTALL_HINT = "<UV_INSTALL_HINT>"
PATH_HINT = "<PATH_HINT>"

_BAK_STAMP = "%Y-%m-%d_%H-%M"
_SECTION_RE = re.compile(r"^\[(.+)\]\s*$")
_INI_KEY_RE = re.compile(r"^([^#;=\s][^=]*?)\s*=(.*)$")
_ENV_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")


def _make_parser() -> configparser.ConfigParser:
    """Create a ConfigParser instance that strips inline comments."""
    return configparser.ConfigParser(inline_comment_prefixes=(";", "#"))


def _strip_inline_comment(raw_value: str) -> str:
    """Extract INI value before any inline comment (; or #)."""
    stripped = raw_value.lstrip()
    if stripped.startswith((";", "#")):
        return ""
    return re.split(r"\s+[;#]", stripped, maxsplit=1)[0].strip()


def _check_uv() -> None:
    """Ensure uv is available on PATH."""
    if not shutil.which("uv"):
        print(f"uv не найден. {UV_INSTALL_HINT}", flush=True)
        sys.exit(1)


def _check_pyproject() -> None:
    """Ensure pyproject.toml exists in PROJECT_ROOT."""
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        print(f"pyproject.toml не найден в корне проекта", flush=True)
        sys.exit(1)


def _ensure_data_dirs() -> None:
    """Create application data, config, and log directories."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "config").mkdir(exist_ok=True)
    (APP_DIR / "log").mkdir(exist_ok=True)


def _copy_translations() -> None:
    """Copy translations.json from repository into APP_DIR/config/."""
    src = PROJECT_ROOT / "config" / "translations.json"
    if not src.exists():
        print(f"Шаблон не найден: {src}", flush=True)
        return
    shutil.copy2(src, APP_DIR / "config" / "translations.json")


def _is_tool_installed(tool_output: str | None = None) -> bool:
    """
    Check whether TOOL_NAME is installed according to `uv tool list`.

    Matches only the exact package name in the first column of non-indented
    lines (ignoring indented `- binary` lines and substring matches).
    """
    if tool_output is None:
        result = subprocess.run(
            ["uv", "tool", "list"], capture_output=True, text=True, check=False
        )
        tool_output = result.stdout
    return any(
        line and not line[0].isspace() and line.split()[0] == TOOL_NAME
        for line in tool_output.splitlines()
    )


def _pyproject_meta() -> tuple[str, str]:
    """Read [project] name and version from pyproject.toml using tomllib."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        return TOOL_NAME, "dev"
    text = pyproject_path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(text)
        project = data.get("project", {})
        if isinstance(project, dict):
            name = str(project.get("name") or TOOL_NAME)
            version = str(project.get("version") or "dev")
            return name, version
    except tomllib.TOMLDecodeError:
        pass
    name_match = re.search(r'^name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    ver_match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return (
        name_match.group(1) if name_match else TOOL_NAME,
        ver_match.group(1) if ver_match else "dev",
    )


def _pyproject_version() -> str:
    """Return [project] version from pyproject.toml."""
    _, version = _pyproject_meta()
    return version


def _semver_key(value: str) -> tuple[int, ...] | None:
    """Parse numeric SemVer string 'X.Y.Z' into an integer tuple for comparison."""
    parts = value.strip().split(".")
    if not parts or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _with_app_values(text: str, name: str, version: str) -> str:
    """
    Return INI text with [app] name and version set to the provided values.

    If [app] exists but is missing name or version, inserts the missing keys
    at the end of the [app] section. If [app] is absent altogether, prepends
    an [app] section with name and version.
    """
    out: list[str] = []
    section = ""
    saw_app = False
    wrote_name = False
    wrote_version = False

    def _flush_missing_app_keys() -> None:
        nonlocal wrote_name, wrote_version
        if wrote_name and wrote_version:
            return
        trailing_blanks: list[str] = []
        while out and not out[-1].strip():
            trailing_blanks.append(out.pop())
        if not wrote_name:
            out.append(f"name = {name}")
            wrote_name = True
        if not wrote_version:
            out.append(f"version = {version}")
            wrote_version = True
        while trailing_blanks:
            out.append(trailing_blanks.pop())

    for line in text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            if section == "app":
                _flush_missing_app_keys()
            section = section_match.group(1).strip()
            if section == "app":
                saw_app = True
            out.append(line)
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section == "app":
            key = key_match.group(1).strip()
            if key == "name":
                out.append(f"name = {name}")
                wrote_name = True
                continue
            if key == "version":
                out.append(f"version = {version}")
                wrote_version = True
                continue
        out.append(line)

    if section == "app":
        _flush_missing_app_keys()

    if not saw_app:
        prefix = [
            "[app]",
            f"name = {name}",
            f"version = {version}",
        ]
        if out and out[0].strip():
            prefix.append("")
        out = prefix + out

    return "\n".join(out) + "\n"


def _read_app_info() -> tuple[str, str]:
    """Read application name and version from config.ini, config.ini.example, or pyproject.toml."""
    default_name, default_version = _pyproject_meta()
    parser = _make_parser()
    for candidate in (
        PROJECT_ROOT / "config" / "config.ini",
        PROJECT_ROOT / "config" / "config.ini.example",
    ):
        if candidate.exists():
            parser.read(candidate, encoding="utf-8")
            if parser.has_section("app"):
                name = parser.get("app", "name", fallback="").strip() or default_name
                version = (
                    parser.get("app", "version", fallback="").strip()
                    or default_version
                )
                return name, version
    return default_name, default_version


def _ensure_dev_config() -> None:
    """Create dev config/config.ini from config.ini.example if missing."""
    dst = PROJECT_ROOT / "config" / "config.ini"
    src = PROJECT_ROOT / "config" / "config.ini.example"
    if dst.exists() or not src.exists():
        return
    pkg_name, pkg_version = _pyproject_meta()
    text = src.read_text(encoding="utf-8")
    dst.write_text(
        _with_app_values(text, pkg_name, pkg_version), encoding="utf-8"
    )
    print(f"Создан dev-конфиг: {dst}", flush=True)


def _sync_version() -> None:
    """Synchronize SemVer across pyproject.toml, config.ini, and config.ini.example."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    ini_paths = [
        PROJECT_ROOT / "config" / "config.ini",
        PROJECT_ROOT / "config" / "config.ini.example",
    ]
    versions: dict[str, str] = {}
    pkg_name, pkg_version = _pyproject_meta()
    if pyproject.exists():
        versions["pyproject"] = pkg_version
    for path in ini_paths:
        if path.exists():
            parser = _make_parser()
            parser.read(path, encoding="utf-8")
            if parser.has_section("app"):
                versions[str(path)] = parser.get("app", "version", fallback="dev")
    numeric = {
        key: value
        for key, value in versions.items()
        if _semver_key(value) is not None
    }
    if not numeric:
        print(f"Версии нечисловые - синхронизация пропущена", flush=True)
        return
    target = max(numeric.values(), key=lambda value: _semver_key(value) or ())
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
        parser = _make_parser()
        parser.read(path, encoding="utf-8")
        name = parser.get("app", "name", fallback="").strip() or pkg_name
        path.write_text(
            _with_app_values(path.read_text(encoding="utf-8"), name, target),
            encoding="utf-8",
        )
    print(f"Версия синхронизирована: {target}", flush=True)


def _ini_structure(text: str) -> dict[str, set[str]]:
    """Extract mapping of section names to key sets from INI text."""
    structure: dict[str, set[str]] = {}
    section = ""
    for line in text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1).strip()
            structure.setdefault(section, set())
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section:
            structure[section].add(key_match.group(1).strip())
    return structure


def _env_keys(text: str) -> list[str]:
    """Extract ordered list of environment variable names from .env text."""
    keys: list[str] = []
    for line in text.splitlines():
        key_match = _ENV_KEY_RE.match(line.strip())
        if key_match:
            keys.append(key_match.group(1))
    return keys


def _rebuild_ini(example_text: str, old_text: str, name: str, version: str) -> str:
    """
    Rebuild config.ini following example_text structure while preserving user values.

    Inline comments on value lines are stripped so values stay clean, and
    [app] name and version are guaranteed to be present and updated.
    """
    old_values: dict[str, dict[str, str]] = {}
    section = ""
    for line in old_text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1).strip()
            continue
        key_match = _INI_KEY_RE.match(line)
        if key_match and section:
            old_values.setdefault(section, {})[key_match.group(1).strip()] = (
                _strip_inline_comment(key_match.group(2))
            )
    out: list[str] = []
    section = ""
    for line in example_text.splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            section = section_match.group(1).strip()
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
                value = _strip_inline_comment(key_match.group(2))
            out.append(f"{key} = {value}")
            continue
        out.append(line)
    return _with_app_values("\n".join(out) + "\n", name, version)


def _rebuild_env(example_text: str, old_text: str) -> str:
    """Rebuild .env following example_text keys while preserving existing user secrets."""
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
    """Rename path to a timestamped .bak_YYYY-MM-DD_HH-MM backup file."""
    stamp = datetime.now().strftime(_BAK_STAMP)
    backup = path.with_name(f"{path.name}.bak_{stamp}")
    if backup.exists():
        backup = path.with_name(f"{path.name}.bak_{stamp}-{datetime.now():%S}")
    path.rename(backup)
    return backup


def _atomic_write(path: Path, text: str) -> None:
    """Write text to path atomically via a temporary sibling file."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _migrate_config() -> None:
    """Migrate production config.ini to match config.ini.example structure."""
    prod = APP_DIR / "config" / "config.ini"
    example = PROJECT_ROOT / "config" / "config.ini.example"
    if not example.exists():
        return
    example_text = example.read_text(encoding="utf-8")
    pkg_name, pkg_version = _pyproject_meta()
    parser = _make_parser()
    parser.read_string(example_text)
    name = parser.get("app", "name", fallback="").strip() or pkg_name
    version = parser.get("app", "version", fallback="").strip() or pkg_version
    if not prod.exists():
        _atomic_write(prod, _with_app_values(example_text, name, version))
        return
    old_text = prod.read_text(encoding="utf-8")
    if _ini_structure(old_text) == _ini_structure(example_text):
        new_text = _with_app_values(old_text, name, version)
        if new_text != old_text:
            _atomic_write(prod, new_text)
        return
    backup = _backup(prod)
    _atomic_write(prod, _rebuild_ini(example_text, old_text, name, version))
    print(f"Конфиг мигрирован, резервная копия: {backup.name}", flush=True)
    old_structure = _ini_structure(old_text)
    new_structure = _ini_structure(example_text)
    added = sorted(
        f"{section}.{key}"
        for section, keys in new_structure.items()
        for key in keys - old_structure.get(section, set())
    )
    removed = sorted(
        f"{section}.{key}"
        for section, keys in old_structure.items()
        for key in keys - new_structure.get(section, set())
    )
    if added:
        print(f"Новые ключи: {', '.join(added)}", flush=True)
    if removed:
        print(f"Ключи только в старом файле: {', '.join(removed)}", flush=True)


def _migrate_env() -> None:
    """Migrate production .env to match .env.example key set."""
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
    if set(old_keys) == set(example_keys):
        return
    backup = _backup(prod)
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
    """Verify that the package is listed in `uv tool list` and available on PATH."""
    if not _is_tool_installed():
        print(f"Пакет {TOOL_NAME} не найден после установки", flush=True)
        sys.exit(1)
    if not shutil.which(TOOL_NAME):
        print(
            f"Команда не найдена в PATH. Добавьте {PATH_HINT} в PATH",
            flush=True,
        )


def main() -> None:
    """Run package update and configuration migration."""
    name, version = _read_app_info()
    print(f"{name} v{version}", flush=True)
    _check_pyproject()
    _check_uv()
    if not _is_tool_installed():
        print(
            f"Пакет {TOOL_NAME} не установлен. Для установки: python run/deploy/install.py",
            flush=True,
        )
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
    print(f"Обновление завершено", flush=True)


if __name__ == "__main__":
    main()
