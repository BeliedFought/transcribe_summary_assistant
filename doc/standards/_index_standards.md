# Standards Package Index. Version 5.0.1

Entry point to the standards package. Tag this file to make an agent load only the documents relevant to the current task. Each overlay applies on top of `project_standards.md` for its project class.

Unified package SemVer (see "Versioning Policy"). The version in this index, in every `doc/standards/*.md` H1, in `AGENTS.md`, `CLAUDE.md`, and `README.md` is the same value.

Decision priority when a rule is missing or ambiguous: `project_standards.md` (Section 07.06).

---

## Mandatory Application

Tagging this file (`@doc/standards/_index_standards.md`) means **mandatory application** of the package, not mere familiarization. The agent:

1. Picks relevant documents from the routing map below.
2. Loads and applies their requirements to the current task.
3. Passes the requirements to subagents; subagents apply them to the same extent.
4. Verifies compliance before reporting completion.

The standards apply whenever work touches the project, tagged or not. Subagents apply them on par with the main agent.

---

## Document Registry

| Document | Load when |
|---|---|
| `project_standards.md` | Always; core changes (structure, config, output, security, git, workflow) |
| `cli_data_standards.md` | Data or CLI project (SQLite mart, diagnostics, sessions, SQL, `run/`) |
| `network_ops_standards.md` | Network or system work (retries, SSH, DPI/routing/SMB, mutations) |
| `code_standards.md` | Writing or reviewing code; linter setup |
| `console_ui_standards.md` | Menu/rich UI, batch CLI, console mockups |
| `cli_output_standards.md` | Script and CLI console output: named formats, `report`, `plain`, `porcelain`, color, language |
| `deploy_standards.md` | Packaging a Python tool; install/update/migration |
| `deploy_lin_standards.md` | Installing on Linux |
| `deploy_win_standards.md` | Installing on Windows |
| `deploy_docker_standards.md` | Docker services, ports, logs, backups |
| `deploy_hyperv_standards.md` | Hyper-V VM deployment |
| `web_standards.md` | Building or deploying a web app |
| `skill_anthropic_standards.md` | Creating, updating, migrating a skill; frontmatter `purpose` and `topic` fields |
| `skill_data_standards.md` | Skill writes registries, journals, state, cache |
| `opencode_tool_standards.md` | Creating or revising custom tools |
| `index_nav_standards.md` | Creating or editing an index or `AGENTS.md`; setting skill purpose or topic fields |
| `memory_standards.md` | Reading or updating agent memory |
| `change_request_standards.md` | Creating, tracking, archiving a CR |
| `repo_info_doc_standards.md` | Writing or updating `README.md` |
| `software_doc_standards.md` | Writing an installation guide |
| `human_text_standards.md` | Writing any human-facing Russian text |
| `human_text_dict_standards.md` | Editing Russian text (stop words) |
| `human_text_dict_ai_standards.md` | Editing Russian text (AI markers) |
| `human_text_allowlist_standards.md` | Choosing a replacement |
### Reference Code Templates (`doc/standards/templates/`)

Synced with `doc/standards/` (read-only in derivative repos). Load a template only when creating or auditing the matching project file.

| Template | Purpose |
|---|---|
| `config.py` | `PROJECT_ROOT`, `config`, `APP_NAME`, `APP_VERSION`; Linux XDG and Windows AppData deploy variants |
| `config.ini.example` | Canonical `config.ini` sections and keys |
| `localization.py` | `t(key, *, count=None, **kwargs)` UI localization; English default, Russian opt-in |
| `logger.py` | Dual-channel logger: English `%s` logs, English-default console (`report`/`plain`/`menu`/`rich`), `_SecretFilter`, rotation |
| `progress.py` | `plain`-mode progress line helpers |
| `gitignore.template` | Base `.gitignore` |
| `install.py` | CLI installer (flat `src/`, `uv tool install`, `PROJECT_ROOT` swap) |
| `update.py` | CLI updater and `config.ini`/`.env` migration |

Archive rule: `.backup/<version>/` holds cold snapshots of prior package versions and is never read by agents unless explicitly requested.

---

## Routing Map

