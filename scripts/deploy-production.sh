#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
: "${ORBIT_PRODUCTION_DEPLOY_COMMAND:?Set ORBIT_PRODUCTION_DEPLOY_COMMAND to your reviewed cloud deploy command.}"
echo "Production deployment requires all MANUAL_RELEASE_STEPS.md release gates to be signed off."
read -r -p "Type DEPLOY PRODUCTION to continue: " confirmation
[[ "$confirmation" == "DEPLOY PRODUCTION" ]] || { echo "Cancelled."; exit 0; }
bash -c "$ORBIT_PRODUCTION_DEPLOY_COMMAND"
