# Skill Runtime Data Standards. Version 5.0.1

This document canonizes storage of data that skills create and maintain during execution: registries, journals, state markers, and cache. Principle: a skill is an engine, not a storage; the skill directory contains only a static package, while runtime data lives in repository zones. The rules are uniform for all skill types (`hub_loc`, `hub_glob`, `pr_glob`, `pr_loc`). The document supplements `project_standards.md` and applies on top of it together with the skill standards.

---

## Table of Contents

**01. Fundamentals:** 01.01 Skill is an engine, not a storage - 01.02 Runtime data classes - 01.03 Machine specificity

**02. Zones:** 02.01 Zone layout - 02.02 Naming - 02.03 Creation on first write and lifecycle

**03. File format:** 03.01 Ownership marker - 03.02 Registry - 03.03 Journal - 03.04 State

**04. Conformance and boundaries:** 04.01 Full conformance table - 04.02 Boundaries with adjacent mechanisms

**05. Prohibitions**

**06. Relations and versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Skill is an engine, not a storage

*Mandatory.*

A skill directory is a static package: instruction, documentation, templates, code. For the Anthropic format - `SKILL.md`, `reference.md`, `examples.md`, `templates/`, `scripts/` (`skill_anthropic_standards.md`, 01.04). Runtime data - accumulators and execution results - is never stored in the skill directory or in the skill body: the rule applies to all types, with no exceptions.

Consequences:

- a skill transfers by copying the directory into any repository and is ready to work without cleanup - package self-sufficiency (`skill_anthropic_standards.md`, 03.03) extends to data: skill state does not travel with the skill;
- the skill creates the required data zones and files itself on the first write in the receiving repository;
- data paths in the skill body and scripts are relative to the repository root (in a session - to the session root), not to the skill directory; `${CLAUDE_SKILL_DIR}` is only for the package's own resources;
- the skill carries initial data file templates in `templates/` of its directory and materializes them on the first run.

## 01.02. Runtime data classes

*Mandatory.*

| Class | What it is | Examples |
| ----- | ---------- | -------- |
| Registry | A directory of entities, updated idempotently | machine variables, inventory, mappings, candidate lists |
| Journal | A chronicle of significant events, records are appended | run history, applied changes, maintenance facts |
| State | Idempotency markers and cursors | "applied", last run, version of the applied change |
| Cache | Recomputable data | intermediate exports, parsed snapshots |

Registry, journal, and state are knowledge living in git (zones - 02.01); cache is an accelerator living outside commits. Other runtime classes (`diag/` snapshots, `tmp/` one-off artifacts, `output/` products, backups, the mart) follow the existing core standard rules - the full conformance table is in 04.01.

## 01.03. Machine specificity

*Mandatory.*

Data of the "registry", "journal", and "state" classes is divided by level:

- **shared level** - the value is the same in any repository clone: inventory of all machines, project directories; written directly to the zone;
- **host level** - the value is valid on one machine only: variables of this host, state applied on it, the chronicle of its runs; written to the `<hostname>` subfolder inside the zone.

Rules:

- the path of machine-specific data is `data/<zone>/<hostname>/<domain>.md`;
- the subfolder name is the short host name (`hostname` without the domain), Latin, kebab-case;
- a machine writes only to its own host subfolder and does not touch others; it reads any - the inventory and state of all machines are visible from any clone, host paths do not overlap, and commits from different machines do not conflict;
- host-level cache does not exist: it is outside git and local to the machine by definition;
- state snapshots of configuring skills in `diag/` (`skill_anthropic_standards.md`, 03.05) are an existing canon and are not reorganized by this document.

---

## 02.01. Zone layout

*Mandatory.*

```text
data/
├── registries/                  # entity registries
│   ├── <domain>.md               # shared level
│   └── <hostname>/
│       └── <domain>.md           # host level
├── journals/                    # event journals (same two levels)
│   ├── <domain>.md
│   └── <hostname>/
│       └── <domain>.md
├── state/                       # state markers (same two levels)
│   ├── <domain>.md
│   └── <hostname>/
│       └── <domain>.md
└── cache/                       # recomputable, outside commits
    └── <skill-name>/
```

