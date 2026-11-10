# CLI Output Standards. Version 5.0.1

This document is the canon for console output of scripts, command-line tools, and skills. It defines the named output formats, the structured `report`, the clean `plain` stream, the machine-readable `--porcelain` mode, color control, and the language default. It supplements `project_standards.md` and `console_ui_standards.md` and applies on top of them. Core requirements remain in force unless this document explicitly overrides them.

Priority: language and typography - `project_standards.md` (04.03); interactive frame - `console_ui_standards.md`; output format - this document.

---

## Table of Contents

**01. Formats:** 01.01 Named formats and defaults - 01.02 Boundaries between formats

**02. Structured report (`report`):** 02.01 Layout - 02.02 Key-value block - 02.03 Steps - 02.04 Result and errors - 02.05 Color - 02.06 Examples

**03. Clean stream (`plain`):** 03.01 Line format - 03.02 Logs and parsing - 03.03 Progress

**04. Machine-readable (`porcelain`):** 04.01 Contract - 04.02 Stability

**05. Language and Localization:** 05.01 English default and Russian opt-in - 05.02 `t()` and translations

**06. Relations and Versioning:** 06.01 Related documents - 06.02 Versioning

---

## 01.01. Named formats and defaults

The package has five named output formats. A script or application selects one format per output channel.

| Name | Human label | Class | Purpose | Default |
|------|-------------|-------|---------|---------|
| `report` | Structured report | human | Snapshot of an object's state: header, key-value pairs, steps, `Result` | Yes, for human-facing output |
| `plain` | Clean stream | log and parsing | Chronological lines `YYYY-MM-DD HH:MM:SS [marker] message`, no color, no frames | Yes, for logs and parsing |
| `menu` | Interactive menu | human, TTY | Frame with menu on top, body in the middle, `[>]` at the bottom | Option |
| `rich` | Rich console | human, TTY | Styled tables, `Live`, progress, role colors | Option |
| `porcelain` | Machine-readable | machine | `key=value` lines, no header, no alignment, no color | Option, CLI flag `--porcelain` |

Rules:

- `report` is the default for human-facing output and the default `get_logger()` mode.
- `plain` is the clean mode for logs and streams. It is always the format of the log file, regardless of the console mode.
- `menu` and `rich` are interactive TTY modes. An entry point selects them explicitly.
- `porcelain` is a CLI flag, not a `get_logger()` mode. It is the only contract for automation.
- Outside an interactive context, `menu` and `rich` degrade to `plain`, not to `report`.
- One channel - one format. Do not mix `report` and `porcelain` on the same stdout.
- `report` is never written to a log file, a pipe, or an artifact consumed by a program.
- `plain` is never used as the human status report when `report` is available.

## 01.02. Boundaries between formats

| Output | Consumer | Format |
|--------|----------|--------|
| Status snapshot of an object | Person | `report` |
| Log file, chronological stream | Person or parser | `plain` |
| Automation, scripts, pipelines | Program | `porcelain` |
| Interactive menu screen | Person in a TTY | `menu` or `rich` |

- The purpose decides the format, not the implementation convenience.
- A human report with a final `Result` line is `report`. A stream of timestamped events is `plain`.
- A file that a program reads is `porcelain`. If a program must read a log, it parses the `plain` prefix, not the human report.
- Color is allowed only in `report`, `menu`, and `rich`. `plain` and `porcelain` emit plain bytes.

## 02.01. Layout

A `report` is a human-readable snapshot of one object or operation. Layout top to bottom:

1. Header: one line with the object name.
2. Key-value block: one pair per line, two-space indent, key column 16 characters.
3. Steps: `[n/m] key value` for multi-stage work.
4. Result: `Result` and a state word.
5. Errors: `error: <text>` on stderr.

Rules:

- Header: short English noun phrase, for example `OpenVPN machine channel`, `OpenVPN PKI`, `VPN profile`.
- No blank lines inside a report. Separate the report from the next output with one blank line. No separator lines (`=====`, `-----`, `---`).
- No trailing period on any line.
- The report ends with the `Result` line. Do not add text after it.
- Keep the key column stable across a script so values align vertically.
- Do not print timestamps in a report. Time belongs to `plain`.

