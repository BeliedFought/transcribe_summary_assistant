---
name: glob-skill-migrate-anthropic
description: Validates and repairs Anthropic Agent Skills packages (a <name>/SKILL.md directory with scripts and data templates), converts legacy plain skills found in sibling repositories into SKILL.md packages, and checks repository-wide package completeness - type, category, prefix, location, frontmatter fields. Use when the user asks to migrate, convert, or move a skill to the SKILL.md / Anthropic / opencode format, validate or repair an existing SKILL.md skill, check all skills, or run a completeness check (мигрировать, конвертировать или перенести навык в формат SKILL.md, Anthropic или opencode, проверить или исправить существующий SKILL.md-навык, проверить все навыки или провести проверку полноты навыков)
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/check_package.py *), Bash(${CLAUDE_SKILL_DIR}/scripts/check_all_skills.py *)
metadata:
  version: 1.9.3
  status: stable
  type: hub_glob
  category: skill
  category_name: Skills
---

# Validate, repair, and migrate skills to the Anthropic Agent Skills format

Validates and repairs `SKILL.md` packages, converts legacy plain skills from sibling repositories into self-contained `SKILL.md` packages, and checks repository-wide completeness. `SKILL.md` is the single editable source; `templates/` holds data templates and artifact blanks only. Three modes: full migration of a legacy flat skill (steps 1-7), repair of an existing package (section 8), completeness check of all repository skills (section 9). The package transfers to any machine as one folder, without the source repository. Other existing files are not changed.

## When to use

- The user asks to migrate, convert, or move a skill to the SKILL.md / Anthropic / opencode format
- The user asks to validate, repair, or align an existing SKILL.md package (the directory exists but does not meet the standard: code in the body, dependencies on project code, script output outside the standard)
- The user asks to check all repository skills, run a completeness check, or audit skills
- The user names the source skill explicitly: tag `@doc/skills/<file>`, file name or `id`, directory name
- The repository moves skills to `doc/standards/skill_anthropic_standards.md`

The completeness check (section 9) is the only mode that works without a named source skill. In other modes, do not run without an explicit source skill: ask the user for a path or name and do not pick candidates yourself.

## Instructions

### 0. Prerequisites

- The source skill is named explicitly by the user (except the completeness check - section 9). If missing, ask and wait.
- Read the target standard: `doc/standards/skill_anthropic_standards.md` (format, body structure, scripts, checklist, legacy migration - 04.02).
- Determine the mode: a legacy flat file `doc/skills/<name>.md` or `data/skills/<name>.md` - full migration (steps 1-7); an existing directory with `SKILL.md` (`doc/skills/` or a local one in `data/skills/`) - repair (section 8); a request to check all skills - completeness check (section 9).
- Target directory - the subdirectory `doc/skills/<kebab-id>/` with `SKILL.md` at the root (standard section 01.03); for a local skill (slug `pr_loc`, optional prefix) - `data/skills/<kebab-id>/`. Do not use live tool directories (`.opencode/skills/` and others): deploy is a separate process outside this standard.
- The target directory name must be free. If occupied, stop and ask the user.

### 1. Study the source skill

1. Read the skill file in full.
2. Extract the frontmatter: `id`, `type`, `description`, `auto_apply`, `version`, `status`, `category`, `category_name`.
3. Record the section composition and order (Description, When to use, Prerequisites, Instructions, Completion criteria, Examples, Restrictions, and so on).
4. Determine destructiveness: deletion, overwrite, DB migration, deploy operations - from the Restrictions section and the instruction commands.
5. Estimate the volume: if the source body is over ~500 lines, plan in advance to move material into `reference.md` / `examples.md`.

### 2. Inventory links and code

Walk the source body and collect every external entity. For each one, check that the path exists and assign its fate:

| Category | What to look for | Fate on migration |
| -------- | ---------------- | ----------------- |
| Project file references | `../../src/<path>`, `run/`, `data/`, `sql/`, `doc/specs/`, `output/` | Rewrite from the repository root; the contract (purpose, format, modes) goes to `reference.md` |
| Invocation commands | `python -m src.tools.<module>`, bash blocks calling modules | Do not carry over as is: the operation code goes to the package `scripts/` (adapted to `${CLAUDE_SKILL_DIR}`); the body holds the invocation command of the new script |
| Inline code | fenced code blocks in the body | All of it goes to `scripts/<name>.<ext>` with an invocation from the body, no length threshold; non-executable schemes (frontmatter structure, directory trees, markup templates) stay in the body |
| External project scripts | `run/<script>.py`, `src/tools/<module>.py` used only by the skill | Move into the package `scripts/` via `git mv` (history preserved), then adapt to `${CLAUDE_SKILL_DIR}` and arguments; if other consumers exist outside the skill - stop and ask the user |
| External URLs | internet sources, APIs | Keep in the body if the instruction uses them; reference material goes to `reference.md` |
| Templates and example files | artifact blanks | `templates/` (data templates and blanks only) or `examples.md` |

