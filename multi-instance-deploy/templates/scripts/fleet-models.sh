#!/bin/bash
# =============================================================================
# fleet-models.sh — Agent-Matrix Fleet Model Configuration Manager (v2.0)
# =============================================================================
# Shows and modifies which LLM models each agent is configured to use.
# Reads/writes runtime configuration from /a0/usr/plugins/_model_config/config.json
#
# Usage (reporting):
#   ./fleet-models.sh
#   ./fleet-models.sh --instances 2,3
#   ./fleet-models.sh --instances 1-5
#   ./fleet-models.sh --verbose
#   ./fleet-models.sh --json
#   ./fleet-models.sh --diagnose
#
# Usage (model management):
#   ./fleet-models.sh --instances 2,3 --set-chat-model openrouter/moonshotai/kimi-k2.6
#   ./fleet-models.sh --instances 1-5 --set-utility-model openai/gpt-5.4-nano --yes
#   ./fleet-models.sh --instances 2 --set-chat-model qwen/qwen3-235b-a22b --dry-run
#   ./fleet-models.sh --instances 1-5 --set-embedding-model sentence-transformers/all-MiniLM-L6-v2 --yes
#
# Requires: docker, python3
# Runs on: g2s host (172.23.100.121)
# =============================================================================

set -euo pipefail

# --- Configuration ---
BASE_DIR="/opt/agent-zero"
ALL_INSTANCES="1 2 3 4 5"
CONFIG_PATH="/a0/usr/plugins/_model_config/config.json"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# --- Parse arguments ---
RAW_INSTANCES=""       # unparsed, for range expansion
VERBOSE=false
OUTPUT_FORMAT="table"  # table, json
DIAGNOSE=false

# Model setting flags
SET_CHAT_MODEL=""
SET_UTILITY_MODEL=""
SET_EMBEDDING_MODEL=""
DRY_RUN=false
YES=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Reporting Options:
  --instances N,N,...    Comma-separated instance numbers (default: all)
  --instances N-M        Range of instance numbers (e.g., 1-5)
  --verbose              Show provider details, context window sizes, and full model names
  --json                 Output in JSON format
  --diagnose             Run diagnostic checks (Change Detection, Config Sync)

Model Management Options:
  --set-chat-model ID       Set main/chat model (e.g., openrouter/moonshotai/kimi-k2.6)
  --set-utility-model ID    Set utility model (e.g., openai/gpt-5.4-nano)
  --set-embedding-model ID  Set embedding model (e.g., sentence-transformers/all-MiniLM-L6-v2)
  --dry-run                 Preview changes without applying
  --yes                     Skip confirmation prompt

  -h, --help             Show this help

Examples:
  $(basename "$0")
  $(basename "$0") --instances 2,3
  $(basename "$0") --instances 1-5 --verbose
  $(basename "$0") --json
  $(basename "$0") --diagnose
  $(basename "$0") --instances 2,3 --set-chat-model openrouter/moonshotai/kimi-k2.6
  $(basename "$0") --instances 1-5 --set-utility-model openai/gpt-5.4-nano --yes
  $(basename "$0") --instances 2 --set-chat-model qwen/qwen3-235b-a22b --dry-run
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --instances)   RAW_INSTANCES="$2"; shift 2 ;;
        --verbose)     VERBOSE=true; shift ;;
        --json)        OUTPUT_FORMAT="json"; shift ;;
        --diagnose)    DIAGNOSE=true; shift ;;
        --set-chat-model)      SET_CHAT_MODEL="$2"; shift 2 ;;
        --set-utility-model)   SET_UTILITY_MODEL="$2"; shift 2 ;;
        --set-embedding-model) SET_EMBEDDING_MODEL="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=true; shift ;;
        --yes)         YES=true; shift ;;
        -h|--help)     usage ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; echo "Use --help for usage."; exit 1 ;;
    esac
done

# --- Helper Functions ---

log() {
    echo -e "$(date '+%H:%M:%S') $1" >&2
}

log_header() {
    echo -e "\n${CYAN}${BOLD}$1${NC}" >&2
}

# Audit log for model changes
# Format: TIMESTAMP|INSTANCE|MODEL_TYPE|OLD_MODEL|NEW_MODEL|TRIGGER
audit_log() {
    local INSTANCE="$1"
    local MODEL_TYPE="$2"
    local OLD_MODEL="$3"
    local NEW_MODEL="$4"
    local TRIGGER="${5:-fleet-models.sh}"
    local TIMESTAMP=$(date -Iseconds)
    local LOG_DIR="/opt/agent-zero/logs"
    local LOG_FILE="${LOG_DIR}/fleet-models-audit.log"
    
    # Create log directory if it doesn't exist
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
    fi
    
    local LOG_LINE="${TIMESTAMP}|${INSTANCE}|${MODEL_TYPE}|${OLD_MODEL}|${NEW_MODEL}|${TRIGGER}"
    
    # Try to write to host log path first, fallback to container-local
    if echo "$LOG_LINE" >> "$LOG_FILE" 2>/dev/null; then
        return 0
    fi
    
    # Fallback: write inside the container's workdir
    local FALLBACK_LOG="/a0/usr/workdir/fleet-models-audit.log"
    echo "$LOG_LINE" >> "$FALLBACK_LOG" 2>/dev/null || true
}

