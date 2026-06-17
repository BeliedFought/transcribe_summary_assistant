# Спецификация проекта: Transcribe & Summary Assistant

**Версия:** 0.6.1
**Дата:** 2026-06-17
**Статус:** Согласована
**Стандарт:** 3.9.0 (project_standards.md)

---

## 1. Назначение проекта

CLI-инструмент для транскрибации (speech-to-text), диаризации (разделение по голосам), саммаризации аудио- и видеофайлов и опциональной рассылки саммари на email (SMTP). Пользователь помещает файлы в папки `input/audio/`, `input/video/` или .txt со ссылками YouTube в `input/yt/`, запускает `python main.py` - инструмент транскрибирует речь в текст через faster-whisper (CUDA), разделяет текст по дикторам через pyannote.audio, формирует саммари (общий контекст + по ролям) через API DeepSeek и при необходимости отправляет на email. Дополнительно генерируется статья для публикации. Каждая обработка - отдельная сессия с уникальным идентификатором. Метаданные сессии хранятся в SQLite. Транскрипция и диаризация кешируются по SHA256-хешу исходного файла.

---

## 2. Принципиальные решения

| Вопрос | Решение |
|--------|---------|
| Движок транскрибации | faster-whisper + CUDA |
| Модель whisper | large-v3 (3 GB, ~10 GB VRAM) |
| Языки транскрибации | русский + английский (автоопределение) |
| Движок саммаризации | DeepSeek API (deepseek-chat) |
| Формат вывода | Markdown (transcription.md + summary.md) |
| Диаризация | pyannote.audio 4.x, pipeline `speaker-diarization-3.1` + gated-подмодели `segmentation-3.0` и `speaker-diarization-community-1` |
| YouTube | .txt файл с одной или несколькими ссылками → yt-dlp → аудио; каждая ссылка - отдельная сессия |
| YouTube (инфо) | Извлечение channel, subscribers, ссылки на видео/канал из метаданных yt-dlp |
| Доп. документ | Статья для публикации (article.md) - краткое изложение без метаданных |
| Рассылка email | SMTP (Yandex), multipart HTML+plain text; отдельные темы для саммари и статьи |
| Оркестратор | main.py в корне, без аргументов |
| Тип интерфейса | CLI-скрипты (без интерактивного меню) |
| Название приложения | Transcribe & Summary Assistant |
| GPU | NVIDIA CUDA доступна |
| Python | 3.14 |
| Виртуальное окружение | `.venv/` в корне проекта |

---

## 3. Архитектура (полная схема, 13 шагов)

```
                           main.py (оркестратор)
                               |
   [0] Pre-flight: cuda_loader.py ──── загрузка CUDA-библиотек (RTLD_GLOBAL)
        preflight.py ───────────────── проверка моделей, API, HF_TOKEN
        _validate_environment() ─────── ffmpeg, yt-dlp, ключи, папки
                               |
                               v
   [1] Сканирование папок input/audio/, input/video/, input/yt/
         |  (порядок: audio -> video -> youtube)
         v
   [2] Если .txt со ссылками YouTube -> yt-dlp -> аудио (opus/m4a/webm)
         |  каждая ссылка - отдельная сессия; извлекается channel, subscribers
         v
   [3] Создание сессии: YYYY-MM-DD_HH-MM-SS_<sha256[:8]>
         |
         v
   [4] Извлечение аудио из видео (ffmpeg: 16kHz mono WAV) - только для video/
         |
         v
   [5] Кеш-проверка: поиск по file_hash в SQLite
         |  └──── transcription найдена? → загрузка transcription.json, пропуск [6]
         |  └──── diarization найдена? → загрузка diarization.json, пропуск [8]
         |
         v
   [6] Транскрибация (faster-whisper large-v3, CUDA, float16, VAD)
         |
         v
   [7] Сохранение сырой транскрипции (transcription.json для кеша)
         |
         v
   [8] Диаризация (pyannote.audio): конвертация в WAV 16kHz → pipeline
         |
         v
   [9] Алайнмент: привязка сегментов транскрипции к дикторам (IOU)
         |
         v
  [10] Сохранение transcription.md с ролями в папку сессии + SQLite
         |
         v
  [11] Саммаризация через DeepSeek API:
         если ≤6000 токенов → прямой запрос
         если >6000 токенов → map-reduce (чанки → саммари чанков → итог)
         |
         v
  [12] Генерация статьи через DeepSeek API (краткое изложение для публикации)
         |
         v
  [13] Сохранение summary.md + article.md
         копии в output/<session_id>_summary.md, output/<session_id>_article.md
         отправка на email (если enabled)
```

---

## 4. Структура папок проекта

