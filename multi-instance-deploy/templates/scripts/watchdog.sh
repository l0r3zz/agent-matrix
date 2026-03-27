#!/bin/bash
# watchdog.sh v2.0 -- with auth health checks
# Monitors bot + MCP, validates Matrix auth, detects token mismatch

LOG="/a0/usr/workdir/startup-services.log"
BOT_PIDFILE="/a0/usr/workdir/matrix-bot/bot.pid"
MCP_PIDFILE="/a0/usr/workdir/matrix-mcp-server/mcp.pid"
MCP_DIR="/a0/usr/workdir/matrix-mcp-server"
TOKEN_CHECK="/a0/usr/workdir/check-token-sync.py"
WATCHDOG_INTERVAL=30
HEALTH_CHECK_INTERVAL=300
LAST_HEALTH_CHECK=0

log() {
    echo "$(date '+%F %T') $*" >> "$LOG"
}

is_alive() {
    [ -f "$1" ] && kill -0 "$(cat "$1" 2>/dev/null)" 2>/dev/null
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
    local RESULT
    RESULT=$(curl -sf --max-time 15 -X POST http://localhost:3000/mcp \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list-joined-rooms","arguments":{}}}' 2>/dev/null)
    if echo "$RESULT" | grep -q text; then
        return 0
    else
        log "HEALTH: Tool check FAILED"
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
    pkill -9 -f 'node dist/http-server.js' 2>/dev/null
    sleep 2
    cd "$MCP_DIR" || return
    > mcp-server.log
    node dist/http-server.js >> mcp-server.log 2>&1 &
    echo $! > "$MCP_PIDFILE"
    log "WATCHDOG: mcp-server restarted PID=$!"
    sleep 5
    if mcp_auth_check; then
        log "HEALTH: Auth PASSED after restart"
    else
        log "HEALTH: WARNING -- Auth FAILED after restart"
    fi
}

# Capture initial PIDs
BOT_PID=$(ps -eo pid,cmd | grep -E '[r]un-matrix-bot\.sh|[p]ython.*matrix_bot\.py|[m]atrix-bot-rust' | awk '{print $1}' | head -1)
MCP_PID=$(ps -eo pid,cmd | grep '[n]ode.*http-server' | awk '{print $1}' | head -1)
[ -n "$BOT_PID" ] && echo "$BOT_PID" > "$BOT_PIDFILE"
[ -n "$MCP_PID" ] && echo "$MCP_PID" > "$MCP_PIDFILE"

log "WATCHDOG v2.0: Starting interval=${WATCHDOG_INTERVAL}s health=${HEALTH_CHECK_INTERVAL}s"
log "WATCHDOG: BOT PID=$(cat "$BOT_PIDFILE" 2>/dev/null || echo none)"
log "WATCHDOG: MCP PID=$(cat "$MCP_PIDFILE" 2>/dev/null || echo none)"

token_sync_check
if mcp_auth_check; then
    log "HEALTH: Initial auth PASSED"
else
    log "HEALTH: Initial auth FAILED"
    log "WATCHDOG: token mismatch detected; syncing settings.json MCP header token"
    python3 /a0/usr/workdir/sync-mcp-token-into-settings.py >> "$LOG" 2>&1 || true
    restart_mcp "AUTH_FAILED"
fi

while true; do
    sleep "$WATCHDOG_INTERVAL"
    NOW=$(date +%s)

    if ! is_alive "$BOT_PIDFILE"; then
        log "WATCHDOG: matrix-bot DEAD -- restarting"
        cd /a0/usr/workdir/matrix-bot || continue
        ./run-matrix-bot.sh >> bot.log 2>&1 &
        echo $! > "$BOT_PIDFILE"
        log "WATCHDOG: matrix-bot restarted PID=$!"
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
                log "WATCHDOG: token mismatch detected; syncing settings.json MCP header token"
                python3 /a0/usr/workdir/sync-mcp-token-into-settings.py >> "$LOG" 2>&1 || true
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