is_container_running() {
    local N=$1
    docker ps --format '{{.Names}}' | grep -qx "agent0-$N" 2>/dev/null
}

# Expand instances: "1,2,3" or "1-5" or "1-3,5"
expand_instances() {
    local RAW="$1"
    local RESULT=""
    
    if [ -z "$RAW" ]; then
        echo "$ALL_INSTANCES"
        return
    fi
    
    # Replace commas with spaces for iteration
    local PARTS=$(echo "$RAW" | tr ',' ' ')
    
    for PART in $PARTS; do
        if [[ "$PART" == *"-"* ]]; then
            local START=$(echo "$PART" | cut -d'-' -f1)
            local END=$(echo "$PART" | cut -d'-' -f2)
            for ((i=START; i<=END; i++)); do
                RESULT="$RESULT $i"
            done
        else
            RESULT="$RESULT $PART"
        fi
    done
    
    echo "$RESULT" | tr ' ' '\n' | sort -n -u | tr '\n' ' '
}

INSTANCES=$(expand_instances "$RAW_INSTANCES")

# Clean profile value - removes template artifacts like {{PROFILE}}\nhacker
# and extracts just the actual profile name
clean_profile_value() {
    local RAW="$1"
    # Replace newlines with spaces, filter out template placeholders, take last word
    echo "$RAW" | tr '\n' ' ' | sed 's/\s\+/ /g' | tr ' ' '\n' | grep -v '{{' | grep -v '^$' | tail -1
}

# Validate model ID format
validate_model_id() {
    local MODEL_ID="$1"
    local TYPE="$2"
    
    if [ -z "$MODEL_ID" ]; then
        return 0
    fi
    
    # Must contain at least one slash (provider/name format)
    if [[ "$MODEL_ID" != *"/"* ]]; then
        echo -e "${RED}Error: Invalid $TYPE model ID '$MODEL_ID'${NC}"
        echo -e "${RED}       Model IDs must use provider/name format (e.g., openrouter/moonshotai/kimi-k2.6)${NC}"
        return 1
    fi
    
    return 0
}

# Get model config from the runtime config file inside the container
get_model_config() {
    local N=$1
    local MODEL_TYPE="$2"  # chat_model, utility_model, embedding_model
    
    if ! is_container_running "$N"; then
        echo "unknown"
        return
    fi
    
    # Read config file from container and extract model info
    docker exec "agent0-$N" python3 -c "
import json
try:
    with open('$CONFIG_PATH', 'r') as f:
        config = json.load(f)
    model_config = config.get('$MODEL_TYPE', {})
    provider = model_config.get('provider', 'unknown')
    name = model_config.get('name', 'unknown')
    ctx_length = model_config.get('ctx_length', 0)
    api_base = model_config.get('api_base', '')
    ctx_history = model_config.get('ctx_history', 0)
    ctx_input = model_config.get('ctx_input', 0)
    vision = model_config.get('vision', False)
    kwargs = model_config.get('kwargs', {})
    max_tokens = kwargs.get('max_tokens', 0)
    if provider and name and provider != 'unknown' and name != 'unknown':
        print(f'{provider}/{name}|{ctx_length}|{api_base}|{ctx_history}|{ctx_input}|{vision}|{max_tokens}')
    else:
        print('unknown|0||||False|0')
except:
    print('unknown|0||||False|0')
" 2>/dev/null || echo "unknown|0||||False|0"
}

# Set model config in the runtime config file inside the container
set_model_config() {
    local N=$1
    local MODEL_TYPE="$2"   # chat_model, utility_model, embedding_model
    local NEW_MODEL_ID="$3" # provider/name
    
    if ! is_container_running "$N"; then
        echo "SKIP"
        return
    fi
    
    local PROVIDER=$(echo "$NEW_MODEL_ID" | cut -d'/' -f1)
    local NAME=$(echo "$NEW_MODEL_ID" | cut -d'/' -f2-)
    
    docker exec "agent0-$N" python3 -c "
import json

try:
    with open('$CONFIG_PATH', 'r') as f:
        config = json.load(f)
    
    if '$MODEL_TYPE' not in config:
        config['$MODEL_TYPE'] = {}
    
    model = config['$MODEL_TYPE']
    old_name = model.get('name', 'unknown')
    
    # Update provider and name
    model['provider'] = '$PROVIDER'
    model['name'] = '$NAME'
    
    # If api_base is empty and provider is openrouter, leave it empty (uses default)
    # Otherwise keep existing api_base
    
    with open('$CONFIG_PATH', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f'OK|{old_name}')
except Exception as e:
    print(f'ERROR|{str(e)}')
" 2>/dev/null || echo "ERROR|python execution failed"
}

