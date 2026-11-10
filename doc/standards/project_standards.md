# Project Standards. Version 5.0.1

Core rules across initialization, development, refactoring, and maintenance. Coding rules: `doc/standards/code_standards.md`. SQLite marts, `diag/`/`tmp/`/`test/`, sessions, SQL/migrations, and `run/` CLI: `doc/standards/cli_data_standards.md`. Retries, SSH, DPI/routing, and system config mutations: `doc/standards/network_ops_standards.md`. Universal rules apply to all repos; Python rules (`.venv`, `requirements.txt`, `pytest`) apply to Python projects; deviations use `doc/specs/overrides.md` (Section 01.01.02). Tagging `@doc/standards/project_standards.md` runs the audit in Section 07.04.

## Table of Contents

- **01. Structure & Config:** `01.01` Layout (`01.01.01`-`01.01.07`), `01.02` `config.ini`, `01.03` Identity/SemVer, `01.04` Paths, `01.05` Validation, `01.06` Deps, `01.07` `.venv`
- **02. Connections:** `02.01`-`02.03` DB/API/Ollama, `02.04` Retry, `02.05` GitHub SSH, `02.06` SMTP, `02.07` SSH Hosts, `02.08` DPI/Routing
- **03. Architecture & CLI:** `03.01` Idempotency, Atomicity & `--dry-run`, `03.02` SQL (`03.02.01`-`03.02.03`), `03.03` `run/` (`03.03.01`-`03.03.04`), `03.04` CLI
- **04. Output & UI:** `04.01` `t()`, `04.02` Markers, `04.03` Language Split & Typography, `04.04` Format (`04.04.01`-`04.04.06`), `04.05` Errors, `04.06` Logging, `04.07` Modes (`04.07.01`-`04.07.04`), `04.08` GUI
- **05. Security:** `05.01` Secrets & Sudoers, `05.02` Exceptions, `05.03` Shutdown & Exit Codes, `05.04` Privileged Operations (Levels 0-3)
- **06. Git & Testing:** `06.01` Git & Pre-Commit Gate, `06.02` `README.md` & `AGENTS.md`, `06.03` Debugging, `06.04` Testing
- **07. Workflow:** `07.01` Superpowers & Subagents, `07.02` Clarification, Specs & `ДЕЛАЙ`/`GO`, `07.03` Init, `07.04` Audit, `07.05` Hub Editing, `07.06` Decision Cascade
- **08-09. Glossary & Links:** `08.01` Glossary, `09.01` Related Standards, `09.02` Versioning

---

# 01. Fundamentals and Project Structure

## 01.01. Project Structure

Create only directories the project uses; never invent top-level folder names.

| Directory | Purpose & Rules |
|-----------|-----------------|
| `config/` | `config.ini` (`[app]` `name`, `version`, Section 01.03) and `translations.json` for DB-less projects (Section 04.01) |
| `data/` | Working data (git-ignored) except tracked: `data/skills/`, `data/memory/`, `data/lessons.md`, `data/registries/`, `data/journals/`, `data/state/`. Backups in `data/backup/<topic>/`; skill cache in `data/cache/<skill>/` |
| `diag/`, `test/` | Optional committed scripts in `<dir>/<domain>/<domain>_<type>_<action>.<ext>` + `_index_diag.md` (01.01.04) / `_index_test.md` (01.01.05) |
| `debug/`, `tmp/` | `debug/`: local debug scripts (`.gitkeep` only). `tmp/`: scratch in `tmp/<domain>/` (01.01.04, untracked, no `.gitkeep`, deleted after commit) |
| `.trash/` | Deletion quarantine `.trash/<slug>_<YYYYMMDDHHMM>/` + `MANIFEST.md` (01.01.06). Untracked, no `.gitkeep` |
| `.backup/<version>/` | Cold read-only snapshots of prior standard versions; ignored by agents unless explicitly requested |
| `doc/standards/` | Standards package (read-only outside hub, Section 07.05); entry point `_index_standards.md` |
| `doc/standards/templates/` | Reference code templates (`config.ini.example`, `config.py`, `localization.py`, `logger.py`, `progress.py`, `gitignore.template`, `install.py`, `update.py`) synced with `doc/standards/`, loaded on demand |
| `doc/specs/` | `init/` (`init_base.txt`, `init_final.md` pre-MVP; archived to `.arch/` at MVP), `spec_<module>.md` (07.02), `spec_ui.html` (`console_ui_standards.md`), `overrides.md` (01.01.02), and `_index_specs.md` (`index_nav_standards.md`, Section 06.03) |
| `doc/agent_questions/` | Batch question files `questions_YYYY-MM-DD_HH-MM.md` (07.02). Untracked except `.gitkeep` |
| `doc/change_requests/` | Incoming CRs `cr_<slug>.md` + `_index_change_requests.md` (`change_request_standards.md`). Committed |
| `doc/skills/` | Anthropic skills (`<name>/SKILL.md`, `skill_anthropic_standards.md`): `hub-` (`hub_loc`), `glob-` (`hub_glob`), `pg-` (`pr_glob`), `ext/<repo>/`. Local skills (`pr_loc`) in `data/skills/` + `_index_skills_pl.md` |
| `input/`, `output/`, `sample/`, `log/` | Input/output files and logs `log_<script>_<timestamp>.log` (04.06, `.gitkeep` only); spec samples `sample/{db,api}_*` (committed) |
| `run/`, `sql/`, `src/`, `templates/` | Entry points `run/{db,api,ai,email}/` (03.03); SQL `sql/{ddl,queries,dml,migrations}/` + `_index_sql.md` (03.02); library `src/` (`config.py`, `logger.py`, `localization.py`, `exceptions.py`, `src/gui/`); content templates `templates/` |

