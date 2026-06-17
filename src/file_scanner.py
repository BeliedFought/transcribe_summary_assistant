"""
Сканирование папок input/ для поиска файлов для обработки.

Использование:
    from src.file_scanner import scan_input_dirs, compute_file_hash, FileInfo
    files = scan_input_dirs(config)
"""

import hashlib
import re
from dataclasses import dataclass
from configparser import ConfigParser
from pathlib import Path

from src.config import PROJECT_ROOT

YOUTUBE_PATTERNS: list[str] = [
    r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
    r"https?://youtu\.be/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/embed/[\w-]+",
]


@dataclass
class FileInfo:
    """Информация о файле для обработки."""

    path: Path
    filename: str
    file_type: str  # 'audio', 'video', 'youtube_link'
    extension: str
    size_bytes: int
    youtube_url: str | None = None


def compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Вычислить SHA256-хеш файла."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def _find_youtube_links(text: str) -> list[str]:
    """
    Найти все ссылки на YouTube в тексте.

    Возвращает уникальные ссылки в порядке их появления (с сохранением
    первого вхождения при дубликатах).
    """
    combined = re.compile("|".join(f"(?:{p})" for p in YOUTUBE_PATTERNS))
    found: list[str] = []
    seen: set[str] = set()
    for match in combined.finditer(text):
        url = match.group(0)
        if url not in seen:
            seen.add(url)
            found.append(url)
    return found


def _extract_youtube_id(url: str) -> str:
    """
    Извлечь video ID из ссылки YouTube.

    :return: video ID или исходная ссылка, если ID не извлечен
    """
    match = re.search(r"(?:v=|youtu\.be/|embed/)([\w-]{6,})", url)
    return match.group(1) if match else url


def scan_input_dirs(config: ConfigParser) -> list[FileInfo]:
    """
    Сканировать папки input/audio/, input/video/, input/yt/.

    :param config: ConfigParser с секцией [processing]
    :return: список FileInfo
    """
    audio_ext = config.get("processing", "audio_extensions", fallback=".mp3,.wav,.flac,.ogg,.m4a,.opus")
    video_ext = config.get("processing", "video_extensions", fallback=".mp4,.webm,.mkv,.mov,.avi")
    text_ext = config.get("processing", "text_extensions", fallback=".txt")

    audio_extensions: set[str] = {e.strip().lower() for e in audio_ext.split(",") if e.strip()}
    video_extensions: set[str] = {e.strip().lower() for e in video_ext.split(",") if e.strip()}
    text_extensions: set[str] = {e.strip().lower() for e in text_ext.split(",") if e.strip()}

    results: list[FileInfo] = []
    seen_urls: set[str] = set()
    input_root = PROJECT_ROOT / "input"

    audio_dir = input_root / "audio"
    if audio_dir.exists():
        for file_path in sorted(audio_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                results.append(FileInfo(
                    path=file_path,
                    filename=file_path.name,
                    file_type="audio",
                    extension=file_path.suffix.lower(),
                    size_bytes=file_path.stat().st_size,
                ))

    video_dir = input_root / "video"
    if video_dir.exists():
        for file_path in sorted(video_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                results.append(FileInfo(
                    path=file_path,
                    filename=file_path.name,
                    file_type="video",
                    extension=file_path.suffix.lower(),
                    size_bytes=file_path.stat().st_size,
                ))

    yt_dir = input_root / "yt"
    if yt_dir.exists():
        for file_path in sorted(yt_dir.iterdir()):
            if not (file_path.is_file() and file_path.suffix.lower() in text_extensions):
                continue
            content = file_path.read_text(encoding="utf-8")
            for youtube_url in _find_youtube_links(content):
                if youtube_url in seen_urls:
                    continue
                seen_urls.add(youtube_url)
                video_id = _extract_youtube_id(youtube_url)
                results.append(FileInfo(
                    path=file_path,
                    filename=video_id,
                    file_type="youtube_link",
                    extension=file_path.suffix.lower(),
                    size_bytes=file_path.stat().st_size,
                    youtube_url=youtube_url,
                ))

    return results
