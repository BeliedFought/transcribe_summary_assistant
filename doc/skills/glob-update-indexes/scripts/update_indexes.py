#!/usr/bin/env python3
"""Rebuild local repository indexes: doc/skills/_index_skills_repo.md,
doc/specs/_index_specs.md, and data/skills/_index_skills_pl.md
per index_nav_standards.md.

Usage (run from repository root):
    update_indexes.py [--skills] [--specs] [--local-skills]
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True

SKILLS_DIR = Path("doc/skills")
SKILLS_INDEX = SKILLS_DIR / "_index_skills_repo.md"
SPECS_DIR = Path("doc/specs")
SPECS_INDEX = SPECS_DIR / "_index_specs.md"
INIT_DIR = SPECS_DIR / "init"
LOCAL_SKILLS_DIR = Path("data/skills")
LOCAL_SKILLS_INDEX = LOCAL_SKILLS_DIR / "_index_skills_pl.md"
STD_INDEX = Path("doc/standards/_index_standards.md")

EXIT_OK = 0

SKILLS_APPLY = """## Mandatory Application

Tagging this file requires applying relevant skills, not merely reading the index:

1. Identify relevant skills via the routing map
2. Open the matched skill files and follow their instructions
3. Apply relevant skills whenever a matching task arises, even without explicit tagging"""

SKILLS_MAP_NOTE = """Maps task topics to skills (`index_nav_standards.md`, Section 04).

| Task Topic | Skill |
|------------|-------|"""

SKILLS_AUTO = """## Index Auto-Update

On any change to `doc/skills/` (adding, removing, renaming, or updating skill frontmatter), rebuild this index with `glob-update-indexes` and report added, updated, and removed entries. Refine purposes and routing map topics in the skill frontmatter (`metadata.purpose`, `metadata.topic`), not in the generated cells - the next rebuild replaces them; wording rules - `index_nav_standards.md` (Sections 03.03, 04). Sections outside the canonical skeleton are preserved and appended after this section.
"""

SPECS_APPLY = """## Mandatory Application

Tagging this file requires using the index when working with specifications:

1. Identify relevant files via the registry and routing map
2. Open only relevant files rather than the entire directory
3. Update this index on any change to `doc/specs/`"""

SPECS_MAP_TOPICS = {
    "init_base.txt": "Initial project requirements, free-form (bootstrap)",
    "init_final.md": "Finalized initialization specification (bootstrap)",
    "spec_ui.html": "Output/UI specification: menu map, frames, keys, log layout",
    "overrides.md": "Project standard overrides",
    "text_overrides.md": "Text overrides: domain terms, forbidden words, canonical vocabulary",
}

SPECS_MAP_NOTE = """Maps task topics to specification files.

| Task Topic | File |
|------------|------|"""

SPECS_AUTO = """## Index Auto-Update

On any change to `doc/specs/` (adding, removing, renaming, or changing file purpose), rebuild this index with `glob-update-indexes`, fill in purposes (include layout SemVer for `spec_ui.html`), update the routing map per `index_nav_standards.md` (Sections 03.03, 04), and report added, updated, and removed entries.
"""

PL_APPLY = """## Mandatory Application

Tagging this file requires applying relevant local skills, not merely reading the index:

1. Identify relevant skills via the routing map
2. Open the matched skill files and follow their instructions
3. Apply relevant skills whenever a matching task arises, even without explicit tagging"""

PL_AUTO = """## Index Auto-Update

On any change to `data/skills/` (adding, removing, renaming, or updating skill frontmatter), rebuild this index with `glob-update-indexes` and report added, updated, and removed entries. Refine purposes and routing map topics in the skill frontmatter (`metadata.purpose`, `metadata.topic`), not in the generated cells - the next rebuild replaces them; wording rules - `index_nav_standards.md` (Sections 03.03, 04). Sections outside the canonical skeleton are preserved and appended after this section.
"""


OWNED_SECTIONS = {
    "Mandatory Application",
    "Skill Registry",
    "Anthropic Agent Skills (SKILL.md)",
    "Routing Map",
    "Index Auto-Update",
}


def now() -> str:
    """Timestamp in strict logger format (04.04.01)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def info(message: str) -> None:
    print(f"{now()} [i] {message}")


