#!/bin/bash
# =============================================================================
# Fleet Matrix Token Health-Check Script
# 
# Tests the Matrix MCP token across agent containers.
# If that token is expired (401), logs in again as the stored MCP device,
# updates the MCP .env and settings.json, and restarts run_mcp only.
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

# matrix-mcp-server-r2 binds its E2EE crypto store to one device. A refreshed
# MCP token must log in as that same device, or the store is orphaned.
get_mcp_device_id() {
    local agent_num=$1
    local store
    store=$(get_container_mcp_env_value "$agent_num" "CRYPTO_STORE_PATH")
    if [[ -n "$store" ]]; then
        docker exec "agent0-${agent_num}" cat "${store}/.device-id" 2>/dev/null | tr -d '\r\n'
    fi
}

update_mcp_env() {
    local agent_num=$1
    local token=$2
    local user_id=$3
    docker exec "agent0-${agent_num}" bash -c \
        "sed -i 's|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${token}|' /a0/usr/workdir/matrix-mcp-server/.env && \
         sed -i 's|^MATRIX_USER_ID=.*|MATRIX_USER_ID=${user_id}|' /a0/usr/workdir/matrix-mcp-server/.env"
}

# v0.93 does not write a token into matrix-bot/.env and does not log in as AgentZeroBot.

sync_settings() {
    local agent_num=$1
    docker exec "agent0-${agent_num}" python3 /a0/usr/workdir/sync-mcp-token-into-settings.py 2>/dev/null || \
        log "  WARN: sync-mcp-token-into-settings.py failed on agent0-${agent_num}"
}

restart_services() {
    local agent_num=$1
    docker exec "agent0-${agent_num}" bash -c \
        "supervisorctl restart run_mcp 2>/dev/null" || \
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
    
    # Get password from deployment .env
    DEPLOY_PASSWORD=$(get_deploy_env_value "$agent_num" "MATRIX_PASSWORD")
    
    # Determine username for login (extract from user_id @user:domain)
    USERNAME=$(echo "$MCP_USER_ID" | sed 's/^@//; s/:.*$//')
    
    log "  MCP User: ${MCP_USER_ID}"
    log "  Homeserver: ${HOMESERVER}"
    log "  Login Username: ${USERNAME}"
    
    if [[ -z "$MCP_TOKEN" || -z "$HOMESERVER" ]]; then
        log "  SKIP: Missing MCP token or homeserver"
        continue
    fi
    
    # Test MCP token (curl inside the container)
    MCP_STATUS=$(test_token "$agent_num" "$HOMESERVER" "$MCP_TOKEN")
    log "  MCP token status: HTTP ${MCP_STATUS}"
    
    NEW_MCP_TOKEN=""

    if [[ "$MCP_STATUS" == "401" ]]; then
        log "  MCP token expired — attempting refresh..."
        MCP_DEVICE_ID=$(get_mcp_device_id "$agent_num")
        MCP_DEVICE_ID=${MCP_DEVICE_ID:-matrix-mcp-server-device}
        log "  MCP device: ${MCP_DEVICE_ID}"

        # Reuse the stored MCP device. Do not log in as AgentZeroBot.
        if [[ -n "$DEPLOY_PASSWORD" ]]; then
            NEW_MCP_TOKEN=$(generate_new_token "$agent_num" "$HOMESERVER" "$USERNAME" "$DEPLOY_PASSWORD" "$MCP_DEVICE_ID")
        fi

        if [[ -z "$NEW_MCP_TOKEN" ]]; then
            log "  Deployment password failed, trying default password..."
            NEW_MCP_TOKEN=$(generate_new_token "$agent_num" "$HOMESERVER" "$USERNAME" "password" "$MCP_DEVICE_ID")
        fi

        if [[ -n "$NEW_MCP_TOKEN" ]]; then
            log "  MCP token refresh succeeded"
            update_mcp_env "$agent_num" "$NEW_MCP_TOKEN" "$MCP_USER_ID"
            log "  Updated MCP .env"
            sync_settings "$agent_num"
            log "  Synced settings.json"
            restart_services "$agent_num"
            log "  Restarted run_mcp"
            sed -i "s|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${NEW_MCP_TOKEN}|" \
                "${AGENT_ZERO_DIR}/agent0-${agent_num}/.env" 2>/dev/null || true
            log "  Updated deployment .env"
        else
            log "  ERROR: Could not generate a new MCP token"
            log "  Manual intervention required for agent0-${agent_num}"
        fi
    elif [[ "$MCP_STATUS" == "200" ]]; then
        log "  MCP token valid"
    else
        log "  WARN: Unexpected MCP status: ${MCP_STATUS}"
    fi
    
    log "--- agent0-${agent_num} done ---"
done

log "=== Fleet Token Health-Check Complete ==="