# Update .env file on host for persistence across restarts
update_env_model() {
    local N=$1
    local ENV_KEY="$2"
    local NEW_VALUE="$3"
    local ENV_FILE="${BASE_DIR}/agent0-${N}/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "NOENV"
        return
    fi
    
    # Check if key exists
    if grep -qE "^[[:space:]]*${ENV_KEY}=" "$ENV_FILE"; then
        # Update existing key (last occurrence)
        local TMP_FILE=$(mktemp)
        local FOUND=false
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ "$line" =~ ^[[:space:]]*${ENV_KEY}= ]]; then
                if [ "$FOUND" = false ]; then
                    echo "${ENV_KEY}=${NEW_VALUE}" >> "$TMP_FILE"
                    FOUND=true
                else
                    # Comment out duplicates
                    echo "# ${line}" >> "$TMP_FILE"
                fi
            else
                echo "$line" >> "$TMP_FILE"
            fi
        done < "$ENV_FILE"
        mv "$TMP_FILE" "$ENV_FILE"
        echo "UPDATED"
    else
        # Append new key
        echo "" >> "$ENV_FILE"
        echo "# Added by fleet-models.sh on $(date '+%Y-%m-%d %H:%M:%S')" >> "$ENV_FILE"
        echo "${ENV_KEY}=${NEW_VALUE}" >> "$ENV_FILE"
        echo "ADDED"
    fi
}

# Get current context tokens from Agent Zero API
get_current_context_tokens() {
    local N=$1
    
    if ! is_container_running "$N"; then
        echo "0"
        return
    fi
    
    # Try to get current context window tokens from API
    docker exec "agent0-$N" python3 -c "
import json
import urllib.request
import urllib.error

try:
    # Get CSRF token from environment
    import os
    csrf_token = os.environ.get('A0_CSRF_TOKEN', '')
    
    # Try to get context window from API
    url = 'http://127.0.0.1:80/api/ctx_window_get'
    headers = {'X-CSRF-Token': csrf_token} if csrf_token else {}
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=2) as response:
        data = json.loads(response.read().decode())
        tokens = data.get('tokens', 0)
        print(int(tokens))
except:
    # API might not be available or no active context
    print(0)
" 2>/dev/null || echo "0"
}

get_agent_profile() {
    local N=$1
    local PROFILE=""
    
    # Primary: try container environment
    if is_container_running "$N"; then
        PROFILE=$(docker exec "agent0-$N" printenv "A0_SET_agent_profile" 2>/dev/null || echo "")
    fi
    
    # Fallback: try .env file if container env is empty or contains template artifacts
    if [ -z "$PROFILE" ] || [[ "$PROFILE" == *"{{"* ]]; then
        local ENV_FILE="${BASE_DIR}/agent0-${N}/.env"
        if [ -f "$ENV_FILE" ]; then
            # Get all matching lines, take the last one with a real value
            local ENV_PROFILE=$(grep -E '^A0_SET_agent_profile=' "$ENV_FILE" 2>/dev/null | \
                tail -1 | \
                sed 's/^A0_SET_agent_profile=//')
            if [ -n "$ENV_PROFILE" ]; then
                PROFILE="$ENV_PROFILE"
            fi
        fi
    fi
    
    # Clean the profile value to remove template artifacts
    if [ -n "$PROFILE" ]; then
        PROFILE=$(clean_profile_value "$PROFILE")
    fi
    
    echo "${PROFILE:-agent0}"
}

shorten_model_name() {
    local FULL_NAME="$1"
    # Remove provider prefix if present (e.g., "openrouter/anthropic/claude-sonnet-4" -> "anthropic/claude-sonnet-4")
    if [[ "$FULL_NAME" == *"/"* ]]; then
        echo "$FULL_NAME" | sed 's|^[^/]*/||'
    else
        echo "$FULL_NAME"
    fi
}

format_number() {
    local NUM="$1"
    if [ "$NUM" -ge 1000000 ] 2>/dev/null; then
        echo "$((NUM/1000000))M"
    elif [ "$NUM" -ge 1000 ] 2>/dev/null; then
        echo "$((NUM/1000))K"
    else
        echo "$NUM"
    fi
}

# Get .env model value for change detection
get_env_model_value() {
    local N=$1
    local KEY="$2"
    local ENV_FILE="${BASE_DIR}/agent0-${N}/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo ""
        return
    fi
    
    # Try to get the value from .env file
    local VALUE=$(grep -E "^[[:space:]]*${KEY}=" "$ENV_FILE" 2>/dev/null | \
        tail -1 | \
        sed "s/^[[:space:]]*${KEY}=//" | \
        sed "s/^[\"']//;s/[\"']$//")
    
    echo "$VALUE"
}