def warn(message: str) -> None:
    print(f"{now()} [*] {message}")


STOP_TAIL = {
    "и", "или", "а", "но", "да", "что", "чтобы", "как", "когда", "если", "чем",
    "в", "во", "на", "по", "с", "со", "из", "от", "до", "для", "при", "про",
    "без", "над", "под", "за", "об", "о", "у", "к", "ко", "не", "же", "ли", "бы",
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "as", "at", "from", "into", "over", "under", "that", "which", "when", "if",
}

ABBREVIATIONS = {
    "т", "е", "к", "п", "д", "др", "пр", "см", "напр", "рис", "табл", "гл",
    "e.g", "i.e", "etc", "vs", "fig",
}


def sentence_end(text: str) -> int:
    """Index after the first sentence terminator, skipping abbreviations and initials."""
    for m in re.finditer(r"[.!?](?=\s|$)", text):
        head = text[: m.start()].rstrip()
        raw = (head.rsplit(" ", 1)[-1] if head else "").strip("\"'`()[]{}«»")
        if len(raw) == 1 and raw.isalpha():
            continue
        if raw.lower().rstrip(".") in ABBREVIATIONS:
            continue
        return m.end()
    return -1


def first_sentence(description: str) -> str:
    """First sentence of description, complete, with no mid-phrase truncation."""
    text = " ".join((description or "").split())
    if not text:
        return ""
    end = sentence_end(text)
    sent = text[:end] if end > 0 else text
    return sent.strip().rstrip(".!?").strip()


def purpose_value(meta: dict, fallback: str) -> str:
    """Purpose: explicit frontmatter value, else the full first sentence, else the old index value."""
    explicit = (meta.get("purpose") or "").strip()
    if explicit:
        return explicit
    desc = (meta.get("description") or "").strip()
    if desc:
        return first_sentence(desc)
    return fallback


def topic_value(purpose: str, explicit: str | None) -> str:
    """Map topic: explicit frontmatter value, else the purpose head before the colon."""
    explicit = (explicit or "").strip()
    if explicit:
        return explicit
    head, sep, _ = purpose.partition(":")
    if sep and head.strip():
        return head.strip()
    return purpose


def check_row(index_label: str, ident: str, purpose: str, topic: str, explicit_topic: bool,
              dup_topics: list[str]) -> None:
    """Report stopped purposes and collect topics that duplicate the purpose."""
    if not purpose or purpose == "-":
        return
    tail = purpose.rstrip(" .,;:-").rsplit(" ", 1)[-1].lower()
    if tail in STOP_TAIL:
        warn(f"{index_label}: purpose of `{ident}` ends with a stop word `{tail}`")
    if not explicit_topic and topic == purpose:
        dup_topics.append(ident)


TYPE_CLASS = {
    "hub_glob": "global",
    "pr_glob": "project",
    "hub_loc": "hub",
    "pr_loc": "local",
}

PREFIX_TYPE = {
    "hub": "hub_loc",
    "glob": "hub_glob",
    "pg": "pr_glob",
    "pl": "pr_loc",
}


def type_slug(name: str, declared: str | None) -> str | None:
    """Skill type slug: from frontmatter, or fallback by name prefix."""
    if declared:
        return declared
    parts = re.split(r"[_\-]", name)
    return PREFIX_TYPE.get(parts[0]) if parts else None


def class_of(name: str, declared: str | None) -> str:
    """Skill class label by type slug."""
    return TYPE_CLASS.get(type_slug(name, declared) or "", "project")


def area_value(category: str | None, category_name: str | None) -> str:
    """Scope column value: category_name (`category`) or dash."""
    if category and category_name:
        return f"{category_name} (`{category}`)"
    return "-"


