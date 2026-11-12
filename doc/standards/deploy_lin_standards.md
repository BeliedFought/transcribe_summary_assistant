# Linux Deploy Standards. Version 5.2.0

OS overlay for Variant A of `deploy_standards.md` (shared core): installing a Python project as a system CLI tool. Apply it together with the core and `project_standards.md`. This document contains Linux specifics only; general deploy rules live in the core, and the solution runtime (Variant B, section 07) needs no overlay.

Installation runs directly on the target Linux machine: `uv tool install .` from the repository root. The agent has full access to the repository and the target machine.

---

## Table of Contents

**01. Flow and paths:** 01.01 Install flow - 01.02 PROJECT_ROOT in installed mode

**02. Install scripts:** 02.01 run/deploy scripts - 02.02 Diagnostic block for AI agents - 02.03 Platform substitutions for scripts

**03. Platform:** 03.01 uv - 03.02 Shell completion - 03.03 .gitignore additions - 03.04 Final structure after installation - 03.05 Version, config and .env sync on update - 03.06 OS-specific checklist (Linux)

**04. Relations and versioning:** 04.01 Related documents - 04.02 Versioning

---

## 01.01. Install flow

*Mandatory.*

Installation runs on the target Linux machine from the repository root:

```bash
uv tool install .
```

The `--force` flag applies only on update (reference - `deploy_standards.md`, 03.04). `uv` builds the wheel automatically from `pyproject.toml`.

---

## 01.02. PROJECT_ROOT in installed mode

*Mandatory.*

In installed mode `PROJECT_ROOT` points to the XDG user data directory: `XDG_CONFIG_HOME / "tool-name"` (default `~/.config/tool-name/`).

Template: `doc/standards/templates/config.py`. Copy it to `src/config.py` and uncomment the Linux deploy block.

**Contract:**

- Development mode: `PROJECT_ROOT = Path(__file__).resolve().parents[1]` when `.git/` exists next to `src/`
- Installed mode: `Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "tool-name"`; keep `expanduser()` for the default only - a custom `XDG_CONFIG_HOME` is already absolute
- The rest of the template (`ENV_PATH`, `CONFIG_PATH`, `config`, `APP_NAME`, `APP_VERSION`) stays unchanged

Replace `tool-name` with the actual tool name.

---

## 02.01. run/deploy scripts

*Mandatory.*

| Script | Purpose |
|--------|---------|
| `run/deploy/install.py` | First-time tool installation |
| `run/deploy/update.py` | Update of the installed tool |

---

## 02.02. Diagnostic block for AI agents

*Mandatory.*

Each script starts with a comment block of instructions (rules - `deploy_standards.md`, 03.02).

**Block template for install.py** (replace `tool-name` with the tool name and `package-name` with the package name from `pyproject.toml`):

```python
#!/usr/bin/env python3
# AI agent:
# If the user references @install.py without further explanation -
# run diagnostics and installation independently:
#
# 1. Verify the run is from the repository (pyproject.toml and .git/ are present).
#    Verify pyproject.toml contains [build-system] and dependency versions pinned with ==.
#
# 2. Check install state:
# uv tool list (tool-name present in the output)
#
# 3. If the package is not installed:
# python run/deploy/install.py
# After installation report the command path and configuration location.
#
# 4. If the package is installed:
# - Report: the package is already installed, command path.
# - Offer an update via @run/deploy/update.py
```

**Block template for update.py** (replace `tool-name` and the file list):

```python
#!/usr/bin/env python3
# AI agent:
# If the user references @update.py without further explanation -
# run diagnostics and update independently:
#
# 1. Verify the run is from the repository (pyproject.toml and .git/ are present).
#
# 2. Check install state:
# uv tool list (tool-name present in the output)
#
# 3. If the package is not installed:
# - Report: the package is not installed.
# - Offer installation via @run/deploy/install.py
#
# 4. If the package is installed - compare sources in the uv venv with the repository:
# diff <file> ~/.local/share/uv/tools/tool-name/lib/python*/site-packages/<file>
#
# Check at minimum: main.py, src/config.py, src/logger.py and all key
# modules from src/ and run/
#
# 5. If sources differ:
# python run/deploy/update.py
# After the update report the synchronized parameters
# and whether config.ini / .env migration occurred.
#
# 6. If sources match:
# - Report: the package is installed and current, no action required
#
# Config/.env migration when the structure differs from the example - algorithm: `deploy_standards.md` (04.01)
```