```
.
+-- AGENTS.md                       # Инструкции AI-агентам (английский)
+-- CLAUDE.md                       # Зеркальная копия AGENTS.md
+-- README.md                       # Документация для пользователей (русский)
+-- main.py                         # Оркестратор: python main.py (полный пайплайн)
+-- requirements.txt                # Зависимости (все зафиксированы ==)
+-- .python-version                 # 3.14
+-- .gitignore                      # Исключения: .env, .venv/, log/, debug/, diag/, input/, output/, data/, __pycache__/, .pytest_cache/, .vscode/, .claude/, .kilo, doc/agent_questions/, doc/change_requests/
+-- .env                            # Secrets (не коммитится)
+-- .env.example                    # Шаблон .env
+-- config/
|   +-- config.ini                  # Все настройки проекта
+-- data/
|   +-- sessions.db                 # SQLite: sessions, processing_queue, translations
|   +-- sessions/                   # Папки сессий обработки
|       +-- <session_id>/
|           +-- metadata.json       # Метаданные сессии (дубль SQLite)
|           +-- transcription.json  # Сырая транскрипция для кеша (опционально)
|           +-- diarization.json    # Сырая диаризация для кеша (опционально)
|           +-- transcription.md    # Полная транскрипция с временными метками
|           +-- summary.md          # Структурированное саммари
|           +-- article.md          # Статья для публикации
+-- debug/                          # Отладочные и временные файлы
|   +-- yt_audio/                   # Временные аудиофайлы YouTube
|   +-- <session_id>.wav            # Временный WAV после извлечения из видео
+-- diag/                           # Диагностические данные (preflight-дампы, тесты)
+-- doc/
|   +-- specs/
|   |   +-- final_spec.md           # Структурированная спецификация (этот файл)
|   +-- standards/                  # Стандарты проекта (read-only)
|   |   +-- project_standards.md    # Эталонный стандарт 3.9.0
|   |   +-- skill_standards.md      # Стандарт оформления навыков
|   +-- agent_questions/            # Уточняющие вопросы агента
|   +-- change_requests/            # Запросы на изменения
|   +-- skills/                     # Навыки агента
+-- input/
|   +-- audio/                      # Аудиофайлы (mp3, wav, flac, ogg, m4a, opus)
|   +-- video/                      # Видеофайлы (mp4, webm, mkv, mov, avi)
|   +-- yt/                         # .txt файлы со ссылками YouTube (можно несколько)
+-- log/                            # Лог-файлы
+-- output/                         # Результаты: <session_id>_summary.md, <session_id>_article.md
+-- run/
|   +-- db/
|   |   +-- db_check_connection.py  # Проверка SQLite
|   |   +-- db_check_schema.py      # Проверка схемы БД
|   |   +-- db_init.py              # Создание/пересоздание таблиц + переводы
|   +-- api/
|   |   +-- api_check_connection.py # Проверка DeepSeek API
|   |   +-- api_test_requests.py    # Тестовый запрос к DeepSeek
|   +-- ai/
|       +-- ai_ollama_check.py      # Проверка Ollama (отключен)
|       +-- ai_ollama_pull_models.py# Pull моделей Ollama (отключен)
+-- .env.example                    # Шаблон .env
+-- sample/                         # Примеры данных
+-- sql/
|   +-- schema.sql                  # DDL для SQLite (read in runtime)
+-- src/                            # Библиотечные модули (17 файлов)
|   +-- config.py                   # Загрузка config.ini и .env, PROJECT_ROOT
|   +-- logger.py                   # Логирование: YYYY-MM-DD HH:MM:SS [маркер]
|   +-- localization.py             # i18n: t(), init(), reload()
|   +-- cuda_loader.py              # Предзагрузка CUDA-библиотек (RTLD_GLOBAL)
|   +-- preflight.py                # Pre-flight: модели, API, HF_TOKEN
|   +-- retry.py                    # Retry с экспоненциальным backoff
|   +-- db_manager.py               # SQLite CRUD + переводы (678 строк)
|   +-- file_scanner.py             # Сканирование input/ + вычисление SHA256
|   +-- audio_extractor.py          # Извлечение аудио из видео (ffmpeg)
|   +-- youtube_downloader.py       # Загрузка аудио с YouTube (yt-dlp)
|   +-- transcriber.py              # Транскрибация (faster-whisper)
|   +-- diarizer.py                 # Диаризация + алайнмент (pyannote)
|   +-- summarizer.py               # Саммаризация (DeepSeek API)
|   +-- session_manager.py          # Управление сессиями на диске
|   +-- progress.py                 # Индикация прогресса (\r)
+-- test/                           # Тесты pytest
    +-- test_file_scanner.py        # 5 тестов: URL, хеш, сканирование
    +-- test_session_manager.py     # 9 тестов: ID, папки, Markdown
    +-- test_transcriber.py         # 1 тест: датаклассы
    +-- test_summarizer.py          # 3 теста: токены, чанки
```

---

## 5. Конфигурация

### config/config.ini

```ini
[app]
name = Transcribe & Summary Assistant
version = 0.6.1
language = ru

[processing]
audio_extensions = .mp3,.wav,.flac,.ogg,.m4a,.opus
video_extensions = .mp4,.webm,.mkv,.mov,.avi
text_extensions = .txt

[whisper]
model_size = large-v3
device = cuda
compute_type = float16
language = ru
vad_filter = true
vad_min_speech_duration_ms = 1000
vad_max_speech_duration_s = 30
beam_size = 5

[diarization]
enabled = true
min_speakers = 1
max_speakers = 10
hf_model = pyannote/speaker-diarization-3.1

[youtube]
audio_format = bestaudio/best
output_template = %(id)s_%(title)s.%(ext)s

[deepseek]
api_url = https://api.deepseek.com/v1
model = deepseek-chat
temperature = 0.3
max_tokens = 4096
timeout = 60

[ollama]
enabled = false
base_url = http://localhost:11434
model = llama3
timeout = 60

[paths]
data_folder = data/
input_folder = input/
output_folder = output/
log_folder = log/

[retry]
count = 3
delay = 2
max_delay = 30

[email]
enabled = true
smtp_host = smtp.yandex.ru
smtp_port = 465
smtp_security = ssl
from = user@domain.com
to = recipient@domain.com
subject_summary = Краткий пересказ - {channel} - {title}
subject_article = Статья - {title}

[output]
generate_summary = true
generate_article = true
```

### .env (secrets)

```
DEEPSEEK_API_KEY=sk-<KEY>
HF_TOKEN=hf_<TOKEN>
SMTP_USER=user@domain.com
SMTP_PASSWORD=app_password
```

`HF_TOKEN` - Hugging Face токен для загрузки gated-моделей pyannote.audio. Пользователь должен:
1. Зарегистрироваться на huggingface.co
2. Принять условия (Accept) на страницах всех gated-репозиториев:
   - `pyannote/speaker-diarization-3.1`
   - `pyannote/segmentation-3.0`
   - `pyannote/speaker-diarization-community-1`
3. Создать токен на huggingface.co/settings/tokens и указать в .env

`SMTP_USER` и `SMTP_PASSWORD` - учетные данные SMTP (пароль приложения) для отправки писем

---

## 6. База данных (SQLite)

Файл: `data/sessions.db`

