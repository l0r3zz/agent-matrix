#!/bin/bash
# Phase 5: Watchdog — monitor and restart crashed services
# Standalone script to avoid inline escaping issues.
# Deployed to /a0/usr/workdir/watchdog.sh inside containers.

LOG="/a0/usr/workdir/startup-services.log"
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

BOT_PIDFILE="/a0/usr/workdir/matrix-bot/bot.pid"
MCP_PIDFILE="/a0/usr/workdir/matrix-mcp-server/mcp.pid"
WATCHDOG_INTERVAL=30

is_alive() {
    [ -f "$1" ] && kill -0 "$(cat "$1" 2>/dev/null)" 2>/dev/null
}

# Capture initial PIDs on first run
BOT_PID=$(ps -eo pid,cmd | grep '[p]ython.*matrix_bot' | awk '{print $1}' | head -1)
MCP_PID=$(ps -eo pid,cmd | grep '[n]ode.*http-server' | awk '{print $1}' | head -1)
[ -n "$BOT_PID" ] && echo "$BOT_PID" > "$BOT_PIDFILE"
[ -n "$MCP_PID" ] && echo "$MCP_PID" > "$MCP_PIDFILE"

log "WATCHDOG: Starting (PID-file edition, interval=${WATCHDOG_INTERVAL}s)"
log "WATCHDOG:   BOT PID=$(cat "$BOT_PIDFILE" 2>/dev/null || echo none)"
log "WATCHDOG:   MCP PID=$(cat "$MCP_PIDFILE" 2>/dev/null || echo none)"

while true; do
    sleep "$WATCHDOG_INTERVAL"

    # Check Matrix bot
    if ! is_alive "$BOT_PIDFILE"; then
        log "WATCHDOG: matrix-bot DEAD — restarting..."
        cd /a0/usr/workdir/matrix-bot
        /opt/venv-a0/bin/python matrix_bot.py >> bot.log 2>&1 &
        echo $! > "$BOT_PIDFILE"
        log "WATCHDOG: matrix-bot restarted (pid $!)"
    fi

    # Check MCP server
    if ! is_alive "$MCP_PIDFILE"; then
        log "WATCHDOG: mcp-server DEAD — restarting..."
        cd /a0/usr/workdir/matrix-mcp-server
        node dist/http-server.js >> mcp-server.log 2>&1 &
        echo $! > "$MCP_PIDFILE"
        log "WATCHDOG: mcp-server restarted (pid $!)"
    fi
done
