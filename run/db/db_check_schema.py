"""
Проверка соответствия схемы БД.

Читает DDL из sql/schema.sql, проверяет наличие
всех таблиц и колонок в SQLite.
"""

import re
import sqlite3
import sys

from src.config import PROJECT_ROOT, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t
from src.startup import validate_startup
from tabulate import tabulate

logger = get_logger("db_check_schema", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")
validate_startup(logger)


def _parse_schema_tables() -> dict[str, set[str]]:
    """Извлечь список таблиц и колонок из sql/schema.sql."""
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    content = schema_path.read_text(encoding="utf-8")
    tables: dict[str, set[str]] = {}
    pattern = r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\)\s*;"
    for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        table_name = match.group(1)
        body = match.group(2)
        columns: set[str] = set()
        col_pattern = r"(\w+)\s+(?:TEXT|INTEGER|REAL|BLOB|TIMESTAMP)"
        for col_match in re.finditer(col_pattern, body, re.IGNORECASE):
            columns.add(col_match.group(1).lower())
        tables[table_name] = columns
    return tables


def main() -> None:
    from src.db_manager import verify_schema

    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    db_path = PROJECT_ROOT / "data" / "sessions.db"

    if not db_path.exists():
        logger.warning(t("msg.db_not_exists"))
        sys.exit(1)

    expected_tables = _parse_schema_tables()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    schema_ok, problems = verify_schema(conn)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    missing_problems = {p.split(":", 1)[1] for p in problems if p.startswith("missing_table:")}
    table_data: list[list[str]] = []

    for table_name in sorted(expected_tables.keys()):
        if table_name in missing_problems:
            table_data.append([table_name, "MISSING", "-"])
            continue
        cols_problem = next(
            (p for p in problems if p.startswith(f"missing_columns:{table_name}:")),
            None,
        )
        missing_cols = cols_problem.split(":", 2)[2] if cols_problem else "-"
        status = "OK" if cols_problem is None else "MISMATCH"
        table_data.append([table_name, status, missing_cols])

    conn.close()

    result_text = tabulate(
        table_data,
        headers=[t("label.table"), t("label.status"), t("label.missing_columns")],
        tablefmt="grid",
        colalign=("left", "left", "left"),
    )
    logger.info(result_text)

    if schema_ok:
        logger.info(t("msg.schema_ok"))
    else:
        logger.warning(t("msg.schema_mismatch_warning"))


if __name__ == "__main__":
    main()
