# Agent Memory (data/memory). Version 5.0.1

Canon for persistent AI agent memory: two scopes (project and session), a closed file list, strict structure, and rules for reading and updating. The document supplements `project_standards.md` and applies on top of it. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

---

## Table of Contents

**01. Purpose and scopes:** 01.01 Purpose - 01.02 Scopes - 01.03 Boundary with adjacent mechanisms

**02. Placement and lifecycle:** 02.01 Placement and committability - 02.02 Creation and filling

**03. Closed file list**

**04. File structure:** 04.01 memory.md index - 04.02 Topic files

**05. Maintenance rules**

**06. Reading memory**

**07. Relations and versioning**

---

## 01.01. Purpose

*Mandatory.*

Agent memory is persistent context passed between sessions, agents, and tools: accepted decisions with rationale, facts about the project environment, user preferences in the project context. Without memory every agent and every session starts from scratch and accumulates context again. The entry point is the `memory.md` index; memory is read at session start and updated during work. Memory does not replace standards, specifications, and git history - it stores working context that has no place in those artifacts.

---

## 01.02. Scopes

*Mandatory.*

| Scope | Path | Commit |
| ----- | ---- | ------ |
| Project | `<repo>/data/memory/` | yes - exception `!data/memory/` in `.gitignore` (`project_standards.md`, 06.01) |
| Session | `<session-dir>/data/memory/` | per session folder rules (`project_standards.md`, 01.01.01) |

- Project memory is shared by all agents, sessions, and tools working with the repository; git transport makes it shared across all clones
- Session memory is the working context of a specific session: draft decisions and observations before they move to project memory
- The file list and structure are identical for both scopes

---

## 01.03. Boundary with adjacent mechanisms

*Mandatory.*

- The lesson journal `data/lessons.md` (`project_standards.md`, 01.01.07) is not part of memory: it is transferable experience for other projects, records are only appended, and capture is done by the `glob-mine-lesson` skill. A lesson is never written to memory; a decision that becomes a lesson moves to the journal and is removed from memory (05)
- Skill runtime data - zones `data/registries/`, `data/journals/`, `data/state/` (`doc/standards/skill_data_standards.md`) - is not memory: zones store task data, memory stores agent context
- Project configuration - `config/` and `.env` (`project_standards.md`, 01.02): code operation parameters, not agent knowledge
- Specifications and CR - `doc/specs/`, `doc/change_requests/`: task contract, not accumulated context
- `AGENTS.md` - permanent instructions; memory - changing context. Separation: a rule goes to AGENTS.md, a state fact goes to memory
- MCP memory servers and vector stores are not canonized: memory content is grepped and diffed by git

---

## 02.01. Placement and committability

*Mandatory.*

Project memory lives in `data/memory/` at the repository root; session memory - in the session folder `data/memory/`. The `data/` directory is ignored by git as a whole; for project memory the exception `!data/memory/` is added (`.gitignore` template - `project_standards.md`, 06.01). Secrets, keys, and personal data are not written to memory (05) - memory committability is safe.

---

## 02.02. Creation and filling

*Mandatory.*

Memory is created on the first write, not at project initialization: the `data/memory/` directory and the `memory.md` index appear when content exists. A repository can live without memory indefinitely; the absence of the directory is not a standard discrepancy. The first write of any type creates the corresponding topic file and registers it in the index.

---

## 03. Closed file list

*Mandatory.*

The list is closed: other file names in `data/memory/` are forbidden. Extending the list is an edit to this standard, not an agent initiative.

| File | Purpose | Requirement |
| ---- | ------- | ----------- |
| `memory.md` | Index: file registry, current state, working rules | mandatory when memory exists; entry point |
| `decisions.md` | Journal of decisions and choices with rationale | on the first decision record |
| `env.md` | Environment facts: paths, versions, project specifics | on the first environment fact |
| `preferences.md` | User preferences in the project context | on the first preference record |

---

## 04.01. memory.md index

*Mandatory.*

Memory does not keep its own SemVer: change history is in git. The index structure is three fixed sections in the order below; custom sections are forbidden:

```markdown
# Память: <repo-or-session>

## Реестр файлов

| Файл | Статус |
|------|--------|
| decisions.md | ведется |
| env.md | ведется |
| preferences.md | пуст |

## Текущее состояние

<current_state>

## Правила

- чтение: индекс + decisions.md + env.md; preferences.md - по релевантности задачи
- пополнение: в конце шага задачи; уроки - в data/lessons.md, не сюда
- канон: doc/standards/memory_standards.md
```

The "Реестр файлов" section lists all files of the list with their actual status (`ведется` / `пуст`); files with status `пуст` are present in the registry only if created. The "Текущее состояние" section is up to 5 lines: where work stopped, what is next. Memory content language follows the project language; records may be Russian.

---

## 04.02. Topic files

*Mandatory.*

The file heading is `# <topic>` (Решения, Окружение, Предпочтения). Records have the form:

```markdown
## YYYY-MM-DD - краткий заголовок

- суть: <decision-or-fact>
- обоснование: <rationale>
```

- New records are added at the top of the file
- One record - one thought; narrative and multi-paragraph text are forbidden
- Implementation details reference artifacts (spec, commit, CR) instead of retelling them

---

## 05. Maintenance rules

*Mandatory.*

- Update at the end of a task step or the whole task, not in the middle of work; draft records at the end of a step are allowed in session memory
- A write to project memory is performed by one agent at the moment a step completes - step completion is the merge point; parallel accumulation happens in session memory
- Contradicting records do not coexist: a new record on the same topic edits or replaces the old one in the same change
- Duplicates are forbidden: a repeated record on the same topic supplements or replaces the existing one
- A decision that becomes a transferable lesson is recorded in the `data/lessons.md` journal (`project_standards.md`, 01.01.07, `glob-mine-lesson` skill) and removed from memory
- Secrets, keys, and personal data are forbidden
- `env.md` does not contain machine-identifying information (host names, users, addresses, serial numbers): the file is committed and must be suitable for a public repository; machine specifics go to the project override (`doc/specs/overrides.md`) or session memory

---

## 06. Reading memory

*Mandatory.*

- Mandatory minimum at session start (when the directory exists): `memory.md`, `decisions.md`, `env.md`
- `preferences.md` is read per the index registry when the task involves interaction with the user
- For a resumable session, session memory is read first, then project memory
- The agent tells the user that memory has been read and what was added at the end of the work

---

## 07. Relations and Versioning

| Document | Relation |
| -------- | -------- |
| `project_standards.md` | project structure and `data/` (01.01), sessions and session memory (01.01.01), `.gitignore` template (06.01), lesson journal (01.01.07) |
| `index_nav_standards.md` | AGENTS.md skeleton - the memory line in "Session Entry Points" (07) |
| `skill_anthropic_standards.md` | boundary with the configuring skill state snapshot (03.05) |
| `skill_data_standards.md` | boundary between memory and skill runtime data zones (01.03) |

Standards package versioning is unified for all package documents; policy - in `doc/standards/_index_standards.md`. Bump the version only on an explicit user request.