def get_index_version(index_path: Path) -> str:
    """Extract SemVer from existing index H1 or _index_standards.md, fallback 1.0.0."""
    for p in (index_path, STD_INDEX):
        if p.exists():
            lines = p.read_text(encoding="utf-8").splitlines()
            if lines:
                m = re.search(r"(?:Version|Версия)\s+(\d+\.\d+\.\d+)", lines[0])
                if m:
                    return m.group(1)
    return "1.0.0"


def frontmatter(path: Path) -> dict:
    meta: dict[str, str | None] = {
        "id": None, "description": None, "auto_apply": None, "version": None, "type": None,
        "category": None, "category_name": None, "purpose": None, "topic": None,
    }
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        fm = text[3:end] if end > 0 else ""
        for key in meta:
            m = re.search(rf"^{key}:\s*(.+)$", fm, re.MULTILINE)
            if not m and key in ("purpose", "topic"):
                m = re.search(rf"^[ \t]+{key}:\s*(.+)$", fm, re.MULTILINE)
            if m:
                meta[key] = m.group(1).strip()
    return meta


def spec_type(name: str) -> str:
    known = {
        "init_base.txt": "Requirements",
        "init_final.md": "Final init spec",
        "spec_ui.html": "UI spec",
        "overrides.md": "Overrides",
        "text_overrides.md": "Text overrides",
    }
    if name in known:
        return known[name]
    if re.fullmatch(r"spec_.+\.md", name):
        return "Module/task spec"
    return "Other"


def old_purposes(path: Path) -> dict[str, str]:
    purposes: dict[str, str] = {}
    if not path.exists():
        return purposes
    in_map = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(("## Routing Map", "## Карта маршрутизации")):
            in_map = True
            continue
        if in_map and line.startswith("## "):
            in_map = False
        if in_map:
            continue
        m = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if m:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 2 and cells[-1] and cells[-1] != "-":
                purposes[m.group(1)] = cells[-1]
    return purposes


def old_map_rows(path: Path) -> list[tuple[str, str]]:
    """Extract existing (topic, target) rows from the Routing Map section of any index."""
    rows: list[tuple[str, str]] = []
    if not path.exists():
        return rows
    in_map = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(("## Routing Map", "## Карта маршрутизации")):
            in_map = True
            continue
        if in_map and (line.startswith("## ") or line.startswith("---")):
            in_map = False
            continue
        if not in_map:
            continue
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|$", line.strip())
        if m:
            topic, target = m.group(1).strip(), m.group(2).strip()
            if "<" in target or ">" in target:
                continue
            rows.append((topic, target))
    return rows


def old_map_by_target(path: Path) -> dict[str, str]:
    """First old routing-map topic per target object."""
    by_target: dict[str, str] = {}
    for topic, target in old_map_rows(path):
        by_target.setdefault(target, topic)
    return by_target


def split_sections(path: Path) -> list[tuple[str, list[str]]]:
    """Existing sections as (heading, body) pairs; H1 and intro are skipped."""
    sections: list[tuple[str, list[str]]] = []
    if not path.exists():
        return sections
    heading: str | None = None
    body: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if heading is not None:
                sections.append((heading, body))
            heading = line[3:].strip()
            body = []
            continue
        if heading is not None:
            body.append(line)
    if heading is not None:
        sections.append((heading, body))
    return sections


