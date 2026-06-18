#!/bin/bash
# watchdog.sh v2.1 -- with auth health checks + duplicate-instance guards
# Monitors bot + MCP, validates Matrix auth, detects token mismatch
#
# v2.1 changes (duplicate-instance hardening):
#   - Singleton guard: only ONE watchdog may run per container (flock).
#   - restart_bot(): pkill stale matrix-bot processes BEFORE launching a new one
#     (mirrors restart_mcp), and records the ACTUAL bot binary PID. Prevents
#     zombie/duplicate matrix-bot-rust accumulation.

LOG="/a0/usr/workdir/startup-services.log"
BOT_PIDFILE="/a0/usr/workdir/matrix-bot/bot.pid"
MCP_PIDFILE="/a0/usr/workdir/matrix-mcp-server/mcp.pid"
MCP_DIR="/a0/usr/workdir/matrix-mcp-server"
BOT_DIR="/a0/usr/workdir/matrix-bot"
TOKEN_CHECK="/a0/usr/workdir/check-token-sync.py"
WATCHDOG_INTERVAL=30
HEALTH_CHECK_INTERVAL=300
LAST_HEALTH_CHECK=0
LOCKFILE="/a0/usr/workdir/watchdog.lock"

log() {
    echo "$(date '+%F %T') $*" >> "$LOG"
}

# --- Singleton guard: prevent multiple concurrent watchdog instances ---
# Two watchdogs each respawning the bot is the root cause of duplicate bots.
exec 9>"$LOCKFILE"
if ! flock -n 9; then
    log "WATCHDOG: another instance already holds $LOCKFILE -- exiting to avoid duplicate respawns"
    exit 0
fi

is_alive() {
    [ -f "$1" ] && kill -0 "$(cat "$1" 2>/dev/null)" 2>/dev/null
}

mcp_variant() {
    local marker="${MCP_DIR}/.mcp-variant"
    if [ -f "$marker" ]; then
        cat "$marker" | tr -d '\n'
    else
        echo "ts"
    fi
}

start_mcp_variant() {
    local variant
    variant=$(mcp_variant)
    cd "$MCP_DIR" || return
    > mcp-server.log
    case "$variant" in
        rust|r2)
            if [ -x "${MCP_DIR}/matrix-mcp-server-r2" ]; then
                log "WATCHDOG: Starting Rust MCP server (variant=rust)"
                "${MCP_DIR}/matrix-mcp-server-r2" >> mcp-server.log 2>&1 &
                echo $! > "$MCP_PIDFILE"
                log "WATCHDOG: Rust MCP PID=$!"
            else
                log "WATCHDOG: ERROR - Rust binary not found, falling back to TS"
                node dist/http-server.js >> mcp-server.log 2>&1 &
                echo $! > "$MCP_PIDFILE"
                log "WATCHDOG: TS MCP PID=$! (fallback)"
            fi
            ;;
        ts|typescript)
            log "WATCHDOG: Starting TypeScript MCP server (variant=ts)"
            node dist/http-server.js >> mcp-server.log 2>&1 &
            echo $! > "$MCP_PIDFILE"
            log "WATCHDOG: TS MCP PID=$!"
            ;;
        *)
            log "WATCHDOG: Unknown MCP variant '$variant', defaulting to TS"
            node dist/http-server.js >> mcp-server.log 2>&1 &
            echo $! > "$MCP_PIDFILE"
            log "WATCHDOG: TS MCP PID=$! (default)"
            ;;
    esac
}

mcp_auth_check() {
    local MCP_ENV="${MCP_DIR}/.env"
    [ ! -f "$MCP_ENV" ] && { log "HEALTH: .env not found"; return 1; }
    local HS_URL TOKEN RESULT
    HS_URL=$(grep '^MATRIX_HOMESERVER_URL=' "$MCP_ENV" | cut -d= -f2- | tr -d '"')
    TOKEN=$(grep '^MATRIX_ACCESS_TOKEN=' "$MCP_ENV" | cut -d= -f2- | tr -d '"')
    [ -z "$HS_URL" ] || [ -z "$TOKEN" ] && { log "HEALTH: Missing creds"; return 1; }
    RESULT=$(curl -sf --max-time 10 -H "Authorization: Bearer $TOKEN" "$HS_URL/_matrix/client/v3/account/whoami" 2>/dev/null)
    if echo "$RESULT" | grep -q user_id; then
        return 0
    else
        log "HEALTH: Auth FAILED -- $RESULT"
        return 1
    fi
}

mcp_tool_check() {
    # v2.1: Use /health endpoint instead of JSON-RPC tool call.
    local RESULT
    RESULT=$(curl -sf --max-time 10 http://localhost:3000/health 2>/dev/null)
    if echo "$RESULT" | grep -q healthy; then
        return 0
    else
        log "HEALTH: Tool check FAILED (health endpoint)"
        return 1
    fi
}

token_sync_check() {
    [ ! -f "$TOKEN_CHECK" ] && return 0
    local SYNC_RESULT
    SYNC_RESULT=$(python3 "$TOKEN_CHECK" 2>/dev/null)
    case "$SYNC_RESULT" in
        MATCH|SKIP) return 0 ;;
        MISMATCH*)
            log "HEALTH: TOKEN $SYNC_RESULT"
            log "HEALTH: TOKEN-GUARD handles this at runtime."
            return 1 ;;
        *) return 0 ;;
    esac
}

