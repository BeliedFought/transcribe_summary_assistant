# CLI & Data Architecture Standards. Version 5.0.1

Architecture, storage, and entry-point rules for CLI pipelines, local SQLite data marts, diagnostic/test harnesses, session subprojects, SQL layout/migrations, and `run/` scripts. Apply on top of `project_standards.md`. For decision priority, see `project_standards.md` (Section 07.06).

## Table of Contents

| Section | Contents |
|---------|----------|
| **01. Local SQLite Data Mart** | Local caching of external DB extracts, `mart.sqlite`, `src_`/`report_` SQL sets, `local`/`refresh` pipeline modes |
| 01.01 | Purpose and Architecture |
| 01.02 | `mart.sqlite`, `src_`/`report_` SQL Sets, and `local`/`refresh` Modes |
| **02. Diagnostic Scripts (`diag/`), Scratch Artifacts (`tmp/`), and Reference Tests (`test/`)** | Reusable diagnostics, hardware stress-testing safeguards, temporary artifacts, and agent reference tests |
| 02.01 | Diagnostic Scripts (`diag/<domain>/` and `_index_diag.md`) |
| 02.02 | Privileged Collectors, Hardware Stress Tests, and Environment Diagnostics |
| 02.03 | Ephemeral Scratch Artifacts (`tmp/<domain>/`) |
| 02.04 | Agent Reference Tests (`test/<domain>/` and `_index_test.md`) |
| **03. Session Structures and `SESSION.md`** | Self-contained session subprojects, metadata marker, overrides, lifecycle, and archiving |
| 03.01 | Session Definition, Localization, ID, and Folder Naming |
| 03.02 | `SESSION.md` Template, Version, Overrides, and Lifecycle |
| 03.03 | Archiving Sessions to `.arch/` |
| **04. SQL Scripts and Schema Migrations** | `sql/` directory layout, index, DDL rules, and incremental schema migrations |
| 04.01 | `sql/` Directory Layout, `_index_sql.md`, and Placement Rules |
| 04.02 | Schema Migrations (`schema_version`, `sql/migrations/`, and Live Data Protection) |
| **05. Entry Points (`run/`) and CLI Contract** | Domain verification scripts, `argparse` flags, localized `--help`, and mutator status contract |
| 05.01 | Entry Points (`run/{db,api,ai,email}`) and Domain Verification Scripts |
| 05.02 | CLI Conventions (`argparse`, `--help` via `t()`, Exit Code 2, and Mutator Item Contract) |
| **06. Cross-References and Versioning** | Related standards and package versioning |
| 06.01 | Related Standards |
| 06.02 | Versioning |

---

# 01. Local SQLite Data Mart

*Required for projects where a pipeline extracts data from an external database.*

## 01.01. Purpose and Architecture

- When a repository or session pipeline queries an external database repeatedly across runs, extract the raw dataset once into a local SQLite data mart and build all reports and downstream outputs from that local snapshot.
- Store the data mart at `data/mart.sqlite` (or `<session>/data/mart.sqlite` inside a session, Section 03.01). When a project maintains multiple independent marts, name them `data/mart_<domain>.sqlite`.
- Exclude `data/mart*.sqlite` from git as part of `data/` (`project_standards.md`, Section 06.01).
- Prefix all data tables in the mart with `mart_` followed by an English snake_case entity name (`mart_orders`, `mart_customers`; `code_standards.md`, Section 02.01).
- Include a metadata table `mart_meta` containing a required row with key `snapshot_ts` and value `YYYY-MM-DD HH:MM:SS` recording the timestamp of the last successful full refresh from the external source.

## 01.02. `mart.sqlite`, `src_`/`report_` SQL Sets, and `local`/`refresh` Modes

