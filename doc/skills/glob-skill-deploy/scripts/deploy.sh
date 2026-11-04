#!/usr/bin/env bash
# Deploy an Anthropic Agent Skills format skill: copy the skill directory
# into the live directory of the target tool, replacing an existing copy,
# or create a symlink to the source (--link mode).
# Guards: refuse before deleting if the target directory equals the source,
# is nested in it, or contains it; __pycache__ directories are excluded on copy.
# Usage:
#   deploy.sh [--link] <source-dir> <target-dir>
#   --link       - create a symlink target -> source instead of copying
#   <source-dir> - skill directory with SKILL.md at the root (e.g. doc/skills/<name>)
#   <target-dir> - target directory (e.g. .opencode/skills/<name>)

set -euo pipefail

now() { date '+%Y-%m-%d %H:%M:%S'; }

MODE="copy"
if [ "${1:-}" = "--link" ]; then
    MODE="link"
    shift
fi

if [ "$#" -ne 2 ]; then
    echo "$(now) [!] Использование: deploy.sh [--link] <source-dir> <target-dir>" >&2
    exit 2
fi

SOURCE="$(readlink -f -- "${1%/}")"
TARGET="$2"

if [ ! -d "$SOURCE" ]; then
    echo "$(now) [!] Каталог навыка не найден: $SOURCE" >&2
    exit 2
fi

if [ ! -f "${SOURCE}/SKILL.md" ]; then
    echo "$(now) [!] SKILL.md отсутствует в корне: $SOURCE" >&2
    exit 2
fi

if [ -z "$TARGET" ]; then
    echo "$(now) [!] Целевой каталог не задан" >&2
    exit 2
fi

PARENT="$(dirname "$TARGET")"
mkdir -p "$PARENT"

# Absolute target path without resolving the last link: an existing symlink
# to the source is a legitimate replacement case on redeploy, not a match
TARGET_ABS="$(readlink -f -- "$PARENT")/$(basename -- "$TARGET")"

if [ "$TARGET_ABS" = "$SOURCE" ]; then
    echo "$(now) [!] Целевой каталог совпадает с источником, отказ: $TARGET_ABS" >&2
    exit 2
fi

case "$SOURCE/" in
    "$TARGET_ABS"/*)
        echo "$(now) [!] Источник находится внутри целевого каталога, отказ: $TARGET_ABS" >&2
        exit 2
        ;;
esac

case "$TARGET_ABS/" in
    "$SOURCE"/*)
        echo "$(now) [!] Целевой каталог находится внутри источника, отказ: $TARGET_ABS" >&2
        exit 2
        ;;
esac

if [ "$MODE" = "link" ]; then
    if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
        rm -rf -- "$TARGET"
        ACTION="заменен симлинком"
    else
        ACTION="развернут симлинком"
    fi
    ln -s -- "$SOURCE" "$TARGET"
    echo "$(now) [i] Навык ${ACTION}: ${TARGET} -> ${SOURCE}"
    exit 0
fi

ACTION="скопирован"
if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
    rm -rf -- "$TARGET"
    ACTION="заменен"
fi

# Copy without __pycache__ artifacts; rsync may be missing on the machine -
# then cp followed by cleanup of __pycache__ from the whole directory
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' -- "$SOURCE"/ "$TARGET"
else
    cp -r -- "$SOURCE" "$TARGET"
    find "$TARGET" -type d -name '__pycache__' -prune -exec rm -rf -- {} +
fi
echo "$(now) [i] Навык ${ACTION}: ${SOURCE} -> ${TARGET}"