Broken paths - record them for the report; do not silently discard or "fix" them.

### 3. Build the package

The directory name is the source `id` in kebab-case: `db_migrate` -> `db-migrate`, `parse_report` -> `parse-report`.

Frontmatter - specification keys only:

```yaml
---
name: <kebab-id>
description: <what-and-when>   # WHAT + WHEN, up to 1024 characters; from the source description, add triggers from "When to use" when needed
metadata:
  version: <version>   # source version or 1.0.0
  status: <status>   # source status or stable
  type: <type>   # source type from the taxonomy (hub_loc, hub_glob, pr_glob, pr_loc); matches the directory name prefix
  category: <category>   # optional: slug from the closed dictionary (skill_anthropic_standards.md, section 01.04)
  category_name: <category-name>   # name from the dictionary, strictly paired with category
---
```

Source field mapping:

| Source | Target |
| ------ | ------ |
| `id` | `name` (snake_case -> kebab-case) |
| `description` | `description` (check that WHAT and WHEN are present) |
| `auto_apply: true` | not carried over; automatic application by `description` is the default behavior |
| `auto_apply: false` | the "explicit invocation by name only" rule goes to the body; for Claude Code, `disable-model-invocation: true` is allowed (extension, standard section 02.01) - only if the skill is not distributed under a strict specification |
| `version`, `status` | `metadata.version`, `metadata.status` |
| `type` | `metadata.type` (taxonomy slug: `hub_loc` / `hub_glob` / `pr_glob` / `pr_loc`; carried over from the source and maintained afterwards, `skill_anthropic_standards.md` section 01.04) |
| `category`, `category_name` | `metadata.category`, `metadata.category_name` (slug and name from the closed dictionary; filled as a pair) |

Section mapping:

| Source | Target |
| ------ | ------ |
| H1 heading | H1 heading |
| Note quote | paragraph after the heading or in `## Restrictions` |
| Description | introductory paragraph before `## When to use` |
| When to use | `## When to use` |
| Prerequisites | first subsection of `## Instructions` (Prerequisites) |
| Instruction | `## Instructions` |
| Completion criteria | `## Completion criteria` |
| Examples | `## Examples` |
| Restrictions | `## Restrictions` |
| Root commands and execution confirmation | `## Root commands and execution confirmation` |
| Script, Result example | `scripts/` invocation, `examples.md` |
| References to standards and neighboring skills | `## References` |

Body requirements - per sections 03.01 and 03.03 of `skill_anthropic_standards.md`:

- imperative, up to 500 lines; overflow goes to `reference.md` / `examples.md` with reading conditions;
- the body is text only: package script invocation commands (paths from `${CLAUDE_SKILL_DIR}`) and non-executable schemes are allowed; all executable operation code goes to `scripts/`;
- transfer the full text of sections, including the introductory text between a section heading and the first subsection; silently discard nothing;
- when migrating several skills in one session, update references to already migrated skills to the new names (`id` snake_case -> `name` kebab-case); list the renames in the report;
- if applying the skill later would delete the migration result (for example, an index rebuild does not see the new `SKILL.md` directories), minimally adjust the wording and record the adaptation in the report;
- project file paths are from the repository root: the source was deeper (usually `doc/skills/<repo-name>/`), and old relative `../../` paths do not work from the new directory;
- package script invocation goes through the skill directory variable (`${CLAUDE_SKILL_DIR}` or the tool equivalent);
- package scripts output per the hub core standard: lines `YYYY-MM-DD HH:MM:SS [marker] message` - logger strict mode style (04.04.01) but without a logger (the script inserts the time, no `src/logger.py` and no log files), monochrome stdout without ANSI colors and frames, markers `[!]` / `[i]` / `[*]`, text per 04.03: Russian, no trailing period, no Cyrillic yo letter (U+0451 / U+0401, only ye U+0435 / U+0415), no em or en dash - hyphen-minus only, no ellipsis; one line - one message, exit codes 0 / 1 / 2 (`project_standards.md` 04.02-04.04, 05.03);
- body language - English for `doc/skills/**` (standard 03.01); user-facing templates, examples, and report blocks may stay in the project language; a legacy Russian body is translated during migration unless the user asks otherwise;
- `templates/` holds data templates and artifact blanks only; do not put a legacy skill copy, a parallel source, or an editable format pair there.

