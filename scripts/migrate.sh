#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ensure_env
require_docker
docker compose run --rm api alembic upgrade head
