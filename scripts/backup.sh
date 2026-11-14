#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_docker
mkdir -p backups
backup_file="backups/orbit-$(date -u +%Y%m%dT%H%M%SZ).sql"
docker compose exec -T db pg_dump -U orbit -d orbit > "$backup_file"
echo "Database backup written to $backup_file"