**SQL query separation (`sql/queries/`):**
- `src_<entity>.sql` - extraction queries executed against the external source database (e.g., MS SQL, PostgreSQL). Keep `src_` queries strictly limited to extraction (projection, filtering, minimal joins); never embed analytical or reporting calculations in `src_` queries, or `local` mode will be unable to reproduce reports without querying the source.
- `report_<entity>.sql` - analytical and reporting queries executed against the local SQLite mart (`data/mart.sqlite`). Place all computational and aggregation logic here.
- Use the `report_` prefix (distinct from the `mart_` table prefix) to prevent running source-dialect SQL against SQLite or vice versa. Register all queries in `sql/_index_sql.md` (Section 04.01).

**Pipeline execution modes:**
- Support two explicit modes in the orchestrator (`main.py` or `<session>/run/orch_*.py`, `project_standards.md`, Section 01.01):
  - `local` - build outputs exclusively from `data/mart.sqlite` without connecting to the external database.
  - `refresh` - validate the source schema, extract data from the external database, atomically replace the local mart tables, update `mart_meta.snapshot_ts`, and then run the `local` build from the mart.
- Pass the mode via a CLI flag (`--mode local|refresh`) or `config.ini` setting, never via interactive prompt. Implement the mart refresh step as a dedicated function/module in `src/` called by the orchestrator.
- **Schema validation on `refresh`:** verify expected source table and column names/types before extracting data. On mismatch, abort `refresh` with a human-readable error (`project_standards.md`, Section 04.05) without modifying `data/mart.sqlite`. Document required source columns in `sql/_index_sql.md`.
- **Atomic replacement:** `refresh` overwrites previous mart data completely within a single transaction or via staging tables followed by an atomic swap (`project_standards.md`, Section 03.01). Update `mart_meta.snapshot_ts` only after the replacement commits. Staleness thresholds and default mode selection are defined per project.

---

# 02. Diagnostic Scripts (`diag/`), Scratch Artifacts (`tmp/`), and Reference Tests (`test/`)

*Required when `diag/`, `tmp/`, or `test/` directories are used.*

## 02.01. Diagnostic Scripts (`diag/<domain>/` and `_index_diag.md`)

- Store only reusable diagnostic scripts in `diag/`: environment checks, state collectors, snapshots, and profilers. Never place one-off scripts or raw artifacts in `diag/`. Commit `diag/` and its index to git.
- **Boundary between `diag/` and `test/` (Section 02.04):** `diag/` answers "what is happening in the environment or component" (investigation, state dumps, profiling without a pass/fail verdict on project correctness). `test/` answers "does the project/change behave as expected" (verification of project invariants and agent changes). Example pair: `diag/db/db_dump_schema.py` (dumps schema for inspection) vs `test/db/db_check_migrations.py` (verifies migration invariants).
- **Layout and naming:** group scripts into domain subdirectories `diag/<domain>/<domain>_<type>_<action>.<ext>` using English snake_case (`code_standards.md`, Section 02.01). Keep only `_index_diag.md` at the root of `diag/`.
  - `<domain>` - shared domain vocabulary across `diag/`, `test/`, and `tmp/` (`env`, `git`, `db`, `net`, `disk`, `py`, etc.).
  - `<type>` - closed vocabulary (extend only by updating the standard, `project_standards.md`, Section 07.05):
    - `check` - targeted point check returning a verdict and exit code
    - `report` - data collection producing a human-readable report
    - `dump` - raw state snapshot for offline analysis
    - `profile` - performance and resource measurement
  - `<action>` - specific action slug (e.g., `diag/env/env_check_python.py`, `diag/git/git_dump_status.sh`, `diag/db/db_check_connectivity.py`).
- **Index `diag/_index_diag.md`:** required whenever `diag/` exists; follow `index_nav_standards.md` (Sections 03, 04, 06.05) with per-domain tables. Do not create separate markdown docs per script; keep descriptions in `_index_diag.md` and update it in the same commit whenever `diag/` changes.

## 02.02. Privileged Collectors, Hardware Stress Tests, and Environment Diagnostics

