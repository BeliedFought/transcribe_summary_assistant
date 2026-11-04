<!-- START static -->
# AGENTS.md

Standard version: 5.0.0

This file contains instructions for AI agents working with this project.

## Session Entry Points

- `@doc/standards/_index_standards.md` - standards package index (registry, routing map, package version); read it first
- `@doc/skills/_index_skills_repo.md` - repository skills index
- `@doc/specs/_index_specs.md` - specifications index
- `data/memory/memory.md`, `data/memory/decisions.md`, `data/memory/env.md` - agent memory minimum when `data/memory/` exists; update it after significant decisions
- Ignore `.backup/`, `.trash/`, `.arch/`, `.opencode/`, `.kilo/` unless the user explicitly asks
- Tagging an `@_index_*.md` file without a task runs its index auto-update procedure

## Language & Typography Matrix

| Contour | Artifacts | Language |
| --- | --- | --- |
| Human | Chat responses, `README.md`, user guides, `doc/specs/`, implementation plans, `doc/change_requests/`, UI and console text through `t()` | Russian |
| Agent and code | `AGENTS.md`, `CLAUDE.md`, standards, indexes, skills, code, comments, docstrings, technical logs (`logger.*`), commit messages, subagent communication | English |

Typography applies to both contours: hyphen-minus `-` only (no em dash or en dash), letter `е` without diaeresis, no ellipsis, no emoji, no exclamation marks, no non-breaking or narrow spaces. User-facing text follows `doc/standards/human_text_standards.md`; the machine override is `~/.config/opencode/AGENTS.md`; the core rule is `project_standards.md` (04.03).

## Development Process

- Use the superpowers skills: `brainstorming` (design exploration and task classification), `writing-plans` (specs and implementation plans), `test-driven-development`, `systematic-debugging`, `subagent-driven-development` or `executing-plans`, `verification-before-completion`, `writing-skills`.
- Classify work as Spike, Bounded, or Architectural before implementation; ratchet up when hidden complexity appears.
- Write specifications and plans in Russian; keep them in `doc/specs/` (`init/` before MVP, `spec_<module>.md` after).
- Delegate isolated search, audit, and verification work to subagents; briefs and answers are English, the user summary is Russian.
- Fact-checking cascade: local code and standards -> `context7` MCP -> `github` MCP -> web search for exact error text -> ask the user when unverifiable.

## Safety, Git & Boundaries

- Mutate code or the system only after the execution trigger `ДЕЛАЙ` or `GO`; design-stage approvals inside `brainstorming` do not replace it.
- Delete repository files only by moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` with `MANIFEST.md`; exceptions: `tmp/` contents, git-native mirror/package synchronization, and `.trash/` purged only on explicit request.
- Run `sudo`, `su`, and `pkexec` only per the privilege levels in `project_standards.md` (05.04); never hardcode secrets.
- Git: one `master` branch; English Conventional Commits `<type>(<scope>): <imperative summary>`; authorship from `whoami` and `hostname`; no AI mention; never bump the package version without an explicit request.
- `CLAUDE.md` mirror: maintained permanently in the hub; deleted by default in derived repositories unless a repo override exists.
<!-- END static -->

<!-- START repo-specific -->
## Специфика репозитория: transcribe_summary_assistant

## Назначение

CLI-инструмент: транскрибация (faster-whisper, CUDA), диаризация (pyannote.audio), саммаризация (DeepSeek API) аудио, видео и YouTube-ссылок, опциональная отправка саммари на email (SMTP). Каждая обработка - отдельная сессия с метаданными в SQLite. Пользовательская документация и описание пайплайна - README.md.

## Сгенерированные команды

<!-- START generated-commands -->
Python 3.14 (`.python-version`), виртуальное окружение `.venv/` в корне проекта:

- Создание и активация: `python3 -m venv --copies .venv` и `source .venv/bin/activate`
- Зависимости: `pip install -r requirements.txt` (версии зафиксированы через `==`)
- Редактируемая установка (обязательна для `run/`-скриптов): `pip install -e .`
- Полный пайплайн: `python main.py`
- Тесты: `pytest` (тесты в `test/`, коммитятся)
- Проверка инфраструктуры: `python run/db/db_init.py`, `python run/db/db_check_schema.py`, `python run/api/api_check_connection.py`, `python run/email/email_test_send.py`
- Зеркало pip не хардкодить: подобрать доступное, навык `doc/skills/glob_setup_pip_mirror.md`
<!-- END generated-commands -->

## Структура репозитория

Полная таблица папок и файлов - в README.md. Поведенческие правила:

- `config/config.ini` - настройки (секции `[app]`, `[processing]`, `[whisper]`, `[diarization]`, `[youtube]`, `[deepseek]`, `[email]`, `[output]`, `[paths]`, `[retry]`); секреты - только в `.env` (`.env.example` - шаблон), загрузка через python-dotenv
- Входные данные: `input/audio/`, `input/video/`, `input/yt/` (`.txt` со ссылками YouTube); результаты - `output/`; отладка и диагностика - `debug/`, `diag/` (не коммитятся)
- SQL и DDL - только в файлах `sql/`; параметризованные запросы
- `doc/standards/` - только чтение; `doc/change_requests/` - транзитная

## Навыки репозитория

Полный реестр - в `doc/skills/_index_skills_repo.md`; специфичных проектных навыков нет, используются только общие (`glob_*`).

## Типичные scope коммитов

`standard`, `skills`, `specs`; продуктовые изменения - `feat`/`fix` без scope (по ранней истории).

## Особенности

- i18n: весь пользовательский текст через `t(key, **kwargs)` из `src/localization.py`, литералы естественного языка в коде запрещены; переводы - в таблице БД `translations`, язык: config.ini -> env `LANGUAGE` -> локаль -> `en`
- Логирование: `src/logger.py`, формат `YYYY-MM-DD HH:MM:SS [маркер] сообщение`, маркеры `[!]` ошибка, `[i]` информация, `[*]` предупреждение; все, что выводится в консоль, дублируется в лог; `print()` - только в интерактивных меню
- Версия приложения: `APP_NAME`/`APP_VERSION` в `src/config.py` из config.ini `[app]`; каждый entry-point при старте выводит имя и версию, агент предлагает бамп по типу коммита (SemVer)
- Запуск `python run/<домен>/<скрипт>.py` без `pip install -e .` падает с `ModuleNotFoundError: No module named 'src'`
- Кеш по `file_hash` (транскрибация, диаризация, YouTube-аудио): повторная обработка того же материала без GPU и загрузки аудио - README.md
<!-- END repo-specific -->

## Ссылки

- doc/standards/_index_standards.md - индекс пакета стандартов и политика версионирования
- doc/skills/_index_skills_repo.md - индекс навыков репозитория
- doc/specs/_index_specs.md - индекс спецификаций
- README.md - пользовательская документация, пайплайн, кеширование
- https://agents.md - канонический формат
