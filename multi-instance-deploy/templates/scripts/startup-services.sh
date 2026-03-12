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
