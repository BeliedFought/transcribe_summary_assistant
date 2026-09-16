#!/usr/bin/env bash
# Деплой навыка формата Anthropic Agent Skills: копирование каталога навыка
# в боевой каталог целевого инструмента с заменой существующей копии
# или создание симлинка на источник (режим --link).
# Использование:
#   deploy.sh [--link] <source-dir> <target-dir>
#   --link       - создать симлинк target -> source вместо копирования
#   <source-dir> - каталог навыка с SKILL.md в корне (например doc/skills/<name>)
#   <target-dir> - целевой каталог (например .opencode/skills/<name>)

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

PARENT="$(dirname "$TARGET")"
mkdir -p "$PARENT"

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

cp -r -- "$SOURCE" "$TARGET"
echo "$(now) [i] Навык ${ACTION}: ${SOURCE} -> ${TARGET}"
