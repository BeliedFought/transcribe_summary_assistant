# Anthropic Agent Skills Standards. Version 5.2.0

This document is the single skill canon for the package. It defines the Anthropic Agent Skills format: a skill directory with a mandatory `SKILL.md`, YAML frontmatter, progressive disclosure, nested files, and scripts. It also defines the four-type taxonomy, the closed ten-category dictionary, naming, distribution, and verification. It supplements `doc/standards/project_standards.md` and applies on top of it.

The package has one skill format: a directory `<name>/SKILL.md`. New skills are created in this format only. Legacy flat skill files (`doc/skills/<name>.md` or `doc/skills/<repo-name>/pg_<name>.md`) may remain in sibling repositories until migrated; they are not created in the hub and do not form a second format.

All core requirements remain in force unless this document explicitly overrides them.

---

## Table of Contents

**01. Fundamentals:** 01.01 Purpose and applicability - 01.02 Skill model - 01.03 Skill location - 01.04 Skill directory, naming, types, and categories

**02. Metadata:** 02.01 YAML frontmatter - 02.02 Progressive disclosure - 02.03 `description` field

**03. Content:** 03.01 SKILL.md body - 03.02 Nested files - 03.03 Scripts - 03.04 Root commands and execution confirmation - 03.05 Configuring skills: apply-script skeleton - 03.06 Artifact directories in scanned trees

**04. Application:** 04.01 Skill activation by the agent - 04.02 Legacy flat skills and migration

**05. Other:** 05.01 Anti-patterns - 05.02 Example - 05.03 Author checklist - 05.04 Skill development and verification

**06. Relations and versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Purpose and applicability

*Mandatory.*

Agent Skills is Anthropic's open specification for packaging instructions, knowledge, and scripts into a skill that an AI agent discovers from metadata and applies on request. The ecosystem supports the format: Claude Code, Claude.ai / Anthropic API, opencode, and other tools read `SKILL.md`.

The primary target tool of this standard is **opencode**: SKILL.md skills are created first of all for it. Sources live in the shared `doc/skills/` directory (subdirectories with `SKILL.md`); deployment to live opencode directories is a separate process (01.03). Claude Code, and other ecosystem tools are compatible consumers of the same format; the Anthropic specification remains the primary source.

Apply this standard when:

- a skill is created for a tool that expects the `SKILL.md` format (a skill directory);
- a skill will be distributed outside the repository: publication, plugin, shared registry;
- an existing third-party SKILL.md skill must be brought to canon before use;
- a skill is needed in one repository only and must stay outside directory synchronization - place it in `data/skills/` (01.03).

This document is the single skill canon: it covers all four types (`hub_loc`, `hub_glob`, `pr_glob`, `pr_loc`). Before creating or editing a skill in `doc/skills/` or `data/skills/`, the agent checks this document.

---

## 01.02. Skill model

An Anthropic skill is a **directory** with a mandatory `SKILL.md` file and optional resources. Three layers:

| Layer | Content | Use |
| ----- | ------- | --- |
| Metadata | frontmatter: `name`, `description` | Always in the agent context; used to select the skill |
| Body | Markdown instruction in `SKILL.md` | Loaded in full when the skill activates |
| Resources | `reference.md`, `examples.md`, templates, `scripts/` | Read or executed on demand |

Activation mechanics: the request matches `description`; the agent loads the body, follows the instruction, reads resources when needed, and runs scripts with tools (Bash and others).

**Format decision:**

| Case | Format |
| ---- | ------ |
| Any new skill | SKILL.md directory (this document) |
| Target tool reads only `SKILL.md` | SKILL.md directory (this document) |
| Skill is published or reused across tools | SKILL.md directory (this document) |
| Legacy flat skill file in a sibling repository | Migrate to SKILL.md (04.02); do not create new flat files |

---

## 01.03. Skill location

**The skill source lives in the repository**, not in live tool directories - in the shared skill directory `doc/skills/`:

```text
doc/skills/
├── glob-skill-deploy/          # global skill: prefix glob-, type hub_glob
│   ├── SKILL.md
│   └── templates/
│       └── data_template.md    # data template only
├── hub-sync-standards/         # hub skill: prefix hub-, type hub_loc
│   └── SKILL.md
├── pg-parse-report/            # project skill: prefix pg-, type pr_glob (in a derivative repo)
│   └── SKILL.md
└── ext/                        # aggregate of external project skills (hub only)
    └── my_repo/
        └── pg-fill-forms/      # project skill (pg-)
            └── SKILL.md
```

**Skill types and distribution.** The slug and the prefix are independent: the slug is the canonical term and the `metadata.type` value; the prefix is the type marker in the directory name.

| Type | Slug (`metadata.type`) | Prefix | Location | Synchronization |
| ---- | ---------------------- | ------ | -------- | --------------- |
| Hub skill | `hub_loc` | `hub-` | `doc/skills/` root, hub only | Hub only |
| Global skill | `hub_glob` | `glob-` | `doc/skills/` root | Hub to all repositories |
| Project skill | `pr_glob` | `pg-` | `doc/skills/pg-<name>/` | Repository to hub (`ext/<repo-name>/`) |
| Local skill | `pr_loc` | `pl-` (optional) | `data/skills/` | None |

