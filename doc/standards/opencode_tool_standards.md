# OpenCode Custom Tool Standards. Version 5.0.1

This document defines rules for creating custom tools for opencode: location and naming, registration through a plugin, argument schema, `description` field, thin wrapper over an external script, output and errors for the agent, permissions, and mutations. It supplements `doc/standards/project_standards.md` and applies on top of it.

Adjacent document - `doc/standards/skill_anthropic_standards.md` (SKILL.md skills). Choosing between a custom tool and a skill - 01.02. The opencode plugin file shape (exports, events, cleanup) - `doc/standards/code_standards.md` (03.05). All core standard requirements remain in force unless this document explicitly overrides them.

---

## Table of Contents

**01. Fundamentals:** 01.01 Purpose and applicability - 01.02 Choosing between tool and skill - 01.03 Location - 01.04 Naming

**02. Contract:** 02.01 Tool registration - 02.02 Arguments and schema - 02.03 `description` field

**03. Implementation:** 03.01 Thin wrapper and external script - 03.02 Output for the agent - 03.03 Errors

**04. Security:** 04.01 Permissions - 04.02 Mutations and determinism

**05. Other:** 05.01 Anti-patterns - 05.02 Example - 05.03 Author checklist

**06. Relations and versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Purpose and applicability

*Mandatory.*

A custom tool is a function that the opencode model calls in a dialog on par with built-in tools (`shell`, `read`, `edit`, `grep`, and others). The model sees three contract elements: name, description, and argument schema; the implementation is not available to it. A tool provides access to a deterministic operation without loading a method and without improvising through `shell`.

The primary target tool of this standard is **opencode version 2**; the contract primary source is the Plugins page of the opencode documentation (Tools section, `https://opencode.ai/v2/docs/build/plugins`). Tools with another contract (MCP servers, tools of other agents) are not regulated by this document; their relation - 01.02, 01.03.

The V1 contract (the `tool()` helper from `@opencode-ai/plugin` in `.opencode/tools/`) does not execute in V2: V1 plugin implementations do not work in V2. V1 material is usable only as migration input; new tools are written to the V2 contract (02.01).

Apply this standard when:

- a custom tool is created in a project (`.opencode/plugins/`) or a personal tool (`~/.config/opencode/plugins/`);
- a wrapper over an existing project script is designed for agent invocation;
- an existing custom tool is reviewed or improved;
- a tool is migrated from the V1 contract to V2.

The standard does not apply to: built-in opencode tools, MCP servers (a ready external specification; connection is configuration, not development), and other opencode plugins outside tool registration.

---

## 01.02. Choosing between tool and skill

*Mandatory.*

Tool and skill solve different tasks and do not duplicate each other:

| Aspect | Custom tool | Skill (SKILL.md) |
| ------ | ----------- | ---------------- |
| Essence | Hard contract: name, argument schema, deterministic implementation | Method: instruction, resources, examples |
| What the model sees | Name, `description`, argument schema | `name`, `description`, and on activation - body and resources |
| Agent freedom | Only arguments from the schema | The whole action sequence per the instruction |
| Context load | Description and schema - always | Metadata - always, body - on activation |
| Permissions | Targeted permission gating by tool name (04.01) | Permissions apply to the skill activation tool (`skill`) and the tools called by its instruction |

A skill with a deterministic script (`skill_anthropic_standards.md`, 03.03) is the default way to package project operations: it carries the contract, the method, and the examples. A custom tool is justified when:

- the operation is called often, and loading the skill body every time is excessive;
- strict argument typing is needed: an invocation error is caught by the schema before execution;
- targeted permission gating is needed: `allow` / `ask` / `deny` by tool name;
- the operation is part of repository plumbing (checks, build, generation), not a scenario with a method.

A duplication sign: if a tool wraps a script already wrapped by a skill and adds neither gating nor typing, the tool is not needed. One scenario - one unit: either a skill or a tool; the "skill tells when, tool executes how" combination is allowed when the method is really needed.

An MCP server is the choice when the functionality already exists in a ready server or is needed outside opencode. If the operation is tied to project code and data, a custom tool is preferable: fewer external dependencies, and the repository controls the contract.

