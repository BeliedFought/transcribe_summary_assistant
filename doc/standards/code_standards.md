# Code Standards. Version 5.0.0

Canonical coding requirements by language: Python, JavaScript, HTML and CSS, Shell, Windows (PowerShell and batch); data formats; shared rules (comments, TODO, line length, encoding); and linters. This document supplements `project_standards.md` and applies on top of it: project structure, configuration, output and UI, security, git, and workflow live in the core standard. For decision priority when a rule is missing or ambiguous, see `project_standards.md` (Section 07.06).

Sections are self-contained: for a single-language task, load that language section plus common sections 01 and 07. A section is mandatory when the repository contains code in the corresponding language; Python sections apply to Python projects and Python skill scripts.

## Table of Contents

**01. Common Code Rules:** 01.01 Comments - 01.02 TODO Comments - 01.03 Line Length - 01.04 Encoding and Line Endings

**02. Python:** 02.01 Naming - 02.02 Constants and Global State - 02.03 Docstrings - 02.04 Typing - 02.05 Programming - 02.06 Exceptions - 02.07 Logging in Code

**03. JavaScript:** 03.01 Modules and Variables - 03.02 Comparison and Strings - 03.03 Functions, Naming, and Documentation - 03.04 Errors and Forbidden Constructs - 03.05 opencode Plugins - 03.06 TypeScript

**04. HTML and CSS:** 04.01 Document Skeleton - 04.02 Semantics and Accessibility - 04.03 Resources and Styles - 04.04 Formatting and Class Naming

**05. Shell (bash):** 05.01 Header and Strict Mode - 05.02 Variables and Quoting - 05.03 Constructs and Functions - 05.04 Errors and Output Streams - 05.05 Working Directory and Line Length - 05.06 busybox ash (Embedded Environments) - 05.07 Aliases and rc Files

**06. Windows:** 06.01 PowerShell - 06.02 Batch (cmd) - 06.03 Windows Specifics in Code

**07. Data Formats:** 07.01 JSON and JSONC - 07.02 TOML and Tool Configurations - 07.03 YAML - 07.04 SQL

**08. Linters and Checks:** 08.01 Python: ruff and mypy - 08.02 Shell: shellcheck - 08.03 JavaScript: eslint and prettier - 08.04 HTML and CSS: W3C Validator and stylelint - 08.05 PowerShell: PSScriptAnalyzer

**09. Cross-References and Versioning:** 09.01 Related Documents - 09.02 Versioning

---

# 01. Common Code Rules

Language-independent rules: comments, TODO, line length, encoding, and line endings.

## 01.01. Comments

*Required.*

- Write code comments in English (language split - `project_standards.md`, Section 04.03)
- A comment is a complete sentence: capitalize the first word and use normal English punctuation
- A comment explains the reason and the decision, not the code; never restate the code in a comment
- Do not leave commented-out code
- A trailing inline comment is a rare case: use it only when the explanation cannot be placed on the line above the code

## 01.02. TODO Comments

*Required.*

- Use one format across all languages: `TODO(owner): summary`; the owner is the user or team responsible for the follow-up
- Never leave a `TODO` without an owner
- Language syntax: Python and Shell - `# TODO(owner): ...`, JavaScript - `// TODO(owner): ...`
- A `TODO` marks a planned change, not a defect: fix defects immediately, without a note

## 01.03. Line Length

*Required.*

Line length follows the language canon and is enforced by a tool (Section 08); do not introduce a single value for all languages:

| Language | Limit | Enforced by |
|----------|-------|-------------|
| Python | 100 | `ruff` (08.01) |
| JavaScript | 80 | `prettier` (08.03) |
| HTML, CSS | target 80, wrap as needed | - |
| Shell | target 80-100 | 05.05 |
| PowerShell | target 80-100, long calls via splatting | 06.01 |
| Batch (cmd) | target 80, line continuation via `^` | 06.02 |

## 01.04. Encoding and Line Endings