Rules:

- The `doc/skills/` directory holds SKILL.md directories only. Legacy flat files from sibling repositories may exist there until migration; do not create new ones.
- One skill - one directory; the directory contains exactly one `SKILL.md` and the skill resources (01.04).
- Distribution mirrors the type: `glob-` is a global skill (`hub_glob`), maintained in the hub and distributed to all repositories by the `hub-sync-skills` skill; `hub-` is a hub skill (`hub_loc`), hub only; `pg-` is a project skill (`pr_glob`), aggregated in the hub under `doc/skills/ext/<repo-name>/`; `pl-` is a local skill (`pr_loc`), `data/skills/` only.
- Subdirectory distinction: a skill directory contains `SKILL.md` at its root; a repository folder `<repo-name>/` (in the hub - under `ext/`) contains legacy flat files and `pg-<name>/` subdirectories, without its own `SKILL.md`. A collision between a skill directory name and a repository folder name is a stop: agree the name with the user.
- Skill directories are versioned in git with the project and carried into derivative repositories as project artifacts.
- A skill is registered in the skill index: in the hub - `_index_skills_hub.md`, in a derivative repository - `_index_skills_repo.md` (index maintenance - `index_nav_standards.md`; updates - the `glob-update-indexes` / `hub-sync-indexes` skills).

**Single editable source.** `SKILL.md` is the only editable source of a skill. `templates/` holds data templates (for example `pip_mirrors.md`), artifact blanks, and static reference material only; it never holds a parallel skill file or a plain-format source. There is no format pair and no migration copy: edit `SKILL.md` directly.

**Local skills (`pr_loc`) - `data/skills/`.** A skill needed in one repository only and not subject to synchronization lives outside `doc/skills/` - in `data/skills/`. New local skills are created as SKILL.md directories only; legacy flat files may remain in sibling repositories until migrated:

```text
data/skills/
├── pl-extract-emails/         # local Anthropic skill: prefix pl-
│   ├── SKILL.md
│   └── scripts/
│       └── extract.py
└── extract_emails.md          # legacy local flat skill: migrate to SKILL.md
```

The `hub-sync-skills` skill traverses only `doc/skills/`, so `data/skills/` is unaffected by synchronization: it is not aggregated in the hub (`ext/<repo-name>/`), not distributed, and not mirrored. Rules:

- New local skills: directory `SKILL.md` only. The name uses the `pl-` prefix (`pl-<name>/SKILL.md`) or no prefix; naming rules - 01.04; membership in `data/skills/` means "outside synchronization".
- Legacy flat local files are allowed only in sibling repositories and only until migration (04.02).
- The directory is committed to git: add the exception `!data/skills/` to the ignored `data/` folder in `.gitignore` (`project_standards.md`, 06.01).
- It is not included in the summary skill indexes (`_index_skills_hub.md`, `_index_skills_repo.md`) - they are built only from `doc/skills/`; local skills are reflected in their own index `data/skills/_index_skills_pl.md` (generated by `glob-update-indexes`; `index_nav_standards.md`, 06.02).

**Deploy is a separate process.** Tool directories are deployment targets, not source storage. Copying a skill from `doc/skills/<name>/` to a live directory is a standalone operation governed by the target tool documentation; this standard does not regulate it. The principle is the same as in `deploy_standards.md`: the repository is the source, installation is a separate process (templates live in the repository, install scripts copy them during deployment).

Deployment target reference (where to copy during deployment):

| Tool | Project | Personal |
| ---- | ------- | -------- |
| opencode | `.opencode/skills/<name>/SKILL.md` | `~/.config/opencode/skills/<name>/SKILL.md` |
| Claude Code | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` |
| Cross-tool registry | - | `~/.agents/skills/<name>/SKILL.md` |

Claude Code plugin skills are published in the plugin structure and follow its documentation; this is also deployment, not source storage.

---

## 01.04. Skill directory, naming, types, and categories

Recommended directory structure:

```text
my-skill/
├── SKILL.md          # mandatory: overview and navigation
├── reference.md      # detailed documentation - on demand
├── examples.md       # usage examples - on demand
├── templates/        # data templates and artifact blanks only (01.03)
└── scripts/
    └── helper.py     # all executable skill code - executed, not read
