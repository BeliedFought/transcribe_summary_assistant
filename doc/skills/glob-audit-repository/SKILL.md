---
name: glob-audit-repository
description: Performs a two-level audit and repair of a repository against the standard, honoring recorded project overrides - a subagent checks the codebase, the agent classifies deviations, runs the reverse check of doc/specs/spec_ui.html, agrees changes with the user, applies them, and updates documentation. Focus - texts, output, logs, security, obvious errors, package version sync, specification freshness. Use when the user asks to check a repo, run an audit, find gaps against the standard, verify compliance, reverse spec_ui, check specification freshness, fix code, update documentation, audit before release (проверить репо, провести аудит, найти расхождения со стандартом, проверить соответствие, реверс spec_ui, актуальность спецификаций, исправить код, обновить документацию, аудит перед релизом)
metadata:
  version: 2.6.1
  status: stable
  type: hub_glob
  category: audit
  category_name: Audit
---

# Two-level repository audit and repair

A two-level process for auditing and repairing any repository built on `project_standards.md` (UI contract - `console_ui_standards.md`):

1. **Subagent** - checks the codebase only (no documentation), returns a raw list of deviations
2. **Agent** - takes the subagent report, classifies deviations into 3 groups, runs the mandatory reverse check of `doc/specs/spec_ui.html` against the code per `console_ui_standards.md`, agrees the changes with the user, applies them, updates documentation

**Audit focus:** texts (04.03), output and frame (`console_ui_standards.md`, 04.04), logs (04.04.01, 04.06), security (05), obvious errors and logic bugs, standards package version sync (AGENTS/CLAUDE/README vs _index_standards.md), specification freshness (`doc/specs/` of the project and active sessions). Do not nitpick details outside the focus.

**Overrides are not violations.** A project may contain many agreed deviations from the standard (overrides). A deviation explicitly recorded as an override under the standard rules is not a non-compliance and is not flagged as a violation. Overrides are collected before the check and excluded from the noise; only their registration is checked when needed (stage 1, step 2).

## When to use

- The user asks to check a repository against the standard, run an audit, or review compliance
- The user asks to find gaps between the code and the standard
- The user requests an audit before a release, refactoring, or a standard update
- The user points to the skill explicitly via `@doc/skills/glob-audit-repository/SKILL.md` or by the name `glob-audit-repository`

## Instructions

### Prerequisites

- Working directory - the root of the audited project (opened by the agent automatically)
- `doc/standards/project_standards.md` is present - the source of truth
- Read and write access to all repository files

### Stage 1. Subagent: codebase check

The agent starts a subagent instructed to check the codebase only (no documentation or git infrastructure).

**Subagent task:**

0. Before the main work, read `doc/standards/_index_standards.md` and apply the standards found there throughout the work.
1. Read all files in `doc/standards/` in full. Determine the standards package version from `doc/standards/_index_standards.md`.
2. **Collect the project override registry** - agreed deviations from the standard recorded explicitly. Sources:
   - the "Standard overrides" block in `SESSION.md` (for session structures - section 01.01.01);
   - `doc/specs/overrides.md` (project override registry - section 01.01.02);
   - the methodology section and temporary exceptions in `doc/specs/spec_ui.html` (temporary digit exceptions, domain rules, statuses, units - `console_ui_standards.md` (02.03, 02.04, 02.05, 04.04));
   - explicit marks "temporarily" / "exception" / "override" / "agreed" in code and configs with a rationale.
   A registered override contains: a reference to the standard section, the deviation text, a rationale, and a note that the user agreed. Put the registry at the start of the raw report.
3. Study all sections of `project_standards.md` and other standards in `doc/standards/`. Determine which sections and standards are relevant to the project (by project nature: DB, API, AI, email, and so on). Do not check irrelevant standards in the report.
4. Build a complete list of codebase files (all files not excluded by `.gitignore`, including `.env.example`, `.python-version`, `pyproject.toml`, `config.ini`, `config.ini.example`). Exclude session folders (with `SESSION.md` at the root) and `.arch/`: the subagent does not check session code or artifacts.
5. Check every file against the applicable standard requirements. **Main focus:** texts (04.03), output and frame (`console_ui_standards.md`, 04.04), logs (04.04.01, 04.06), security (05), obvious errors and logic bugs, **package version sync** (`AGENTS.md`, `README.md`, `CLAUDE.md` if present - the `Standard version:` or `Соответствует стандарту:` line must match _index_standards.md). Take requirements from the standard text, not from a hardcoded list. For each deviation, state the exact standard section the requirement comes from. **A deviation covered by a registered override from step 2 is not a violation and is not reported as a deviation**; if the override is incomplete (no rationale, reference, or agreement note), report it separately as "override needs registration", not as a standard violation. **Text deviations in non-console contexts** (web, rich, custom UI) mark as "C: text override - <context>" in the raw report - the agent classifies them into group C, not group A.

