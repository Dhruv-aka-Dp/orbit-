#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ensure_env() {
  if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env from .env.example. Review POSTGRES_PASSWORD before sharing this environment."
  fi
}

require_docker() {
  command -v docker >/dev/null || { echo "Docker is required." >&2; exit 1; }
  docker info >/dev/null 2>&1 || { echo "Docker daemon is not running." >&2; exit 1; }
}