```

**Skill name (`name`, directory name):**

| Rule | Example |
| ---- | ------- |
| Lowercase Latin letters, digits, hyphens | `glob-render-chart` |
| Must not start or end with a hyphen, no double hyphens | `glob-render-chart`, not `-glob-render` / `glob-render-` / `glob-render--chart` |
| Up to 64 characters | - |
| Matches the directory name | `glob-render-chart/SKILL.md` |
| English words, no transliteration | `parse-report`, not `razbor-otcheta` |
| Reflects the task, not generic words | `pdf-fill-form`, not `helper` |
| Unique within the tool installation | - |
| Prefix `glob-` / `hub-` / `pg-` / `pl-` marks the type (01.03); for local skills (`pr_loc`) the prefix is optional | `glob-skill-migrate-anthropic` (global, `hub_glob`); `pg-<name>` - project (`pr_glob`); `pl-<name>` or `<name>` - local (`pr_loc`, in `data/skills/`); `hub-<name>` - hub (`hub_loc`) |
| Category is the second level of the prefix: `<prefix>-<category>-<name>`; the slug comes from the closed dictionary below and matches `metadata.category`; `<prefix>-<category>` is allowed when the name equals the slug; for a local skill without a prefix the category is the first segment: `<category>-<name>` | `glob-cfg-pip` (global, `cfg`); `glob-update-indexes` (`update`); `hub-update` (`update`); `cfg-kde` (local, `cfg`) |

**Closed category dictionary.** A category is optional. The slug is taken only from this table; `category_name` is only the corresponding name. A new slug is added by editing this standard in the hub; local categories, synonyms, and renamed names are forbidden. Legacy Russian category names from sibling repositories are accepted only during transition; new skills use the English names.

| Slug (`metadata.category`) | Name (`metadata.category_name`) |
| -------------------------- | ------------------------------- |
| `sync` | Sync |
| `update` | Update |
| `audit` | Audit |
| `skill` | Skills |
| `cfg` | Configuration |
| `rules` | Agent Rules |
| `shell` | Terminal Settings |
| `git` | Git Settings |
| `ssh` | SSH Settings |
| `mine` | Knowledge Mining |

Rules:

- The slug is the second level of the directory name: `glob-cfg-pip` -> `metadata.category: cfg`; the abbreviation `<prefix>-<category>` is allowed when the name equals the slug (`hub-update`). For a local skill (`pr_loc`) without a type prefix, the category occupies the first name segment: `cfg-kde` -> `metadata.category: cfg`.
- The category fields are optional and are filled only as a pair; `category_name` is strictly the name from the dictionary.
- Without a category, the name consists of the type prefix and the skill name (`glob-<name>`, `pg-<name>`), the category fields are empty, and the corresponding name segment must not match any dictionary slug.
- Type and category are independent: the first sets distribution and location, the second sets the application domain.

**Nested files:** Latin characters, `snake_case` or `kebab-case`, no Cyrillic and no spaces in names. Nesting `scripts/` inside the skill directory is allowed; skills inside skills are not. `templates/` stores data templates only and keeps their original names.

---

## 02.01. YAML frontmatter

*Mandatory.*

Metadata block at the start of `SKILL.md`. The Agent Skills specification defines a **strict six-key allowlist**; on the packaging and loading paths defined by the specification (claude.ai, API, skill registries) an unknown key is an error. Tools may extend the list with their own fields (second table below).

```yaml
---
name: glob-render-chart
description: Renders a chart image from a CSV file. Use when the user asks to visualize tabular data, plot a graph, or create a chart from CSV
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)
license: MIT
metadata:
  version: 1.2.0
  status: stable
  type: hub_glob
  category: cfg
  category_name: Configuration
