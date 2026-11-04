# Console UI Standards. Version 5.0.0

This document fixes the visual and navigation contract of the interactive console UI (`menu` / `rich` modes) and the mandatory reference `doc/specs/spec_ui.html`. It supplements `doc/standards/project_standards.md` and applies on top of it. All core standard requirements remain in force unless this document explicitly states otherwise.

The method comes from a portable contract for interactive projects with a frame of "menu on top, body in the middle, `[>]` at the bottom" and a single TTY/non-TTY path without ANSI cursor tricks. Domain rules of a specific application are not part of the universal standard: they are fixed in the project `spec_ui.html`.

**Priority:** when frame examples in `spec_ui.html` conflict with the method, the method in this document (and the project method in `spec_ui`) and the code win. Frame examples are illustrative.

---

## Table of Contents

**01. Foundation:** 01.01 Purpose - 01.02 Mandatory `doc/specs/spec_ui.html` Artifact

**02. Frame and Navigation:** 02.01 Screen Frame - 02.02 Navigation Header - 02.03 Menu Keys - 02.04 Post-Action Navigation - 02.05 Conditional Menu Items

**03. Presentation:** 03.01 Colors (Roles) and Font - 03.02 Tables - 03.03 Result Lists - 03.04 Summaries - 03.05 Texts and Localization

**04. Channels, Session, and Boundaries:** 04.01 After an Item Is Selected - 04.02 Two Channels (Console and Log) - 04.03 Session Messages - 04.04 Batch / Non-Menu CLI - 04.05 Examples vs Method

**05. Porting:** 05.01 Porting Checklist for Another Repository - 05.02 Related Documents - 05.03 Versioning

---

## 01.01. Purpose

*Required.*

- The reference and this standard fix the **visual and navigation contract**: the TTY frame, keys, post-action transitions (project contract), tables, summaries, and the difference between the console and the log file.
- The console is a color framed representation (menu on top, body in the middle, `[>]` at the bottom; status semantics through color).
- The log is a complete chronological plain stream without ANSI and without screen clearing.
- Style rules describe **roles** (title, navigation, section, numeric key, service key, command, hint, status and summary roles), not the application brand or domain.
- Domain strings come from project translations / code; do not invent them in reference examples.

---

## 01.02. Mandatory `doc/specs/spec_ui.html` Artifact

*Required for repositories with user-facing output - entry points the user runs directly (run/, main.py, menu, rich, batch CLI). Repositories without user-facing output (documentation, reference) do not create the artifact; it is created when the first user-facing output appears.*

- One file per repository. The mockup has its own SemVer (`Версия макета: X.Y.Z`), independent of the application version and the standards package version; it is **mandatory**. When frames, the map, the method, or log mockups change, bump the mockup version in the same change.
- **Structural template:** `doc/specs/spec_ui.html` in the `project_standards` hub (section 01 "How to build the mockup"). The agent copies or adapts this structure; it does not invent a different section scheme.
- Minimum composition:
  1. mockup version and instruction/priority (examples are illustrative);
  2. table of contents (TOC);
  3. **navigation map** (menu) or output point map (plain/rich/GUI) - a mandatory artifact; without the map the reference is incomplete;
  4. role palette (project hex values);
  5. console frame / screen examples;
  6. mandatory log file fragments;
  7. project method section (post-action contract, conditional items, statuses, digit exceptions, batch CLI when present);
  8. explicitly state priority: the `console_ui_standards.md` package + project method + code over frame examples.
- Update the map and frames together when the menu or output changes. When the README menu tree and the `spec_ui.html` map conflict, `spec_ui.html` wins.
- When the menu structure changes, update the map, the project method, and (if needed) examples in one change.
- **File footer (mandatory):** at the end of `spec_ui.html`, write the full absolute path and open commands in this format:

```html
<p class="note spec-footer">Файл: <code>/home/&lt;user&gt;/&lt;repo&gt;/doc/specs/spec_ui.html</code>. Открыть: <code>xdg-open /home/&lt;user&gt;/&lt;repo&gt;/doc/specs/spec_ui.html</code> или <code>file:///home/&lt;user&gt;/&lt;repo&gt;/doc/specs/spec_ui.html</code></p>
```

Style the footer indentation and other presentation through the `spec-footer` class in the mockup styles; inline styles are forbidden (`code_standards.md`, Section 04.03).

