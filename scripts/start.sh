#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ensure_env
require_docker
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up --detach
echo "Orbit is running at http://localhost:8080"