def foreign_sections(path: Path) -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Sections outside the generator-owned set and their names found before the last owned one."""
    sections = split_sections(path)
    foreign = [(heading, body) for heading, body in sections if heading not in OWNED_SECTIONS]
    last_owned = -1
    for i, (heading, _) in enumerate(sections):
        if heading in OWNED_SECTIONS:
            last_owned = i
    misplaced = [heading for i, (heading, _) in enumerate(sections)
                 if heading not in OWNED_SECTIONS and i < last_owned]
    return foreign, misplaced


def render_section(heading: str, body: list[str]) -> list[str]:
    """Section lines with the heading, one blank line, and the trimmed body."""
    trimmed = list(body)
    while trimmed and trimmed[-1].strip() in ("", "---"):
        trimmed.pop()
    while trimmed and not trimmed[0].strip():
        trimmed.pop(0)
    return [f"## {heading}", ""] + trimmed


def append_foreign_sections(lines: list[str], path: Path, label: str) -> None:
    """Append preserved sections after the last owned one (index_nav_standards.md, 03.01)."""
    preserved, misplaced = foreign_sections(path)
    for heading in misplaced:
        warn(f"{label}: section `{heading}` moved after `## Index Auto-Update` - "
             f"check the order (index_nav_standards.md, 03.01)")
    if preserved and lines:
        lines[-1] = lines[-1].rstrip("\n")
    for heading, body in preserved:
        lines.extend(["", "---", ""])
        lines.extend(render_section(heading, body))
    if preserved:
        info(f"{label}: preserved foreign sections: {', '.join(h for h, _ in preserved)}")


def merged_topic(ident: str, purpose: str, explicit: str, old_topics: dict[str, str],
                 label: str) -> str:
    """Map topic: explicit frontmatter value, else the old index row, else the purpose head."""
    explicit = (explicit or "").strip()
    if explicit:
        return explicit
    derived = topic_value(purpose, None)
    previous = old_topics.get(ident)
    if previous and previous != derived:
        warn(f"{label}: topic for `{ident}` migrated from the previous index - "
             f"set `metadata.topic` in frontmatter")
        return previous
    return derived


def anthropic_meta(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta = {"name": "", "description": "", "version": "", "type": "", "category": "",
            "category_name": "", "purpose": "", "topic": ""}
    if not text.startswith("---"):
        return meta
    end = text.find("\n---", 3)
    fm = text[3:end] if end > 0 else ""
    for key in ("name", "description"):
        m = re.search(rf"^{key}:\s*(.+)$", fm, re.MULTILINE)
        if m:
            meta[key] = m.group(1).strip()
    for key in ("version", "type", "category", "category_name", "purpose", "topic"):
        m = (re.search(rf"^[ \t]+{key}:\s*(\S.*)$", fm, re.MULTILINE)
             or re.search(rf"^{key}:\s*(\S.*)$", fm, re.MULTILINE))
        if m:
            meta[key] = m.group(1).strip()
    return meta


def warn_purpose_override(label: str, ident: str, meta: dict, old: str | None,
                          purpose: str) -> None:
    """Report a previous index purpose replaced by the description."""
    if not (meta.get("purpose") or "").strip() and old and old != purpose:
        warn(f"{label}: previous purpose of `{ident}` replaced with the first sentence "
             f"of the description - set `metadata.purpose` in frontmatter")


def rebuild_skills_index(root: Path) -> None:
    if not SKILLS_DIR.exists():
        warn(f"Skipped skills index: folder {SKILLS_DIR} not found")
        return
    ver = get_index_version(SKILLS_INDEX)
    purposes = old_purposes(SKILLS_INDEX)
    old_topics = old_map_by_target(SKILLS_INDEX)
    skills = [p for p in sorted(SKILLS_DIR.glob("*.md")) if not p.name.startswith("_index")]
    sub_skills = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if (d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_index")
                and not (d / "SKILL.md").is_file()):
            sub_skills.extend(sorted(d.glob("pg_*.md")))
    lines = [
        f"# Repository Skills Index. Version {ver}",
        "",
        f"Entry point for `doc/skills/` in `{root.name}`: lists global (`glob-*`, `glob_*`) and project (`pg-*`, `pg_*`) skills. Load this index rather than the full directory and use the routing map to open relevant skills. Decision order when norms are absent - `project_standards.md`, Section 07.06.",
        "",
        "---",
        "",
        SKILLS_APPLY,
        "",
        "---",
        "",
    ]
    map_rows = []
    dup_topics: list[str] = []
    if skills or sub_skills:
        lines += [
            "## Skill Registry",
            "",
            "| Skill | Class | Scope | Auto-Apply | Version | Purpose |",
            "|-------|-------|-------|------------|---------|---------|",
        ]
    for p in skills + sub_skills:
        m = frontmatter(p)
        cls = class_of(p.stem, m["type"])
        ident = m["id"] or p.stem
        old = purposes.get(ident)
        purpose = purpose_value(m, old or "-")
        warn_purpose_override("skills index", ident, m, old, purpose)
        topic = merged_topic(ident, purpose, m["topic"] or "", old_topics, "skills index")
        check_row("skills index", ident, purpose, topic, bool((m["topic"] or "").strip()), dup_topics)
        lines.append(f"| `{ident}` | {cls} | {area_value(m['category'], m['category_name'])} | {m['auto_apply'] or '-'} | {m['version'] or '-'} | {purpose} |")
        map_rows.append(f"| {topic} | `{ident}` |")
    if skills or sub_skills:
        lines.append("")
    anthropic = [
        d
        for d in sorted(SKILLS_DIR.rglob("SKILL.md"))
        if "/templates/" not in d.as_posix()
    ]
    if anthropic:
        lines += [
            "## Anthropic Agent Skills (SKILL.md)",
            "",
            "| Skill (dir) | Class | Scope | Version | Purpose |",
            "|-------------|-------|-------|---------|---------|",
        ]
        for d in anthropic:
            m = anthropic_meta(d)
            name = d.parent.relative_to(SKILLS_DIR).as_posix()
            cls = class_of(name, m["type"])
            old = purposes.get(name)
            purpose = purpose_value(m, old or "-")
            warn_purpose_override("skills index", name, m, old, purpose)
            topic = merged_topic(name, purpose, m["topic"], old_topics, "skills index")
            check_row("skills index", name, purpose, topic, bool((m["topic"] or "").strip()), dup_topics)
            lines.append(f"| `{name}` | {cls} | {area_value(m['category'], m['category_name'])} | {m['version'] or '-'} | {purpose} |")
            map_rows.append(f"| {topic} | `{name}` |")
        lines.append("")
    lines += [
        "---",
        "",
        "## Routing Map",
        "",
        SKILLS_MAP_NOTE,
        *map_rows,
        "",
        "---",
        "",
        SKILLS_AUTO,
    ]
    append_foreign_sections(lines, SKILLS_INDEX, "skills index")
    if dup_topics:
        warn(f"Skills index: topic equals purpose - set `metadata.topic`: "
             f"{', '.join(dup_topics)}")
    SKILLS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    info(f"Updated {SKILLS_INDEX} - skills: {len(skills) + len(sub_skills)}, SKILL.md directories: {len(anthropic)}")
    for p in skills:
        info(f"- {p.name}")


def rebuild_local_skills_index(root: Path) -> None:
    if not LOCAL_SKILLS_DIR.exists():
        warn(f"Skipped local skills index: folder {LOCAL_SKILLS_DIR} not found")
        return
    purposes = old_purposes(LOCAL_SKILLS_INDEX)
    old_topics = old_map_by_target(LOCAL_SKILLS_INDEX)
    flat = [p for p in sorted(LOCAL_SKILLS_DIR.glob("*.md")) if not p.name.startswith("_index")]
    dirs = [d for d in sorted(LOCAL_SKILLS_DIR.iterdir())
            if d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").is_file()]
    lines = [
        "# Local Repository Skills Index",
        "",
        f"Entry point for `data/skills/` in `{root.name}`: lists local skills (`pr_loc`) excluded from shared indexes. Load this index rather than the full directory and use the routing map to open relevant skills. Decision order when norms are absent - `project_standards.md`, Section 07.06.",
        "",
        "---",
        "",
        PL_APPLY,
        "",
        "---",
        "",
    ]
    map_rows = []
    dup_topics: list[str] = []
    if flat:
        lines += [
            "## Skill Registry",
            "",
            "| Skill | Class | Scope | Auto-Apply | Version | Purpose |",
            "|-------|-------|-------|------------|---------|---------|",
        ]
    for p in flat:
        m = frontmatter(p)
        ident = m["id"] or p.stem
        old = purposes.get(ident)
        purpose = purpose_value(m, old or "-")
        warn_purpose_override("local skills index", ident, m, old, purpose)
        topic = merged_topic(ident, purpose, m["topic"] or "", old_topics, "local skills index")
        check_row("local skills index", ident, purpose, topic, bool((m["topic"] or "").strip()), dup_topics)
        lines.append(f"| `{ident}` | local | {area_value(m['category'], m['category_name'])} | {m['auto_apply'] or '-'} | {m['version'] or '-'} | {purpose} |")
        map_rows.append(f"| {topic} | `{ident}` |")
    if flat:
        lines.append("")
    if dirs:
        lines += [
            "## Anthropic Agent Skills (SKILL.md)",
            "",
            "| Skill (dir) | Class | Scope | Version | Purpose |",
            "|-------------|-------|-------|---------|---------|",
        ]
        for d in dirs:
            m = anthropic_meta(d / "SKILL.md")
            old = purposes.get(d.name)
            purpose = purpose_value(m, old or "-")
            warn_purpose_override("local skills index", d.name, m, old, purpose)
            topic = merged_topic(d.name, purpose, m["topic"], old_topics, "local skills index")
            check_row("local skills index", d.name, purpose, topic, bool((m["topic"] or "").strip()), dup_topics)
            lines.append(f"| `{d.name}` | local | {area_value(m['category'], m['category_name'])} | {m['version'] or '-'} | {purpose} |")
            map_rows.append(f"| {topic} | `{d.name}` |")
        lines.append("")
    lines += [
        "---",
        "",
        "## Routing Map",
        "",
        SKILLS_MAP_NOTE,
        *map_rows,
        "",
        "---",
        "",
        PL_AUTO,
    ]
    append_foreign_sections(lines, LOCAL_SKILLS_INDEX, "local skills index")
    if dup_topics:
        warn(f"Local skills index: topic equals purpose - set `metadata.topic`: "
             f"{', '.join(dup_topics)}")
    LOCAL_SKILLS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    info(f"Updated {LOCAL_SKILLS_INDEX} - skills: {len(flat)}, SKILL.md directories: {len(dirs)}")
    for p in flat:
        info(f"- {p.name}")
    for d in dirs:
        info(f"- {d.name}/")


def spec_map_row(key: str, name: str) -> str | None:
    if name in SPECS_MAP_TOPICS:
        return f"| {SPECS_MAP_TOPICS[name]} | `{key}` |"
    if re.fullmatch(r"spec_.+\.md", name):
        return f"| Module or task specification `{name}` | `{key}` |"
    return None


def rebuild_specs_index(root: Path) -> None:
    if not SPECS_DIR.exists():
        warn(f"Skipped specs index: folder {SPECS_DIR} not found")
        return
    purposes = old_purposes(SPECS_INDEX)
    existing_map = old_map_rows(SPECS_INDEX)
    root_files = sorted(
        p for p in SPECS_DIR.iterdir()
        if p.is_file() and p.name not in ("_index_specs.md", ".gitkeep")
    )
    init_files = sorted(
        p for p in INIT_DIR.iterdir()
        if p.is_file() and p.name not in (".gitkeep", "_index_specs.md")
    ) if INIT_DIR.is_dir() else []
    subdirs = sorted(d for d in SPECS_DIR.iterdir()
                     if d.is_dir() and d.name != "init" and not d.name.startswith("."))
    lines = [
        "# Specifications Index",
        "",
        f"Entry point for `doc/specs/` in `{root.name}`. Load this index rather than the full directory and open only relevant files via the registry and routing map. Decision order when norms are absent - `project_standards.md`, Section 07.06.",
        "",
        "---",
        "",
        SPECS_APPLY,
        "",
        "---",
        "",
        "## Root Files Registry",
        "",
        "| File | Type | Purpose |",
        "|------|------|---------|",
    ]
    for p in root_files:
        lines.append(f"| `{p.name}` | {spec_type(p.name)} | {purposes.get(p.name, '-')} |")
    lines.append("")
    if init_files:
        lines += [
            "## Bootstrap Specifications (`init/`)",
            "",
            "| File | Type | Purpose |",
            "|------|------|---------|",
        ]
        for p in init_files:
            key = f"init/{p.name}"
            lines.append(f"| `{key}` | {spec_type(p.name)} | {purposes.get(key, purposes.get(p.name, '-'))} |")
        lines.append("")
    if subdirs:
        lines += [
            "## Project Subfolders",
            "",
            "| Folder | Files | Purpose |",
            "|--------|-------|---------|",
        ]
        for d in subdirs:
            names = [f.name for f in sorted(d.iterdir()) if f.is_file()]
            key = f"{d.name}/"
            lines.append(f"| `{key}` | {', '.join(names) or '-'} | {purposes.get(key, '-')} |")
        lines.append("")
    map_rows: list[str] = []
    covered_targets: set[str] = set()
    for topic, target in existing_map:
        target_path = SPECS_DIR / target.rstrip("/")
        if target_path.exists():
            map_rows.append(f"| {topic} | `{target}` |")
            covered_targets.add(target)
    for p in root_files:
        if p.name not in covered_targets:
            row = spec_map_row(p.name, p.name)
            if row:
                map_rows.append(row)
    for p in init_files:
        key = f"init/{p.name}"
        if key not in covered_targets and p.name not in covered_targets:
            row = spec_map_row(key, p.name)
            if row:
                map_rows.append(row)
    lines += [
        "---",
        "",
        "## Routing Map",
        "",
        SPECS_MAP_NOTE,
        *map_rows,
        "",
        "---",
        "",
        SPECS_AUTO,
    ]
    SPECS_INDEX.write_text("\n".join(lines), encoding="utf-8")
    info(f"Updated {SPECS_INDEX} - root files: {len(root_files)}, "
         f"init files: {len(init_files)}, subfolders: {len(subdirs)}")
    for p in root_files:
        info(f"- {p.name}")
    for p in init_files:
        info(f"- init/{p.name}")
    for d in subdirs:
        info(f"- {d.name}/")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild local repository indexes (_index_skills_repo.md, _index_specs.md, _index_skills_pl.md)"
    )
    parser.add_argument("--skills", action="store_true", help="rebuild only doc/skills/_index_skills_repo.md")
    parser.add_argument("--specs", action="store_true", help="rebuild only doc/specs/_index_specs.md")
    parser.add_argument("--local-skills", action="store_true", help="rebuild only data/skills/_index_skills_pl.md")
    args = parser.parse_args()

    any_flag = args.skills or args.specs or args.local_skills
    root = Path.cwd().resolve()

    if root.name == "project_standards":
        if not any_flag or args.skills or args.specs:
            warn("Hub project_standards: the hub index _index_skills_hub.md is owned by hub-sync-indexes, "
                 "doc/specs/_index_specs.md is the reference template; only "
                 "data/skills/_index_skills_pl.md is rebuilt")
        if not any_flag or args.local_skills:
            rebuild_local_skills_index(root)
        return EXIT_OK

    if not any_flag:
        rebuild_skills_index(root)
        rebuild_specs_index(root)
        rebuild_local_skills_index(root)
    else:
        if args.skills:
            rebuild_skills_index(root)
        if args.specs:
            rebuild_specs_index(root)
        if args.local_skills:
            rebuild_local_skills_index(root)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
