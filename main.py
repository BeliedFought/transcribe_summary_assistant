"""
Оркестратор пайплайна обработки.

Запуск: python main.py

Сканирует папки input/audio/, input/video/, input/yt/ и обрабатывает
все найденные файлы: транскрибация, диаризация, саммаризация.
Каждый запуск создает новые сессии для всех файлов в input/.
"""

import signal
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.config import PROJECT_ROOT, config, APP_NAME, APP_VERSION
from src.cuda_loader import preload_cuda_libs
from src.logger import get_logger
from src.localization import init as i18n_init, t
from src.progress import clear_progress

preload_cuda_libs()
logger = get_logger("main", log_dir=PROJECT_ROOT / "log")
i18n_init(db_path=PROJECT_ROOT / "data" / "sessions.db")


def _signal_handler(sig: int, frame: object) -> None:
    """Обработчик SIGINT."""
    clear_progress()
    logger.info(t("msg.interrupted"))
    sys.exit(1)


signal.signal(signal.SIGINT, _signal_handler)


def _validate_environment() -> None:
    """Проверка окружения перед запуском (fail fast)."""
    logger.info(t("msg.validating"))

    errors: list[str] = []

    required_dirs = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "log",
        PROJECT_ROOT / "output",
    ]
    for d in required_dirs:
        if not d.exists():
            errors.append(t("error.folder_not_found", path=str(d)))

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            errors.append(t("error.ffmpeg_not_found"))
    except FileNotFoundError:
        errors.append(t("error.ffmpeg_not_found"))

    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            errors.append(t("error.ytdlp_not_found"))
    except FileNotFoundError:
        errors.append(t("error.ytdlp_not_found"))

    import os
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not deepseek_key:
        errors.append(t("error.api_key_missing", key="DEEPSEEK_API_KEY"))

    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        errors.append(t("error.api_key_missing", key="HF_TOKEN"))

    if errors:
        for err in errors:
            logger.error(err)
        sys.exit(1)

    from src.preflight import check_all
    preflight_errors = check_all(config)
    if preflight_errors:
        sys.exit(1)

    logger.info(t("msg.validation_passed"))


def _build_sources_summary(files: list) -> str:
    """Сформировать сводку источников к обработке по типам с плюрализацией."""
    from collections import Counter

    counts = Counter(f.file_type for f in files)
    parts: list[str] = []
    if counts.get("youtube_link"):
        parts.append(t("msg.src_links", count=counts["youtube_link"]))
    if counts.get("video"):
        parts.append(t("msg.src_video", count=counts["video"]))
    if counts.get("audio"):
        parts.append(t("msg.src_audio", count=counts["audio"]))
    return t("label.list_separator").join(parts)


def main() -> None:
    """Основная логика пайплайна."""
    logger.info(t("msg.app_started", name=APP_NAME, version=APP_VERSION))

    _validate_environment()

    from src.file_scanner import scan_input_dirs, FileInfo
    from src.db_manager import init_db, create_session, update_session, enqueue_stage

    db_path = PROJECT_ROOT / "data" / "sessions.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    init_db(conn)

    from src.db_manager import verify_schema, translations_count
    schema_ok, problems = verify_schema(conn)
    if not schema_ok:
        for problem in problems:
            logger.error(t("error.db_schema_problem", problem=problem))
        logger.error(t("error.run_db_init"))
        conn.close()
        sys.exit(1)
    logger.info(t("msg.schema_ok"))

    if translations_count(conn) == 0:
        logger.error(t("error.translations_empty"))
        logger.error(t("error.run_db_init"))
        conn.close()
        sys.exit(1)

    files = scan_input_dirs(config)
    if not files:
        logger.info(t("msg.nothing_to_process"))
        conn.close()
        return

    logger.info(t("msg.sources_summary", parts=_build_sources_summary(files)))

    success_count = 0
    failed_count = 0

    for file_info in files:
        try:
            _process_file(file_info, conn)
            success_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(t("msg.session_failed", session_id=file_info.filename, error=str(e)))

    logger.info(t("msg.all_done", total=success_count + failed_count, success=success_count, failed=failed_count))
    conn.close()


def _speaker_sort_key(name: str) -> int:
    """Извлечь номер диктора для числовой сортировки."""
    import re
    m = re.search(r"\d+", name)
    return int(m.group()) if m else 0