restart_mcp() {
    log "WATCHDOG: mcp-server $1 -- restarting"
    local variant=$(mcp_variant)
    log "WATCHDOG: MCP variant=$variant"
    pkill -9 -f 'node dist/http-server.js' 2>/dev/null
    pkill -9 -f 'matrix-mcp-server-r2' 2>/dev/null
    sleep 2
    start_mcp_variant
    sleep 5
    if mcp_auth_check; then
        log "HEALTH: Auth PASSED after restart"
    else
        log "HEALTH: WARNING -- Auth FAILED after restart"
    fi
}

# --- Bot restart with duplicate guard (mirrors restart_mcp) ---
# Always kill ALL stale matrix-bot processes before starting a fresh one,
# then record the actual bot binary PID (not the launcher wrapper PID).
restart_bot() {
    log "WATCHDOG: matrix-bot $1 -- killing stale instances before restart"
    pkill -9 -f 'matrix-bot-rust' 2>/dev/null
    pkill -9 -f 'python.*matrix_bot' 2>/dev/null
    sleep 2
    cd "$BOT_DIR" || return
    if [ -x "${BOT_DIR}/run-matrix-bot.sh" ]; then
        setsid ./matrix-bot-rust </dev/null >> bot.log 2>&1 &
    else
        setsid ./matrix-bot-rust </dev/null >> bot.log 2>&1 &
    fi
    sleep 3
    # Record the ACTUAL bot binary PID, not the launcher wrapper.
    local real_pid
    real_pid=$(pgrep -f 'matrix-bot-rust' | head -1)
    [ -z "$real_pid" ] && real_pid=$(pgrep -f 'python.*matrix_bot' | head -1)
    if [ -n "$real_pid" ]; then
        echo "$real_pid" > "$BOT_PIDFILE"
        log "WATCHDOG: matrix-bot restarted PID=$real_pid (count=$(pgrep -fc 'matrix-bot-rust' 2>/dev/null || echo 0))"
    else
        log "WATCHDOG: WARNING -- matrix-bot did not come up after restart"
    fi
}

# Capture initial PIDs (real binary PID, not wrapper)
BOT_PID=$(pgrep -f 'matrix-bot-rust' | head -1)
[ -z "$BOT_PID" ] && BOT_PID=$(ps -eo pid,cmd | grep -E '[p]ython.*matrix_bot' | awk '{print $1}' | head -1)
MCP_PID=$(ps -eo pid,cmd | grep -E '[n]ode.*http-server|[m]atrix-mcp-server-r2' | awk '{print $1}' | head -1)
[ -n "$BOT_PID" ] && echo "$BOT_PID" > "$BOT_PIDFILE"
[ -n "$MCP_PID" ] && echo "$MCP_PID" > "$MCP_PIDFILE"

# Startup hygiene: if more than one bot binary is already running, collapse to one.
BOT_COUNT=$(pgrep -fc 'matrix-bot-rust' 2>/dev/null || echo 0)
if [ "$BOT_COUNT" -gt 1 ]; then
    log "WATCHDOG: detected $BOT_COUNT bot instances at startup -- collapsing to one"
    restart_bot "STARTUP_DUPLICATE"
fi

log "WATCHDOG v2.1: Starting interval=${WATCHDOG_INTERVAL}s health=${HEALTH_CHECK_INTERVAL}s"
log "WATCHDOG: BOT PID=$(cat "$BOT_PIDFILE" 2>/dev/null || echo none)"
log "WATCHDOG: MCP PID=$(cat "$MCP_PIDFILE" 2>/dev/null || echo none)"

if ! token_sync_check; then
    log "WATCHDOG: token mismatch detected; syncing settings.json MCP header token"
    /a0/usr/workdir/sync-mcp-token-into-settings.py >> "$LOG" 2>&1 || true
fi
token_sync_check
if mcp_auth_check; then
    log "HEALTH: Initial auth PASSED"
else
    log "HEALTH: Initial auth FAILED"
    restart_mcp "AUTH_FAILED"
fi

while true; do
    sleep "$WATCHDOG_INTERVAL"
    NOW=$(date +%s)

    if ! is_alive "$BOT_PIDFILE"; then
        restart_bot "DEAD"
    else
        # Guard against duplicates even when the tracked PID is alive.
        BOT_COUNT=$(pgrep -fc 'matrix-bot-rust' 2>/dev/null || echo 0)
        if [ "$BOT_COUNT" -gt 1 ]; then
            log "WATCHDOG: $BOT_COUNT bot instances detected -- collapsing to one"
            restart_bot "DUPLICATE"
        fi
    fi

    if ! is_alive "$MCP_PIDFILE"; then
        restart_mcp "DEAD"
    fi

    if [ $((NOW - LAST_HEALTH_CHECK)) -ge $HEALTH_CHECK_INTERVAL ]; then
        LAST_HEALTH_CHECK=$NOW
        if is_alive "$MCP_PIDFILE"; then
            token_sync_check
            if ! mcp_auth_check; then
                log "HEALTH: Periodic auth FAILED"
                restart_mcp "AUTH_FAILED"
            elif ! mcp_tool_check; then
                log "HEALTH: Periodic tool FAILED"
                restart_mcp "TOOL_FAILED"
            else
                log "HEALTH: Periodic check PASSED"
            fi
        fi
    fi
done
