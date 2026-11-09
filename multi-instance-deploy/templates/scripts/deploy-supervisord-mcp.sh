#!/bin/bash
# Deploy supervisord-managed MCP + Bot programs to an agent container.
# Replaces the fragile watchdog.sh pattern with robust supervisord management.
#
# Usage:
#   ./deploy-supervisord-mcp.sh agent0-2
#   ./deploy-supervisord-mcp.sh agent0-3 --verbose
#
# What this script does:
#   1. Creates run-mcp-wrapper.sh and run-bot-wrapper.sh inside the container
#   2. Adds [program:run_mcp] and [program:run_bot] to supervisord.conf
#   3. Disables watchdog.sh in startup-services.sh
#   4. Kills watchdog and stale bot/MCP processes
#   5. Reloads supervisord. run_mcp stays up. run_bot stays stopped.
#
# Author: Galadriel/agent0-2
# Created: 2026-07-06

set -euo pipefail

AGENT="${1:?Usage: $0 <agent-name> [--verbose]}"
VERBOSE="${2:-}"

if ! docker ps --format '{{.Names}}' | grep -q "^${AGENT}$"; then
    echo "ERROR: Container ${AGENT} not found or not running"
    exit 1
fi

echo "Deploying supervisord MCP+Bot management to ${AGENT}..."

# 1. Create wrapper scripts
echo "[1/5] Creating wrapper scripts..."
docker exec "$AGENT" bash -c '
    # MCP wrapper
    cat > /a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh << '\''MCP_EOF'\''
#!/bin/bash
cd /a0/usr/workdir/matrix-mcp-server
source .env
exec ./matrix-mcp-server-r2
MCP_EOF
    chmod +x /a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh

    # Bot wrapper
    cat > /a0/usr/workdir/matrix-bot/run-bot-wrapper.sh << '\''BOT_EOF'\''
#!/bin/bash
cd /a0/usr/workdir/matrix-bot
source .env
exec ./matrix-bot-rust
BOT_EOF
    chmod +x /a0/usr/workdir/matrix-bot/run-bot-wrapper.sh

    echo "  Wrappers created"
'

# 2. Check if programs already exist in supervisord.conf
echo "[2/5] Patching supervisord.conf..."
ALREADY_HAS=$(docker exec "$AGENT" grep -c 'program:run_mcp' /etc/supervisor/conf.d/supervisord.conf 2>/dev/null || echo 0)

if [ "$ALREADY_HAS" -gt 0 ]; then
    echo "  supervisord.conf already has run_mcp; correcting run_bot only"
else
    docker exec "$AGENT" bash -c '
        cat >> /etc/supervisor/conf.d/supervisord.conf << '\''SUP_EOF'\''

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
stopasgroup=true
killasgroup=true

[program:run_bot]
command=/a0/usr/workdir/matrix-bot/run-bot-wrapper.sh
environment=
user=root
stopwaitsecs=10
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
autostart=false
autorestart=false
startretries=10
stopasgroup=true
killasgroup=true
SUP_EOF
        echo "  supervisord.conf patched"
    '
fi

docker exec "$AGENT" python3 - /etc/supervisor/conf.d/supervisord.conf << 'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text().splitlines(keepends=True)
out = []
in_bot = False
seen_auto = False
seen_restart = False

def close_bot():
    if not seen_auto:
        out.append("autostart=false\n")
    if not seen_restart:
        out.append("autorestart=false\n")

for line in lines:
    if line.startswith("["):
        if in_bot:
            close_bot()
        in_bot = line.strip() == "[program:run_bot]"
        seen_auto = False
        seen_restart = False
        out.append(line if line.endswith("\n") else line + "\n")
        continue
    if in_bot and line.startswith("autostart="):
        out.append("autostart=false\n")
        seen_auto = True
        continue
    if in_bot and line.startswith("autorestart="):
        out.append("autorestart=false\n")
        seen_restart = True
        continue
    out.append(line if line.endswith("\n") else line + "\n")
if in_bot:
    close_bot()
path.write_text("".join(out))
PY

# 3. Disable watchdog in startup-services.sh
echo "[3/5] Disabling watchdog in startup-services.sh..."
docker exec "$AGENT" bash -c '
    STARTUP=/a0/usr/workdir/startup-services.sh
    if grep -q "nohup /a0/usr/workdir/watchdog.sh" "$STARTUP" 2>/dev/null; then
        sed -i "s|^\(.*nohup /a0/usr/workdir/watchdog.sh.*\)|# DISABLED: supervisord now manages MCP/bot\n# \1|" "$STARTUP"
        echo "  Watchdog disabled in startup-services.sh"
    else
        echo "  Watchdog already disabled or not found"
    fi
'

# 4. Kill watchdog and stale processes
echo "[4/5] Killing watchdog and stale processes..."
docker exec "$AGENT" bash -c '
    pkill -f watchdog.sh 2>/dev/null || true
    supervisorctl stop run_bot 2>/dev/null || true
    echo "  run_bot stopped; run_mcp was left running"
'

# 5. Reload supervisord
echo "[5/5] Reloading supervisord..."
docker exec "$AGENT" bash -c '
    supervisorctl reread 2>&1
    supervisorctl update 2>&1
    supervisorctl stop run_bot 2>/dev/null || true
    sleep 2
    supervisorctl status 2>&1
'

echo ""
echo "Done. ${AGENT} runs run_mcp. run_bot stays stopped."
