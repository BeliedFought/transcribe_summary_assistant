"""
Project logging module.

Dual-Channel Contract:
    - logger.debug/info/warning/error/exception write English technical records
      to the log file only, using lazy %-formatting:
          logger.debug("Query executed in %.2fs: %s", elapsed, query_name)
          logger.info("Connected to database: %s", db_host)
          logger.warning("Retrying request (attempt %d/%d)", attempt, max_retries)
          logger.error("Failed to process record %s: %s", record_id, err)
    - User-facing console output defaults to English and goes through
      console_message() or the report helpers; Russian is allowed through the
      locale:
          console_message(logging.INFO, t("msg.app_started", name=APP_NAME, version=APP_VERSION))

Output modes (mode parameter, canon - doc/standards/cli_output_standards.md):
    report - structured human report (default): header, key-value block,
             steps, and a final Result line; console_message prints a plain
             line without a timestamp; the log file stays plain
    plain  - clean stream: console_message prints
             "YYYY-MM-DD HH:MM:SS [marker] message" to stdout; the log file is
             English; use for logs and parsable streams
    menu   - interactive menu: the frame is rendered by src/menu.py;
             console_message is a no-op
    rich   - rich console: rendered by src/rich_console.py and
             src/console_table.py; console_message is a no-op

Color (report mode only):
    auto   - enabled when stdout is a TTY, TERM is not dumb, CI is empty,
             and NO_COLOR is unset
    always - forced on
    never  - forced off
    CLI_COLOR overrides the default; NO_COLOR and FORCE_COLOR are respected;
    --color in the CLI overrides both through the color parameter.

Log levels:
    file_level - file handler threshold from [logging] in config.ini (default: DEBUG)

The log file always records the full plain format (timestamp + marker + message)
in English, regardless of the console mode.

log_file_only(logger, message) writes an explicit record to FileHandler only;
it is kept for semantic audit events and compatibility.

Log rotation: [logging] keep_last (disabled by default) removes older log files
for the same script when creating a new log file, keeping the N most recent files.

Usage:
    from pathlib import Path

    from src.config import PROJECT_ROOT
    from src.logger import get_logger, report_header, report_kv, report_result

    logger = get_logger(Path(__file__).stem, log_dir=PROJECT_ROOT / "log")
    report_header("VPN profile")
    report_kv("Service", "openvpn-client@hm")
    report_result("UP")
    logger.info("Service initialized: %s", service_name)
"""

import configparser
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Secret key names whose values are masked in log output
SECRET_KEYS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "api_secret",
    "auth",
    "authorization",
    "bearer",
    "smtp_user",
    "smtp_password",
)

LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

MODES = ("report", "plain", "menu", "rich")
COLOR_MODES = ("auto", "always", "never")

RESULT_SUCCESS = frozenset(
    {
        "UP",
        "DEPLOYED",
        "INSTALLED",
        "BUILT",
        "ISSUED",
        "REVOKED",
        "GENERATED",
        "INITIALIZED",
    }
)
RESULT_FAILURE = frozenset({"DOWN", "FAILED"})
RESULT_SKIP = frozenset({"SKIPPED", "CHECK", "ALREADY"})


class _SecretFilter(logging.Filter):
    """Mask values of known secret keys and Bearer tokens in log messages."""

    _KV_PATTERN = re.compile(
        r"(?i)\b("
        + "|".join(re.escape(k) for k in SECRET_KEYS)
        + r")\b\s*[:=]\s*(?:(bearer|basic)\s+)?(?:\"[^\"]*\"|'[^']*'|\S+)"
    )
    _BEARER_PATTERN = re.compile(
        r"(?i)\b(bearer)\s+(?!\*\*\*)(?:\"[^\"]*\"|'[^']*'|\S+)"
    )
    _PATTERN = _KV_PATTERN

    @staticmethod
    def _replace_kv(match: re.Match[str]) -> str:
        key = match.group(1)
        scheme = match.group(2)
        if scheme:
            return f"{key}: {scheme} ***"
        return f"{key}=***"

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        masked = self._KV_PATTERN.sub(self._replace_kv, message)
        masked = self._BEARER_PATTERN.sub(r"\1 ***", masked)
        record.msg = masked
        record.args = None
        return True


class _MarkerFormatter(logging.Formatter):
    """Formatter using text markers [!], [i], [*] instead of level names."""

    MARKERS = {
        logging.ERROR: "[!]",
        logging.CRITICAL: "[!]",
        logging.WARNING: "[*]",
        logging.INFO: "[i]",
        logging.DEBUG: "[i]",
    }

    def __init__(self, *, with_prefix: bool = True) -> None:
        super().__init__()
        self._with_prefix = with_prefix

    def format(self, record: logging.LogRecord) -> str:
        marker = self.MARKERS.get(record.levelno, "[i]")
        message = record.getMessage()
        if self._with_prefix:
            timestamp = datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            return f"{timestamp} {marker} {message}"
        return message


def _read_file_level() -> int:
    """Read file_level from [logging] in config.ini (default: DEBUG)."""
    try:
        from src.config import config
    except ImportError:
        return logging.DEBUG
    try:
        level_name = config.get(
            "logging", "file_level", fallback="DEBUG"
        ).strip().upper()
        return LEVEL_MAP.get(level_name, logging.DEBUG)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return logging.DEBUG


_CONSOLE_MODE = "report"
_COLOR_MODE = "auto"


