# Deploy Standards. Version 5.0.0

This document defines OS-agnostic rules for installing a Python project as a system CLI tool. It supplements `doc/standards/project_standards.md` and applies on top of it. All core requirements remain in force unless this document explicitly overrides them.

OS specifics (data paths, install flow, shell commands) live in overlay documents:

- `deploy_lin_standards.md` - installation on Linux
- `deploy_win_standards.md` - installation on Windows

Apply this document together with the relevant overlay.

---

## Table of Contents

**01. Prerequisites and build:** 01.01 Mandatory project conditions - 01.02 `pyproject.toml` structure - 01.03 Packaging non-Python files (01.03.01 MANIFEST.in - 01.03.02 package-data in pyproject.toml - 01.03.03 Accessing data files in code - 01.03.04 Rules)

**02. Code and data separation:** 02.01 PROJECT_ROOT swap in config.py - 02.02 Building paths from PROJECT_ROOT

**03. Install scripts:** 03.01 Install scripts - general rules - 03.02 Diagnostic block for AI agents - 03.03 install.py reference - 03.04 update.py reference

**04. Name and version:** 04.01 Application version and config migration on update

**05. Maintenance rules:** 05.01 Entry point - 05.02 Developer mode - 05.03 Uninstall - 05.04 Pre-release checklist

**06. Relations and versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Mandatory project conditions

*Mandatory.*

Before installation the project must meet these requirements:

1. **Root module with an entry point** - a `main()` function in a file (for example `main.py` or `cli.py`). Call it via `if __name__ == "__main__": main()`; no module-level side effects. `main()` must not hold logic directly - parse arguments, initialize configuration, delegate execution (per the core standard).
2. **All imports through packages** - `from src.xxx import <name>`. No `sys.path` hacks, no relative imports outside the package, no dynamically built import paths. The `src` import package is the same in both modes (packaging - 01.02): in development mode code lives in the repository `src/`, in installed mode in `site-packages/src/` of the isolated tool venv.
3. **`__init__.py`** in every directory imported as a package. Empty file, no initialization code.
4. **All dependencies pinned** in `requirements.txt` with exact versions (`==`).

---

## 01.02. pyproject.toml structure

*Mandatory.*

`pyproject.toml` lives in the project root. It is the only build configuration file.

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "tool-name"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "requests==2.32.3",
]

[project.scripts]
tool-name = "main:main"

