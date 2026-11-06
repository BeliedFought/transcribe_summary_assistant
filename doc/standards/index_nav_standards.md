# Repository Navigation Documents: Indexes and AGENTS.md. Version 5.0.0

Canon for repository navigation documents: directory indexes and the agent instruction file `AGENTS.md`. Purpose - fast and accurate AI agent routing: in one pass over an index the agent determines which files to open for a task and does not load whole directories. The document supplements `project_standards.md` and applies on top of it. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

The canon for human repository documents (README.md, instructions, descriptions) is `repo_info_doc_standards.md`.

---

## Table of Contents

**01. Purpose and scope:** 01.01 Purpose - 01.02 Scope

**02. Agent routing principles:** 02.01 Progressive disclosure - 02.02 Session entry points - 02.03 Index tagging - 02.04 Relation to the source hierarchy

**03. Index canon:** 03.01 Mandatory index skeleton - 03.02 Heading and versions - 03.03 Registry rules - 03.04 Update rules

**04. Routing map:** 04.01 Purpose and format - 04.02 Map row quality rules - 04.03 Coverage completeness - 04.04 Anti-patterns

**05. Repository index registry:** 05.01 Summary table

**06. Specific indexes:** 06.01 Standards package index - 06.02 Skill indexes - 06.03 Specifications index - 06.04 SQL file index (reference template) - 06.05 diag and test indexes - 06.06 Change request index

**07. AGENTS.md - agent router:** 07.01 Purpose and language - 07.02 Session entry points - 07.03 AGENTS.md and CLAUDE.md policy - 07.04 Layers and content principle - 07.05 Section taxonomy - 07.06 Skeleton

**08. Relations and versioning:** 08.01 Related documents - 08.02 Versioning

---

## 01.01. Purpose

*Mandatory.*

Indexes are entry points to repository directories. Their task is routing: connect a task type to specific files (and their sections) that must be opened. An index is valuable for speed: the agent reads one compact file instead of rereading the whole directory.

`AGENTS.md` is the top-level router: it condenses global canons into an excerpt and points the agent to session entry points - the indexes to read first.

The requirements of this document are mandatory when creating and editing any index and `AGENTS.md` in any repository (hub and derivative).

---

## 01.02. Scope

*Mandatory.*

The document covers:

- repository directory indexes: `doc/standards/_index_standards.md`, `doc/skills/_index_skills_hub.md`, `doc/skills/_index_skills_repo.md`, `data/skills/_index_skills_pl.md`, `doc/specs/_index_specs.md`, `doc/change_requests/_index_change_requests.md`, `sql/_index_sql.md`, `diag/_index_diag.md`, `test/_index_test.md` (full registry - 05.01)
- `AGENTS.md` and its mirror `CLAUDE.md` (mirror policy - 07.03)

The document does not cover: README.md and other human documents (`repo_info_doc_standards.md`), internal indexes of the standards package documents (section tables of contents), task specifications (`project_standards.md`, 07.02).

---

## 02.01. Progressive disclosure

*Mandatory.*

The agent loads the directory index, not the directory itself. From the index it determines relevant files and opens only them. Rules:

1. The context receives the index, not a listing of directory files
2. From the registry and routing map the agent determines relevant files and sections
3. Only relevant files are opened; reading a whole directory is an exception and requires a reason (the index is stale or the task requires a full review)
4. If the index did not help find the required file, the index is updated at the end of the task - the discovered routing gap is closed

---

## 02.02. Session entry points

*Mandatory.*

`AGENTS.md` must explicitly reference repository indexes at the start of the file so the agent reads them first at session start:

- standards package index `doc/standards/_index_standards.md` - document registry, routing map, versioning policy
- skill index - in the hub `doc/skills/_index_skills_hub.md`, in derivative repositories `doc/skills/_index_skills_repo.md` (when the index exists in the repository)
- specifications index `doc/specs/_index_specs.md` (mandatory, 05.01)

The reference is a file path mention at the start of `AGENTS.md` - for example the line `@doc/standards/_index_standards.md` or an explicit instruction to read the file first. References to other indexes (`sql/_index_sql.md`, `diag/_index_diag.md`, `test/_index_test.md`, `doc/change_requests/_index_change_requests.md`) are placed in the repo-specific part - when the directories exist in the repository.

