#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_docker
docker compose build api
docker compose run --rm api python -m unittest discover -s tests -v
