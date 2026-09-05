#!/usr/bin/env bash
# Деплой навыка формата Anthropic Agent Skills: копирование каталога навыка
# в боевой каталог целевого инструмента с заменой существующей копии.
# Использование:
#   deploy.sh <source-dir> <target-dir>
#   <source-dir> - каталог навыка с SKILL.md в корне (например doc/skills/<name>)
#   <target-dir> - целевой каталог (например .opencode/skills/<name>)

set -euo pipefail

now() { date '+%Y-%m-%d %H:%M:%S'; }

if [ "$#" -ne 2 ]; then
    echo "$(now) [!] Использование: deploy.sh <source-dir> <target-dir>" >&2
    exit 2
fi

SOURCE="${1%/}"
TARGET="$2"

if [ ! -d "$SOURCE" ]; then
    echo "$(now) [!] Каталог навыка не найден: $SOURCE" >&2
    exit 2
fi

if [ ! -f "${SOURCE}/SKILL.md" ]; then
    echo "$(now) [!] SKILL.md отсутствует в корне: $SOURCE" >&2
    exit 2
fi

PARENT="$(dirname "$TARGET")"
mkdir -p "$PARENT"

ACTION="скопирован"
if [ -e "$TARGET" ]; then
    rm -rf -- "$TARGET"
    ACTION="заменен"
fi

cp -r -- "$SOURCE" "$TARGET"
echo "$(now) [i] Навык ${ACTION}: ${SOURCE} -> ${TARGET}"
