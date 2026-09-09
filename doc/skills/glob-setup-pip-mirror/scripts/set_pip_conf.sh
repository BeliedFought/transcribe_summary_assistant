#!/usr/bin/env bash
# Запись выбранного зеркала PyPI в pip.conf текущего пользователя.
# Использование:
#   set_pip_conf.sh <mirror_url>
#   <mirror_url> - URL зеркала, например https://mirror.example.com/pypi/simple/

set -euo pipefail

now() { date '+%Y-%m-%d %H:%M:%S'; }

if [ "$#" -ne 1 ]; then
    echo "$(now) [!] Использование: set_pip_conf.sh <mirror_url>" >&2
    exit 2
fi

MIRROR="$1"
CONF_DIR="$HOME/.config/pip"
CONF_FILE="$CONF_DIR/pip.conf"

mkdir -p "$CONF_DIR"
cat > "$CONF_FILE" << EOF
[global]
index-url = ${MIRROR}
EOF

echo "$(now) [i] Записано зеркало PyPI: ${MIRROR} -> ${CONF_FILE}"