6. Write the raw report to `doc/agent_questions/audit_raw_{STANDARD_VERSION}.md` listing every deviation in the format:
   - File:path:line
   - Standard section: 0X.0Y
   - Problem description
   - Recommendation

**The subagent does not check:**
- Documentation (README.md, AGENTS.md, CLAUDE.md)
- Git infrastructure (.gitignore, .venv/)
- Standard versioning in documentation

### Stage 2. Agent: classify deviations and reverse the UI mockup

The agent reads the subagent raw report and determines the project baseline standard version:
- Read `AGENTS.md`, `CLAUDE.md`, or `README.md` (the `Standard version:` or `Соответствует стандарту:` line) - this is the baseline the project was built for
- Compare the baseline with the current version from `doc/standards/_index_standards.md`
- If versions differ, determine which requirements appeared in the current version compared with the baseline (read the standards and extract new or changed requirements)
- Matching package versions **do not cancel** the UI mockup reverse check and the applicable output rule check

**Mandatory reverse check of `doc/specs/spec_ui.html` (regardless of the package version diff and the application version):**

Reverse-check rules - `doc/standards/console_ui_standards.md` (plus anchors in `project_standards.md` 01.01 / 04 / 07).

1. The file exists and declares its own mockup SemVer (`Версия макета`)
2. Completeness: TOC; navigation map or output point map; console/screen frames; log frames; project methodology; **footer with the full absolute path** (`xdg-open` / `file://`)
3. Check against the code per `console_ui_standards.md`: frame order (breadcrumb -> items -> body -> empty -> `[>]` at the bottom; full `clear_screen` without the previous body tail; **no** ANSI cursor tricks CUP/CSI s/u/DECSTBM; clear right after `input()`; body from re-read state); keys (digits only for table rows; the `Z X C V B N M` row; temporary digit exceptions only if explicit in `spec_ui`); breadcrumb without `---`; styling roles; semantic action log; lists/summaries/tables (plain output takes priority over tabulate in the log)
4. A mockup outdated against the code, or a mockup edit without a SemVer bump - a deviation (group A or B by impact)
5. A missing `spec_ui.html` or a footer without the absolute path - a group B deviation (mandatory standard artifact). Exception - the `project_standards` hub template: its footer contains the placeholder `/home/<user>/<repo>/` and is not a deviation

**Specification freshness (after the mockup reverse check):**

Scope: `doc/specs/*.md` at the project root, `doc/specs/init/*.md` (start specifications), and `doc/specs/*.md` of active sessions (status "active" in the session `SESSION.md`). `spec_ui.html` is covered by the reverse check above, `overrides.md` - by the override registry. Sessions with a status other than "active" and `.arch/` are out of scope; the report has one line "skipped: session inactive".

For each specification, check against the current code and structure:
- files, modules, and folders mentioned in the specification exist
- the described behavior matches the actual code behavior
- completed items and decisions are marked as done

An outdated specification or one that contradicts the code - a group A deviation stating what diverged (07.01 item 3: documentation reflects the current state).

Then the agent classifies each deviation (from the subagent report and the mockup reverse check) into one of three groups:

**Overrides are not classified as violations.** Deviations covered by registered overrides from the registry (stage 1, step 2) do not fall into groups A/B/C. Only overrides with incomplete registration (no standard section reference, rationale, or agreement note) appear in a separate "Overrides" report block - that is an override registration problem, not a standard violation. Correctly registered overrides do not appear in the report (or appear as one line: "N overrides registered, registration checked").

**Group A: Text problems** (non-critical for logic, important for aesthetics)
- Violations of standard formatting requirements for console output and log text (characters, punctuation, case)
- Violations of marker and output styling requirements
- Violations that do not affect program operation but break output uniformity
- Outdated specifications in `doc/specs/` (documentation does not reflect the current state - 07.01 item 3)