---

## 02.03. Index tagging

*Mandatory.*

Tagging an index (`@path/to/_index_*.md`) means mandatory application of the relevant objects, not mere familiarization. The agent:

1. Determines relevant files from the index routing map
2. Loads the specified files and applies their requirements to the current task
3. Verifies compliance before finishing the work

If the index is tagged without a specific task, the index auto-update procedure runs per its "Index Auto-Update" section (03.04).

The index always applies when working with its directory, regardless of whether it was explicitly tagged; tagging only tells the agent to load and apply the index explicitly. Index requirements extend to subagents on par with the main agent.

---

## 02.04. Relation to the source hierarchy

*Mandatory.*

Indexes are the fourth level of the source hierarchy in decision-making (`project_standards.md`, 07.06): after explicit user instructions and overrides (session and project). An index does not create new norms - it routes to norms and files. If an index and a source document diverge, the document wins; the divergence is recorded and the index is updated.

---

## 03.01. Mandatory index skeleton

*Mandatory.*

Every index follows a single skeleton. Sections in order:

| Section | Purpose | Note |
| ------- | ------- | ---- |
| H1 title | index name (and version - for package indexes, 03.02) | the only H1 in the file |
| Intro | what the index is, which directory purpose it serves, how the agent uses it; a pointer to the decision order (`project_standards.md`, 07.06) | 1-3 sentences |
| Mandatory application | the meaning of tagging, agent steps, the rule of application without tagging | wording per 02.03 of this document |
| Registry | tables of directory objects | column composition per directory type (05.01, 06) |
| Routing map | task topic -> object | rules - 04 |
| Index auto-update | a numbered rebuild procedure on tagging without a task | steps: reread the directory, update the registry, update the map, check versions (if applicable), output a report |

Additional sections are allowed after the mandatory ones (for example "Versioning Policy" in `_index_standards.md`, "Project skills by repository" in `_index_skills_hub.md`) and must not duplicate the mandatory ones.

---

## 03.02. Heading and versions

*Mandatory.*

Two versioning modes:

- **Package indexes** (`doc/standards/_index_standards.md`, `doc/skills/_index_skills_hub.md`, `doc/skills/_index_skills_repo.md`): the H1 title carries the standards package version; it must match all package version locations (`project_standards.md`, 07.04). The index follows the package composition, and the version number follows package compatibility
- **Local repository indexes** (`data/skills/_index_skills_pl.md`, `_index_specs.md`, `_index_change_requests.md`, `sql/_index_sql.md`, `diag/_index_diag.md`, `test/_index_test.md`): no version in the title. Currency is determined by matching the actual directory composition; change history is in git. A date is not used in titles

Local index H1 format: `# <dir> Index` (for the hub - without a repository name or with the hub name as appropriate).

---

## 03.03. Registry rules

*Mandatory.*

1. The registry is a table (or tables by directory subfolders); the first column is the object path relative to the directory
2. Base column composition: object, purpose, when to apply. Directory specifics add columns: for SQL - parameters and consumer scripts (06.04); for skills - class, application domain, version (06.02)
3. Purpose is factual, one sentence, without evaluations, stories, and promises (text requirements - `project_standards.md`, 04.03). For `spec_ui.html` the purpose additionally states the mockup SemVer
4. Every registry row corresponds to an existing file or directory; every directory object (except the index files themselves and `.gitkeep`) is present in the registry
5. The index does not duplicate object content - only pointers: purpose, application triggers, links to sections. Content is read in the file itself
6. Archive elements (`<dir>/.arch/`) are not entered in the registry; a row of an archived object is removed from the registry (`project_standards.md`, 01.01)
7. A skill purpose can be fixed in frontmatter (`metadata.purpose`; top-level `purpose` for legacy flat skills); the explicit value takes precedence over `description`. A purpose is never cut inside a phrase - only at a sentence boundary

---

## 03.04. Update rules

*Mandatory.*

1. The index is updated in the same change (commit) as the directory composition change: addition, deletion, rename, purpose change of an object. For the hub standards package the control is the pre-commit hook (`project_standards.md`, 07.05)
2. If the index is tagged without a specific task, the procedure from the index's own "Index Auto-Update" section runs: reread the directory, update the registry, update the map, check versions (if applicable), output a report
3. The update is performed by the agent manually or by a dedicated skill (see the "Maintainer" column in 05.01); a script rebuild does not cancel manual verification of the registry and map per 03.03 and 04
4. The update report states: what was added, changed, deleted; version status (for package indexes); discovered discrepancies