---

## 01.03. Location

*Mandatory.*

In V2 custom tools are registered by an opencode plugin. Project plugins are discovered in `.opencode/plugins/` automatically (direct `.ts` / `.js` files and plugin package directories); additionally a plugin is connected by an entry in the `plugins` array of `opencode.json(c)`.

| Scope | Directory | Storage |
| ----- | --------- | ------- |
| Project plugins | `<repo>/.opencode/plugins/` | In the repository, committed with the project |
| Personal plugins | `~/.config/opencode/plugins/` | Outside repositories, on the machine |

Rules:

- A project plugin with tools (tied to repository code, scripts, and data) lives only in `.opencode/plugins/` of that repository. A personal plugin (repository-independent) lives in `~/.config/opencode/plugins/`.
- One plugin - one domain: the plugin registers a group of homogeneous domain tools and sets a namespace (01.04).
- External script sources called by the tool are stored in the project structure (`run/`, `src/` per the core standard), not inside `.opencode/plugins/`; the plugin directory contains only contract registration code.
- In a non-runnable repository (the standards hub) there are no `run/` and `src/` directories: an executable tool script is placed in `doc/skills/<name>/scripts/` or another repository script location; in derivative projects - `run/` or `src/`.
- `.opencode/tools/` is the V1 contract registration point; it is not used in V2. New tools are not created in `.opencode/tools/`.
- The tool name is set by the `name` field in the definition, not by the file name; the plugin file name carries the plugin `id` (01.04).
- A custom tool with the effective name of a built-in tool overrides it - **forbidden** without an explicit user request; to disable a built-in tool use a `permissions` entry, not an override (04.01).
- Cross-tool logic (argument validation, path protection, env substitution, modification of all tool calls) lives in the plugin through `ctx.tool.hook("execute.before")` / `ctx.tool.hook("execute.after")` hooks, not in each tool. The extraction sign: the rule is needed by all tools at once.
- Plugin logging is structured and does not pollute the tool result; plugin `console.log` does not reach the call result, diagnostics use `console.error` (`code_standards.md`, 03.05).

---

## 01.04. Naming

*Mandatory.*

| Object | Rule | Example |
| ------ | ---- | ------- |
| Plugin (`id`) | Latin, lowercase, domain from general to specific; a dot prefix is allowed | `reports`, `db`, `company.guard` |
| Tool (`name`) | Latin, `snake_case`, verb + object | `run_report`, `check_connection` |
| Namespace | `editor.namespace` or `options.namespace`; domain prefix for a tool group | `reports`, `db`, `etl` |
| Effective name | `<namespace>_<name>` when a namespace is set; otherwise `name` | `reports_run_report` |
| Arguments | `snake_case`, unambiguous, with a qualifier instead of a bare noun | `report_name`, `source_db`, not `name`, not `db` |

opencode replaces dots in the namespace and invalid characters in the name with `_`. The effective name is what the model sees and what permissions reference (04.01).

The name must distinguish the tool among neighbors: overlapping names and purposes confuse the model when choosing. The name reflects the operation, not the implementation: `search_logs`, not `grep_wrapper`.

---

## 02.01. Tool registration

*Mandatory.*

The only canonical form is a plugin from the `@opencode/plugin` package that registers tools in `setup` through the synchronous `ctx.tool.transform` transform:

```typescript
import { Plugin } from "@opencode/plugin"

export default Plugin.define({
  id: "reports",
  setup(ctx) {
    ctx.tool.transform((editor) => {
      editor.namespace({ name: "reports", description: "Project report catalog tools" })
      editor.add({
        name: "run_report",
        description: "Brief description of purpose and applicability (02.03)",
        input: {
          type: "object",
          properties: {
            report_name: { type: "string", description: "Report name from the project report catalog" }
          },
          required: ["report_name"],
          additionalProperties: false
        },
        options: { codemode: true },
        async execute(input, context) {
          // run the external script and shape the response only
        }
      })
    })
  }
})
```

Rules:

- Tool definition: `name`, `description`, `input` (argument schema), `execute`, optionally `output` (structured result schema) and `options`.
- `options`: `namespace` (group name when not set through `editor.namespace`), `codemode` (tool availability in Code Mode), `permission` (permission action name when it must differ from the tool effective name).
- The transform is synchronous and replayable: inside the callback - registration only, without I/O, network access, and one-time side effects. External data is loaded before registration and captured in the callback; when data changes, call `ctx.tool.reload()`.
- The implementation receives `input` (schema-validated) and `context`: `sessionID`, `agent`, `messageID`, `id`, `signal`, `progress`. The working directory and project root come from `ctx.location` (`ctx.location.directory`, `ctx.location.project.canonical`) in `setup`; **requiring the project path from the model as a parameter is forbidden**.
- `context.signal` is an `AbortSignal` for cancellable operations; pass it to `fetch` and child process launches so session stop stops the work.
- `context.progress(metadata)` is an intermediate status for the interface; it does not reach the tool result.
- The result is a `Tool.Result` object: `content` (a string or `text` / `file` parts, 03.02), `output` (structured data matching the `output` schema), `metadata` (service data for the client, not shown to the model).
- The wrapper contains no business logic (03.01) and creates no side effects beyond the script call.
- The argument schema is JSON Schema; an acceptable alternative is Standard Schema (Zod) or Effect Schema (02.02).
- `editor.update` / `editor.remove` / `editor.list` / `editor.get` edit and remove previously registered tools; a registration lives as long as the plugin and is removed when the plugin unloads.

---

## 02.02. Arguments and schema

*Mandatory.*

- The argument schema (`input`) is a JSON Schema object: `type: "object"`, `properties`, `required`, `additionalProperties: false`; every field has a `description` key.
- An acceptable alternative to JSON Schema is Standard Schema (Zod) or Effect Schema; in this case field descriptions are set through `.describe()`. The canon is JSON Schema: it matches opencode documentation and needs no dependency.
- The model reads the argument description: format, units, allowed values.
- Minimum required arguments: only what the model cannot know itself (report name, entity identifier). Everything else gets defaults inside the implementation.
- Composite schemas (`enum`, `oneOf`) are described in the field `description` by listing allowed values.
- A correct call example goes in the field or tool `description` when the input format is non-obvious.
- Forbidden: flag arguments duplicating permissions (secrets, destructive confirmation are not arguments but `permissions` entries, 04.01); session context arguments and project path arguments (02.01).

---

## 02.03. `description` field

*Mandatory.*

`description` is the main factor in tool selection by the model; write for the model, not for a human. Canon:

- what the tool does, then when to apply it and when not to;
- what it returns and in what volume;
- constraints: read-only or mutation, environment requirements, call cost;
- concrete wording from real user requests;
- no marketing ("powerful", "easy to use") and no implementation retelling.

| Bad | Good |
| --- | ---- |
| `Runs a report` | `Generates a report by name from the project report catalog as HTML, Excel, and JSON in output/. Use when the user asks for a ready report by name. Does not run ad-hoc SQL - use execute_mssql for that` |
| `Database tool` | `Checks connections to all databases from the db_* config sections and prints each status. Read-only. Use when diagnosing connectivity before queries` |

Wording is part of the contract: on repeated model invocation errors, fix the tool `description` and schema field descriptions, not the implementation (see checklist, 05.03).

---

## 03.01. Thin wrapper and external script

*Mandatory.*

The tool definition is TypeScript, the logic is in the project language. The wrapper does exactly three things: describes the contract, runs the external script, and shapes the response.

```typescript
import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"
import { promisify } from "node:util"
import path from "node:path"

const run = promisify(execFile)

export default Plugin.define({
  id: "reports",
  setup(ctx) {
    const projectDir = ctx.location.directory
    ctx.tool.transform((editor) => {
      editor.namespace({ name: "reports", description: "Project report catalog tools" })
      editor.add({
        name: "run_report",
        description: "See section 02.03",
        input: {
          type: "object",
          properties: {
            report_name: { type: "string", description: "Report name from the report catalog" }
          },
          required: ["report_name"],
          additionalProperties: false
        },
        async execute(input, context) {
          const { report_name } = input as { report_name: string }
          const script = path.join(projectDir, "run", "reports", "build_report.py")
          const { stdout } = await run("python3", [script, "--name", report_name], { signal: context.signal })
          return { content: stdout.trim() }
        }
      })
    })
  }
})
```

