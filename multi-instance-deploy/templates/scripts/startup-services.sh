#!/usr/bin/env bash
# =============================================================================
# startup-services.sh — Golden Template (v3.20 — Phase 8 Inside-Container Hardening)
# =============================================================================
# Persistent auto-start script for Matrix services on Agent Zero containers.
# Launched via docker-compose command: runs in background alongside supervisord.
# Lives on bind mount: /a0/usr/workdir/startup-services.sh
#
# Boot sequence:
#   Phase 0.5: Apply Time Travel plugin patches
#   Phase 5: Ensure supervisord-managed MCP + bot (with preflight gate)
#   Phase 5.5: Launch Watchdog v3.0 (platform-integrated health reporter)
#   Phase 6: Start wiki HTTP server (port 8080)
# =============================================================================

set -euo pipefail

LOG="/a0/usr/workdir/startup-services.log"
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "========== startup-services.sh v3.20 starting =========="

# -------------------------------------------------------
# PHASE 0.5: Apply Time Travel plugin patches
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
# PHASE 5: Ensure supervisord-managed MCP + bot services.
# Only write wrapper scripts if missing so deployed Phase 3/8
# wrappers are never overwritten on container restart.
# -------------------------------------------------------
MCP_WRAPPER="/a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh"
if [ -d /a0/usr/workdir/matrix-mcp-server ] && [ ! -f "$MCP_WRAPPER" ]; then
    cat > "$MCP_WRAPPER" << 'MCPW'
#!/bin/bash
cd /a0/usr/workdir/matrix-mcp-server
source .env
exec ./matrix-mcp-server-r2
MCPW
    chmod +x "$MCP_WRAPPER"
    log "Phase 5: Default MCP wrapper script installed"
fi

BOT_WRAPPER="/a0/usr/workdir/matrix-bot/run-bot-wrapper.sh"
if [ -d /a0/usr/workdir/matrix-bot ] && [ ! -f "$BOT_WRAPPER" ]; then
    cat > "$BOT_WRAPPER" << 'BOTW'
#!/usr/bin/env bash
set -euo pipefail

cd /a0/usr/workdir/matrix-bot

if [[ -x /a0/usr/workdir/derive-a0-token.sh ]]; then
    FP="$(/a0/usr/workdir/derive-a0-token.sh --output /a0/usr/workdir/matrix-bot/.a0-api-key)"
    echo "[run-bot-wrapper] Derived canonical A0 credential (fingerprint=${FP})"
elif [[ ! -s /a0/usr/workdir/matrix-bot/.a0-api-key ]]; then
    echo "[run-bot-wrapper] ERROR: derive-a0-token.sh missing and no .a0-api-key present; failing closed" >&2
    exit 1
fi

if [[ -x /a0/usr/workdir/preflight-check.sh ]]; then
    if [[ "${SKIP_PREFLIGHT:-0}" == "1" ]]; then
        /a0/usr/workdir/preflight-check.sh --skip-preflight
    else
        /a0/usr/workdir/preflight-check.sh
    fi
fi

set -a
source .env
set +a
unset A0_API_KEY

exec ./matrix-bot-rust
BOTW
    chmod +x "$BOT_WRAPPER"
    log "Phase 5: Default Phase 8 bot wrapper script installed"
fi

# Append supervisord config for MCP and bot (if not already present)
SUPERVISORD_CONF="/etc/supervisor/conf.d/supervisord.conf"
if [ -f "$SUPERVISORD_CONF" ] && ! grep -q "\[program:run_mcp\]" "$SUPERVISORD_CONF"; then
    cat >> "$SUPERVISORD_CONF" << 'SUPEREOF'

# Matrix MCP server — managed by supervisord
[program:run_mcp]
command=/a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh
environment=
user=root
stopwaitsecs=10
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
startretries=10
exitcodes=0,2,241

# Matrix bot — managed by supervisord
[program:run_bot]
command=/a0/usr/workdir/matrix-bot/run-bot-wrapper.sh
environment=
user=root
stopwaitsecs=10
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autorestart=true
startretries=10
exitcodes=0,2,241
SUPEREOF
    log "Phase 5: Supervisord config updated for run_mcp + run_bot"
    supervisorctl reread 2>/dev/null || true
    supervisorctl update 2>/dev/null || true
else
    log "Phase 5: Supervisord config already has run_mcp (skipping)"
fi

rm -f /a0/usr/workdir/matrix-mcp-server/mcp.pid 2>/dev/null || true
rm -f /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null || true
rm -f /a0/usr/workdir/watchdog.lock 2>/dev/null || true

# -------------------------------------------------------
# PHASE 5.5: Launch Watchdog v3.0 (Platform Health Reporter)
# -------------------------------------------------------
if [ -x /a0/usr/workdir/watchdog.sh ]; then
    if ! pgrep -f "/a0/usr/workdir/watchdog.sh" > /dev/null 2>&1; then
        nohup /a0/usr/workdir/watchdog.sh >> "$LOG" 2>&1 &
        log "Phase 5.5: Watchdog v3.0 launched (pid $!)"
    else
        log "Phase 5.5: Watchdog v3.0 already running"
    fi
fi

log "Phase 5: MCP + bot services under supervisord management"

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

log "========== startup-services.sh complete =========="
