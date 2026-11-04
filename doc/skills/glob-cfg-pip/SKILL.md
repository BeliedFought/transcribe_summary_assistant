---
name: glob-cfg-pip
description: Finds a working PyPI mirror, measures candidate response times, and writes the selected mirror to pip.conf when pypi.org is unreachable. Use when installing dependencies, on package download errors, or when the user asks to configure pip, choose a PyPI mirror, or speed up installation (установка зависимостей, ошибки скачивания пакетов, настроить pip, выбрать зеркало PyPI, ускорить установку)
metadata:
  version: 1.2.0
  status: stable
  type: hub_glob
  category: cfg
  category_name: Configuration
---

# Select and configure a PyPI mirror

Finds a working PyPI mirror on the current machine, measures candidate response times, writes the selected mirror to `~/.config/pip/pip.conf`, and reports the choice to the user. The candidate mirror list is kept in the repository registry `data/registries/pip-mirrors.md` (runtime data canon - `doc/standards/skill_data_standards.md`); the algorithm rule is `project_standards.md` 01.07.

## When to use

- Dependency installation (`pip install`) fails with a network error or download timeout
- `~/.config/pip/pip.conf` is missing or points to a dead mirror
- The user asks to configure pip, choose a mirror, or speed up package installation
- A new project and environment are created (dependency installation step per `project_standards.md` 01.07)

## Instructions

1. Check `~/.config/pip/pip.conf`: if the file exists and its `index-url` answers a fast request (HEAD or a short curl timeout), leave it unchanged and report to the user
2. If the mirror is missing or dead, probe the candidates from `data/registries/pip-mirrors.md` (if the file is missing, create it from the skill template `templates/pip_mirrors.md`), measuring each response time; check the official source last
3. Select the fastest available mirror
4. Write the selected mirror:

```bash
${CLAUDE_SKILL_DIR}/scripts/set_pip_conf.sh <mirror_url>
```

5. Report the selected mirror and the reason for the choice (response time) to the user

## Candidate registry

The candidate mirror list is the repository registry `data/registries/pip-mirrors.md` (domain `pip-mirrors`, ownership marker `generated-by: glob-cfg-pip`). Maintenance rules:

- on the first run in a repository, the registry is created from the template `templates/pip_mirrors.md`
- when a dead URL is found, remove it from the registry; when a new stable mirror appears, add it (merge is idempotent by key)
- durable changes to the candidate set for all repositories go through the template `templates/pip_mirrors.md` in the `project_standards` hub; a single repository registry is updated by the skill itself

## Completion criteria

- `~/.config/pip/pip.conf` exists and points to a responding mirror
- The user is told the selected mirror and response time
- Dependency installation succeeds

## Examples

- «pip не может скачать пакеты» -> check pip.conf, probe candidates, write the best mirror, retry installation
- «настрой зеркало pip на этой машине» -> run steps 1-5 without installing packages

## Restrictions

- Deleting repository files and folders means moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` (quarantine, `project_standards.md` 01.01.06), never deletion; clean `.trash/` only on an explicit user request
- The script overwrites `~/.config/pip/pip.conf` entirely - before writing, make sure the current config does not respond (step 1)
- The script changes only the user pip configuration; the repository and its files are not touched

## References

- `templates/pip_mirrors.md` - initial candidate registry template (materialized to `data/registries/pip-mirrors.md` on the first run)
- `scripts/set_pip_conf.sh` - writes the selected mirror to `~/.config/pip/pip.conf`
- `doc/standards/project_standards.md` (section 01.07) - dependency installation algorithm rule
- `doc/standards/skill_data_standards.md` - skill runtime data canon (registry `data/registries/`)
- `doc/standards/skill_anthropic_standards.md` - skill package format and quality requirements
- `superpowers:writing-skills` - skill authoring and review guidance
