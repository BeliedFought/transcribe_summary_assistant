"""
Инициализация БД: создание таблиц по схеме из sql/schema.sql
и заполнение таблицы translations начальными переводами.

Логика: проверка схемы. Если схема соответствует - запрос на очистку.
Если схема не соответствует - запрос на пересоздание.
"""

import re
import sqlite3
import sys

from src.config import PROJECT_ROOT, APP_NAME, APP_VERSION
from src.logger import get_logger
from src.localization import init as i18n_init, t
from src.startup import validate_startup

logger = get_logger("db_init", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")
validate_startup(logger)


def _read_schema() -> str:
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def _parse_schema_tables() -> dict[str, set[str]]:
    """Извлечь список таблиц и колонок из sql/schema.sql."""
    content = _read_schema()
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


def _insert_translations(conn: sqlite3.Connection) -> None:
    from src.db_manager import insert_initial_translations
    insert_initial_translations(conn)


def _report_status(conn: sqlite3.Connection) -> tuple[bool, bool]:
    """
    Вывести отчет о состоянии БД.

    :return: (схема_структурно_ок, переводы_заполнены)
    """
    from src.db_manager import verify_schema

    logger.info(t("msg.db_init_report"))

    schema_ok, problems = verify_schema(conn)

    missing_tables = {p.split(":", 1)[1] for p in problems if p.startswith("missing_table:")}
    mismatch_map: dict[str, str] = {}
    for p in problems:
        if p.startswith("missing_columns:"):
            _, table, cols = p.split(":", 2)
            mismatch_map[table] = cols

    expected_tables = _parse_schema_tables()
    cursor = conn.cursor()
    for table_name in sorted(expected_tables.keys()):
        if table_name == "translations":
            continue
        if table_name in missing_tables:
            logger.warning(t("msg.db_init_table_missing", table=table_name))
            continue
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        row_count = cursor.fetchone()[0]
        if table_name in mismatch_map:
            logger.warning(
                t("msg.db_init_table_mismatch", table=table_name, cols=mismatch_map[table_name])
            )
        else:
            logger.info(t("msg.db_init_table_ok", table=table_name, count=row_count))

    cursor.execute("SELECT COUNT(*) FROM translations")
    translations_count = cursor.fetchone()[0]
    logger.info(t("msg.db_init_translations", count=translations_count))

    if not schema_ok:
        logger.warning(t("msg.schema_mismatch_warning"))

    return schema_ok, translations_count > 0


def _clear_tables(conn: sqlite3.Connection) -> None:
    """Удалить все строки из таблиц схемы."""
    cursor = conn.cursor()
    for table_name in _parse_schema_tables():
        cursor.execute(f'DELETE FROM "{table_name}"')
    conn.commit()


def _recreate_tables(conn: sqlite3.Connection, schema: str) -> None:
    """Пересоздать таблицы по схеме."""
    for table_name in _parse_schema_tables():
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.commit()
    conn.executescript(schema)
    conn.commit()


def _show_menu(schema_ok: bool, translations_present: bool) -> None:
    """Вывести меню действий."""
    print(t("msg.db_init_menu_header"))
    print(f"1 - {t('menu.db_init_clear')}")
    print(f"2 - {t('menu.db_init_recreate')}")
    print(f"3 - {t('menu.db_init_fill_translations')}")
    print(f"0 - {t('menu.db_init_exit')}")


def main() -> None:
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    db_path = PROJECT_ROOT / "data" / "sessions.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema = _read_schema()
    conn = sqlite3.connect(str(db_path))

    try:
        conn.executescript(schema)
        conn.commit()

        schema_ok, translations_present = _report_status(conn)

        _show_menu(schema_ok, translations_present)
        choice = input().strip()

        if choice == "0":
            return

        if choice == "1":
            _clear_tables(conn)
            logger.info(t("msg.db_tables_cleared"))
            _insert_translations(conn)
        elif choice == "2":
            if not schema_ok:
                _recreate_tables(conn, schema)
                logger.info(t("msg.db_tables_recreated"))
                _insert_translations(conn)
            else:
                logger.warning(t("msg.db_init_recreate_unnecessary"))
                return
        elif choice == "3":
            if not translations_present:
                _insert_translations(conn)
            else:
                logger.warning(t("msg.db_init_translations_already"))
                return
        else:
            logger.warning(t("msg.db_init_unknown_choice"))
            return

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM translations")
        logger.info(t("msg.db_init_translations_filled", count=cursor.fetchone()[0]))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