---

## 02.03. Platform substitutions for scripts

*Mandatory.*

Reference code - `deploy_standards.md`, 03.03 and 03.04; this section defines platform values only. `run/deploy/install.py` and `run/deploy/update.py` use the shared core code; below are Linux constant and step values.

| Constant / step | Linux value |
|-----------------|-------------|
| `APP_DIR` | `$XDG_CONFIG_HOME/tool-name` (default `~/.config/tool-name`) |
| Command path | `~/.local/bin/tool-name` |
| uv venv directory | `~/.local/share/uv/tools/tool-name` |
| `.env` mode | `0600` |
| PATH hint | `~/.local/bin` |
| `uv` install hint | `sudo pacman -S uv` (Arch) or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

In the core code these values substitute the constants `APP_DIR`, `PATH_HINT`, `UV_INSTALL_HINT` and the command name `TOOL_NAME`. Replace `tool-name` with the actual tool name.

---

## 03.01. uv

*Mandatory.*

`uv` is the only installation tool. It installs the package into an isolated venv without touching the system. `uv tool install .` uses `pyproject.toml` in the project root.

**Installing uv:**

Arch Linux:

```bash
sudo pacman -S uv
```

Other distributions (official uv installer):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install scripts check for `uv` before starting and exit with an installation message when `uv` is missing.

---

## 03.02. Shell completion

*Optional - for CLIs with many commands and arguments.*

For CLI tools with many commands and arguments, add shell completion generation. With `argparse`, generate completions through the `argcomplete` package (required Python version - per the package documentation). Registration example:

```bash
eval "$(register-python-argcomplete tool-name)"
```

For bash add this to `~/.bashrc`. Document it in the project README.

---

## 03.03. .gitignore additions

*Mandatory.*

When preparing the project for deploy, add to `.gitignore`:

```
*.egg-info/
dist/
build/
```

These are build artifacts created by setuptools during installation. They must not enter the repository.

---

## 03.04. Final structure after installation

```
Code:        ~/.local/share/uv/tools/tool-name/lib/python*/site-packages/ (src/ import package and main.py module)
Command:     ~/.local/bin/tool-name
Config:      ~/.config/tool-name/config/config.ini
Secrets:     ~/.config/tool-name/.env
Logs:        ~/.config/tool-name/log/
```

The source repository becomes independent of the installed tool - it can be deleted, overwritten or cloned again.

---

## 03.05. Version, config and .env sync on update

*Mandatory.*

The migration algorithm canon (structure comparison, backups, value transfer, rules) - core `deploy_standards.md`, 04.01; here only Linux platform specifics:

- Script - `run/deploy/update.py` (reference code - `deploy_standards.md`, 03.04; substitutions - 02.03)
- **Stage 0 - version sync in the repository (before installation):** runs before `uv tool install --force`; algorithm - core canon (`deploy_standards.md`, 04.01)
- Example structure source - the repository (installation runs from its root)
- Prod files - `XDG_CONFIG_HOME/tool-name/` (default `~/.config/tool-name/`): `config/config.ini`, `.env`
- Backups and rewriting - core canon (`deploy_standards.md`, 04.01)

---

## 03.06. OS-specific checklist (Linux)

*Mandatory.*

Add to the common checklist (core - `deploy_standards.md`, 05.04):

1. Install scripts (`run/deploy/install.py`, `run/deploy/update.py`) use the correct `TOOL_NAME`.
2. `.gitignore` contains `*.egg-info/`, `dist/`, `build/`.
3. A test installation and run on a clean machine succeeded.
4. The `PROJECT_ROOT` swap uses the correct tool name and the XDG path.

---

## 04.01. Related documents

| Document | Relation |
|----------|----------|
| `deploy_standards.md` | Shared deploy core; this document is an OS overlay applied together with it |
| `deploy_win_standards.md` | Paired OS overlay for Windows (same script structure, platform specifics) |
| `doc/standards/project_standards.md` | Core standard |

---

## 04.02. Versioning

Standards package versioning is unified for all package documents. The versioning policy, registry and routing map live in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see _index_standards.md).
