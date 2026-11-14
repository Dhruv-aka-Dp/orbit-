#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
"$ROOT_DIR/scripts/lint.sh"
"$ROOT_DIR/scripts/test.sh"