- **Privileged dump collector vs unprivileged parser:** split root-level diagnostics into two layers: a minimal privileged collector script that outputs raw state (one command per output section with a header containing host, timestamp, and invoker), and an unprivileged parser/agent pass that builds the human-readable report.
- **Hardware stress-testing safeguards:**
  - Enforce named emergency cutoffs (thermal threshold, minimum battery level) with automatic abort.
  - Verify that the workload actually started by sampling utilization right after launch (preventing false pass verdicts on idle hardware).
  - Record an explicit named stop reason in the output artifact for every termination, and inspect kernel logs (`dmesg` / `journalctl -k`) for hardware errors after the run.
  - When a test requires a physical user action (e.g., plugging in AC power), poll state in a loop and record the wait event in the artifact; run bounded test intervals rather than full battery discharge or destructive wear cycles.
- **Cleaning up orphaned hardware test processes and device operations:**
  - Launch stress utilities that fork child processes in a dedicated process group/session (`os.setsid` / `start_new_session=True`), terminate the entire process group on exit or abort, and then kill any surviving stragglers by binary name.
  - For operations that continue autonomously on hardware after the host process exits (e.g., `smartctl` drive self-tests), explicitly issue the device abort command (`smartctl -X`) in the interrupt/cleanup handler.
- **Environment diagnostic patterns:**
  - When scanning logs by pattern, maintain an explicit allowlist of known benign matches (feature capability lines, normal idle state codes) with explanatory comments next to each entry.
  - Run preflight dependency checks before long diagnostic runs, including conditional tools required by the detected hardware/environment, and print exact install commands for every missing tool.
  - Collect hardware metrics across multi-vendor devices via a cascading provider chain, tagging each reading with its source provider; when a sensor is unavailable, record the specific reason instead of an empty value.
  - When checking whether a systemd unit is enabled via `systemctl is-enabled`, treat all active unit states (`enabled`, `enabled-runtime`, `static`, `alias`, `indirect`, `generated`) as enabled rather than only literal `enabled`.

## 02.03. Ephemeral Scratch Artifacts (`tmp/<domain>/`)

- Place all one-off agent and tool artifacts (Playwright screenshots, temporary exports, drafts, debug dumps) in domain subdirectories `tmp/<domain>/` using the same `<domain>` vocabulary as `diag/` and `test/`.
- Never store secrets in `tmp/` (`project_standards.md`, Section 05.01). Never commit `tmp/` or add `tmp/.gitkeep` (`project_standards.md`, Section 06.01).
- Delete artifacts created in `tmp/` immediately after completing and committing the task. Any file in `tmp/` may be deleted at any time without notice; never reference `tmp/` paths from project code or persistent documentation.

## 02.04. Agent Reference Tests (`test/<domain>/` and `_index_test.md`)

- `test/` holds permanent, reusable verification scripts that agents run to verify project behavior after modifications (`project_standards.md`, Section 06.04). Scripts may use `pytest` or standalone executable scripts. Commit `test/` and `test/_index_test.md` to git.
- **User approval required:** always propose and obtain explicit user confirmation before adding or removing reference tests in `test/` (`project_standards.md`, Section 07.02).
- **Layout, naming, and index:** group files under `test/<domain>/<domain>_<type>_<action>.<ext>` using the same domain and `<type>` vocabulary as `diag/` (Section 02.01), e.g., `test/env/env_check_python.py`, `test/db/db_check_migrations.py`. Maintain `test/_index_test.md` per `index_nav_standards.md` (Sections 03, 04, 06.05) and update it in the same commit whenever `test/` changes.

---

# 03. Session Structures and `SESSION.md`

*Required when working with session subprojects.*

## 03.01. Session Definition, Localization, ID, and Folder Naming

