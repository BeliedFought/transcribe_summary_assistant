"""
Тесты модуля file_scanner.
"""

from pathlib import Path

from src.file_scanner import (
    scan_input_dirs,
    compute_file_hash,
    _find_youtube_links,
    _extract_youtube_id,
)


def test_find_youtube_links_single() -> None:
    """_find_youtube_links находит одну ссылку."""
    text = "https://www.youtube.com/watch?v=abc123"
    assert _find_youtube_links(text) == ["https://www.youtube.com/watch?v=abc123"]


def test_find_youtube_links_multiple() -> None:
    """_find_youtube_links находит несколько ссылок с сохранением порядка."""
    text = (
        "https://www.youtube.com/watch?v=aaa111\n"
        "комментарий\n"
        "https://youtu.be/bbb222\n"
        "https://youtube.com/embed/ccc333\n"
    )
    assert _find_youtube_links(text) == [
        "https://www.youtube.com/watch?v=aaa111",
        "https://youtu.be/bbb222",
        "https://youtube.com/embed/ccc333",
    ]


def test_find_youtube_links_dedup() -> None:
    """_find_youtube_links исключает дубликаты, сохраняя первое вхождение."""
    text = (
        "https://youtu.be/abc123\n"
        "https://youtu.be/abc123\n"
    )
    assert _find_youtube_links(text) == ["https://youtu.be/abc123"]


def test_find_youtube_links_invalid() -> None:
    """_find_youtube_links возвращает пустой список для невалидного текста."""
    assert _find_youtube_links("not a link") == []
    assert _find_youtube_links("https://google.com") == []
    assert _find_youtube_links("") == []


def test_extract_youtube_id() -> None:
    """_extract_youtube_id извлекает video ID из разных форматов ссылок."""
    assert _extract_youtube_id("https://www.youtube.com/watch?v=abc123") == "abc123"
    assert _extract_youtube_id("https://youtu.be/abc123") == "abc123"
    assert _extract_youtube_id("https://youtube.com/embed/abc123") == "abc123"


