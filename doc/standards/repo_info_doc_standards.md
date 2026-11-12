# Repository Human Documentation: README and Descriptions. Version 5.2.0

Canon for human repository documents: README.md, instructions, and user descriptions. The document supplements `project_standards.md` and applies on top of it. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

The canon for agent navigation documents (indexes, AGENTS.md) is `index_nav_standards.md`.

---

## Table of Contents

**01. Audience and principles:** 01.01 Audience - 01.02 Language - 01.03 Text style - 01.04 Boundary with agent documents

**02. README.md:** 02.01 Mandatory status and minimum structure - 02.02 File and directory structure - 02.03 Menu

**03. Section applicability:** 03.01 Applicability rule - 03.02 Always mandatory sections

**04. Updates and other documents:** 04.01 README updates - 04.02 Other human documents

**05. Relations and versioning:** 05.01 Related documents - 05.02 Versioning

---

## 01.01. Audience

*Mandatory.*

Human documents are written for the project user, not for an agent: business language of the project domain, without technical jargon where it is not needed, without mention of AI agents, standards, and the internal mechanics of agent work (indexes, routing, triggers). Agent working rules live in `AGENTS.md` (`index_nav_standards.md`); they do not belong in README.

---

## 01.02. Language

*Mandatory.*

The document language is Russian by default; English only on an explicit user request or when the document is already maintained in English. Do not mix languages in one document. When editing an existing document, write in that document language. Commands, paths, and configuration keys keep their original spelling (Latin).

---

## 01.03. Text style

*Mandatory.*

The text is factual: what it does, what it consists of, how it starts. No evaluations, no change stories, no promises of future features (text requirements - `project_standards.md`, 04.03). Paths in the document are relative to the repository root. Volatile lists (dependency versions, file composition) are kept in sync with the actual project state.

---

## 01.04. Boundary with agent documents

*Mandatory.*

README and descriptions are for humans; indexes and `AGENTS.md` are for the agent (`index_nav_standards.md`). The requirements of this document do not extend to navigation documents, and vice versa: the README menu map does not duplicate `spec_ui.html`, and README references to agent service documents are given without retelling their content.

---

## 02.01. Mandatory status and minimum structure

*Mandatory.*

Every project contains `README.md` at the root. Minimum structure:

- **Standard version** - the line `Соответствует стандарту: X.Y.Z` (the standards package semantic version the project was created with; `project_standards.md`, 07.04)
- **`Назначение`** - what the project does (1-3 sentences)
- **`Требования`** - Python version, dependency list
- **`Установка`** - environment creation, dependency installation. Must include bash commands for venv setup:

```bash
python3 -m venv --copies .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- **`Настройка`** - what to fill in `.env` (key list) and `config/config.ini` (parameter list)
- **`Пайплайн проекта`** - description of the data processing stage sequence: which steps run, in what order, what each stage receives and what it produces
- **`Структура файлов и директорий`** - table (02.02)
- **`Запуск`** - which scripts to run and in what order
- **`Меню`** - only for projects with an interactive menu (02.03)

The section names above stay Russian in the README; the standard describes their meaning.

---

## 02.02. File and directory structure

*Mandatory.*

The `Структура файлов и директорий` section is a table describing the purpose of every project folder and file, without exceptions. Format: the first column is the folder or file path, the second column is the purpose. The table is the source of truth on repository composition for humans; `AGENTS.md` duplicates it with a pointer to README, not a copy.

When updating documentation on a user request, the agent rereads the whole project and updates the table to the current project state.

---

## 02.03. Menu

*Mandatory for projects with an interactive menu.*

The menu map is not duplicated in README; the only source of the map, frames, and keys is `doc/specs/spec_ui.html` (mandatory per `console_ui_standards.md`). README provides an explicit reference to `doc/specs/spec_ui.html` as the source of the menu structure.

---

## 03.01. Applicability rule

*Mandatory.*

README sections (02.01) are mandatory when applicable to the project. A non-applicable section is not created and not left as a stub - instead, a section answering the same question for the given repository type is included. Replacement examples:

- a non-runnable repository (standards hub, scaffold, documentation) instead of `Требования`, `Установка`, `Настройка`, `Пайплайн` uses sections about real usage: pre-commit hook activation, synchronization procedure, how to work with the repository
- a library instead of `Запуск` uses a section about importing and entry points

Fictitious sections (a heading with the text "none" or empty content) are forbidden: README must not pretend to be a runnable project.

---

## 03.02. Always mandatory sections

*Mandatory.*

Regardless of repository type, README contains:

1. The standard version line `Соответствует стандарту: X.Y.Z`
2. `Назначение`
3. `Структура файлов и директорий` (02.02)
4. A section about launching or the way to use the repository

Other sections follow the applicability rule (03.01).

---

## 04.01. README updates

*Mandatory.*

README is updated when the facts it describes change: file and folder composition, pipeline, settings, launch method. A repository change and a README edit are one change (commit) when README is affected. On the user request "update the documentation" the agent rereads the whole project and brings README (primarily the structure table) to the current state.

---

## 04.02. Other human documents

*Mandatory when the corresponding documents exist.*

- Application installation documents in documentation repositories - `software_doc_standards.md`; the H1 form `# <Title>. Version X.Y.Z` and the document version rules - `software_doc_standards.md` (04.02)
- Web application service documentation (installation, deploy, update) - `web_standards.md` (12)
- Windows deploy archive `README.txt` - generated by the build script, text canon - `deploy_win_standards.md`
- Project specifications: start specifications (`doc/specs/init/` folder: `init_base.txt`, `init_final.md`) - the pre-MVP development stage; on transition to production the folder is archived to `.arch/`; live ones - module `spec_<module>.md` support specifications. Creation and approval - `project_standards.md` (07.02), placement - 01.01; this document does not extend to them
- Mockup `doc/specs/spec_ui.html` - `console_ui_standards.md`

---

## 05.01. Related documents

| Document | Relation |
| -------- | -------- |
| `doc/standards/project_standards.md` | Core standard; specification process (07.02), document placement (01.01) |
| `index_nav_standards.md` | Agent navigation document canon; boundary - indexes and `AGENTS.md` versus human documents |
| `console_ui_standards.md` | Source of the menu map (`doc/specs/spec_ui.html`); README does not duplicate the map |
| `software_doc_standards.md` | Application installation document template; document H1 version form and version bump rules (04.02) |
| `web_standards.md` | Web application service documentation template (12) |
| `deploy_win_standards.md` | Text canon for the Windows deploy archive `README.txt` |

---

## 05.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and routing map - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