def _format_duration(seconds: float) -> str:
    """Форматировать длительность в H:MM:SS или M:SS."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_size(size_bytes: int) -> str:
    """Форматировать размер файла в человекочитаемый вид."""
    value = float(size_bytes)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if value < 1024 or unit == "ГБ":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} ГБ"


def _format_subscribers(count_str: str) -> str:
    """Форматировать число подписчиков; пустое значение - 'н/д'."""
    count_str = count_str.strip()
    if not count_str:
        return t("label.not_available")
    try:
        count = int(count_str)
    except ValueError:
        return t("label.not_available")
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f} {t('label.million')}".replace(".", ",")
    if count >= 1_000:
        return f"{count / 1_000:.0f} {t('label.thousand')}"
    return str(count)


def _build_source_block(file_info: "FileInfo", duration_sec: float) -> tuple[str, str]:
    """
    Сформировать многострочное описание источника для шапки саммари.

    :return: (блок описания, имя канала; пусто для источников без канала)
    """
    if file_info.file_type == "youtube_link" and file_info.youtube_url:
        channel = ""
        channel_url = ""
        subscribers = ""
        try:
            from src.youtube_downloader import get_channel_info
            info = get_channel_info(file_info.youtube_url)
            channel = info.get("channel", "")
            channel_url = info.get("channel_url", "")
            subscribers = info.get("subscribers", "")
        except Exception as e:
            logger.warning(t("msg.yt_channel_info_failed", detail=str(e)))

        lines = [
            t("msg.src_md_channel", name=channel or file_info.youtube_url),
            t("msg.src_md_subscribers", value=_format_subscribers(subscribers)),
            t("msg.src_md_video_url", url=file_info.youtube_url),
        ]
        if channel_url:
            lines.append(t("msg.src_md_channel_url", url=channel_url))
        return "\n".join(lines), channel

    return "\n".join([
        t("msg.src_md_file", name=file_info.filename),
        t("msg.src_md_duration", duration=_format_duration(duration_sec)),
        t("msg.src_md_size", size=_format_size(file_info.size_bytes)),
    ]), ""


def _process_file(file_info: "FileInfo", conn: sqlite3.Connection) -> None:
    """Обработать один файл."""
    from src.session_manager import (
        generate_session_id,
        create_session_dir,
        save_metadata,
        save_transcription,
        save_transcription_raw,
        load_transcription_raw,
        save_diarization_raw,
        load_diarization_raw,
        save_summary,
        save_article,
        build_transcription_markdown,
        build_summary_markdown,
        copy_summary_to_output,
        copy_article_to_output,
    )
    from src.db_manager import create_session, update_session, enqueue_stage, update_stage

    processing_start = datetime.now()

    audio_path = file_info.path

    video_title = ""
    if file_info.file_type == "youtube_link" and file_info.youtube_url:
        from src.youtube_downloader import download_audio, get_video_title
        from src.db_manager import find_sessions_by_youtube_url

        prev_sessions = find_sessions_by_youtube_url(conn, file_info.youtube_url)

        reused_path: Path | None = None
        for prev in prev_sessions:
            prev_audio = Path(prev.get("original_path", ""))
            if prev_audio.exists():
                reused_path = prev_audio
                break

        # осмысленное название берем из прежних сессий; пропускаем технические
        # значения: имя файла ссылок (link.txt) и video_id, которые не являются
        # настоящим названием ролика
        stale_names = {file_info.path.name, file_info.filename}
        for prev in prev_sessions:
            candidate = (prev.get("source_filename") or "").strip()
            if candidate and candidate not in stale_names:
                video_title = candidate
                break

        if reused_path is not None:
            audio_path = reused_path
            logger.info(
                t("msg.yt_reused", url=file_info.youtube_url, filename=audio_path.name)
            )
        else:
            logger.info(t("msg.yt_downloading", url=file_info.youtube_url))
            temp_dir = PROJECT_ROOT / "debug" / "yt_audio"
            temp_dir.mkdir(parents=True, exist_ok=True)
            audio_path, dl_title = download_audio(file_info.youtube_url, temp_dir, config)
            if dl_title:
                video_title = dl_title
            logger.info(t("msg.yt_downloaded", filename=audio_path.name))

        if not video_title:
            try:
                video_title = get_video_title(file_info.youtube_url)
            except Exception as e:
                logger.warning(t("msg.yt_title_failed", detail=str(e)))

    session_id = generate_session_id(audio_path)
    session_dir = create_session_dir(session_id)
    logger.info(t("msg.session_created", session_id=session_id))

    file_hash = ""
    try:
        from src.file_scanner import compute_file_hash
        file_hash = compute_file_hash(audio_path)
    except Exception:
        pass

    file_size = audio_path.stat().st_size if audio_path.exists() else 0

    source_filename = file_info.filename
    if file_info.file_type == "youtube_link" and video_title:
        source_filename = video_title

    session_data = {
        "id": session_id,
        "source_filename": source_filename,
        "source_type": file_info.file_type,
        "source_url": file_info.youtube_url or "",
        "original_path": str(audio_path),
        "session_dir": str(session_dir),
        "file_size_bytes": file_size,
        "file_hash": file_hash,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    create_session(conn, session_data)

    wav_path: Path | None = None
    duration_sec = 0.0

    try:
        if file_info.file_type == "video":
            enqueue_stage(conn, session_id, "audio_extraction")
            from src.audio_extractor import extract_audio
            logger.info(t("msg.extracting_audio", filename=file_info.filename))
            wav_path = PROJECT_ROOT / "debug" / f"{session_id}.wav"
            wav_path.parent.mkdir(parents=True, exist_ok=True)
            duration = extract_audio(file_info.path, wav_path)
            audio_path = wav_path
            update_session(conn, session_id, {"duration_seconds": duration})
            update_stage(conn, session_id, "audio_extraction", "completed")

        enqueue_stage(conn, session_id, "transcription")
        from src.transcriber import transcribe, TranscriptionSegment, TranscriptionResult
        from src.progress import update_progress
        from src.db_manager import find_cached_transcription

        trans_result: TranscriptionResult | None = None

        if file_hash:
            for cached in find_cached_transcription(conn, file_hash):
                cached_dir = Path(cached["session_dir"])
                raw = load_transcription_raw(cached_dir)
                if raw is None:
                    continue
                segments = [
                    TranscriptionSegment(
                        start=s["start"],
                        end=s["end"],
                        text=s["text"],
                    )
                    for s in raw.get("segments", [])
                ]
                trans_result = TranscriptionResult(
                    segments=segments,
                    language=raw.get("language", ""),
                    confidence=raw.get("confidence", 0.0),
                    word_count=raw.get("word_count", 0),
                )
                logger.info(t("msg.transcription_cached", session_id=cached["id"]))
                break

        if trans_result is None:
            transcribe_display = video_title or file_info.filename
            logger.info(t("msg.transcribing", filename=transcribe_display))

            def _on_transcribe_progress(pct: float, seg_end: float, seg_count: int) -> None:
                update_progress(
                    t("msg.transcribing_progress", pct=pct)
                    + " "
                    + t("msg.transcribing_progress_detail", segments=seg_count, seconds=int(seg_end))
                )

            trans_result = transcribe(audio_path, config, on_progress=_on_transcribe_progress)
            clear_progress()

            save_transcription_raw(session_dir, {
                "segments": [
                    {"start": s.start, "end": s.end, "text": s.text}
                    for s in trans_result.segments
                ],
                "language": trans_result.language,
                "confidence": trans_result.confidence,
                "word_count": trans_result.word_count,
            })

        logger.info(
            t(
                "msg.whisper_result",
                words=trans_result.word_count,
                confidence=trans_result.confidence,
                language=trans_result.language,
            )
        )
        update_stage(conn, session_id, "transcription", "completed")

        update_session(conn, session_id, {
            "whisper_model": config.get("whisper", "model_size", fallback="large-v3"),
            "whisper_language": trans_result.language,
            "whisper_confidence": trans_result.confidence,
            "word_count": trans_result.word_count,
            "status": "transcribed",
        })

        speaker_segments = []
        speaker_count = 0
        aligned_segments = []

        if config.getboolean("diarization", "enabled", fallback=True):
            enqueue_stage(conn, session_id, "diarization")
            from src.diarizer import diarize, align_segments as do_align, SpeakerSegment

            diarization_loaded_from_cache = False
            if file_hash:
                for cached in find_cached_transcription(conn, file_hash):
                    cached_dir = Path(cached["session_dir"])
                    raw = load_diarization_raw(cached_dir)
                    if raw is None:
                        continue
                    speaker_segments = [
                        SpeakerSegment(
                            start=s["start"],
                            end=s["end"],
                            speaker_id=s["speaker_id"],
                        )
                        for s in raw.get("segments", [])
                    ]
                    logger.info(t("msg.diarization_cached", session_id=cached["id"]))
                    diarization_loaded_from_cache = True
                    break

            if not diarization_loaded_from_cache:
                diarize_display = video_title or file_info.filename
                logger.info(t("msg.diarizing", filename=diarize_display))
                speaker_segments = diarize(audio_path, config)
                save_diarization_raw(session_dir, {
                    "segments": [
                        {"start": s.start, "end": s.end, "speaker_id": s.speaker_id}
                        for s in speaker_segments
                    ],
                })

            speaker_ids = set(s.speaker_id for s in speaker_segments)
            speaker_count = len(speaker_ids)
            logger.info(t("msg.diarization_result", count=speaker_count))
            update_stage(conn, session_id, "diarization", "completed")

            aligned_segments = do_align(trans_result.segments, speaker_segments)
        else:
            aligned_segments = trans_result.segments

        duration_sec = 0.0
        if speaker_segments:
            duration_sec = max(s.end for s in speaker_segments)
        elif trans_result.segments:
            duration_sec = trans_result.segments[-1].end if trans_result.segments else 0.0

        if video_title and file_info.youtube_url:
            source_display = f"{video_title} ({file_info.youtube_url})"
        else:
            source_display = file_info.youtube_url or file_info.filename

        transcription_md = build_transcription_markdown(
            aligned_segments,
            source_display,
            duration_sec,
            trans_result.language,
            config.get("whisper", "model_size", fallback="large-v3"),
            speaker_count,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        trans_path = save_transcription(session_dir, transcription_md)

        speakers_list = (
            ", ".join(sorted(
                set(s.speaker_id for s in speaker_segments),
                key=_speaker_sort_key,
            ))
            if speaker_segments else ""
        )

        update_session(conn, session_id, {
            "speaker_count": speaker_count,
            "speakers_list": speakers_list,
            "transcription_path": str(trans_path),
            "duration_seconds": duration_sec,
        })

        from src.summarizer import summarize_deepseek, generate_article_deepseek
        from src.email_sender import is_email_enabled, send_summary, send_article

        generate_summary = config.getboolean("output", "generate_summary", fallback=True)
        generate_article = config.getboolean("output", "generate_article", fallback=True)

        summary_path = None
        article_path = None
        summary_email_status = None
        article_email_status = None

        if generate_summary:
            summarize_display = video_title or file_info.filename
            logger.info(t("msg.summarizing", filename=summarize_display))
            summary_text, usage = summarize_deepseek(transcription_md, config)
            logger.info(t("msg.summarization_done"))

            source_block, channel_name = _build_source_block(file_info, duration_sec)

            summary_md = build_summary_markdown(
                summary_text,
                source_block,
                datetime.now().strftime("%Y-%m-%d"),
                config.get("deepseek", "model", fallback="deepseek-chat"),
                speakers_list,
                summarizer_params={
                    "model": config.get("deepseek", "model", fallback="deepseek-chat"),
                    "temperature": config.getfloat("deepseek", "temperature", fallback=0.3),
                    **usage,
                },
            )
            summary_path = save_summary(session_dir, summary_md)

            logger.info(t("msg.copying_output", filename=f"{session_id}_summary.md"))
            copy_summary_to_output(session_id, session_dir)

            if is_email_enabled(config):
                try:
                    send_summary(summary_md, source_filename, channel_name, config)
                except Exception as email_err:
                    summary_email_status = "failed"
                    logger.error(t("error.email_send_failed", detail=str(email_err)))
                else:
                    summary_email_status = "sent"

        if generate_article:
            article_display = video_title or file_info.filename
            logger.info(t("msg.generating_article", filename=article_display))
            article_text, _ = generate_article_deepseek(transcription_md, config)
            logger.info(t("msg.article_done"))

            article_path = save_article(session_dir, article_text)

            logger.info(t("msg.copying_output", filename=f"{session_id}_article.md"))
            copy_article_to_output(session_id, session_dir)

            if is_email_enabled(config):
                try:
                    send_article(article_text, source_filename, channel_name, config)
                except Exception as email_err:
                    article_email_status = "failed"
                    logger.error(t("error.email_send_failed", detail=str(email_err)))
                else:
                    article_email_status = "sent"

        processing_time = (datetime.now() - processing_start).total_seconds()
        session_update: dict = {
            "summarizer_engine": "deepseek",
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
        }
        if summary_path is not None:
            session_update["summary_path"] = str(summary_path)
        if article_path is not None:
            session_update["article_path"] = str(article_path)
        if summary_email_status is not None:
            session_update["email_status"] = summary_email_status
        if article_email_status is not None:
            session_update["article_email_status"] = article_email_status
        update_session(conn, session_id, session_update)

        logger.info(
            t("msg.session_completed", session_id=session_id, duration=int(processing_time))
        )

    except Exception as e:
        update_session(conn, session_id, {
            "status": "failed",
            "error_message": str(e),
        })
        raise

    finally:
        if wav_path is not None and wav_path.exists():
            wav_path.unlink(missing_ok=True)

    metadata = {
        "session_id": session_id,
        "source_filename": source_filename,
        "source_type": file_info.file_type,
        "file_hash": file_hash,
        "duration_seconds": duration_sec,
        "word_count": trans_result.word_count,
        "whisper_model": config.get("whisper", "model_size", fallback="large-v3"),
        "whisper_language": trans_result.language,
        "whisper_confidence": trans_result.confidence,
        "summarizer_engine": "deepseek",
        "status": "completed",
        "created_at": session_data["created_at"],
        "completed_at": datetime.now().isoformat(),
        "processing_time_seconds": (datetime.now() - processing_start).total_seconds(),
    }
    save_metadata(session_dir, metadata)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_progress()
        logger.info(t("msg.interrupted"))
        sys.exit(1)