*Required.*

- All repository text files are UTF-8 without BOM, with LF line endings enforced through `.gitattributes`; canon - `project_standards.md` (Sections 01.04, 06.01)
- Exceptions: `.ps1` is UTF-8 with BOM (Windows PowerShell 5.1 otherwise reads the file as ANSI); `.bat` and `.cmd` are ASCII (06.02); line endings of `.ps1`, `.bat`, `.cmd` are CRLF via `.gitattributes` (core standard, Section 06.01)

---

# 02. Python

Rules apply to Python project code and Python skill scripts; skill script output follows `skill_anthropic_standards.md` (Section 03.03).

## 02.01. Naming

*Required.*

| Entity             | Style       | Example                     |
| ------------------ | ----------- | --------------------------- |
| Variables          | snake_case  | `user_id`, `file_path`      |
| Functions          | snake_case  | `load_data`, `get_user`     |
| Classes            | PascalCase  | `DataLoader`, `ApiClient`   |
| Constants          | UPPER_CASE  | `MAX_RETRIES`, `BASE_URL`   |
| Private attributes | _snake_case | `_session`, `_config`       |
| Modules / files    | snake_case  | `data_loader.py`            |

**Naming language.** Identifiers are written in English (meaningful English words and established abbreviations: `id`, `url`, `api`, `db`, `config`). Transliterating Russian words into Latin is forbidden: use `data`, `writeoff`, `turnover`, not `dannye`, `spisanie`, `oborot`. Cyrillic in technical naming is not allowed (see also core standard Section 04.03). Human-readable user strings (UI, documentation) are Russian via `t()` or documentation; they are not code identifiers.

**Hierarchy in compound names (general to specific).** When a file, module, key, or other identifier name consists of several meaningful parts, the parts run left to right from the larger context to the narrower detail: domain / section / block / detail. Do not start with a small detail and do not put a common prefix at the end. Examples: `log_export_summary.txt` (log -> export section -> summary block), `db_init.py`, `api_sync_users.py`. Domain prefixes defined in the core standard (`db_`, `api_`, `ai_`, `email_`, `orch_`, and similar) are the first level of this hierarchy.

**Names to avoid:**

- Single-letter names `l`, `O`, `I` are forbidden - they are confused with one and zero
- When a name conflicts with a keyword, add a trailing underscore: `class_`
- Abbreviations in PascalCase names are written in full uppercase: `HTTPServerError`, not `HttpServerError`

**Slugs.** A slug is a short text label that is part of file and folder names (the `<slug>` part in `2026-07-21_setup-db`, `spec_<slug>.md`). Two slug types:

- *Latin slug* - a programmatic identifier:
  - lowercase Latin letters, digits, hyphen; the word separator is a hyphen (kebab-case)
  - English words; transliteration is forbidden: `setup-db`, not `nastroyka-db`
  - starts and ends with a letter or digit; double hyphens are forbidden
  - up to 4 words, up to 64 characters in total
- *Russian slug* - a human-readable name for the user (recommended session folder names - core standard Section 01.01.01):
  - Cyrillic letters; digits are allowed; Latin letters and spaces are forbidden
  - the word separator is a hyphen: `Настройка-выгрузки`
  - the first word is capitalized, the rest are lowercase
  - letter е without a diacritic mark; the diaeresis variant is forbidden (core standard Section 04.03)
  - 2-4 words

The boundary between types follows the purpose of the name (core standard Section 04.03): a name used by code as an identifier (search pattern, glob, literal) is built from a Latin slug; a human-readable artifact name for the user is built from a Russian slug.

## 02.02. Constants and Global State

*Required.*

- Numbers and strings with domain meaning (timeouts, ports, limits, codes, sizes) go into named `UPPER_CASE` constants; domain-meaning literals in logic without a name are forbidden, except self-evident ones (`0`, `1`, `-1`)
- Module constants are allowed and encouraged; internal ones (not part of the module API) use the `_` prefix
- Avoid mutable global state (module dicts, lists, flags mutated from multiple places); pass state through parameters and return it through results
- If mutable global state is unavoidable: use a `_` prefix, access it through functions, and record the reason in a comment at the declaration

