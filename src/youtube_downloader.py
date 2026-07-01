"""
Загрузка аудио из YouTube через yt-dlp.

Использование:
    from src.youtube_downloader import download_audio, get_video_title
    audio_path, video_title = download_audio("https://youtube.com/watch?v=...", output_dir, config)
"""

import re
import shutil
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path

_INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_VIDEO_EXTS: tuple[str, ...] = (".mp4", ".webm", ".mkv", ".mov", ".avi")


def _find_ytdlp() -> str:
    """Найти исполняемый файл yt-dlp."""
    ytdlp_path = shutil.which("yt-dlp")
    if not ytdlp_path:
        venv_path = Path(sys.executable).parent / "yt-dlp"
        if venv_path.exists():
            ytdlp_path = str(venv_path)
    if not ytdlp_path:
        raise RuntimeError("yt-dlp not found")
    return ytdlp_path


def _term_width() -> int:
    """Вернуть ширину терминала (минимум 80)."""
    try:
        return max(shutil.get_terminal_size().columns, 80)
    except Exception:
        return 80


_YTDLP = _find_ytdlp()


def _sanitize_name(name: str) -> str:
    """Заменить недопустимые в имени файла/папки символы и убрать крайние точки/пробелы."""
    cleaned = _INVALID_NAME_CHARS.sub("_", name).strip().rstrip(".")
    return cleaned or "unknown"


def _extract_video_id(url: str) -> str:
    """Извлечь video ID из ссылки YouTube (или вернуть исходную ссылку)."""
    match = re.search(r"(?:v=|youtu\.be/|embed/)([\w-]{6,})", url)
    return match.group(1) if match else url


def get_video_title(youtube_url: str) -> str:
    """
    Получить название видео YouTube через yt-dlp.

    :param youtube_url: ссылка на видео YouTube
    :return: название видео
    :raises RuntimeError: при ошибке получения названия
    """
    cmd = [
        _YTDLP,
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
        _YTDLP,
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
        _YTDLP,
        "-f", audio_format,
        "-o", url_output_template,
        "--no-playlist",
        "--extract-audio",
        "--remote-components", "ejs:github",
        "--progress-template", "progress:%(progress._percent_str)s:%(progress._speed_str)s:%(progress._eta_str)s",
        "--newline",
        youtube_url,
    ]

    stderr_lines: list[str] = []
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
        assert process.stdout is not None
        for line in process.stdout:
            line_stripped = line.strip()
            if line_stripped.startswith("progress:") and line_stripped.count(":") >= 3:
                _, pct_str, speed, eta = line_stripped.split(":", 3)
                try:
                    pct = float(pct_str.strip().rstrip("%"))
                    bar_w = 30
                    filled = int(pct / 100 * bar_w)
                    bar = "\u2588" * filled + "\u2591" * (bar_w - filled)
                    line = f"\r{bar} {pct:.1f}% {speed} ETA {eta}"
                    line = line.ljust(_term_width())
                    sys.stdout.write(line)
                    sys.stdout.flush()
                except ValueError:
                    pass
        returncode = process.wait()
        sys.stdout.write("\r" + " " * _term_width() + "\r")
        sys.stdout.flush()
        if process.stderr is not None:
            stderr_lines = process.stderr.read().strip().splitlines()

    if returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {'; '.join(stderr_lines) if stderr_lines else 'unknown error'}")

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


def download_video(youtube_url: str, output_dir: Path, config: ConfigParser) -> tuple[str, Path | None]:
    """
    Скачать видео из YouTube целиком (видео + аудио), качество не выше 720p.

    Файл сохраняется в подпапку по названию канала:
    ``output_dir/<канал>/<канал> - <название>.<ext>``. Имя файла берется из
    параметра ``[youtube] download_template`` конфига.

    Идемпотентность: отслеживание скачанных ссылок по video ID через
    archive-файл yt-dlp (``output_dir/.ytdl_archive``). При повторном запуске
    уже скачанная ссылка пропускается без повторного обращения к сети.

    :param youtube_url: ссылка на видео YouTube
    :param output_dir: корневая папка-приемник (создается подпапка канала)
    :param config: ConfigParser с секцией ``[youtube]``
    :return: кортеж ``(статус, путь)``. Статус ``"downloaded"`` - файл скачан,
             ``"skipped"`` - ссылка уже была скачана ранее (путь None)
    :raises RuntimeError: при ошибке загрузки
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_path = output_dir / ".ytdl_archive"
    video_id = _extract_video_id(youtube_url)
    if archive_path.exists() and video_id in archive_path.read_text(encoding="utf-8").splitlines():
        return "skipped", None

    channel = ""
    try:
        channel = (get_channel_info(youtube_url).get("channel") or "").strip()
    except Exception:
        channel = ""
    channel_dir = output_dir / _sanitize_name(channel or "unknown")
    channel_dir.mkdir(parents=True, exist_ok=True)

    download_template = config.get(
        "youtube", "download_template", fallback="%(channel)s - %(title)s.%(ext)s"
    )
    output_template = str(channel_dir / download_template)

    cmd = [
        _YTDLP,
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "-o", output_template,
        "--no-playlist",
        "--merge-output-format", "mp4",
        "--download-archive", str(archive_path),
        "--remote-components", "ejs:github",
        "--progress-template", "progress:%(progress._percent_str)s:%(progress._speed_str)s:%(progress._eta_str)s",
        "--newline",
        youtube_url,
    ]

    before = {p for p in channel_dir.iterdir() if p.is_file()}
    stderr_lines: list[str] = []
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
        assert process.stdout is not None
        for line in process.stdout:
            line_stripped = line.strip()
            if line_stripped.startswith("progress:") and line_stripped.count(":") >= 3:
                _, pct_str, speed, eta = line_stripped.split(":", 3)
                try:
                    pct = float(pct_str.strip().rstrip("%"))
                    bar_w = 30
                    filled = int(pct / 100 * bar_w)
                    bar = "\u2588" * filled + "\u2591" * (bar_w - filled)
                    line = f"\r{bar} {pct:.1f}% {speed} ETA {eta}"
                    line = line.ljust(_term_width())
                    sys.stdout.write(line)
                    sys.stdout.flush()
                except ValueError:
                    pass
        returncode = process.wait()
        sys.stdout.write("\r" + " " * _term_width() + "\r")
        sys.stdout.flush()
        if process.stderr is not None:
            stderr_lines = process.stderr.read().strip().splitlines()

    if returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {'; '.join(stderr_lines) if stderr_lines else 'unknown error'}")

    new_files = sorted(
        (p for p in channel_dir.iterdir() if p.is_file() and p not in before),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    new_files = [p for p in new_files if p.suffix.lower() in _VIDEO_EXTS]

    if not new_files:
        return "skipped", None

    return "downloaded", new_files[0]