A relative path such as `doc/specs/spec_ui.html` without an absolute path is an insufficient footer. In the hub template (`doc/specs/spec_ui.html` of the `project_standards` repository), the footer contains the placeholder `/home/<user>/<repo>/` - the template is not tied to a specific machine; when copying to a target repository, the agent substitutes the actual absolute path of that repository.

---

## 02.01. Screen Frame

*Required when an interactive menu frame exists.*

- On every full redraw of an interactive screen in a TTY: full clear (`clear_screen`: home + ED2 + erase-below + ED3 scrollback where supported). Never leave a tail of previous body lines under a shorter new frame. The log file is not cleared. Do not clear when there is no TTY.
- Block order top to bottom (API: `begin_screen` -> items -> `finish_screen_prompt`):
  1. breadcrumb;
  2. menu items (numeric first, then service letters);
  3. body: pending action result (if any), then the **current** screen tables / messages (state is re-read before the frame); skip the block when the body is empty;
  4. blank line (exactly one before `[>]`, always);
  5. `[>]` prompt - **at the bottom, after the body**.
- The menu is always in the top zone; the body (pending + overview) is in the middle; the `[>]` input is always below the body. Never print the menu after long content.
- **One path for TTY and non-TTY:** print the body, a blank line, `[>]`, `input()`. No ANSI cursor tricks (CUP / CSI s/u / DECSTBM) and no body buffering. After `input()` - `clear_screen` again.
- Always exactly one blank line before `[>]` (after the body, or after the items when there is no body).
- Pipes and CI are not the target scenario for a color UI; the contract targets an interactive TTY. Non-interactive signs (no TTY, `CI`, `TERM=dumb`) - see `project_standards.md` (Section 04.07): the rich/menu frame degrades to plain. UI color is always on in an interactive TTY (never disabled for `NO_COLOR`).

**Body sections.**

- Every content block in the body (overview, empty state, pending announce, list) starts with a section title (cyan without bold, like a table title), followed by text or a table. A bare message line without a section title above it is not allowed.
- **Blank line before every title:** exactly one blank line before every section title (`print_section_title`) and before a table title (`print_table` with a non-empty title). This applies to the first title after menu items, to a title after a CLI banner, and to adjacent sections. Implement it inside `print_section_title` / `print_table`; the caller does not duplicate `print()` before them.
- Empty overview state: the same title as the table for a non-empty list, then the empty message line.
- Exactly one blank line between adjacent body sections (ensured by the "blank line before every title" rule).

**Abstract frame example with a body:**

```
{t("title.main_menu")} > {t("title.section")}
[1, 2] {t("menu.action.connect")}
[Z] {t("menu.action.connect_all")}
[X] {t("menu.back")}
[C] {t("menu.main_menu")}

{t("msg.action_title")}
- item_a
- item_b
{t("msg.action_done")}: ok: 2, skip: 0

[>]
```

(Menu on top, body in the middle, `[>]` at the bottom; input without cursor tricks.)

**Frame API (`src/menu.py` - contract, not a full implementation):**

| Function / method | When to call | Responsibility |
|-------------------|--------------|----------------|
| `clear_screen()` | Before a full frame; immediately after `input()` | Clear the TTY (home + ED2 + erase-below + ED3); no-op outside a TTY |
| `begin_screen()` | Start of a frame after clear | Breadcrumb, menu items, body (pending + tables from re-read state) |
| `finish_screen_prompt()` | End of a frame | Blank line, `[>]`, `input()`; after return the caller clears |
| `emit_session_notice(...)` | Start, immediate session messages | Single-line output to the screen + `log_file_only` |
| `_queue_notice_body` / `_queue_invalid_choice` / `_queue_nothing_selected` | Before the next `begin_screen` | Pending body for an invalid/empty selection |
| `_emit_interrupted()` | Ctrl+C / EOF after clear | `msg.interrupted` on screen + `log_file_only`; see Section 04.03 |

Loop order: `begin_screen()` -> `finish_screen_prompt()` -> (action) -> `begin_screen()` again.

---

## 02.02. Navigation Header

*Required when a menu frame exists.*