# Check MCP token sync
check_mcp_token_sync() {
    local N=$1
    local ENV_FILE="${BASE_DIR}/agent0-${N}/matrix-mcp-server/.env"
    local SETTINGS_FILE="${BASE_DIR}/agent0-${N}/settings.json"
    
    # Check if both files exist
    if [ ! -f "$ENV_FILE" ] || [ ! -f "$SETTINGS_FILE" ]; then
        echo "SKIP"
        return
    fi
    
    # Get token from MCP server .env
    local ENV_TOKEN=$(grep "MATRIX_ACCESS_TOKEN=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | sed 's/^["'\'']\|["'\'']$//g')
    
    # Get token from Agent Zero settings.json
    local A0_TOKEN=$(docker exec "agent0-$N" python3 -c "
import json
try:
    with open('/a0/usr/settings.json', 'r') as f:
        settings = json.load(f)
    mcp_str = settings.get('mcp_servers', '{}')
    # The mcp_servers field is a JSON string
    import ast
    mcp = ast.literal_eval(mcp_str) if isinstance(mcp_str, str) else mcp_str
    # Look for matrix server
    servers = mcp.get('mcpServers', {})
    matrix_server = servers.get('matrix', {})
    headers = matrix_server.get('headers', {})
    token = headers.get('matrix_access_token', '')
    print(token)
except:
    print('')
" 2>/dev/null || echo "")
    
    # Compare tokens
    if [ -z "$ENV_TOKEN" ] || [ -z "$A0_TOKEN" ]; then
        echo "SKIP"
    elif [ "$ENV_TOKEN" = "$A0_TOKEN" ]; then
        echo "MATCH"
    else
        echo "MISMATCH"
    fi
}

# --- Model Setting Mode ---

# Validate all requested model changes before proceeding
if [ -n "$SET_CHAT_MODEL" ] || [ -n "$SET_UTILITY_MODEL" ] || [ -n "$SET_EMBEDDING_MODEL" ]; then
    
    # Validate model IDs
    validate_model_id "$SET_CHAT_MODEL" "chat" || exit 1
    validate_model_id "$SET_UTILITY_MODEL" "utility" || exit 1
    validate_model_id "$SET_EMBEDDING_MODEL" "embedding" || exit 1
    
    # Map model types to env keys
    declare -A MODEL_TYPE_TO_ENV_KEY=(
        ["chat_model"]="A0_SET_chat_model"
        ["utility_model"]="A0_SET_utility_model"
        ["embedding_model"]="A0_SET_embedding_model"
    )
    
    # Build preview table
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    if [ "$DRY_RUN" = true ]; then
        log_header "  Fleet Model Change Preview (DRY RUN)"
    else
        log_header "  Fleet Model Change Preview"
    fi
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    
    # Summary of changes
    echo -e "  ${BOLD}Changes to apply:${NC}"
    [ -n "$SET_CHAT_MODEL" ] && echo -e "    • Chat model:      ${CYAN}$SET_CHAT_MODEL${NC}"
    [ -n "$SET_UTILITY_MODEL" ] && echo -e "    • Utility model:   ${CYAN}$SET_UTILITY_MODEL${NC}"
    [ -n "$SET_EMBEDDING_MODEL" ] && echo -e "    • Embedding model: ${CYAN}$SET_EMBEDDING_MODEL${NC}"
    echo ""
    
    # Target instances
    echo -e "  ${BOLD}Target instances:${NC} ${CYAN}$INSTANCES${NC}"
    echo ""
    
    # Per-instance preview
    printf "  ${BOLD}%-12s %-10s %-30s %-30s %-30s${NC}\n" \
        "Agent" "Status" "Chat" "Utility" "Embedding"
    printf "  %-12s %-10s %-30s %-30s %-30s\n" \
        "──────────" "─────────" "──────────────────────────────" "──────────────────────────────" "──────────────────────────────"
    
    local CHANGES_COUNT=0
    local SKIP_COUNT=0
    
    for N in $INSTANCES; do
        if is_container_running "$N"; then
            local STATUS="${GREEN}online${NC}"
            
            # Get current models
            local CHAT_CURR=$(get_model_config "$N" "chat_model" | cut -d'|' -f1)
            local UTIL_CURR=$(get_model_config "$N" "utility_model" | cut -d'|' -f1)
            local EMBED_CURR=$(get_model_config "$N" "embedding_model" | cut -d'|' -f1)
            
            # Determine new values
            local CHAT_NEW="${SET_CHAT_MODEL:-$CHAT_CURR}"
            local UTIL_NEW="${SET_UTILITY_MODEL:-$UTIL_CURR}"
            local EMBED_NEW="${SET_EMBEDDING_MODEL:-$EMBED_CURR}"
            
            # Highlight changes
            local CHAT_DISP="$CHAT_CURR"
            local UTIL_DISP="$UTIL_CURR"
            local EMBED_DISP="$EMBED_CURR"
            
            if [ -n "$SET_CHAT_MODEL" ] && [ "$CHAT_CURR" != "$SET_CHAT_MODEL" ]; then
                CHAT_DISP="${YELLOW}$CHAT_CURR → $SET_CHAT_MODEL${NC}"
                CHANGES_COUNT=$((CHANGES_COUNT + 1))
            fi
            if [ -n "$SET_UTILITY_MODEL" ] && [ "$UTIL_CURR" != "$SET_UTILITY_MODEL" ]; then
                UTIL_DISP="${YELLOW}$UTIL_CURR → $SET_UTILITY_MODEL${NC}"
                CHANGES_COUNT=$((CHANGES_COUNT + 1))
            fi
            if [ -n "$SET_EMBEDDING_MODEL" ] && [ "$EMBED_CURR" != "$SET_EMBEDDING_MODEL" ]; then
                EMBED_DISP="${YELLOW}$EMBED_CURR → $SET_EMBEDDING_MODEL${NC}"
                CHANGES_COUNT=$((CHANGES_COUNT + 1))
            fi
            
            # Truncate for display
            local CHAT_SHORT="${CHAT_DISP:0:28}"
            local UTIL_SHORT="${UTIL_DISP:0:28}"
            local EMBED_SHORT="${EMBED_DISP:0:28}"
            
            printf "  %-12b %-10b %-30b %-30b %-30b\n" \
                "agent0-$N" "$STATUS" "$CHAT_SHORT" "$UTIL_SHORT" "$EMBED_SHORT"
        else
            local STATUS="${DIM}offline${NC}"
            printf "  %-12b %-10b %-30s %-30s %-30s\n" \
                "agent0-$N" "$STATUS" "—" "—" "—"
            SKIP_COUNT=$((SKIP_COUNT + 1))
        fi
    done
    
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${BOLD}Dry run complete.${NC} No changes were made."
        echo -e "  ${DIM}Use without --dry-run to apply changes.${NC}"
        echo ""
        log_header "═══════════════════════════════════════════════════════════════════════════════"
        exit 0
    fi
    
    if [ "$CHANGES_COUNT" -eq 0 ]; then
        echo -e "  ${YELLOW}No changes needed — all targeted instances already have the requested models.${NC}"
        echo ""
        log_header "═══════════════════════════════════════════════════════════════════════════════"
        exit 0
    fi
    
    # Confirmation prompt
    if [ "$YES" = false ]; then
        echo -e "  ${YELLOW}This will modify $CHANGES_COUNT model configuration(s) across $(echo "$INSTANCES" | wc -w) instance(s).${NC}"
        echo -e "  ${YELLOW}Changes take effect immediately (next message).${NC}"
        echo ""
        read -p "  Proceed? [y/N]: " CONFIRM
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo -e "  ${RED}Aborted.${NC}"
            exit 1
        fi
        echo ""
    fi
    
    # Apply changes
    log_header "Applying Changes..."
    echo ""
    
    local APPLIED=0
    local FAILED=0
    
    for N in $INSTANCES; do
        if ! is_container_running "$N"; then
            echo -e "  ${DIM}agent0-$N: Container offline — skipped${NC}"
            continue
        fi
        
        echo -e "  ${BOLD}agent0-$N${NC}:"
        
        # Apply chat model change
        if [ -n "$SET_CHAT_MODEL" ]; then
            local RESULT=$(set_model_config "$N" "chat_model" "$SET_CHAT_MODEL")
            local STATUS=$(echo "$RESULT" | cut -d'|' -f1)
            local OLD_NAME=$(echo "$RESULT" | cut -d'|' -f2)
            
            if [ "$STATUS" = "OK" ]; then
                echo -e "    ${GREEN}✓${NC} Chat model: ${OLD_NAME} → ${CYAN}$SET_CHAT_MODEL${NC}"
                APPLIED=$((APPLIED + 1))
                audit_log "agent0-$N" "chat_model" "$OLD_NAME" "$SET_CHAT_MODEL" "fleet-models-cli"
            else
                echo -e "    ${RED}✗${NC} Chat model: $STATUS"
                FAILED=$((FAILED + 1))
            fi
            
            # Update .env for persistence
            local ENV_STATUS=$(update_env_model "$N" "A0_SET_chat_model" "$SET_CHAT_MODEL")
            case "$ENV_STATUS" in
                "UPDATED") echo -e "      ${DIM}└─ .env updated${NC}" ;;
                "ADDED")   echo -e "      ${DIM}└─ .env added${NC}" ;;
                "NOENV")   echo -e "      ${YELLOW}└─ .env not found (runtime only)${NC}" ;;
            esac
        fi
        
        # Apply utility model change
        if [ -n "$SET_UTILITY_MODEL" ]; then
            local RESULT=$(set_model_config "$N" "utility_model" "$SET_UTILITY_MODEL")
            local STATUS=$(echo "$RESULT" | cut -d'|' -f1)
            local OLD_NAME=$(echo "$RESULT" | cut -d'|' -f2)
            
            if [ "$STATUS" = "OK" ]; then
                echo -e "    ${GREEN}✓${NC} Utility model: ${OLD_NAME} → ${CYAN}$SET_UTILITY_MODEL${NC}"
                APPLIED=$((APPLIED + 1))
                audit_log "agent0-$N" "utility_model" "$OLD_NAME" "$SET_UTILITY_MODEL" "fleet-models-cli"
            else
                echo -e "    ${RED}✗${NC} Utility model: $STATUS"
                FAILED=$((FAILED + 1))
            fi
            
            local ENV_STATUS=$(update_env_model "$N" "A0_SET_utility_model" "$SET_UTILITY_MODEL")
            case "$ENV_STATUS" in
                "UPDATED") echo -e "      ${DIM}└─ .env updated${NC}" ;;
                "ADDED")   echo -e "      ${DIM}└─ .env added${NC}" ;;
                "NOENV")   echo -e "      ${YELLOW}└─ .env not found (runtime only)${NC}" ;;
            esac
        fi
        
        # Apply embedding model change
        if [ -n "$SET_EMBEDDING_MODEL" ]; then
            local RESULT=$(set_model_config "$N" "embedding_model" "$SET_EMBEDDING_MODEL")
            local STATUS=$(echo "$RESULT" | cut -d'|' -f1)
            local OLD_NAME=$(echo "$RESULT" | cut -d'|' -f2)
            
            if [ "$STATUS" = "OK" ]; then
                echo -e "    ${GREEN}✓${NC} Embedding model: ${OLD_NAME} → ${CYAN}$SET_EMBEDDING_MODEL${NC}"
                APPLIED=$((APPLIED + 1))
                audit_log "agent0-$N" "embedding_model" "$OLD_NAME" "$SET_EMBEDDING_MODEL" "fleet-models-cli"
            else
                echo -e "    ${RED}✗${NC} Embedding model: $STATUS"
                FAILED=$((FAILED + 1))
            fi
            
            local ENV_STATUS=$(update_env_model "$N" "A0_SET_embedding_model" "$SET_EMBEDDING_MODEL")
            case "$ENV_STATUS" in
                "UPDATED") echo -e "      ${DIM}└─ .env updated${NC}" ;;
                "ADDED")   echo -e "      ${DIM}└─ .env added${NC}" ;;
                "NOENV")   echo -e "      ${YELLOW}└─ .env not found (runtime only)${NC}" ;;
            esac
        fi
    done
    
    echo ""
    log_header "───────────────────────────────────────────────────────────────────────────────"
    echo -e "  ${BOLD}Summary:${NC} Applied: ${GREEN}$APPLIED${NC} | Failed: ${RED}$FAILED${NC}"
    echo -e "  ${DIM}Changes take effect on the next message turn — no restart required.${NC}"
    echo ""
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    exit 0
fi