---

## 04.01. Purpose and format of the map

*Mandatory.*

The routing map is a table connecting a task type to directory objects (for `_index_standards.md` - to package documents and their sections). Format: "Task topic" and object columns (for package indexes - a "Document(s)" column with section numbers). The map is the main fast-routing tool: the agent decides from the map what to open, without reading the directory.

---

## 04.02. Map row quality rules

*Mandatory.*

1. The topic is phrased from the user task perspective - as the task would be stated in a request, in the domain terms of the directory
2. The row lists request trigger synonyms (comma-separated): different formulations of one task lead to one row
3. A reference points to a precise object section (section number, paragraph), not the whole document - when only a part is relevant; to the whole document - when the entire document applies
4. Row language is Russian in Russian-language repositories; in the English agent contour rows are English. Technical identifiers (paths, masks, keys) stay English
5. One row - one topic; do not split a row into duplicate synonyms, and do not merge until specificity is lost
6. A skill map topic can be fixed in frontmatter (`metadata.topic`; top-level `topic` for legacy flat skills). Without it the topic is the purpose head before the first colon; with no colon the topic repeats the purpose and the row is reported for manual refinement

---

## 04.03. Coverage completeness

*Mandatory.*

1. Every registry object is reachable by at least one map row (no orphans)
2. Every map row leads to an existing object and an existing section; references to missing or archived objects are a discrepancy
3. The map is updated synchronously with the registry in the same change
4. A routing gap discovered in work (a task was not found by the map) is closed by adding a row at the end of the task

---

## 04.04. Anti-patterns

*Mandatory.*

Forbidden in the routing map:

1. Vague topics: "other", "miscellaneous", "general questions", "everything else" - the topic must name the task
2. Duplicating document content in map rows - a row routes, it does not retell
3. References to non-existent, archived, or renamed objects without an update
4. Rows without a link to a directory object (text explanations only)
5. Mixing audiences: a navigation index map is addressed to the agent and must not solve human documentation tasks (`repo_info_doc_standards.md`)

---

## 05.01. Summary table

*Mandatory.*

| Index | Directory | Requirement | Maintainer |
| ----- | --------- | ----------- | ---------- |
| `doc/standards/_index_standards.md` | Standards package | Mandatory in the hub; copied to derivative repos with the package | `hub-sync-indexes` skill (hub only) |
| `doc/skills/_index_skills_hub.md` | Hub skills (all repositories) | Hub only | `hub-sync-indexes` skill |
| `doc/skills/_index_skills_repo.md` | Derivative repository skills | Mandatory when `doc/skills/` exists in a derivative repository | `glob-update-indexes` skill |
| `data/skills/_index_skills_pl.md` | Repository local skills (`pr_loc`) | Mandatory when `data/skills/` exists | `glob-update-indexes` skill |
| `doc/specs/_index_specs.md` | Specifications | Mandatory in every repository | `glob-update-indexes` skill |
| `doc/change_requests/_index_change_requests.md` | Change requests (CR) | Mandatory when `doc/change_requests/` exists | Agent manually (canon - `change_request_standards.md`, 02.03) |
| `sql/_index_sql.md` | SQL files | Mandatory when `sql/` exists | Agent |
| `diag/_index_diag.md` | Diagnostic scripts | Mandatory when `diag/` exists | Agent |
| `test/_index_test.md` | Reference agent tests | Mandatory when `test/` exists | Agent |

Notes:

- In the `project_standards` hub the `sql/`, `diag/`, and `test/` folders are not created (hub specifics); `_index_specs.md` in the hub is a reference template and is not overwritten by the `glob-update-indexes` skill; in the hub the skill applies only to `data/skills/_index_skills_pl.md` (when the `data/skills/` directory exists)
- Package and hub skill directory indexes are maintained by synchronization skills; local ones - by the agent or a package script with manual verification per 03.03, 04

---

## 06.01. Standards package index

*Mandatory.*

