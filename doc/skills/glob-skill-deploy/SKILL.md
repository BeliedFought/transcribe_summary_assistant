---
name: glob-skill-deploy
description: Deploys an Anthropic Agent Skills skill from doc/skills/<name>/ to live tool directories - opencode, Kilo Code, Cursor (project or personal), by copy or symlink (--link). Use when the user asks to deploy, install, or make a skill available to an agent in opencode / Kilo / Cursor (задеплоить, развернуть или установить навык в opencode / Kilo / Cursor, сделать навык доступным агенту)
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/deploy.sh *)
metadata:
  version: 1.3.0
  status: stable
  type: hub_glob
  category: skill
  category_name: Skills
---

# Deploy a skill to tools

Deploys a skill directory from the repository source (`doc/skills/<name>/`) to live directories of target tools: opencode, Kilo Code, Cursor. Two modes: copying the directory as a whole (SKILL.md, scripts, templates, and resources; the deployed copy works without the source repository) and symlink (`--link`; the live directory points to the source, and the skill is always current without redeploy). The source and the repository are not changed; deploy is a separate process from skill authoring and migration.

## When to use

- The user asks to deploy, install, or set up a skill in opencode / Kilo Code / Cursor
- The user asks to make a skill available to the tool agent
- The skill was changed in the source - redeploy is required

## Instructions

### 0. Prerequisites

- The source skill is named by the user: name or path. The directory `doc/skills/<name>/` with `SKILL.md` exists. If not, ask; do not guess.
- Clarify with the user: target tools (opencode, Kilo Code, Cursor, all) and scope - project (default) or personal. If not stated, ask.

### 1. Validate the package

- `SKILL.md` (uppercase) is at the root of the skill directory.
- Frontmatter: `name` matches the directory name (strictly checked in Kilo Code and Cursor), `description` is filled.
- The `allowed-tools` / `disable-model-invocation` fields do not block deploy: opencode ignores them, Cursor reads `disable-model-invocation`.

### 2. Choose deploy targets

| Tool | Project | Personal |
| ---- | ------- | -------- |
| opencode | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Kilo Code | `.kilo/skills/` | `~/.kilo/skills/` |
| Cursor (>= 2.4) | `.cursor/skills/` | `~/.cursor/skills/` |

Additional compatibility targets: `.claude/skills/` is read by opencode (always), Cursor (always), and Kilo Code (with Claude Code Compatibility enabled) - use only on an explicit request.

**Mode choice:** personal deploy on the hub machine - `--link` (symlink to `doc/skills/<name>/`, source edits are picked up without redeploy; confirmed for opencode, for Kilo Code and Cursor verify symlink pickup and fall back to a copy if it fails). Project deploy, deploy on other machines, and portability copies - copying.

**Git:** live directories are not the source; before deploy, check the repository `.gitignore`: target directories (`.opencode/`, `.kilo/`, `.cursor/`) must not get into a commit; add missing exclusions with user agreement.

### 3. Deploy

1. For each selected target, call the deploy script (creates the target directory when missing, replaces an existing copy or symlink entirely - no mix of old and new files):

```bash
# copy
${CLAUDE_SKILL_DIR}/scripts/deploy.sh doc/skills/<name> <target-dir>/<name>
# symlink (personal deploy on the hub machine)
${CLAUDE_SKILL_DIR}/scripts/deploy.sh --link doc/skills/<name> <target-dir>/<name>
```

2. Change nothing in the repository (except `.gitignore` lines from step 2, by agreement).

### 4. Refresh and verification per tool

| Tool | Pickup | Check |
| ---- | ------ | ----- |
| opencode | Restart opencode (the skill cache is per instance; there is no reload command) | `opencode debug skill` - the skill is in the JSON list |
| Kilo Code | `/reload` in the current session or a new session | Ask the agent "Do you have access to skill X?" |
| Cursor | Restart Cursor | Customize -> Skills; invoke `/skill-name` in the agent chat |

Details:

- `--link` mode: no redeploy after source edits, the live copy is always current; the skill cache per tool instance remains (opencode - restart), SKILL.md edits are picked up in a new session
- Kilo Code: shell commands `` !`command` `` in the skill body run only in personal (trusted) directories; project `.kilo/skills/` does not execute them. A skill with scripts in the body needs a personal deploy.
- opencode: if needed, grant permission in `opencode.json` - `"permission": { "skill": { "<name>": "allow" } }`.
- Cursor: personal skills are not transferred to Cloud Agents / remote SSH - only project skills from the repo work there.
- Cursor below version 2.4 does not support the SKILL.md format.

### 5. Report to the user

- Table: tool - deploy path - result (copied / replaced / symlink).
- How to refresh and verify in each tool (step 4 table).
- Reminder: the source is `doc/skills/<name>/`; after source edits with a copy deploy, repeat the deploy manually; with a symlink, edits are picked up automatically.

## Examples

1. «задеплой glob-skill-migrate-anthropic в opencode» -> validate the package; `deploy.sh` to `.opencode/skills/glob-skill-migrate-anthropic`; suggest a restart and `opencode debug skill`; report.
2. «установи parse-report во все инструменты» -> `deploy.sh` to `.opencode/skills/`, `.kilo/skills/`, `.cursor/skills/`; Kilo - `/reload`, opencode and Cursor - restart; report with a verification table.
3. «разверни навык в kilo персонально» -> `deploy.sh` to `~/.kilo/skills/<name>/`; remind about the trusted status (shell commands work) and `/reload`.
4. «задеплой все навыки хаба себе в opencode симлинками» -> for every `doc/skills/glob-*/` and `doc/skills/hub-*/` directory call `deploy.sh --link` to `~/.config/opencode/skills/<name>`; restart opencode; report.

## References

- `doc/standards/skill_anthropic_standards.md` - skill package format, deploy target reference
- `scripts/deploy.sh` - copies the skill directory to a live directory, replacing an existing copy
- Official documentation: `opencode.ai/docs/skills`, `docs.kilocode.ai/docs/customize/skills`, `cursor.com/docs/skills`
- `superpowers:writing-skills` - skill authoring and review guidance

## Restrictions

- Deleting repository files and folders means moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` (quarantine, `project_standards.md` 01.01.06), never deletion; clean `.trash/` only on an explicit user request
- Deploy does not change the source, indexes, or standards; with copying there is no automatic sync with the source - redeploy manually; with a symlink the live copy is the source
- One deploy - one skill; for a skill package, repeat for each one named by the user
- The symlink is created absolute: moving the source repository requires redeploy
- The procedure is verified against the official documentation of opencode, Kilo Code, and Cursor (version 2.4+); when tool behavior changes, consult their documentation