- Breadcrumb format: `A > B > C` (levels separated by `>` with spaces).
- The breadcrumb reflects the navigation path (the items traversed). Table content titles and universal labels are not part of the breadcrumb. Rule: one transition - one segment.
- The breadcrumb uses the title role (bold) in the project tone.
- **Table title and body section titles** - cyan without bold (rich `cyan`, ANSI 36). Do not confuse them with the breadcrumb.
- **Nav** (Back / Main menu / Exit) - the same tone as the breadcrumb, without bold.
- `title_justify=left` (not centered in the frame).
- No `---` lines and no centering.

---

## 02.03. Menu Keys

*Required when an interactive menu frame exists.* Scope - menu frame only; it does not extend to plain prompts such as 1/0.

- **Digits** - table rows only (`#` column). Not for modes, navigation, batch actions, or other items outside the table.
- **Temporary exceptions:** allowed only when explicitly recorded in the project `spec_ui.html` (a "temporary" / "exception" note in the method or map). Without a `spec_ui` entry, an exception is forbidden.
- **Letters** of the `Z X C V B N M` row - all other items. Assign top-down in row order (`bind_svc_keys_top_down` or equivalent). The "popular at the bottom" rule does not apply.
- Letter input is case-insensitive.
- **Input on a non-English layout.** Match by physical key, not glyph: pressing a row key on any layout is accepted as input of the corresponding row letter (for example, the physical Z key on the Russian layout produces the glyph «Я» - this is valid input for item Z). Implementation: a table mapping glyphs to physical EN/RU keys in `src/menu.py` (or equivalent); the entered character is first resolved through the table, then compared with the row. Glyph collisions (a character legitimate for items in both layouts) resolve in favor of the `Z X C V B N M` row letter.
- Group keys `[1, 2, 3]` - only row numbers of one operation (comma and space). Single key: `[1]` or `[Z]`.
- **Navigation items** («Назад», «Главное меню», «Выход»): the label uses the navigation role (same tone as the breadcrumb, no bold); the letter key uses the service key role. Other service items use the item text role.
- Navigation roles use fixed translation keys; **the letter on screen is not fixed** (it comes from the row):

| Role | Key | Russian | English |
|------|-----|---------|---------|
| Exit | `menu.exit` | Выход | Exit |
| Main menu | `menu.main_menu` | Главное меню | Main menu |
| Back | `menu.back` | Назад | Back |

**Stable cross-screen commands.** Commands repeated across several screens (navigation, batch actions, and similar) should get the same letter on every screen where possible. Reserve letters from the end of the row (`M`, `N`, `B`) for them, while unique screen items are assigned top-down from the start (`Z`, `X`, `C`). Record the list of cross-screen commands and their keys in `spec_ui.html`. Optionally, with user agreement, cross-screen commands may be bound to digits as an exception to the "digits - table rows only" rule, with a mandatory entry in `spec_ui.html`.

**Abstract main menu frame example (no content):**

```
{t("title.main_menu")}
[Z] {t("menu.main.section_a")}
[X] {t("menu.main.section_b")}
[C] {t("menu.main.section_c")}
[B] {t("menu.exit")}

[>]
```

---

## 02.04. Post-Action Navigation

*Required when a menu frame exists (project contract).*

The universal standard does not define domain transitions of a specific application. The project **must** record the contract in `spec_ui.html` (method and/or map):

- after which actions the UI returns to the main menu;
- after which actions it stays on the screen with a redraw and pending body;
- the behavior of «Назад» / «Главное меню» (including `force_menu` and equivalents);
- the behavior when entering a screen fails.

Example contract statements (templates, not domain): "single row action -> main"; "batch -> stay + pending"; "screen preparation error -> main".

---

## 02.05. Conditional Menu Items

*Required when conditional items exist.*

- Items appear only when the condition holds; row letters are reassigned top-down on every frame.
- Specific conditions (when to show refresh, cleanup, publish, and similar) live in the project `spec_ui.html`, not in the universal standard.
- **Hint tails** of the form ` ← если <condition>` - only in the `spec_ui` mockup (neutral role, for the reference reader, explaining why the item is on the frame). Never print them at runtime: an item is either visible (condition true) or hidden. Navigation and anchor items never have a tail.

---

## 03.01. Colors (Roles) and Font

*Required for `menu` and `rich` modes in an interactive TTY.*

