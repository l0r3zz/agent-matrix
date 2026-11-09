#!/usr/bin/env python3
"""Deploy supervisord-managed MCP + Bot programs to an agent container.
Replaces the fragile watchdog.sh pattern with robust supervisord management.

Usage:
    python3 deploy-supervisord-mcp.py agent0-2
    python3 deploy-supervisord-mcp.py agent0-3 --verbose

Author: Galadriel/agent0-2
Created: 2026-07-06
"""
import subprocess
import sys
import time

AGENT = sys.argv[1] if len(sys.argv) > 1 else None
VERBOSE = '--verbose' in sys.argv

if not AGENT:
    print('Usage: python3 deploy-supervisord-mcp.py <agent-name> [--verbose]')
    sys.exit(1)

# Check container is running
result = subprocess.run(
    ['docker', 'ps', '--format', '{{.Names}}'],
    capture_output=True, text=True
)
if AGENT not in result.stdout.strip().split('\n'):
    print(f'ERROR: Container {AGENT} not found or not running')
    sys.exit(1)

print(f'Deploying supervisord MCP+Bot management to {AGENT}...')

# ── Step 1: Create wrapper scripts ──
print('[1/5] Creating wrapper scripts...')
mcp_wrapper = """#!/bin/bash
cd /a0/usr/workdir/matrix-mcp-server
source .env
exec ./matrix-mcp-server-r2
"""
bot_wrapper = """#!/bin/bash
cd /a0/usr/workdir/matrix-bot
source .env
exec ./matrix-bot-rust
"""

# Write MCP wrapper
subprocess.run(['docker', 'exec', AGENT, 'bash', '-c',
    f"cat > /a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh << 'EOF'\n{mcp_wrapper}EOF\nchmod +x /a0/usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh"
], check=True)

# Write Bot wrapper
subprocess.run(['docker', 'exec', AGENT, 'bash', '-c',
    f"cat > /a0/usr/workdir/matrix-bot/run-bot-wrapper.sh << 'EOF'\n{bot_wrapper}EOF\nchmod +x /a0/usr/workdir/matrix-bot/run-bot-wrapper.sh"
], check=True)
print('  Wrappers created')

# ── Step 2: Patch supervisord.conf ──
print('[2/5] Patching supervisord.conf...')
result = subprocess.run(
    ['docker', 'exec', AGENT, 'grep', '-c', 'program:run_mcp',
     '/etc/supervisor/conf.d/supervisord.conf'],
    capture_output=True, text=True
)
already_has = int(result.stdout.strip()) if result.returncode == 0 else 0

if already_has > 0:
    print('  supervisord.conf already has run_mcp; correcting run_bot only')
else:
    supervisord_block = """
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
"""
    subprocess.run(['docker', 'exec', AGENT, 'bash', '-c',
        f"cat >> /etc/supervisor/conf.d/supervisord.conf << 'EOF'\n{supervisord_block}EOF"
    ], check=True)
    print('  supervisord.conf patched')

patcher = r'''
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
'''
subprocess.run(
    ['docker', 'exec', '-i', AGENT, 'python3', '-', '/etc/supervisor/conf.d/supervisord.conf'],
    input=patcher, text=True, check=True,
)

# ── Step 3: Disable watchdog in startup-services.sh ──
print('[3/5] Disabling watchdog in startup-services.sh...')
subprocess.run(['docker', 'exec', AGENT, 'bash', '-c',
    'STARTUP=/a0/usr/workdir/startup-services.sh; '
    'if grep -q "nohup /a0/usr/workdir/watchdog.sh" "$STARTUP" 2>/dev/null; then '
    'sed -i "s|^\\(.*nohup /a0/usr/workdir/watchdog.sh.*\\)|# DISABLED: supervisord now manages MCP/bot\\n# \\1|" "$STARTUP"; '
    'echo "  Watchdog disabled in startup-services.sh"; '
    'else echo "  Watchdog already disabled or not found"; fi'
], check=True)

# ── Step 4: Kill watchdog and stale processes ──
print('[4/5] Killing watchdog and stale processes...')
subprocess.run(['docker', 'exec', AGENT, 'bash', '-c',
    'pkill -f watchdog.sh 2>/dev/null || true; '
    'supervisorctl stop run_bot 2>/dev/null || true; '
    'echo "  run_bot stopped; run_mcp was left running"'
], check=True)

# ── Step 5: Reload supervisord ──
print('[5/5] Reloading supervisord...')
result = subprocess.run(
    ['docker', 'exec', AGENT, 'bash', '-c',
     'supervisorctl reread 2>&1; '
     'supervisorctl update 2>&1; '
     'supervisorctl stop run_bot 2>/dev/null || true; '
     'sleep 2; '
     'supervisorctl status 2>&1'
    ],
    capture_output=True, text=True
)
print(result.stdout)
if result.stderr and VERBOSE:
    print(result.stderr)

print(f'\nDone. {AGENT} runs run_mcp. run_bot stays stopped.')