[tool.setuptools]
packages = ["src"]
py-modules = ["main"]
```

**Section notes:**

- **`[build-system]`** - defines the build tool and its dependencies. An explicit declaration guarantees identical behavior on every machine regardless of the pip/setuptools version.
- **`[project.scripts]`** - creates the CLI command. Format: `command_name = "module:function"`; the module is written as imported after installation: the root orchestrator `main` or a package module `src.xxx`. The wrapper script lands in the user directory after installation. Example: `tool-name = "main:main"` creates the `tool-name` command that calls `main()` from the root `main.py`.
- **`[tool.setuptools]`** - packages the flat structure of the core standard: `packages = ["src"]` packages the whole `src/` directory as the `src` import package, `py-modules = ["main"]` adds the root orchestrator `main.py`. After installation site-packages contains `src/` and `main.py`; imports `from src.xxx import <name>` work unchanged in both modes.
- The distribution name (`name`) does not affect import names: it is package metadata for pip/uv. The import package is `src` both in the repository and in site-packages; the generic name collision is excluded because the tool is installed into an isolated venv (`uv tool install`, 05.02).

**Rules:**

- `pyproject.toml.version` is the package metadata source (pip/uv); the displayed application version is `config.ini [app].version` (04.01). Version sync is the agent's responsibility at commit.
- Distribution name (`name`) - lowercase Latin letters, digits, hyphens only. No underscores; the wheel filename normalizes hyphens to underscores (`tool_name-1.0.0-*.whl`).
- The CLI command name (`[project.scripts]`) matches the distribution name: overlay install scripts use one `TOOL_NAME` for the command, distribution and `uv tool` entry (`deploy_lin_standards.md`, 02.03; `deploy_win_standards.md`, 04.04).
- `requires-python` - the minimum version actually tested with the project.
- Pin **runtime dependency** versions (`[project] dependencies`) with `==`, same as `requirements.txt`. Build dependencies (`[build-system] requires`) use `>=`; the pinning rule does not apply to them.
- Commit a current lockfile `uv.lock`: `uv lock --check` must be clean before release (05.04). Limitation: `uv tool install` builds the tool environment from `pyproject.toml`, the project lockfile does not participate in installation - the lockfile ensures rebuild reproducibility and tree audit, not the installation itself; strict reproducible package deployment uses `uv sync --frozen` from the project (applied in `web_standards.md`).
- `requirements.txt` and `pyproject.toml` must stay synchronized: identical packages and versions in both files. Check before every commit: compare both dependency lists and confirm each `requirements.txt` line has a matching `dependencies` line in `pyproject.toml`.

---

## 01.03. Packaging non-Python files

*Optional - only when the project contains SQL, templates or other non-Python data.*

If the project contains SQL files, templates or other non-Python data, include them explicitly in the distribution. By default setuptools packages only `.py` files.

Recommended approach - runtime assets inside the package: the `[tool.setuptools.package-data]` section includes files in the wheel, plus `MANIFEST.in` controls sdist contents.

### 01.03.01. MANIFEST.in

*Mandatory when packaging non-Python files.*

`MANIFEST.in` lives in the project root next to `pyproject.toml`. It defines which additional files enter the sdist (source distribution). Without it non-Python files are absent from the sdist and installation from it fails.

Example `MANIFEST.in` for a project with SQL files:

```
recursive-include src/sql *.sql
recursive-include config *.example
```

**Directives:**

- `include` - include files by glob pattern relative to the project root
- `recursive-include dir pattern` - recursively include files from a directory
- `exclude` / `recursive-exclude` - exclude files
- `global-include` / `global-exclude` - apply a pattern to the whole tree

Details: https://packaging.python.org/en/latest/guides/using-manifest-in/

### 01.03.02. package-data in pyproject.toml

*Mandatory when packaging non-Python files.*

Runtime assets read by the installed tool (SQL files per `project_standards.md`, 03.02) live inside the `src` import package: `src/sql/`. For deployable projects this placement overrides the root `sql/` folder from `project_standards.md` (01.01): in development mode the package sits in the repository `src/`, in installed mode in site-packages of the isolated venv, and code reads files the same way.

The `[tool.setuptools.package-data]` section includes files inside the package in the wheel (with pyproject.toml configuration `include-package-data = true` is the default):

```toml
[tool.setuptools.package-data]
src = [
    "sql/ddl/*.sql",
    "sql/queries/*.sql",
    "sql/dml/*.sql",
    "sql/_index_sql.md",
]
```

File inclusion condition (setuptools documentation): the file is selected by `package-data` or by `MANIFEST.in` with `include-package-data = true`, and is not excluded by `exclude-package-data`.

Do not use `[tool.setuptools.data-files]` (files outside the package, relative to the install prefix, for example `share/tool-name/`): after wheel installation there is no supported reliable way to obtain such files; the setuptools/PyPA recommendation is runtime data inside the package.

Templates used by overlay install scripts (`config/config.ini.example`, `config/translations.json`) stay in the root `config/` folder: install and update scripts copy them from the repository or archive; they are not wheel runtime assets.

### 01.03.03. Accessing data files in code

*Mandatory when packaging non-Python files.*

Access package assets through `importlib.resources`; the path is identical in development and installed modes:

```python
from importlib.resources import files

