#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
: "${ORBIT_STAGING_DEPLOY_COMMAND:?Set ORBIT_STAGING_DEPLOY_COMMAND to your reviewed cloud deploy command.}"
echo "Deploying the reviewed image to staging."
bash -c "$ORBIT_STAGING_DEPLOY_COMMAND"
