# Repository Skills Index. Version 5.0.0

Entry point for `doc/skills/` in `transcribe_summary_assistant`: lists global (`glob-*`, `glob_*`) and project (`pg-*`, `pg_*`) skills. Load this index rather than the full directory and use the routing map to open relevant skills. Decision order when norms are absent - `project_standards.md`, Section 07.06.

---

## Mandatory Application

Tagging this file requires applying relevant skills, not merely reading the index:

1. Identify relevant skills via the routing map
2. Open the matched skill files and follow their instructions
3. Apply relevant skills whenever a matching task arises, even without explicit tagging

---

## Skill Registry

| Skill | Class | Scope | Auto-Apply | Version | Purpose |
|-------|-------|-------|------------|---------|---------|

## Anthropic Agent Skills (SKILL.md)

| Skill (dir) | Class | Scope | Version | Purpose |
|-------------|-------|-------|---------|---------|
| `glob-audit-repository` | global | Audit (`audit`) | 2.6.1 | Performs a two-level audit and repair of a repository against the standard, honoring recorded project overrides - a subagent checks the codebase, the agent classifies deviations |
| `glob-cfg-pip` | global | Configuration (`cfg`) | 1.2.0 | Finds a working PyPI mirror, measures candidate response times, and writes the selected mirror to pip.conf when pypi.org is unreachable |
| `glob-mine-lesson` | global | Knowledge Mining (`mine`) | 1.0.1 | Records a lesson in the lesson journal data/lessons.md - transferable experience from project work: a technique, a library or environment trap, a non-obvious solution and its |
| `glob-skill-deploy` | global | Skills (`skill`) | 1.3.0 | Deploys an Anthropic Agent Skills skill from doc/skills/<name>/ to live tool directories - opencode, Kilo Code, Cursor (project or personal), by copy or symlink (--link) |
| `glob-skill-migrate-anthropic` | global | Skills (`skill`) | 1.9.3 | Validates and repairs Anthropic Agent Skills packages (a <name>/SKILL.md directory with scripts and data templates), converts legacy plain skills found in sibling repositories |
| `glob-update-indexes` | global | Update (`update`) | 1.6.0 | Rebuilds the repository local indexes by the index_nav_standards.md canon - the skills index _index_skills_repo.md, the specifications index doc/specs/_index_specs.md, and the |

---

## Routing Map

Maps task topics to skills (`index_nav_standards.md`, Section 04).

| Task Topic | Skill |
|------------|-------|
| Performs a two-level audit and repair of a repository against the standard, honoring recorded project overrides - a subagent checks the codebase, the agent classifies deviations | `glob-audit-repository` |
| Finds a working PyPI mirror, measures candidate response times, and writes the selected mirror to pip.conf when pypi.org is unreachable | `glob-cfg-pip` |
| Records a lesson in the lesson journal data/lessons.md - transferable experience from project work: a technique, a library or environment trap, a non-obvious solution and its | `glob-mine-lesson` |
| Deploys an Anthropic Agent Skills skill from doc/skills/<name>/ to live tool directories - opencode, Kilo Code, Cursor (project or personal), by copy or symlink (--link) | `glob-skill-deploy` |
| Validates and repairs Anthropic Agent Skills packages (a <name>/SKILL.md directory with scripts and data templates), converts legacy plain skills found in sibling repositories | `glob-skill-migrate-anthropic` |
| Rebuilds the repository local indexes by the index_nav_standards.md canon - the skills index _index_skills_repo.md, the specifications index doc/specs/_index_specs.md, and the | `glob-update-indexes` |

---

## Index Auto-Update

On any change to `doc/skills/` (adding, removing, renaming, or updating skill frontmatter), rebuild this index with `glob-update-indexes`, refine purposes and routing map topics per `index_nav_standards.md` (Sections 03.03, 04), and report added, updated, and removed entries.
