# Windows Deploy Standards. Version 5.0.1

OS overlay for `deploy_standards.md` (shared core). Apply it together with the core and `project_standards.md` to install a project as a system tool on Windows. This document contains Windows specifics only; general deploy rules live in the core.

The document applies to Windows 10/11 and Windows Server 2016+. The Windows version does not matter - every mechanism used (PowerShell 5.1+, pathlib, uv) behaves identically.

**Key difference from Linux deploy:** the base mode of this standard has no direct agent access to the Windows machine (the agent prepares commands and an archive, the user runs commands on the machine). A separate scenario - the agent works on a Windows host directly in a PowerShell session: the canon of that mode is `deploy_hyperv_standards.md`; the norms of both documents apply each in its own access mode. Installation has two phases:

1. **Preparation on Linux (agent machine)** - build the wheel, create the installation ZIP archive with instructions, template configs and the install script. Performed by the agent with full repository access.
2. **Installation on Windows (target machine)** - the user (and administrator) unpack the archive and follow the instructions. The agent's role is only to prepare the package, automate installation as far as possible and supply clear instructions.

Goal: perform as many preparatory actions as possible on the Linux machine so the Windows side needs minimal manual steps.

---

## Table of Contents

**01. Windows environment:** 01.01 Responsibility split - 01.02 Administrator request (01.02.01 Optional: UTF-8 encoding) - 01.03 User actions - 01.04 Environment readiness check - 01.05 UTF-8 encoding

**02. Flow and paths:** 02.01 Install flow - 02.02 PROJECT_ROOT in installed mode

**03. Package preparation on Linux:** 03.01 Wheel build - 03.02 Archive structure - 03.03 README.txt content - 03.04 Archive creation

**04. Install scripts:** 04.01 run/deploy scripts - 04.02 Diagnostic block for AI agents - 04.03 package.py - 04.04 Platform substitutions for scripts - 04.05 package.py logic - archive build (Linux)

**05. Platform:** 05.01 uv - 05.02 Shell completion - 05.03 .gitignore additions - 05.04 Final structure after installation - 05.05 Version, config and .env sync on update - 05.06 OS-specific checklist (Windows)

**06. Relations and versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Responsibility split

*Mandatory.*

Instructions from this section are included in the archive as `README.txt` (see 03.03). The user and administrator run them on the target Windows machine.

A user without administrative rights can install and use the tool entirely independently. The administrator is needed only to install base software on the machine.

| Component | Installed by | Why |
|-----------|--------------|-----|
| Python 3.12+ (minimum tested project version - core standard 01.07) | Administrator | System package, requires writing to Program Files and PATH |
| uv | User | Installs into the user profile, no admin needed |
| Encoding UTF-8 | Administrator (optional) | Registry change for system encoding |
| Project (tool-name) | User | Installed from the archive via `python install.py` |

Total: the user contacts the administrator once - to install Python on the machine. Everything else the user does from the installation archive.

---

## 01.02. Administrator request

*Mandatory when Python is absent from the machine.*

The user sends the administrator the following text unchanged (replace `TOOL-NAME` with the project name):

---

> **Тема: Запрос на установку ПО для работы с Python-проектом**
>
> Для работы нужен Python-проект (TOOL-NAME). Сам проект я установлю самостоятельно.
> Прошу установить на мою машину один компонент:
>
> **1. Python 3.12 или новее (минимальная тестированная версия проекта)**
>
> Скачать: https://www.python.org/downloads/
>
> При установке обязательно отметить галочку **"Add Python to PATH"**.
>
> Или из командной строки (тихая установка для всех пользователей):
> ```powershell
> $pyVer = "3.12.0"  # заменить на актуальный патч выбранной минимальной версии перед отправкой
> Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$pyVer/python-$pyVer-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"
> Start-Process -Wait -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1"
> Remove-Item "$env:TEMP\python-installer.exe"
> ```
>
> **После установки прошу подтвердить**, что команда работает:
> ```powershell
> python --version
> ```
> Команда должна вывести версию без ошибок.
>
> Больше ничего устанавливать не нужно - остальное я сделаю сам.