def test_compute_file_hash(tmp_path: Path) -> None:
    """compute_file_hash вычисляет SHA256."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello", encoding="utf-8")
    result = compute_file_hash(test_file)
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_scan_input_dirs(tmp_path: Path, monkeypatch) -> None:
    """scan_input_dirs находит файлы в input/audio/."""
    monkeypatch.setattr("src.file_scanner.PROJECT_ROOT", tmp_path)

    audio_dir = tmp_path / "input" / "audio"
    audio_dir.mkdir(parents=True)
    (audio_dir / "test.mp3").write_text("dummy", encoding="utf-8")

    video_dir = tmp_path / "input" / "video"
    video_dir.mkdir(parents=True)

    yt_dir = tmp_path / "input" / "yt"
    yt_dir.mkdir(parents=True)

    from configparser import ConfigParser
    config = ConfigParser()
    config.add_section("processing")
    config.set("processing", "audio_extensions", ".mp3,.wav")
    config.set("processing", "video_extensions", ".mp4")
    config.set("processing", "text_extensions", ".txt")

    results = scan_input_dirs(config)
    assert len(results) == 1
    assert results[0].filename == "test.mp3"
    assert results[0].file_type == "audio"


def test_scan_input_dirs_youtube_single(tmp_path: Path, monkeypatch) -> None:
    """scan_input_dirs находит YouTube ссылку в .txt файле."""
    monkeypatch.setattr("src.file_scanner.PROJECT_ROOT", tmp_path)

    (tmp_path / "input" / "audio").mkdir(parents=True)
    (tmp_path / "input" / "video").mkdir(parents=True)

    yt_dir = tmp_path / "input" / "yt"
    yt_dir.mkdir(parents=True)
    (yt_dir / "link.txt").write_text(
        "https://www.youtube.com/watch?v=abc123",
        encoding="utf-8",
    )

    from configparser import ConfigParser
    config = ConfigParser()
    config.add_section("processing")
    config.set("processing", "audio_extensions", ".mp3")
    config.set("processing", "video_extensions", ".mp4")
    config.set("processing", "text_extensions", ".txt")

    results = scan_input_dirs(config)
    assert len(results) == 1
    assert results[0].file_type == "youtube_link"
    assert results[0].youtube_url == "https://www.youtube.com/watch?v=abc123"
    assert results[0].filename == "abc123"


def test_scan_input_dirs_youtube_multiple_links(tmp_path: Path, monkeypatch) -> None:
    """scan_input_dirs создает отдельный FileInfo на каждую ссылку в одном .txt."""
    monkeypatch.setattr("src.file_scanner.PROJECT_ROOT", tmp_path)

    (tmp_path / "input" / "audio").mkdir(parents=True)
    (tmp_path / "input" / "video").mkdir(parents=True)

    yt_dir = tmp_path / "input" / "yt"
    yt_dir.mkdir(parents=True)
    (yt_dir / "links.txt").write_text(
        "https://youtu.be/aaa111\n"
        "какой-то комментарий\n"
        "https://www.youtube.com/watch?v=bbb222\n"
        "\n"
        "https://youtu.be/aaa111\n",
        encoding="utf-8",
    )

    from configparser import ConfigParser
    config = ConfigParser()
    config.add_section("processing")
    config.set("processing", "audio_extensions", ".mp3")
    config.set("processing", "video_extensions", ".mp4")
    config.set("processing", "text_extensions", ".txt")

    results = scan_input_dirs(config)
    assert len(results) == 2
    assert [r.youtube_url for r in results] == [
        "https://youtu.be/aaa111",
        "https://www.youtube.com/watch?v=bbb222",
    ]
    assert results[0].filename == "aaa111"
    assert results[1].filename == "bbb222"


def test_scan_input_dirs_youtube_multiple_files(tmp_path: Path, monkeypatch) -> None:
    """scan_input_dirs собирает ссылки из всех .txt файлов в input/yt/."""
    monkeypatch.setattr("src.file_scanner.PROJECT_ROOT", tmp_path)

    (tmp_path / "input" / "audio").mkdir(parents=True)
    (tmp_path / "input" / "video").mkdir(parents=True)

    yt_dir = tmp_path / "input" / "yt"
    yt_dir.mkdir(parents=True)
    (yt_dir / "a.txt").write_text("https://youtu.be/aaa111\n", encoding="utf-8")
    (yt_dir / "b.txt").write_text("https://youtu.be/bbb222\n", encoding="utf-8")

    from configparser import ConfigParser
    config = ConfigParser()
    config.add_section("processing")
    config.set("processing", "audio_extensions", ".mp3")
    config.set("processing", "video_extensions", ".mp4")
    config.set("processing", "text_extensions", ".txt")

    results = scan_input_dirs(config)
    assert len(results) == 2
    urls = {r.youtube_url for r in results}
    assert urls == {"https://youtu.be/aaa111", "https://youtu.be/bbb222"}


def test_scan_input_dirs_youtube_global_dedup(tmp_path: Path, monkeypatch) -> None:
    """scan_input_dirs дедуплицирует ссылки между разными .txt файлами."""
    monkeypatch.setattr("src.file_scanner.PROJECT_ROOT", tmp_path)

    (tmp_path / "input" / "audio").mkdir(parents=True)
    (tmp_path / "input" / "video").mkdir(parents=True)

    yt_dir = tmp_path / "input" / "yt"
    yt_dir.mkdir(parents=True)
    (yt_dir / "a.txt").write_text("https://youtu.be/abc123\n", encoding="utf-8")
    (yt_dir / "b.txt").write_text("https://youtu.be/abc123\n", encoding="utf-8")

    from configparser import ConfigParser
    config = ConfigParser()
    config.add_section("processing")
    config.set("processing", "audio_extensions", ".mp3")
    config.set("processing", "video_extensions", ".mp4")
    config.set("processing", "text_extensions", ".txt")

    results = scan_input_dirs(config)
    assert len(results) == 1
    assert results[0].youtube_url == "https://youtu.be/abc123"