The palette is a set of roles. **Role names are stable**; hex values and mockup styling live only in the project `spec_ui.html`. Baseline recommendation: success - green, warning - yellow, error - red; specifics are in the project reference.

Roles:

- **title** (breadcrumb) - bold; project tone;
- **section / table title** - body headings and table caption (cyan, rich `cyan`, no bold); do not confuse with the breadcrumb;
- **numeric key** - numeric selectors and `#` in a table; yellow bold;
- **service key** - letter selectors; terracotta, no bold;
- **item text** - action label;
- **navigation** / nav - «Назад», «Главное меню», «Выход» labels; same tone as the breadcrumb, no bold; the letter key uses the service key role;
- **command** - inline CLIs in text (command names, system calls); in the console use the command role (green bold); the rest of the message uses the item text role; in the log - plain;
- **hint** - reference remarks (not an action result), format `* <text>`; italic + gray; an inline command inside uses the command role;
- **prompt** - `[>]`; yellow bold (same tone as the numeric key; not the command color, so the input line reads separately);
- **add** / ok - more / appeared / active presence; green;
- **remove** / rm - fewer / removed / deleted; pink (do not confuse with error);
- **neutral** / dim - no quantity change, skipped, already done, zero; gray; in the mockup also the condition tail of a menu item;
- **column header** / th - table column labels; gray bold (not the data cell color);
- **error** / err - refusal / unavailability / failure; red.

UI color is always on in an interactive scenario. The log file has no ANSI. Emoji are forbidden. Separator lines (`=====`, `-----`, `---`) are forbidden.

**Change on user request:** hex role colors and the reference font styling (`spec_ui.html`: CSS `:root`, frame monospace family/size) may change on an explicit user request. Role names, the frame contract, and role application rules do not change. After a change, update the palette in `spec_ui.html`, the mockup CSS, and bump the mockup SemVer in the same change.

---

## 03.02. Tables

*Required when tables are printed in `menu` / `rich`.*

- **Console:** only through `src/console_table.py` (rich, `rounded` border); domain code and `src/menu.py` never import rich for tables directly. Other rich output in `rich` mode (Live, progress) goes through `src/rich_console.py` (`project_standards.md`, Section 04.07.03).
- **Log:** the hierarchy for tabular data - `project_standards.md` (Section 04.04.04): prefer lines, lists (Section 03.03), and summaries (Section 03.04); `tabulate` only when a tabular structure is required.
- Dual render: one module `src/console_table.py` produces the console view and (when a tabular structure is required) the file view from a single data source.
- **Console title:** `Table.title` via `t()`, justify left, section/title role style (cyan without bold); do not duplicate it with a separate caption line above the border.
- **Title before log `tabulate`:** per core standard Section 04.04.04 - a line via `t()` immediately before the table; exactly one blank line before the title is the rule of Section 02.01 here.
- **Column headers:** column header role (th) - gray bold; visually separated from data cells. In rich: `header_style="bold bright_black"` or an equivalent dim bold.
- The status column uses semantic coloring: active presence - add; inactive - neutral; refusal - error.
- **`status_col` + map pattern:** `print_table` accepts the status column index (0-based, e.g. `status_col=4`) and a `status -> role/style` dictionary (keys are normalized strings from `t()`, including ru/en variants such as `ок`/`ok`, `пропуск`/`skip`, `ошибка`/`fail`). Color only cells in that column; in log `tabulate` use the same texts without ANSI. Domain code passes the index and data, never duplicates the style map.
- Alignment: numbers and sizes right; text and paths left; statuses consistent within a column. `colalign` for log `tabulate` follows core standard Section 04.04.04.
- Table row numbers = numeric menu keys.
- Empty list: the same title, no table border - an empty message line under the section title (via `print_section_title` + empty message).
- Optional `to_console` / `to_log` flags on `print_table` when a table is needed in one channel only.
- Batch CLI (if any): one table of status columns + summaries below it (not a second table). See Section 04.04.

---

## 03.03. Result Lists

*Required when lists are printed.*