`doc/standards/_index_standards.md` is the entry point of the standards package. Composition: package document registry (document, purpose, applicability, when to apply), package routing map (topic -> document and sections), package versioning policy, auto-update. It is the only index containing the versioning policy: package SemVer rules, version location list, bump procedure - the canon is there and must not be duplicated in other documents.

---

## 06.02. Skill indexes

*Mandatory when skills exist in the repository.*

Three indexes for different levels:

- `_index_skills_hub.md` (hub only): summary index - global skills (`glob-*`, type `hub_glob`), hub skills (`hub-*`, type `hub_loc`), aggregated project skills of all repositories from `doc/skills/ext/<repo>/` (`pg-*`, type `pr_glob`). Additional sections: project skill summary by repository, a note on skill versioning
- `_index_skills_repo.md` (derivative repositories): local index - root Anthropic-format directories (`glob-*`, `pg-*`); legacy flat `*.md` skills are listed until migration. Generated by the package script (`glob-update-indexes` skill)
- `_index_skills_pl.md` (in `data/skills/`, any repository): local skill index (`pr_loc`) - SKILL.md directories in `data/skills/`. Generated by the same package script (`glob-update-indexes`) when the directory exists; local skills are not included in the summary indexes (`_index_skills_hub.md`, `_index_skills_repo.md`)

Skill registry columns: directory name, class (by `metadata.type`), application domain (`metadata.category` / `metadata.category_name`), version (`metadata.version`), purpose and when to apply (`description`). Class is determined by the type slug (`skill_anthropic_standards.md`, 01.03): `hub_glob` - global, `pr_glob` - project, `hub_loc` - hub, `pr_loc` - local. The application domain is the category slug and its name from the closed dictionary (`skill_anthropic_standards.md`, 01.04); the category is optional, and when absent the column is filled with `-`. The local skill index link is placed in the repo-specific part of `AGENTS.md` (when the `data/skills/` directory exists).

---

## 06.03. Specifications index

*Mandatory in every repository.*

`doc/specs/_index_specs.md` is the entry point to the specifications directory. Composition: a root file registry (file, type, purpose), a section for start specifications `doc/specs/init/` (file, type, purpose), and a summary of subfolders `doc/specs/<project>/` (folder, file composition, purpose). Root file types: `spec_<slug>.md` - a live task or module specification; `spec_ui.html` - output specification (mandatory for user-facing output; the purpose states the mockup SemVer); `overrides.md` - project override registry; `text_overrides.md` - text override. Start file types (`init/`): `init_base.txt` - user requirements; `init_final.md` - final initialization specification. The reference template is the hub `doc/specs/_index_specs.md`; in a derivative repository the index is formed from the actual composition. Sessions outside `doc/specs/` are not covered by the root index (`project_standards.md`, 01.01.01).

---

## 06.04. SQL file index (reference template)

*Mandatory when SQL files exist.*

The file `sql/_index_sql.md` is the registry of all project SQL files. Column specifics: parameters (variables substituted into the query) and consumer scripts. Reference template:

```markdown
# SQL Files Index - <repo-name>

Entry point to the SQL file directory. This file is tagged for an AI agent so it determines which SQL files are relevant to the current task. The agent loads the index, not all SQL files, and finds the required files from the index. Decision order when a rule is missing - `project_standards.md` 07.06.

---

## Mandatory Application

Tagging this file (`@sql/_index_sql.md`) means mandatory use of the index when working with SQL. The agent and subagents:

1. Add `sql/_index_sql.md` to the context, not individual .sql files
2. Determine from the index which SQL file the task needs
3. Read only the relevant .sql file
4. Update this index on any SQL file change

The index always applies when working with its directory, regardless of whether this file was explicitly tagged.

---

## SQL File Registry

### ddl/

| File | Purpose | Parameters | Consumer scripts |
| ---- | ------- | ---------- | ---------------- |
| create_users.sql | Users table (id, login, hash) | - | db_init, db_check_schema |

### queries/

| File | Purpose | Parameters | Consumer scripts |
| ---- | ------- | ---------- | ---------------- |
| get_active_users.sql | Active users for a period | :start_date, :end_date | report_users |

### dml/

| File | Purpose | Parameters | Consumer scripts |
| ---- | ------- | ---------- | ---------------- |
| seed_categories.sql | Initial category directory seed | - | db_init |

### migrations/

| File | Purpose | Parameters | Consumer scripts |
| ---- | ------- | ---------- | ---------------- |
| M001_add_orders_status.sql | Add the status column to the orders table | - | db_migrate |

---

## Routing Map

The map connects a task type to an SQL file. The agent finds the required file in the index and reads its content.

| Task topic | SQL file |
| ---------- | -------- |
| Database initialization, schema check | ddl/*.sql |
| Active user report | queries/get_active_users.sql |

---

## Index Auto-Update

On any change of SQL files in `sql/` (addition, deletion, purpose or parameter change) the agent must:

1. Update the SQL file registry: current file list, purpose, parameters, consumers
2. Update the routing map: current task topics and file references
3. Output a report: which files were added, changed, or deleted
```