**Archiving the source.** After the package is built and validated, archive the legacy flat skill file per repository rules (`.arch/`), not into `templates/`. Do not keep a parallel copy of the legacy skill as an editable source. For project skills the source path is `doc/skills/<repo-name>/<name>.md`; for local skills - `data/skills/<name>.md` or `data/skills/<name>/SKILL.md` (the skill stays local inside `data/skills/`). External project scripts used only by the skill are moved into `scripts/` via `git mv` (history preserved) and adapted there; the source is not duplicated in `templates/`.

### 4. Validate the package

Run the author checklist from section 05.03 of `skill_anthropic_standards.md` and the package check script:

```bash
${CLAUDE_SKILL_DIR}/scripts/check_package.py doc/skills/<kebab-id>
```

Additional checks:

- [ ] frontmatter has no `id` / `auto_apply` or other legacy fields
- [ ] `name` matches the directory name, kebab-case, up to 64 characters
- [ ] `description` - WHAT + WHEN, up to 1024 characters
- [ ] skill type is carried over: `metadata.type` from the source `type` field (taxonomy slug `hub_loc` / `hub_glob` / `pr_glob` / `pr_loc`), matches the directory name prefix; there is no top-level `type` field in frontmatter (strict allowlist)
- [ ] category (when present): `metadata.category` / `metadata.category_name` from the closed dictionary, the slug matches the second segment of the directory name (for a local skill without a type prefix - the first segment), filled as a pair
- [ ] body up to 500 lines
- [ ] no executable code in the body: only package `scripts/` invocation commands and non-executable schemes; `check_package.py` warnings about body blocks are resolved
- [ ] scripts are executable (`chmod +x`) with a shebang; `py_compile` passes; `__pycache__` artifacts are removed by the check script
- [ ] script output - lines `YYYY-MM-DD HH:MM:SS [marker] message` (the script inserts the time, no logger and no log files), monochrome, markers per the core standard (04.02, 04.04.01), text per 04.03: no trailing period, no Cyrillic yo letter (U+0451 / U+0401), dash - hyphen-minus only; exit codes 0 / 1 / 2 (05.03)
- [ ] every path from the inventory exists; broken ones are listed in the report
- [ ] relative `../..` paths from the source are rewritten from the repository root
- [ ] external project scripts: working copies live in `scripts/`, adapted to `${CLAUDE_SKILL_DIR}` and arguments, with no other consumers outside the skill
- [ ] the legacy flat source is archived per repository rules and does not remain in `doc/skills/` (or `data/skills/`) as a parallel source
- [ ] sections are transferred fully (text comparison with the source): "When to use", "Instructions" with introductory text, "Completion criteria", "Examples", "Restrictions"
- [ ] a skill with privileged operations contains a "Root commands and execution confirmation" section (application levels and waiting rules - `skill_anthropic_standards.md`, section 03.04); a skill without such operations does not contain it
- [ ] `templates/` holds data templates and artifact blanks only, with no legacy skill copy or parallel source
- [ ] adaptations beyond mechanical transfer (renamed references to migrated skills, adjusted wording, scripts adapted to `${CLAUDE_SKILL_DIR}`) are collected for the report

### 5. Register in the skill index

- Derived repository: regenerate `_index_skills_repo.md` with `glob-update-indexes --skills`; the generated registry has columns "Skill (dir), Class, Scope, Version, Purpose". If the index is maintained manually, add the row to the SKILL.md section and remove the legacy flat row (the file is no longer at the root).
- Hub: `_index_skills_hub.md` - add a row to the "Anthropic Agent Skills format skills (SKILL.md)" section; if the legacy flat skill had a row in the main registry, remove it.
- Running an index rebuild (`glob-update-indexes` / `hub-sync-indexes`) requires a user request. The generators include SKILL.md directories; after a run, verify that the migrated skill row is present.

### 6. Change boundaries

