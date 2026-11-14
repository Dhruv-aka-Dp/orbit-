#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_docker
backup_file="${1:-}"
[[ -f "$backup_file" ]] || { echo "Usage: $0 backups/orbit-YYYYMMDDTHHMMSSZ.sql" >&2; exit 2; }
echo "This replaces the current local Orbit database with $backup_file."
read -r -p "Type RESTORE LOCAL DATA to continue: " confirmation
[[ "$confirmation" == "RESTORE LOCAL DATA" ]] || { echo "Cancelled."; exit 0; }
docker compose exec -T db psql -U orbit -d postgres -c 'DROP DATABASE IF EXISTS orbit;'
docker compose exec -T db psql -U orbit -d postgres -c 'CREATE DATABASE orbit;'
docker compose exec -T db psql -U orbit -d orbit < "$backup_file"
echo "Restore completed. Run ./scripts/migrate.sh if the backup predates the current schema."
