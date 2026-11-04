---
name: glob-update-indexes
description: Rebuilds the repository local indexes by the index_nav_standards.md canon - the skills index _index_skills_repo.md, the specifications index doc/specs/_index_specs.md, and the local skills index data/skills/_index_skills_pl.md (when the directory exists). Regenerates the full canonical skeleton (intro, mandatory application, registries, routing map, auto-update) and checks index structure against the canon checklist; supports targeted rebuilds with --skills, --specs, and --local-skills. Use when asked to update local indexes, refresh the skill or specification list, or after changes in doc/skills/, doc/specs/, or data/skills/
metadata:
  version: 1.6.0
  status: stable
  type: hub_glob
  category: update
  category_name: Update
---

# Rebuild Repository Local Indexes

Global skill (prefix `glob-`), distributed to every repository. Works only on the local repository and knows nothing about cross-repo state. In the `project_standards` hub the summary skills index `_index_skills_hub.md` is maintained by `hub-sync-indexes`, and the hub `doc/specs/_index_specs.md` is a reference template; in the hub this skill rebuilds only `data/skills/_index_skills_pl.md` (when the directory exists).

The skill rebuilds three repository indexes by the navigation canon `index_nav_standards.md`: `doc/skills/_index_skills_repo.md` - the skills directory entry point, `doc/specs/_index_specs.md` - the specification registry with a subfolder summary, and `data/skills/_index_skills_pl.md` - the local skills index (slug `pr_loc`; built when `data/skills/` exists, including in the hub). The script generates the full canonical skeleton: an intro pointing to 07.06, mandatory application, registries, a routing map (initial fill from descriptions), and an auto-update section. After rebuilding, the skill checks the generated index structure against the canon checklist and refines purposes and the routing map. The skill edits only these indexes and never the skills, specifications, standards, or their indexes.

## When to Use

- The user asks to update or refresh repository local indexes (skills, specifications, or local skills)
- A skill in the root `doc/skills/`, a file in `doc/specs/`, or a skill in `data/skills/` was added, removed, or renamed
- A skill frontmatter changed (`name`, `description`, `metadata.type`, `metadata.category`, `metadata.category_name`, `metadata.version` for Anthropic; `id`, `description`, `auto_apply`, `version`, `type`, `category`, `category_name` for legacy plain) - in `doc/skills/` or `data/skills/`
- The user tagged `@doc/skills/_index_skills_repo.md`, `@doc/specs/_index_specs.md`, or `@data/skills/_index_skills_pl.md` without a concrete task

## Instructions

### Preconditions

- Run from the repository root
- At least one of the folders exists: `doc/skills/`, `doc/specs/`, `data/skills/`; in the `project_standards` hub only `data/skills/` is rebuilt

### Procedure

1. Run the package script from the repository root:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/update_indexes.py
```

   To rebuild only selected indexes, pass one or more flags: `--skills`, `--specs`, `--local-skills`. With no flags the script rebuilds all applicable indexes (in the hub - only the local skills index).

2. The script rebuilds indexes in the canonical skeleton:
   - `doc/skills/_index_skills_repo.md`: intro, mandatory application, skill registry (class, scope, version, purpose, when to apply), a SKILL.md directories section, a routing map (initial topics from skill descriptions), auto-update; legacy flat `*.md` skills are listed until migration;
   - `doc/specs/_index_specs.md`: intro, mandatory application, root file registry with types, the `init/` section, a `doc/specs/<project>/` subfolder summary, a routing map (by known file types), auto-update;
   - `data/skills/_index_skills_pl.md` (when the directory exists, in any repository including the hub): intro, mandatory application, a registry of flat skills and SKILL.md directories (class - local, scope from `category` / `metadata.category`), a routing map, auto-update.
3. The script preserves previously filled `Purpose` values in the specifications index and the local skills index (when frontmatter has no description); new files and subfolders get `-`. After the run, fill purposes manually (for `spec_ui.html` state the mockup SemVer per `console_ui_standards.md`). Existing custom routing-map rows for live files are preserved.
4. Check the generated index structure against the `index_nav_standards.md` canon checklist:
   - full skeleton (Section 03.01): intro pointing to 07.06, mandatory application, registry, routing map, auto-update;
   - registry (Section 03.03): every row is an existing file; every directory object is present; purposes are factual, without evaluations or history;
   - map (Section 04): topics phrased as user tasks, no vague wording ("other", "misc"), every registry object covered by at least one row, links point to existing objects;
   - the pointer to `project_standards.md` 07.06 is present.
   Fix deviations in the indexes; report anything that cannot be fixed.
5. Refine initial routing-map topics: phrase them as user tasks and add trigger synonyms (canon - `index_nav_standards.md`, Section 04).
6. In the `project_standards` hub the script skips `_index_skills_repo.md` and `_index_specs.md` (reason in the log) and rebuilds only `data/skills/_index_skills_pl.md`.
7. Report to the user: what went into each index, structure check results, and paths to updated files.

## Completion Criteria

- Generated indexes match the `index_nav_standards.md` canon skeleton (Section 03.01): intro, mandatory application, registry, routing map, auto-update
- `doc/skills/_index_skills_repo.md` matches the actual root skills, project `pg-*` skills in subfolders, and SKILL.md directories; index files (`_index_*.md`) are not listed
- `doc/specs/_index_specs.md` matches the actual `doc/specs/` composition: root files with types, the `init/` section, and a subfolder summary
- `data/skills/_index_skills_pl.md` (when the directory exists) matches the actual `data/skills/` composition: flat skills and SKILL.md directories
- The Section 04 structure check is complete: topics phrased as tasks, full object coverage, no vague wording
- Purposes of new specification files and subfolders, and of local skills, are filled manually after the rebuild
- In the hub the skill rebuilds only `data/skills/_index_skills_pl.md` and reports the skipped indexes
- The user receives a report for each generated index with structure check results

## Examples

1. User: "update the indexes" -> the agent runs the script, rebuilds the indexes, checks the structure, and reports.
2. A specification `spec_export.md` was added to `doc/specs/` -> the agent regenerates the index; a row with type "Task or module specification" appears in the registry and map; the purpose is filled manually.
3. A directory `pl-report/SKILL.md` was added to `data/skills/` -> the script includes it in `_index_skills_pl.md` (in any repository, including the hub); purposes and the map are refined manually.

## Restrictions

- Deleting repository files and folders - move to `.trash/<slug>_<YYYYMMDDHHMM>/` (quarantine, `project_standards.md` 01.01.06), never delete; purge `.trash/` only on explicit user request
- In the `project_standards` hub the summary skills index is maintained by `hub-sync-indexes`, and `doc/specs/_index_specs.md` is a reference template; only `data/skills/_index_skills_pl.md` is rebuilt in the hub
- Edit only `doc/skills/_index_skills_repo.md`, `doc/specs/_index_specs.md`, and `data/skills/_index_skills_pl.md`; never change skills, specifications, standards, or their indexes
- No cross-repo synchronization - local repository only

## References

- `scripts/update_indexes.py` - index rebuild in the canonical skeleton; run from the repository root
- `doc/standards/index_nav_standards.md` - navigation document canon: index skeleton and routing-map rules (skills indexes - Section 06.02)
- `doc/standards/project_standards.md` (Section 07.06) - agent decision order when a rule is missing
