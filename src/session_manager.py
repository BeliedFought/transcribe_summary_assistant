"""
Управление сессиями обработки.

Создание папок сессии, генерация ID, сохранение метаданных,
транскрипции, саммари.

Использование:
    from src.session_manager import create_session, save_transcription, save_summary
    session_id, session_dir = create_session(file_info)
    save_transcription(session_dir, content)
    save_summary(session_dir, content)
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from src.config import PROJECT_ROOT
from src.file_scanner import FileInfo
from src.localization import t


def generate_session_id(source_path: Path) -> str:
    """Сгенерировать уникальный ID сессии."""
    file_hash = hashlib.sha256()
    with open(source_path, "rb") as f:
        while chunk := f.read(8192):
            file_hash.update(chunk)
    hash_hex = file_hash.hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{timestamp}_{hash_hex}"


def create_session_dir(session_id: str) -> Path:
    """Создать папку сессии и вернуть путь к ней."""
    sessions_root = PROJECT_ROOT / "data" / "sessions"
    session_dir = sessions_root / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def save_metadata(session_dir: Path, metadata: dict) -> Path:
    """Сохранить metadata.json атомарно."""
    target = session_dir / "metadata.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(target)
    return target


def save_transcription(session_dir: Path, content: str) -> Path:
    """Сохранить transcription.md атомарно."""
    target = session_dir / "transcription.md"
    temp = target.with_suffix(".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(target)
    return target


def save_transcription_raw(session_dir: Path, result: dict) -> Path:
    """
    Сохранить сырую транскрипцию (segments + мета) в JSON атомарно.

    Используется для кеша: при повторном запуске того же файла транскрипция
    загружается из JSON, транскрибация пропускается.
    :param result: словарь с ключами segments, language, confidence, word_count
    """
    target = session_dir / "transcription.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    temp.replace(target)
    return target


def load_transcription_raw(session_dir: Path) -> dict | None:
    """
    Загрузить сырую транскрипцию из JSON.

    :return: словарь или None, если файл отсутствует/поврежден
    """
    path = session_dir / "transcription.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_diarization_raw(session_dir: Path, result: dict) -> Path:
    """
    Сохранить сырую диаризацию (сегменты дикторов) в JSON атомарно.

    Используется для кеша: при повторном запуске того же файла диаризация
    загружается из JSON, запуск pyannote на GPU пропускается.
    :param result: словарь с ключом segments (start, end, speaker_id)
    """
    target = session_dir / "diarization.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    temp.replace(target)
    return target


def load_diarization_raw(session_dir: Path) -> dict | None:
    """
    Загрузить сырую диаризацию из JSON.

    :return: словарь или None, если файл отсутствует/поврежден
    """
    path = session_dir / "diarization.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_summary(session_dir: Path, content: str) -> Path:
    """Сохранить summary.md атомарно."""
    target = session_dir / "summary.md"
    temp = target.with_suffix(".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(target)
    return target


def save_article(session_dir: Path, content: str) -> Path:
    """Сохранить article.md атомарно."""
    target = session_dir / "article.md"
    temp = target.with_suffix(".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(target)
    return target


def copy_summary_to_output(session_id: str, session_dir: Path) -> Path:
    """Скопировать summary.md в output/."""
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    source = session_dir / "summary.md"
    dest = output_dir / f"{session_id}_summary.md"
    temp = dest.with_suffix(".tmp")
    if source.exists():
        shutil.copy2(source, temp)
        temp.replace(dest)
    return dest


def copy_article_to_output(session_id: str, session_dir: Path) -> Path:
    """Скопировать article.md в output/."""
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    source = session_dir / "article.md"
    dest = output_dir / f"{session_id}_article.md"
    temp = dest.with_suffix(".tmp")
    if source.exists():
        shutil.copy2(source, temp)
        temp.replace(dest)
    return dest


def build_transcription_markdown(
    aligned_segments: list,
    source_filename: str,
    duration_seconds: float,
    language: str,
    whisper_model: str,
    speaker_count: int,
    processed_at: str,
) -> str:
    """
    Сформировать transcription.md в формате Markdown.

    :param aligned_segments: список AlignedSegment
    :param source_filename: имя исходного файла
    :param duration_seconds: длительность в секундах
    :param language: язык транскрипции
    :param whisper_model: модель whisper
    :param speaker_count: количество дикторов
    :param processed_at: время обработки
    :return: строка Markdown
    """
    mins = int(duration_seconds // 60)
    secs = int(duration_seconds % 60)

    lines: list[str] = [
        t("msg.transcription_md_title", source=source_filename),
        "",
        t("msg.transcription_md_date", date=processed_at),
        t("msg.transcription_md_duration", mins=mins, secs=secs),
        t("msg.transcription_md_language", language=language),
        t("msg.transcription_md_model", model=whisper_model),
        t("msg.transcription_md_diarization", speakers=speaker_count),
        "",
        "---",
        "",
        t("msg.transcription_md_section"),
        "",
    ]

    for seg in aligned_segments:
        start_ts = _format_timestamp(seg.start)
        end_ts = _format_timestamp(seg.end)
        lines.append(f"[{start_ts} -> {end_ts}] **{seg.speaker_id}:** {seg.text}")

    return "\n".join(lines)


def build_summary_markdown(
    summary_text: str,
    source_block: str,
    processed_date: str,
    summarizer_engine: str,
    speakers_list: str,
    summarizer_params: dict | None = None,
) -> str:
    """
    Сформировать summary.md в формате Markdown.

    :param summary_text: текст саммари от API
    :param source_block: многострочное описание источника (канал/ссылки/подписчики
                         для YouTube или файл/длительность/размер для аудио-видео)
    :param processed_date: дата обработки
    :param summarizer_engine: движок саммаризации
    :param speakers_list: строка со списком дикторов
    :param summarizer_params: доп. параметры (model, tokens, temperature)
    :return: строка Markdown
    """
    lines: list[str] = [
        t("msg.summary_md_heading"),
        "",
        f"**{t('msg.summary_md_source_label')}:**",
        source_block,
        "",
        t("msg.summary_md_date", date=processed_date),
    ]

    if summarizer_params:
        engine_parts = [summarizer_engine]
        if summarizer_params.get("model"):
            engine_parts[0] = summarizer_params["model"]
        lines.append(t("msg.summary_md_engine", engine=", ".join(engine_parts)))

        if summarizer_params.get("temperature") is not None:
            lines.append(
                "**{label}:** {temp}".format(
                    label=t("label.temperature"),
                    temp=summarizer_params["temperature"],
                )
            )
        tokens_in = summarizer_params.get("prompt_tokens", 0)
        tokens_out = summarizer_params.get("completion_tokens", 0)
        if tokens_in or tokens_out:
            lines.append(
                "**{label}:** {in_} (prompt) + {out} (completion) = {total}".format(
                    label=t("label.tokens"),
                    in_=tokens_in,
                    out=tokens_out,
                    total=tokens_in + tokens_out,
                )
            )
    else:
        lines.append(t("msg.summary_md_engine", engine=summarizer_engine))

    lines += [
        t("msg.summary_md_speakers", speakers=speakers_list),
        "",
        "---",
        "",
        summary_text.strip(),
    ]

    return "\n".join(lines)


def _format_timestamp(seconds: float) -> str:
    """Форматировать секунды в HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
