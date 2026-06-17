"""
Тесты модуля session_manager.
"""

import json
import sqlite3
from pathlib import Path

import pytest

from src.localization import init as i18n_init, _translations as i18n_translations
from src.session_manager import (
    generate_session_id,
    create_session_dir,
    save_metadata,
    save_transcription,
    save_summary,
    copy_summary_to_output,
    build_transcription_markdown,
    build_summary_markdown,
    _format_timestamp,
)

_MD_TRANSLATIONS_RU: dict[str, str] = {
    "msg.transcription_md_title": "# Транскрипция: {source}",
    "msg.transcription_md_date": "**Дата обработки:** {date}",
    "msg.transcription_md_duration": "**Длительность:** {mins} мин {secs} сек",
    "msg.transcription_md_language": "**Язык:** {language}",
    "msg.transcription_md_model": "**Модель:** faster-whisper {model}",
    "msg.transcription_md_diarization": "**Диаризация:** pyannote.audio ({speakers} диктора)",
    "msg.transcription_md_section": "## Текст (по ролям)",
    "msg.summary_md_heading": "# Саммари",
    "msg.summary_md_source_label": "Источник",
    "msg.summary_md_date": "**Дата:** {date}",
    "msg.summary_md_engine": "**Движок:** {engine}",
    "msg.summary_md_speakers": "**Дикторы:** {speakers}",
}


@pytest.fixture(autouse=True)
def _setup_i18n(tmp_path: Path) -> None:
    """Инициализировать i18n перед тестами Markdown."""
    i18n_translations.update(_MD_TRANSLATIONS_RU)


def test_generate_session_id(tmp_path: Path) -> None:
    """generate_session_id должен создавать ID с временной меткой и хешем."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content", encoding="utf-8")

    session_id = generate_session_id(test_file)
    parts = session_id.split("_")
    assert len(parts) >= 3
    assert len(parts[-1]) == 8


def test_create_session_dir(tmp_path: Path, monkeypatch) -> None:
    """create_session_dir создает папку с session_id."""
    monkeypatch.setattr("src.session_manager.PROJECT_ROOT", tmp_path)
    (tmp_path / "data" / "sessions").mkdir(parents=True)

    session_id = "2026-06-15_17-30-00_a1b2c3d4"
    sess_dir = create_session_dir(session_id)
    assert sess_dir.exists()
    assert sess_dir.is_dir()
    assert sess_dir.name == session_id


def test_save_metadata(tmp_path: Path) -> None:
    """save_metadata сохраняет JSON атомарно."""
    target = tmp_path / "session"
    target.mkdir()
    metadata = {"key": "value", "num": 42}
    path = save_metadata(target, metadata)
    assert path.suffix == ".json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["key"] == "value"
    assert data["num"] == 42


def test_save_transcription(tmp_path: Path) -> None:
    """save_transcription сохраняет transcription.md."""
    target = tmp_path / "session"
    target.mkdir()
    content = "# Transcription\n\nTest text"
    path = save_transcription(target, content)
    assert path.name == "transcription.md"
    assert path.read_text(encoding="utf-8") == content


def test_save_summary(tmp_path: Path) -> None:
    """save_summary сохраняет summary.md."""
    target = tmp_path / "session"
    target.mkdir()
    content = "# Summary\n\nTest summary"
    path = save_summary(target, content)
    assert path.name == "summary.md"
    assert path.read_text(encoding="utf-8") == content


def test_copy_summary_to_output(tmp_path: Path, monkeypatch) -> None:
    """copy_summary_to_output копирует в output/."""
    monkeypatch.setattr("src.session_manager.PROJECT_ROOT", tmp_path)
    (tmp_path / "output").mkdir(parents=True)
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    summary_content = "# Summary"
    (session_dir / "summary.md").write_text(summary_content, encoding="utf-8")

    session_id = "2026-test-id"
    dest = copy_summary_to_output(session_id, session_dir)
    assert dest.exists()
    assert f"{session_id}_summary.md" in dest.name
    assert dest.read_text(encoding="utf-8") == summary_content


def test_format_timestamp() -> None:
    """_format_timestamp корректно форматирует секунды."""
    assert _format_timestamp(0) == "00:00:00"
    assert _format_timestamp(61) == "00:01:01"
    assert _format_timestamp(3661) == "01:01:01"


def test_build_transcription_markdown() -> None:
    """build_transcription_markdown формирует корректный Markdown."""

    class MockSegment:
        def __init__(self, start: float, end: float, text: str, speaker_id: str) -> None:
            self.start = start
            self.end = end
            self.text = text
            self.speaker_id = speaker_id

    segments = [MockSegment(0.0, 5.0, "Привет", "Спикер_1")]
    result = build_transcription_markdown(
        segments, "test.mp3", 300.0, "ru", "large-v3", 1, "2026-06-15 17:30",
    )
    assert "# Транскрипция: test.mp3" in result
    assert "Спикер_1:" in result
    assert "5 мин 0 сек" in result


def test_build_summary_markdown() -> None:
    """build_summary_markdown формирует корректный Markdown."""
    source_block = "Файл: test.mp3\nДлительность: 5:00\nРазмер: 1.0 МБ"
    result = build_summary_markdown(
        "Краткое содержание", source_block, "2026-06-15", "deepseek-chat", "Спикер_1, Спикер_2",
    )
    assert "# Саммари" in result
    assert "Источник" in result
    assert "Файл: test.mp3" in result
    assert "deepseek-chat" in result
    assert "Краткое содержание" in result