- **Root files:** `README.md`, `AGENTS.md`, `.env`, `.env.example` (empty-value mirror of `.env`), `requirements.txt`, `.gitignore` (06.01), `.gitattributes` (06.01), `.python-version` (01.07).
- **Archiving (`.arch/`):** move completed/superseded artifacts (fulfilled CRs, pre-MVP `doc/specs/init/`, finished sessions) intact into a sibling `.arch/` folder and remove their rows from active `_index_*.md`. Auto-archive artifacts completed in the current task; never touch historical artifacts without user request. `.arch/` is git-ignored at all depths; include `.arch/` in uniqueness checks.
- **Orchestration:** repeatable pipelines use one orchestrator (`main.py` at root or `<session>/run/orch_<name>.py`). Steps in `src/` exchange files/DB tables; the orchestrator sequences calls, checks statuses, and halts on error (parameters via CLI flags or `config.ini`, never interactive input).

### 01.01.01. Session Structures and `SESSION.md`

Subproject marked by `SESSION.md` (`ID: YYYY-MM-DD_<slug>`, localized `data/`, `log/`, `doc/specs/`, SemVer, overrides, `<session>/run/orch_*.py`). See `cli_data_standards.md` (Sections 03.01-03.03).

### 01.01.02. Project Standard Overrides (`doc/specs/overrides.md`)

Record agreed deviations in `doc/specs/overrides.md` (`Standard Section | Deviation | Rationale | Approval Date`). Without a row and user approval, global rules apply (Section 07.06).

### 01.01.03. Local Data Mart and Pipeline Modes

External DB extracts cache in `data/mart.sqlite` (`mart_*` + `mart_meta.snapshot_ts`) with `src_*.sql` / `report_*.sql` and `--mode local|refresh`. See `cli_data_standards.md` (Sections 01.01, 01.02).

### 01.01.04. `diag/` and `tmp/`: Diagnostics and Scratch Artifacts

`diag/<domain>/<domain>_<type>_<action>.<ext>` (`check`, `report`, `dump`, `profile`) + `diag/_index_diag.md`, hardware stress-test cutoffs, and `tmp/<domain>/` rules: see `cli_data_standards.md` (Sections 02.01-02.03).

### 01.01.05. `test/`: Agent Reference Tests

`test/<domain>/<domain>_<type>_<action>.<ext>` + `test/_index_test.md` (user approval required to add/remove tests). See `cli_data_standards.md` (Section 02.04) and Section 06.04.

### 01.01.06. Agent Trash Quarantine (`.trash/`)

Never delete repo files directly (`rm`, `unlink`, `git clean`); move intact (preserving relative paths) to `.trash/<slug>_<YYYYMMDDHHMM>/` with `MANIFEST.md` (date, agent/host, reason, paths + git status, count). Exceptions: `tmp/`, `.trash/` (purged only on user request), git mirror syncs (`reset --hard`, `checkout`, `pull`) when state is in reflog, and managed package/skill file removals performed by sync skills (git-native deletions recoverable from history; check `git status` first and quarantine or ask on uncommitted changes). Skills modifying `$HOME` configs quarantine displaced files into an adjacent folder with a manifest and restore commands.

### 01.01.07. Lessons Log (`data/lessons.md`)

Append-only log (`!data/lessons.md`) of portable lessons (`glob-mine-lesson` / `hub-mine-knowledge`): `## YYYY-MM-DD - <topic>`, `Контекст: <file/commit/OS>`, `Урок: <generalized rule without hostnames/paths>`. Instance facts go to `data/memory/env.md` or `doc/specs/overrides.md`.

## 01.02. Configuration (`config/config.ini`)

Store tunable settings in `config/config.ini` and secrets in `.env` (Section 05.01). Use typed getters (`getint()`, `getfloat()`, `getboolean()`). Include `[app]` (`name`, `version`, optional `language`) and used sections only. **Template:** `doc/standards/templates/config.ini.example`.

## 01.03. Application Identity and Versioning

Ask the user for `[app] name` before scaffolding (Section 07.03); initialize `[app] version = 0.1.0` (SemVer; synced with `pyproject.toml` in deployable tools). Log `logger.info("Started %s v%s", APP_NAME, APP_VERSION)` (English technical log) and render the user banner with `console_message(logging.INFO, t("msg.app_started", name=APP_NAME, version=APP_VERSION))` in every entry point (Section 04.06). On commit, propose a SemVer bump by commit type (`feat` -> MINOR; `fix`/`chore` -> PATCH; `refactor` -> PATCH/MINOR; `docs`/`test`/`style` -> none; never auto-propose MAJOR).

## 01.04. File Paths and Cross-Platform Compatibility

Compute `PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent` once in `src/config.py` and import `PROJECT_ROOT`, `config`, `APP_NAME`, `APP_VERSION` everywhere. Build paths via `pathlib.Path` relative to `PROJECT_ROOT` (no `cwd` reliance or string concatenation; `/` in `config.ini`). Enforce LF via `.gitattributes` (Section 06.01). **Template:** `doc/standards/templates/config.py`.