def _read_keep_last() -> int:
    """Read keep_last from [logging] in config.ini (default: 0 = disabled)."""
    try:
        from src.config import config
    except ImportError:
        return 0
    try:
        return max(0, config.getint("logging", "keep_last", fallback=0))
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        return 0


def _cleanup_old_logs(log_dir: Path, script_name: str, keep_last: int) -> None:
    """Remove stale log files for script_name, keeping the keep_last newest files."""
    if keep_last <= 0:
        return
    files = sorted(
        (p for p in log_dir.glob(f"log_{script_name}_*.log") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for stale in files[keep_last:]:
        try:
            stale.unlink()
        except OSError:
            pass


def _color_enabled(stream: object = sys.stdout) -> bool:
    """Resolve color: CLI_COLOR, NO_COLOR/FORCE_COLOR, then TTY detection."""
    if _COLOR_MODE == "always":
        return True
    if _COLOR_MODE == "never":
        return False

    env_mode = os.environ.get("CLI_COLOR", "").strip().lower()
    if env_mode == "always":
        return True
    if env_mode == "never":
        return False

    if os.environ.get("NO_COLOR"):
        return False
    force = os.environ.get("FORCE_COLOR", "")
    if force and force != "0":
        return True

    isatty = getattr(stream, "isatty", None)
    if not callable(isatty) or not isatty():
        return False
    if os.environ.get("CI"):
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return True


def _paint(text: str, code: str, stream: object = sys.stdout) -> str:
    """Wrap text in an ANSI style when color is enabled for the stream."""
    if not _color_enabled(stream):
        return text
    return f"\033[{code}m{text}\033[0m"


def get_logger(
    script_name: str,
    log_dir: Path,
    mode: str = "report",
    color: str = "auto",
) -> logging.Logger:
    """
    Create and configure a file-only logger.

    Args:
        script_name: Script identifier used in the log file name.
        log_dir: Directory path where log files are stored.
        mode: Console output mode ("report", "plain", "menu", or "rich").
        color: Color mode ("auto", "always", or "never"); the CLI --color flag
            passes its value here and overrides CLI_COLOR.

    Returns:
        Configured logging.Logger instance.
    """
    global _CONSOLE_MODE, _COLOR_MODE
    if mode not in MODES:
        mode = "report"
    if color not in COLOR_MODES:
        color = "auto"
    _CONSOLE_MODE = mode
    _COLOR_MODE = color

    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"log_{script_name}_{timestamp}.log"

    # Log rotation: [logging] keep_last (disabled by default)
    _cleanup_old_logs(log_dir, script_name, _read_keep_last())

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers on repeated calls with the same name
    if logger.handlers:
        return logger

    # Attach secret masking filter once per logger
    logger.addFilter(_SecretFilter())

    file_level = _read_file_level()

    # File handler always uses full plain format (timestamp + marker + message)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(_MarkerFormatter(with_prefix=True))
    logger.addHandler(file_handler)

    return logger


def console_message(level: int, message: str) -> None:
    """
    Print an English user-facing console line (Russian opt-in through t()).

    In report mode the line goes to stdout without a timestamp; the report
    helpers build the structured block. In plain mode the line uses the strict
    "YYYY-MM-DD HH:MM:SS [marker] message" format. In menu and rich modes the
    presentation layer renders the screen, so this function is a no-op. The log
    file is never touched here.
    """
    if _CONSOLE_MODE == "report":
        print(message, flush=True)
        return
    if _CONSOLE_MODE != "plain":
        return
    marker = _MarkerFormatter.MARKERS.get(level, "[i]")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} {marker} {message}", flush=True)


def report_header(title: str) -> None:
    """Print the report header (bold bright yellow in an interactive TTY)."""
    if _CONSOLE_MODE != "report":
        return
    print(_paint(title, "1;93"), flush=True)


def report_kv(key: str, value: str) -> None:
    """Print one key-value pair with a 16-character key column."""
    if _CONSOLE_MODE != "report":
        return
    print(f"  {_paint(f'{key:<16}', '2')}{value}", flush=True)


def report_step(index: int, total: int, key: str, value: str) -> None:
    """Print one completed step as '  [n/m] key value'."""
    if _CONSOLE_MODE != "report":
        return
    width = len(str(total))
    counter = f"{index:0{width}d}" if total >= 10 else str(index)
    print(f"  [{counter}/{total}] {_paint(f'{key:<16}', '2')}{value}", flush=True)


def report_result(value: str) -> None:
    """Print the final Result line with a semantic color role."""
    if _CONSOLE_MODE != "report":
        return
    upper = value.upper()
    if upper in RESULT_FAILURE:
        code = "31"
    elif upper in RESULT_SKIP or upper.startswith("ALREADY"):
        code = "33"
    elif upper in RESULT_SUCCESS:
        code = "32"
    else:
        code = ""
    painted = _paint(value, code) if code else value
    print(f"{'Result':<20}{painted}", flush=True)


def report_error(message: str) -> None:
    """Print 'error: <text>' to stderr; color only when stderr is a TTY."""
    if _CONSOLE_MODE != "report":
        return
    print(_paint(f"error: {message}", "31", sys.stderr), file=sys.stderr, flush=True)


def log_file_only(
    logger: logging.Logger,
    message: str,
    level: int = logging.INFO,
) -> None:
    """Write a log record only to FileHandler instances, bypassing console output."""
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=None,
        exc_info=None,
    )
    for flt in logger.filters:
        if not flt.filter(record):
            return
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.handle(record)
