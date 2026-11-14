#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_docker
echo "This deletes the local Docker database volume."
read -r -p "Type DELETE LOCAL DATA to continue: " confirmation
[[ "$confirmation" == "DELETE LOCAL DATA" ]] || { echo "Cancelled."; exit 0; }
docker compose down --volumes --remove-orphans
