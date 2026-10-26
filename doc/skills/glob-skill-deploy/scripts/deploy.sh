#!/usr/bin/env bash
# Деплой навыка формата Anthropic Agent Skills: копирование каталога навыка
# в боевой каталог целевого инструмента с заменой существующей копии
# или создание симлинка на источник (режим --link).
# Защита: отказ до удаления, если целевой каталог совпадает с источником,
# вложен в него или содержит его; при копировании исключаются каталоги __pycache__.
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

if [ -z "$TARGET" ]; then
    echo "$(now) [!] Целевой каталог не задан" >&2
    exit 2
fi

PARENT="$(dirname "$TARGET")"
mkdir -p "$PARENT"

# Абсолютный путь цели без раскрытия последнего звена: существующий симлинк
# на источник - легальный случай замены при повторном деплое, а не совпадение
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

# Копия без артефактов __pycache__; rsync может отсутствовать на машине -
# тогда cp с последующей зачисткой __pycache__ из целого каталога
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' -- "$SOURCE"/ "$TARGET"
else
    cp -r -- "$SOURCE" "$TARGET"
    find "$TARGET" -type d -name '__pycache__' -prune -exec rm -rf -- {} +
fi
echo "$(now) [i] Навык ${ACTION}: ${SOURCE} -> ${TARGET}"