sql_content = (
    files("src")
    .joinpath("sql", "ddl", "create_users.sql")
    .read_text(encoding="utf-8")
)
```

Do not build asset paths from `sys.prefix`, `__file__` of neighboring modules or the current working directory.

**Approach:** runtime assets of the installed tool (SQL, DDL, query templates) - inside the package via `package-data` + `MANIFEST.in`; configuration templates - the root `config/` folder, installed by overlay scripts. Do not use `[tool.setuptools.data-files]`.

### 01.03.04. Rules

*Mandatory when packaging non-Python files.*

- Do not package data files needed only in development mode (examples, test data). Package only files required by the installed tool
- Verify data availability after `uv tool install .`: inspect wheel contents with `unzip -l dist/<tool_name>-<version>-*.whl` - files must be inside the package path (`src/sql/`)
- Do not use relative paths with `..` in `package-data` and `importlib.resources` - behavior depends on the setuptools version and archive format
- When adding new data file types, update `MANIFEST.in` and `[tool.setuptools.package-data]` in `pyproject.toml`
- Do not use `[tool.setuptools.data-files]`: files outside the package have no supported reliable retrieval after wheel installation

---

## 02.01. PROJECT_ROOT swap in config.py

*Mandatory.*

After installation code lives in `site-packages/`, while configs, logs and secrets must be user-accessible. The solution is swapping `PROJECT_ROOT` in `src/config.py` by run mode. In both modes the file lives in the `src` import package (`<repo>/src/config.py` or `site-packages/src/config.py`), so `parents[1]` is the root of the respective tree.

The reference `src/config.py` (core standard, 01.04) does not change. When preparing a project for installation, add a mode check and the `PROJECT_ROOT` swap:

- **Development mode** (run from the repository): `PROJECT_ROOT = Path(__file__).resolve().parents[1]` - as in the core standard, unchanged.
- **Installed mode** (`uv tool install`): `PROJECT_ROOT = <OS-CONFIG-ROOT> / "tool-name"`. The root depends on the OS:
  - Linux: `XDG_CONFIG_HOME / "tool-name"` (default `~/.config/tool-name/`) - see `deploy_lin_standards.md`
  - Windows: `APPDATA / "tool-name"` (usually `C:\Users\<user>\AppData\Roaming\tool-name\`) - see `deploy_win_standards.md`

Template: `doc/standards/templates/config.py`. Copy it to `src/config.py` and uncomment the deploy block for the target OS; the template already ships both variants commented out.

**Contract:**

- Exports `PROJECT_ROOT`, `ENV_PATH`, `CONFIG_PATH`, `config`, `APP_NAME`, `APP_VERSION`; `config` is a `ConfigParser` with `inline_comment_prefixes=(";", "#")`
- `ENV_PATH = PROJECT_ROOT / ".env"`; load it with `load_dotenv(ENV_PATH, override=False)` only when it exists
- `CONFIG_PATH = PROJECT_ROOT / "config" / "config.ini"`; read it when it exists
- `APP_NAME` / `APP_VERSION` come from `[app]` with fallbacks (name - empty or tool name, version - `dev`)
- No imports from other project modules, no side effects beyond loading `.env` and `config.ini`

The mode marker is the presence of `.git/` next to `src/`. If the directory exists, this is a repository clone and development mode applies. If not (code runs from `site-packages/` after installation), installed mode applies.

One `.git/` check is enough; do not use `importlib.metadata`:

- Under `uv tool install` code runs from an isolated venv without `.git/` - installed mode.
- When run from the repository (regardless of a system-wide install) `.git/` exists - development mode.
- Under `uv pip install -e .` code runs from the repository, `.git/` is present - development mode.
- In CI/CD from the repository `.git/` exists - development mode, correct for tests.

Replace `tool-name` with the actual tool name. All other `config.py` logic (`.env` loading, `config.ini` reading) stays unchanged - it works with `PROJECT_ROOT`, which already points to the required directory.

---

## 02.02. Building paths from PROJECT_ROOT

*Mandatory.*

Build every path in code from `PROJECT_ROOT` (as in the core standard):

```python
from src.config import PROJECT_ROOT

