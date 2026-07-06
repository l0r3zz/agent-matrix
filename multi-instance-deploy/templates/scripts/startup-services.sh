#!/bin/bash
# =============================================================================
# startup-services.sh — Golden Template (v3.16)
# =============================================================================
# Persistent auto-start script for Matrix services on Agent Zero containers.
# Launched via docker-compose command: runs in background alongside supervisord.
# Lives on bind mount: /a0/usr/workdir/startup-services.sh
#
# Boot sequence:
#   Phase 0: Apply runtime patches (auth bypass, token sync)
#   Phase 1: Start MCP server (must be up before Agent Zero preload)
#   Phase 2: Wait for Agent Zero API (localhost:80)
#   Phase 3: Install Python dependencies (non-persistent, reinstalled each boot)
#   Phase 4: Start Matrix bot
# =============================================================================

set -euo pipefail

LOG="/a0/usr/workdir/startup-services.log"
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "========== startup-services.sh phases 0-4 complete =========="

# -------------------------------------------------------
# PHASE 0.5: Apply Time Travel plugin patches
# The Time Travel plugin is baked into the Docker image and
# does not survive container recreation. These patches fix:
#   1. GIT_TIMEOUT_SECONDS 20 -> 60 (prevents stale index.lock)
#   2. Add 'target' to EXCLUDED_DIR_NAMES (Rust build artifacts)
# -------------------------------------------------------
TT_PLUGIN="/a0/plugins/_time_travel/helpers/time_travel.py"
if [ -f "$TT_PLUGIN" ]; then
    sed -i 's/GIT_TIMEOUT_SECONDS = 20/GIT_TIMEOUT_SECONDS = 60/' "$TT_PLUGIN" 2>/dev/null || true
    grep -q '"target"' "$TT_PLUGIN" 2>/dev/null || sed -i 's/".parcel-cache",/".parcel-cache",\n    "target",/' "$TT_PLUGIN" 2>/dev/null || true
    log "Phase 0.5: Time Travel plugin patched (timeout=60, target excluded)"
else
    log "Phase 0.5: WARNING — Time Travel plugin not found at $TT_PLUGIN"
fi

# -------------------------------------------------------
# PHASE 5: Start the watchdog as a background process.
# The watchdog monitors bot and MCP server and restarts
# them automatically if they crash. See watchdog.sh for
# the full implementation.
# -------------------------------------------------------
if [ -x /a0/usr/workdir/watchdog.sh ]; then
    nohup /a0/usr/workdir/watchdog.sh >> "$LOG" 2>&1 &
    log "Phase 5: Watchdog launched (pid $!)"
else
    log "Phase 5: WARNING — watchdog.sh not found or not executable"
fi

# -------------------------------------------------------
# PHASE 6: Start the wiki HTTP server (port 8080)
# -------------------------------------------------------
if [ -d /a0/usr/workdir/galadriel-workspace/wiki-site ]; then
    if ! pgrep -f "http.server 8080" > /dev/null 2>&1; then
        nohup python3 -m http.server 8080 --directory /a0/usr/workdir/galadriel-workspace/wiki-site >> "$LOG" 2>&1 &
        log "Phase 6: Wiki server launched (pid $!)"
    else
        log "Phase 6: Wiki server already running"
    fi
else
    log "Phase 6: WARNING — wiki-site directory not found"
fi
