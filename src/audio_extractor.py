"""
Извлечение аудиодорожки из видеофайла через ffmpeg.

Использование:
    from src.audio_extractor import extract_audio
    duration = extract_audio(video_path, output_wav_path)
"""

import subprocess
from pathlib import Path


def extract_audio(video_path: Path, output_wav_path: Path) -> float:
    """
    Извлечь аудио из видео в формат WAV 16kHz mono.

    :param video_path: путь к видеофайлу
    :param output_wav_path: путь для сохранения WAV
    :return: длительность аудио в секундах
    :raises RuntimeError: при ошибке ffmpeg
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_wav_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.strip()}")

    duration_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(output_wav_path),
    ]

    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
    if duration_result.returncode == 0:
        try:
            return float(duration_result.stdout.strip())
        except ValueError:
            pass

    return 0.0