---

## 06.05. diag and test indexes

*Mandatory when the corresponding directories exist.*

The indexes `diag/_index_diag.md` and `test/_index_test.md` follow the skeleton of 03.01. Specifics:

- Registry: tables by domain subfolders (one per `<domain>`); columns - path, type/purpose, when to apply; the first column is the path with the domain (`<domain>/<domain>_<type>_<action>.<ext>`); files live in domain subfolders, the name follows the mask `<domain>_<type>_<action>` (`project_standards.md`, 01.01.04)
- Separate doc files for scripts are not created - the script description lives in the index
- The routing map connects a task type (what to check, what to diagnose) to the script

---

## 06.06. Change request index

*Mandatory when the `doc/change_requests/` directory exists.*

`doc/change_requests/_index_change_requests.md` is the entry point to the change request directory, following the skeleton of 03.01. Composition: a request registry (file, topic, status, execution) and a routing map. It is maintained by the agent manually on any composition change - creation, status change, transfer to a live specification, archiving, rejection; the `glob-update-indexes` skill does not regenerate it. Document skeleton, lifecycle, and transfer to a live specification - `change_request_standards.md`; archived requests (`.arch/`) are not reflected in the registry.

---

## 07.01. Purpose and language

*Mandatory.*

`AGENTS.md` is a mandatory AI agent instruction file at the repository root. Language - English by default; another language only on an explicit user request, without mixing languages in one document. When editing, write in the document language.

Content principle: `AGENTS.md` is a router and an excerpt of global canons, not a copy of sources. Common canons are in the static body; everything already recorded in indexes, README, or other documents (full registries, lists, structure tables, versions) is not duplicated in `AGENTS.md` - a pointer to the source of truth is used instead. Volatile content (skill registries, generated lists, anything updated by scripts or synchronization) is always referenced, so the file does not go stale between syncs. The repo-specific part contains only what affects agent behavior: commands, behavioral rules, typical problems.

The package version line `Standard version: X.Y.Z` is mandatory (`project_standards.md`, 07.04). The intro line is `This file contains instructions for AI agents working with this project.`

Header example:

```markdown
# AGENTS.md

Standard version: X.Y.Z

This file contains instructions for AI agents working with this project.
```

---

## 07.02. Session entry points

*Mandatory.*

At the start of `AGENTS.md` - explicit references to repository indexes (the list and formatting rules - 02.02). This is the only place where indexes and `AGENTS.md` overlap in mandatory terms: `AGENTS.md` routes to indexes, indexes route to files. The references are placed in the `## Session Entry Points` section of the static body. The section also states the minimum memory read (`data/memory/memory.md`, `decisions.md`, `env.md` when the directory exists) and the directories the agent ignores: `.backup/`, `.trash/`, `.arch/`, `.opencode/`, `.kilo/`.

---

## 07.03. AGENTS.md and CLAUDE.md policy

*Mandatory.*