## 02.03. Docstrings

*Required.*

- Every module has a module docstring: the first line states the module purpose briefly
- All public functions, methods, and classes have docstrings; private ones (`_name`) as needed
- Style - Google (readable, supported by Sphinx and IDEs out of the box). Example:

```python
def get_logger(name: str, log_dir: Path) -> logging.Logger:
    """Create a file-only logger.

    Args:
        name: Script name used in the log file name.
        log_dir: Directory for the log file.

    Returns:
        Configured Logger instance.
    """
```

- Write docstrings in English (core standard Section 04.03); describe the purpose, parameters, return value, and exceptions (`Raises:` section when applicable)
- Form per PEP 257: the summary is one sentence in the imperative; in a multi-line docstring, a blank line follows the summary and the closing quotes sit on their own line; a single-line docstring keeps the quotes on the same line. End the summary with a period (unlike log messages, where a trailing period is forbidden)
- Generators use `Yields:`, not `Returns:`
- Omit docstrings for trivial getters/setters and obvious wrappers: redundant comments are worse than none

## 02.04. Typing

*Required.*

- Type annotations for all functions: parameters and return value
- For complex types, use the `typing` module or `from __future__ import annotations`
- Example: `def get_logger(name: str, log_dir: Path) -> logging.Logger:`
- Do not use `Any` where a type is expressible: `X | None` / `Optional`, unions, `Protocol`
- `TypeVar` names are short PascalCase: `T`, `AnyStr`, `KT_contra`
- Modern union syntax `X | None` is allowed and preferred

## 02.05. Programming

*Required.*

Generic Python style is enforced by the configured linters (Section 08.01): formatting and indentation, import order, `None` comparisons, `isinstance` checks, boolean comparisons, lambda assignment, mutable defaults, and return consistency. This section defines project requirements and non-obvious restrictions.

**Truthiness and comparisons:**

- Test sequences for truthiness instead of `len()`: `if seq:` / `if not seq:` for strings, lists, dicts, and sets; `if len(seq) == 0` is forbidden
- For integers, use an explicit comparison: `if i % 10 == 0:`; `if not i % 10:` is forbidden as non-obvious

**Functions:**

- Check prefixes and suffixes with `name.startswith("tmp")`, not with slices such as `name[:3] == "tmp"`
- A comprehension has one `for` and at most one `if`; nested `for` clauses in a comprehension are forbidden - write a regular loop

**Default values:**

- The `x = x or []` antipattern is forbidden: it replaces any falsy value, not only `None`

**Strings:**

- Build strings with f-strings; use `.format()` and `%` for templates coming from data and for logger arguments (02.07)

**File structure:**

- Header order: module docstring, then `from __future__ import annotations`, then module dunder names (`__all__`, `__version__`), then imports
- Keep imports at the top of the file; `from x import *` is forbidden; local imports are absolute; import order and grouping are enforced by ruff (`I`)
- Public and internal interface: internal names start with `_`; modules with a public API declare `__all__`; do not re-export imported names without an explicit decision
- In multi-line collections, keep a trailing comma after the last element when the closing bracket is on its own line; a one-element tuple requires it: `(1,)`

**Powerful language features:**

- Metaclasses, `__del__` for cleanup, dynamic compilation, `sys.path` edits, and reflection through `getattr` require an explicit need and a comment justifying it
- Avoid `@staticmethod`; use `@classmethod` for named constructors

## 02.06. Exceptions

*Required.*

Construct rules are in this section; the handling policy (specific classes, no swallowing, `raise ... from`, `ProjectError` hierarchy, context managers) is in `project_standards.md` (Section 05.02).

