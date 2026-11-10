# Software Installation Document Standards. Version 5.0.1

A single template for documents describing software installation and configuration. Each document is one `.md` file with bash blocks. Skip optional sections without leaving empty headings.

The standard is intended for documentation repositories that describe software or system setup and installation. Each document covers one application or infrastructure component and follows a single section structure. A repository based on this standard contains a set of such documents, providing uniform formatting and reproducible installation procedures.

It supplements `doc/standards/project_standards.md` and applies on top of it. All core standard requirements remain in force unless this document explicitly overrides them. Installation documents are Russian human-contour documents; the required section names stay Russian as defined below.

---

## Table of Contents

**01. General rules:** 01.01 General formatting rules

**02. Section catalog:** 02.01 Section catalog (02.01.01 Heading - 02.01.02 Description - 02.01.03 Dependencies - 02.01.04 Installation - 02.01.05 Launch - 02.01.06 Verification - 02.01.07 Removal - 02.01.08 Configuration - 02.01.09 Troubleshooting - 02.01.10 Update - 02.01.11 Usage - 02.01.12 References)

**03. Scheme:** 03.01 Reference scheme

**04. Relations and versioning:** 04.01 Related documents - 04.02 Versioning

---

## 01.01. General formatting rules

*Mandatory.*

- All commands are inside bash blocks only (triple backticks with `bash`), except in the `Ссылки` section
- Comments inside blocks are concise, Russian, capitalized, without emoji
- Privileged commands (pacman, system file sed, systemctl) go through `sudo`, with a comment about the root requirement
- Do not use hardcoded user names and hostnames; use `"$(whoami)"` and `"$(hostname)"`
- Install packages from official repositories through `pacman`, from AUR through `yay`
- Skip optional sections without content, without leaving empty headings
- Do not use Obsidian markup (callouts, `[[...]]` links)

---

## 02.01. Section catalog

*Mandatory.*

Target document sections follow strictly in the specified order. The numbering below is for the target installation document.

### 02.01.01. Heading

*Mandatory.*

```
# <app_name>
```

The H1 is the application name as it is used; the target section is `Заголовок`.

### 02.01.02. Description

*Mandatory.*

Target section name: `Описание`. A brief software purpose, 1-3 sentences. Placed immediately after the heading, without an H2.

### 02.01.03. Dependencies

*Optional.*

Heading: `## Зависимости`.

Required packages, runtimes, enabled repositories. State only when additional components are needed that are not pulled in automatically as dependencies.

### 02.01.04. Installation

*Mandatory.*

Heading: `## Установка (<mode>)`.

The installation mode is stated in parentheses in the section heading.

Allowed modes:

| Mode | Package manager |
| ---- | --------------- |
| `pacman` | Official repositories |
| `AUR` | AUR through yay |
| `makepkg` | Manual AUR build |
| `npm` | npm (global installation) |
| `pip` | pip (global/user) |
| `Flatpak` | Flatpak |
| `curl` | Installation script download |
| `GUI` | Graphical installer |

Rules:

- For project tools installed per the deploy standard (a system tool through `uv tool`), the installation section describes the steps of `deploy_standards.md` and the platform overlay documents; the package manager modes in the table are for third-party applications
- If an application can be installed from several sources, each method gets a separate `## Установка (<mode>)` section
- Additional packages (fonts, plugins) required for full operation are included in the same section as separate blocks with comments
- Groups of related utilities (disk utilities, fonts) - all packages in one block; with different sources - several blocks
- If an application requires a system service, `systemctl enable --now` is included in the same installation block
- For user services - `systemctl --user enable --now` likewise in the installation block
- If the application requires group membership, `usermod -aG` is included in the installation block with a comment about the required re-login

### 02.01.05. Launch

*Mandatory.*

Heading: `## Запуск`.

The application launch command or a reference to the launch method (GUI applications through the menu, services through systemctl).

### 02.01.06. Verification

*Mandatory.*

Heading: `## Проверка`.

A command that verifies the version, status, or operability. It must give an unambiguous answer: whether the package is installed and which version.

Rules:

- The preferred method is `--version`
- If the application does not support `--version` - `pacman -Q <package>`
- For services - `systemctl status <service>`
- For loadable modules - `lsmod | grep <module>`

### 02.01.07. Removal

*Mandatory.*

Heading: `## Удаление`.

The package removal command. Use `pacman -Rns` (or `yay -Rns` for AUR) to remove the package, unneeded dependencies, and configs.

Rules:

- If configs are stored in user directories, add their cleanup commands (`~/.config/`, `~/.local/share/`, `~/.cache/`)

### 02.01.08. Configuration

*Mandatory.*

Heading: `## Конфигурация`.

Standard configuration file paths. State all relevant locations.

Typical paths:

| Location | Purpose |
| -------- | ------- |
| `~/.config/<app>/` | User configs (XDG) |
| `~/.local/share/<app>/` | User data |
| `~/.cache/<app>/` | Cache |
| `/etc/<app>/` | System configs |
| `~/.<app>rc` | RC file in the home directory |
| `~/.<app>/` | Hidden directory in the home directory (legacy format) |

Rules:

- If the configuration requires target environment settings (Wayland, KDE, NVIDIA), state them here with an explanation
- Place wrapper scripts in `~/.local/bin/`
- `.desktop` files go to `~/.local/share/applications/`
- Autostart goes to `~/.config/autostart/`
- If a custom systemd service is required, include its creation in this section

### 02.01.09. Troubleshooting

*Optional.*

Heading: `## Решение проблем`.

Known problems and their solutions in the target environment. Each fix is a separate `### <symptom>` subsection with a symptom description and solution.

### 02.01.10. Update

*Optional.*

Heading: `## Обновление`.

State only when the update method differs from the standard `pacman -Syu` / `yay -Syu`.

### 02.01.11. Usage

*Optional.*

Heading: `## Использование`.

Examples of typical commands, aliases, shortcuts. For CLI/TUI utilities and applications with non-obvious controls.

Rules:

- Single commands go in one bash block
- Multi-step procedures go in a separate bash block with step comments

### 02.01.12. References

*Optional.*

Heading: `## Ссылки`.

Useful links to documentation, Wiki pages, AUR pages. Format as a regular list, not a bash block.

---

## 03.01. Reference scheme

*Mandatory.*

Target document section order:

```
# <app_name>
(Описание - без заголовка, 1-3 предложения)

## Зависимости              (опционально)
## Установка (<mode>)      (обязательно)
## Запуск                   (обязательно)
## Проверка                 (обязательно)
## Удаление                 (обязательно)
## Конфигурация             (обязательно)
## Решение проблем          (опционально)
## Обновление               (опционально)
## Использование            (опционально)
## Ссылки                   (опционально)
```

Minimal document (mandatory sections only):

````
# <app_name>

Описание приложения.

## Установка (pacman)

```bash
sudo pacman -S <package>
```

## Запуск

```bash
<package>
```

## Проверка

```bash
<package> --version
```

## Удаление

```bash
sudo pacman -Rns <package>
```

## Конфигурация

```bash
~/.config/<package>/
```
````

---

## 04.01. Related documents

| Document | Relation |
| -------- | -------- |
| `doc/standards/project_standards.md` | Core standard; this document applies on top of it (documentation and comments) |
| `doc/standards/repo_info_doc_standards.md` | README and human document canon; boundary between README and installation documents |

---

## 04.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and routing map - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