## 01.05. Startup Validation (Fail Fast)

Before domain logic, validate in order: (1) load `config.ini`/`.env`, (2) required keys/secrets, (3) required paths/files, (4) external connections. Report all failures in one batch via `t()` and exit with code `2` (Section 05.03). Probe host environment via a heuristic cascade before aborting.

## 01.06. Dependencies and Static Analysis

Pin `==` versions in `requirements.txt` and prefer stdlib. Commit `uv.lock` when using `uv`; run `pip-audit` before releases. Keep dev tools (`ruff`, `mypy`) in `requirements.txt` (or `pyproject.toml` dev group, never mixed). Run linters per `code_standards.md` (Section 08).

## 01.07. Virtual Environment and Python Version

Create `.venv/` with copies (`python3 -m venv --copies .venv`) and record `.python-version`. Before `pip install`, verify `~/.config/pip/pip.conf`; if missing or slow, benchmark candidates from `glob-cfg-pip` (never hardcode mirror URLs), write the fastest to `~/.config/pip/pip.conf`, and report latency.

---

# 02. External Connections

## 02.01. Database Connection

Read `DRIVER`, `SERVER`, `DATABASE`, `PORT` from `[db]` in `config.ini` and credentials from `.env`; ask the user if missing.

## 02.02. External API Connection

Read `BASE_URL`, `ENDPOINTS`, `timeout` from `[api]` in `config.ini` and auth tokens/keys from `.env`.

## 02.03. Ollama Connection

Read `BASE_URL`, `MODEL` (comma-separated), `DEVICE` (`cpu`/`gpu`), `timeout` from `[ollama]` in `config.ini`.

## 02.04. Connection Retries and Channel Liveness

Shared `retry()` helper with exponential backoff from `[retry]` (`retry_count = 3`, `retry_delay = 2`, max `30s`), `Retry-After` on HTTP `429`, and channel liveness HTTP probes (`!= 000` vs `000`). See `network_ops_standards.md` (Sections 01.01, 01.02).

## 02.05. GitHub SSH Discovery and Network Operations

Never hardcode SSH key names. Loop over `~/.ssh/*github*.pub` and test each key until the first working key authenticates:

```bash
KEY_PATH=""
for pub in ~/.ssh/*github*.pub; do
    [ -e "$pub" ] || continue
    cand="${pub%.pub}"
    if ssh -i "$cand" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new -T -p 443 git@ssh.github.com 2>&1 | grep -q "successfully authenticated"; then
        KEY_PATH="$cand"; break
    fi
done
[ -n "$KEY_PATH" ] || { echo "[!] No working GitHub SSH key in ~/.ssh/*github*.pub" >&2; exit 1; }
export GIT_SSH_COMMAND="ssh -i $KEY_PATH -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
```

If missing, ask the user to generate `~/.ssh/id_ed25519_$(hostname -s)_github`. Never use `StrictHostKeyChecking=no`.

## 02.06. Email Connection (SMTP)

Read `enabled`, `smtp_host`, `smtp_port`, `smtp_security` (`ssl`/`starttls`/`none`), `from`, `to`, `subject_*` from `[email]` in `config.ini` and `SMTP_USER`, `SMTP_PASSWORD` from `.env`. Send multipart (`text/plain` + `text/html`) email via `src/email_sender.py`.

## 02.07. SSH Client Configuration and Embedded Targets

`Host <shortname>` blocks in `~/.ssh/config` with mandatory `HostKeyAlias <shortname>`, `SSH_ASKPASS_REQUIRE=force` on embedded devices, lockout protection, and `/usr/bin/ssh`: see `network_ops_standards.md` (Sections 02.01, 02.02).

## 02.08. DPI Networks, Selective Routing, and SMB

IKEv2/IPsec DPI blocking, DNS spoofing vs DoT/DoH, SOCKS5 SNI desync + tunnel, IPv6 blackholes, CDN routing (`curl --resolve`), vendor geo-gates, and Samba/SMB (`nofail`): see `network_ops_standards.md` (Sections 03.01-03.07).

---

# 03. Architecture and Entry Points

## 03.01. Idempotency, Atomicity, and File Operations

- **Idempotency & DB atomicity:** re-runs yield identical state without duplicates (`UPSERT`, unique indexes, checkpoints); wrap multi-row/table writes in one transaction with `rollback()` on error.
- **Atomic file writes:** write to a hidden temp file in the same directory, flush + `os.fsync()`, set/preserve permissions (`0600`), and `temp_path.replace(target_path)` (over SSH shell: temp + `chmod` + `mv`). Always pass `encoding="utf-8"`.
- **Mutation preview (`--dry-run`):** required on all mutating CLI / `run/` scripts (prints planned changes without mutating, exits `0`). In non-interactive contexts (Section 04.07), never auto-confirm prompts silently; require `--yes` or abort suggesting `--dry-run`.
- **System reliability patterns:** watchdog state retention, multi-phase reboot migrations, `/proc` running-app checks, and vendor base-file hashing: see `network_ops_standards.md` (Sections 04.01-04.04).

## 03.02. SQL and DDL

Store SQL in `sql/{ddl,queries,dml,migrations}/` and load at runtime with parameterized queries. See `cli_data_standards.md` (Section 04.01).

### 03.02.01. SQL Index (`sql/_index_sql.md`)