- Keep the `try` body minimal: only the operation handled by `except`; move the rest into `else`; a broad `try` hides unrelated errors
- Do not use `assert` for business-logic preconditions: checks disappear under `-O`. Validate arguments with `raise ValueError(...)`; `assert` is acceptable as an internal safeguard and in tests
- Choose the exception class by meaning: a violated argument precondition - `ValueError`; a missing key - `KeyError`; domain errors - dedicated classes with the `Error` suffix and a hierarchy by meaning

## 02.07. Logging in Code

*Required.*

- Write `logger.*` calls in English with lazy `%s` arguments passed separately from the template: `logger.info("Loaded %s items from %s", count, path)`. Never use `t()` or f-strings inside a logger call (`project_standards.md`, Section 04.06)
- Exception - skill scripts: they have their own output canon without a logger (`skill_anthropic_standards.md`, Section 03.03); this rule does not apply to them
- Logger canon, levels, and formats - `project_standards.md` (Sections 04.06 and 04.04)

---

# 03. JavaScript

Rules apply to opencode plugins, configuration scripts, and future frontend code.

## 03.01. Modules and Variables

*Required.*

- New code uses ES modules only: `import` / `export`; do not use `require` or `module.exports`
- Declare a variable next to its use and initialize it immediately
- Variable declarations (`const` by default, `let` only for reassignment, no `var`) and one variable per declaration are enforced by ESLint (Section 08.03)

## 03.02. Comparison and Strings

*Required.*

- Comparison, quote style, and string layout are enforced by ESLint and Prettier (Section 08.03); the intentional exception is `x == null`, which deliberately catches both `null` and `undefined`

## 03.03. Functions, Naming, and Documentation

*Required.*

- Use arrow functions for nested functions (`=>`); do not bind `this` through `bind` or `const self = this`
- Name nested functions: `const name = () => {...}`
- Naming: variables and functions - `lowerCamelCase`; classes - `UpperCamelCase`; constants - `CONSTANT_CASE`; file names - lowercase words separated by hyphens (kebab-case) with the `.js` extension
- Document exported functions and classes with JSDoc `@param` and `@returns`; internal one-line helpers may stay undocumented
- Formatting (indentation, braces, semicolons) is enforced by ESLint and Prettier (Section 08.03)

## 03.04. Errors and Forbidden Constructs

*Required.*

- Throw `Error` objects or subclasses; throwing strings is forbidden
- `catch` without a parameter and an empty `catch {}` block are forbidden
- Use `async` / `await` for asynchronous code; do not write nested callbacks
- Forbidden: `with`; `eval` and `new Function(...)`; non-standard and deprecated features; undocumented runtime extensions
- Use ECMA-262 and WHATWG; environment-specific APIs (Node, Bun) are allowed where used

## 03.05. opencode Plugins

*Required for repositories with opencode plugins.*

Canonical plugin file shape:

- Export `export default Plugin.define({ id, setup })` from the `@opencode/plugin` package
- Subscribe to events through `ctx.event.subscribe({ signal })` with an `AbortController`
- `setup` returns a cleanup function that cancels subscriptions and running processes
- Do not keep global state; store own state in `ctx.storage`
- Report diagnostics through `console.error`

## 03.06. TypeScript

*Required for repositories with TypeScript, including opencode plugins.*

- `tsconfig.json` with `strict: true`; `target` and `module` match the execution runtime
- Explicit types in public signatures; use type inference for local variables
- Do not use `any`; a value of unknown external type is `unknown`, narrowed by a check
- Naming: types and interfaces - PascalCase; variables and functions - camelCase; rules 03.01-03.04 apply
- Import host package types (for example `@opencode/plugin`) as types: `import type { Plugin } from "@opencode/plugin"`
- Export domain types from one module; do not duplicate overlapping definitions

---

# 04. HTML and CSS

Rules apply to the `doc/specs/spec_ui.html` artifact (contract - `console_ui_standards.md`), live HTML mockups, and frontend code (`web_standards.md`).

## 04.01. Document Skeleton

*Required.*

