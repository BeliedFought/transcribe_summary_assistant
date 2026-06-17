"""
Загрузка аудио из YouTube через yt-dlp.

Использование:
    from src.youtube_downloader import download_audio, get_video_title
    audio_path, video_title = download_audio("https://youtube.com/watch?v=...", output_dir, config)
"""

import subprocess
from configparser import ConfigParser
from pathlib import Path


def get_video_title(youtube_url: str) -> str:
    """
    Получить название видео YouTube через yt-dlp.

    :param youtube_url: ссылка на видео YouTube
    :return: название видео
    :raises RuntimeError: при ошибке получения названия
    """
    cmd = [
        "yt-dlp",
        "--print", "title",
        "--no-playlist",
        youtube_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp --print title failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_channel_info(youtube_url: str) -> dict[str, str]:
    """
    Получить информацию о канале YouTube через yt-dlp.

    :param youtube_url: ссылка на видео YouTube
    :return: словарь с ключами channel, channel_url, subscribers
             (subscribers - пустая строка, если недоступно)
    :raises RuntimeError: при ошибке получения данных
    """
    cmd = [
        "yt-dlp",
        "--print", "channel",
        "--print", "channel_url",
        "--print", "channel_follower_count",
        "--no-playlist",
        youtube_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp channel info failed: {result.stderr.strip()}")
    lines = result.stdout.strip().splitlines()
    channel = lines[0].strip() if len(lines) > 0 else ""
    channel_url = lines[1].strip() if len(lines) > 1 else ""
    subscribers = lines[2].strip() if len(lines) > 2 else ""
    if subscribers in ("NA", "None"):
        subscribers = ""
    return {
        "channel": channel,
        "channel_url": channel_url,
        "subscribers": subscribers,
    }


def download_audio(youtube_url: str, output_dir: Path, config: ConfigParser) -> tuple[Path, str]:
    """
    Скачать аудио из YouTube через yt-dlp.

    :param youtube_url: ссылка на видео YouTube
    :param output_dir: папка для сохранения аудио
    :param config: ConfigParser с секцией [youtube]
    :return: кортеж (путь к скачанному аудиофайлу, название видео)
    :raises RuntimeError: при ошибке загрузки
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_format = config.get("youtube", "audio_format", fallback="bestaudio/best")

    url_output_template = str(output_dir / "%(id)s_%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-f", audio_format,
        "-o", url_output_template,
        "--no-playlist",
        "--extract-audio",
        youtube_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")

    audio_files = sorted(
        output_dir.iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    audio_files = [f for f in audio_files if f.is_file() and f.suffix.lower() in (".opus", ".m4a", ".webm", ".mp3", ".wav")]

    if not audio_files:
        raise RuntimeError("yt-dlp: no audio file found after download")

    video_title = get_video_title(youtube_url)

    return audio_files[0], video_title
