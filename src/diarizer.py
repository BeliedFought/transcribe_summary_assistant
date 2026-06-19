"""
Диаризация (разделение по голосам) через pyannote.audio.

Использование:
    from src.diarizer import diarize, align_segments
    speakers = diarize(audio_path, config)
    aligned = align_segments(transcription_segments, speakers)
"""

from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.localization import t


@dataclass
class SpeakerSegment:
    """Временный сегмент диктора."""

    start: float
    end: float
    speaker_id: str


@dataclass
class AlignedSegment:
    """Сегмент транскрипции, привязанный к диктору."""

    start: float
    end: float
    text: str
    speaker_id: str


_pipeline: Any = None


def _get_pipeline(config: ConfigParser) -> Any:
    """Получить (или загрузить) pyannote pipeline."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    import os
    from pyannote.audio import Pipeline

    hf_token = os.environ.get("HF_TOKEN", "")
    hf_model = config.get("diarization", "hf_model", fallback="pyannote/speaker-diarization-3.1")

    _pipeline = Pipeline.from_pretrained(
        hf_model,
        token=hf_token,
    )

    device = config.get("whisper", "device", fallback="cpu")
    if device == "cuda":
        import torch
        if torch.cuda.is_available():
            _pipeline.to(torch.device("cuda"))

    return _pipeline


def diarize(audio_path: Path, config: ConfigParser) -> list[SpeakerSegment]:
    """
    Выполнить диаризацию аудиофайла.

    Перед подачей в pyannote аудио конвертируется в WAV 16kHz через ffmpeg.
    Это решает проблему несоответствия длины чанков для mp3 (VBR/CBR
    кодирование дает нецелое число сэмплов на 10-секундный чанк).

    :param audio_path: путь к аудиофайлу
    :param config: ConfigParser с секциеи [diarization]
    :return: список сегментов дикторов
    """
    import os
    import subprocess
    import tempfile

    min_speakers = config.getint("diarization", "min_speakers", fallback=1)
    max_speakers = config.getint("diarization", "max_speakers", fallback=10)

    wav_fd, wav_name = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)
    wav_path = Path(wav_name)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(audio_path),
                "-ar", "16000",
                "-ac", "1",
                "-f", "wav",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )

        pipeline = _get_pipeline(config)
        output = pipeline(
            str(wav_path),
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
    finally:
        wav_path.unlink(missing_ok=True)

    segments: list[SpeakerSegment] = []

    for turn, _, speaker in output.speaker_diarization.itertracks(yield_label=True):
        segments.append(SpeakerSegment(
            start=turn.start,
            end=turn.end,
            speaker_id=speaker,
        ))

    segments.sort(key=lambda s: s.start)

    unique_speakers = sorted(set(s.speaker_id for s in segments))
    total = len(unique_speakers)
    width = len(str(total)) if total > 1 else 0
    speaker_names: dict[str, str] = {}
    for i, speaker_id in enumerate(unique_speakers, 1):
        if width:
            speaker_names[speaker_id] = t("label.speaker", number=f"{i:0{width}d}")
        else:
            speaker_names[speaker_id] = t("label.speaker", number=str(i))

    for seg in segments:
        seg.speaker_id = speaker_names[seg.speaker_id]

    return segments


def _midpoint(seg: Any) -> float:
    """Средняя точка сегмента."""
    return (seg.start + seg.end) / 2.0


def align_segments(
    transcription_segments: list[Any],
    speaker_segments: list[SpeakerSegment],
) -> list[AlignedSegment]:
    """
    Привязать сегменты транскрипции к дикторам по временным меткам.

    Стратегия: для каждого сегмента транскрипции находим диктора,
    чей интервал максимально пересекается с сегментом. Если пересечения
    нет - назначаем [неизвестно].

    :param transcription_segments: сегменты транскрипции (start, end, text)
    :param speaker_segments: сегменты дикторов
    :return: AlignedSegment с привязкой к дикторам
    """
    aligned: list[AlignedSegment] = []

    for tseg in transcription_segments:
        best_speaker = t("label.unknown_speaker")
        best_overlap = 0.0

        for sseg in speaker_segments:
            overlap_start = max(tseg.start, sseg.start)
            overlap_end = min(tseg.end, sseg.end)
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = sseg.speaker_id

        aligned.append(AlignedSegment(
            start=tseg.start,
            end=tseg.end,
            text=tseg.text,
            speaker_id=best_speaker,
        ))

    return aligned
