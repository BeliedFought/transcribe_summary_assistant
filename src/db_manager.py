"""
Работа с SQLite: управление сессиями, очередь обработки, переводы.

Использование:
    from src.db_manager import init_db, create_session, update_session
    conn = sqlite3.connect(str(db_path))
    init_db(conn)
    create_session(conn, session_data)
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import PROJECT_ROOT


def _read_schema() -> str:
    """Прочитать DDL из sql/schema.sql."""
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def _parse_schema_tables() -> dict[str, set[str]]:
    """Извлечь список таблиц и колонок из sql/schema.sql."""
    content = _read_schema()
    tables: dict[str, set[str]] = {}
    pattern = r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\)\s*;"
    col_pattern = re.compile(r"(\w+)\s+(?:TEXT|INTEGER|REAL|BLOB|TIMESTAMP)", re.IGNORECASE)
    for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        table_name = match.group(1)
        body = match.group(2)
        columns: set[str] = {m.group(1).lower() for m in col_pattern.finditer(body)}
        tables[table_name] = columns
    return tables


def verify_schema(conn: sqlite3.Connection) -> tuple[bool, list[str]]:
    """
    Проверить соответствие схемы БД ожидаемой (sql/schema.sql).

    Проверяются: наличие всех таблиц, совпадение состава колонок,
    наличие хотя бы одной строки в таблице translations.

    :return: (схема_соответствует, список_описании_проблем)
    """
    problems: list[str] = []
    expected_tables = _parse_schema_tables()

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    missing_tables = set(expected_tables.keys()) - existing_tables
    for table_name in sorted(missing_tables):
        problems.append(f"missing_table:{table_name}")

    for table_name, expected_cols in expected_tables.items():
        if table_name not in existing_tables:
            continue
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        existing_cols = {row[1].lower() for row in cursor.fetchall()}
        missing_cols = expected_cols - existing_cols
        if missing_cols:
            cols = ", ".join(sorted(missing_cols))
            problems.append(f"missing_columns:{table_name}:{cols}")

    return (len(problems) == 0, problems)


def translations_count(conn: sqlite3.Connection) -> int:
    """Вернуть количество строк в таблице translations."""
    if ("translations",) not in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall():
        return 0
    return int(conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0])


def init_db(conn: sqlite3.Connection) -> None:
    """Создать таблицы по схеме."""
    schema = _read_schema()
    conn.executescript(schema)
    _migrate_sessions_columns(conn)
    conn.commit()


def _migrate_sessions_columns(conn: sqlite3.Connection) -> None:
    """
    Дописать отсутствующие колонки таблицы sessions для существующих БД.

    CREATE TABLE IF NOT EXISTS не меняет структуру уже существующей таблицы,
    поэтому новые колонки добавляются через безопасную миграцию.
    """
    cursor = conn.execute("PRAGMA table_info(sessions)")
    existing = {row[1].lower() for row in cursor.fetchall()}
    migrations: list[tuple[str, str]] = [
        ("email_status", "TEXT"),
        ("article_path", "TEXT"),
        ("article_email_status", "TEXT"),
    ]
    for column, col_type in migrations:
        if column.lower() not in existing:
            conn.execute(f'ALTER TABLE sessions ADD COLUMN "{column}" {col_type}')


def create_session(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    """Создать запись о сессии."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    sql = f"INSERT INTO sessions ({columns}) VALUES ({placeholders})"
    conn.execute(sql, list(data.values()))
    conn.commit()


def update_session(conn: sqlite3.Connection, session_id: str, data: dict[str, Any]) -> None:
    """Обновить запись сессии."""
    set_clause = ", ".join(f"{k} = ?" for k in data)
    values = list(data.values()) + [session_id]
    sql = f"UPDATE sessions SET {set_clause} WHERE id = ?"
    conn.execute(sql, values)
    conn.commit()