Maintain `sql/_index_sql.md` (`index_nav_standards.md`, Section 06.04) and read it before loading `.sql` files. See `cli_data_standards.md` (Section 04.01).

### 03.02.02. SQL Placement Rules

Place DDL in `sql/ddl/`, `SELECT`s in `sql/queries/`, seeds in `sql/dml/`, and live migrations in `sql/migrations/`. See `cli_data_standards.md` (Section 04.01).

### 03.02.03. Schema Migrations

Track `sql/migrations/M<N>_*.sql` in `schema_version` transactionally; never run `DROP + CREATE` on live data. See `cli_data_standards.md` (Section 04.02).

## 03.03. Entry Points (`run/`)

Domain entry points live in `run/{db,api,ai,email}/` (`<domain>_<action>.py`). See `cli_data_standards.md` (Section 05.01).

### 03.03.01. `run/db`

`db_check_connection.py`, `db_check_schema.py`, `db_init.py`, `db_migrate.py`: see `cli_data_standards.md` (Section 05.01).

### 03.03.02. `run/api`

`api_check_connection.py`, `api_test_requests.py`: see `cli_data_standards.md` (Section 05.01).

### 03.03.03. `run/ai`

`ai_ollama_check.py`, `ai_ollama_pull_models.py`: see `cli_data_standards.md` (Section 05.01).

### 03.03.04. `run/email`

`email_test_send.py`: see `cli_data_standards.md` (Section 05.01).

## 03.04. CLI Conventions

`argparse`, localized `--help` via `t()`, exit code `2` on unknown flags, and mutator `unavailable` vs `not applicable` contract: see `cli_data_standards.md` (Section 05.02).

---

# 04. Output and Interface

## 04.01. Localization (`i18n` and `src/localization.py`)

- **Language boundary:** **user-facing UI and console output** (`report`, `menu`, `rich`, GUI widgets, `--help`, and status/error notices in `plain` and `report` modes) defaults to **English** and goes through `t(key, *, count=None, **kwargs)` from `src/localization.py` (`config/translations.json` or SQLite `translations` table); `en` is the default locale. Russian is allowed through `t()`, `[app] language`, `LANGUAGE`, or a project override. Internal technical logs use **English** with `%s` formatting without `t()` (Section 04.06). Developer-only check scripts in `run/` may omit `t()` if recorded in the project spec.
- **Keys & fallback:** dot-separated Latin keys (`menu.*`, `msg.*`, `error.*`, `title.*`, `prompt.*`, `label.*`, `help.*`) with plural suffixes (`.zero`, `.one`, `.few`, `.many`). Priority: `[app] language` -> `LANGUAGE` -> locale -> `"en"`. The default catalog is English; Russian is an optional translation. Fallback: `active_lang -> default_lang -> "!KEY!"`. No literal `{}` outside `{param}`.
- **API contract:** `t(key, *, count=None, **kwargs) -> str`, `init(language=None) -> None`, `reload(language=None) -> None`. **Template:** `doc/standards/templates/localization.py`.

## 04.02. Text Markers (No Emoji)

`_MarkerFormatter` in `src/logger.py` prefixes plain-mode and log-file lines with `[!]` (`ERROR`/`CRITICAL`), `[i]` (`INFO`/`DEBUG`), or `[*]` (`WARNING`). Never embed markers inside `t()` strings or log literals; never use emoji.

## 04.03. Language Split and Typography Rules

- **Human Contour (Russian):** user chat responses, `README.md`, user guides, `doc/specs/`, `doc/change_requests/`, `data/lessons.md`, `SESSION.md`. Governed by `doc/standards/human_text_standards.md` and its three dictionaries.
- **User-Facing Output (English default, Russian opt-in):** console strings, `report`, `menu`, `rich`, GUI widgets, and `--help` via `t()` (`translations.json`, `spec_ui.html`). English is the default catalog; Russian is allowed through `t()`, `[app] language`, `LANGUAGE`, or a project override, so the package does not cement one language. Format canon - `cli_output_standards.md`.
- **Agent and Code Contour (English):** code identifiers, filenames, config/translation keys (Latin only, no transliteration; `code_standards.md`, Section 02.01), code comments and docstrings, technical log records (`logger.*` with `%s`), git commit messages (Section 06.01), subagent briefs/reports, `AGENTS.md` / `CLAUDE.md`, `doc/standards/*.md`, `doc/skills/**`, and `_index_*.md`. (Cyrillic allowed only in `[app] name`, session folder names `YYYY-MM-DD_<Cyrillic-Slug>`, and user content filenames in `output/`/`data/`/`input/`/`backup/`).
- **Typography Rules (mandatory across all contours):**
  - **Hyphen-minus (`-`, U+002D) only:** never use em dash (U+2014) or en dash (U+2013), including number ranges (`10-15`).
  - **Letter `е` (U+0435 / U+0415) only:** never use the letter with diaeresis (U+0451 / U+0401).
  - **No ellipsis (`...` or U+2026), no emoji, no exclamation marks (`!`)**, and **no non-breaking/narrow spaces** (U+00A0, U+202F) or leading paragraph indentation.
  - **No trailing period** on log lines, console status messages, or commit titles.
  - **Normative present-state facts only:** no emotional qualifiers, no ALL-CAPS emphasis, no historical "was/became" narratives, no `CHANGELOG` unless requested, no raw DB/enum/config identifiers in user text, no host absolute paths in docs (except `spec_ui.html` footer), and Latin `<placeholder_name>` with zero-padded numbers (`item_001`).

