#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
python3 -m py_compile backend/app/*.py
node --check <(sed -n '/<script>/,/<\/script>/p' app/orbit.html | sed '1d;$d')
bash -n scripts/*.sh
echo "Static checks passed."
