---
name: glob-mine-lesson
description: Records a lesson in the lesson journal data/lessons.md - transferable experience from project work: a technique, a library or environment trap, a non-obvious solution and its reason. An entry pairs a concrete context with a generalized lesson for a class of situations. Use when the user asks to record a lesson, write down a technique or experience, or when the agent finds knowledge useful for other projects (зафиксировать урок, записать урок, отметить прием или опыт)
metadata:
  version: 1.0.1
  status: stable
  type: hub_glob
  category: mine
  category_name: Knowledge Mining
---

# Record a lesson in the journal

Adds transferable experience to the repository lesson journal `data/lessons.md` (journal canon - `project_standards.md`, section 01.01.07). The journal is the knowledge accumulation point for enriching the standards hub: candidate collection from a project is done by the `hub-mine-knowledge` skill in the hub. The skill only adds entries and changes nothing else in the repository.

## When to use

- The user asks to record a lesson, write down a lesson or experience, or note a technique
- Transferable knowledge is found during work: a technique, a library or environment trap, a non-obvious solution - something useful in other projects
- The user explicitly invokes the skill by the name `glob-mine-lesson`

## Instructions

1. Read `doc/standards/_index_standards.md` and apply the standards found there; text requirements for an entry are in `project_standards.md` (section 04.03)
2. Check whether `data/lessons.md` exists; if not, create it from the header template below
3. Form a "context - lesson" pair:
   - context - the specifics of the situation: file and line, commit, task, machine, version; any details are allowed - the journal stays inside the repository
   - lesson - a generalized statement for a class of situations (architecture, OS family, library version range, device class); without machine and user names, addresses, and paths of a specific machine
4. Apply the value test: will the lesson recur in the next project. Knowledge tied only to this environment instance is a candidate for a project override (`doc/specs/overrides.md`, section 01.01.02), not for the journal; offer this option to the user instead of an entry
5. Determine the lesson class: rule (a norm missing from the standards package), example (a reference code or configuration fragment), dictionary (text dictionary additions), skill (a repeatable procedure)
6. Append the entry to the end of the journal using the template; the number is the next sequential one
7. Tell the user the entry number and summary; commit - on the user request or per repository rules

## Templates

File header on creation:

```markdown
# Журнал уроков

Переносимый опыт проекта; канон - project_standards.md, раздел 01.01.07
```

Entry template:

```markdown
## <NN>. <title>

- Дата: <YYYY-MM-DD>
- Источник: <source>
- Контекст: <context>
- Урок: <lesson>
- Класс: правило | пример | словарь | навык
- Кандидат в хаб: да | нет
```

## Examples

1. User: «зафиксируй урок» after solving a driver problem -> the agent records the context with the device class and driver version, and the lesson as a flag requirement for the whole device class on this architecture; class "rule", hub candidate - yes
2. The agent finds a library workaround not described in the documentation -> offers the user to record a lesson, and after confirmation adds an entry with class "example"

## Restrictions

- The skill only adds entries to `data/lessons.md`; existing entries are not edited or deleted
- Journal archiving - only on an explicit user request
- Deleting repository files and folders means moving them to `.trash/<slug>_<YYYYMMDDHHMM>/` (quarantine, `project_standards.md` 01.01.06), never deletion; clean `.trash/` only on an explicit user request

## References

- `doc/standards/project_standards.md` - section 01.01.07: lesson journal canon
- `doc/skills/hub-mine-knowledge/` - knowledge collection from the journal and codebase for hub enrichment (hub only)
- `doc/standards/skill_anthropic_standards.md` - skill package format and quality requirements
- `superpowers:writing-skills` - skill authoring and review guidance