1. Only `AGENTS.md` maintains agent instructions; the primary target tool is opencode, compatible consumers are other ecosystem tools (Kilo Code, Cursor; Claude Code reads `AGENTS.md` by default when there is no `CLAUDE.md` in the project directory and above; when `CLAUDE.md` exists, only it is read - loading is controlled by the Project instructions setting; actual behavior is checked against the installed tool version)
2. `CLAUDE.md` is **not maintained** and not created by default. If a repository has `CLAUDE.md` - delete it during `AGENTS.md` synchronization (the `hub-sync-agents` skill); move valuable content to `AGENTS.md` before deletion
3. The exception is a repo override on an explicit user request: then `CLAUDE.md` is maintained as a mirror of `AGENTS.md`. The mirror reference is the hub `CLAUDE.md`. Mirror copies match except for the H1 title and the purpose line: `AGENTS.md` uses `This file contains instructions for AI agents working with this project.`, `CLAUDE.md` uses `This file contains instructions for Claude Code working with this project.`. Any change to one file is made synchronously in the other. `AGENTS.md` is the primary file
4. Language - English by default; another language only on an explicit user request, without mixing languages in one document
5. The `project_standards` hub permanently maintains `CLAUDE.md` as the mirror reference - without an entry in `doc/specs/overrides.md`; derivative repositories follow the general policy (not maintained, override on explicit request)

---

## 07.04. Layers and content principle

*Mandatory.*

The `AGENTS.md` structure is not invented from scratch - it uses the skeleton of 07.06. The file is divided into layers by markers (technical synchronization identifiers, Latin):

- From `<!-- START static -->` to `<!-- END static -->` - the common body, identical in all repositories. Content: version, session entry points, language matrix, development process, safety, git, mirror policy, boundaries. Edited only in the hub; derivative projects receive it through package synchronization and do not edit it there
- From `<!-- START repo-specific -->` to `<!-- END repo-specific -->` - repository specifics: purpose, commands, structure, skills, specifics. Filled in locally
- From `<!-- START generated-commands -->` to `<!-- END generated-commands -->` - a block inside the repo-specific part for machine-generated commands. Regenerated by a script or skill; handwritten sections around it are not changed. A permanent element of the block is the package integrity gate activation: `git config core.hooksPath .githooks` (`project_standards.md`, 06.01)

The machine layer is the OpenCode global file `~/.config/opencode/AGENTS.md`. It is optional and, when present, takes precedence over the static block. The static block is self-sufficient for sessions without that layer and must not contradict it. The duplication is intentional: the static block stays self-sufficient without the layer. This applies to the typography rules and the language split. The canon for both is `project_standards.md` (04.03).

The static block has exactly four H2 sections (07.05). The repo-specific block starts with `## Repository Specifics: <name>`; `## References` follows after `<!-- END repo-specific -->`.

---

## 07.05. Section taxonomy

*Mandatory.*

The order and names of sections are fixed; language - English.

| Section | Layer | Purpose |
| ------- | ----- | ------- |
| Session Entry Points | static | session entry points (standards, skills, specifications indexes); agent memory `data/memory/memory.md` when the directory exists; ignored directories; index auto-update on tagging without a task |
| Language & Typography Matrix | static | Russian human contour (chat, README, specs, plans, CR, UI via `t()`) versus English agent and code contour (code, comments, docstrings, technical logs, commits, agent documents, standards, skills); typography rules; duplication follows from static-block self-sufficiency (07.04); optional machine layer; takes precedence when present; no contradiction between the machine layer and the static block for typography and the language split; references to `~/.config/opencode/AGENTS.md` and `human_text_standards.md` |
| Development Process | static | mandatory superpowers skills; task classification (Spike / Bounded / Architectural); Russian specs and plans; isolated task delegation; fact-checking cascade |
| Safety, Git & Boundaries | static | approval gate; `.trash/` quarantine; sudo levels; git branch, commits, authorship; no AI mention; no package version bump without a request; `CLAUDE.md` mirror policy |
| Repository Specifics | repo-specific | all repository-specific subsections: purpose, structure, skills, commit scopes, specifics |
| References | - | indexes, standard sections, https://agents.md |

---

## 07.06. Skeleton

*Mandatory.*

