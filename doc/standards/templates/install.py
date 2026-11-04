#!/usr/bin/env python3
"""
First-time package installation script (run/deploy/install.py).

Installs the CLI tool into an isolated uv environment and initializes the
user configuration directory (APP_DIR) with config.ini, .env (mode 0600),
and translations.json.

Substitute platform-specific constants (<OS_CONFIG_ENV>, <OS_CONFIG_DEFAULT>,
<UV_INSTALL_HINT>, <PATH_HINT>, and TOOL_NAME) according to the target OS
overlay standard (deploy_lin_standards.md or deploy_win_standards.md).
"""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# AI-AGENT DIAGNOSTIC BLOCK (standard deploy_standards.md, 03.02)
# Activation: the user tags this file without explanation.
# Check: `uv tool list` contains TOOL_NAME in the first column; installed sources match the repository.
# Result: install when missing, update when stale, report "up to date" otherwise.
# Concrete platform commands: deploy_lin_standards.md / deploy_win_standards.md.

# Platform constants: replace placeholders using the target OS overlay table
SCRIPT_DIR = Path(__file__).resolve().parent
# Repository deploy (run/deploy/install.py): repo root is two levels up.
# Windows archive scenario: the script sits in the archive root; set PROJECT_ROOT = SCRIPT_DIR.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_NAME = "tool-name"
APP_DIR = (
    Path(os.environ.get("<OS_CONFIG_ENV>", "<OS_CONFIG_DEFAULT>")).expanduser()
    / TOOL_NAME
)
UV_INSTALL_HINT = "<UV_INSTALL_HINT>"
PATH_HINT = "<PATH_HINT>"


def _check_uv() -> None:
    """Ensure uv is available on PATH."""
    if not shutil.which("uv"):
        print(f"uv не найден. {UV_INSTALL_HINT}", flush=True)
        sys.exit(1)


def _check_pyproject() -> dict[str, object]:
    """Ensure pyproject.toml exists and is valid TOML."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"pyproject.toml не найден в корне проекта", flush=True)
        sys.exit(1)
    try:
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        print(f"Ошибка чтения pyproject.toml: {exc}", flush=True)
        sys.exit(1)


def _ensure_data_dirs() -> None:
    """Create application data, config, and log directories."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "config").mkdir(exist_ok=True)
    (APP_DIR / "log").mkdir(exist_ok=True)


def _copy_if_missing(src: Path, dst: Path) -> None:
    """Copy template file src to dst only if dst does not already exist."""
    if dst.exists():
        return
    if not src.exists():
        print(f"Шаблон не найден: {src}", flush=True)
        return
    shutil.copy2(src, dst)


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


def main() -> None:
    """Run first-time tool installation."""
    _check_pyproject()
    _check_uv()
    if _is_tool_installed():
        print(
            f"Пакет '{TOOL_NAME}' уже установлен. Для обновления: python run/deploy/update.py",
            flush=True,
        )
        return
    try:
        subprocess.run(["uv", "tool", "install", "."], cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Ошибка установки пакета: {exc}", flush=True)
        sys.exit(1)
    _ensure_data_dirs()
    _copy_if_missing(
        PROJECT_ROOT / "config" / "config.ini.example",
        APP_DIR / "config" / "config.ini",
    )
    _copy_if_missing(PROJECT_ROOT / ".env.example", APP_DIR / ".env")
    # Set 0600 permissions on .env upon creation and after any update
    env_file = APP_DIR / ".env"
    if env_file.exists():
        env_file.chmod(0o600)
    _copy_translations()
    cmd_path = shutil.which(TOOL_NAME)
    if cmd_path:
        print(f"Команда '{TOOL_NAME}' доступна: {cmd_path}", flush=True)
    else:
        print(
            f"Команда установлена, но не найдена в PATH. Добавьте {PATH_HINT} в PATH или перезапустите оболочку",
            flush=True,
        )


if __name__ == "__main__":
    main()
