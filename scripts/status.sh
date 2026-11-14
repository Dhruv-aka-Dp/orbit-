#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_docker
docker compose ps
curl --fail --silent --show-error http://localhost:8080/api/healthz
echo
