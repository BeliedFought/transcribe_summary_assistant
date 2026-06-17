# Инструкции для Claude Code

Этот файл содержит инструкции для AI-агента Claude Code при работе с данным проектом.

Соответствует стандарту: 3.9.0

## Repository Purpose

Transcribe & Summary Assistant - CLI-инструмент для транскрибации (speech-to-text), диаризации (разделение по голосам), саммаризации аудио- и видеофайлов и опциональной рассылки саммари на email (SMTP).

## Communication Language

All communication with the user, comments in code, documentation, and log messages must be in **Russian**. Replace ё/Ё with е/Е everywhere (including code comments and docs).

## Clarification Workflow

Before writing any code or making changes:
1. Collect all clarifying questions and write them to `doc/agent_questions/questions_[timestamp].md` (not in chat). Use `doc/agent_questions/questions_YYYY-MM-DD_HH-MM.md` as a structural reference for file format.
2. Notify the user in chat with the file path.
3. Wait for answers before proceeding.
4. Do not change any project files without explicit user confirmation.

## Repository Structure

| Path | Purpose |
|------|---------|
| `README.md` | Документация проекта для пользователей (русский) |
| `AGENTS.md` | Инструкции для AI-агентов (Kilo Code, Cursor) |
| `CLAUDE.md` | Зеркальная копия AGENTS.md (Claude Code) |
| `config/config.ini` | Все настройки проекта |
| `data/` | Рабочие данные: SQLite, кеш, сессии |
| `data/sessions/` | Папки сессий обработки |
| `debug/` | Отладочные скрипты и временные файлы |
| `diag/` | Диагностические данные (preflight-дампы, тесты моделей) |
| `doc/specs/` | Спецификации: init_spec.txt, final_spec.md |
| `doc/agent_questions/` | Уточняющие вопросы агента |
| `doc/change_requests/` | Запросы на изменения |
| `doc/skills/` | Навыки агента |
| `doc/standards/project_standards.md` | Эталонный стандарт (read-only) |
| `input/audio/` | Аудиофайлы для обработки |
| `input/video/` | Видеофайлы для обработки |
| `input/yt/` | .txt файлы со ссылками YouTube (можно несколько ссылок на файл) |
| `log/` | Лог-файлы |
| `main.py` | Оркестратор полного пайплайна |
| `output/` | Результаты обработки |
| `run/db/` | Скрипты работы с БД |
| `run/api/` | Скрипты проверки API |
| `run/ai/` | Скрипты проверки Ollama |
| `run/email/` | Скрипты проверки отправки email |
| `sample/` | Примеры данных |
| `sql/schema.sql` | DDL-схема SQLite |
| `src/` | Библиотечные модули |
| `test/` | Тесты pytest |

## Configuration & Secrets

- All configurable parameters -> `config/config.ini`
- Secrets (tokens, passwords, API keys) -> `.env` only
- Load via `python-dotenv`

## File Paths

Determine `PROJECT_ROOT` from `__file__` or location of `config/config.ini`. Build all paths as absolute relative to `PROJECT_ROOT`. Never rely on `cwd`.

## SQL

- All SQL queries and DDL in `.sql` files under `sql/`; never embed in code
- Use parameterized queries; never concatenate user input into query strings

## Localization (i18n)

- All output text (logs, console, menus, errors, prompts) must use `t(key, **kwargs)` from `src/localization.py`
- No natural language string literals in code - only in translation files and comments
- Translation storage: DB table `translations` (key + lang composite PK)
- Key naming: hierarchical with dot separator - `msg.*`, `error.*`, `prompt.*`, `label.*`
- Fallback: current lang -> default lang -> `!KEY!`
- Pluralization via `count` parameter: `.zero`, `.one`, `.few`, `.many` suffixes
- Language detection priority: config.ini `[app] language` -> env `LANGUAGE` -> system locale -> `en`

## Logging

- Shared logger module: `src/logger.py`; config/env loading in `src/config.py`
- Every `run/` script and `main.py` gets its own log file by default
- Log location: `log/log_[script_name]_[timestamp].log`; one run = one log file
- Log everything that is output to console, always and without exception; output is identical in both
- Never use `print()`; no colour, no emoji
- **Exception:** interactive menu modules may use `print()` for menu display
- Format: `YYYY-MM-DD HH:MM:SS [marker] message`
- Markers: `[!]` error, `[i]` info, `[*]` warning

## Startup Validation

- Every script validates its environment before main logic: required config params, paths, files, external connections
- Fail fast: output all problems at once, then exit with clear messages via `t()`
- Validation order: config -> required params -> paths/files -> external connections

## Retry for External Connections

- Use exponential backoff for DB, API connections: configurable `retry_count` and `retry_delay` in config
- Max delay: 30 seconds. Log each retry attempt
- Do NOT retry auth errors (401/403) or validation errors (400/422) - only timeouts and 5xx

## Idempotency and Atomicity

- Scripts must be safe to re-run: no duplicates, use UPSERT or existence checks
- Atomic file writes: write to `.tmp` then `replace()` - never write directly to target
- DB operations: use transactions, rollback on error, batch commits

## Graceful Shutdown

- Handle SIGINT (Ctrl+C) via `signal` or `try/except KeyboardInterrupt`
- Release resources: close DB connections, open files, delete temp files
- Rollback incomplete transactions on interruption
- Use context managers (`with`) for files and connections