- Block: section title (section/title role) -> item lines -> summary when needed.
- Item: `- item` (hyphen, space, text); a translation template (for example `msg.list_item`). The title and item texts go through `t()`.
- Block structure and blank lines in the log (no leading spaces, no blank line between the title and items, exactly one between adjacent blocks) - `project_standards.md` (Section 04.04.05).
- On a menu frame, a list/summary from an action goes into the pending body (above the main screen table, if any).
- Logging a list by mode (`console_message()` in `plain`, `log_file_only` in `menu` / `rich`) - `project_standards.md` (Section 04.04.05); on the frame - pending body.

---

## 03.04. Summaries

*Required when summaries are printed.*

- A dedicated summary module (for example `src/console_summary.py`: `emit_summary` / `emit_summary_from_template` or equivalent).
- One-line format - `project_standards.md` (Section 04.04.06): `prefix: key: N, key: M`, keys via `t()` / template. The prefix uses the item text role, the separator ", " uses the neutral role.
- Metric color follows the **direction of change** (delta), not "operation success" and not field order:
  - **add** (green): more / appeared;
  - **remove** (pink): fewer / removed / deleted;
  - **neutral** (gray): no quantity delta (example words - «уже выполнено», «пропущено», «не выполнено», «перенесено», «обновлено»); non-numeric metric tails (for example a backup path);
  - **error** (red): the error metric when the value is > 0.
- The value `0` is always neutral (dim), regardless of the metric direction (including «ошибок: 0»).
- **Canon:** per-metric delta coloring (rows above). **Optional:** positional value palette (one ordinal value number - one color across all lines) only when explicitly recorded in the project `spec_ui.html`.
- The block title for a list/action - section/title role.
- A summary is one counter line, not a second table and not a panel.
- The log gets the same meaning in plain without ANSI.

---

## 03.05. Texts and Localization

*Required.*

- User-facing menu and message strings go through `t()` (`project_standards.md`, Section 04.01), except status/unit hardcodes explicitly listed in the project `spec_ui.html`.
- Record units of measure, status values in cells, and state wording in the project `spec_ui.html` method.
- Inline commands in text use the command role (Section 03.01): helpers `emit_message_with_command` / `menu_item_with_command` or equivalent.
- Reference hints (not an action result) use the hint role: helper `emit_hint_with_command` or equivalent; text `* <hint>`, italic + dim; an inline command uses the command role.

---

## 04.01. After an Item Is Selected

*Required when a menu frame exists.*

- Immediately after `input()` in `finish_screen_prompt` - `clear_screen` (do not leave the previous frame body on screen).
- Then the action (if needed) and a full frame of the next state via `begin_screen` (clear again) -> menu -> body -> blank -> `[>]`.
- Do not duplicate the user's choice in the menu console with a separate announce above the items; write the choice to the log via `log_file_only` (or an equivalent semantic log).
- The action result goes into the body (pending) above the **fresh** screen overview (tables/messages after re-reading state), or the screen changes per the contract in Section 02.04 / project `spec_ui`. Pending + current tables is the norm, not "no redraw"; tables must reflect state after the action.
- **Invalid input** and "nothing selected" - not via `logger.warning` to the console; the next frame pending is a «Выбор» section + a line (error / neutral role); the log gets `log_file_only`. See Section 04.03.
- Do not duplicate a second selection title above the menu on the return frame.
- Do not use the `[>] N` / «Выбран пункт [N]» canon.
- The contract is common to all project menu loops (main, subsections, screens with table rows).

---

## 04.02. Two Channels (Console and Log)

*Required.*

- **Console:** clear, color, rich tables, menu frame through the presentation channel (`src/menu.py`, `print` / ANSI clear), not through the info logger to the console. Session messages (Section 04.03) also go through `print` / `emit_session_notice`.
- **Log file:** plain; format `YYYY-MM-DD HH:MM:SS [marker] message` (`project_standards.md` 04.04.01); tables per the hierarchy in Section 03.02; summaries and commands without ANSI; no clear.
- User actions and results are written to the log even when the console shows only the current frame.
- Service hints outside the frame body may go to the log only (`log_file_only`).
- Entry-point logger: `mode="menu"` or `mode="rich"` (`project_standards.md`, Sections 04.06, 04.07). The `mode` parameter disables `console_message()`; the frame is rendered only by the presentation channel. Non-interactive signs (no TTY, `CI`, `TERM=dumb`) - `project_standards.md` (Section 04.07).
- Menus, section titles, prompts, clear, and decorative elements are not written to the log.