- `<!doctype html>` on the first line of the document
- `<meta charset="utf-8">`, `<html lang="...">` with the content language, and `<title>`
- `<meta name="viewport" ...>` for responsive pages

## 04.02. Semantics and Accessibility

*Required.*

- HTML and CSS are valid (validator checks - 08.04)
- Use elements for their purpose: headings for headings, `p` for paragraphs, `a` for links, `nav` / `main` / `section` by meaning; `div` does not replace a semantic element
- Accessibility: `alt` on images (empty for decorative ones); `<label>` captions for form fields; text contrast; use ARIA only when native semantics is insufficient
- Headings follow the hierarchy without skipping levels

## 04.03. Resources and Styles

*Required.*

- Load external resources only over `https://`; do not use protocol-relative `//` links
- Keep presentation in `<style>` or an external CSS file; do not use inline styles or presentational attributes (`width`, `height` for styling, `<font>`, `align`)
- Do not write the `type` attribute on `style` and `script` tags

## 04.04. Formatting and Class Naming

*Required.*

- HTML: 2-space indent, tabs forbidden; lowercase tags and attributes; double-quoted attribute values; block, list, and table elements on new lines with indented descendants; no trailing whitespace
- CSS: valid; one selector per line in a selector list; declaration blocks indented 2 spaces; a space after the colon and none before it; a semicolon after every declaration; lowercase selectors and properties; lowercase or shortened hex colors; separate file sections with comments such as `/* Header */`
- Class names are meaningful or generic functional names that reflect the element purpose; presentational and meaningless names (`red`, `left`, `div2`) are not used

---

# 05. Shell (bash)

Rules apply to repository shell scripts, including skill scripts (`scripts/` in skill packages); skill script output follows `skill_anthropic_standards.md` (Section 03.03).

## 05.01. Header and Strict Mode

*Required.*

- The first line is `#!/usr/bin/env bash`
- Next comes a header comment: script purpose, expected arguments, and return codes
- Strict mode: `set -euo pipefail` immediately after the header
- If a script intentionally relies on uninitialized variables, record this in a comment and write default value references as `${VAR:-}`

## 05.02. Variables and Quoting

*Required.*

- Quote all variable substitutions: `"$var"`, `"${arr[@]}"`, `"$@"`; unquoted `$var` in commands and tests is forbidden
- Function variables are `local`
- Naming: variables and functions - `lower_snake_case`; constants and environment variables - `UPPER_SNAKE_CASE`; constants are `readonly`; loop counters `i`, `j`, `k` are allowed

## 05.03. Constructs and Functions

*Required.*

- Use `[[ ... ]]` instead of `[ ... ]` for tests
- Command substitution - `$(...)`; do not use backticks
- Arithmetic - `$((...))`
- Functions - `lower_snake_case`, without the `function` keyword
- The main scenario is a `main` function; call `main "$@"` at the end of the file

## 05.04. Errors and Output Streams

*Required.*

- Check command return codes: `if ! cmd; then ...; fi`
- Ignore an error through `|| true` only with a justifying comment
- Write data to `STDOUT`; errors and the usage message go to `STDERR` (`>&2`)
- `eval` is forbidden; use arrays and `printf -v` for indirect access

## 05.05. Working Directory and Line Length

*Required.*

- A script does not depend on the current directory: use an explicit `cd` with a check (`cd "$dir" || exit 1`) or absolute paths from a known variable
- Build paths without hardcoded separators
- Line length target is 80-100 (01.03); write long messages and commands via heredoc or arrays
- Do not use separator lines (`=====`, `-----`) (`project_standards.md`, 04.04.02)

## 05.06. busybox ash (Embedded Environments)

*Required for scripts in embedded Linux environments (Entware, OpenWrt, and similar).*

