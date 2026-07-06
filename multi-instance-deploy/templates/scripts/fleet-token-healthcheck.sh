#!/bin/bash
# =============================================================================
# Fleet Matrix Token Health-Check Script
# 
# Tests Matrix MCP and bot tokens across all agent containers.
# If a token is expired (401), generates a fresh token via login API,
# updates MCP .env + settings.json, and restarts the MCP server and bot.
#
# Usage: ./fleet-token-healthcheck.sh [agent-number ...]
#   If agent-number(s) provided, only check those agents.
#   Otherwise, check all agents (1-5).
#
# Author: Galadriel/agent0-2
# Created: 2026-07-06
# =============================================================================
set -euo pipefail

# --- Config ---
AGENT_ZERO_DIR="/opt/agent-zero"
DEPLOY_REPO_DIR="/opt/agent-zero/multi-instance-deploy"
LOG_FILE="/opt/agent-zero/multi-instance-deploy/logs/fleet-token-healthcheck.log"

if [[ $# -ge 1 ]]; then
    AGENTS=("$@")
else
    AGENTS=(1 2 3 4 5)
fi

# --- Helpers ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

get_container_mcp_env_value() {
    local agent_num=$1
    local key=$2
    docker exec "agent0-${agent_num}" bash -c "grep '^${key}=' /a0/usr/workdir/matrix-mcp-server/.env 2>/dev/null | cut -d'=' -f2-" 2>/dev/null | tr -d '\r\n'
}

get_container_bot_env_value() {
    local agent_num=$1
    local key=$2
    docker exec "agent0-${agent_num}" bash -c "grep '^${key}=' /a0/usr/workdir/matrix-bot/.env 2>/dev/null | cut -d'=' -f2-" 2>/dev/null | tr -d '\r\n'
}

get_deploy_env_value() {
    local agent_num=$1
    local key=$2
    grep "^${key}=" "${AGENT_ZERO_DIR}/agent0-${agent_num}/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '\r\n'
}

test_token() {
    local agent_num=$1
    local homeserver=$2
    local token=$3
    docker exec "agent0-${agent_num}" curl -s -o /dev/null -w '%{http_code}' \
        -H "Authorization: Bearer ${token}" \
        "${homeserver}/_matrix/client/v3/account/whoami" 2>/dev/null || echo "000"
}

generate_new_token() {
    local agent_num=$1
    local homeserver=$2
    local username=$3
    local password=$4
    local device_id=$5
    local response
    response=$(docker exec "agent0-${agent_num}" curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"m.login.password\",\"identifier\":{\"type\":\"m.id.user\",\"user\":\"${username}\"},\"password\":\"${password}\",\"device_id\":\"${device_id}\"}" \
        "${homeserver}/_matrix/client/v3/login" 2>/dev/null)
    echo "$response" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('access_token',''))" 2>/dev/null
}

update_mcp_env() {
    local agent_num=$1
    local token=$2
    local user_id=$3
    docker exec "agent0-${agent_num}" bash -c \
        "sed -i 's|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${token}|' /a0/usr/workdir/matrix-mcp-server/.env && \
         sed -i 's|^MATRIX_USER_ID=.*|MATRIX_USER_ID=${user_id}|' /a0/usr/workdir/matrix-mcp-server/.env"
}

update_bot_env() {
    local agent_num=$1
    local token=$2
    local user_id=$3
    docker exec "agent0-${agent_num}" bash -c \
        "sed -i 's|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${token}|' /a0/usr/workdir/matrix-bot/.env && \
         sed -i 's|^MATRIX_USER_ID=.*|MATRIX_USER_ID=${user_id}|' /a0/usr/workdir/matrix-bot/.env"
}

sync_settings() {
    local agent_num=$1
    docker exec "agent0-${agent_num}" python3 /a0/usr/workdir/sync-mcp-token-into-settings.py 2>/dev/null || \
        log "  WARN: sync-mcp-token-into-settings.py failed on agent0-${agent_num}"
}

restart_services() {
    local agent_num=$1
    docker exec "agent0-${agent_num}" bash -c \
        "supervisorctl restart run_mcp run_bot 2>/dev/null" || \
        log "  WARN: supervisorctl restart failed on agent0-${agent_num}"
}

# --- Main ---
mkdir -p "$(dirname "$LOG_FILE")"
log "=== Fleet Token Health-Check Start ==="
log "Checking agents: ${AGENTS[*]}"

for agent_num in "${AGENTS[@]}"; do
    log "--- agent0-${agent_num} ---"
    
    # Get MCP token and user_id from container
    MCP_TOKEN=$(get_container_mcp_env_value "$agent_num" "MATRIX_ACCESS_TOKEN")
    MCP_USER_ID=$(get_container_mcp_env_value "$agent_num" "MATRIX_USER_ID")
    HOMESERVER=$(get_container_mcp_env_value "$agent_num" "MATRIX_HOMESERVER_URL")
    
    # Get bot token from container
    BOT_TOKEN=$(get_container_bot_env_value "$agent_num" "MATRIX_ACCESS_TOKEN")
    
    # Get password from deployment .env
    DEPLOY_PASSWORD=$(get_deploy_env_value "$agent_num" "MATRIX_PASSWORD")
    
    # Determine username for login (extract from user_id @user:domain)
    USERNAME=$(echo "$MCP_USER_ID" | sed 's/^@//; s/:.*$//')
    
    log "  MCP User: ${MCP_USER_ID}"
    log "  Homeserver: ${HOMESERVER}"
    log "  MCP Token: ${MCP_TOKEN:0:12}..."
    log "  Bot Token: ${BOT_TOKEN:0:12}..."
    log "  Deploy Password: ${DEPLOY_PASSWORD:0:8}..."
    log "  Login Username: ${USERNAME}"
    
    if [[ -z "$MCP_TOKEN" || -z "$HOMESERVER" ]]; then
        log "  SKIP: Missing MCP token or homeserver"
        continue
    fi
    
    # Test MCP token (curl inside the container)
    MCP_STATUS=$(test_token "$agent_num" "$HOMESERVER" "$MCP_TOKEN")
    log "  MCP token status: HTTP ${MCP_STATUS}"
    
    # Test bot token
    BOT_STATUS=$(test_token "$agent_num" "$HOMESERVER" "$BOT_TOKEN")
    log "  Bot token status: HTTP ${BOT_STATUS}"
    
    NEW_MCP_TOKEN=""
    NEW_BOT_TOKEN=""
    
    if [[ "$MCP_STATUS" == "401" || "$BOT_STATUS" == "401" ]]; then
        log "  Token(s) expired — attempting refresh..."
        
        # Try login with deployment password
        if [[ -n "$DEPLOY_PASSWORD" ]]; then
            NEW_MCP_TOKEN=$(generate_new_token "$agent_num" "$HOMESERVER" "$USERNAME" "$DEPLOY_PASSWORD" "matrix-mcp-server-device")
            NEW_BOT_TOKEN=$(generate_new_token "$agent_num" "$HOMESERVER" "$USERNAME" "$DEPLOY_PASSWORD" "AgentZeroBot")
        fi
        
        # If deployment password fails, try "password" (common default)
        if [[ -z "$NEW_MCP_TOKEN" ]]; then
            log "  Deployment password failed, trying default password..."
            NEW_MCP_TOKEN=$(generate_new_token "$agent_num" "$HOMESERVER" "$USERNAME" "password" "matrix-mcp-server-device")
            NEW_BOT_TOKEN=$(generate_new_token "$agent_num" "$HOMESERVER" "$USERNAME" "password" "AgentZeroBot")
        fi
        
        if [[ -n "$NEW_MCP_TOKEN" && -n "$NEW_BOT_TOKEN" ]]; then
            log "  Refresh successful: MCP=${NEW_MCP_TOKEN:0:12}... Bot=${NEW_BOT_TOKEN:0:12}..."
            
            # Update MCP .env
            update_mcp_env "$agent_num" "$NEW_MCP_TOKEN" "$MCP_USER_ID"
            log "  Updated MCP .env"
            
            # Update bot .env
            update_bot_env "$agent_num" "$NEW_BOT_TOKEN" "$MCP_USER_ID"
            log "  Updated bot .env"
            
            # Sync settings.json
            sync_settings "$agent_num"
            log "  Synced settings.json"
            
            # Restart services
            restart_services "$agent_num"
            log "  Restarted MCP + bot"
            
            # Update deployment .env for persistence
            sed -i "s|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${NEW_MCP_TOKEN}|" \
                "${AGENT_ZERO_DIR}/agent0-${agent_num}/.env" 2>/dev/null || true
            log "  Updated deployment .env"
        else
            log "  ERROR: Could not generate new token — login failed with all passwords"
            log "  Manual intervention required for agent0-${agent_num}"
        fi
    elif [[ "$MCP_STATUS" == "200" && "$BOT_STATUS" == "200" ]]; then
        log "  All tokens valid"
    else
        log "  WARN: Unexpected status — MCP:${MCP_STATUS} Bot:${BOT_STATUS}"
    fi
    
    log "--- agent0-${agent_num} done ---"
done

log "=== Fleet Token Health-Check Complete ==="