- **Definition:** a session is any repository subdirectory explicitly designated by the user that contains a `SESSION.md` marker file at its root (e.g., under `doc/change_requests/<id>/` or `doc/specs/<project>/`). A directory without `SESSION.md` is not a session. A session acts as a self-contained mini-repository with its own optional `src/`, `data/`, `sql/`, `log/`, `doc/`, and `run/` directories governed by all project standards, sharing the root git repository.
- **Prohibitions:** never create nested sessions (`SESSION.md` inside an existing session tree) and never place `SESSION.md` at the repository root.
- **Session root discovery:** search upward from the current working directory to the repository root for `SESSION.md`; the first match defines the active session root.
- **Artifact localization:** keep session-specific `doc/agent_questions/`, `doc/specs/`, `log/`, `data/`, and session memory `data/memory/` (`memory_standards.md`) inside the session folder rather than the repository root. Place one-off scratch files in the root `tmp/` (Section 02.03). Use `<session>/config/config.ini` if custom settings are needed, or fall back to the root `config/config.ini`. Place the session orchestrator at `<session>/run/orch_<action>.py`.
- **Session ID:** `YYYY-MM-DD_<slug>` where `<slug>` is an English kebab-case slug without transliteration (`code_standards.md`, Section 02.01), e.g., `2026-07-21_setup-db`. Use the Session ID in commit scopes (`feat(2026-07-21_setup-db): add export module`), orchestrator references, and links. Verify repository-wide uniqueness (including `.arch/` folders) before creating a new `SESSION.md`.
- **Session folder name:** independent of the canonical Session ID in `SESSION.md`. Recommend naming the folder `YYYY-MM-DD_<Russian-Summary-Slug>` (date, underscore, capitalized Cyrillic words joined by hyphens, 2-4 words, e.g., `2026-07-21_Настройка-выгрузки`), which is an explicit human-readable exception to Latin technical naming (`project_standards.md`, Section 04.03).

## 03.02. `SESSION.md` Template, Version, Overrides, and Lifecycle

- **Creation and maintenance:** create `SESSION.md` only when the user explicitly designates a session directory (or propose a draft header and wait for confirmation if a folder looks like an unmarked session). Update `SESSION.md` whenever the session structure, entry point, outputs, status, or version changes.
- **Session version:** independent SemVer (`MAJOR.MINOR.PATCH`) tracked in `SESSION.md`, bumped on user request or significant session changes.
- **Session overrides:** deviations from global standards require explicit user agreement and a row in the `SESSION.md` overrides section (standard section reference, deviation, rationale, approval date). Priority order (`project_standards.md`, Section 07.06): current dialogue instructions > `SESSION.md` overrides > repository `doc/specs/overrides.md` > global standards.
- **Lifecycle statuses:** `активна` (active), `приостановлена` (paused), `завершена` (completed), `отменена` (cancelled). Never modify files in a session whose status is not `активна` without explicit user instruction.

**`SESSION.md` template:**

```markdown
# Сессия: <title>. Версия X.Y.Z

Маркер сессионной структуры. Папка с этим файлом - самостоятельный подпроект: на нее распространяются все требования стандарта (именование, структура, конфигурация, логирование, требования к тексту), кроме отдельного git. Агент при любых изменениях в сессии поддерживает этот файл актуальным - как README корневого проекта.

---

Идентификатор: 2026-07-21_setup-db
Дата создания: 2026-07-21
Статус: активна
Версия: 0.1.0
Цель: <goal>

---

## Структура сессии

<structure_description>

## Точка входа

<entry_point_path>

## Результаты

<expected_results>

## Оверрайды стандарта

<overrides>
```

## 03.03. Archiving Sessions to `.arch/`

- Apply the repository archiving rules (`project_standards.md`, Section 01.01): move completed (`завершена`) or cancelled (`отменена`) session directories intact into the `.arch/` subdirectory of their parent folder (e.g., `doc/change_requests/.arch/<session_folder>/`).
- Include archived sessions in `.arch/` when checking Session ID and folder name uniqueness.

---

# 04. SQL Scripts and Schema Migrations