**Abstract log stream example** (the same scenario as the frame with a body in Section 02.01; the `{t("...")}` entry marks the place of a domain string from translations - the log receives the finished message text, not the key):

```
2026-07-21 21:00:20 [i] {t("msg.action_title")}
2026-07-21 21:00:20 [i] - item_a
2026-07-21 21:00:20 [i] - item_b
2026-07-21 21:00:20 [i] {t("msg.action_done")}: ok: 2, skip: 0
```

---

## 04.03. Session Messages

*Required when a menu frame exists.*

Messages outside the usual pending action: application start, interruption (Ctrl+C / EOF), invalid or empty input. Not through the info logger to the menu console; through `print` / `emit_session_notice` (or equivalent).

- **Form:** section title (cyan) + one body line. The startup banner and the interruption message are an **exception**: only an item text role line, no section (single-line banner). The interruption message is optional: exiting without it is allowed (`project_standards.md`, Section 05.03).
- **Log:** message text only via `log_file_only` (no ANSI).
- **Start:** only `msg.app_started` (name version), item text role, no section.
- **Ctrl+C / EOF:** after `clear_screen` when printing the message - only `msg.interrupted`, item text role, no section; the message is optional and exiting without it is allowed. Interception points: menu loops (`finish_screen_prompt` / `input()`) and the outer entry-point wrapper (dependencies, preparation, `run()` before the menu). Then exit cleanly with code 130 (`project_standards.md`, Section 05.03).
- **Invalid choice:** next frame pending - «Выбор» section + `msg.invalid_choice`; error role.
- **Nothing selected:** pending - «Выбор» section + `msg.nothing_selected`; neutral role.
- API: `emit_session_notice` (immediately to screen); `_queue_notice_body` / `_queue_invalid_choice` / `_queue_nothing_selected` (pending); `_emit_interrupted`.

---

## 04.04. Batch / Non-Menu CLI

*Optional - when the project provides a batch CLI outside the menu.*

- A CLI outside the menu, but **the same visual style** as the session (not the info logger to the console as the only frame channel).
- Output (top to bottom): `msg.app_started` banner (item text role, no section) -> startup sections if needed (run parameters, paths) -> progress during a long run (below) -> **one** table of status columns -> **color summaries** below it (not a second table and not a panel). A blank line before a table/section title (Section 02.01).
- Summaries may be several lines of one style (total, subtotal, archive path, time) - each per Section 03.04 (per-metric coloring; value `0` neutral). Do not merge unrelated totals into a second table.
- Console - rich + colored summaries; log - plain (lines/list/summary; `tabulate` only when a tabular structure is required).
- The column, cell status, and summary template contract lives in the project `spec_ui.html` (output point map and batch method).
- **Interactive context:** canonical definition and signs - `project_standards.md` 04.07. Outside the interactive context - `mode="plain"`, no Live/progress. Decide once at entry-point initialization.
- Mutating batch commands require an explicit `--dry-run` (`project_standards.md` 03.01); note in the mockup if dry-run changes the set of sections/summaries (plan instead of apply).

**Presentation modules (roles, not domain implementation):**

| Module | Responsibility |
|--------|----------------|
| `src/rich_console.py` | Shared `Console`, banner, sections, progress, dual-channel to log |
| `src/console_table.py` | Dual render of tables; `status_col` + status map (Section 03.02) |
| `src/console_summary.py` | Summaries from Section 03.04 (per-metric delta; positional palette optional per `spec_ui`) |
| `src/logger.py` | `mode="rich"`, `log_file_only`; console output through `console_message()` and the presentation layer |

**`src/rich_console.py` (batch contract):**

- `Console(highlight=False, soft_wrap=False)` - otherwise rich highlights paths/numbers itself and breaks roles.
- Dual-channel helpers: banner / section title / summary write styled text to the console in an interactive context and the same text to the log via `log_file_only`; outside it - via `console_message()` (plain format).
- A blank line before a section title - inside the section helper (the caller does not duplicate `print()`).
- Positional value palette (optional, when recorded in `spec_ui`): one ordinal value number - one color across all summary lines; the key uses the section role/cyan. The summary canon is per-metric delta (Section 03.04).

**Two-line progress (`rich.progress` + `Live`, interactive console only):**