| Task topic | Document (section) |
|---|---|
| Project structure, folder layout, `.arch/` archiving, `.trash/` quarantine, overrides, lessons log | `project_standards.md` (01.01) |
| Agent memory `data/memory/` | `memory_standards.md` |
| Sessions `SESSION.md`; local SQLite mart and modes; `diag/`/`tmp/`/`test/`; SQL layout, migrations, `schema_version`; `run/` entry points and CLI | `cli_data_standards.md` |
| Configuration, `[app]` identity and SemVer, paths/`PROJECT_ROOT`, startup validation, dependencies, `.venv`, pip mirror | `project_standards.md` (01.02-01.07); `glob-cfg-pip` |
| DB/API/Ollama settings, SMTP; GitHub SSH discovery | `project_standards.md` (02.01-02.06) |
| Retry/liveness, SSH hosts and embedded targets, DPI/DNS/SNI/IPv6/CDN/SMB, system config mutation patterns | `network_ops_standards.md` |
| Idempotency, atomic writes, `--dry-run`, non-interactive confirmation | `project_standards.md` (03.01) |
| Output modes, TTY detection, localization `t()`, markers, formatting, errors | `project_standards.md` (04.01-04.07); `console_ui_standards.md`; `cli_output_standards.md` |
| Script and CLI output: named formats, `report` default, clean `plain`, `--porcelain`, color, English default with Russian opt-in | `cli_output_standards.md`; `project_standards.md` (04.04, 04.07) |
| Language split, typography, dual-channel logging | `project_standards.md` (04.03, 04.06); `cli_output_standards.md` (05); `human_text_standards.md` |
| GUI startup validation and `tkinter` | `project_standards.md` (04.08) |
| Console UI frame, keys and menu layout, roles, tables, batch progress, `spec_ui.html` | `console_ui_standards.md` |
| Secrets, external input validation, SQL/subprocess/TLS/path safety, sudoers fragments | `project_standards.md` (05.01) |
| Exceptions, shutdown, exit codes, privileged levels 0-3 | `project_standards.md` (05.02-05.04); `skill_anthropic_standards.md` (03.04) |
| Git, `.gitignore`, English commits, dynamic author, pre-commit gate | `project_standards.md` (06.01) |
| `README.md` (Russian) and `AGENTS.md` (English); index and `CLAUDE.md` policy | `project_standards.md` (06.02); `repo_info_doc_standards.md`; `index_nav_standards.md` (07) |
| AGENTS.md typography layer: static block, machine layer, where rules live | `index_nav_standards.md` (07.04-07.06); `project_standards.md` (04.03) |
| Debugging discipline and 3-fix rule | `project_standards.md` (06.03); `superpowers:systematic-debugging` |
| Testing priorities and reference tests | `project_standards.md` (06.04); `cli_data_standards.md` (02.04) |
| Workflow, superpowers delegation, task classification, clarification modes, Russian specs, screenshots, `ДЕЛАЙ`/`GO`, data UI recon, initialization, audit, editing standards, decision cascade | `project_standards.md` (07) |
| Package glossary and versioning | `project_standards.md` (08.01); this index |
| Code naming and slugs, comments/TODO, Python, JS/TS and plugins, HTML/CSS, Shell, PowerShell/batch, JSON/TOML/YAML/SQL, linters | `code_standards.md` (01-08) |
| Deploy CLI: packaging, `PROJECT_ROOT`, install/update contracts, config/.env migration; Linux and Windows overlays | `deploy_standards.md`; `deploy_lin_standards.md`; `deploy_win_standards.md` |
| Docker compose, ports, ufw, logs, backups, service docs, host overrides | `deploy_docker_standards.md` |
| Hyper-V Linux VM deployment and maintenance | `deploy_hyperv_standards.md` |
| Web app structure, FastAPI, nginx fronts, systemd/Docker, TLS, update/rollback, runtime data, UI base | `web_standards.md` |
| Skill `SKILL.md` layout, frontmatter, types, categories, scripts, root commands, discovery/testing | `skill_anthropic_standards.md`; `superpowers:writing-skills` |
| Skill runtime data zones and formats | `skill_data_standards.md` |
| Local skills and skill indexes | `skill_anthropic_standards.md` (01.03); `index_nav_standards.md` (06.02) |
| Custom OpenCode tool vs skill; plugin V2, schema, output, permissions | `opencode_tool_standards.md` |
| Index skeleton, registry, routing map, auto-update | `index_nav_standards.md` (03-06) |
| Change requests: create, review, transfer to spec, archive | `change_request_standards.md` |
| `README.md` structure and file table; app installation documents | `repo_info_doc_standards.md`; `software_doc_standards.md` |
| Russian text genres, speech styles, writing and self-check | `human_text_standards.md` |
| Russian stop words, AI markers, preferred constructions and replacements; text overrides | `human_text_dict_standards.md`; `human_text_dict_ai_standards.md`; `human_text_allowlist_standards.md`; `human_text_standards.md` (05.03) |
| Plan-file style | `superpowers:writing-plans` |

## Versioning Policy

The package uses one SemVer `MAJOR.MINOR.PATCH` for every document. Individual document versions are abolished.

Header format for every document: `# <document_name>. Version X.Y.Z`. No dates in headers; the actual change date lives in git history.

- **PATCH** - wording clarifications, typo fixes, formatting, example updates, additions to existing lists.
- **MINOR** - new sections, rules, or requirements inside existing documents; structural changes inside a document.
- **MAJOR** - adding or removing package documents, incompatible structure or requirement changes, changed document purpose or scope, model changes.

**Bump only on explicit user request.** Editing `doc/standards/` content never bumps the version by itself.

On an explicit bump request: choose PATCH/MINOR/MAJOR unless the user named the level, then set one value in this index, every `doc/standards/*.md` H1, `AGENTS.md`, `README.md`, and `CLAUDE.md`. All present locations must match. Updating the registry and routing map is mandatory on any package file change.

---

## Index Auto-Update

Tagging this file without a concrete task triggers auto-update: read every `doc/standards/*.md` except this index, extract name/scope/version, refresh the registry and routing map, verify one package version across standards and root files, and report changes and mismatches.
