#!/bin/bash
# =============================================================================
# Deploy supervisord-managed MCP + bot to fleet agents
# Replaces watchdog.sh on agents that don't have it yet
# =============================================================================
set -uo pipefail

if [[ $# -ge 1 ]]; then
    AGENTS=("$@")
else
    AGENTS=(1 2 3 4 5)
fi

for i in "${AGENTS[@]}"; do
    echo "=== agent0-$i ==="
    
    # Install MCP wrapper
    docker exec agent0-$i bash -c 'cat > /a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh << "MCPW"
#!/bin/bash
cd /a0/usr/workdir/matrix-mcp-server
source .env
exec ./matrix-mcp-server-r2
MCPW
chmod +x /a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh' 2>&1
    echo "  MCP wrapper installed"
    
    # Install bot wrapper
    docker exec agent0-$i bash -c 'cat > /a0/usr/workdir/matrix-bot/run-bot-wrapper.sh << "BOTW"
#!/bin/bash
cd /a0/usr/workdir/matrix-bot
source .env
exec ./matrix-bot-rust
BOTW
chmod +x /a0/usr/workdir/matrix-bot/run-bot-wrapper.sh' 2>&1
    echo "  Bot wrapper installed"
    
    # Append supervisord config if not present
    docker exec agent0-$i bash -c 'if ! grep -q "\[program:run_mcp\]" /etc/supervisor/conf.d/supervisord.conf; then cat >> /etc/supervisor/conf.d/supervisord.conf << "SUPEREOF"

# Matrix MCP server -- managed by supervisord (replaces watchdog.sh)
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

# Matrix bot -- managed by supervisord (replaces watchdog.sh)
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
echo "  Supervisord config added"
else
echo "  Supervisord config already present"
fi' 2>&1
    
    # Kill watchdog
    docker exec agent0-$i bash -c 'pkill -f watchdog.sh 2>/dev/null || true' 2>&1
    echo "  Watchdog killed"
    
    # Remove stale PID files
    docker exec agent0-$i bash -c 'rm -f /a0/usr/workdir/matrix-mcp-server/mcp.pid /a0/usr/workdir/matrix-bot/bot.pid /a0/usr/workdir/watchdog.lock 2>/dev/null || true' 2>&1
    
    # Kill orphaned bot/mcp processes (not under supervisord)
    docker exec agent0-$i bash -c '
SUP_PIDS=$(supervisorctl status 2>/dev/null | grep -oP "pid \K[0-9]+" || echo "")
for pid in $(pgrep -f matrix-bot-rust 2>/dev/null); do
    if echo "$SUP_PIDS" | grep -qw "$pid" 2>/dev/null; then
        echo "  Bot PID $pid is supervisord-managed (keeping)"
    else
        kill $pid 2>/dev/null || true
        echo "  Killed orphaned bot PID $pid"
    fi
done
for pid in $(pgrep -f matrix-mcp-server-r2 2>/dev/null); do
    if echo "$SUP_PIDS" | grep -qw "$pid" 2>/dev/null; then
        echo "  MCP PID $pid is supervisord-managed (keeping)"
    else
        kill $pid 2>/dev/null || true
        echo "  Killed orphaned MCP PID $pid"
    fi
done
' 2>&1
    
    # Reload supervisord and start services
    docker exec agent0-$i bash -c 'supervisorctl reread 2>/dev/null; supervisorctl update 2>/dev/null; sleep 1; supervisorctl start run_mcp run_bot 2>/dev/null || true' 2>&1
    echo "  Services started"
    
    # Wait and check status
    sleep 3
    docker exec agent0-$i supervisorctl status run_mcp run_bot 2>&1
    echo
done

echo "=== FLEET DEPLOYMENT COMPLETE ==="