**Text overrides in non-console contexts** (web interfaces, rich menus, custom UI, graphic elements) are not group A violations. Text deviations in such contexts are often deliberate design decisions and go to group C as low-priority notes - without a hard fix requirement. When the subagent finds a text deviation in a non-console context, it marks it as "C: text override - <context>".

**Group B: Critical code problems** (affect security, correctness, reliability)
- Security violations (secrets, injections, missing validation)
- Violations of error handling and correct termination
- Violations of structure, configuration, and file sync
- Package version mismatches between **present** locations (AGENTS, README, CLAUDE if present - do not match _index_standards.md)
- Violations that may cause failures, data leaks, or incorrect operation

**Group C: Possible improvements for new standards** (optional, only by agreement)
- Standard requirements that appeared in a new version and were absent from the project before
- Improvements that are not violations but are recommended by the new standard
- New patterns and approaches introduced in the current standard version
- i18n violations (output bypassing the translation system)
- Text overrides in non-console contexts (web, rich menus, custom UI) - low priority, often deliberate design decisions

The agent builds a classified report and presents it to the user in chat as numbered groups with checkboxes for easy selection:

```
## Результаты аудита кодовой базы

### Группа A: Текстовые проблемы (N найдено)
1. src/main.py:42 - точка в конце сообщения лога (04.05)
2. src/utils.py:15 - длинное тире в сообщении вывода вместо дефиса (04.05)
3. src/menu.py:57 - многоточие в пункте меню вместо явной формулировки (04.03)

### Группа B: Кодовые критические проблемы (N найдено)
1. src/db.py:78 - SQL-инъекция, конкатенация пользовательского ввода (03.01)
2. config.ini:12 - секрет в конфиге, должен быть в .env (05.01)
3. AGENTS.md:3 - версия 4.7.0 не совпадает с _index_standards.md 4.9.0 (01.03)
4. src/cli.py:64 - код завершения 3 вне допустимых значений 0 / 1 / 2 (05.03)

### Группа C: Возможные доработки под новые стандарты (N найдено)
1. src/localization.py:25 - отсутствует плюрализация через count (новая возможность 04.01)
2. src/app.py:60 - вывод текста напрямую, минуя систему переводов (04.01)
3. src/table_view.py:19 - таблица в логе через tabulate, приоритет plain вывода не учтен (новая возможность 04.04)

Выберите что исправить:
  1. Группа A: Текстовые проблемы
  2. Группа B: Кодовые критические проблемы
  3. Группа C: Возможные доработки (обсудим каждую отдельно)
  4. Все группы (A + B + C)
  5. Только выбранные пункты (укажите номера)
```
The agent uses the `question` tool to offer the user a choice when multi-select is available in chat.

### Stage 3. Agreement with the user

The agent shows the classified report (format above) and uses the `question` tool to offer groups or specific items:

- Group A (text) - fast and safe, recommended for fixing
- Group B (critical) - mandatory to consider, includes security, errors, package version mismatches
- Group C (improvements) - optional, each discussed separately
- All groups at once (A + B + C)
- Specific items by number

The user may choose any option. The agent applies no changes without an explicit user choice.

### Stage 4. Applying changes

The agent applies the agreed changes to the codebase:
- For each problem in the agreed list, apply the recommendation from the subagent report
- After the changes, run the linter and type checker if available
- Record the list of changed files

### Stage 5. Documentation update and version sync

After the code changes, the agent updates documentation:

1. **README.md:**
   - Update the project file list if new files appeared
   - Update command descriptions if behavior changed
   - Update the application version if it changed
   - Make sure every mentioned file actually exists
   - Check the explicit reference to `doc/specs/spec_ui.html` as the menu map source (`repo_info_doc_standards.md`, 02.03; the menu map is not duplicated in README)

2. **Specifications (`doc/specs/*.md`, including session specifications in active sessions):**
   - Refresh outdated specifications from the agreed group A list: bring them in line with the code and structure
   - Mark completed items and decisions as done
   - Do not touch specifications of inactive sessions

3. **`doc/specs/spec_ui.html`:**
   - Sync with the current output code per `console_ui_standards.md`
   - On changes to frames/map/log/methodology, bump the mockup SemVer
   - The footer with the full absolute file path is mandatory