# --- Diagnostic Mode ---

if [ "$DIAGNOSE" = true ]; then
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    log_header "  Agent-Matrix Fleet — Diagnostic Report"
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    
    log_header "Change Detection:"
    echo "  Comparing runtime config with .env template values..."
    echo ""
    
    for N in $INSTANCES; do
        if ! is_container_running "$N"; then
            printf "  ${DIM}agent0-$N: Container not running — skipping${NC}\n"
            continue
        fi
        
        printf "  ${BOLD}agent0-$N${NC}:\n"
        
        # Chat model
        CHAT_RUNTIME=$(get_model_config "$N" "chat_model" | cut -d'|' -f1)
        CHAT_ENV=$(get_env_model_value "$N" "A0_SET_chat_model")
        if [ -z "$CHAT_ENV" ]; then
            CHAT_ENV=$(get_env_model_value "$N" "A0_SET_chat_model_name")
        fi
        
        if [ -z "$CHAT_ENV" ]; then
            echo -e "    Chat model: ${YELLOW}No .env value found${NC}"
        elif [ "$CHAT_RUNTIME" = "$CHAT_ENV" ]; then
            echo -e "    Chat model: ${GREEN}OK${NC}"
        else
            echo -e "    Chat model: ${YELLOW}Mismatch${NC}"
            echo -e "      Runtime: $CHAT_RUNTIME"
            echo -e "      .env:    $CHAT_ENV"
        fi
        
        # Utility model
        UTILITY_RUNTIME=$(get_model_config "$N" "utility_model" | cut -d'|' -f1)
        UTILITY_ENV=$(get_env_model_value "$N" "A0_SET_utility_model")
        if [ -z "$UTILITY_ENV" ]; then
            UTILITY_ENV=$(get_env_model_value "$N" "A0_SET_utility_model_name")
        fi
        
        if [ -z "$UTILITY_ENV" ]; then
            echo -e "    Utility model: ${YELLOW}No .env value found${NC}"
        elif [ "$UTILITY_RUNTIME" = "$UTILITY_ENV" ]; then
            echo -e "    Utility model: ${GREEN}OK${NC}"
        else
            echo -e "    Utility model: ${YELLOW}Mismatch${NC}"
            echo -e "      Runtime: $UTILITY_RUNTIME"
            echo -e "      .env:    $UTILITY_ENV"
        fi
        
        # Embedding model
        EMBEDDING_RUNTIME=$(get_model_config "$N" "embedding_model" | cut -d'|' -f1)
        EMBEDDING_ENV=$(get_env_model_value "$N" "A0_SET_embedding_model")
        if [ -z "$EMBEDDING_ENV" ]; then
            EMBEDDING_ENV=$(get_env_model_value "$N" "A0_SET_embeddings_model_name")
        fi
        
        if [ -z "$EMBEDDING_ENV" ]; then
            echo -e "    Embedding model: ${YELLOW}No .env value found${NC}"
        elif [ "$EMBEDDING_RUNTIME" = "$EMBEDDING_ENV" ]; then
            echo -e "    Embedding model: ${GREEN}OK${NC}"
        else
            echo -e "    Embedding model: ${YELLOW}Mismatch${NC}"
            echo -e "      Runtime: $EMBEDDING_RUNTIME"
            echo -e "      .env:    $EMBEDDING_ENV"
        fi
        echo ""
    done
    
    log_header "Config Sync Check:"
    echo "  Checking Matrix MCP token synchronization..."
    echo ""
    
    for N in $INSTANCES; do
        if ! is_container_running "$N"; then
            printf "  ${DIM}agent0-$N: Container not running — skipping${NC}\n"
            continue
        fi
        
        SYNC_STATUS=$(check_mcp_token_sync "$N")
        case "$SYNC_STATUS" in
            "MATCH")
                echo -e "  ${GREEN}agent0-$N: MCP token MATCH${NC}"
                ;;
            "MISMATCH")
                echo -e "  ${RED}agent0-$N: MCP token MISMATCH${NC}"
                echo -e "      MCP server .env and Agent Zero settings.json have different tokens"
                ;;
            "SKIP")
                echo -e "  ${YELLOW}agent0-$N: MCP token check SKIPPED${NC} (files not found)"
                ;;
            *)
                echo -e "  ${RED}agent0-$N: MCP token check ERROR${NC}"
                ;;
        esac
    done
    
    echo ""
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    exit 0
fi