### 6.1. Таблица sessions

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source_filename TEXT NOT NULL,
    source_type TEXT NOT NULL,          -- 'audio', 'video', 'youtube_link'
    source_url TEXT,                    -- ссылка YouTube (только для source_type=youtube_link)
    original_path TEXT NOT NULL,
    session_dir TEXT NOT NULL,
    file_size_bytes INTEGER,
    duration_seconds REAL,
    file_hash TEXT,
    whisper_model TEXT,
    whisper_language TEXT,
    whisper_confidence REAL,
    word_count INTEGER,
    speaker_count INTEGER,
    speakers_list TEXT,                 -- "Спикер_01, Спикер_02"
    transcription_path TEXT,
    summary_path TEXT,
    article_path TEXT,                  -- путь к статье для публикации
    summarizer_engine TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, transcribed, completed, failed, partial
    error_message TEXT,
    email_status TEXT,                  -- статус отправки саммари: sent, failed, NULL
    article_email_status TEXT,          -- статус отправки статьи: sent, failed, NULL
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    processing_time_seconds REAL
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_hash ON sessions(file_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
```

### 6.2. Таблица processing_queue

```sql
CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    stage TEXT NOT NULL,                -- 'audio_extraction', 'transcription', 'diarization', 'summarization'
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### 6.3. Таблица translations

```sql
CREATE TABLE IF NOT EXISTS translations (
    key TEXT NOT NULL,
    lang TEXT NOT NULL DEFAULT 'ru',
    value TEXT NOT NULL,
    PRIMARY KEY (key, lang)
);
```

Заполняется в `db_init.py` начальными переводами для ru и en. Всего ~851 ключей. Fallback-цепочка: текущий язык → язык по умолчанию (ru) → en → `!KEY!`.

---

## 7. Формат сессии на диске

### 7.1. Имя папки сессии

`YYYY-MM-DD_HH-MM-SS_<первые 8 символов SHA256 хеша файла>`

Пример: `2026-06-15_17-30-00_a1b2c3d4`

Идентификатор гарантированно уникален (момент времени + хеш содержимого), даже при повторной обработке одного файла.

### 7.2. Структура папки сессии

```
data/sessions/2026-06-15_17-30-00_a1b2c3d4/
+-- metadata.json         # Метаданные сессии (дубль SQLite)
+-- transcription.json    # Сырая транскрипция для кеша (может отсутствовать)
+-- diarization.json      # Сырая диаризация для кеша (может отсутствовать)
+-- transcription.md      # Полная транскрипция с ролями и временными метками
+-- summary.md            # Структурированное саммари
+-- article.md            # Статья для публикации
```

### 7.3. metadata.json

```json
{
  "session_id": "2026-06-15_17-30-00_a1b2c3d4",
  "source_filename": "lecture.mp4",
  "source_type": "video",
  "file_hash": "a1b2c3d4e5f6789",
  "duration_seconds": 3660.0,
  "word_count": 15234,
  "whisper_model": "large-v3",
  "whisper_language": "ru",
  "whisper_confidence": 0.89,
  "summarizer_engine": "deepseek",
  "status": "completed",
  "created_at": "2026-06-15T17:30:00",
  "completed_at": "2026-06-15T18:15:00",
  "processing_time_seconds": 2700
}
```

### 7.4. transcription.json (сырая транскрипция для кеша)

```json
{
  "segments": [
    {"start": 0.0, "end": 15.0, "text": "Текст первого сегмента"},
    {"start": 15.0, "end": 30.0, "text": "Текст второго сегмента"}
  ],
  "language": "ru",
  "confidence": 0.89,
  "word_count": 15234
}
```

Используется для кеша: при повторном запуске того же файла транскрипция загружается из JSON (поиск по `file_hash` в SQLite), повторная транскрибация пропускается. Аналогично кешируется `diarization.json` - диаризация не выполняется заново, если найден валидный файл. Файлы не сохраняются, если данные были восстановлены из кеша.

### 7.5. transcription.md

```markdown
# Транскрипция: lecture.mp4

**Дата обработки:** 2026-06-15 17:30
**Длительность:** 61 мин 0 сек
**Язык:** русский
**Модель:** faster-whisper large-v3
**Диаризация:** pyannote.audio (2 диктора)

---

## Текст (по ролям)

[00:00:00 -> 00:00:15] **Спикер_01:** Текст первого сегмента
[00:00:15 -> 00:00:30] **Спикер_02:** Текст второго сегмента
[00:00:30 -> 00:01:00] **Спикер_01:** Текст третьего сегмента
```

Дикторы именуются: `Спикер_01`, `Спикер_02` (с ведущими нулями, если дикторов > 1). При одном дикторе: `Спикер_1`. При сбое алайнмента: `[неизвестно]`.

### 7.6. summary.md

```markdown
# Саммари: lecture.mp4

**Дата:** 2026-06-15
**Движок:** deepseek-chat
**Температура:** 0.3
**Токенов:** 15200 (prompt) + 3200 (completion) = 18400
**Дикторы:** Спикер_01, Спикер_02

---

[текст саммари от DeepSeek API]
```

### 7.7. Выходной файл (output/)

Файлы: `output/<session_id>_summary.md` и `output/<session_id>_article.md` - атомарные копии из папки сессии (write .tmp → replace).

---

## 8. Пайплайн обработки (детально)

### Шаг 0: Pre-flight валидация и загрузка CUDA

**До любого импорта faster-whisper** выполняется `preload_cuda_libs()` из `src/cuda_loader.py`. Модуль обходит `site-packages/nvidia/cuda_runtime/lib`, `cublas/lib`, `cudnn/lib`, `cuda_nvrtc/lib` и загружает все `.so` файлы через `ctypes.CDLL(so, mode=ctypes.RTLD_GLOBAL)`. Это необходимо, потому что ctranslate2 (бэкенд faster-whisper) динамически ищет `libcublas.so.12` и др. при первом encode на GPU. Библиотеки находятся в site-packages/nvidia/*/lib и не входят в стандартный путь поиска ld.so. Изменение `LD_LIBRARY_PATH` в рантайме бесполезно, так как ld.so кеширует путь при старте процесса. Явная загрузка через `CDLL(RTLD_GLOBAL)` делает библиотеки доступными для последующих dlopen-вызовов.

**Затем** выполняется `_validate_environment()`:
1. Проверка наличия папок (`data/`, `log/`, `output/`)
2. Проверка наличия ffmpeg и yt-dlp в `PATH`
3. Проверка наличия `DEEPSEEK_API_KEY` и `HF_TOKEN` в `.env`
4. Pre-flight проверки (`src/preflight.py check_all()`):
   - **Целостность модели whisper** (`Systran/faster-whisper-large-v3`): проверка наличия `config.json`, `preprocessor_config.json`, `tokenizer.json`, `vocabulary.json`, `model.bin` в HF-кеше. При отсутствии - попытка авто-доустановки через `snapshot_download()` с таймаутом 30 минут. Xet-бэкенд отключается (`HF_HUB_DISABLE_XET = True`), так как в `huggingface_hub` 1.19 он может зависать на крупных моделях на сетевом уровне.
   - **Целостность моделей pyannote** (при `[diarization] enabled=true`):
     - `pyannote/speaker-diarization-3.1` - pipeline config (`config.yaml`)
     - `pyannote/segmentation-3.0` - gated-подмодель (`config.yaml`, `pytorch_model.bin`)
     - `pyannote/speaker-diarization-community-1` - gated-подмодель x-vector/PLDA рескоринга (`config.yaml`, `embedding/pytorch_model.bin`, `segmentation/pytorch_model.bin`, `plda/plda.npz`, `plda/xvec_transform.npz`)
   - **Доступность DeepSeek API**: `GET /models` с авторизацией, таймаут 15 сек
   - **Доступность HuggingFace Hub**: `HfApi.whoami(token=HF_TOKEN)`, таймаут 15 сек
5. Проверка схемы БД: `verify_schema()` сверяет таблицы/колонки с `sql/schema.sql`
6. Проверка переводов: `translations_count() > 0`

Все проверки выполняются до начала обработки. Fail fast: все ошибки выводятся одним блоком, затем `sys.exit(1)`.

### Шаг 1: Сканирование папок input/

- Модуль: `src/file_scanner.py`
- Функция: `scan_input_dirs(config) -> list[FileInfo]`
- Поиск файлов в `input/audio/`, `input/video/`, `input/yt/` по расширениям из конфига
- Для `input/yt/`: читается содержимое `.txt`, извлекаются все ссылки YouTube (по одной на строку, 3 паттерна), дедупликация
- На каждую ссылку создается отдельная сессия
- Результат: `FileInfo` с полями `path`, `filename`, `file_type` (`audio`, `video`, `youtube_link`), `extension`, `size_bytes`, `youtube_url`
- Если файлов нет - сообщение и выход без ошибки

### Шаг 2: Загрузка из YouTube

- Модуль: `src/youtube_downloader.py`
- Функция: `download_audio(youtube_url, output_dir, config) -> Path`
- Команда: `yt-dlp -f bestaudio/best -o "%(id)s_%(title)s.%(ext)s" --no-playlist --extract-audio <url>`
- После загрузки: поиск самого свежего аудиофайла в `output_dir` по расширениям `.opus`, `.m4a`, `.webm`, `.mp3`, `.wav`
- source_type = `youtube_link`, source_url сохраняется в метаданных

### Шаг 3: Создание сессии

- `session_id = generate_session_id(audio_path)`: вычисляет SHA256 файла (первые 8 символов) + `datetime.now()` в формате `YYYY-MM-DD_HH-MM-SS`
- Создание папки `data/sessions/<session_id>/` (`mkdir(parents=True, exist_ok=True)`)
- INSERT в `sessions` (статус `pending`)
- Вычисление file_hash для кеша

### Шаг 4: Извлечение аудио из видео

- Модуль: `src/audio_extractor.py`
- Функция: `extract_audio(video_path, output_wav_path) -> float` (длительность)
- Команда ffmpeg: `ffmpeg -y -i <input> -vn -acodec pcm_s16le -ar 16000 -ac 1 <output.wav>`
- Определение длительности через `ffprobe -v error -show_entries format=duration`
- Временный WAV сохраняется в `debug/<session_id>.wav`, удаляется в `finally` блоке

### Шаг 5: Кеш-проверка транскрипции

- Поиск в SQLite всех сессий с тем же `file_hash`, упорядоченных от новой к старой
- Для каждого кандидата: проверка наличия `transcription.json` в `session_dir` и его валидности
- Если найден - загрузка segments из JSON, построение `TranscriptionResult`
- Кеш НЕ фильтруется по статусу (транскрипция может быть успешной даже при `status=failed` из-за сбоя диаризации)
- Если кеш найден - пропуск шага 6, переход к шагу 8

### Шаг 6: Транскрибация

- Модуль: `src/transcriber.py`
- Модель кешируется в памяти: синглтон `ModelCache`, модель загружается один раз при первом запросе и переиспользуется между сессиями
- Параметры: `WhisperModel(model_size, device=cuda, compute_type=float16)`
- Вызов: `model.transcribe(audio_path, language=ru, beam_size=5, vad_filter=True, vad_parameters=dict())`
- VAD: `min_speech_duration_ms=1000`, `max_speech_duration_s=30` (обязателен для файлов > 30 сек)
- Прогресс: колбэк `on_progress(pct, seg_end, seg_count)` вызывается для каждого сегмента. Использует `update_progress()` из `progress.py` (`\r` + `sys.stdout.write`)
- Результат: `TranscriptionResult` со списком `TranscriptionSegment` (start, end, text), языком, уверенностью, количеством слов
- Уверенность вычисляется как средневзвешенное `avg_logprob` сегментов по количеству слов

### Шаг 7: Сохранение сырой транскрипции

- Атомарная запись `transcription.json` в папку сессии (`.tmp` → `replace`)
- Используется для кеша при будущих запусках
- Не сохраняется, если транскрипция восстановлена из кеша

### Шаг 8: Диаризация

- Модуль: `src/diarizer.py`
- Модель: синглтон `_pipeline` - pyannote.audio `Pipeline.from_pretrained(hf_model, token=HF_TOKEN)`
- На GPU: `pipeline.to(torch.device("cuda"))` (в 3-5 раз быстрее CPU)
- **Конвертация в WAV перед pyannote**: ffmpeg `-ar 16000 -ac 1 -f wav` во временный файл. Это обязательно для mp3, так как VBR/CBR кодирование дает нецелое число сэмплов на 10-секундный чанк, что вызывает ошибку pyannote.
- Временный WAV удаляется после обработки (`unlink(missing_ok=True)` в `finally`)
- Вызов: `pipeline(wav_path, min_speakers, max_speakers)`
- Результат: `list[SpeakerSegment]` с `start`, `end`, `speaker_id`
- Дикторы переименовываются: `Спикер_01`, `Спикер_02` (с ведущими нулями для числовой сортировки в Markdown). При одном дикторе: `Спикер_1`

### Шаг 9: Алайнмент

- Функция: `align_segments(transcription_segments, speaker_segments) -> list[AlignedSegment]`
- Стратегия: для каждого сегмента транскрипции - поиск диктора, чей интервал максимально пересекается с сегментом (Intersection over Union)
- Если пересечения нет - назначается `[неизвестно]`
- Результат: `AlignedSegment` с `start`, `end`, `text`, `speaker_id`

### Шаг 10: Сохранение транскрипции

- `build_transcription_markdown()` формирует Markdown с метаданными и разбиением по дикторам
- Атомарная запись `transcription.md` (`.tmp` → `replace`)
- UPDATE sessions: `status=transcribed`, `word_count`, `confidence`, `transcription_path`, `speaker_count`, `speakers_list`

### Шаг 11: Саммаризация (общий контекст + по ролям)

- Модуль: `src/summarizer.py`
- Системный промпт: "Проанализируй транскрипцию диалога и составь структурированное саммари на языке исходного текста. Саммари должно включать: 1. Общий контекст 2. По ролям 3. Ключевые моменты. Формат вывода - Markdown."
- Оценка токенов: `len(text) / 2.5` (приближенно, chars_per_token)
- **Прямой запрос** (≤6000 токенов): один вызов `POST /v1/chat/completions`
- **Map-reduce** (>6000 токенов):
  1. Разбиение на чанки по `MAX_CHUNK_TOKENS * 2.5 * 0.7` символов (с запасом 0.7), разбивка по строкам для сохранения целостности
  2. Каждый чанк саммаризируется отдельно: `"Это часть {i}/{total} текста."`
  3. Объединение саммари чанков через `---`
  4. Итоговый запрос: "Ниже приведены саммари отдельных частей разговора. Составь итоговое саммари, объединив их в единый связный текст."
- Параметры: `model=deepseek-chat`, `temperature=0.3`, `max_tokens=4096`
- Retry (через `src/retry.py`): 3 попытки с экспоненциальным backoff для `Timeout`, `ConnectionError`, `HTTPError`. Не retry для 401/403.
- Возвращает `(текст саммари, usage_stats)`

### Шаг 12: Генерация статьи

- Модуль: `src/summarizer.py` (та же функция с другим системным промптом)
- Промпт: "Напиши краткую структурированную статью на русском языке, готовую к публикации. Без метаданных, технических пометок и разделения по дикторам."
- Параметры: те же, что для саммари (`temperature=0.3`, `max_tokens=4096`)
- Retry: через `src/retry.py` (3 попытки, экспоненциальный backoff)
- Сохранение: `build_article_markdown()` → атомарная запись `article.md`
- UPDATE sessions: `article_path`

### Шаг 13: Финализация

- `build_summary_markdown()` формирует Markdown с метаданными и текстом саммари
- Атомарная запись `summary.md` и `article.md` (`.tmp` → `replace`)
- `copy_summary_to_output()`: атомарное копирование в `output/<session_id>_summary.md`
- `copy_article_to_output()`: атомарное копирование в `output/<session_id>_article.md`
- UPDATE sessions: `status=completed`, `completed_at`, `processing_time_seconds`, `summary_path`, `summarizer_engine`
- UPDATE processing_queue: `status=completed`
- Запись `metadata.json`
- Отправка на email (если `[email] enabled=true`): саммари и статья - отдельными письмами с разными темами (`subject_summary` / `subject_article`). Статусы отправки - `email_status` и `article_email_status`. При ошибке - логирование, обработка продолжается

---

## 9. Индикация прогресса

- Модуль: `src/progress.py`
- `update_progress(line)`: `\r` + `sys.stdout.write(line)` + `sys.stdout.flush()` - перезапись одной строки
- `clear_progress()`: `\r\033[K` - очистка строки прогресса
- Прогресс транскрибации: колбэк `on_progress` в `transcribe()` выводит процент и детали (сегменты, позиция)
- Прогресс НЕ дублируется в лог-файл - только промежуточные строки в консоли
- Итоговая строка (результат транскрибации) - через `logger.info()`, попадает в лог
- При Ctrl+C - обязательный вызов `clear_progress()` перед выходом

---

## 10. Graceful shutdown

- `signal.signal(signal.SIGINT, _signal_handler)` в начале main.py
- При Ctrl+C:
  - `clear_progress()` - очистка строки прогресса
  - `logger.info(t("msg.interrupted"))` и `sys.exit(1)`
- Внешний `try/except KeyboardInterrupt` в `__main__` на случай, если сигнал пришел не из основного потока
- `finally` блок для каждого файла: удаление временного WAV (`wav_path.unlink(missing_ok=True)`)

---

## 11. Обработка ошибок

| Ситуация | Действие |
|----------|-----------|
| Транскрибация не удалась | `status=failed`, `error_message` заполнен |
| Загрузка YouTube не удалась | `status=failed`, `error_message` (невалидная ссылка / нет сети / yt-dlp error) |
| Диаризация не удалась | `status=partial` (транскрипция без ролей) |
| Саммаризация не удалась | `status=partial` (транскрипция с ролями готова) |
| Генерация статьи не удалась | `status=partial` (саммари готово, статья пропущена) |
| DeepSeek 401/403 | Не retry, сообщить о невалидном ключе |
| DeepSeek 429/5xx | Retry с экспоненциальным backoff (3 попытки, от 2 сек, макс 30 сек) |
| ffmpeg / yt-dlp не найдены | Fail fast при валидации, до обработки |
| Модель whisper недокачана | Pre-flight авто-доустановка, при неудаче - fail fast с инструкцией |
| Модели pyannote недокачаны / gated | Pre-flight авто-доустановка, при GatedRepoError - fail fast со списком URL для принятия условий |
| HF_TOKEN невалиден | Pre-flight fail fast |
| DeepSeek API недоступен | Pre-flight fail fast |
| Схема БД не соответствует | Fail fast с инструкцией выполнить `python run/db/db_init.py` |
| Таблица переводов пуста | Fail fast с инструкцией выполнить `python run/db/db_init.py` |
| Файл не найден в input/ | Просто сообщение, выход 0 (не ошибка) |
| Отправка email не удалась | `email_status` / `article_email_status = failed`; обработка продолжается |

---

## 12. Модули src/ - полное описание

| Модуль | Ключевые функции/классы | Назначение |
|--------|------------------------|-----------|
| `config.py` | - | Загрузка `config/config.ini` + `.env`. Экспорт: `config` (ConfigParser), `PROJECT_ROOT` (Path), `APP_NAME` (str), `APP_VERSION` (str). `PROJECT_ROOT = Path(__file__).resolve().parents[1]` |
| `logger.py` | `get_logger(name, log_dir, menu_mode=False)` | `_MarkerFormatter`: `YYYY-MM-DD HH:MM:SS [!] / [i] / [*] message`. Два хендлера: stdout + файл `log/log_<name>_<timestamp>.log`. Защита от дублирования через `if logger.handlers: return` |
| `localization.py` | `init(language, db_path)`, `t(key, *, count, **kwargs)`, `reload()` | i18n: загрузка из SQLite `translations`. Кеш в памяти. Плюрализация: ru (zero/one/few/many), en (zero/one/many). Определение языка: config → env LANGUAGE → системная локаль → en |
| `cuda_loader.py` | `preload_cuda_libs() -> int` | Предзагрузка CUDA-библиотек из `site-packages/nvidia/*/lib` через `ctypes.CDLL(RTLD_GLOBAL)`. Порядок: cuda_runtime → cublas → cudnn → cuda_nvrtc. Вызывается до импорта faster_whisper |
| `preflight.py` | `check_all(config) -> list[str]` | Pre-flight: проверка целостности whisper (5 файлов), pyannote pipeline config, segmentation-3.0 (2 файла), community-1 (5 файлов), DeepSeek API, HuggingFace Hub. Авто-доустановка моделей с таймаутом 30 мин (thread). Gated-ошибки → список URL для принятия условий. |
| `retry.py` | `retry(func, config, retryable_types) -> T` | Экспоненциальный backoff: `delay * 2^attempt`, макс 30 сек. `NON_RETRYABLE_HTTP_CODES = {401, 403, 400, 422}` |
| `db_manager.py` | `init_db()`, `create_session()`, `update_session()`, `verify_schema()`, `translations_count()`, `find_cached_transcription()`, `find_cached_diarization()`, `enqueue_stage()`, `update_stage()`, `insert_initial_translations()` | SQLite CRUD. `verify_schema()` парсит `sql/schema.sql` и сверяет с реальной БД. `find_cached_transcription()` и `find_cached_diarization()` ищут сессии по file_hash для кеша |
| `file_scanner.py` | `scan_input_dirs()`, `compute_file_hash()`, `FileInfo` dataclass | Сканирование input/audio/, input/video/, input/yt/. 3 паттерна YouTube URL. SHA256 через `hashlib.sha256()` |
| `audio_extractor.py` | `extract_audio(video_path, output_wav_path) -> float` | ffmpeg: видео → WAV 16kHz mono. ffprobe: длительность |
| `youtube_downloader.py` | `download_audio(youtube_url, output_dir, config) -> Path`, `get_channel_info(url) -> dict` | yt-dlp: bestaudio/best, --extract-audio, --no-playlist. Поиск результата по расширениям и mtime. Извлечение channel, subscribers, ссылок на видео/канал |
| `transcriber.py` | `transcribe(audio_path, config, on_progress=None) -> TranscriptionResult`, `ModelCache` (синглтон), `TranscriptionSegment`, `TranscriptionResult` | faster-whisper: `WhisperModel(model_size, device=cuda, compute_type=float16)`. VAD-фильтрация. Колбэк прогресса. Уверенность = взвешенное среднее avg_logprob |
| `diarizer.py` | `diarize(audio_path, config) -> list[SpeakerSegment]`, `align_segments(transcription_segments, speaker_segments) -> list[AlignedSegment]`, `_get_pipeline()` (синглтон) | pyannote.audio `Pipeline.from_pretrained()`. Внутренняя конвертация в WAV 16kHz. GPU via `pipeline.to(torch.device("cuda"))`. Имена дикторов: Спикер_01, Спикер_02. Алайнмент через IOU |
| `summarizer.py` | `summarize_deepseek(transcription_with_roles, config) -> (str, dict)` | DeepSeek API: саммари и статья - два вызова с разными системными промптами. ≤6000 токенов - прямой запрос. >6000 - map-reduce. Retry через `src/retry.py` |
| `session_manager.py` | `generate_session_id()`, `create_session_dir()`, `save_metadata()`, `save_transcription()`, `save_transcription_raw()`, `load_transcription_raw()`, `save_diarization_raw()`, `load_diarization_raw()`, `save_summary()`, `save_article()`, `copy_summary_to_output()`, `copy_article_to_output()`, `build_transcription_markdown()`, `build_summary_markdown()`, `build_article_markdown()` | Все операции с сессией на диске. Атомарная запись (`.tmp` → `replace`). `transcription.json` + `diarization.json` - кеш. Markdown-форматирование через `t()` |
| `progress.py` | `update_progress(line)`, `clear_progress()` | `\r` + `sys.stdout.write()`, минуя логгер. Очистка: `\r\033[K` |

---

## 13. Предзагрузка CUDA-библиотек (cuda_loader.py) - подробно

**Проблема:** ctranslate2 (бэкенд faster-whisper) динамически загружает `libcublas.so.12`, `libcudnn.so.X`, `libcudart.so.X` и др. при первом encode на GPU. Эти библиотеки устанавливаются pip-пакетами `nvidia-cublas-cu12`, `nvidia-cuda-runtime-cu12`, `nvidia-cuda-nvrtc-cu12`, `nvidia-cudnn-cu12` в `site-packages/nvidia/*/lib`. Стандартный механизм поиска ld.so не находит их, так как пути не в `LD_LIBRARY_PATH`. Изменить `LD_LIBRARY_PATH` в рантайме нельзя - ld.so кеширует пути при старте процесса.

**Решение:** до импорта faster-whisper/ctranslate2 загрузить все `.so` файлы явно через `ctypes.CDLL(so, mode=ctypes.RTLD_GLOBAL)`. `RTLD_GLOBAL` делает символы библиотеки доступными для последующих `dlopen`-вызовов (включая те, что делает ctranslate2).

**Порядок загрузки** (важен для зависимостей):
1. `cuda_runtime` (libcudart)
2. `cublas` (libcublas, libcublasLt)
3. `cudnn` (libcudnn, библиотеки бэкендов)
4. `cuda_nvrtc` (libnvrtc, опционально)

**Важно:** модуль импортируется и вызывается в `main.py` до `from src.transcriber import transcribe`, чтобы CUDA-библиотеки были загружены до первого обращения к ctranslate2.

---

## 14. Pre-flight проверки (preflight.py) - подробно

### 14.1. Целостность моделей в HF-кеше

**Whisper** (`Systran/faster-whisper-{model_size}`): проверяются 5 обязательных файлов через `try_to_load_from_cache()`:
- `config.json`, `preprocessor_config.json`, `tokenizer.json`, `vocabulary.json`, `model.bin`

**pyannote pipeline** (`pyannote/speaker-diarization-3.1`): проверяется `config.yaml`

**pyannote segmentation** (`pyannote/segmentation-3.0`): проверяются `config.yaml`, `pytorch_model.bin`

**pyannote community** (`pyannote/speaker-diarization-community-1`): проверяются `config.yaml`, `embedding/pytorch_model.bin`, `segmentation/pytorch_model.bin`, `plda/plda.npz`, `plda/xvec_transform.npz`

### 14.2. Авто-доустановка

При отсутствии файлов: `snapshot_download(repo_id, token=HF_TOKEN)` в отдельном потоке с жестким таймаутом 30 минут (`threading.Thread` + `join(timeout)`). При `TimeoutError` - ошибка с инструкцией скачать вручную.

**Xet-бэкенд отключается:** `huggingface_hub.constants.HF_HUB_DISABLE_XET = True`. В `huggingface_hub` 1.19 xet-бэкенд может зависать на сетевом уровне при загрузке крупных моделей.

### 14.3. Gated-модели

При `GatedRepoError` (HTTP 403) выводится:
- Сообщение для каждой gated-модели с URL страницы на huggingface.co
- Для pyannote - общее сообщение: "Примите условия на всех трех страницах, либо отключите диаризацию"

### 14.4. Проверка API

- **DeepSeek:** `GET {api_url}/models` с `Authorization: Bearer {api_key}`, таймаут 15 сек
- **HuggingFace Hub:** `HfApi.whoami(token=HF_TOKEN)`, таймаут 15 сек. 401/403 → "HF_TOKEN невалиден или истек"

---

## 15. Кеширование транскрипций

**Цель:** избежать повторной транскрибации одного и того же файла (large-v3 обрабатывает ~5-10 минут на час аудио даже на GPU).

**Механизм:**
1. Для каждого файла вычисляется `file_hash = SHA256(file)`
2. Перед транскрибацией: `find_cached_transcription(conn, file_hash)` ищет в SQLite все сессии с тем же хешем (от новых к старым)
3. Для каждого кандидата проверяется наличие и валидность `transcription.json` в `session_dir`
4. При успехе: сегменты загружаются из JSON, строится `TranscriptionResult` - транскрибация пропускается
5. После успешной транскрибации: сырые данные сохраняются в `transcription.json` через `save_transcription_raw()`

**Важно:** кеш не фильтруется по статусу сессии, так как транскрипция могла завершиться успешно, но сессия помечена как `failed` из-за сбоя диаризации или саммаризации.

**Ограничения:** кешируется только транскрипция, не диаризация (зависит от настроек `min_speakers`/`max_speakers`) и не саммари (зависит от промпта).

---

## 16. Зависимости (requirements.txt)

```
faster-whisper==1.1.1
nvidia-cublas-cu12==12.4.5.8
nvidia-cuda-runtime-cu12==12.4.127
nvidia-cuda-nvrtc-cu12==12.4.127
nvidia-cudnn-cu12==9.1.0.70
pyannote.audio==4.0.4
python-dotenv==1.1.0
requests==2.32.3
tabulate==0.9.0
yt-dlp==2026.6.9
pytest==8.3.4
```

**Пояснение nvidia-* пакетов:** faster-whisper использует ctranslate2, который под капотом использует cuBLAS и cuDNN для GPU-вычислений. Пакеты устанавливают `.so` библиотеки в `site-packages/nvidia/*/lib`. `cuda_loader.py` загружает их через ctypes до импорта faster-whisper.

**Стандартная библиотека Python 3.14:** `configparser`, `pathlib`, `logging`, `sqlite3`, `subprocess`, `hashlib`, `json`, `datetime`, `typing`, `dataclasses`, `signal`, `time`, `sys`, `os`, `re`, `locale`, `threading`, `urllib`, `ctypes`, `shutil`, `tempfile`.

---

## 17. Рекомендации по реализации (best practices)

### 17.1. Выбор и загрузка модели Whisper

| Модель | Размер | VRAM | Качество |
|--------|--------|------|----------|
| large-v3 | 3 GB | ~10 GB | Лучшее |

- Кешировать модель в памяти через синглтон (один экземпляр на весь пайплайн)
- `compute_type=float16` для экономии VRAM
- VAD-фильтрация обязательна для файлов длиннее 30 секунд
- Язык указывать явно (ru) для повышения точности
- CUDA-библиотеки должны быть предзагружены через `cuda_loader.py` до импорта faster-whisper

### 17.2. Диаризация (pyannote.audio 4.x)

- Версия 4.0.4 (не 3.x - API изменился: `Pipeline.from_pretrained()` вместо `Pipeline.from_pretrained()`)
- Pipeline `pyannote/speaker-diarization-3.1` требует 3 gated-подмодели:
  - `pyannote/segmentation-3.0` - модель сегментации
  - `pyannote/speaker-diarization-community-1` - x-vector/PLDA рескоринг
  - `pyannote/wespeaker-voxceleb-resnet34-LM` - эмбеддинги (подтягивается как зависимость)
- Требуется HF_TOKEN с правами доступа ко всем gated-репозиториям
- Конвертация аудио в WAV 16kHz через ffmpeg обязательна перед pyannote (mp3 VBR/CBR дает нецелое число сэмплов)
- На GPU (CUDA) pyannote в 3-5 раз быстрее, чем на CPU
- Имена дикторов с ведущими нулями для правильной сортировки (`Спикер_01`, `Спикер_02`, ..., `Спикер_10`)

### 17.3. Саммаризация (DeepSeek API)

- Системный промпт: автоопределение языка текста, саммари на том же языке
- Temperature=0.3 (низкая креативность, высокая фактологичность)
- Map-reduce для длинных текстов: чанки по ~10500 символов (6000 токенов * 2.5 * 0.7), каждый чанк саммаризируется, затем итоговое саммари из саммари чанков
- Retry: 3 попытки, экспоненциальный backoff, не retry при 401/403

### 17.4. CUDA и GPU

- `nvidia-smi` должен показывать доступную CUDA
- Пакеты nvidia-* в requirements.txt должны соответствовать версии CUDA в системе
- `cuda_loader.py` - обязательный первый импорт в main.py
- При отсутствии GPU или ошибках CUDA - падение с понятным сообщением

### 17.5. ffmpeg и yt-dlp

- Проверять наличие при валидации: `subprocess.run(["ffmpeg", "-version"])` и `subprocess.run(["yt-dlp", "--version"])`
- Параметры ffmpeg для whisper: 16kHz, mono, 16-bit PCM WAV
- Временные файлы WAV - в `debug/`, удалять в `finally`
- yt-dlp скачивает аудио в нативном формате (opus/m4a/webm), ffmpeg декодирует любой кодек

### 17.6. Идемпотентность

- Каждый запуск main.py создает новые сессии для всех файлов в input/ - уникальность гарантируется timestamp в session_id
- Кеширование транскрипции по file_hash экономит время, но не нарушает идемпотентность (новая сессия все равно создается)
- UPSERT для всех операций с БД
- Атомарная запись файлов: `.tmp` → `replace()`

### 17.7. Атомарность записи файлов

```python
temp_path = target_path.with_suffix(".tmp")
temp_path.write_text(content, encoding="utf-8")
temp_path.replace(target_path)
```

### 17.8. Логирование

- Формат: `YYYY-MM-DD HH:MM:SS [маркер] сообщение`
- Маркеры: `[!]` error, `[i]` info, `[*]` warning
- Один запуск = один файл `log/log_main_<timestamp>.log`
- Все, что в консоли - в лог (кроме прогресса)
- Вывод через `t()` - ни одного строкового литерала в коде
- Без эмодзи, без цвета

### 17.9. Graceful shutdown

- `signal.signal(signal.SIGINT, _signal_handler)` + внешний `try/except KeyboardInterrupt`
- `clear_progress()` перед выходом
- Временные файлы удаляются в `finally`

### 17.10. Валидация при запуске (fail fast)

Порядок проверок:
1. Чтение config.ini и .env
2. Наличие `DEEPSEEK_API_KEY` и `HF_TOKEN`
3. Существование папок: `data/`, `log/`, `output/`
4. Наличие ffmpeg и yt-dlp в системе
5. Pre-flight: целостность моделей (whisper + pyannote), авто-доустановка
6. Pre-flight: доступность DeepSeek API, валидность HF_TOKEN
7. Схема БД соответствует `sql/schema.sql`
8. Таблица `translations` содержит переводы

Все проблемы выводятся одним блоком до начала обработки.

---

## 18. Формат лога

```
2026-06-15 17:30:00 [i] Запущен Transcribe & Summary Assistant v0.1.0
2026-06-15 17:30:00 [i] Проверка окружения
2026-06-15 17:30:01 [i] Проверка готовности пайплайна
2026-06-15 17:30:01 [i] Проверка модели: Systran/faster-whisper-large-v3
2026-06-15 17:30:01 [i] Модель готова: Systran/faster-whisper-large-v3
2026-06-15 17:30:01 [i] Проверка модели: pyannote/speaker-diarization-3.1
2026-06-15 17:30:01 [i] Модель готова: pyannote/speaker-diarization-3.1
2026-06-15 17:30:01 [i] Проверка DeepSeek API
2026-06-15 17:30:02 [i] DeepSeek API доступен
2026-06-15 17:30:02 [i] Проверка HuggingFace Hub и HF_TOKEN
2026-06-15 17:30:03 [i] HuggingFace Hub доступен
2026-06-15 17:30:03 [i] Проверка готовности пройдена
2026-06-15 17:30:03 [i] Проверка окружения завершена
2026-06-15 17:30:03 [i] Файлов к обработке: 2
2026-06-15 17:30:03 [i] Транскрибация: lecture.mp3
2026-06-15 17:35:15 [i] Транскрибация завершена: 15234 слов, уверенность 0.89, язык ru
2026-06-15 17:35:15 [i] Диаризация: lecture.mp3
2026-06-15 17:35:30 [i] Найдено дикторов: 2
2026-06-15 17:35:30 [i] Саммаризация: lecture.mp3 (DeepSeek)
2026-06-15 17:35:48 [i] Саммаризация завершена
2026-06-15 17:35:48 [i] Обработка завершена: 2026-06-15_17-30-03_a1b2c3d4, длительность: 345 сек
2026-06-15 17:35:48 [i] Обработано сессий: 2. Успешно: 2, с ошибками: 0
```

---

## 19. Переводы (i18n)

Хранилище: таблица `translations` в SQLite (key + lang composite PK).

113 ключей перевода в пространствах:
- `msg.*` - информационные сообщения (app_started, transcribing, session_completed)
- `error.*` - сообщения об ошибках (api_key_missing, transcription_failed)
- `prompt.*` - промпты для интерактивных меню
- `label.*` - метки (file, status, type, temperature, tokens)
- `menu.*` - пункты меню (db_init_clear, db_init_recreate)

Языки: ru (default), en. Fallback: ru → en → `!KEY!`.

Плюрализация для ru: `.zero`, `.one`, `.few`, `.many`. Для en: `.zero`, `.one`, `.many`.

---

## 20. Тестирование

Тесты в `test/`, pytest, 4 файла, 22 теста:

| Файл | Тестов | Покрытие |
|------|--------|----------|
| `test_file_scanner.py` | 9 | YouTube URL (валидные/невалидные несколько на файл), SHA256, сканирование audio/, yt/ |
| `test_session_manager.py` | 9 | generate_session_id, create_session_dir, save_metadata, save_transcription, save_summary, copy_summary_to_output, _format_timestamp, build_transcription_markdown, build_summary_markdown |
| `test_transcriber.py` | 1 | TranscriptionResult и TranscriptionSegment датаклассы |
| `test_summarizer.py` | 3 | _estimate_tokens, _chunk_text (короткий и длинный текст) |

Запуск: `pytest test/ -v`

---

## 21. Критерии готовности

1. `python main.py` проходит полный пайплайн для файлов из `input/audio/`, `input/video/`, `input/yt/`
2. `.txt` файл из `input/yt/` со ссылкой YouTube → yt-dlp → аудио → обработка
3. Каждый запуск создает новые сессии для всех файлов в input/ без пропусков
4. Pre-flight проверяет и авто-доустанавливает модели whisper + pyannote при необходимости
5. CUDA-библиотеки предзагружаются через cuda_loader.py до импорта faster-whisper
6. Транскрипции кешируются по file_hash (SHA256) - повторная обработка того же файла не выполняет транскрибацию заново; диаризация кешируется аналогично
7. Сессии создаются в `data/sessions/` с корректной структурой (metadata.json, transcription.md + transcription.json, diarization.json, summary.md, article.md)
8. Результаты (summary + article) копируются в `output/` атомарно; при включенной отправке email - каждое отправляется отдельным письмом
9. SQLite хранит историю сессий: sessions + processing_queue + translations
10. DeepSeek API работает с retry (3 попытки, эксп. backoff), map-reduce для длинных текстов
11. `run/db/*` скрипты проходят проверки (connection, schema, init)
12. `run/api/*` скрипты проверяют DeepSeek
13. Логи пишутся в `log/` с корректными маркерами `YYYY-MM-DD HH:MM:SS [i]`
14. Все тексты через `t()` (i18n, ru + en, 113 ключей)
15. Тесты покрывают ключевые модули (22 теста, 4 модуля)
16. Аннотации типов для всех функций
17. ffmpeg и yt-dlp проверяются при валидации
18. Graceful shutdown при Ctrl+C (сигнал + try/except)
19. Временные файлы удаляются в `finally`
20. Атомарная запись всех выходных файлов (`.tmp` → `replace`)

---

*Спецификация сформирована на основе стандарта 3.9.0 с учетом полного опыта реализации.*
