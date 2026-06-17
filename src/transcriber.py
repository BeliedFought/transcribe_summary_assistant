"""
Транскрибация аудио через faster-whisper.

Модель кешируется в памяти (синглтон ModelCache) для переиспользования
между сессиями.

Использование:
    from src.transcriber import transcribe
    result = transcribe(audio_path, config)
"""

from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TranscriptionSegment:
    """Сегмент транскрипции."""

    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    """Результат транскрибации."""

    segments: list[TranscriptionSegment] = field(default_factory=list)
    language: str = ""
    confidence: float = 0.0
    word_count: int = 0


class ModelCache:
    """Синглтон для кеширования модели faster-whisper."""

    _instance: "ModelCache | None" = None
    _model: Any = None

    def __new__(cls) -> "ModelCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, model_size: str, device: str, compute_type: str) -> Any:
        """Получить (или загрузить) модель."""
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
        return self._model


def transcribe(
    audio_path: Path,
    config: ConfigParser,
    on_progress: "Any | None" = None,
) -> TranscriptionResult:
    """
    Транскрибировать аудиофайл через faster-whisper.

    :param audio_path: путь к аудиофайлу (WAV или поддерживаемый формат)
    :param config: ConfigParser с секцией [whisper]
    :param on_progress: опциональный колбэк(pct: float, seg_end: float, seg_count: int),
        вызывается по мере обработки сегментов
    :return: TranscriptionResult с сегментами, языком, уверенностью
    """
    model_size = config.get("whisper", "model_size", fallback="large-v3")
    device = config.get("whisper", "device", fallback="cuda")
    compute_type = config.get("whisper", "compute_type", fallback="float16")
    language = config.get("whisper", "language", fallback="ru")
    beam_size = config.getint("whisper", "beam_size", fallback=5)
    vad_filter = config.getboolean("whisper", "vad_filter", fallback=True)
    vad_min_duration = config.getint("whisper", "vad_min_speech_duration_ms", fallback=1000)
    vad_max_duration = config.getint("whisper", "vad_max_speech_duration_s", fallback=30)

    vad_params = None
    if vad_filter:
        vad_params = {
            "vad_filter": True,
            "vad_parameters": {
                "min_speech_duration_ms": vad_min_duration,
                "max_speech_duration_s": vad_max_duration,
            },
        }
    else:
        vad_params = {"vad_filter": False}

    cache = ModelCache()
    model = cache.get_model(model_size, device, compute_type)

    segments_raw, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=beam_size,
        **vad_params,
    )

    audio_duration = getattr(info, "duration", 0.0) or 0.0

    result = TranscriptionResult(
        language=info.language,
        confidence=0.0,
    )

    total_conf = 0.0
    total_words = 0
    segments_list: list[TranscriptionSegment] = []

    for seg in segments_raw:
        segments_list.append(TranscriptionSegment(
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
        ))
        word_count = len(seg.text.split())
        total_words += word_count
        total_conf += word_count * (seg.avg_logprob if seg.avg_logprob else 0.0)

        if on_progress is not None:
            pct = (seg.end / audio_duration * 100.0) if audio_duration > 0 else 0.0
            try:
                on_progress(pct, seg.end, len(segments_list))
            except Exception:
                pass

    if total_words > 0:
        result.confidence = total_conf / total_words

    result.word_count = total_words
    result.segments = segments_list

    return result