def get_pending_sessions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Получить сессии со статусом pending."""
    cursor = conn.execute("SELECT * FROM sessions WHERE status = 'pending'")
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def find_cached_transcription(conn: sqlite3.Connection, file_hash: str) -> list[dict[str, Any]]:
    """
    Наити все сессии с заданным file_hash, упорядоченные от свежеи к старои.

    Используется для кеша транскрипции: вызывающий код перебирает кандидатов и
    берет первого, у которого валиден transcription.json. Фильтр по статусу не
    применяется, так как статус мог стать failed при сбое диаризации, хотя
    транскрипция успешно завершилась.
    :return: список словареи-строк сессии (пустои список, если ничего не наидено)
    """
    sql = (
        "SELECT * FROM sessions "
        "WHERE file_hash = ? "
        "ORDER BY created_at DESC"
    )
    cursor = conn.execute(sql, (file_hash,))
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def find_sessions_by_youtube_url(
    conn: sqlite3.Connection, youtube_url: str
) -> list[dict[str, Any]]:
    """
    Наити все сессии YouTube для заданнои ссылки, от свежеи к старои.

    Совпадение определяется по video ID, извлеченному из ссылки, поэтому
    работает для разных форматов URL (watch?v=, youtu.be/, embed/).
    Используется для переиспользования ранее скачанного аудиофаила
    и кешированнои транскрипции без повторнои загрузки.
    :return: список словареи-строк сессии (пустои список, если ничего не наидено)
    """
    from src.file_scanner import _extract_youtube_id

    video_id = _extract_youtube_id(youtube_url)
    sql = (
        "SELECT * FROM sessions "
        "WHERE source_type = 'youtube_link' AND source_url LIKE ? "
        "ORDER BY created_at DESC"
    )
    cursor = conn.execute(sql, (f"%{video_id}%",))
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def enqueue_stage(
    conn: sqlite3.Connection, session_id: str, stage: str
) -> None:
    """Добавить этап в очередь обработки."""
    sql = (
        "INSERT INTO processing_queue (session_id, status, stage, created_at) "
        "VALUES (?, ?, ?, ?)"
    )
    now = datetime.now().isoformat()
    conn.execute(sql, (session_id, "queued", stage, now))
    conn.commit()


def update_stage(
    conn: sqlite3.Connection,
    session_id: str,
    stage: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Обновить статус этапа."""
    if status in ("completed", "failed"):
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE processing_queue SET status = ?, completed_at = ?, error_message = ? "
            "WHERE session_id = ? AND stage = ? AND status = 'queued'",
            (status, now, error_message, session_id, stage),
        )
    else:
        conn.execute(
            "UPDATE processing_queue SET status = ?, error_message = ? "
            "WHERE session_id = ? AND stage = ?",
            (status, error_message, session_id, stage),
        )
    conn.commit()