## 04.04. Output Formatting

### 04.04.01. Line Format

Log file (always, English) and `plain` console through `console_message()` (English default, Russian opt-in): `YYYY-MM-DD HH:MM:SS [marker] message`. `report` console: structured report (`cli_output_standards.md`, Section 02). `menu` console: `message` (no prefix). `rich` console: styled via `src/rich_console.py` (Section 04.07.03).

### 04.04.02. General Formatting Rules

One message per line; no separator lines (`=====`, `-----`), emoji, or trailing periods; zero-pad counters (`09/23`). Log files and `plain` are monochrome; `report` color follows `cli_output_standards.md` (02.05); `menu`/`rich` colors follow `doc/specs/spec_ui.html` (`console_ui_standards.md`).

### 04.04.03. Block Spacing

Separate logical stages in `plain` console and log files with one blank line (`\n\n`).

### 04.04.04. Tables

In log files, use `tabulate` (`grid`, `simple`, `pipe`, `outline`; text left, numbers right) with a localized title. In `menu`/`rich`, render dual-channel tables via `src/console_table.py` (`console_ui_standards.md`).

### 04.04.05. Lists

Localized header followed immediately by `- item` lines and optional summary (`console_message()` in `plain`; `log_file_only()` + frame body in `menu`/`rich`, `console_ui_standards.md`, Section 03.03).

### 04.04.06. Summaries

Single-line `prefix: key: N, key: M` via `t()` without panels (`console_ui_standards.md`, Section 03.04).

## 04.05. Error Wording and Terminology

Format user-facing errors as single-line human-readable messages via `t()` (English default, Russian opt-in) without raw subprocess `stderr`/`stdout` or internal jargon. Keep domain terminology uniform everywhere.

## 04.06. Dual-Channel Logging (`src/logger.py`)

- **Dual-channel contract:** `logger.debug/info/warning/error/exception` write **English** technical records to the **log file only**, using lazy `%s` formatting (`logger.info("Loaded %d rows from %s", count, table)`), never f-strings or `t()`. User-facing console output defaults to **English** via `console_message(level, t("key", ...))` in `plain` mode and as a bare line without a timestamp in `report` mode; Russian is allowed through the locale. In `report` mode the structured block is rendered by the report helpers (`cli_output_standards.md`, Section 02); in `menu`/`rich` modes the presentation layer (`src/menu.py`, `src/rich_console.py`) renders the screen and `console_message()` is a no-op. The log file always uses `plain`, regardless of the console mode. Use `log_file_only(logger, message, level)` for explicit audit events.
- **Files & levels:** one file per run at `log/log_<script_name>_<YYYY-MM-DD_HH-MM-SS>.log`. `[logging] file_level` (default `DEBUG`) sets the `FileHandler` level. `[logging] keep_last` (default `0`) rotates older logs per script. `_SecretFilter` masks `SECRET_KEYS` (Section 05.01).
- **Permitted `print()` exemptions (no log file):** (1) `scripts/` in Anthropic skills (full `YYYY-MM-DD HH:MM:SS [marker] message` emulation required), (2) temporary scripts in `tmp/`/`debug/`, (3) agreed read-only check scripts in `run/`, (4) custom OpenCode tool scripts (`opencode_tool_standards.md`).
- **Template:** `doc/standards/templates/logger.py`.

## 04.07. Console Output Modes

Select `mode="report" | "plain" | "menu" | "rich"` in `get_logger()`. The default is `report` for human-facing output; `plain` is the clean mode for logs and parsable streams; `menu` and `rich` are interactive TTY modes selected explicitly. **Interactive context (TTY):** `sys.stdout.isatty()` is true and neither `CI` nor `TERM=dumb` is set (plus `sys.stdin.isatty()` for `menu`). Decide fallback once at startup: outside interactive context, degrade `menu`/`rich` to `plain` without `Live`/colors and never call `input()`. The log file always uses `plain`, regardless of the console mode (`cli_output_standards.md`, 01.01).

### 04.07.01. Clean Stream (`plain`) and `src/progress.py`

Clean mode for logs and parsable streams. Not the default for human status output; `report` is. For long loops, use `src/progress.py` (`update_progress(line)` via `\r` and `clear_progress()` via `\r\033[K` on `sys.stdout`, bypassing the log file), calling `clear_progress()` on completion and `SIGINT` before printing the final summary via `console_message()`. **Template:** `doc/standards/templates/progress.py`.

### 04.07.02. Interactive Menu (`menu`)

Rendered by `src/menu.py` without raw ANSI cursor positioning; governed by `console_ui_standards.md` and `doc/specs/spec_ui.html`.

### 04.07.03. Rich Console (`rich`)

Rendered by `src/rich_console.py`, `src/console_table.py`, and `src/console_summary.py`; governed by `console_ui_standards.md` and `doc/specs/spec_ui.html`. Stop `Live`/progress on `SIGINT`/`SIGTERM`.

### 04.07.04. Structured Report (`report`)

Default for human-facing status output. Renders a snapshot of one object: header, key-value block with a 16-character key column, steps `[n/m]`, and a final `Result` line. Errors go to stderr as `error: <text>`; exit codes are `0`/`1`/`2`. Color follows `CLI_COLOR`, `NO_COLOR`, `FORCE_COLOR`, and auto-detection; `plain` and `--porcelain` never receive ANSI. The full contract and examples - `cli_output_standards.md` (Section 02).