---
```

**Agent Skills specification keys:**

| Field | Requirement | Rule |
| ----- | ----------- | ---- |
| `name` | required by the specification | Skill name; rules in 01.04. The field is set explicitly in every package skill |
| `description` | required | Up to 1024 characters; canon - 02.03. Determines skill discovery by the agent |
| `allowed-tools` | optional | Tool permissions for the skill with script path prefixes; removes redundant confirmation prompts |
| `license` | optional | License for distribution |
| `metadata` | optional | Arbitrary dictionary for custom fields (`version`, `status`, `type`, and others) |
| `compatibility` | optional | Compatibility limits (tool, version) |

**Skill type.** The type from the taxonomy (`hub_loc`, `hub_glob`, `pr_glob`, `pr_loc` - 01.03) is recorded in the skill header - in `metadata.type`. A top-level `type` field in frontmatter is forbidden (strict allowlist). The slug corresponds to the directory name prefix: `hub_loc` - `hub-`, `hub_glob` - `glob-`, `pr_glob` - `pg-`; for `pr_loc` the prefix is optional - `pl-` or a name without a prefix (in `data/skills/`). Set the field at creation and keep it current on update.

**Skill category.** The application domain is recorded in `metadata.category` (a slug from the closed dictionary) and `metadata.category_name` (the name from the same dictionary) - 01.04. The fields are optional and filled only as a pair; `category_name` is strictly the dictionary name, local synonyms are forbidden.

**Index maintenance fields.** `metadata.purpose` and `metadata.topic` are optional fields consumed by `glob-update-indexes` when it rebuilds a skill index. `metadata.purpose` overrides the first sentence of `description` as the registry purpose and must be a complete factual sentence cut only at a sentence boundary. `metadata.topic` sets the routing-map topic from the user task perspective with trigger synonyms and overrides the colon-head fallback. Both fields live in the arbitrary `metadata` dictionary allowed by the specification; a generated index cell is not a storage for edited wording, the next rebuild replaces it (`index_nav_standards.md`, 03.03 and 04.02).

**Tool extensions** (outside the specification; work in a tool that supports them but do not pass strict packaging - do not use in distributed skills):

| Field | Tool | Rule |
| ----- | ---- | ---- |
| `disable-model-invocation` | Claude Code | `true` - the skill is invoked by the user explicitly only, the agent does not apply it on its own. Destructive skills - always `true` |

Package-internal fields (`id`, `auto_apply`, and others) are forbidden in SKILL.md; the index maintenance fields `metadata.purpose` and `metadata.topic` are the only exception. The `argument-hint` field is valid for Claude Code commands but not for skills.

---

## 02.02. Progressive disclosure

*Mandatory.*

The three-level loading principle saves agent context:

| Level | Content | When in context |
| ----- | ------- | --------------- |
| 1 | `name` + `description` | Always (metadata of all installed skills) |
| 2 | `SKILL.md` body | When the skill activates (request match or explicit invocation) |
| 3 | nested files: `reference.md`, `examples.md`, templates | When read through a body reference |

**Rules:**

- Keep level 1 minimal: a short, precise `description`; the full volume goes below.
- The body (level 2) does not duplicate resource content: only references and reading conditions ("read `reference.md` before the first API X request generation").
- Resources (level 3) load only when needed: examples for a non-standard case, reference for API code generation.
- Scripts at level 3 are not read as text - they are executed (03.03).
- Recommended body size - up to 500 lines; move excess to `reference.md` / `examples.md`.

---

## 02.03. `description` field

*Mandatory.*

The only field by which the agent finds a skill. Canon:

- third person, "what and when" narration;
- first what the skill does (WHAT), then when to apply it (WHAT -> WHEN);
- application conditions - concrete wording from real requests: "Use when the user asks to visualize tabular data"; these are not action launch triggers (`ДЕЛАЙ` / `GO`, `project_standards.md` 07.02);
- request keywords explicitly in the text;
- up to 1024 characters; no marketing, no "powerful / easy to use";
- retelling the process and step-by-step method is forbidden: the agent follows the description instead of reading the skill body. Description canon (skill description object, SDO) and rationale - `superpowers:writing-skills`; target size - under 500 characters;
- for a disciplining skill - a precursor symptom of violation (for example "when the code is already written before the test", "when the edit seems too simple to check").

| Bad | Good |
| --- | ---- |
| `Helps with PDFs` | `Fills PDF forms from structured data. Use when the user mentions filling a form, completing a PDF application` |
| `Code review assistant` | `Reviews code for best practices and potential issues. Use when reviewing code, checking PRs, or analyzing code quality` |
| `Useful report helper` | `Builds monthly sales reports in XLSX. Use when the user asks for a sales report, monthly summary, or revenue breakdown` |

---

## 03.01. SKILL.md body

*Mandatory.*

The body is the instruction for the agent, loaded when the skill activates. Recommended section structure (order matters, do not create empty sections):

```markdown
# <title>

Brief overview: what the skill does and what result is expected.

## When to use
- <condition_1>
- <condition_2>
- <condition_3>

## Instructions
1. <step_1>
2. <step_2>

## Examples
1-2 pairs "request -> expected action"

