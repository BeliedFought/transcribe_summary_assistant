"""
Project configuration loader.

Loads config/config.ini and .env relative to PROJECT_ROOT.
In development mode, PROJECT_ROOT is the repository root (parent of src/).
For deployed CLI tools, uncomment the appropriate platform block below.

Usage:
    from src.config import (
        APP_NAME,
        APP_VERSION,
        CONFIG_PATH,
        ENV_PATH,
        PROJECT_ROOT,
        config,
    )

    db_server = config.get("db", "server")
    output_dir = Path(config.get("paths", "output_folder"))
"""

import configparser
import os
from pathlib import Path

from dotenv import load_dotenv

# Standard development mode: repository root (parent directory of src/)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# --- Deploy mode: Linux XDG ---
# _repo_root = Path(__file__).resolve().parent.parent
# if (_repo_root / ".git").exists():
#     PROJECT_ROOT = _repo_root
# else:
#     # expanduser() handles the default "~/.config"; custom XDG_CONFIG_HOME is already absolute
#     PROJECT_ROOT = (
#         Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
#         / "tool-name"
#     )

# --- Deploy mode: Windows AppData ---
# _repo_root = Path(__file__).resolve().parent.parent
# if (_repo_root / ".git").exists():
#     PROJECT_ROOT = _repo_root
# else:
#     PROJECT_ROOT = (
#         Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
#         / "tool-name"
#     )

# Load .env secrets without overriding existing environment variables
ENV_PATH: Path = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=False)

# Load config/config.ini
CONFIG_PATH: Path = PROJECT_ROOT / "config" / "config.ini"
config = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
if CONFIG_PATH.exists():
    config.read(CONFIG_PATH, encoding="utf-8")

APP_NAME: str = config.get("app", "name", fallback="")
APP_VERSION: str = config.get("app", "version", fallback="dev")