# --- Regular Model Report ---

if [ "$OUTPUT_FORMAT" = "json" ]; then
    echo "{\"fleet_models\": ["
else
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    log_header "  Agent-Matrix Fleet — Model Configuration Report"
    log_header "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    
    # Table header
    printf "  ${BOLD}%-12s %-12s %-24s %-24s %-20s${NC}\n" \
        "Agent" "Profile" "Main Model" "Utility Model" "Embedding"
    printf "  %-12s %-12s %-24s %-24s %-20s\n" \
        "──────────" "──────────" "──────────────────────" "──────────────────────" "──────────────────"
fi

TOTAL=0
ONLINE=0
OFFLINE=0
FIRST=true

for N in $INSTANCES; do
    TOTAL=$((TOTAL + 1))
    
    # Container status
    if is_container_running "$N"; then
        ONLINE=$((ONLINE + 1))
        STATUS_COLOR="${GREEN}"
        
        # Get agent profile
        PROFILE=$(get_agent_profile "$N")
        
        # Get model configurations (pipe-separated: provider/name|ctx_length|...)
        CHAT_RAW=$(get_model_config "$N" "chat_model")
        UTILITY_RAW=$(get_model_config "$N" "utility_model")
        EMBEDDING_RAW=$(get_model_config "$N" "embedding_model")
        
        # Parse model info
        CHAT_MODEL_FULL=$(echo "$CHAT_RAW" | cut -d'|' -f1)
        CHAT_CTX_LENGTH=$(echo "$CHAT_RAW" | cut -d'|' -f2)
        UTILITY_MODEL_FULL=$(echo "$UTILITY_RAW" | cut -d'|' -f1)
        UTILITY_CTX_LENGTH=$(echo "$UTILITY_RAW" | cut -d'|' -f2)
        EMBEDDING_MODEL_FULL=$(echo "$EMBEDDING_RAW" | cut -d'|' -f1)
        
        # Extract provider and shorten model names
        CHAT_PROVIDER="unknown"
        UTILITY_PROVIDER="unknown"
        EMBEDDING_PROVIDER="unknown"
        
        if [[ "$CHAT_MODEL_FULL" == *"/"* ]]; then
            CHAT_PROVIDER=$(echo "$CHAT_MODEL_FULL" | cut -d'/' -f1)
            CHAT_MODEL_SHORT=$(shorten_model_name "$CHAT_MODEL_FULL")
        else
            CHAT_MODEL_SHORT="$CHAT_MODEL_FULL"
        fi
        
        if [[ "$UTILITY_MODEL_FULL" == *"/"* ]]; then
            UTILITY_PROVIDER=$(echo "$UTILITY_MODEL_FULL" | cut -d'/' -f1)
            UTILITY_MODEL_SHORT=$(shorten_model_name "$UTILITY_MODEL_FULL")
        else
            UTILITY_MODEL_SHORT="$UTILITY_MODEL_FULL"
        fi
        
        if [[ "$EMBEDDING_MODEL_FULL" == *"/"* ]]; then
            EMBEDDING_PROVIDER=$(echo "$EMBEDDING_MODEL_FULL" | cut -d'/' -f1)
            EMBEDDING_MODEL_SHORT=$(shorten_model_name "$EMBEDDING_MODEL_FULL")
        else
            EMBEDDING_MODEL_SHORT="$EMBEDDING_MODEL_FULL"
        fi
        
        # Truncate if too long for table
        CHAT_MODEL_SHORT="${CHAT_MODEL_SHORT:0:22}"
        UTILITY_MODEL_SHORT="${UTILITY_MODEL_SHORT:0:22}"
        EMBEDDING_MODEL_SHORT="${EMBEDDING_MODEL_SHORT:0:18}"
        
    else
        OFFLINE=$((OFFLINE + 1))
        STATUS_COLOR="${DIM}"
        PROFILE="offline"
        CHAT_MODEL_SHORT="—"
        UTILITY_MODEL_SHORT="—"
        EMBEDDING_MODEL_SHORT="—"
        CHAT_MODEL_FULL="unknown"
        UTILITY_MODEL_FULL="unknown"
        EMBEDDING_MODEL_FULL="unknown"
        CHAT_PROVIDER="unknown"
        UTILITY_PROVIDER="unknown"
        EMBEDDING_PROVIDER="unknown"
        CHAT_CTX_LENGTH="0"
        UTILITY_CTX_LENGTH="0"
    fi
    
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        [ "$FIRST" = true ] && FIRST=false || echo ","
        cat <<EOF
  {
    "agent": "agent0-$N",
    "profile": "$PROFILE",
    "main_model": "$CHAT_MODEL_FULL",
    "utility_model": "$UTILITY_MODEL_FULL",
    "embedding_model": "$EMBEDDING_MODEL_FULL",
    "main_provider": "$CHAT_PROVIDER",
    "utility_provider": "$UTILITY_PROVIDER",
    "embedding_provider": "$EMBEDDING_PROVIDER",
    "main_ctx_length": $CHAT_CTX_LENGTH,
    "utility_ctx_length": $UTILITY_CTX_LENGTH,
    "status": "$([ "$ONLINE" -gt 0 ] && echo "online" || echo "offline")"
  }