def get_translation(conn: sqlite3.Connection, key: str, lang: str) -> str | None:
    """Получить перевод по ключу и языку."""
    cursor = conn.execute(
        "SELECT value FROM translations WHERE key = ? AND lang = ?",
        (key, lang),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def set_translation(conn: sqlite3.Connection, key: str, lang: str, value: str) -> None:
    """Установить перевод (UPSERT)."""
    conn.execute(
        "INSERT INTO translations (key, lang, value) VALUES (?, ?, ?) "
        "ON CONFLICT(key, lang) DO UPDATE SET value = excluded.value",
        (key, lang, value),
    )
    conn.commit()


def insert_initial_translations(conn: sqlite3.Connection) -> None:
    """Заполнить таблицу translations начальными переводами (ru + en)."""
    translations: dict[str, dict[str, str]] = {
        "msg.app_started": {
            "ru": "Запущен {name} v{version}",
            "en": "Started {name} v{version}",
        },
        "msg.scan_started": {
            "ru": "Сканирование папок input/",
            "en": "Scanning input/ folders",
        },
        "msg.files_found": {
            "ru": "Найдено файлов",
            "en": "Files found",
        },
        "msg.files_found.one": {
            "ru": "Найден {count} файл",
            "en": "Found {count} file",
        },
        "msg.files_found.few": {
            "ru": "Найдено {count} файла",
            "en": "Found {count} files",
        },
        "msg.files_found.many": {
            "ru": "Найдено {count} файлов",
            "en": "Found {count} files",
        },
        "msg.files_to_process": {
            "ru": "Файлов к обработке: {count}",
            "en": "Files to process: {count}",
        },
        "msg.sources_summary": {
            "ru": "К обработке: {parts}",
            "en": "To process: {parts}",
        },
        "msg.nothing_to_process": {
            "ru": "Нечего обрабатывать",
            "en": "Nothing to process",
        },
        "label.list_separator": {
            "ru": ", ",
            "en": ", ",
        },
        "msg.src_links.one": {
            "ru": "{count} ссылка",
            "en": "{count} link",
        },
        "msg.src_links.few": {
            "ru": "{count} ссылки",
            "en": "{count} links",
        },
        "msg.src_links.many": {
            "ru": "{count} ссылок",
            "en": "{count} links",
        },
        "msg.src_video.one": {
            "ru": "{count} видео",
            "en": "{count} video",
        },
        "msg.src_video.few": {
            "ru": "{count} видео",
            "en": "{count} videos",
        },
        "msg.src_video.many": {
            "ru": "{count} видео",
            "en": "{count} videos",
        },
        "msg.src_audio.one": {
            "ru": "{count} аудио",
            "en": "{count} audio",
        },
        "msg.src_audio.few": {
            "ru": "{count} аудио",
            "en": "{count} audios",
        },
        "msg.src_audio.many": {
            "ru": "{count} аудио",
            "en": "{count} audios",
        },
        "msg.extracting_audio": {
            "ru": "Извлечение аудио: {filename}",
            "en": "Extracting audio: {filename}",
        },
        "msg.transcribing": {
            "ru": "Транскрибация: {filename}",
            "en": "Transcribing: {filename}",
        },
        "msg.transcribing_progress": {
            "ru": "Транскрибация {pct:.1f}%",
            "en": "Transcribing {pct:.1f}%",
        },
        "msg.transcribing_progress_detail": {
            "ru": "сегментов: {segments}, позиция: {seconds} сек",
            "en": "segments: {segments}, position: {seconds} sec",
        },
        "msg.whisper_result": {
            "ru": "Транскрибация завершена: {words} слов, уверенность {confidence:.2f}, язык {language}",
            "en": "Transcription complete: {words} words, confidence {confidence:.2f}, language {language}",
        },
        "msg.diarizing": {
            "ru": "Диаризация: {filename}",
            "en": "Diarizing: {filename}",
        },
        "msg.diarization_result": {
            "ru": "Найдено дикторов: {count}",
            "en": "Speakers found: {count}",
        },
        "msg.summarizing": {
            "ru": "Краткий пересказ: {filename} (DeepSeek)",
            "en": "Brief recap: {filename} (DeepSeek)",
        },
        "msg.summarizing_map_reduce": {
            "ru": "Краткий пересказ: map-reduce, чанков: {chunks}",
            "en": "Brief recap: map-reduce, chunks: {chunks}",
        },
        "msg.summarizing_chunk": {
            "ru": "Краткий пересказ: чанк {current}/{total}",
            "en": "Brief recap: chunk {current}/{total}",
        },
        "msg.summarization_done": {
            "ru": "Краткий пересказ готов",
            "en": "Brief recap complete",
        },
        "msg.generating_article": {
            "ru": "Генерация статьи: {filename} (DeepSeek)",
            "en": "Generating article: {filename} (DeepSeek)",
        },
        "msg.article_done": {
            "ru": "Генерация статьи завершена",
            "en": "Article generation complete",
        },
        "msg.session_completed": {
            "ru": "Обработка завершена: {session_id}, длительность: {duration} сек",
            "en": "Processing complete: {session_id}, duration: {duration} sec",
        },
        "msg.session_failed": {
            "ru": "Обработка прервана: {session_id}, причина: {error}",
            "en": "Processing failed: {session_id}, reason: {error}",
        },
        "msg.interrupted": {
            "ru": "Прерывание пользователем",
            "en": "User interrupted",
        },
        "msg.yt_downloading": {
            "ru": "Загрузка YouTube: {url}",
            "en": "Downloading YouTube: {url}",
        },
        "msg.yt_downloaded": {
            "ru": "YouTube загружен: {filename}",
            "en": "YouTube downloaded: {filename}",
        },
        "msg.yt_reused": {
            "ru": "YouTube уже загружен ранее, переиспользование: {filename} ({url})",
            "en": "YouTube already downloaded, reusing: {filename} ({url})",
        },
        "msg.session_created": {
            "ru": "Сессия создана: {session_id}",
            "en": "Session created: {session_id}",
        },
        "msg.copying_output": {
            "ru": "Копирование в output/: {filename}",
            "en": "Copying to output/: {filename}",
        },
        "msg.all_done": {
            "ru": "Обработано сессии: {total}. Успешно: {success}, с ошибками: {failed}",
            "en": "Sessions processed: {total}. Success: {success}, failed: {failed}",
        },
        "msg.validating": {
            "ru": "Проверка окружения",
            "en": "Validating environment",
        },
        "msg.validation_passed": {
            "ru": "Проверка окружения завершена",
            "en": "Validation passed",
        },
        "error.config_missing": {
            "ru": "Отсутствует параметр конфигурации: {param}",
            "en": "Missing config parameter: {param}",
        },
        "error.api_key_missing": {
            "ru": "Отсутствует ключ API: {key} в .env",
            "en": "Missing API key: {key} in .env",
        },
        "error.connection_failed": {
            "ru": "Ошибка подключения: {detail}",
            "en": "Connection failed: {detail}",
        },
        "error.transcription_failed": {
            "ru": "Ошибка транскрибации: {detail}",
            "en": "Transcription failed: {detail}",
        },
        "error.summarization_failed": {
            "ru": "Ошибка саммаризации: {detail}",
            "en": "Summarization failed: {detail}",
        },
        "error.diarization_failed": {
            "ru": "Ошибка диаризации: {detail}",
            "en": "Diarization failed: {detail}",
        },
        "error.ffmpeg_not_found": {
            "ru": "ffmpeg не найден. Установите ffmpeg и добавьте в PATH",
            "en": "ffmpeg not found. Install ffmpeg and add to PATH",
        },
        "error.ytdlp_not_found": {
            "ru": "yt-dlp не найден. Установите: pip install yt-dlp",
            "en": "yt-dlp not found. Install: pip install yt-dlp",
        },
        "error.folder_not_found": {
            "ru": "Папка не найдена: {path}",
            "en": "Folder not found: {path}",
        },
        "error.youtube_invalid": {
            "ru": "Невалидная ссылка YouTube: {url}",
            "en": "Invalid YouTube link: {url}",
        },
        "error.youtube_download_failed": {
            "ru": "Ошибка загрузки YouTube: {detail}",
            "en": "YouTube download failed: {detail}",
        },
        "error.no_input_files": {
            "ru": "Нет файлов для обработки в input/",
            "en": "No files to process in input/",
        },
        "label.file": {
            "ru": "Файл",
            "en": "File",
        },
        "label.table": {
            "ru": "Таблица",
            "en": "Table",
        },
        "label.session": {
            "ru": "Сессия",
            "en": "Session",
        },
        "label.status": {
            "ru": "Статус",
            "en": "Status",
        },
        "label.type": {
            "ru": "Тип",
            "en": "Type",
        },
        "label.duration_sec": {
            "ru": "Длительность (сек)",
            "en": "Duration (sec)",
        },
        "label.words": {
            "ru": "Слов",
            "en": "Words",
        },
        "label.speakers": {
            "ru": "Дикторов",
            "en": "Speakers",
        },
        "label.result": {
            "ru": "Результат",
            "en": "Result",
        },
        "label.missing_columns": {
            "ru": "Пропущенные колонки",
            "en": "Missing columns",
        },
        "msg.connection_db_ok": {
            "ru": "Соединение с БД установлено",
            "en": "DB connection established",
        },
        "msg.db_not_exists": {
            "ru": "База данных не существует. Выполните db_init.py",
            "en": "Database does not exist. Run db_init.py",
        },
        "msg.table_missing": {
            "ru": "Отсутствует таблица: {table}",
            "en": "Missing table: {table}",
        },
        "msg.schema_mismatch_warning": {
            "ru": "Схема не соответствует. Рекомендуется выполнить db_init",
            "en": "Schema mismatch. Run db_init.py recommended",
        },
        "msg.schema_ok": {
            "ru": "Схема соответствует",
            "en": "Schema matches",
        },
        "error.db_schema_problem": {
            "ru": "Проблема схемы БД: {problem}",
            "en": "DB schema problem: {problem}",
        },
        "error.run_db_init": {
            "ru": "Схема БД не соответствует ожидаемой. Выполните: python run/db/db_init.py",
            "en": "DB schema mismatch. Run: python run/db/db_init.py",
        },
        "error.translations_empty": {
            "ru": "Таблица переводов пуста. Выполните: python run/db/db_init.py",
            "en": "Translations table is empty. Run: python run/db/db_init.py",
        },
        "msg.tables_translations_created": {
            "ru": "Таблицы созданы, переводы заполнены",
            "en": "Tables created, translations populated",
        },
        "msg.db_init_report": {
            "ru": "Отчет о состоянии БД",
            "en": "DB status report",
        },
        "msg.db_init_table_ok": {
            "ru": "{table}: OK, строк: {count}",
            "en": "{table}: OK, rows: {count}",
        },
        "msg.db_init_table_missing": {
            "ru": "{table}: отсутствует",
            "en": "{table}: missing",
        },
        "msg.db_init_table_mismatch": {
            "ru": "{table}: не соответствует, пропущены колонки: {cols}",
            "en": "{table}: mismatch, missing columns: {cols}",
        },
        "msg.db_init_translations": {
            "ru": "Переводов в БД: {count}",
            "en": "Translations in DB: {count}",
        },
        "msg.db_init_translations_filled": {
            "ru": "Переводы заполнены, всего: {count}",
            "en": "Translations populated, total: {count}",
        },
        "msg.db_init_no_action": {
            "ru": "Схема соответствует, переводы заполнены. Действия не требуются",
            "en": "Schema OK, translations populated. No action needed",
        },
        "msg.db_tables_cleared": {
            "ru": "Таблицы очищены",
            "en": "Tables cleared",
        },
        "msg.db_tables_recreated": {
            "ru": "Таблицы пересозданы",
            "en": "Tables recreated",
        },
        "prompt.db_init_clean": {
            "ru": "Очистить таблицы? 1 - да, 0 - нет",
            "en": "Clear tables? 1 - yes, 0 - no",
        },
        "prompt.db_init_recreate": {
            "ru": "Пересоздать таблицы по схеме? 1 - да, 0 - нет",
            "en": "Recreate tables from schema? 1 - yes, 0 - no",
        },
        "msg.db_init_menu_header": {
            "ru": "Выберите действие:",
            "en": "Choose action:",
        },
        "msg.db_init_recreate_unnecessary": {
            "ru": "Схема соответствует, пересоздание не требуется",
            "en": "Schema OK, recreate not needed",
        },
        "msg.db_init_translations_already": {
            "ru": "Переводы уже заполнены",
            "en": "Translations already populated",
        },
        "msg.db_init_unknown_choice": {
            "ru": "Неизвестный вариант",
            "en": "Unknown choice",
        },
        "menu.db_init_clear": {
            "ru": "Очистить все таблицы и заполнить переводы",
            "en": "Clear all tables and fill translations",
        },
        "menu.db_init_recreate": {
            "ru": "Пересоздать таблицы и заполнить переводы (только при несоответствии схемы)",
            "en": "Recreate tables and fill translations (only on schema mismatch)",
        },
        "menu.db_init_fill_translations": {
            "ru": "Только заполнить переводы",
            "en": "Fill translations only",
        },
        "menu.db_init_exit": {
            "ru": "Выход",
            "en": "Exit",
        },
        "msg.api_deepseek_ok": {
            "ru": "Соединение с DeepSeek API установлено",
            "en": "DeepSeek API connection established",
        },
        "msg.api_test_prompt": {
            "ru": "Промпт: {text}",
            "en": "Prompt: {text}",
        },
        "msg.api_test_answer": {
            "ru": "Ответ: {text}",
            "en": "Answer: {text}",
        },
        "msg.api_test_ok": {
            "ru": "Тестовый запрос выполнен успешно",
            "en": "Test request completed successfully",
        },
        "msg.ollama_disabled": {
            "ru": "Ollama отключен в конфигурации (enabled=false)",
            "en": "Ollama disabled in config (enabled=false)",
        },
        "msg.ollama_ok": {
            "ru": "Соединение с Ollama установлено",
            "en": "Ollama connection established",
        },
        "msg.ollama_models_not_configured": {
            "ru": "Модели Ollama не указаны в конфигурации",
            "en": "Ollama models not specified in config",
        },
        "msg.ollama_downloading_model": {
            "ru": "Загрузка модели: {model}",
            "en": "Downloading model: {model}",
        },
        "msg.ollama_model_downloaded": {
            "ru": "Модель {model} загружена",
            "en": "Model {model} downloaded",
        },
        "msg.ollama_model_download_error": {
            "ru": "Ошибка загрузки модели {model}: {detail}",
            "en": "Model download error {model}: {detail}",
        },
        "msg.retry_attempt": {
            "ru": "retry: попытка {attempt}/{total}, задержка {delay} сек, причина: {reason}",
            "en": "retry: attempt {attempt}/{total}, delay {delay} sec, reason: {reason}",
        },
        "msg.transcription_md_title": {
            "ru": "# Транскрипция: {source}",
            "en": "# Transcription: {source}",
        },
        "msg.transcription_md_date": {
            "ru": "**Дата обработки:** {date}",
            "en": "**Processing date:** {date}",
        },
        "msg.transcription_md_duration": {
            "ru": "**Длительность:** {mins} мин {secs} сек",
            "en": "**Duration:** {mins} min {secs} sec",
        },
        "msg.transcription_md_language": {
            "ru": "**Язык:** {language}",
            "en": "**Language:** {language}",
        },
        "msg.transcription_md_model": {
            "ru": "**Модель:** faster-whisper {model}",
            "en": "**Model:** faster-whisper {model}",
        },
        "msg.transcription_md_diarization": {
            "ru": "**Диаризация:** pyannote.audio ({speakers} диктора)",
            "en": "**Diarization:** pyannote.audio ({speakers} speakers)",
        },
        "msg.transcription_md_section": {
            "ru": "## Текст (по ролям)",
            "en": "## Text (by roles)",
        },
        "msg.summary_md_title": {
            "ru": "# Саммари: {source}",
            "en": "# Summary: {source}",
        },
        "msg.summary_md_heading": {
            "ru": "# Краткий пересказ",
            "en": "# Brief recap",
        },
        "msg.summary_md_source_label": {
            "ru": "Источник",
            "en": "Source",
        },
        "msg.src_md_channel": {
            "ru": "Канал: {name}",
            "en": "Channel: {name}",
        },
        "msg.src_md_subscribers": {
            "ru": "Подписчики: {value}",
            "en": "Subscribers: {value}",
        },
        "msg.src_md_video_url": {
            "ru": "Ссылка на видео: {url}",
            "en": "Video link: {url}",
        },
        "msg.src_md_channel_url": {
            "ru": "Ссылка на канал: {url}",
            "en": "Channel link: {url}",
        },
        "msg.src_md_file": {
            "ru": "Файл: {name}",
            "en": "File: {name}",
        },
        "msg.src_md_duration": {
            "ru": "Длительность: {duration}",
            "en": "Duration: {duration}",
        },
        "msg.src_md_size": {
            "ru": "Размер: {size}",
            "en": "Size: {size}",
        },
        "msg.summary_md_date": {
            "ru": "**Дата:** {date}",
            "en": "**Date:** {date}",
        },
        "msg.summary_md_engine": {
            "ru": "**Движок:** {engine}",
            "en": "**Engine:** {engine}",
        },
        "msg.summary_md_speakers": {
            "ru": "**Дикторы:** {speakers}",
            "en": "**Speakers:** {speakers}",
        },
        "label.temperature": {
            "ru": "Температура",
            "en": "Temperature",
        },
        "label.tokens": {
            "ru": "Токенов",
            "en": "Tokens",
        },
        "label.not_available": {
            "ru": "н/д",
            "en": "n/a",
        },
        "msg.yt_channel_info_failed": {
            "ru": "Не удалось получить информацию о канале: {detail}",
            "en": "Failed to get channel info: {detail}",
        },
        "msg.yt_title_failed": {
            "ru": "Не удалось получить название видео: {detail}",
            "en": "Failed to get video title: {detail}",
        },
        "msg.preflight_start": {
            "ru": "Проверка готовности пайплайна",
            "en": "Pipeline readiness check",
        },
        "msg.preflight_summary_ok": {
            "ru": "Проверка готовности пройдена",
            "en": "Readiness check passed",
        },
        "msg.preflight_model_checking": {
            "ru": "Проверка модели: {model}",
            "en": "Checking model: {model}",
        },
        "msg.preflight_model_ok": {
            "ru": "Модель готова: {model}",
            "en": "Model ready: {model}",
        },
        "msg.preflight_model_incomplete": {
            "ru": "Модель недокачана: {model}, отсутствуют файлы: {files}",
            "en": "Model incomplete: {model}, missing files: {files}",
        },
        "msg.preflight_model_downloading": {
            "ru": "Доустановка модели: {model}",
            "en": "Downloading model: {model}",
        },
        "msg.preflight_model_download_ok": {
            "ru": "Модель доустановлена: {model}",
            "en": "Model downloaded: {model}",
        },
        "msg.preflight_model_download_failed": {
            "ru": "Не удалось доустановить модель {model} за {timeout} сек: {detail}",
            "en": "Failed to download model {model} within {timeout} sec: {detail}",
        },
        "msg.preflight_model_manual": {
            "ru": "Скачайте модель вручную: huggingface-cli download {repo}",
            "en": "Download model manually: huggingface-cli download {repo}",
        },
        "msg.preflight_deepseek_checking": {
            "ru": "Проверка DeepSeek API",
            "en": "Checking DeepSeek API",
        },
        "msg.preflight_deepseek_ok": {
            "ru": "DeepSeek API доступен",
            "en": "DeepSeek API available",
        },
        "msg.preflight_hf_checking": {
            "ru": "Проверка HuggingFace Hub и HF_TOKEN",
            "en": "Checking HuggingFace Hub and HF_TOKEN",
        },
        "msg.preflight_hf_ok": {
            "ru": "HuggingFace Hub доступен, пользователь: {user}",
            "en": "HuggingFace Hub available, user: {user}",
        },
        "msg.preflight_hf_token_invalid": {
            "ru": "HF_TOKEN невалиден или истек",
            "en": "HF_TOKEN invalid or expired",
        },
        "error.preflight_failed": {
            "ru": "Проверка готовности не пройдена",
            "en": "Readiness check failed",
        },
        "msg.preflight_gated": {
            "ru": "Модель требует доступа (gated): {repo}. Запросите доступ: {url}",
            "en": "Model requires access (gated): {repo}. Request access: {url}",
        },
        "msg.preflight_gated_pyannote": {
            "ru": "Для диаризации нужны gated-модели pyannote: speaker-diarization-3.1, segmentation-3.0, speaker-diarization-community-1. Примите условия на всех страницах, либо отключите диаризацию ([diarization] enabled=false)",
            "en": "Diarization needs gated pyannote models: speaker-diarization-3.1, segmentation-3.0, speaker-diarization-community-1. Accept terms on all pages, or disable diarization ([diarization] enabled=false)",
        },
        "msg.transcription_cached": {
            "ru": "Транскрипция восстановлена из кеша: {session_id}",
            "en": "Transcription restored from cache: {session_id}",
        },
        "msg.diarization_cached": {
            "ru": "Диаризация восстановлена из кеша: {session_id}",
            "en": "Diarization restored from cache: {session_id}",
        },
        "msg.email_sending": {
            "ru": "Отправка саммари на email: {to}",
            "en": "Sending summary to email: {to}",
        },
        "msg.email_sending_article": {
            "ru": "Отправка статьи на email: {to}",
            "en": "Sending article to email: {to}",
        },
        "msg.email_sent": {
            "ru": "Письмо отправлено: {to}",
            "en": "Email sent: {to}",
        },
        "error.email_send_failed": {
            "ru": "Ошибка отправки письма: {detail}",
            "en": "Email send failed: {detail}",
        },
        "error.email_not_enabled": {
            "ru": "Отправка email отключена в конфигурации (enabled=false)",
            "en": "Email sending disabled in config (enabled=false)",
        },
    }

    for key, lang_values in translations.items():
        for lang, value in lang_values.items():
            set_translation(conn, key, lang, value)
