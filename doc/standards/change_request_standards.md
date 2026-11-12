# Change Requests (CR). Version 5.2.0

Canon for incoming change requests (`doc/change_requests/`): purpose and place in the workflow, folder and naming, document skeleton, lifecycle, transfer to a live specification, and directory index. The document supplements `project_standards.md` and applies on top of it. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

The canon for navigation documents (indexes) is `index_nav_standards.md`.

---

## Table of Contents

**01. Purpose and place in the workflow:** 01.01 Purpose - 01.02 Boundary with adjacent documents - 01.03 Execution flow

**02. Folder and naming:** 02.01 Folder and committability - 02.02 File naming - 02.03 Directory index

**03. CR document skeleton:** 03.01 Header - 03.02 Mandatory base - 03.03 Optional sections - 03.04 Reference skeleton

**04. Lifecycle:** 04.01 Statuses and transitions - 04.02 Approval and execution start - 04.03 Transfer to a live specification and direct execution - 04.04 Archiving and rejection

**05. Text rules**

**06. Relations and versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Purpose

*Mandatory.*

A change request (CR) is an incoming document that records the problem before work on a change begins: context, current state with references to norms, solution options with advantages, constraints and risks, and a recommendation. A CR is the starting point of a task: it decides "what to do and which path to take" - before a live specification is formed and before the execution trigger.

---

## 01.02. Boundary with adjacent documents

*Mandatory.*

- `doc/agent_questions/` - agent clarifying questions during a dialog (`project_standards.md`, 07.02); not a change request
- `doc/specs/spec_<slug>.md` - the live execution specification: use cases, answers to questions, affected components, acceptance criteria (07.02); the CR answers "what and why, by which paths", the spec answers "how to do it"
- `doc/specs/overrides.md` - the standard deviation registry (01.01.02); not a change request
- Sessions (`SESSION.md`, 01.01.01) - the working execution container; a CR and a spec can be executed inside a session but are not sessions themselves

---

## 01.03. Execution flow

*Mandatory.*

1. The problem is recorded in a CR: `doc/change_requests/cr_<slug>.md`
2. The CR is agreed with the user: option selection, answers to open questions, status `согласован`
3. A large task is transferred to a live specification `doc/specs/spec_<slug>.md` (same slug, different prefix - 04.03); a small task is executed directly after approval
4. Execution starts on the `ДЕЛАЙ` / `GO` trigger (`project_standards.md`, 07.02); execution progress is tracked in the spec, not in the CR
5. Final step - archive the CR in `doc/change_requests/.arch/` (04.04)

---

## 02.01. Folder and committability

*Mandatory.*

CRs live in `doc/change_requests/`. The folder is committed: requests are project artifacts with a git history. The `.arch/` subfolder is a local archive excluded from git (`project_standards.md`, 01.01, 06.01). The transient folder status does not apply to `doc/change_requests/`: it is committed on par with `doc/specs/`.

---

## 02.02. File naming

*Mandatory.*

The file name is `cr_<slug>.md`; `<slug>` is a Latin kebab-case slug without transliteration (`code_standards.md`, 02.01). Request numbers are not maintained - identification is by slug. Slug uniqueness is checked across the whole directory, including `.arch/` (01.01). One CR - one problem; several independent problems get separate CRs.

---

## 02.03. Directory index

*Mandatory.*

The index `doc/change_requests/_index_change_requests.md` is mandatory when the directory exists. Skeleton, registry, and routing map - the canon of `index_nav_standards.md` (03, 04, 05.01, 06). The agent updates the index on any composition change: CR creation, status change, transfer to a spec, archiving, rejection. The index is maintained manually per this canon; the `glob-update-indexes` skill does not regenerate it.

---

## 03.01. Header

*Mandatory.*

The header follows immediately after H1 as a marked list of three fields:

- `Дата`: `YYYY-MM-DD` of creation
- `Статус`: one of 04.01
- `Исполнение`: brief factual state (`не начато`, in progress, `завершено`)

A CR does not keep its own SemVer: change history is in git, lifecycle is tracked through status.

---

## 03.02. Mandatory base

*Mandatory.*

The sections below are present in every CR.

**Проблематика:**

- Context: the scenario and user requirements for the change
- Current state: how it works now, with references to standard sections and files
- Consequences of inaction: what happens if the change is not made

**Варианты решения:**

- Each option is a separate block: description, advantages, constraints and risks
- Options are ordered by preference, the recommended one first
- A recommendation with rationale closes the section

**Затрагиваемое:** files, documents, and components affected by execution

**Открытые вопросы:** what the user must decide before execution; closed questions move into the text of the relevant sections