```markdown
<!-- START static -->
# AGENTS.md

Standard version: X.Y.Z

This file contains instructions for AI agents working with this project.

## Session Entry Points

- `@doc/standards/_index_standards.md` - standards package index (registry, routing map, package version); read it first
- `@doc/skills/_index_skills_hub.md` (hub) or `@doc/skills/_index_skills_repo.md` (derivative repositories) - skill index
- `@doc/specs/_index_specs.md` - specifications index
- `data/memory/memory.md`, `data/memory/decisions.md`, `data/memory/env.md` - agent memory minimum when `data/memory/` exists; update it after significant decisions
- Ignore `.backup/`, `.trash/`, `.arch/`, `.opencode/`, `.kilo/` unless the user explicitly asks
- Tagging an `@_index_*.md` file without a task runs its index auto-update procedure

## Language & Typography Matrix

| Contour | Artifacts | Language |
| --- | --- | --- |
| Human | Chat responses, `README.md`, user guides, `doc/specs/`, implementation plans, `doc/change_requests/`, UI and console text through `t()` | Russian |
| Agent and code | `AGENTS.md`, `CLAUDE.md`, standards, indexes, skills, code, comments, docstrings, technical logs (`logger.*`), commit messages, subagent communication | English |

Typography applies to both contours: hyphen-minus `-` only (no em dash or en dash), letter `е` without diaeresis, no ellipsis, no emoji, no exclamation marks, no non-breaking or narrow spaces. User-facing text follows `doc/standards/human_text_standards.md`; the machine override is `~/.config/opencode/AGENTS.md`; the core rule is `project_standards.md` (04.03). This block is self-sufficient and keeps the rules for sessions where the machine layer is absent. When the machine layer is present, it takes precedence over this block; the two texts must not contradict. Do not remove the rules as duplicates.

The language split in the table above is self-sufficient and applies when the machine layer is absent. When the machine layer is present, its `## Language` section takes precedence on conflict; the two texts must not contradict.

## Development Process

- Use the superpowers skills: `brainstorming` (design exploration and task classification), `writing-plans` (specs and implementation plans), `test-driven-development`, `systematic-debugging`, `subagent-driven-development` or `executing-plans`, `verification-before-completion`, `writing-skills`.
- Classify work as Spike, Bounded, or Architectural before implementation; ratchet up when hidden complexity appears.
- Write specifications and plans in Russian; keep them in `doc/specs/` (`init/` before MVP, `spec_<module>.md` after).
- Delegate isolated search, audit, and verification work to subagents; briefs and answers are English, the user summary is Russian.
- Fact-checking cascade: local code and standards -> `context7` MCP -> `github` MCP -> web search for exact error text -> ask the user when unverifiable.

## Safety, Git & Boundaries

- Mutate code or the system only after the execution trigger `ДЕЛАЙ` or `GO`; design-stage approvals inside `brainstorming` do not replace it.
- Delete repository files only by moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` with `MANIFEST.md`; exceptions: `tmp/` contents, git-native mirror/package synchronization, and `.trash/` purged only on explicit request.
- Run `sudo`, `su`, and `pkexec` only per the privilege levels in `project_standards.md` (05.04); never hardcode secrets.
- Git: one `master` branch; English Conventional Commits `<type>(<scope>): <imperative summary>`; authorship from `whoami` and `hostname`; no AI mention; never bump the package version without an explicit request.
- `CLAUDE.md` mirror: maintained permanently in the hub; deleted by default in derived repositories unless a repo override exists.
<!-- END static -->

<!-- START repo-specific -->
## Repository Specifics: <repo-name>

### Purpose

<repo purpose - source of truth>

<!-- START generated-commands -->
<setup, run, tests, lint - regenerated block>
Activate pre-commit after cloning (before the first commit, on every machine): `git config core.hooksPath .githooks`
<!-- END generated-commands -->

### Structure

<behavioral structure rules (what is edited, where noise); full folder and file table - in README.md>

### Skills

<only skills used in commands and session start; full registry - in the skills index>

### Commit Scopes

<project scopes>

### Specifics

<typical issues not covered by other documents: hook nuances, check specifics, cross-document dependencies>
<!-- END repo-specific -->

## References

- doc/standards/_index_standards.md - standards registry and versioning policy
- doc/standards/index_nav_standards.md - navigation document canon (indexes, AGENTS.md skeleton)
- doc/standards/repo_info_doc_standards.md - README and human document canon
- https://agents.md - canonical format
```

---

## 08.01. Related documents

| Document | Relation |
| -------- | -------- |
| `doc/standards/project_standards.md` | Core standard; source hierarchy and text rules (07.06, 04.03) |
| `doc/standards/repo_info_doc_standards.md` | Human document canon; boundary - README and descriptions for humans versus agent indexes |
| `doc/standards/software_doc_standards.md` | Installation document template for documentation repositories |

---

## 08.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and routing map - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