*Optional - required when the project uses a database.*

## 04.01. `sql/` Directory Layout, `_index_sql.md`, and Placement Rules

- Store all SQL queries and DDL schemas in `.sql` files under `sql/` and load them at runtime; never embed raw SQL strings or table names in Python code. Always use parameterized queries (`project_standards.md`, Section 05.01).

| Subdirectory | Contents | Example |
|--------------|----------|---------|
| `sql/ddl/` | `CREATE TABLE`, `ALTER`, indexes (initial schema) | `create_users.sql` |
| `sql/queries/` | Runtime `SELECT` queries (`src_` and `report_`, Section 01.02) | `get_active_users.sql` |
| `sql/dml/` | `INSERT`, `UPDATE`, `DELETE` seeds and data scripts | `seed_categories.sql` |
| `sql/migrations/` | Incremental schema migrations for live databases | `M001_add_status.sql` |

- **SQL index (`sql/_index_sql.md`):** required whenever `sql/` contains files. Follow the skeleton and template in `index_nav_standards.md` (Section 06.04), listing each file, purpose, query parameters, and consumer scripts per subdirectory. Agents read `sql/_index_sql.md` first and load only the relevant `.sql` files. Update `sql/_index_sql.md` in the same commit whenever SQL files change.
- **Placement rules:** `run/db` scripts read `sql/ddl/` recursively to determine expected tables and columns. Evolve live databases exclusively through `sql/migrations/`, never by editing `sql/ddl/` and re-running destructive initialization.

## 04.02. Schema Migrations (`schema_version`, `sql/migrations/`, and Live Data Protection)

- Track applied migrations in a `schema_version` table with columns `version` (`TEXT PRIMARY KEY`) and `applied_at` (`TEXT`).
- Name migration files `sql/migrations/M<N>_<description>.sql` with zero-padded sequential numbers (`M001_add_orders_status.sql`, `M012_create_mart_indexes.sql`).
- Apply each migration exactly once inside a single transaction together with its `INSERT INTO schema_version` record (`project_standards.md`, Section 03.01). Never edit an already applied migration; fix mistakes with a new sequential migration.
- **Prohibition on live data destruction:** agents must never execute `DROP TABLE`, `DROP + CREATE`, or `TRUNCATE` on a live database containing accumulated data. Instead, generate a migration file or provide exact commands for the user. Any table deletion or truncation requires explicit interactive confirmation (`project_standards.md`, Section 04.07); in non-interactive contexts, abort and suggest `--dry-run` (`project_standards.md`, Section 03.01).

---

# 05. Entry Points (`run/`) and CLI Contract

*Required for CLI entry points and domain scripts.*

## 05.01. Entry Points (`run/{db,api,ai,email}`) and Domain Verification Scripts

- Group user-invocable scripts under `run/<domain>/` with filename prefix `<domain>_<action>.py`. Keep the repository orchestrator at root `main.py` and session orchestrators at `<session>/run/orch_*.py` (`project_standards.md`, Section 01.01).
- Create the standard verification scripts below whenever the project uses the corresponding domain (output messages use `t()` in English by default with Russian opt-in, plus automatic logger markers `[i]` / `[*]` / `[!]`, `project_standards.md`, Section 04.04.01):