config_path = PROJECT_ROOT / "config" / "config.ini"
log_dir = PROJECT_ROOT / "log"
env_path = PROJECT_ROOT / ".env"
```

In development mode `PROJECT_ROOT` points to the repository root. In installed mode it points to the user data directory (per OS). Code using `PROJECT_ROOT / "config" / "config.ini"` and `PROJECT_ROOT / "log"` works unchanged in both modes.

**Rules:**

- Do not use `Path.cwd()` or `os.getcwd()` to resolve data paths.
- Do not hardcode absolute paths.
- Use `pathlib.Path` for all path operations.
- On first run in installed mode, create directories with `path.mkdir(parents=True, exist_ok=True)`.

---

## 03.01. Install scripts - general rules

*Mandatory.*

Install scripts live in `run/deploy/`. The script set depends on the platform (see the overlay). General rules for all scripts:

- Each script performs exactly one task, with no command-line arguments or subcommands.
- Scripts do not depend on other project modules - no imports from `src/`, no logger.
- Output goes through `print()` as an exception to the general rule.
- Output lines must not start with bracketed level markers (`[i]`, `[!]`, `[*]`).
- Each script starts with the AI-agent diagnostic block (03.02).

---

## 03.02. Diagnostic block for AI agents

*Mandatory.*

Each script in `run/deploy/` serves a double role: an executable script for the user and a skill for an AI agent. If the user tags the file without explanation (for example `@run/deploy/install.py`), the agent must diagnose the state, perform the required actions and report the result.

The script must start with a comment block containing AI-agent instructions.

**Block structure:**

1. **Activation condition** - when the AI agent must run the check (usually - the user references the file without explanation).
2. **Install state check** - whether the package is installed and whether sources match.
3. **Actions by result** - install, update or report that everything is current.

Concrete block templates (with OS commands) live in the overlays `_lin.md` / `_win.md`.

**Block rules:**

- The file list for `diff` / `fc` checks must include all key project modules - `main.py`, `src/config.py`, `src/logger.py` and every file from `src/` and `run/` that affects tool behavior.
- Put commands on separate lines - the agent (and the user) must be able to copy them verbatim.
- Replace `tool-name` with the actual tool name.
- Do not include script logic in the block - only check instructions.
- The agent decides independently, without asking the user about next steps.
- Windows specifics: mark commands explicitly - the agent has no direct access to the Windows machine, the user runs these commands.

---

## 03.03. install.py reference

*Mandatory.*

Reference source - `doc/standards/templates/install.py`; copy it to `run/deploy/install.py`. Platform differences are limited to constants (`APP_DIR`, shell hints, command directory, install source) and, in the Windows archive scenario, verification of `pyproject.toml` (absent from the archive - replaced by a wheel check); the procedure order and code are otherwise shared by Linux and Windows. The overlay sets the constants and steps (`_lin.md` / `_win.md`, platform substitution table; Windows archive scenario - `_win.md`, 04.04, 05.01). The script is isolated (03.01) and prints through `print(message, flush=True)`.

**Contract:**

- **Placeholders** - `TOOL_NAME`, `<OS_CONFIG_ENV>`, `<OS_CONFIG_DEFAULT>`, `<UV_INSTALL_HINT>`, `<PATH_HINT>`; `PROJECT_ROOT = Path(__file__).resolve().parents[2]`; `APP_DIR` per the overlay table
- **Input** - repository root with `pyproject.toml` (direct deploy) or unpacked archive with the wheel (Windows scenario); `uv` on `PATH`; no CLI arguments
- **Behavior** - check `pyproject.toml` (or the wheel in the archive) and `uv`; if `uv tool list` already shows `TOOL_NAME` in the first column, print the update hint and return; otherwise run `uv tool install .` in `PROJECT_ROOT` (Windows archive: `uv tool install <wheel>`); create `APP_DIR` with `config/` and `log/`; copy `config.ini.example` to `config.ini` and `.env.example` to `.env` only when the target is missing; set `.env` mode `0600`; always copy `translations.json` from the install source; report the command path or the PATH hint
- **Exit codes** - `0` success or already installed; `1` missing `uv`/`pyproject.toml` or failed `uv tool install`
- **Output** - `print(message, flush=True)`; no imports from `src/`, no logger

The template ships helpers `_check_uv`, `_check_pyproject`, `_is_tool_installed`, `_ensure_data_dirs`, `_copy_if_missing`, `_copy_translations` and `main`; preserve their behavior when adapting.

---

## 03.04. update.py reference

*Mandatory.*

Reference source - `doc/standards/templates/update.py`; copy it to `run/deploy/update.py`. Platform differences are limited to constants (`APP_DIR`, shell hints, command directory, template source, install source) and, in the Windows archive scenario, skipped repository-bound steps (stage 0 and the `pyproject.toml` check); the procedure order and code are otherwise shared by Linux and Windows. The overlay sets the constants and steps (`_lin.md` / `_win.md`, platform substitution table; Windows archive scenario - `_win.md`, 04.04, 05.05). The script is isolated (03.01) and prints through `print(message, flush=True)`.

**Update order:**

1. Check `pyproject.toml` and `uv`.
2. Check that the package is installed. If not, report and exit (install with `run/deploy/install.py`).
3. Create the dev config `config/config.ini` from `config.ini.example` when absent, substituting `name`/`version` from `pyproject.toml` (canon - 04.01, stage 0).
4. Sync the version across `pyproject.toml`, `config/config.ini` and `config/config.ini.example` by SemVer - raise all three to the maximum value (canon - 04.01, stage 0). Non-numeric versions (`dev` and similar) - skip with a message.
5. Clean the cache: `uv cache clean tool-name`. Without this, with an unchanged `pyproject.toml` version, `uv tool install . --force` installs the cached wheel instead of rebuilding from current sources - code changes never reach the installed package.
6. Reinstall: `uv tool install . --force`.
7. Update `translations.json` in the data directory (always copy from the install source).
8. Migrate prod `config.ini` and prod `.env` by the algorithm in 04.01 (structure comparison, backups, value transfer).
9. Verify the installation briefly (`uv tool list`, command on `PATH`) and report the result.

**Contract:**

- **Input** - repository root with `pyproject.toml` (direct deploy) or unpacked archive without it (Windows scenario), `uv` on `PATH`; no CLI arguments
- **Behavior** - helpers `_pyproject_meta`, `_ensure_dev_config`, `_sync_version`, `_migrate_config`, `_migrate_env`, `_verify_install`; config migration uses `_ini_structure`, `_rebuild_ini`, `_backup`, `_atomic_write`; env migration uses `_env_keys`, `_rebuild_env`
- **Safety** - atomic writes (temp file + `replace`); backups named `<file>.bak_YYYY-MM-DD_HH-MM` (seconds suffix on collision) are never deleted by the script; `.env` mode `0600` after every write; secrets are never printed
- **Exit codes** - `0` success or package absent (with install hint); `1` missing `uv`/`pyproject.toml`, failed reinstall or failed post-install verification
- **Output** - `print(message, flush=True)`; report synced version, backup names, added keys and old-only key names (never values)

New `config.ini` and `.env` are assembled from the example text with substituted values (section order, key order and template comments are preserved); `ConfigParser.write()` is not the sole write method.

---

## 04.01. Application version and config migration on update

*Mandatory.*

The application name and version shown to the user (logs, console) live in `config/config.ini`, section `[app]` (`name` and `version`). This is the single source for all modes - development and installed.

The version in `pyproject.toml` (`version`) is package metadata (pip/uv) only and is not displayed. Version sync between `pyproject.toml` and `config.ini` is the agent's responsibility; the agent offers to update both at commit (core standard, 01.03).

```python
from src.config import APP_NAME, APP_VERSION
```

The install script `update.py` runs a single migration algorithm on update. **This section is the algorithm canon**; overlay documents (`deploy_lin_standards.md`, 03.05; `deploy_win_standards.md`, 05.05) contain only platform paths, template sources and commands.

**Stage 0 - version sync in the repository (direct repository deploy only).** Compare versions in `config/config.ini` (`version` in `[app]`), `pyproject.toml` (`version`) and `config/config.ini.example` by SemVer; write the maximum value to all three files. Non-numeric versions (`dev` and similar) - skip with a message. The migration algorithm starts from the dev config `config/config.ini`. If it is absent, create it from `config/config.ini.example` with `name`/`version` from `pyproject.toml`. Archive deployment skips this stage: the version is fixed in the wheel on the build machine.

**Stage 1 - prod `config.ini` migration.** The source of the new structure is `config.ini.example`.

Compare section and key sets only (user values do not affect the migration decision).

If structures match:
- update only `app.name` and `app.version` from the source when they differ, without renaming

If structures differ:
1. Rename the current file to `config.ini.bak_YYYY-MM-DD_HH-MM` (history accumulates; on name collision add a seconds suffix)
2. Create a new `config.ini` from the example text (section/key order and template comments preserved)
3. Substitute old file values for matching keys
4. For new keys (present in example, absent in old) - take the example value
5. `app.name` and `app.version` always come from the source, never from the old file
6. Keys present only in the old config and absent from the example - do not migrate (they remain in `.bak`)
7. Print to console: backup name, transferred keys and added keys (no secrets)

If the prod config does not exist yet, create it by copying the example (`name`/`version` from the example).

**Stage 2 - prod `.env` migration.** The source of the new structure is `.env.example`.

Compare key sets only (values/secrets are neither compared nor printed).

If key sets match - leave the file untouched.

If they differ:
1. Rename the current file to `.env.bak_YYYY-MM-DD_HH-MM`
2. Create a new `.env` from the example keys
3. Transfer old values for matching keys
4. For new keys - take the example value (often empty)
5. Keys present only in the old `.env` - do not migrate (they remain in `.bak`); report the list of key names without values

If the prod `.env` does not exist yet - copy the example.

**Stage 3 - `translations.json`.** Always update by copying from the install source.

**Rules:**

- Preserve user values of matching keys during migration; the new structure always comes from the example
- The script never deletes backups
- Write the new file from the example template with value substitution, not with a bare `ConfigParser.write()` as the sole assembly method
- Write critical files (`config.ini`, `.env`) atomically: temporary file, then `rename` over the target (`project_standards.md`, 03.01) - an interrupted write leaves no corrupted file
- Compare key sets only: a renamed key leaves the old one in `.bak` and takes the new one from the example; comment-only example changes do not trigger migration

---

## 05.01. Entry point

*Mandatory.*

The `main()` function must not hold logic directly. Its job is to parse arguments, initialize configuration and delegate execution:

```python
import logging
from pathlib import Path