- `registries/`, `journals/`, and `state/` are committed - exceptions `!data/registries/`, `!data/journals/`, `!data/state/` in `.gitignore` (`project_standards.md`, 06.01); host subfolders are covered by the same patterns;
- `cache/<skill-name>/` is not committed - it stays in the ignored `data/`; its content can be deleted at any time without losing knowledge;
- in a session (`project_standards.md`, 01.01.01) the zones are the same, but under the session `data/` folder.

## 02.02. Naming

*Mandatory.*

| Entity | Rule | Example |
| ------ | ---- | ------- |
| Zone file | content domain slug, kebab-case, Latin, no transliteration | `machines.md`, `pip-mirrors.md` |
| Host subfolder | short host name, kebab-case | `pchm02` |
| Private skill chronicle without a dedicated domain | file named after the skill | `journals/glob-cfg-pip.md` |
| Cache directory | skill name | `cache/glob-cfg-pip/` |

The domain names the content, not the skill: the file is understandable without knowing who maintains it; the owner is fixed by the marker (03.01). One domain - one file per level; splitting into `<domain>_<subdomain>.md` only when really necessary. The registry of all machines and the registry of one host are different levels of the same domain: `registries/machines.md` and `registries/<hostname>/env.md`.

## 02.03. Creation on first write and lifecycle

*Mandatory.*

- Zones are created on the first write, not at project initialization: `data/registries/` appears when the first skill maintains the first registry; a repository can live without zones indefinitely.
- The initial file template is in the skill `templates/`; on the first run the skill materializes it into the zone, and subsequent runs merge per the format rules (03.02-03.04).
- Outdated zone content is archived per the general `.arch/` rules (`project_standards.md`, 01.01).
- Zones are not served by indexes: a registry is its own registry, navigation uses zone and domain names; `_index_*.md` indexes navigate static directories (`index_nav_standards.md`).

---

## 03.01. Ownership marker

*Mandatory.*

The first line of every zone file is an ownership marker (an extension of `skill_anthropic_standards.md`, 03.06):

```markdown
<!-- generated-by: <skill-or-domain> -->
```

The marker distinguishes a generated file from a user file: a file with a marker is maintained by its owner and is freely overwritten or merged by it; a file without a marker is considered user-owned - overwrite only with an explicit flag (03.06 there). Inside a host subfolder the marker names the owner, not the host: the host is visible in the path.

## 03.02. Registry format

*Mandatory.*

```markdown
<!-- generated-by: <owner> -->
# Реестр: <domain>

<purpose>

| Ключ | Значение | Дата | Источник |
| ---- | -------- | ---- | -------- |
```

- A registry is a Markdown table; rows are merged idempotently by key: a repeated write updates the value and date without creating duplicates.
- The registry stores the current state of the directory; the change history, if needed, is in the journal of the same domain.

## 03.03. Journal format

*Mandatory.*

```markdown
<!-- generated-by: <owner> -->
# Журнал: <domain>

## YYYY-MM-DD HH:MM - <event-title>

- суть: <what-happened>
- результат: <outcome>
```

- New records are added at the top of the file.
- One record - one event; narrative and multi-paragraph text are forbidden (following the pattern of memory topic files - `memory_standards.md`, 04.02).

## 03.04. State format

*Mandatory.*

```markdown
<!-- generated-by: <owner> -->
# Состояние: <domain>

| Элемент | Значение | Дата |
| ------- | -------- | ---- |
```

- Rows are merged idempotently by item; the table format is the same as the applied-state snapshot (`skill_anthropic_standards.md`, 03.05).
- State records applied facts, not plans; a plan belongs to a task or specification.

---

## 04.01. Full conformance table

*Mandatory.*