## 04.08. Graphical User Interface (GUI)

Launch from `main.py` (`{APP_NAME} v{APP_VERSION}` title, `tkinter` by default), isolating UI in `src/gui/` with all strings via `t()` (English default, Russian opt-in) and blocking I/O on background threads. Run startup validation (Section 01.05) before opening the window; on critical failure, report via `t()` and exit with **`sys.exit(2)`**.

---

# 05. Security and Reliability

## 05.01. Security

- **Secrets:** keep secrets only in `.env` (`0600` on POSIX); enforce two-tier log protection (call-site whitelist + `_SecretFilter` blacklist in `src/logger.py`). Store external app config secrets in separate `0600` files and sanitize skill snapshots/reports.
- **External input:** validate every external value before use (schema, type, range, length); reject or normalize invalid input at the boundary. Never pass raw user, network, file, or API data into SQL, shell, paths, or templates.
- **SQL, subprocess, TLS, paths:** use parameterized SQL, `subprocess.run(["cmd", ...], shell=False)`, `verify=True` on TLS requests, and `Path(user_path).resolve()` containment checks under `PROJECT_ROOT / "data"`.
- **`/etc/sudoers.d/` fragments:** narrow Level 2 commands only (exact `command -v` paths and args, explicit `user`/`host`, no `*`, `ALL`, shells, or root-equivalent write/unit primitives; cloud-init image provisioning exempt). Stage via `mktemp` (`0600`), filename without dots, validate with `visudo -cf` before installing `root:root` `0440`, then verify with `visudo -c`.

## 05.02. Error Handling

Catch specific exceptions (never bare `except:` or `except Exception: pass`), log unexpected tracebacks with `logger.exception()` and expected errors with `logger.error()`, chain with `raise ... from err`, and define domain exceptions under `ProjectError(Exception)` in `src/exceptions.py`.

## 05.03. Graceful Shutdown and Exit Codes

Close DB connections, roll back uncommitted transactions, clean up `tmp/`, and clear progress on exit or `SIGINT`/`SIGTERM` (never rely on `atexit` for critical cleanup). Propagate failed step codes in orchestrators.
- **Exit codes:** `0` = success (or clean daemon `SIGTERM` stop), `1` = runtime error, `2` = startup validation (Sections 01.05, 04.08) or CLI usage error (`cli_data_standards.md`, Section 05.02), `130` = `SIGINT` (`Ctrl+C`), `143` = CLI `SIGTERM`.

## 05.04. Privileged Operations (`root`, `sudo`)

By default, agents never run `sudo`, `su`, `pkexec`, or `sudo -S`; explain the command and ask the user to run it manually.
- **Privilege levels for scripts (Linux only):**
  - **Level 0 (PTY `tmux`/`screen`):** on explicit user request in the current session, print the command, create an isolated `tmux -L <sock>` session running `sudo <abs_interp> <abs_script>`, and let the user type their password within `passwd_timeout` (5 min). The agent never passes the password through `tmux send-keys`, the clipboard, or argv; a closed session return code is not proof of success - verify the resulting system state.
  - **Level 1 (GUI askpass):** script self-elevates via `sudo -k -A` with GUI askpass.
  - **Level 2 (Narrow `NOPASSWD`):** script runs `sudo -k -n <exact_cmd>` against a validated `/etc/sudoers.d/` rule (Section 05.01).
  - **Level 3 (File askpass):** wrapper reads first line of a user-created `0600` file (in `0700` dir outside repo/`/tmp`, max 4096B, non-symlink) once per run (single-attempt marker prevents AD/LDAP lockout) for `sudo -k -A`. Agents never read/print the password file.
- **Protocol (Levels 1-3):** requires a targeted `doc/specs/overrides.md` row (`05.04`, skill/script, level `1`/`2`/`3`, date) verified by the script itself before self-elevation; never downgrade to Level 3 on failure (exit `1` and print manual commands). The agent never constructs or executes `sudo` commands directly for Levels 1-3; the script performs self-elevation. After execution, verify state objectively, `chown "$SUDO_UID:$SUDO_GID"` created artifacts, include `sbin` in `PATH`, and use `runuser` with `XDG_RUNTIME_DIR` for user-session tools.

---

# 06. Documentation and Versioning

## 06.01. Git and Pre-Commit Integrity Gate