## References
- reference.md - read before <condition>
- scripts/render.sh - call for <action>
```

**Content and style:**

- Imperative: instructions as direct orders, without "perhaps one should consider".
- Concise: no retelling of basic model knowledge and no tutorial explanations.
- One skill - one scenario; unrelated scenarios get separate skills.
- No time-sensitive data (library versions, dates) - put it in `reference.md` with an update obligation.
- Terms are consistent across the skill; one entity - one name.
- "When to use" states the application conditions. A separate "Trigger words" section and verbal synonyms of launch triggers are not allowed: launch triggers are only `ДЕЛАЙ` and `GO` (`project_standards.md`, 07.02).
- Detail level follows task fragility: migrations and deploy - exact commands; review and analysis - principles and a checklist.
- Language of headings, body, and `description` is uniform and **English** by default for every `doc/skills/**` skill (`project_standards.md`, 04.03). Russian is allowed in user-facing templates, examples, report blocks, and script output when the project locale or an override selects it; the package does not cement one language. Legacy team skills may keep a Russian body until migration; mixing languages in headings and body is forbidden.
- The body is text only. Allowed fenced blocks are of two kinds: invocation commands for the skill's own scripts and resources (paths from `${CLAUDE_SKILL_DIR}`) and non-executable schemes (frontmatter structure, directory tree, markup templates). Executable operation code - shell command sequences, programs, SQL - is forbidden in the body: all code goes to `scripts/` (03.03).
- Do not mention concrete skills from concrete repositories: names of other repositories, `doc/skills/ext/<repo>/` paths, and real project skills of neighbors are forbidden. Only placeholders (`<repo-name>`, `pg-<name>`, `pl-<name>`, `glob-<name>`) and generalized examples; references to neighboring skills of the same repository are allowed.
- Placeholders are Latin only (`<name>`, `<dir-name>`, `<repo-name>`); Cyrillic inside angle brackets is forbidden (`project_standards.md`, 04.03).

---

## 03.02. Nested files

*Mandatory.*

Resource files of the skill directory. The agent loads them on demand - only through a body reference.

| File type | Purpose | When read |
| --------- | ------- | --------- |
| `reference.md` | Detailed documentation: API, data schema, formats, rules | Before code generation or a non-standard case |
| `examples.md` | Extended input and output examples | When the body's basic examples are insufficient |
| `templates/` | Data templates and artifact blanks: configs, document skeletons | When the skill creates an artifact |
| `scripts/` | All executable skill code | Executed, not read (03.03) |

**Rules:**

- The `SKILL.md` body states an explicit reading condition for every resource: which file, when to open it. A resource without a reading condition is not used.
- Paths to skill directory files use `${CLAUDE_SKILL_DIR}` (or the tool equivalent), not absolute machine paths.
- Resources are self-sufficient: the basic scenario must work without mandatory reading of `reference.md`; the reference is a deepening, not a precondition.
- Duplication between the body and resources is forbidden: the body is a short version and a reference, the resource is the full version.

---

## 03.03. Scripts

*Mandatory.*

The skill says "when", the script says "how": all executable skill code lives in `scripts/` and is invoked from the body; the body contains no logic. Only invocation commands (paths from `${CLAUDE_SKILL_DIR}`) and non-executable schemes are allowed in the body (03.01).

**Package self-sufficiency.** The skill directory is transferred as a whole: the copied folder works on any machine without the source repository. Therefore:

- scripts do not depend on source project code or paths - only `${CLAUDE_SKILL_DIR}` and passed arguments;
- external project scripts and modules the skill relies on are moved into the package: the working copy goes to `scripts/`; do not keep a second source copy in `templates/`; if other consumers of the script exist outside the skill, stop and ask the user;
- inline source code (fenced blocks) is moved to `scripts/` in full, with no length threshold.

This rule is stricter than the Anthropic canon (the specification allows inline code in the body); it is a deliberate local portability requirement recorded by this standard (06.01).

**Script requirements:**

- Executability: execute permission, shebang, dependencies described in the body or a resource.
- Safety: arguments through parameters, no side effects beyond the task, destructive actions only behind an explicit flag.
- One script - one operation; output is compact, to stdout or an artifact file.
- Script output and text follow `cli_output_standards.md`: human status uses `report` (header, key-value block, steps `[n/m]`, `Result`, `error:` on stderr); logs and parsable streams use `plain` (`YYYY-MM-DD HH:MM:SS [marker] message`, the time inserted by the script itself, monochrome, no ANSI, no frames, no separator lines, markers `[!]` / `[i]` / `[*]`; no `src/logger.py`, no log files, no `log` folder); automation uses `--porcelain`. English is the default; Russian is allowed through the project locale or an override (04.03). Typography: no trailing period, no diaeresis letter, hyphen-minus U+002D only, no ellipsis; one line - one message (04.04.02); exit codes 0 / 1 / 2 - success / execution error / usage error (05.03).
- Remove tool confirmations with a prefix in `allowed-tools`:

```yaml
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)
```

- Invocation from the body:

```markdown
Run `${CLAUDE_SKILL_DIR}/scripts/render.sh <csv-file>` to render the chart.
```

- Scripts do not rely on the current working directory - only on `${CLAUDE_SKILL_DIR}` and passed arguments.

---

## 03.04. Root commands and execution confirmation

*Mandatory for skills with privileged operations.*

A skill whose application performs privileged operations (changing system configs, installing packages, managing system services) must contain a dedicated root-commands section in the body. The canonical heading is `## Root Commands and Execution Confirmation`; a legacy Russian-language skill uses `## Root-команды и подтверждение выполнения` until migration. The section describes the application levels and mandatory waiting rules for the agent; the general privileged-operation procedure is in `project_standards.md`, 05.04, and the point override is 01.01.02. A skill without privileged operations does not contain this section.

Privileged action application levels:

- level 0 - a human at the terminal: on an explicit user request in the current session the agent starts the script under a pseudo-terminal (tmux or screen), the user enters the password at the `sudo` prompt; the agent neither shifts the launch to the user nor elevates privileges itself;
- levels 1-3 under an active project override of `project_standards.md` 05.04: the script applies changes itself - GUI askpass, a narrow `NOPASSWD` rule, or a file askpass; the agent does not shift this work to the user;
- manual path: if no level applies, the commands are passed to the user; the agent does not run sudo itself.

Mandatory rules for the agent (stated in the skill body):

- after giving the user commands, the agent does not consider them executed: it waits for explicit user confirmation or an objective state check (repeated `recon` or `status`, reading the target file or value);
- before confirmation or verification the agent does not move to the next item or the next skill and does not finish the cycle;
- if the state cannot be checked without root, the agent requests confirmation and the exact check command;
- the agent reports the item outcome (applied or not applied) only from a confirmed or verified state.

The reference behavior of the script itself at levels 1-3 under an active override (self-elevation with `sudo -A` or a `sudo -n` call with condition checks and recursion protection, series pre-authorization, objective state re-check after the run, sudo environment traps) is in `project_standards.md`, 05.04.

---

## 03.05. Configuring skills: apply-script skeleton

*Mandatory for skills that manage runtime environment configuration.*

A skill that applies a set of settings to an environment (application configs, system parameters) follows a single skeleton:

- Declarative item registry: identifier, title, description, root flag; logic lives in the registry, not in subcommand code
- Per-item function contract: reason for unavailability, idempotent applied check, current and target values
- CLI subcommands: environment and precondition recon, "now - will be" plan, status, apply (with `--dry-run`, explicit item selection, and batch mode), state snapshot, root-item confirmation, output of root commands to the user
- The applied-state snapshot is kept as an artifact in the project `diag/` (core standard, 01.01.04): an "item - value - date" table and a change history; the record is merged idempotently, without duplicates
- Confirmation of root items whose state is unreadable without root is recorded in the snapshot by a separate subcommand: subsequent runs trust the snapshot without asking the user again
- Series of similar skills: only skills with `stable` status participate (draft is skipped silently), the order is alphabetical, the composition is checked against the index; an item failure does not stop the pass, unconfirmed root commands block the transition to the next skill
- The state snapshot in `diag/` records the applied environment state and does not replace agent memory: persistent cross-session context is `data/memory/` per `doc/standards/memory_standards.md`

---

## 03.06. Artifact directories in scanned trees

*Mandatory for skills that install files and directories into loader-scanned trees.*

Tools scan their directories (plugins, skills, autostart) and recognize any content, including backups:

- Backups and quarantine are not placed inside a scanned tree: a copy is recognized as a duplicate and breaks the canonical instance (identifier conflict, duplication); copies are placed next to the tree, outside scanning
- Updating an artifact directory by copying over it does not replace it but nests the new version inside the old one; update by replacing the directory as a whole; nesting after update is an error
- A generated file over a possibly user file is marked with an ownership marker in the first line; an existing file without a marker is considered user-owned - overwrite only with an explicit flag

---

## 04.01. Skill activation by the agent

*Mandatory.*

Two activation paths:

1. **Automatic** - the user request matches `description`; the agent loads the body and applies it. Impossible with `disable-model-invocation: true` (Claude Code extension, 02.01).
2. **Explicit** - the user invokes the skill directly (tool command, name mention).

**Rules:**

- A skill without `description` is not discovered automatically; fill it in (02.03).
- Destructive skills (deletion, overwrite, deploy, migrations) - `disable-model-invocation: true` (Claude Code extension), explicit invocation only. In tools without this field - forbid auto-application and require explicit invocation by name in the skill body.
- When several matches conflict, explicit invocation wins; at equal specificity the agent asks the user and does not merge instructions from different skills.
- Skill actions do not contradict the core project standard and confirmed constraints.

---

## 04.02. Legacy flat skills and migration

*Mandatory when a legacy flat skill is found.*

A legacy flat skill is a single `.md` file: `doc/skills/<name>.md`, `doc/skills/<repo-name>/pg_<name>.md`, or `data/skills/<name>.md`. Such files may exist in sibling repositories. In the hub and in new work they are not created: `SKILL.md` is the single editable source (01.03).

Migration is one-way and mechanical: map the fields per the table, bring the section structure to 03.01, and write `SKILL.md`. The process is automated by the `glob-skill-migrate-anthropic` skill. After migration the legacy flat file is archived per repository rules; it is not moved into `templates/` and is not kept as a parallel source.

| Aspect | Legacy flat skill | SKILL.md |
| ------ | ----------------- | -------- |
| Skill unit | one `.md` file | `<name>/SKILL.md` directory |
| Identifier | `id` = file name without `.md` | `name` = directory name |
| Auto-application | `auto_apply: true / false` | `disable-model-invocation: false / true` (inversion; Claude Code extension) |
| Destructive | `auto_apply: false` | `disable-model-invocation: true` (Claude Code extension) |
| Custom metadata | `version`, `status` | `metadata` dictionary |
| Skill type | frontmatter `type` | `metadata.type` |
| Category (application domain) | `category` + `category_name` | `metadata.category` + `metadata.category_name` |
| Tool permissions | none | `allowed-tools` |
| Skill resources | external (`run/`, `doc/specs/`) | inside the directory (`reference.md`, `scripts/`) |
| Skill code | inline code in the body allowed (up to ~100 lines) | all executable code in `scripts/`, invocation commands in the body (03.03) |
| Size limit | 800 lines | 500-line body |
| Language | project language | English default, uniform for headings, body, and description; Russian allowed by project override; fully English for ecosystem publication |
| Storage directory | `doc/skills/<repo-name>/pg_<name>.md` | `doc/skills/pg-<name>/SKILL.md`; local - `data/skills/pl-<name>/SKILL.md` |
| Frontmatter | required plain fields (including `type`) plus arbitrary extras | strict allowlist (02.01) |

---

## 05.01. Anti-patterns

*Mandatory.*

| Anti-pattern | Correct |
| ------------ | ------- |
| Extra frontmatter key (`id`, `auto_apply`) | Only the allowlist of 02.01; `version` goes to `metadata` |
| The whole API reference in the skill body | Body up to 500 lines; reference in `reference.md` with a reading condition |
| Duplicating a reference file in the body | Body is a short version and a reference |
| Vague description ("helps with docs") | WHAT + WHEN with concrete application conditions (02.03) |
| A "Trigger words" section or verbal synonyms of launch triggers in the body | Application conditions in "When to use"; launch triggers are only `ДЕЛАЙ` / `GO` (`project_standards.md` 07.02) |
| Destructive skill with auto-invocation | `disable-model-invocation: true` (Claude Code extension); in tools without the field - forbid auto-application in the skill body |
| Prose instead of a script for a precise operation | Script in `scripts/`, invocation and `allowed-tools` in the skill |
| Executable code in the SKILL.md body (command sequences, programs) | All code in `scripts/`; the body holds invocation commands and non-executable schemes (03.01, 03.03) |
| Skill dependency on project scripts and modules outside the skill directory | The script is moved into the package: working copy in `scripts/`; the package transfers as one folder (03.03) |
| Absolute machine paths in the body and scripts | `${CLAUDE_SKILL_DIR}` and passed arguments |
| Colored or decorative output in `plain` or `--porcelain` (ANSI colors, frames, emoji); a log line without a timestamp | `report` color follows `cli_output_standards.md`; `plain` lines `YYYY-MM-DD HH:MM:SS [marker] message` - logger strict style without a logger (04.02, 04.04.01) |
| Cyrillic or transliteration in `name` and file names | Latin, `kebab-case` for `name` |
| Arbitrary category or a synonym outside the dictionary; `metadata.category` without `category_name` | Slug and name strictly from the closed dictionary (01.04), filled as a pair |
| One skill for several unrelated scenarios | A separate directory for each scenario |
| Time-sensitive data in the body | Current values; reference material in `reference.md` |
| Source storage in live tool directories; `SKILL.md` outside a skill subdirectory | Source in `doc/skills/<name>/` with `SKILL.md` (01.03); deploy is a separate process |
| A legacy flat skill file kept as a parallel source or moved into `templates/` | `SKILL.md` is the single editable source; `templates/` holds data templates only (01.03, 04.02) |
| Mentions of concrete skills from other repositories in the body and scripts (repository names, `ext/<repo>/` paths) | Placeholders `<repo-name>` / `pg-<name>` / `pl-<name>`; specifics only in skill indexes |
| Cyrillic placeholders (`<имя-каталога>`) | Latin: `<dir-name>`, `<repo-name>`, `<name>` (`project_standards.md`, 04.03) |
| A skill with privileged operations without a root-commands section; the agent moves to the next item before confirmation of passed commands | Mandatory section with levels (pty with password entry / `sudo -A`, `sudo -n`, or file askpass under the 05.04 override / manual) and waiting rules; outcome only from a confirmed or verified state (03.04, `project_standards.md` 05.04) |
| Runtime data in the skill directory: registries, journals, state, cache, updatable lists | The skill directory is a static package; runtime data lives in repository `data/` zones (`doc/standards/skill_data_standards.md`) |
| Mutable data in the SKILL.md body or in `templates/` ("updatable artifact", candidate list, counter) | Registry `data/registries/<domain>.md` with an ownership marker; body and `templates/` are static only (`doc/standards/skill_data_standards.md`) |

---

## 05.02. Example

A minimal complete skill - fully English (03.01). The example is a project skill (prefix `pg-`, slug `pr_glob`).

```text
pg-pdf-fill-form/
├── SKILL.md
└── scripts/
    └── fill_form.py
```

`SKILL.md`:

```markdown
---
name: pg-pdf-fill-form
description: Fills PDF forms from structured data. Use when the user asks to fill a form, complete a PDF application, or populate form fields from JSON or CSV
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/fill_form.py *)
metadata:
  version: 1.0.0
  type: pr_glob
---

# Fill PDF forms

Maps keys from a JSON or CSV file to fields of a PDF form and writes the filled document.

## When to use

- The user asks to fill or complete a PDF form
- The user provides a data file and a blank PDF form
- The user asks to populate form fields from structured data

## Instructions

1. Inspect the form: run the script with `--list-fields <pdf>` to get field names
2. Map data keys to field names; show the mapping to the user if any key is ambiguous
3. Fill the form: `${CLAUDE_SKILL_DIR}/scripts/fill_form.py <pdf> <data> --out <result.pdf>`
4. Verify the output opens and report the path

## Examples

- "fill this application form from data.json" - list fields, map keys, fill, report path
- "complete the tax form PDF with the CSV data" - same flow with CSV input
```

---

## 05.03. Author checklist

*Mandatory.*

Before publishing a skill, check:

- [ ] One scenario - one directory with a single `SKILL.md`
- [ ] The source is in `doc/skills/<name>/SKILL.md`, not in a live tool directory
- [ ] A local skill (`pr_loc`) is outside synchronization - in `data/skills/`: directory `pl-<name>/SKILL.md` (or without a prefix); committed (`!data/skills/` in `.gitignore`), reflected in `data/skills/_index_skills_pl.md` (01.03)
- [ ] `name`: lowercase Latin letters and digits, hyphens, up to 64 characters, matches the directory name, reflects the task
- [ ] `description`: WHAT + WHEN, concrete application conditions, up to 1024 characters; SDO canon - `superpowers:writing-skills`
- [ ] Frontmatter has allowlist keys only; `version` / `status` / `type` are inside `metadata`; `metadata.type` is a taxonomy type slug (01.03), set at creation and current on update
- [ ] Category: when present - `metadata.category` and `metadata.category_name` strictly from the closed dictionary (01.04), the slug matches the second segment of the directory name (for a local skill without a type prefix - the first segment), the fields are filled as a pair; when absent - the corresponding name segment matches no dictionary slug
- [ ] Destructive skill - `disable-model-invocation: true` (Claude Code extension) or a ban on auto-application in the body for tools without the field
- [ ] Body up to 500 lines; excess in `reference.md` / `examples.md` with reading conditions
- [ ] All executable code is in `scripts/` with `allowed-tools` and `${CLAUDE_SKILL_DIR}`; the body holds only invocation commands and non-executable schemes (03.01, 03.03)
- [ ] The skill is self-sufficient: the directory transfers to any machine as a whole, without dependencies on source repository code and paths (03.03)
- [ ] Skill runtime data (registries, journals, state, cache) is in repository `data/` zones with an ownership marker, not in the skill directory or body; machine-specific data is in the `<hostname>` subfolder (`doc/standards/skill_data_standards.md`)
- [ ] Script output follows `cli_output_standards.md`: `report` for human status, `plain` for logs (`YYYY-MM-DD HH:MM:SS [marker] message`, the script inserts the time, no logger and no log files, monochrome, no ANSI, no frames), `--porcelain` for automation; English default, Russian opt-in; no trailing period, no diaeresis letter, hyphen-minus only; exit codes 0 / 1 / 2 (`project_standards.md`, 04.02, 04.04, 05.03)
- [ ] No duplication between the body and resources
- [ ] No time-sensitive data and no absolute machine paths
- [ ] No mentions of concrete skills from other repositories and no `doc/skills/ext/<repo>/` paths - only placeholders and generalized examples
- [ ] Placeholders are Latin only, without Cyrillic inside angle brackets
- [ ] `description` does not retell the process or step-by-step method; for a disciplining skill - a precursor symptom of violation (`superpowers:writing-skills`)
- [ ] Behavioral verification passed by skill class: disciplining - pressure scenarios and loophole closure; behavior change - wording micro-tests (`superpowers:writing-skills`)
- [ ] A skill with privileged operations contains a root-commands section (application levels, waiting for confirmation or objective verification before moving on, outcome only from a verified state); a skill without such operations does not contain the section (03.04)
- [ ] The skill is tested on real requests: it is found by `description`, the instruction leads to a result

---

## 05.04. Skill development and verification

*Mandatory.*

Skill development methodology and pre-publication behavioral verification - `superpowers:writing-skills`: discovery description (SDO), RED-GREEN-REFACTOR, pressure scenarios, wording micro-tests, rule form for the failure type, loophole closure.

Verification is mandatory by skill class: for a disciplining skill, behavioral verification is mandatory in full; for others - wording micro-tests and application to a new scenario. An edit to an existing skill wording is verified in the same order as a new skill.

Red flags - reasons to stop before publication: "the skill is obvious, verification is not needed", "the edit is small, testing is excessive", "I am sure it works", "I will check if problems appear".

---

## 06.01. Related documents

| Document | Purpose |
| -------- | ------- |
| `doc/standards/project_standards.md` | Core project rules; this standard applies on top of it |
| `doc/standards/skill_data_standards.md` | Skill runtime data: `data/` zones, classes, machine specificity |
| `doc/standards/skill_anthropic_standards.md` | Anthropic Agent Skills format (this document) |
| `doc/standards/_index_standards.md` | Standards package registry; unified version |
| `superpowers:writing-skills` | Skill development methodology: SDO, behavioral testing, pressure scenarios |
| Anthropic Agent Skills specification | Primary source of the SKILL.md format (docs.anthropic.com, code.claude.com) |
| Target tool documentation | Skill directories and tool specifics (01.03) |

If this document conflicts with the Anthropic specification, the specification wins; record the divergence by editing this standard.

---

## 06.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and routing map - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