- Changes to existing files: external project scripts used only by the skill move into the package `scripts/` via `git mv`, and the legacy flat skill file is archived per repository rules. Nothing else changes.
- Do not edit standards, project code, files referenced by the skill, or tool configuration. Adaptation of moved scripts happens in the working copy in the package `scripts/`, not in a duplicate source; if other consumers of the script exist outside the skill, stop and ask the user.
- Allowed writes: files of the new directory (including moved scripts) and skill index row edits (adding a SKILL.md row, removing a legacy flat skill row from the main registry).
- Confirm with `git status`: the new directory (untracked), script moves (rename), the legacy source archive, and index row changes. Any other changes - revert and repeat the step more carefully.

### 7. Report to the user

- Tree of the created package (including scripts and data templates).
- Mapping table: source field or section - where it went.
- Fate of every link and code block from the inventory.
- Source archiving fact: from where to where - the legacy skill file and each external script.
- Adaptations beyond mechanical transfer: renamed references to migrated skills, adjusted wording, scripts adapted to `${CLAUDE_SKILL_DIR}` - with a rationale for each.
- Broken links, volume limit overruns, open questions - in a separate list.
- Reminder: the skill lives in `doc/skills/<kebab-id>/`; `SKILL.md` is the single editable source for further changes. To make the tool apply the skill, copy the directory to the tool live directory (for example `.opencode/skills/`) as a separate operation; after deploy, invoke it by the `name`.

### 8. Repair an existing package

Mode for an existing `<name>/` directory with `SKILL.md` (shared - in `doc/skills/`, local - in `data/skills/`) that does not meet the standard: executable code in the body, dependencies on project code and scripts, script output outside the hub standard, frontmatter or checklist violations of section 05.03.

1. Diagnostics: run `${CLAUDE_SKILL_DIR}/scripts/check_package.py doc/skills/<name>` (for a local package - `data/skills/<name>`) and the author checklist (standard section 05.03); record the list of violations.
2. Inventory the `SKILL.md` body and package scripts by the rules of step 2: inline body code goes to `scripts/`; project module invocation commands and external scripts are moved into `scripts/` (via `git mv` when the script has no other consumers); if other consumers of the script exist outside the skill, stop and ask the user.
3. Fix by editing `SKILL.md` and package resources in place: `SKILL.md` is the single editable source, there is no format pair and no `templates/` source copy.
4. Bring package scripts to the hub core standard output: lines `YYYY-MM-DD HH:MM:SS [marker] message` - logger strict mode style but without a logger (the script inserts the time, no `src/logger.py` and no log files), monochrome stdout without ANSI colors and frames, markers `[!]` / `[i]` / `[*]`, text per 04.03: no trailing period, no Cyrillic yo letter (U+0451 / U+0401), dash - hyphen-minus only, no ellipsis; one line - one message, exit codes 0 / 1 / 2 (`project_standards.md` 04.02-04.04, 05.03).
5. Control: rerun `check_package.py` - no errors, body warnings resolved; change boundaries - per step 6; report - per step 7 (what was fixed and why, before and after). For a local package (`data/skills/`), check the registry row in `data/skills/_index_skills_pl.md` (the summary indexes `_index_skills_hub.md` and `_index_skills_repo.md` do not include local skills).

### 9. Completeness check of all repository skills

Mass mode: all repository skills in canonical locations - `SKILL.md` packages and legacy flat files when present - are checked against the standard. It changes nothing and only reports. No source skill is required.

Run from the repository root:

```bash
${CLAUDE_SKILL_DIR}/scripts/check_all_skills.py
```

The script checks for every skill:

- storage by type: legacy flat `hub_*` / `glob_*` - at the `doc/skills/` root, `pg_*` - in `doc/skills/<repo-name>/`; Anthropic packages `hub-` / `glob-` / `pg-` - in `doc/skills/`; local (`pr_loc`) - only in `data/skills/`, both forms: `pl-` or prefixless directories and `pl_` or prefixless flat files;
- legacy plain format - required frontmatter fields: `id` (matches the file name), `type`, `description`, `auto_apply`;
- Anthropic format - required fields: `name` (matches the directory name), `description`, `metadata.type`; a top-level `type` is a violation (strict allowlist);
- the type slug is valid: `hub_loc`, `hub_glob`, `pr_glob`, `pr_loc`;
- application category (when present): slug and name from the closed dictionary, the second name segment matches the slug (for a local skill without a type prefix - the first segment), the `category` / `category_name` fields (or `metadata.category` / `metadata.category_name`) are filled as a pair; without a category, the corresponding name segment matches no dictionary slug (`skill_anthropic_standards.md`, section 01.04);
- the name prefix matches the slug: `hub_` / `hub-` - `hub_loc`, `glob_` / `glob-` - `hub_glob`, `pg_` / `pg-` - `pr_glob`; for `pr_loc` the prefix is optional: `pl_` / `pl-` or no prefix;
- skills without a type prefix in `doc/skills/` are a violation (rename candidates); for local `data/skills/` skills a name without a prefix is allowed;
- the walk covers `doc/skills/` (including `<repo-name>/` subfolders, except the `ext/` aggregate) and `data/skills/` in both formats; index files `_index*.md` are skipped - they are not skills;
- the `doc/skills/ext/` aggregate is skipped - its content is checked in the source repositories.