## 02.02. Key-value block

- Line: two spaces, key, padding to 16 characters, value.
- Key: short English label, one or two words, capital first letter, for example `Service`, `Tunnel`, `Profile`, `Server`, `Route`.
- Value: the observed value, no trailing period. Paths, addresses, unit names, and state words are allowed.
- A missing value is `-`, not an empty string.
- Do not hide the state word behind color. The word is the carrier of meaning; color is an accent.
- Example:

```
OpenVPN machine channel
  Service         openvpn-client@hm
  State           active (running)
  Tunnel          tun0 10.8.0.10
  Server          203.0.113.10:443
```

## 02.03. Steps

- Step line: two spaces, `[n/m]`, space, key padded to 16 characters, value.
- `n` and `m` are decimal counters. Pad `n` to the width of `m` only when the total has two or more digits: `[2/4]`, `[03/12]`.
- One step per completed stage. Do not print a step before the stage starts.
- Step values are short state words or facts, for example `checked`, `started`, `installed`, `skipped`.
- Steps are optional. A report with one observation may contain only the header, the key-value block, and `Result`.

## 02.04. Result and errors

- Result line: `Result` padded to 20 characters, no indent, then a state word.
- Human result words: `UP`, `DOWN`, `SKIPPED`, `INSTALLED`, `DEPLOYED`, `BUILT`, `ISSUED`, `REVOKED`, `GENERATED`, `INITIALIZED`, `FAILED`. A project may extend the list in its method.
- Exit codes: `0` success, `1` runtime error, `2` usage or precondition error (`project_standards.md`, 05.03).
- Errors go to stderr as one line: `error: <text>`. No traceback, no raw subprocess output, no stack trace.
- The report may end with `Result FAILED` and a non-zero exit code. The error line explains the failure.
- The `Result` line is always present, including on failure.

## 02.05. Color

Roles:

| Element | Style |
|---------|-------|
| Header | Bold bright yellow `1;93` |
| Keys | Dim `2` |
| Success state (`UP`, `DEPLOYED`, `INSTALLED`, `BUILT`, `ISSUED`, `REVOKED`, `GENERATED`, `INITIALIZED`) | Green `32` |
| Failure state (`DOWN`, `FAILED`) | Red `31` |
| Skip, warning, check, already done | Yellow `33` |
| Neutral value | Default |

Control order, highest first:

1. `--color=auto|always|never`.
2. `CLI_COLOR=auto|always|never`.
3. `NO_COLOR` and `FORCE_COLOR`: non-empty `NO_COLOR` disables, non-empty `FORCE_COLOR` (not `0`) enables; `NO_COLOR` wins on conflict.
4. Auto: enabled only when stdout is a TTY, `TERM` is not `dumb`, and `CI` is empty.

Additional rules:

- Errors are colored only when stderr itself is a TTY.
- A pipe, a file, a CI log, and a log file receive plain bytes.
- Color is never the only carrier of meaning. The state word always stays.
- `--color` and `CLI_COLOR` are the only per-tool controls. Do not add tool-specific color variables.

## 02.06. Examples

Human report:

```
OpenVPN machine channel
  Service         openvpn-client@hm
  State           active (running)
  Tunnel          tun0 10.8.0.10
  [1/3] profile         checked
  [2/3] service         started
  [3/3] route           installed
Result              UP
```

Failure:

```
OpenVPN machine channel
  Service         openvpn-client@hm
  State           inactive (dead)
  Profile         /etc/openvpn/client/hm.conf
Result              DOWN
```

stderr:

```
error: profile /etc/openvpn/client/hm.conf is missing
```

## 03.01. Line format

`plain` is the clean stream format for logs and parsing.

