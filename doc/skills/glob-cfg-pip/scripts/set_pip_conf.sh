#!/usr/bin/env bash
# Write the selected PyPI mirror into the current user pip.conf.
# Usage:
#   set_pip_conf.sh <mirror_url>
#   <mirror_url> - mirror URL, e.g. https://mirror.example.com/pypi/simple/

set -euo pipefail

now() { date '+%Y-%m-%d %H:%M:%S'; }

if [ "$#" -ne 1 ]; then
    echo "$(now) [!] Usage: set_pip_conf.sh <mirror_url>" >&2
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

echo "$(now) [i] PyPI mirror written: ${MIRROR} -> ${CONF_FILE}"
