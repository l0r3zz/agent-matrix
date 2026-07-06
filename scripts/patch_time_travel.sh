#!/bin/bash
# Time Travel Plugin Patch Script
# Fixes:
# 1. Increases GIT_TIMEOUT_SECONDS from 20 to 60 (prevents stale index.lock on large workdirs)
# 2. Adds "target" to EXCLUDED_DIR_NAMES (excludes Rust build artifacts from snapshots)
#
# Usage: bash patch_time_travel.sh [container_name]
# If container_name is provided, patches inside that container via docker exec
# If no container_name, patches locally

set -e

CONTAINER="${1:-}"
PLUGIN_PATH="/a0/plugins/_time_travel/helpers/time_travel.py"

patch_cmd() {
    if [ -n "$CONTAINER" ]; then
        docker exec "$CONTAINER" bash -c "$1"
    else
        bash -c "$1"
    fi
}

echo "Patching Time Travel plugin${CONTAINER:+ in container $CONTAINER}..."

# Patch 1: Increase timeout from 20 to 60 seconds
patch_cmd "sed -i 's/GIT_TIMEOUT_SECONDS = 20/GIT_TIMEOUT_SECONDS = 60/' $PLUGIN_PATH"
echo "  [1/2] GIT_TIMEOUT_SECONDS = 60"

# Patch 2: Add 'target' to excluded directories (Rust build output)
patch_cmd "grep -q '\"target\"' $PLUGIN_PATH || sed -i 's/\".parcel-cache\",/\".parcel-cache\",\n    \"target\",/' $PLUGIN_PATH"
echo "  [2/2] Added 'target' to EXCLUDED_DIR_NAMES"

# Verify
patch_cmd "grep -n 'GIT_TIMEOUT_SECONDS' $PLUGIN_PATH | head -1"
patch_cmd "grep -n '\"target\"' $PLUGIN_PATH | head -1"

echo "Done."