---

## 03.03. Optional sections

*Mandatory.*

Sections for large or risky tasks; small CRs may omit them:

- `Цели и non-goals`: what must be achieved and what is deliberately outside the task scope
- `Риски исполнения и откат`: how execution can cause harm and how to restore the original state
- `Критерии приемки`: how to verify that the task is executed
- `Журнал согласования`: records "date - decision - summary"; maintained during long approvals with several iterations

---

## 03.04. Reference skeleton

*Mandatory.*

```markdown
# CR: <task-summary>

- Дата: YYYY-MM-DD
- Статус: новый
- Исполнение: не начато

---

## 1. Проблематика

### 1.1. Контекст
<scenario_and_requirements>

### 1.2. Текущее состояние
<current_state_and_refs>

### 1.3. Следствия бездействия
<consequence_of_inaction>

## 2. Варианты решения

### 2.1. <option-title> (рекомендация)
- Описание: <description>
- Достоинства: <pros>
- Ограничения и риски: <risks>

### 2.2. <option-title>
- Описание: <description>
- Достоинства: <pros>
- Ограничения и риски: <risks>

Рекомендация: <option-and-rationale>

## 3. Затрагиваемое

| Объект | Изменение |
|--------|-----------|
| <file-or-component> | <change> |

## 4. Открытые вопросы

1. <open-question>

<!-- Опционально: цели и non-goals, риски исполнения и откат, критерии приемки, журнал согласования -->
```

The CR document language is Russian: headings, field names, and statuses stay Russian as defined in this skeleton.

---

## 04.01. Statuses and transitions

*Mandatory.*

The status is recorded in the header. There are exactly five statuses:

| Status | Meaning |
| ------ | ------- |
| `новый` | created, awaiting discussion and option selection |
| `согласован` | option selected, open questions closed by the user |
| `перенесен в спеку` | the task is transferred to a live specification (04.03) |
| `исполнен напрямую` | a small task executed without a spec (04.03) |
| `отклонен` | the user refused execution |

The final statuses are the last three; a final CR is subject to archiving (04.04).

---

## 04.02. Approval and execution start

*Mandatory.*

- CR discussion happens in preparation mode: options and questions without project mutations (`project_standards.md`, 07.02)
- The user decision is recorded in the CR: selected option, answers to open questions, status change to `согласован` with a date
- Execution starts only on the `ДЕЛАЙ` / `GO` trigger (07.02); the trigger applies to one task
- Revision of an approved CR (new facts, changed requirements) returns the status to `новый` with a reason recorded in the problem statement

---

## 04.03. Transfer to a live specification and direct execution

*Mandatory.*

- Large task: after approval a live spec `doc/specs/spec_<slug>.md` is created - the same slug as the CR, a different prefix; spec composition - `project_standards.md`, 07.02; the spec is registered in `doc/specs/_index_specs.md`. At transfer the CR gets status `перенесен в спеку` and the line "Перенесено в `doc/specs/spec_<slug>.md` (дата)", then is archived
- Small task (one module, several point edits): executed directly per the general rules; the CR gets status `исполнен напрямую` with a date, then is archived
- Execution progress is tracked in the spec and the working dialog, not in the CR: the CR is a path-selection document, not an execution tracker

---

## 04.04. Archiving and rejection

*Mandatory.*

- A final CR is moved to `doc/change_requests/.arch/` immediately upon reaching a final status; the "Archive instead of delete" rule - `project_standards.md`, 01.01
- Transfer is complete, without renaming; the CR row is removed from `_index_change_requests.md` (indexing rule for `.arch/` - 01.01)
- The archived CR slug is considered when checking the uniqueness of new ones
- A rejected CR is supplemented with the rejection reason before archiving - in the problem statement or the approval journal

---

## 05. Text rules

*Mandatory.*

- Language - Russian; style - `project_standards.md` (04.02, 04.03): factual, without evaluations and stories, without emoji and exclamation marks, dashes - hyphen only
- Any reference to a norm states the document and section; a statement about current code behavior states the file
- Solution options are described comparably - the same attribute composition (description, advantages, constraints and risks) so the choice is substantive
- The problem statement is separated from the solution: problem and options are not mixed; the recommendation closes the options section

---

## 06.01. Related documents

| Document | Relation |
| -------- | -------- |
| `project_standards.md` | basis: workflow and triggers (07.02), document placement (01.01), .gitignore (06.01), text style (04.02, 04.03) |
| `index_nav_standards.md` | canon for the `_index_change_requests.md` index (skeleton, registry, routing map) |
| `code_standards.md` | slug rules (02.01) |

---

## 06.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and update rules - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
