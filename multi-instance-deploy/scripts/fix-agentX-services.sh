#!/bin/bash
set -euo pipefail

# =============================================================================
# fix-agentX-services.sh - Self-Service Service Recovery Script (v4.0)
# =============================================================================
# Usage: ./fix-agentX-services.sh <agent-name>
# Supported: agent0-1 through agent0-5
# 
# This script fixes agents with services not starting (MCP server, matrix-bot):
#   1. SSH to g2s host (172.23.100.121)
#   2. Copy startup-services.sh template to agent container
#   3. Run startup-services.sh to start missing services
#   4. Verify MCP server (http-server.js) and matrix-bot are running
#   5. Show diagnostics and next steps
# =============================================================================

if [ $# -eq 0 ]; then
    echo "Usage: $0 <agent-name>"
    echo ""
    echo "Supported agents: agent0-1, agent0-2, agent0-3, agent0-4, agent0-5"
    echo ""
    echo "This script performs:"
    echo "  1. SSH to g2s host (172.23.100.121)"
    echo "  2. Copy startup-services.sh to agent container"
    echo "  3. Run startup-services.sh to start services"
    echo "  4. Verify MCP server (http-server.js) running"
    echo "  5. Verify matrix-bot runtime running"
    echo "  6. Show diagnostics and next steps"
    exit 1
fi

AGENT="$1"
AGENTS=(agent0-1 agent0-2 agent0-3 agent0-4 agent0-5)

if [[ ! " ${AGENTS[@]} " =~ " ${AGENT} " ]]; then
    echo "ERROR: Invalid agent: $AGENT"
    echo "Must be one of: ${AGENTS[*]}"
    exit 1
fi

echo "========================================"
echo "Service Fix for $AGENT (v4.0)"
echo "Host: g2s (172.23.100.121)"
echo "========================================"
echo ""

ssh -o StrictHostKeyChecking=no l0r3zz@172.23.100.121 << SSH_EOF

echo "Step 1: Verify startup-services.sh template exists..."
if ! [ -f /opt/agent-zero/multi-instance-deploy/templates/scripts/startup-services.sh ]; then
    echo "ERROR: startup-services.sh not found on g2s!"
    echo "Run: cd /opt/agent-zero && git pull"
    exit 1
fi
echo "OK: Template found at /opt/agent-zero/multi-instance-deploy/templates/scripts/startup-services.sh"

# Check if template version matches current (compare hashes)
SCRIPT_HASH=$(sha256sum /opt/agent-zero/multi-instance-deploy/templates/scripts/startup-services.sh | cut -d' ' -f1)
echo "Template hash: $SCRIPT_HASH"

echo
exec step 2: Copy startup-services.sh to $AGENT container..."
docker cp /opt/agent-zero/multi-instance-deploy/templates/scripts/startup-services.sh \$AGENT:/a0/usr/workdir/startup-services.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy startup-services.sh to $AGENT!"
    exit 1
fi
echo "OK: startup-services.sh copied to $AGENT container"

echo
exec step 3: Run startup-services.sh to start services..."
DOCKER_OUTPUT=$(docker exec \$AGENT sh -c "/a0/usr/workdir/startup-services.sh" 2>&1)
echo "$DOCKER_OUTPUT"

echo
exec step 4: Verify MCP server (http-server.js)..."
MCP_CHECK=$(docker exec \$AGENT sh -c "ps aux 2>/dev/null | grep 'node.*http-server.js' | grep -v grep" || echo "NOT RUNNING")
echo "$MCP_CHECK"
if echo "$MCP_CHECK" | grep -q "node.*http-server.js"; then
    MCP_PID=$(echo "$MCP_CHECK" | awk '{print \$2}')
    echo "OK: MCP server running (PID \$MCP_PID)"
else
    echo "ERROR: MCP server NOT RUNNING"
    echo "Troubleshooting: docker logs \$AGENT-matrix-mcp-server --tail 20"
    exit 1
fi

echo
exec step 5: Verify matrix-bot runtime..."
BOT_CHECK=$(docker exec \$AGENT sh -c "ps aux 2>/dev/null | grep -E 'run-matrix-bot.sh|python.*matrix_bot.py|matrix-bot-rust' | grep -v grep" || echo "NOT RUNNING")
echo "$BOT_CHECK"
if ! echo "$BOT_CHECK" | grep -q "NOT RUNNING"; then
    BOT_PID=$(echo "$BOT_CHECK" | awk '{print \$2}')
    echo "OK: matrix-bot running (PID \$BOT_PID)"
else
    echo "WARNING: matrix-bot NOT running"
    echo "Run again: docker exec \$AGENT sh -c '/a0/usr/workdir/startup-services.sh'"
fi

echo
exec step 6: Container status for $AGENT..."
docker ps --filter name=\$AGENT --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"

echo
exec step 7: Recent startup-services.log (last 15 lines)..."
docker exec \$AGENT tail -15 /a0/usr/workdir/startup-services.log 2>/dev/null || echo "No startup log found"

echo
exec ================================="
echo SERVICE FIX COMPLETE"
echo ================================="
echo ""
echo "Next: In Element (Fleet HQ Clean room), send:"
echo "  AG_NAME: federation diagnostics"
echo ""
echo "Expected: ALL services show GREEN ✓"
echo "If OK: Fleet is healthy"
echo ""
SSH_EOF

echo ""
echo "Script execution complete!"
