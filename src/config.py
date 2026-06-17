"""
Загрузка конфигурации проекта.

Загружает config/config.ini и .env относительно PROJECT_ROOT.
PROJECT_ROOT определяется как родительская папка папки src/.

Использование:
    from src.config import config, PROJECT_ROOT, APP_NAME, APP_VERSION
    model = config.get("whisper", "model_size")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    output_dir = Path(config.get("paths", "output_folder"))
"""

import configparser
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)

config = configparser.ConfigParser(interpolation=None)
_config_file = PROJECT_ROOT / "config" / "config.ini"
if _config_file.exists():
    config.read(_config_file, encoding="utf-8")

APP_NAME: str = config.get("app", "name", fallback="")
APP_VERSION: str = config.get("app", "version", fallback="dev")