EOF
    else
        printf "  ${STATUS_COLOR}%-12s${NC} %-12s %-24s %-24s %-20s\n" \
            "agent0-$N" "$PROFILE" "$CHAT_MODEL_SHORT" "$UTILITY_MODEL_SHORT" "$EMBEDDING_MODEL_SHORT"
        
        # Verbose mode: show providers, context windows, and full model names
        if [ "$VERBOSE" = true ] && is_container_running "$N"; then
            echo -e "             ${DIM}├─ Providers: chat=$CHAT_PROVIDER | utility=$UTILITY_PROVIDER | embedding=$EMBEDDING_PROVIDER${NC}"
            
            # Format context window sizes
            CHAT_CTX_FORMATTED=$(format_number "$CHAT_CTX_LENGTH")
            UTILITY_CTX_FORMATTED=$(format_number "$UTILITY_CTX_LENGTH")
            
            if [ "$CHAT_CTX_LENGTH" -gt 0 ] 2>/dev/null; then
                echo -e "             ${DIM}├─ Context Windows: chat=${CHAT_CTX_FORMATTED} | utility=${UTILITY_CTX_FORMATTED}${NC}"
            fi
            
            # Get current context usage ratio if possible
            if [ "$CHAT_CTX_LENGTH" -gt 0 ] 2>/dev/null; then
                CURRENT_TOKENS=$(get_current_context_tokens "$N")
                if [ "$CURRENT_TOKENS" -gt 0 ] 2>/dev/null; then
                    CURRENT_FORMATTED=$(format_number "$CURRENT_TOKENS")
                    RATIO=$(python3 -c "print(f'{$CURRENT_TOKENS/$CHAT_CTX_LENGTH*100:.1f}%')" 2>/dev/null || echo "N/A")
                    echo -e "             ${DIM}├─ Current Context Usage: ${CURRENT_FORMATTED}/${CHAT_CTX_FORMATTED} (${RATIO})${NC}"
                fi
            fi
            
            # Show full model names if truncated
            if [ ${#CHAT_MODEL_FULL} -gt 22 ]; then
                echo -e "             ${DIM}├─ Full main: $CHAT_MODEL_FULL${NC}"
            fi
            if [ ${#UTILITY_MODEL_FULL} -gt 22 ]; then
                echo -e "             ${DIM}├─ Full utility: $UTILITY_MODEL_FULL${NC}"
            fi
            if [ ${#EMBEDDING_MODEL_FULL} -gt 18 ]; then
                echo -e "             ${DIM}└─ Full embedding: $EMBEDDING_MODEL_FULL${NC}"
            fi
            echo ""
        fi
    fi
done

if [ "$OUTPUT_FORMAT" = "json" ]; then
    echo "]"
    echo ",  \"summary\": {"
    echo "    \"total\": $TOTAL,"
    echo "    \"online\": $ONLINE,"
    echo "    \"offline\": $OFFLINE"
    echo "  }"
    echo "}"
else
    echo ""
    
    # Summary
    log_header "───────────────────────────────────────────────────────────────────────────────"
    echo -e "  ${BOLD}Summary:${NC} Total: ${BOLD}$TOTAL${NC} | Online: ${GREEN}$ONLINE${NC} | Offline: ${DIM}$OFFLINE${NC}"
    echo ""
    
    # Legend
    if [ "$VERBOSE" = false ]; then
        echo -e "  ${DIM}Tip: Use --verbose to see provider details, context windows, and full model names${NC}"
        echo -e "  ${DIM}Tip: Use --diagnose to run Change Detection and Config Sync Check${NC}"
        echo -e "  ${DIM}Tip: Use --set-chat-model, --set-utility-model, --set-embedding-model to change models${NC}"
        echo ""
    fi
    
    log_header "═══════════════════════════════════════════════════════════════════════════════"
fi
