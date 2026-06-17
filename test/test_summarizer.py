"""
Тесты модуля summarizer (mock requests).
"""

from configparser import ConfigParser

from src.summarizer import _estimate_tokens, _chunk_text, MAX_CHUNK_TOKENS


def test_estimate_tokens() -> None:
    """_estimate_tokens оценивает количество токенов."""
    text = "hello" * 100
    tokens = _estimate_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_chunk_text_short() -> None:
    """_chunk_text не разбивает короткии текст."""
    text = "hello world"
    chunks = _chunk_text(text, 1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long() -> None:
    """_chunk_text разбивает длинный текст."""
    lines = ["line " + str(i) + " " + "x" * 20 for i in range(2000)]
    text = "\n".join(lines)
    max_chars = 500
    chunks = _chunk_text(text, max_chars)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= max_chars * 2