- A background launch from an SSH session or a firmware hook dies with the parent: detach via `start-stop-daemon -S -b -m -p <pidfile>`
- `start-stop-daemon -K` and `-t` with `-x` do not work for interpreted scripts: they match the interpreter binary, so stop reports "not running" while the process is alive, and the "already running" check falsely fails and spawns duplicates
- Check process liveness through `/proc/<pid>/cmdline` containing the script name
- A hand-made lock directory survives a reboot and blocks the loop forever: use a pid file or a lock with an expiry
- The built-in command set is narrower than bash: verify that a built-in command exists in the target environment before using it

## 05.07. Aliases and rc Files

*Required when editing user shell configuration (`~/.bashrc`, `~/.bash_aliases`).*

- Place user aliases and shell functions strictly in `~/.bash_aliases`; defining them in `~/.bashrc` is forbidden
- `~/.bashrc` contains only: a header and interactivity check, `PS1`, `export` lines, tool initialization lines (`starship init`, `zoxide init`, and similar), and the line `[ -f "$HOME/.bash_aliases" ] && source "$HOME/.bash_aliases"` at the end of the file
- Managed blocks of customization skills live in marker sections: opening line `# >>> <owner>: <domain> >>>`, closing line `# <<< <owner>: <<<`; `<owner>` is the skill or component name, `<domain>` is the block purpose (example: `# >>> cfg-mc: lastdir >>>`); replace a block entirely by its markers and never touch other sections
- Keep the comment short and functional, above the line or group: what it does and why; comment text follows Section 01.01 (English, hyphen-minus, no trailing period)
- Do not use decorative separator lines (`# --- xxx ---`) in rc files
- Group aliases by domain (vpn commands together, rdp together, and so on); paired commands follow one naming pattern `<domain>-on` / `<domain>-off` / `<domain>-status` (example: the `vpntg-on`, `vpntg-off`, `vpntg-status` family)
- One alias has one owner: the skill that writes and verifies it; two skills never manage the same line; an alias owned by another skill migrates or is skipped during cleanup, never deleted
- Append new definitions to the end of their domain; keep domain order stable between runs so repeated applications are idempotent

---

# 06. Windows: PowerShell and Batch

Rules apply to Windows scripts: `.ps1` (PowerShell) and `.bat` / `.cmd` (batch). Write new automation scenarios in PowerShell or Python; batch is only simple glue.

## 06.01. PowerShell

*Required when .ps1 scripts exist.*

- The target version for new scripts is PowerShell 7.x (the current LTS branch); use 7 syntax (`&&`, `||`, ternary `?:`, `??`) freely
- Windows PowerShell 5.1 is a compatibility mode for systems without PowerShell 7: such a script avoids 7 syntax and declares the minimum in the header `#Requires -Version 5.1`
- Revisit the decision on a trigger: a PowerShell 7.x LTS branch change or a full migration of target systems to PowerShell 7 - then reduce the 5.1 compatibility mode
- Strict mode at the start of the script: `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'`
- Name functions with an approved PowerShell verb-noun pair (`Get-Verb`) in PascalCase: `Get-Report`, `Set-Option`
- Use full command and parameter names, no aliases: `Where-Object`, not `?`; `Select-String`, not `sls`; use named parameters
- Function parameters go in a typed `param()` block; add `[CmdletBinding()]` when using common parameters
- Error handling: `try` / `catch` / `finally`; instead of `$?` checks, use `-ErrorAction Stop` on the specific call
- Output streams: data - `Write-Output` (to the pipeline); user messages - `Write-Host` (direct output only); errors - `Write-Error`; diagnostics - `Write-Verbose` / `Write-Debug`
- Strings: single quotes for literals, double quotes only for interpolation; multi-line strings use here-strings (interpolating `@"..."@`, literal `@'...'@`)
- Long calls use splatting (`$params = @{...}`; `Cmdlet @params`), not backtick line continuations
- Forbidden: `Invoke-Expression` and dynamic string execution; bypassing the execution policy from scripts
- `.ps1` encoding is UTF-8 with BOM (Windows PowerShell 5.1 otherwise reads the file as ANSI and corrupts Cyrillic); line endings are CRLF