Each runtime class has one place. The segment `[<hostname>/]` is the host level for machine specificity (01.03). Classes outside the zones live by existing rules and are not retaught by this document:

| Class | Place | Git | Canon |
| ----- | ----- | --- | ----- |
| Registry | `data/registries/[<hostname>/]<domain>.md` | yes | this document |
| Journal | `data/journals/[<hostname>/]<domain>.md` | yes | this document |
| State (skill execution markers) | `data/state/[<hostname>/]<domain>.md` | yes | this document |
| Cache | `data/cache/<skill-name>/` | no | this document |
| Applied environment settings snapshot (configuring skills) | `diag/` | yes | `skill_anthropic_standards.md` (03.05) |
| Lesson (transferable experience) | `data/lessons.md` | yes | `project_standards.md` (01.01.07) |
| One-off artifact (export, snapshot for analysis, screenshot, lock, pid) | `tmp/<domain>/` | no | `project_standards.md` (01.01.04) |
| User product (report, result file) | `output/` | no | `project_standards.md` (01.01) |
| Backup | `data/backup/<task>/` | no | `project_standards.md` (01.01) |
| Accumulated dataset (mart) | `data/mart_<domain>.sqlite` | no | `project_standards.md` (01.01.03) |
| Technical execution log | not written to a file - script stdout | - | `skill_anthropic_standards.md` (03.03) |
| Web subsystem runtime | `web/var/` | no | `web_standards.md` (02.07) |

## 04.02. Boundaries with adjacent mechanisms

*Mandatory.*

- Agent memory `data/memory/` (`memory_standards.md`) is a closed list; skill runtime data is not memory: memory stores agent context, zones store task data.
- The lesson journal `data/lessons.md` is an existing canon (`project_standards.md`, 01.01.07); it is not moved into `journals/`.
- Snapshots in `diag/` per 03.05 are the existing canon of configuring skills; new skills without the 03.05 skeleton keep state in `data/state/`.
- `config/` and `.env` (`project_standards.md`, 01.02) are code operation parameters, not skill accumulators.
- `_index_*.md` indexes (`index_nav_standards.md`) navigate static directories; registry zones are not served by indexes.
- Web subsystem runtime `web/var/` (`web_standards.md`, 02.07) is a separate canon not affected by this document.

---

## 05.01. Prohibitions

*Mandatory.*

| Prohibition | Correct |
| ----------- | ------- |
| Runtime data in the skill directory: registries, journals, state, cache, updatable lists | Repository zones (02.01); the skill directory is a static package |
| Mutable data in the skill body and `templates/` ("updatable artifact", candidate list, counter) | Registry `data/registries/<domain>.md` with an ownership marker; body and `templates/` are static only |
| Writing to another host's subfolder | Only your own `<hostname>` (01.03) |
| Cache and one-off artifacts in commit zones (`registries/`, `journals/`, `state/`) | Cache in `cache/<skill-name>/`, one-off data in `tmp/<domain>/` |
| Runtime data in memory, the lesson journal, or a `diag/` snapshot (outside the 03.05 skeleton) | Zones; boundaries - 04.02 |
| Backups inside zones | `data/backup/<task>/` |

---

## 06.01. Related documents

| Document | Relation |
| -------- | -------- |
| `project_standards.md` | `data/` (01.01), sessions (01.01.01), `tmp/` (01.01.04), lessons (01.01.07), `.gitignore` template (06.01) |
| `skill_anthropic_standards.md` | skill directory (01.04), package self-sufficiency (03.03), configuring skill snapshot (03.05), ownership marker (03.06), anti-patterns (05.01), checklist (05.03) |
| `memory_standards.md` | boundary between memory and runtime data zones (01.03) |
| `web_standards.md` | web subsystem runtime `web/var/` (02.07) - outside this canon |
| `index_nav_standards.md` | repository indexes, including `data/skills/_index_skills_pl.md`; runtime data zones are not part of indexes |
| `doc/standards/_index_standards.md` | package registry and routing map |

## 06.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and routing map - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request.
