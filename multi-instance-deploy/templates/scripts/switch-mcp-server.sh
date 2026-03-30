#!/bin/bash
# =============================================================================
# switch-mcp-server.sh -- Toggle between TypeScript and Rust MCP server
# =============================================================================
# Run inside the agent-zero container:
#   /a0/usr/workdir/switch-mcp-server.sh rust    # switch to Rust
#   /a0/usr/workdir/switch-mcp-server.sh ts      # switch back to TypeScript
#   /a0/usr/workdir/switch-mcp-server.sh status   # show which is running
#
# Prerequisites:
#   - The Rust binary must be at /a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2
#   - The TS server must be built at /a0/usr/workdir/matrix-mcp-server/dist/http-server.js
#
# The script:
#   1. Kills whichever MCP server is currently running
#   2. Starts the requested variant
#   3. Updates the PID file so the watchdog tracks the correct process
#   4. Verifies the /health endpoint responds
# =============================================================================

set -euo pipefail

MCP_DIR="/a0/usr/workdir/matrix-mcp-server"
MCP_PIDFILE="${MCP_DIR}/mcp.pid"
MCP_LOG="${MCP_DIR}/mcp-server.log"
RUST_BIN="${MCP_DIR}/matrix-mcp-server-r2"
TS_ENTRY="${MCP_DIR}/dist/http-server.js"
MARKER_FILE="${MCP_DIR}/.mcp-variant"
HEALTH_URL="http://localhost:3000/health"

log() {
    echo "$(date '+%F %T') SWITCH: $*" | tee -a "$MCP_LOG"
}

current_variant() {
    if [ -f "$MARKER_FILE" ]; then
        cat "$MARKER_FILE"
    elif pgrep -f "matrix-mcp-server-r2" >/dev/null 2>&1; then
        echo "rust"
    elif pgrep -f "node.*http-server" >/dev/null 2>&1; then
        echo "ts"
    else
        echo "none"
    fi
}

kill_mcp() {
    log "Stopping current MCP server..."
    pkill -9 -f 'matrix-mcp-server-r2' 2>/dev/null || true
    pkill -9 -f 'node.*http-server' 2>/dev/null || true
    sleep 2
    rm -f "$MCP_PIDFILE"
}

start_rust() {
    if [ ! -x "$RUST_BIN" ]; then
        echo "ERROR: Rust binary not found at $RUST_BIN"
        echo "Build it first:"
        echo "  docker build -t matrix-mcp-server-r2 /path/to/matrix-mcp-server-r2-repo"
        echo "  docker create --name mcp-build matrix-mcp-server-r2"
        echo "  docker cp mcp-build:/usr/local/bin/matrix-mcp-server-r2 ${RUST_BIN}"
        echo "  docker rm mcp-build"
        exit 1
    fi

    log "Starting Rust MCP server..."
    cd "$MCP_DIR"
    "$RUST_BIN" >> "$MCP_LOG" 2>&1 &
    local PID=$!
    echo "$PID" > "$MCP_PIDFILE"
    echo "rust" > "$MARKER_FILE"
    log "Rust MCP server started (PID=$PID)"
}

start_ts() {
    if [ ! -f "$TS_ENTRY" ]; then
        echo "ERROR: TypeScript server not found at $TS_ENTRY"
        echo "Run 'npm install && npm run build' in $MCP_DIR first."
        exit 1
    fi

    log "Starting TypeScript MCP server..."
    cd "$MCP_DIR"
    node dist/http-server.js >> "$MCP_LOG" 2>&1 &
    local PID=$!
    echo "$PID" > "$MCP_PIDFILE"
    echo "ts" > "$MARKER_FILE"
    log "TypeScript MCP server started (PID=$PID)"
}

wait_healthy() {
    local TRIES=0
    while [ $TRIES -lt 15 ]; do
        if curl -sf --max-time 3 "$HEALTH_URL" >/dev/null 2>&1; then
            log "Health check PASSED"
            return 0
        fi
        TRIES=$((TRIES + 1))
        sleep 2
    done
    log "WARNING: Health check did not pass after 30 seconds"
    return 1
}

show_status() {
    local VARIANT
    VARIANT=$(current_variant)
    case "$VARIANT" in
        rust)
            local PID
            PID=$(pgrep -f 'matrix-mcp-server-r2' 2>/dev/null | head -1)
            echo "MCP server: RUST (PID=${PID:-unknown})"
            ;;
        ts)
            local PID
            PID=$(pgrep -f 'node.*http-server' 2>/dev/null | head -1)
            echo "MCP server: TypeScript (PID=${PID:-unknown})"
            ;;
        *)
            echo "MCP server: NOT RUNNING"
            ;;
    esac
    if curl -sf --max-time 3 "$HEALTH_URL" >/dev/null 2>&1; then
        echo "Health: OK"
        curl -sf "$HEALTH_URL" 2>/dev/null | python3 -m json.tool 2>/dev/null || true
    else
        echo "Health: UNREACHABLE"
    fi
}

# ---- Main ----

case "${1:-status}" in
    rust|r2)
        CURRENT=$(current_variant)
        if [ "$CURRENT" = "rust" ]; then
            echo "Already running Rust MCP server"
            show_status
            exit 0
        fi
        kill_mcp
        start_rust
        wait_healthy
        show_status
        ;;
    ts|typescript|node)
        CURRENT=$(current_variant)
        if [ "$CURRENT" = "ts" ]; then
            echo "Already running TypeScript MCP server"
            show_status
            exit 0
        fi
        kill_mcp
        start_ts
        wait_healthy
        show_status
        ;;
    status|s)
        show_status
        ;;
    *)
        echo "Usage: $0 {rust|ts|status}"
        echo ""
        echo "  rust   - Switch to Rust MCP server (matrix-mcp-server-r2)"
        echo "  ts     - Switch to TypeScript MCP server (node http-server.js)"
        echo "  status - Show which variant is running"
        exit 1
        ;;
esac
