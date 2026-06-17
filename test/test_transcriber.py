"""
Тесты модуля transcriber (mock faster-whisper).
"""

from configparser import ConfigParser
from pathlib import Path

from src.transcriber import TranscriptionResult, TranscriptionSegment


def test_transcription_result_dataclass() -> None:
    """TranscriptionResult и TranscriptionSegment создаются корректно."""
    seg = TranscriptionSegment(start=0.0, end=1.5, text="Привет")
    assert seg.start == 0.0
    assert seg.end == 1.5
    assert seg.text == "Привет"

    result = TranscriptionResult(
        segments=[seg],
        language="ru",
        confidence=0.95,
        word_count=1,
    )
    assert len(result.segments) == 1
    assert result.language == "ru"
    assert result.confidence == 0.95