- Line: `YYYY-MM-DD HH:MM:SS [marker] message`.
- Marker: `[!]` for error or critical, `[i]` for info or debug, `[*]` for warning.
- Monochrome. No ANSI, no frames, no separator lines, no screen clearing, no progress bar.
- One record per line. A list uses one `- item` line per record; a table uses `tabulate` only when a tabular structure is required (`project_standards.md`, 04.04.04).
- English by default. A Russian record is allowed only through the project locale (`05.01`).
- No trailing period on a record.
- The timestamp is the output moment. A script inserts it itself when it has no logger.

## 03.02. Logs and parsing

- The log file always uses `plain`, regardless of the console format.
- A log record is stable: fixed-width timestamp, space, marker, space, message.
- A parser reads the prefix, not the human report. Do not parse `report`, `menu`, or `rich` output.
- Machine data that must be reliable goes through `porcelain`, not through log text.
- A log file never contains ANSI, colors, frames, prompts, or screen clearing.
- Secrets are masked before the record is written (`project_standards.md`, 05.01).

## 03.03. Progress

- Long loops may use `\r` progress on stdout (`project_standards.md`, 04.07.01).
- Clear the progress line before the final summary and on `SIGINT` or `SIGTERM`.
- Progress is never written to the log.
- Progress is not part of `report`; use `report` steps for a stage snapshot.

## 04.01. Contract

`--porcelain` is the machine-readable mode.

- One `key=value` pair per line.
- No header, no alignment, no color, no blank lines, no decorations.
- Keys: lowercase English snake_case, stable across versions.
- Values: raw text without quotes unless the value itself contains a space or `=`; never spans lines.
- Errors: `error=<text>` on stderr.
- Exit codes: `0`, `1`, `2` (`project_standards.md`, 05.03).
- Example:

```
site=hm
profile_state=present
service=openvpn-client@hm
service_state=active
tunnel=tun0
tunnel_addr=10.8.0.10
server_replies=yes
result=up
```

## 04.02. Stability

- The key set is a contract. Adding a key is compatible; renaming or removing a key is a breaking change.
- The order of keys is stable for a given command.
- Document the keys in the script help or the skill reference.
- Automation reads `--porcelain`, never the human report and never the log text.
- A script that supports `--porcelain` keeps the human `report` as the default.

## 05.01. English default and Russian opt-in

- English is the default language for all user-facing output: scripts, CLI, `report`, `menu`, `rich`, `--help`, and GUI widgets.
- Russian is allowed through `t()`, `[app] language`, `LANGUAGE`, or a project override (`project_standards.md`, 04.01, 04.03). It is an option, not a forbidden language.
- Documentation, `README.md`, user guides, specifications, change requests, and chat remain Russian.
- The package does not cement a single language: a project may ship Russian UI, but the default catalog and the examples are English.
- Skill scripts follow the same rule: English default, Russian allowed by project override.
- Typography applies to both languages: hyphen-minus `-` only, no em dash or en dash, no ellipsis, no emoji, no exclamation marks, no non-breaking or narrow spaces, no trailing period on status or error lines.

## 05.02. `t()` and translations

- Applications use `t(key, *, count=None, **kwargs)` for user-facing strings (`project_standards.md`, 04.01).
- The default catalog is English. Russian is an optional translation loaded by the locale.
- Scripts without a localization layer print literal English.
- Do not put a marker inside a `t()` string.
- Do not use `t()` for technical log records; logs are English literals (`project_standards.md`, 04.06).
- A project that ships Russian UI records the choice in `doc/specs/overrides.md` and keeps the English catalog as the fallback.

## 06.01. Related documents

| Topic | Document |
|-------|----------|
| Core output, language, logging, modes, exit codes | `project_standards.md` (04.01-04.07, 05.03) |
| Interactive menu and rich frame, roles, `spec_ui.html` | `console_ui_standards.md` |
| Skill scripts and package self-sufficiency | `skill_anthropic_standards.md` (03.03) |
| Custom tool output and errors | `opencode_tool_standards.md` (03.01-03.03) |
| CLI flags, `--help`, `--dry-run` | `cli_data_standards.md` (05.02) |
| Russian text quality for documentation | `human_text_standards.md` |

## 06.02. Versioning

The package uses one SemVer. The versioning policy, registry, and routing map are in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request.