from src.config import PROJECT_ROOT, APP_NAME, APP_VERSION
from src.localization import t
from src.logger import console_message, get_logger


def main() -> None:
    logger = get_logger(Path(__file__).stem, log_dir=PROJECT_ROOT / "log")
    logger.info("Started %s v%s", APP_NAME, APP_VERSION)
    console_message(
        logging.INFO,
        t("msg.app_started", name=APP_NAME, version=APP_VERSION),
    )
    args = parse_args()
    init_config()
    run(args)


if __name__ == "__main__":
    main()
```

---

## 05.02. Developer mode

*Optional - for debugging without installation.*

For debugging without installation use `uv` in editable mode. An active venv is required. The venv activation command depends on the OS (see the overlay):

```bash
# activate the venv (Linux: source .venv/bin/activate; Windows: .venv\Scripts\activate)
uv pip install -e .
```

This installs the package in editable mode - code changes apply immediately without reinstall. Code runs from the repository (`.git/` present), so `PROJECT_ROOT` points to the repository root (development mode).

**Difference between `uv` modes:**

- `uv tool install .` - isolated CLI command installation for daily use. The package goes into a separate venv, the command is globally available.
- `uv pip install -e .` - installation into the current venv for development. Requires an activated venv; code changes apply immediately.

---

## 05.03. Uninstall

*Optional.*

```bash
uv tool uninstall tool-name
```

The user data directory is not touched when the package is removed - the user deletes it manually if needed. The exact data path depends on the OS (see the overlay).

---

## 05.04. Pre-release checklist

*Mandatory.*

Common items (OS-specific items are in the overlay for the target OS):

1. All dependencies are listed in `pyproject.toml` with exact versions (`==`).
2. `requirements.txt` and `pyproject.toml` are synchronized (identical packages and versions).
3. The version in `pyproject.toml` is updated.
4. The `[app]` section in `config.ini` contains correct `name` and `version`.
5. `__init__.py` exists in every imported package.
6. The `PROJECT_ROOT` swap in `config.py` uses the correct tool name.
7. Install scripts use the correct tool name (`TOOL_NAME`).
8. `.gitignore` contains build artifacts (`*.egg-info/`, `dist/`, `build/`).
9. Data files (SQL, templates) are available after installation.
10. The lockfile is current: `uv lock --check` runs clean.

---

## 06.01. Related documents

| Document | Relation |
|----------|----------|
| `doc/standards/project_standards.md` | Core standard; this document applies on top of it (project structure, configuration, code) |
| `deploy_lin_standards.md` / `deploy_win_standards.md` | OS overlays: platform paths, install scripts and commands; applied together with this core |
| `deploy_docker_standards.md` | Adjacent standard: Docker infrastructure (network, volumes, port publication); applies to container deployment instead of this core |
| `web_standards.md` | Adjacent standard: web applications (FastAPI + nginx); this core does not apply to web applications (boundary - `web_standards.md`, 12.02) |
| `doc/standards/_index_standards.md` | Standards package registry and routing map |

---

## 06.02. Versioning

Standards package versioning is unified for all package documents. The versioning policy, registry and routing map live in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see _index_standards.md).