Procedure:

1. Run the script and record the violations from the report.
2. For each violation, propose a fix: edit or add the `type` / `metadata.type` field; rename with a type prefix via `git mv`; move a `pl-` directory to `data/skills/`; fill in the frontmatter. Submit the fix package for user approval (batch or interactive mode - section 07.02 of the core standard); change nothing without confirmation.
3. For `SKILL.md` packages, fix in place; for legacy flat skills, convert by full migration (steps 1-7) - do not edit them as a parallel format. For a local skill (`data/skills/`), the registry row is in `data/skills/_index_skills_pl.md`; it is not part of the summary indexes.
4. Rerun the script - no errors. Report: how many skills were checked, the list of violations, what was fixed, what remains for the user to decide.

## Examples

1. «мигрируй @doc/skills/<repo-name>/pg_<name>.md на формат SKILL» -> study the skill; inventory: `src/` modules, commands, report paths; create `doc/skills/pg-<name>/SKILL.md` and `scripts/` (all code goes there, project paths become arguments), put the path contract in `reference.md`; move the external script `run/<script>.py` into `scripts/`; archive the legacy source; register in the index; report.
2. «перенеси pg_<name> в opencode» -> package `doc/skills/pg-<name>/`, inline code entirely in `scripts/`, description based on the source description and "When to use"; the legacy source is archived; deploy to `.opencode/skills/` is a separate operation, not part of migration.
3. «проверь и поправь pg-render-chart, он не по стандарту» -> `check_package.py`: code blocks in the body, dependency on `run/render.sh`; move the code and the script into `scripts/`; edit `SKILL.md` in place (there is no format pair); rerun without errors; "before and after" report.
4. «проверь все навыки на соответствие стандарту» -> `check_all_skills.py`: a skill without the `type` field and a `pl-` directory in `doc/skills/` are found; report with target names; after confirmation, fill in `type` and move `pl-` to `data/skills/`; rerun - no errors.

## References

- `doc/standards/skill_anthropic_standards.md` - target format: frontmatter, body structure, progressive disclosure, package self-sufficiency, code rules and root commands (sections 01.03, 01.04, 03.01, 03.03, 03.04), author checklist (05.03), legacy migration (04.02)
- `superpowers:writing-skills` - skill authoring and review guidance
- `scripts/check_package.py` - single package checks: frontmatter (`name`, `metadata.type` and prefix match, `metadata.category` / `metadata.category_name` and second name segment match), script executability, compilation, executable body blocks
- `scripts/check_all_skills.py` - completeness check: all repository skills in canonical locations, including legacy flat files when present, against the requirements (type, prefix, location, frontmatter fields)
- `scripts/skill_common.py` - shared constants and checker helpers (type taxonomy, name prefixes, category dictionary, frontmatter parsing, index file predicate, and the optional-prefix policy for local skills); the single point of truth that keeps `check_package.py` and `check_all_skills.py` checks aligned
- Repository skill index (`_index_skills_repo.md`; in the hub - `_index_skills_hub.md`) - result registration

## Restrictions

- Deleting repository files and folders means moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` (quarantine, `project_standards.md` 01.01.06), never deletion; clean `.trash/` only on an explicit user request
- Migration archives the legacy flat skill file per repository rules and moves external project scripts into `scripts/`; deletion of sources and reverse conversion are not performed; the archived source is not edited; script adaptation happens only in the `scripts/` working copy
- Distribution to other repositories - via the `hub-sync-skills` skill for shared skills (directories with the `glob-` prefix); a skill without the prefix is project-specific and is aggregated into the hub under `doc/skills/ext/<repo-name>/<name>/`
- One skill is migrated per run (in any mode); for a skill package, repeat for each one named by the user
- The completeness check changes nothing: report only; apply fixes per section 9 and only after user confirmation
- Repair mode does not change the skill purpose or name: `name` and the directory name stay; if they mismatch, align to the directory name