| Domain | Script | Behavior |
|--------|--------|----------|
| `run/db/` | `db_check_connection.py` | Connect using `config.ini` / `.env`; log `[i] Соединение с БД установлено` on success or `[!]` and `exit(1)` on failure |
| `run/db/` | `db_check_schema.py` | Recursively read `CREATE TABLE` definitions from `sql/ddl/` and verify all tables and columns exist; log `[i] Схема соответствует` or `[*] Схема не соответствует - рекомендуется выполнить db_init` |
| `run/db/` | `db_init.py` | For non-live/dev databases only (Section 04.02). Check schema: if matching, prompt `Очистить таблицы? 1 - да, 0 - нет` (`TRUNCATE` or SQLite `DELETE FROM` + reset `sqlite_sequence`); if mismatched, prompt `Пересоздать таблицы по схеме? 1 - да, 0 - нет` (`CREATE` missing tables, `DROP + CREATE` mismatched tables). Require explicit confirmation; abort in non-interactive mode |
| `run/db/` | `db_migrate.py` | Read `schema_version`, list pending `sql/migrations/M<N>_*.sql` files in numerical order, apply each in a transaction with its `schema_version` row, and print a summary |
| `run/api/` | `api_check_connection.py` | Call API health/ping or base URL from `config.ini` / `.env`; log `[i] Соединение с API установлено` or `[!]` and `exit(1)` |
| `run/api/` | `api_test_requests.py` | Send configured test requests and log HTTP method, URL, status code, and response excerpt |
| `run/ai/` | `ai_ollama_check.py` | Verify Ollama API reachability and send a test prompt; log prompt, model response, and status or `[!]` and `exit(1)` |
| `run/ai/` | `ai_ollama_pull_models.py` | Pull all models listed in `[ollama] model` (`config.ini`) and run a test prompt against each |
| `run/email/` | `email_test_send.py` | Send a multipart test email via `src/email_sender.py` using `[email]` in `config.ini` and `SMTP_USER`/`SMTP_PASSWORD` in `.env` (defaulting empty `from`/`to` to `SMTP_USER`); log recipient and result or `[!]` and `exit(1)` |

## 05.02. CLI Conventions (`argparse`, `--help` via `t()`, Exit Code 2, and Mutator Item Contract)

- Parse CLI arguments with standard-library `argparse` (external CLI frameworks like `click` or `typer` require explicit justification in `requirements.txt`, `project_standards.md`, Section 01.06).
- Support `--help` on every CLI entry point with help strings localized via `t()` (English default, Russian opt-in; `project_standards.md`, Section 04.01).
- Use long English kebab-case flags (`--output-dir`, `--mode`, `--dry-run`); single-letter short flags are optional aliases and never replace long flags.
- On any unknown flag or invalid argument, print usage/help and exit with code `2` (`project_standards.md`, Section 05.03); never ignore unknown flags silently.
- Read defaults from `config/config.ini` and let explicit CLI flags override config values.
- Support `--dry-run` on all mutating entry points (`project_standards.md`, Section 03.01) and `--mode local|refresh` on data mart pipelines (Section 01.02).
- Support `--porcelain` on scripts whose output is consumed by automation; the human default stays `report` (`cli_output_standards.md`, 04.01).
- **Mutating CLI item status contract:**
  - Distinguish between **unavailable** (`недоступно` - a fixable precondition is missing) and **not applicable** (`неприменимо` - structurally irrelevant to the current environment, omitted from candidates and never treated as an error).
  - When the user explicitly selects an unavailable item, fail immediately with an error and stop. When running in batch mode (`--all`), skip unavailable items with a `[*]` warning and continue.

---

# 06. Cross-References and Versioning

## 06.01. Related Standards

| Document | Relationship |
|----------|--------------|
| `doc/standards/project_standards.md` | Core standard: directory structure (01.01), configuration (01.02), idempotency and `--dry-run` (03.01), dual-language logging and `t()` (04.01, 04.06), exit codes (05.03), testing (06.04) |
| `doc/standards/code_standards.md` | Naming conventions (02.01), SQL formatting (07.04), and static analysis (08) |
| `doc/standards/index_nav_standards.md` | Canonical index skeletons for `sql/_index_sql.md`, `diag/_index_diag.md`, and `test/_index_test.md` |
| `doc/standards/console_ui_standards.md` | Console UI rendering, batch rich-progress, and `spec_ui.html` |

## 06.02. Versioning

Unified package SemVer is governed by `doc/standards/_index_standards.md` and `project_standards.md` (Sections 07.04, 07.05).