---

### 01.02.01. Optional: UTF-8 encoding

*Optional.*

If programs print `??????` or mojibake instead of Cyrillic, ask the administrator to enable UTF-8 system-wide (add to the request from 01.02). On Windows 10/11 use the standard "Use Unicode UTF-8 for worldwide language support" option in regional settings (`intl.cpl`); it requires a reboot. The registry change below is the equivalent for Windows Server and automation scenarios:

> **Опционально: кодировка UTF-8**
>
> Включить UTF-8 системно:
> ```powershell
> Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage" -Name "OEMCP" -Value "65001"
> Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage" -Name "ACP" -Value "65001"
> ```
> После применения перезагрузить машину.

---

## 01.03. User actions

*Mandatory.*

After administrator confirmation the user installs `uv`:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Alternatives (if the PowerShell script fails):

- **pip**: `pip install uv` (when Python is installed and available)
- **winget**: `winget install astral-sh.uv` (Windows 10+, does not work on Server)

Verify:

```powershell
uv --version
```

If the command is not found, restart the shell. `uv` installs into the user profile (`%USERPROFILE%\.local\bin\` or `%USERPROFILE%\.cargo\bin\`); administrative rights are not required.

---

## 01.04. Environment readiness check

*Mandatory.*

The user runs:

```powershell
python --version
uv --version
```

Both commands must return a version without errors. The project can now be installed: unpack the archive and run `python install.py`.

---

## 01.05. UTF-8 encoding

*Mandatory.*

For correct Cyrillic in logs and output:

- **Windows Terminal** - UTF-8 is native, no extra action needed
- **PowerShell** - PowerShell 7+ is UTF-8 by default. In PowerShell 5.1, when needed:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
  ```
- **cmd** - run `chcp 65001` to switch to UTF-8

Prefer Windows Terminal as the primary shell - UTF-8 works there without extra configuration.

---

## 02.01. Install flow

*Mandatory.*

Windows installation is two-phase (see the introduction). On the Linux machine the agent builds the wheel and packs the installation ZIP archive (`python run/deploy/package.py`). On the Windows machine the user unpacks the archive and runs `python install.py` (or `python update.py` to update). Installation from wheel: `uv tool install <wheel>`.

---

## 02.02. PROJECT_ROOT in installed mode

*Mandatory.*

In installed mode `PROJECT_ROOT` points to the user data directory: `APPDATA / "tool-name"` (usually `C:\Users\<user>\AppData\Roaming\tool-name\`).

Template: `doc/standards/templates/config.py`. Copy it to `src/config.py` and uncomment the Windows deploy block.

**Contract:**

- Development mode: `PROJECT_ROOT = Path(__file__).resolve().parents[1]` when `.git/` exists next to `src/`
- Installed mode: `Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "tool-name"`
- The rest of the template (`ENV_PATH`, `CONFIG_PATH`, `config`, `APP_NAME`, `APP_VERSION`) stays unchanged

Replace `tool-name` with the actual tool name.

---

## 03.01. Wheel build

*Mandatory.*

From the repository root (on the Linux machine):

```bash
uv build
```

The command creates a wheel file in `dist/` (for example `dist/tool_name-1.0.0-py3-none-any.whl`). The wheel contains all project code and metadata from `pyproject.toml`.

---

## 03.02. Archive structure

*Mandatory.*

The archive is named `tool-name-1.0.0-install.zip`. Inside is a directory with a flat structure:

```
tool-name-1.0.0-install/
├── install.py               # Installation (reference - deploy_standards.md, 03.03)
├── update.py                # Update (reference - deploy_standards.md, 03.04)
├── dist/
│   └── tool_name-1.0.0-py3-none-any.whl
├── config/
│   ├── config.ini.example
│   └── translations.json
├── .env.example
└── README.txt               # Instructions (section 1)
```

| File | Repository source | Purpose |
|------|-------------------|---------|
| `install.py` | `run/deploy/install.py` | Installation from archive (Windows) |
| `update.py` | `run/deploy/update.py` | Update from archive (Windows) |
| `dist/*.whl` | Built by `uv build` | Ready package |
| `config/config.ini.example` | `config/config.ini.example` | Configuration template |
| `config/translations.json` | `config/translations.json` | Localization (copied to prod on install/update) |
| `.env.example` | `.env.example` | Secrets template |
| `README.txt` | Generated by the script | Instructions for administrator and user |

---

## 03.03. README.txt content

*Mandatory.*

`README.txt` is generated by `package.py` during archive build. It contains:

1. **Administrator request** - text from 01.02 (Python installation, optional UTF-8)
2. **User actions** - uv installation (01.03), archive unpacking, `python install.py`
3. **Installation check** - `tool-name --help`

The README text is generated from a template in the `package.py` code. This guarantees the instructions always match the current project version.

---

## 03.04. Archive creation

*Mandatory.*

Build the archive from the repository root:

```bash
python run/deploy/package.py
```

The script:

1. Checks for `pyproject.toml` and `uv`
2. Runs `uv build` to build the wheel
3. Creates a temporary directory with the archive contents
4. Copies: the wheel from `dist/`, `config/config.ini.example`, `config/translations.json`, `.env.example`, `install.py`, `update.py`
5. Generates `README.txt` from the template (substituting project name and version)
6. Packs the ZIP archive: `tool-name-1.0.0-install.zip`
7. Computes the archive SHA256 and writes a `<archive>.sha256` file next to it; prints the value to the console (integrity check on Windows: `certutil -hashfile <archive> SHA256`)
8. Places the archive in the project root

The archive is ready for transfer to the Windows machine. The source repository is not needed on Windows.

---

## 04.01. run/deploy scripts

*Mandatory.*

| Script | Runs on | Purpose |
|--------|---------|---------|
| `run/deploy/package.py` | Linux (from the repository) | Build the wheel and create the ZIP archive |
| `run/deploy/install.py` | Windows (from the archive) | First installation from the wheel |
| `run/deploy/update.py` | Windows (from the archive) | Update from a new wheel |

Each script performs exactly one task, with no command-line arguments or subcommands. `install.py` and `update.py` are copied into the archive root unchanged.

---

## 04.02. Diagnostic block for AI agents

*Mandatory.*

Each script starts with a comment block of instructions (rules - `deploy_standards.md`, 03.02).

**Block template for package.py** (replace `tool-name`):

```python
#!/usr/bin/env python3
# AI agent:
# If the user references @package.py without further explanation -
# prepare the Windows installation ZIP archive:
#
# 1. Verify the run is from the repository (pyproject.toml and .git/ are present).
#    Verify pyproject.toml contains [build-system] and dependency versions pinned with ==.
#
# 2. Build the archive:
# python run/deploy/package.py
#
# 3. Report the path to the created ZIP archive.
#    Transfer the archive to the Windows machine by any means (USB drive, network, email).
```

**Block template for install.py** (replace `tool-name` and the file list; the agent has no direct Windows access):

```python
#!/usr/bin/env python3
# AI agent:
# If the user references @install.py without further explanation:
#
# 1. If run from the Linux repository (pyproject.toml and .git/ are present):
#    - Check install state on Linux: uv tool list (tool-name present in the output)
#    - If not installed: python run/deploy/install.py
#    - If installed: report and offer @run/deploy/update.py
#
# 2. If the user reports problems on the Windows machine:
#    Check whether the package is installed (on Windows, the user runs):
# where.exe tool-name
#
# 3. If the package is not installed on Windows:
#    - Rebuild the archive: python run/deploy/package.py
#    - Transfer the archive to Windows; the user unpacks it and runs:
# python install.py
#
# 4. If the package is installed and sources match:
#    - Report: the package is installed and current
```

**Block template for update.py** (replace `tool-name` and the file list):

```python
#!/usr/bin/env python3
# AI agent:
# If the user references @update.py without further explanation:
#
# 1. If run from the Linux repository (pyproject.toml and .git/ are present):
#    - Verify the package is installed: uv tool list (tool-name present in the output)
#    - If not installed: report and offer @run/deploy/install.py
#    - Compare sources in the uv venv with the repository:
#      diff <file> ~/.local/share/uv/tools/tool-name/lib/python*/site-packages/<file>
#      Check at minimum: main.py, src/config.py, src/logger.py and all
#      key modules from src/ and run/
#    - If they differ: python run/deploy/update.py
#    - If they match: report that everything is current
#
# 2. If the user reports problems on the Windows machine:
#    Compare sources in the uv venv with the repository (the user runs this).
#    The site-packages directory in the tool venv; the Windows venv has no
#    pythonX.Y level, unlike Linux:
# $(uv tool dir)\tool-name\Lib\site-packages
#    Then compare files by exact path:
# fc <file> "$(uv tool dir)\tool-name\Lib\site-packages\<file>"
#    Check at minimum: main.py, src/config.py, src/logger.py and all
#    key modules from src/ and run/
#
# 3. If sources differ:
#    - Rebuild the archive: python run/deploy/package.py
#    - Transfer the archive to Windows; the user unpacks it and runs:
# python update.py
#    After the update report name/version synchronization
#    and whether config.ini / .env migration occurred.
#
# 4. If the package is installed and sources match:
#    - Report: the package is installed and current
#
# Config/.env migration when the structure differs from the archive example -
# algorithm: `deploy_standards.md` (04.01)
```

---

## 04.03. package.py

*Mandatory.*

File `run/deploy/package.py`. Runs on Linux from the repository. The diagnostic block from 04.02 goes at the top of the file.

**Contract:**

- Input: project repository (`pyproject.toml` in the root), installed `uv`
- Output: archive `<tool-name>-<version>-install.zip` in the repository root (structure - 03.02); the archive path is printed to the console
- Exit codes: 0 - archive created; 1 - `uv` or `pyproject.toml` missing, `uv build` failed
- The script is isolated (`deploy_standards.md`, 03.01): no imports from `src/`, output through `print()`
- Constants: `TOOL_NAME`, `TOOL_VERSION` (synchronized with the project), `REPO_ROOT = Path(__file__).resolve().parents[2]`

**Pseudocode:**

```
main():
    check pyproject.toml and uv (otherwise print a message and exit 1)
    uv build                                  # wheel into dist/
    create temporary directory <tool>-<version>-install/
    copy: install.py, update.py, dist/*.whl,
          config/config.ini.example, config/translations.json, .env.example
    generate README.txt                       # text - 01.02, 01.03, 03.03
    pack into zip (all files, paths relative to the repository root)
    remove the temporary directory
    print the archive path
```

Step-by-step logic - 04.05. `README.txt` content: administrator request (01.02, verbatim), uv installation and launch (01.03, 03.03), with project name and version substituted.

---

## 04.04. Platform substitutions for scripts

*Mandatory.*

Reference code - `deploy_standards.md`, 03.03 and 03.04; this section defines platform values only. `install.py` and `update.py` in the archive root use the shared core code; below are Windows constant and step values. The template source (`config/config.ini.example`, `.env.example`, `config/translations.json`) is the unpacked archive directory, not the repository.

| Constant / step | Windows value |
|-----------------|---------------|
| `PROJECT_ROOT` | `SCRIPT_DIR` (archive root, instead of the repository `parents[2]`) |
| `APP_DIR` | `%APPDATA%\tool-name` |
| Installation | `uv tool install <wheel>` from the archive `dist/` |
| Command path | `uv` shim in `%USERPROFILE%\.local\bin` |
| uv venv directory | `$(uv tool dir)\tool-name` |
| `.env` mode | `0600` |
| PATH hint | restart PowerShell |
| `uv` install hint | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

Run scripts as `python install.py` (first installation) and `python update.py` (update) from the unpacked archive root. The repository version sync stage (04.01, stage 0) is absent: the archive is built on Linux, the package version is fixed in the wheel.

---

## 04.05. package.py logic - archive build (Linux)

*Mandatory.*

1. Check for `pyproject.toml` and `uv`.
2. Run `uv build` - build the wheel into `dist/`.
3. Create a temporary directory `tool-name-1.0.0-install/`.
4. Copy into it: `install.py`, `update.py`, the wheel from `dist/`, `config/config.ini.example`, `config/translations.json`, `.env.example`.
5. Generate `README.txt` with instructions (text from section 1).
6. Pack into the ZIP archive `tool-name-1.0.0-install.zip`.
7. Remove the temporary directory.
8. Place the archive in the repository root.

## 05.01. uv

*Mandatory.*

`uv` is the only installation tool. On Linux it builds the wheel (`uv build`). On Windows it installs from the wheel file: `uv tool install <wheel>`. The `--force` flag applies only on update.

**Installing uv on Windows:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Install scripts check for `uv` before starting and exit with an installation message when `uv` is missing.

---

## 05.02. Shell completion

*Optional - for CLIs with many commands and arguments.*

**PowerShell** - argparse tool completion is not canonicalized: argcomplete does not support PowerShell natively. `Register-ArgumentCompleter` applies only on explicit user request and with real completion logic; a stub registration without logic is not produced.

**cmd** - completion via `argcomplete` is not supported natively.

---

## 05.03. .gitignore additions

*Mandatory.*

When preparing the project for deploy, add to `.gitignore`:

```
*.egg-info/
dist/
build/
*-install.zip
```

Build artifacts (setuptools) and ready installation archives must not enter the repository.

---

## 05.04. Final structure after installation

```
Code:        $(uv tool dir)\tool-name\Lib\site-packages\ (src\ import package and main.py module)
Command:     tool-name (uv shim in `%USERPROFILE%\.local\bin\`, directory on PATH)
Config:      $env:APPDATA\tool-name\config\config.ini
Secrets:     $env:APPDATA\tool-name\.env
Logs:        $env:APPDATA\tool-name\log\
```

The source repository and installation archive are not needed for the tool to work after installation.

---

## 05.05. Version, config and .env sync on update

*Mandatory.*

The migration algorithm canon (structure comparison, backups, value transfer, rules) - core `deploy_standards.md`, 04.01; here only Windows platform specifics:

- Script - `update.py` in the archive root (reference code - `deploy_standards.md`, 03.04; substitutions - 04.04)
- Stage 0 (repository version sync) is absent: the archive is built on Linux, the package version is fixed in the wheel
- Example structure source - the archive (`SCRIPT_DIR`): `config/config.ini.example`, `.env.example`; `app.name` / `app.version` - from the archive
- Prod files - `$env:APPDATA\tool-name\`: `config\config.ini`, `.env`
- Backups and rewriting - core canon (`deploy_standards.md`, 04.01)

---

## 05.06. OS-specific checklist (Windows)

*Mandatory.*

Add to the common checklist (core - `deploy_standards.md`, 05.04):

1. Install scripts (`run/deploy/install.py`, `run/deploy/update.py`, `run/deploy/package.py`) use the correct `TOOL_NAME` and version (`TOOL_VERSION` for `package.py`).
2. `.gitignore` contains `*.egg-info/`, `dist/`, `build/`, `*-install.zip`.
3. A test archive build (`python run/deploy/package.py`) succeeded.
4. A test installation from the archive on the target Windows machine succeeded.
5. The `PROJECT_ROOT` swap uses the correct tool name and the APPDATA path.

---

## 06.01. Related documents

| Document | Relation |
|----------|----------|
| `deploy_standards.md` | Shared deploy core; this document is an OS overlay applied together with it |
| `deploy_lin_standards.md` | Paired OS overlay for Linux (the archive preparation phase runs on the Linux machine) |
| `doc/standards/project_standards.md` | Core standard |

---

## 06.02. Versioning

Standards package versioning is unified for all package documents. The versioning policy, registry and routing map live in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see _index_standards.md).