Rules:

- All logic is in the external project script (`run/`, `src/`); the wrapper has no business logic. The script is testable and reusable independently of opencode.
- The script does not depend on the current working directory - only on passed arguments and the path from `ctx.location`.
- Script output and text follow `cli_output_standards.md`: human status uses `report`; logs and parsable streams use `plain` (`YYYY-MM-DD HH:MM:SS [marker] message`, monochrome, no ANSI, no frames, markers `[!]` / `[i]` / `[*]`); automation uses `--porcelain`. English is the default; Russian is allowed through the locale or a project override (04.03). Typography: no trailing period, no diaeresis letter, hyphen-minus only. Exit codes 0 / 1 / 2 (`project_standards.md`, 04.02-04.04, 05.03); the wrapper result format is 03.02 of this document.
- Script dependencies are in the project dependencies (`requirements.txt`); the plugin adds no dependencies.
- Process launch uses plugin runtime facilities (`node:child_process`, `Bun.spawn`, and similar) with `context.signal` passed; in V2 the `Bun.$` helper is not provided to the plugin, the process is managed by plugin code.
- Script noise (stack traces, progress, timings) is filtered by the wrapper: success - a brief mark, full output only on a non-zero exit code.

---

## 03.02. Output for the agent

*Mandatory.*

The tool result is a `Tool.Result` object:

- `content` - what the model sees: a string or parts `{ type: "text", text }` and `{ type: "file", uri, mime, name? }` for artifacts; the main response channel.
- `output` - structured data matching the definition `output` schema; for programmatic processing and Code Mode calls.
- `metadata` - service data for the client; not shown to the model.

The model reads `content` to choose the next step; design the response for it, not for a human:

- only high-signal data; no technical identifiers (uuid, mime types) unless needed in the call chain; human-readable names instead of surrogate keys when the object is selected by meaning;
- truncation is the wrapper's duty, not the model's: reasonable default volumes, a guide of up to 25 thousand tokens per response; the full volume goes to an artifact file with the path in the response (`file` part);
- `concise` / `detailed` modes - if one tool needs both; identifiers for subsequent calls only in `detailed`;
- the response structure is stable across calls: the same fields in the same order - the model relies on the format;
- pagination or filtering by arguments - for potentially large selections, before the request, not after;
- the intermediate status of a long operation is delivered through `context.progress`, not separate tool calls.

---

## 03.03. Errors

*Mandatory.*

- An error message is a concrete fixable action with a correct input example; no raw codes and stack traces in the tool response.
- An execution error is returned in the result `content` (as a string, with the script `[!]` marker), not thrown as an unhandled exception: the model must see the failure and correct the call.
- An exception is allowed only for unrecoverable infrastructure failures of the plugin itself; the client shows it as a call error.
- Error classes are separated explicitly: usage error (invalid arguments - code 2) and execution error (environment, data - code 1) - `project_standards.md`, 05.03.
- Reproducible diagnostics get a separate read-only tool (`*_check`), not text inside another tool.

---

## 04.01. Permissions

*Mandatory.*

Permissions in V2 are one ordered `permissions` array of `{ action, resource, effect }` records. The last match applies; `effect` is `allow`, `deny`, or `ask`; with no match - `ask`. The base agent policy starts with `{ "action": "*", "resource": "*", "effect": "allow" }`, so restrictions are set by explicit rules after it.

Masks `*` (any string, including `/`) and `?` (one character) apply to both `action` and `resource`.

```jsonc
{
  "permissions": [
    { "action": "reports_run_report", "resource": "*", "effect": "allow" },
    { "action": "db_execute", "resource": "*", "effect": "ask" },
    { "action": "deploy_*", "resource": "*", "effect": "ask" }
  ]
}
```