- Layout (two lines under the section title):
  1. active item - numeric key role (bold yellow); a typographic marker before the name is **recommended** (for example `▸ name` or ASCII `> name`) - a visual "first floor" above the bar; not an emoji pack;
  2. bar + percentage + counter.
- Bar width is fixed (`bar_width=40` or equivalent) so percentages/counters do not jump when terminal width changes.
- Counter with leading zeros to the width of total (`04/23`, `09/23`) - alignment per core standard Section 04.04; a dedicated `ProgressColumn` if needed.
- Context API: `step(name)` - update the active item name **before** work; `advance()` - move the counter **after** processing an item (otherwise the bar lies during a long operation).
- Progress is not written to the log; per-item results and retry noise - `log_file_only` (or `console_message()` outside Live).
- Outside an interactive context, do not print progress to the console; results and the list go through `console_message()` in plain mode.
- Do not mix with the `\r` progress from `src/progress.py` (`project_standards.md`, Section 04.07.01). The signal handler (Section 05.03) must terminate Live/progress before exit.

The illustrative batch frame order and two-line progress are in the `doc/specs/spec_ui.html` template (sections 01 and 01.01 - batch sample).

---

## 04.05. Examples vs Method

*Required.*

- Frame examples in `spec_ui.html` may simplify numbers, truncate long paths, and show a "full" item set as a "when the condition holds" scenario.
- If a frame card conflicts with the method or code, the method and code win; align the card on the next reference edit.
- Temporary digit exceptions (Section 02.03) - only with an explicit note in `spec_ui`.
- The log fragment is a sample of the stream format, not a full session dump.
- ` ← если <condition>` tails of conditional items - only in the mockup, never at runtime.

---

## 05.01. Porting Checklist for Another Repository

*Required when porting to another repository.*

1. Record the role palette (including command, hint, add, remove, column header) in `spec_ui.html`.
2. One menu module: full `clear_screen`, breadcrumb, items, body, then `[>]` at the bottom (no cursor tricks); letters `Z X C V B N M` top-down; digits for table rows (plus explicit temporary exceptions in `spec_ui` if needed); navigation items use the navigation role. A blank line before every section title / table title.
3. One dual-render table module; title justify left; column headers use the column header role; frame body from re-read state.
4. One summary module with Section 03.04 rules (delta coloring).
5. HTML reference: mockup version, navigation map, examples, method; method+code priority over examples; footer with the full absolute path.
6. Record the "which action leads to which screen" contract (Section 02.04) and conditional items (Section 02.05).
7. Session messages (start, interruption, invalid input) - Section 04.03; not via the info logger to the console.
8. UI texts from localization; units and statuses in the `spec_ui` method.
9. Check the TTY: `[>]` below the body; blank lines before every section title; no tail from the previous body; breadcrumb on the left without `---`; log is a plain stream.
10. Batch CLI (if any): dual-channel helpers; interactive context - `project_standards.md` (Section 04.07); with progress - two lines (marker+name / bar+zero-padded counter); `status_col` + map for the status column; summaries per Section 03.04; mutations - `--dry-run` (`project_standards.md`, Section 03.01).

---

## 05.02. Related Documents

| Topic | Normative location |
|-------|--------------------|
| i18n `t()`, translations | `project_standards.md` 04.01 |
| Markers, text style | 04.02, 04.03 |
| Log line format, plain | 04.04.01, 04.06 |
| Logger mode selection, progress, rich Live, interactive context | 04.07, 04.07.01, 04.07.03 |
| `log_file_only`, `console_message` | 04.06 |
| `--dry-run` for CLI mutations | 03.01 |
| GUI | 04.08; screens in `spec_ui.html` |
| Menu frame, roles, keys, UI tables, summaries, session messages, spec_ui | **this document** |
| Menu in README | `repo_info_doc_standards.md` 02.03: the map is not duplicated, README links to `spec_ui.html` |
| Rollout order / verification | 07.03, 07.04 |

`print()` / screen clearing in `src/menu.py` is a permitted exception to the ban on direct output outside the logger (`project_standards.md` 04.06). ANSI cursor tricks (CUP, CSI s/u, DECSTBM) are not used: the frame is built with ordinary output + `input()`.

---

## 05.03. Versioning

Versioning of the standards package is unified for all package documents. The versioning policy, registry, and routing map are in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see `_index_standards.md`).