## 06.02. Batch (cmd)

*Required when .bat or .cmd scripts exist.*

- Batch purpose is simple glue: launch Python or uv, set variables, forward arguments; computational logic and error parsing belong to PowerShell or Python
- Header: `@echo off` on the first line; with delayed expansion, `setlocal enabledelayedexpansion` and a matching `endlocal` at the end
- Quote variables and paths: `"%VAR%"`, `"C:\path with spaces"`; assign without spaces around `=`
- Return codes: check `if errorlevel 1` or `%ERRORLEVEL%`; exit with `exit /b <code>`; code convention - 0 / 1 / 2 (`project_standards.md`, Section 05.03)
- File encoding is ASCII: write comments and messages in English (an exception to the text-language rule in `project_standards.md` 04.03 - a technical limitation of the cmd OEM console encoding; Russian text in batch is unreliable). If Russian output is required, use `chcp 65001` with UTF-8 without BOM and verify on the target system; line endings are CRLF
- Break long commands with `^` at the end of the line; a space after `^` breaks the continuation

## 06.03. Windows Specifics in Code

*Required for code running on Windows.*

- Do not use reserved Windows names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`) for files and directories, including with an extension; names do not end with a period or space
- Do not create names that differ only by case: the Windows file system is case-insensitive
- Do not create deep paths: the classic Win32 limit is 260 characters; do not rely on the OS long-path policy
- Environment variables: `%USERPROFILE%` in cmd, `$env:USERPROFILE` in PowerShell, `os.environ` / `Path.home()` in Python; `~` is not expanded in Windows commands
- Build paths through `pathlib.Path` in Python (`project_standards.md`, 01.04) and `Join-Path` in PowerShell (06.01); string concatenation and hardcoded separators are forbidden
- Do not assume POSIX permissions or symlinks in the repository; line endings of `.ps1`, `.bat`, `.cmd` are CRLF via `.gitattributes` (`project_standards.md`, 06.01)

---

# 07. Data Formats

## 07.01. JSON and JSONC

*Required.*

- Indent - 2 spaces
- Keys and strings in double quotes
- End the file with a newline
- Comments are not allowed in JSON; configuration files with comments use the `.jsonc` extension

## 07.02. TOML and Tool Configurations

*Required when the corresponding files exist.*

- External theme templates (for example `starship.toml`) are copies of external sources: do not change the key set without updating the theme, and do not impose formatting
- opencode configuration (`opencode.jsonc`): `$schema` at the root, MCP servers under `mcp.servers`, secrets only as `{file:...}` references, secret files with mode 600

## 07.03. YAML

*Required when YAML exists (CI, third-party configs).*

- Indent - 2 spaces, tabs forbidden
- Quote values with special characters (`:`, `{`, `[`, `#`, leading `-`)
- Literals `true` / `false` / `null` are lowercase; number-like values (`3.10`, `1.0`) are quoted so parsers do not normalize them
- Multi-line strings use `|` (block with newlines) or `>` (folded) as appropriate
- Do not use anchors and aliases (`&`, `*`): not all tools expand them

## 07.04. SQL

*Required when SQL files or embedded queries exist.*

- Keywords are UPPER (`SELECT`, `FROM`, `WHERE`); identifiers are snake_case (`code_standards.md`, 02.01)
- Put semantic clauses (`JOIN`, `WHERE`, `AND`, `GROUP BY`, `ORDER BY`) on new lines; keep continuation indentation consistent within a file
- Use explicit `JOIN` only; do not use implicit comma joins
- Table aliases are short and meaningful (`u` for users, `o` for orders); meaningless aliases (`t1`, `a`) are not allowed
- Do not use `SELECT *` - list columns; substitution parameters are driver placeholders (`project_standards.md`, Section 03.02)
- The query file header states the purpose in one line (comment rules - 01.01)

---

# 08. Linters and Checks

The requirements of sections 02-06 are enforced by tools, not by declaration alone. Run checks before commit; disable a specific rule only with an inline comment and a justification next to it.

## 08.01. Python: ruff and mypy

*Required.*

- Linter and formatter - `ruff` (one tool instead of flake8+isort+black); configuration in `pyproject.toml`, section `[tool.ruff]`
- Rule set: `E`, `F`, `I` (imports), `UP` (pyupgrade), `B` (bugs), `RET` (return consistency), `SIM` (simplifications), `C4` (comprehensions), `BLE` (no blind exception catching)
- Line length - 100 characters
- Type checker - `mypy` (the only pinned option); configuration in `pyproject.toml`, section `[tool.mypy]`; the baseline is the `strict = true` preset, targeted disables use `disable_error_code` globally or in per-module sections, and every disable carries a justification:

```toml
[tool.mypy]
strict = true

# example of a targeted disable: the external package ships no type stubs
disable_error_code = ["import-untyped"]
```
- Add tools to `requirements.txt` or the dev section of `pyproject.toml` following the project dev-dependency mechanism (`project_standards.md`, Section 01.06)
- Pre-commit check command: `ruff check . && ruff format --check . && mypy src`
- Scope: `ruff` - all `.py` files in the repository, including skill scripts (`data/skills/*/scripts/`, `doc/skills/*/scripts/`); `mypy` - `src/`
- Disable a rule with `# noqa: CODE` plus a justification comment next to it

## 08.02. Shell: shellcheck

*Required when shell scripts exist.*

- All `.sh` files in the repository are checked by `shellcheck`
- Disable a specific warning (`# shellcheck disable=SC2034`) only with a justification comment

## 08.03. JavaScript: eslint and prettier

*Required for repositories with maintained JS code.*

- Static analysis - `eslint` (`eslint.config.js`, flat config); formatting - `prettier` (`.prettierrc`)
- Pin tools in the repository dev dependencies (`package.json`)
- Key prettier settings that enforce section 03: `singleQuote: true`, `printWidth: 80`, `tabWidth: 2`, `useTabs: false`
- Pre-commit check command: `npx eslint . && npx prettier --check .`
- Disable an eslint rule with an inline comment and a justification

## 08.04. HTML and CSS: W3C Validator and stylelint

*Required for repositories with HTML/CSS.*

- Validate HTML with the W3C validator (validator.w3.org) when creating or significantly changing `spec_ui.html`, live mockups, and frontends
- Check CSS with `stylelint` and the `stylelint-config-standard` baseline (`.stylelintrc.json`, dev dependencies in `package.json`); do not use the W3C jigsaw.w3.org CSS validator - it is frozen and does not support modern CSS
- Pre-commit CSS check command: `npx stylelint "**/*.css"`

## 08.05. PowerShell: PSScriptAnalyzer

*Required when .ps1 scripts exist.*

- All `.ps1` files in the repository are checked by `PSScriptAnalyzer` (`Invoke-ScriptAnalyzer`); deviate from a specific rule only with a justification nearby (a suppression comment or an analyzer settings file)
- Batch files have no linter: follow section 06.02 manually

---

# 09. Cross-References and Versioning

## 09.01. Related Documents

| Document | Relationship |
|----------|--------------|
| `doc/standards/project_standards.md` | Core: project structure, output and UI (04), error handling policy (05.02), logging (04.06), text (04.03), dependencies (01.06) |
| `doc/standards/skill_anthropic_standards.md` | Output canon for skill scripts (Section 03.03); this standard applies to skill script code on top of the output canon |
| `doc/standards/console_ui_standards.md` | `spec_ui.html` artifact; HTML rules apply to the mockup |
| `doc/standards/web_standards.md` | Frontend and web structure; JS and HTML/CSS rules apply to frontend code |
| `doc/standards/_index_standards.md` | Package registry, routing map, and versioning policy |

## 09.02. Versioning

Versioning of the standards package is unified for all package documents. For the versioning policy, see `doc/standards/_index_standards.md`.