## Log/Console Format

```
YYYY-MM-DD HH:MM:SS [marker] message
```

Markers: `[!]` error, `[i]` info, `[*]` warning.

## Virtual Environment & Python Version

- Store the virtual environment inside the project: `.venv/` folder in the project root
- Create with: `python3 -m venv --copies .venv`
- Activate via `source .venv/bin/activate`
- Install dependencies with: `pip install -r requirements.txt`
- Pin Python version in `.python-version`
- pip mirror: pypi.org may be unavailable (TLS, network restrictions).
  Do NOT hardcode a mirror. Probe candidates and pick the fastest available:
  https://pypi.ru/simple/, https://mirror.yandex.ru/pypi/simple/, https://mirrors.aliyun.com/pypi/simple/
  If current `~/.config/pip/pip.conf` works fine - leave it unchanged.
  Otherwise write the selected mirror to `~/.config/pip/pip.conf`
- `.gitignore` excludes: `.env`, `.venv/`, `log/`, `debug/`, `diag/`, `input/`, `output/`, `data/`, `__pycache__/`, `.pytest_cache/`, `.vscode/`, `.claude/`, `.kilo`, `doc/agent_questions/`, `doc/change_requests/`

## Git

- Single branch: `master`
- Commit message format - Conventional Commits, language: Russian
- Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`
- One logical change per commit; do not mix unrelated changes
- AI-agent commit authorship: determine dynamically at each commit
  - `user.name` = output of `whoami`
  - `user.email` = `$(whoami)@$(hostname)`
  - First commit: save to local repo config:
    `git config --local user.name "$(whoami)" && git config --local user.email "$(whoami)@$(hostname)"`
  - Subsequent commits: verify saved values; auto-update if whoami/hostname changed
  - Do NOT use `-c` flags in git commit; rely on local repo config
- On explicit commit request: include ALL changed and untracked files not in `.gitignore`.
  Run `git status`, verify no `.gitignore` files are staged, then `git add` and commit

## Dependencies

- Pin all versions with `==` in `requirements.txt`
- Prefer the standard library; justify any new dependency

## Error Handling

- Log errors with context (script name, execution stage, relevant inputs)
- Exit with `sys.exit(1)` on critical failure

## Text Requirements

- All output text uses `t()` from `src/localization.py` - no natural language string literals in code
- Language: Russian for comments, documentation, user messages
- No emotional language, no ALL-CAPS emphasis, no exclamation marks
- Use hyphen `-` (U+002D) instead of em-dash `---` and en-dash `--` everywhere
- No ellipsis (`...` or `...`) anywhere
- Always specify `encoding="utf-8"` when opening files
- No leading spaces at the start of new text lines
- No period at the end of log/console messages

## Typing

- Use type annotations for all functions: parameters and return values
- For complex types use `typing` or `from __future__ import annotations`

## Testing

- Place tests in `tests/` at project root
- Use pytest; naming: `test_[module_name].py`
- `tests/` is not excluded from git; tests are committed

## Cross-platform Paths

- Use `pathlib.Path` for all paths - auto OS-specific separators
- Do not concatenate paths via strings or use hardcoded separators
- Paths from config/env wrap in `Path()` when reading
- Paths in `config.ini` use forward slashes - pathlib handles both OS
- For directory creation: `path.mkdir(parents=True, exist_ok=True)`

## GitHub

- SSH key: scan `~/.ssh/*github*.pub` (do not hardcode key name)
- Key creation pattern: `id_ed25519_{hostname}_github`
- Test connection: `ssh -i "$KEY_PATH" -T -p 443 git@ssh.github.com`
- Network git commands: set `GIT_SSH_COMMAND="ssh -i $KEY_PATH -o BatchMode=yes -o StrictHostKeyChecking=no"`

## Editing README.md, AGENTS.md and CLAUDE.md

When editing `README.md`, `AGENTS.md` or `CLAUDE.md`: determine the original language of the document and write new content in that same language. Preferred language: `AGENTS.md` and `CLAUDE.md` - English; `README.md` - Russian.

`AGENTS.md` is the primary AI agent instructions file. `CLAUDE.md` is its mirror copy (except for the main H1 header and the purpose description). Any change in one must be synchronously applied to the other. The content of both files is always identical.

## Maintaining doc/standards/project_standards.md

- In this repo: read-only. Do not edit.

## Privileged Operations (root, sudo)

- NEVER execute commands with `sudo`, `su`, `pkexec`, or any other privilege-elevation mechanism
- If a task requires root/sudo: tell the user, ask to run manually, wait for confirmation

## Application Versioning

- `config.ini [app]`: name (human-readable) and version (SemVer)
- `src/config.py` exports `APP_NAME` (str) and `APP_VERSION` (str)
- Initial version: `0.1.0`
- Every entry-point script outputs `APP_NAME v{APP_VERSION}` as one of the first actions
- Agent proposes version bump at each commit based on commit type

## Naming Conventions

- All identifiers, filenames, modules: Latin characters, `snake_case`
- Numbered identifiers use leading zeros for alignment: `step_01`, `batch_003`
- No emotional language, no ALL-CAPS emphasis, no exclamation marks, no ellipsis in any generated text