Rules:

- The custom tool action is its effective name (01.04), for example `reports_run_report`; `options.permission` overrides the action name when needed.
- A read-only tool is the default and may be `allow`; a mutating and destructive tool gets a record with at least `ask`. Automatic launch (`allow`) only for idempotent read-only operations.
- Permissions can be narrowed per agent: `agents.<id>.permissions` are appended after the general ones and do not replace them.
- Disabling a built-in tool uses a `{ "action": "<name>", "resource": "*", "effect": "deny" }` record, not an override.
- MCP tools use the action `<server>_<tool>`.
- Secrets go through environment variables and config substitutions; there are no secrets in `description`, schema, or plugin code (`project_standards.md`, 05).
- Minimal tool set in context: remove unused tools (`editor.remove`), not just disable them - every description consumes context at every step.

---

## 04.02. Mutations and determinism

*Mandatory.*

- Deterministic behavior is preferable to model choice: if the required action is known, the decision is fixed in the implementation, not passed as an argument for the model to decide.
- Idempotency: a repeated call with the same arguments does not change the environment result again; non-idempotent operations - only through `ask`.
- Mutating operations support `--dry-run` per the core standard (`project_standards.md`, 03.01); the mode is passed as an argument marked in the field description.
- Do not store state between tool calls: each call is self-sufficient, intermediate data goes to project files or project storage; plugin state is `ctx.storage`.

---

## 05.01. Anti-patterns

*Mandatory.*

| Anti-pattern | Correct |
| ------------ | ------- |
| One-to-one REST API wrapper (one tool per method) | Tools for agent work scenarios; fewer and more capacious |
| `list_*` where search is needed | `search_*` with a filter and relevant rows |
| A stub description of one phrase | WHAT + WHEN + constraints (02.03) |
| Raw stack trace in the response | A fixable action and a correct input example (03.03) |
| Full dump of logs and test output | A brief mark, an artifact with a path, full output only on error (03.02) |
| The model truncates output itself (`head`, arbitrary limits) | Truncation defaults in the wrapper (03.02) |
| Overlapping tools with vague purposes | Distinct clear purposes; merge overlaps |
| Overriding a built-in tool | Forbidden without an explicit request; disable through `permissions` (01.03) |
| Business logic in plugin code | Logic in the external project script (03.01) |
| Script dependency on cwd and absolute machine paths | Arguments and a path from `ctx.location` (03.01) |
| I/O inside `ctx.tool.transform` | Load data before registration, call `reload()` on change (02.01) |
| Project path as a model parameter | `ctx.location.directory` / `project.canonical` (01.03, 02.01) |
| Tool name from the file name | The name is set by `name`; the file carries the plugin `id` (01.04) |
| Secrets in the schema, code, or `description` | Environment variables and project config (04.01) |
| Duplicating a skill with a tool without new properties | One unit per scenario; the combination only for real benefit (01.02) |
| A "just in case" tool with no real calls | Remove it; agent context is a limited resource (04.01) |

---

## 05.02. Example

A project report dispatcher plugin: a thin wrapper over an existing project script, one plugin per domain with a namespace.

```text
<repo>/
├── .opencode/
│   └── plugins/
│       └── reports.ts           # domain tool registration
├── run/
│   └── reports/
│       └── build_report.py      # implementation: SQL, HTML, Excel, JSON
└── opencode.jsonc               # project permissions
```

`reports.ts`:

```typescript
import { Plugin } from "@opencode/plugin"
import { execFile } from "node:child_process"
import { promisify } from "node:util"
import path from "node:path"

const run = promisify(execFile)

export default Plugin.define({
  id: "reports",
  setup(ctx) {
    const projectDir = ctx.location.directory
    ctx.tool.transform((editor) => {
      editor.namespace({ name: "reports", description: "Project reports" })
      editor.add({
        name: "run_report",
        description:
          "Generates a ready project report by name: writes HTML, Excel, and JSON to output/ and returns paths and KPIs. " +
          "Use when the user asks for a ready report by name from the report catalog. " +
          "Does not run arbitrary SQL - use database tools for data exploration",
        input: {
          type: "object",
          properties: {
            report_name: { type: "string", description: "Report name from the project report catalog, for example items_units_diff" },
            dry_run: { type: "boolean", description: "true - show the plan without writing files; default false" }
          },
          required: ["report_name"],
          additionalProperties: false
        },
        options: { codemode: true },
        async execute(input, context) {
          const { report_name, dry_run } = input as { report_name: string; dry_run?: boolean }
          const script = path.join(projectDir, "run", "reports", "build_report.py")
          const args = [script, "--name", report_name]
          if (dry_run) args.push("--dry-run")
          const { stdout } = await run("python3", args, { signal: context.signal })
          return { content: stdout.trim() }
        }
      })
    })
  }
})
```

`opencode.jsonc`:

```jsonc
{
  "permissions": [
    { "action": "reports_run_report", "resource": "*", "effect": "allow" }
  ]
}
```

---

## 05.03. Author checklist

Before publishing a tool, check:

- [ ] The contract is needed: it does not duplicate a skill and does not wrap an API one-to-one (01.02)
- [ ] The plugin is in the right directory: project - `.opencode/plugins/` of the repository, personal - `~/.config/opencode/plugins/` (01.03)
- [ ] The plugin `id` and tool `name` are declared; the domain namespace is set; the effective name does not conflict with built-ins (01.03, 01.04)
- [ ] Registration goes through `ctx.tool.transform`; the transform is synchronous, without I/O (02.01)
- [ ] The working path comes from `ctx.location`, not from a model parameter (01.03, 02.01)
- [ ] The argument schema is JSON Schema with a description for every field; required arguments are minimal (02.02)
- [ ] `description`: WHAT + WHEN + constraints + response composition (02.03)
- [ ] Logic is in the external script; the wrapper only launches and shapes the response (03.01)
- [ ] The process launch passes `context.signal`; the script does not depend on cwd; output follows `cli_output_standards.md` (`report`, `plain`, or `--porcelain`); exit codes 0 / 1 / 2 (03.01)
- [ ] The result is a `Tool.Result`; `content` is high-signal and truncated by the wrapper, artifacts are `file` parts (03.02)
- [ ] Errors are fixable messages with an input example, without stack traces (03.03)
- [ ] A mutating tool is in `permissions` with at least `ask`; read-only may be `allow` (04.01)
- [ ] Mutations are idempotent or protected; `--dry-run` exists (04.02)
- [ ] There are no secrets in the file (04.01)
- [ ] The tool is tested on real requests: the model selects it by `description`, call errors are absent; on selection errors, descriptions were fixed, not the implementation

---

## 06.01. Related documents

| Document | Purpose |
| -------- | ------- |
| `doc/standards/project_standards.md` | Core project rules: text (04.03), output (04.04), `--dry-run` (03.01), exit codes (05.03), security (05); this standard applies on top of it |
| `doc/standards/code_standards.md` | Code writing canon: Python (02), JavaScript and opencode plugins (03, including the plugin file shape - 03.05), HTML/CSS (04), Shell (05), Windows - PowerShell and batch (06), linters (08); applies when writing plugin code and external tool scripts |
| `doc/standards/skill_anthropic_standards.md` | SKILL.md skills; choosing between tool and skill - 01.02 of this document |
| `doc/standards/_index_standards.md` | Standards package registry; unified version |
| Tools section of the opencode Plugins documentation | Contract primary source: `Plugin.define`, `ctx.tool.transform`, input schema, `options`, `execute` (opencode.ai/v2/docs/build/plugins) |
| opencode Permissions documentation page | `permissions` array format, actions, masks, order and last match (opencode.ai/v2/docs/permissions) |
| opencode Migrate from V1 documentation page | Moving tools from the V1 contract to V2, action renames (opencode.ai/v2/docs/migrate-v1) |

If this document conflicts with the opencode documentation, the documentation wins; record the divergence by editing this standard.

---

## 06.02. Versioning

Standards package versioning is unified for all package documents. Versioning policy, registry, and routing map - in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
