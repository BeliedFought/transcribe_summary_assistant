#!/usr/bin/env bash
# Перемещение исходника (навыка или внешнего скрипта проекта) в templates/
# пакета навыка через git mv с сохранением истории. Исходник становится
# каноном пары форматов и под своим исходным именем больше не редактируется.
# Использование:
#   move_source.sh <source-path> <skill-dir>
#   <source-path> - существующий файл в рабочем дереве git
#   <skill-dir>   - каталог пакета навыка (doc/skills/<kebab-id>)

set -euo pipefail

now() { date '+%Y-%m-%d %H:%M:%S'; }

if [ "$#" -ne 2 ]; then
    echo "$(now) [!] Использование: move_source.sh <source-path> <skill-dir>" >&2
    exit 2
fi

SOURCE="$1"
SKILL_DIR="$2"
TARGET_DIR="${SKILL_DIR%/}/templates"

if [ ! -f "$SOURCE" ]; then
    echo "$(now) [!] Исходник не найден: $SOURCE" >&2
    exit 2
fi

if [ ! -d "$SKILL_DIR" ]; then
    echo "$(now) [!] Каталог пакета навыка не найден: $SKILL_DIR" >&2
    exit 2
fi

mkdir -p "$TARGET_DIR"
TARGET="${TARGET_DIR}/$(basename "$SOURCE")"

if [ -e "$TARGET" ]; then
    echo "$(now) [!] Цель уже занята: $TARGET" >&2
    exit 2
fi

git mv -- "$SOURCE" "$TARGET"
echo "$(now) [i] Исходник перемещен: ${SOURCE} -> ${TARGET}"