4. **AGENTS.md and CLAUDE.md (if present):**
   - A missing `CLAUDE.md` when only `AGENTS.md` exists is **not a deviation**; do not recommend creating `CLAUDE.md` (policy - `index_nav_standards.md`, 07.03)
   - If both files exist, sync them with each other (except H1 and the purpose block)
   - Update the skill registry if new skills appeared
   - The standard version in AGENTS (and CLAUDE if present) must match `_index_standards.md` (package bump - only on an explicit user request)

5. **Package version sync:**
   - Package version mismatches are fixed as part of group B (see stage 2)
   - At this stage, verify that the version in `doc/standards/_index_standards.md` matches AGENTS, README, and CLAUDE (if present) after all changes
   - Do not bump the package number without an explicit user request

6. **Final report:**
   - Write the final report to `doc/agent_questions/audit_{STANDARD_VERSION}_final.md`:
     - List of fixed problems by group (including the spec_ui reverse check)
     - List of changed files
     - `spec_ui.html` mockup version
     - Package version sync status

## Completion criteria

- The subagent checked the codebase and created `audit_raw_{VERSION}.md`
- The agent ran the `spec_ui.html` reverse check against the code and classified deviations into 3 groups
- Specification freshness is checked: `doc/specs/` of the root and active sessions; inactive sessions are marked as skipped
- The user agreed the fix list
- The agreed changes are applied to the codebase
- Documentation (README, AGENTS, CLAUDE if present, spec_ui, outdated specifications) is updated to the current code state
- Standards package versions are aligned across locations (no unauthorized bump)
- The final report `audit_{VERSION}_final.md` is created
- A short summary is posted to chat: what was fixed, which files changed, mockup and version status

## Audit principles

- **Thoroughness within the focus:** the goal is to find real gaps in texts, output, logs, security, and obvious errors, not to confirm compliance or nitpick details outside the focus
- **Overrides are not violations:** an explicitly agreed deviation registered as an override under the standard rules is not a non-compliance; do not raise noise for every override, check only its registration
- **Text overrides outside the console are group C:** text deviations in web interfaces, rich menus, and custom UI are low priority, not group A
- **Doubt means a question:** when the interpretation is ambiguous, mark it as a question, not a violation
- **Two levels:** the subagent checks the code, the agent classifies and agrees
- **Agreement:** no changes are applied without explicit user consent
- **Specificity:** a recommendation must be an action, not a statement
- **Completeness:** after the changes, documentation and `spec_ui.html` must reflect the current code state
- **Mockup reverse check:** the presence and freshness of `spec_ui.html` are checked always, not only on a standards package version mismatch
- **Specification freshness:** specifications in `doc/specs/` of the project and active sessions are checked against the code and fixed as part of the audit
- **Sessions mean specifications only:** session code and artifacts are not audited; only `doc/specs/` of an active session is checked and fixed; inactive sessions and `.arch/` are not touched

## Examples

1. User: «проверь репо на соответствие стандарту» -> the agent starts a subagent to check the code, gets the raw report, classifies it into 3 groups, shows it to the user, agrees the changes, applies them, updates the docs, syncs versions.
2. User: «проведи аудит перед релизом» -> the subagent checks the code, the agent classifies, the user selects only group B (critical), the agent applies the critical fixes and updates the docs.
3. User: «исправь все текстовые проблемы» -> the subagent checks the code, the agent classifies, the user selects only group A, the agent applies the text fixes and updates the docs.

## Restrictions

- Deleting repository files and folders means moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` (quarantine, `project_standards.md` 01.01.06), never deletion; clean `.trash/` only on an explicit user request
- Do not edit `doc/standards/project_standards.md` - it is the source of truth
- The subagent checks the codebase only, not documentation
- Session folders (with `SESSION.md`) and `.arch/` are excluded from the code audit; only `doc/specs/` of an active session is checked and fixed
- The agent applies no changes without user agreement
- Group C (improvements for new standards) is discussed item by item
- Registered overrides are not flagged as violations; only their registration is checked
- Do not flood the report with noise for every override - correctly registered overrides do not appear in groups A/B/C
- If the project has no `doc/standards/project_standards.md`, tell the user that the skill applies only to projects built on this standard and stop

## References

- `doc/standards/project_standards.md` - core standard; audited sections are named in the stage text
- `doc/standards/console_ui_standards.md` - UI contract, `spec_ui.html` reverse check
- `doc/standards/_index_standards.md` - standards package registry and version
- `doc/standards/skill_anthropic_standards.md` - skill package format and quality requirements
- `superpowers:writing-skills` - skill authoring and review guidance
