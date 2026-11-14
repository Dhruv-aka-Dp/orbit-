#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_docker
docker compose logs --follow --tail=200 "${1:-}"