- Single branch `master`; `.gitattributes` with `* text=auto eol=lf`; `.gitignore` from `doc/standards/templates/gitignore.template` (with `.gitkeep` in used ignored folders).
- **Commit messages:** English Conventional Commits `<type>(<scope>): <imperative summary>` (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`), lowercase imperative verb, no trailing period, no AI mention.
- **Dynamic author:** set `git config --local user.name "$(whoami)"` and `user.email "$(whoami)@$(hostname)"` before committing (never `-c`). When asked to commit, stage all non-ignored modified/untracked files after checking `git status`.
- **Pre-commit gate (`.githooks/pre-commit`, activated via `git config core.hooksPath .githooks`):** blocks commits if (1) `doc/standards/*.md` is staged without `_index_standards.md`, (2) package versions mismatch across `doc/standards/*.md` and `AGENTS.md`/`README.md`/`CLAUDE.md`, (3) `CLAUDE.md` diverges from `AGENTS.md`, or (4) any `Section NN.NN` / `раздел NN.NN` / `(NN.NN` reference in staged standards is broken. Never use `--no-verify`.

## 06.02. `README.md` and `AGENTS.md`

Write `README.md` in Russian per `repo_info_doc_standards.md` (linking to `spec_ui.html` for menu maps) and `AGENTS.md` in compact English per `index_nav_standards.md` (Section 07). Include the package version marker (Section 07.04).

## 06.03. Debugging Discipline

Keep debug scripts in `debug/` and scratch files in `tmp/<domain>/`. Follow `superpowers:systematic-debugging` for root-cause investigation (reproduce -> localize boundary -> verify hypothesis via Section 07.06 -> minimal fix) and stop after **3 failed fix attempts** to re-evaluate architecture or escalate to the user.

## 06.04. Testing

Store agent reference tests in `test/<domain>/` (`cli_data_standards.md`, Section 02.04) using `pytest` (`test_<topic>.py`, fixtures, parametrize, mocked DB/API/Ollama, synthetic data). Prioritize testing retry backoff/`Retry-After` (02.04), idempotency (03.01), log rotation (04.06), migrations (03.02.03), and core `src/{config,logger,localization}.py`.

---

# 07. Workflow

## 07.01. General Workflow Rules and Superpowers Integration

1. Never change existing business logic without user approval.
2. **Superpowers delegation:** use `superpowers:brainstorming` (design exploration), `superpowers:writing-plans` (implementation plans), `superpowers:test-driven-development` (TDD), `superpowers:subagent-driven-development` / `superpowers:executing-plans` (execution, model selection, ruling ledger, two-stage review), `superpowers:systematic-debugging` (Section 06.03), `superpowers:verification-before-completion` (fresh command output required before any completion claim), and `superpowers:writing-skills` (creating or editing skills).
3. **Subagent language contract:** write subagent briefs in **English** (passing large inputs via file paths) with `Respond in English; keep verbatim repo quotes in Russian`. Subagent repo outputs must obey Section 04.03.
4. **Documentation sync:** update `README.md` and `doc/specs/spec_ui.html` on structural/UI changes; ask before deleting outdated docs.

## 07.02. User Communication, Requirement Clarification, and Execution Trigger

- Communicate with the user in **Russian** (Section 04.03).
- **Superpowers delegation:** use `superpowers:brainstorming` for design exploration and task classification, `superpowers:writing-plans` for written specs and implementation plans (including the `Review Focus` rubric).
- **Task classification & ratchet:** classify tasks as **Spike**, **Bounded**, or **Architectural**; halt and ratchet up if hidden complexity appears.
- **Clarification modes:** ask once per dialogue whether to use **Interactive mode** (one prioritized question at a time via the `question` tool with ranked options citing Section 07.06 sources, updating the spec incrementally) or **Batch mode** (`doc/agent_questions/questions_YYYY-MM-DD_HH-MM.md` with ranked options and `Ответ:` blocks, moved to `.trash/` once answered).
- **Russian specifications (`doc/specs/`):** pre-MVP specs in `doc/specs/init/` (`init_base.txt` -> `init_final.md`), archived to `doc/specs/.arch/` at MVP; post-MVP modular specs in `doc/specs/spec_<module>.md` (with up to 5 **Review Focus** out-of-scope failure classes) fed by `doc/change_requests/cr_<slug>.md` and indexed in `doc/specs/_index_specs.md`.
- **User screenshots:** when mentioned without a path, inspect the newest image in `~/Pictures/Screenshots`, `~/Рабочий стол`, `~/Desktop` (or Windows/macOS equivalents), copy to `tmp/<domain>/` if needed, and ask on ambiguity.
- **Execution trigger (`ДЕЛАЙ` or `GO`):** stay in read/plan/spec mode until the user sends uppercase `ДЕЛАЙ` or `GO` (word-boundary match; authorizes one major task).
- **Data UI recon & mockup:** before building any first UI over real data, run read-only data recon into `tmp/<domain>/`, review anomalies with the user, and obtain approval on a single-file interactive HTML+JS mockup in `tmp/<domain>/` before `ДЕЛАЙ` / `GO`.

## 07.03. Project Initialization Sequence (14 Steps)

Verify `doc/standards/project_standards.md` exists, then: (1) ask for `[app] name`, (2) save `doc/specs/init/init_base.txt`, (3) clarify requirements (07.02), (4) write `doc/specs/init/init_final.md` & `_index_specs.md`, (5) agree on `doc/specs/spec_ui.html` if UI output exists, (6) `git init` + `.gitignore` + `.gitattributes`, (7) create needed folders (01.01), (8) create `.env` (`0600`), `.env.example`, `config/config.ini` (`0.1.0`), `requirements.txt`, `.python-version`, (9) create `.venv` (`--copies`), check `pip.conf` (01.07), install deps, (10) scaffold `src/{config,logger,localization,exceptions}.py` from `doc/standards/templates/` and test, (11) implement domain `src/` & `run/`/`main.py`, (12) verify TTY output vs `spec_ui.html`, (13) write `README.md` & `AGENTS.md`, (14) set local git author and commit `feat: initialize project`.

## 07.04. Standard Compliance Audit and Upgrade Procedure

Version marker in `AGENTS.md`, `README.md`, and `CLAUDE.md`: `Standard version: X.Y.Z` (or `Соответствует стандарту: X.Y.Z`). When auditing: compare `project_standards.md` H1 version with repo markers, verify `spec_ui.html` against code, and if discrepancies exist, output a numbered remediation list citing sections (always including version marker update, Section 04.03 text/language check, and `doc/` indexes) without mutating files until approved. On package upgrades (`hub-sync-standards`), apply PATCH/MINOR/MAJOR diffs or record overrides in `doc/specs/overrides.md`.

## 07.05. Editing Standards in the Hub

Edit `doc/standards/*.md` only in the `project_standards` hub (read-only in derivative repos). Never bump package SemVer without an explicit user request (`_index_standards.md`). Whenever any `doc/standards/*.md` changes, update `_index_standards.md` in the same commit and verify with `.githooks/pre-commit` and `python3 doc/skills/hub-sync-indexes/scripts/collect_meta.py`.

## 07.06. Decision and Fact-Checking Cascade

Priority order: (1) current dialogue user instructions -> (2) `SESSION.md` overrides (01.01.01) -> (3) `doc/specs/overrides.md` (01.01.02) -> (4) repo indexes (`_index_standards.md`, skill indexes, `_index_sql.md`) -> (5) repo precedent -> (6) verified external sources -> (7) documented platform conventions -> (8) reversible agent judgment (ask user for irreversible choices).
- **Fact-checking cascade (never guess):** on any unfamiliar API, version/compatibility doubt, new dependency, pattern choice, or unexplained error, check in order: Local code/standards -> **Context7 MCP (`context7`)** for library/API/SDK docs -> **GitHub MCP (`github`)** for real-world patterns, code, and issues -> Web search for exact error strings. Cite sources for key decisions; if uncheckable (offline/missing source), stop and ask the user (Section 07.02).

---

# 08. Terminology

## 08.01. Package Glossary

- **Session / Override:** subproject directory with `SESSION.md` (`01.01.01`, `cli_data_standards.md` 03.01) / agreed deviation in `SESSION.md` or `doc/specs/overrides.md` (`01.01.02`).
- **Execution Trigger:** uppercase word `ДЕЛАЙ` or `GO` authorizing one major task (`07.02`).
- **Hub / Skills (`pr_glob`, `pr_loc`):** `project_standards` repo (`07.05`) / `pg-` skills in `doc/skills/` vs local skills in `data/skills/` (`skill_anthropic_standards.md` 01.03).
- **Data Mart / Pipeline Modes:** local `data/mart.sqlite` snapshot and `local` / `refresh` modes (`01.01.03`, `cli_data_standards.md` 01.01-01.02).
- **Lessons Log / Agent Memory:** append-only `data/lessons.md` (`01.01.07`) vs persistent context in `data/memory/` (`memory_standards.md`).
- **Orchestrator / Migration:** pipeline entry point `main.py` or `orch_*` (`01.01`) / one-time `sql/migrations/M<N>_*.sql` in `schema_version` (`03.02.03`, `cli_data_standards.md` 04.02).
- **Dual-Channel / Interactive Context:** English file logs (`logger.*`) vs user-facing console output (`report`, `plain`, `menu`/`rich`; English default, Russian opt-in) (`04.06`) / TTY without `CI` or `TERM=dumb` (`04.07`).
- **Output Format (`report` / `plain` / `menu` / `rich` / `porcelain`):** human status report, clean stream for logs and parsing, interactive menu, rich console, and machine-readable `--porcelain` (`cli_output_standards.md`, 01.01).
- **Frame / Role / Batch CLI / `spec_ui.html`:** console screen unit, semantic style role, two-line rich-progress CLI, and visual UI/log spec (`console_ui_standards.md`).
- **Init vs Active Specs:** pre-MVP `doc/specs/init/` (archived to `.arch/` at MVP) vs modular `doc/specs/spec_<module>.md` (`07.02`, `07.03`).
- **Front / Backend / Pre-Commit Hook:** nginx server block vs FastAPI uvicorn process (`web_standards.md` 01.02) / `.githooks/pre-commit` gate (`06.01`).

---

# 09. Cross-References and Versioning

## 09.01. Related Standards

- **Core & Architecture:** `_index_standards.md` (registry, routing, SemVer), `cli_data_standards.md` (`mart.sqlite`, `diag/`/`tmp/`/`test/`, `SESSION.md`, `sql/`, `run/`), `network_ops_standards.md` (retries, SSH, DPI/routing/SMB, config mutations), `code_standards.md` (languages & linters).
- **UI & Text:** `console_ui_standards.md` (`menu`, `rich`, `spec_ui.html`), `cli_output_standards.md` (named formats, `report`, `plain`, `porcelain`, color, language), `human_text_standards.md` + `human_text_*_standards.md` (Russian text rules and dictionaries), `repo_info_doc_standards.md` (`README.md`), `software_doc_standards.md` (install guides).
- **Deploy & Web:** `deploy_standards.md`, `deploy_lin_standards.md`, `deploy_win_standards.md`, `deploy_docker_standards.md`, `deploy_hyperv_standards.md`, `web_standards.md`.
- **Agent Ecosystem:** `skill_anthropic_standards.md`, `skill_data_standards.md`, `opencode_tool_standards.md`, `memory_standards.md`, `index_nav_standards.md`, `change_request_standards.md`.

## 09.02. Versioning

Unified package SemVer is governed by `doc/standards/_index_standards.md` (see Sections 07.04 and 07.05). Never bump the package version without an explicit user request.
