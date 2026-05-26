#!/usr/bin/env bash
# =============================================================================
# create-instance.sh — Agent Zero + Matrix Sovereign (v3.4 CLI-Flavor Edition)
# Host: g2s.cybertribe.com
# =============================================================================
set -euo pipefail

BASE_DIR="/opt/agent-zero"
TEMPLATE_DIR="$(cd "$(dirname "$0")" && pwd)/templates"
SELECTED_PROFILE="agent0"

# List of common keys we want to auto-extract from the shell environment
KEY_LIST=("API_KEY_OPENROUTER" "API_KEY_OPENAI" "API_KEY_ANTHROPIC" "API_KEY_GOOGLE")

usage() {
    cat <<USAGE
Usage: $(basename "$0") [OPTIONS] <instance-number>

Arguments:
  instance-number   Integer 1-99 (e.g., 2 for agent0-2)

Options:
  -p, --profile     Set Agent Flavor: agent0, hacker, researcher, developer (Default: agent0)
  -h, --help        Show this help message

Flavor Descriptions:
  agent0      - Standard balanced AI assistant (The Default)
  hacker      - Cybersecurity, pentesting, & security auditing specialist
  developer   - Software engineering, refactoring, & architecture specialist
  researcher  - Data gathering, analysis, & comprehensive reporting specialist

Examples:
  $(basename "$0") 2                 # Create standard agent0-2
  $(basename "$0") --profile hacker 3 # Create agent0-3 with Hacker persona

Port Allocation:
  Instance N: Web UI 5000N, SSH 5002(N+1)
  Network: Agent IP .88.N, Continuwuity IP .89.N
USAGE
    exit 0
}

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--profile) SELECTED_PROFILE="$2"; shift 2 ;;
        -h|--help) usage ;;
        -*) echo "Error: Unknown option $1"; usage ;;
        *) INSTANCE_NUM="$1"; shift ;;
    esac
done

if [[ -z "${INSTANCE_NUM:-}" ]]; then usage; fi

# --- Values ---
INSTANCE_NAME="agent0-${INSTANCE_NUM}"
INSTANCE_DIR="${BASE_DIR}/${INSTANCE_NAME}"
MAC_SUFFIX=$(printf '%02X' "$INSTANCE_NUM")
WEB_PORT=$((50000 + INSTANCE_NUM))
SSH_PORT=$((50021 + INSTANCE_NUM))

# --- Directories ---
mkdir -p "${INSTANCE_DIR}/usr" "${INSTANCE_DIR}/mhs/data"

# --- 1. Compose Generation ---
sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
    -e "s/__MAC_SUFFIX__/${MAC_SUFFIX}/g" \
    -e "s/__WEB_PORT__/${WEB_PORT}/g" \
    -e "s/__SSH_PORT__/${SSH_PORT}/g" \
    "${TEMPLATE_DIR}/docker-compose.yml.template" > "${INSTANCE_DIR}/docker-compose.yml"

# --- 2. .env Generation & Key Injection ---
cp "${TEMPLATE_DIR}/env.template" "${INSTANCE_DIR}/.env"
echo "🔑 Injecting API Keys from shell environment..."
for key in "${KEY_LIST[@]}"; do
    if [ -n "${!key:-}" ]; then
        val=$(echo "${!key}" | sed 's/\//\\\//g')
        sed -i "s/^${key}=.*/${key}=${val}/" "${INSTANCE_DIR}/.env"
    fi
done

# Add A0_SET_ overrides
cat << ENV_EXT >> "${INSTANCE_DIR}/.env"

# --- Zero-Touch Agent Config ---
A0_SET_chat_model=openrouter/google/gemini-2.0-flash-001
A0_SET_embedding_model=openai/text-embedding-3-small
A0_SET_agent_profile=${SELECTED_PROFILE}
ENV_EXT

# --- 3. Matrix Config ---
# NOTE: Continuwuity configured via docker-compose env vars; no dendrite.yaml needed
# sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
# touch "${INSTANCE_DIR}/mhs/matrix_key.pem"
# 
# --- 4. Startup Services ---
mkdir -p "${INSTANCE_DIR}/usr/workdir/matrix-bot"
if [ -f "${TEMPLATE_DIR}/startup-services.sh.template" ]; then
    cp "${TEMPLATE_DIR}/startup-services.sh.template" "${INSTANCE_DIR}/usr/workdir/startup-services.sh"
    chmod +x "${INSTANCE_DIR}/usr/workdir/startup-services.sh"
fi

# --- 5. Agent Settings (MCP server definitions) ---
# Generate settings.json with Matrix + open-brain MCP definitions.
# The __MATRIX_ACCESS_TOKEN__ placeholder will be replaced by
# sync-mcp-token-into-settings.py on first boot once the MCP .env
# has a real token from Matrix user registration.
if [ -f "${TEMPLATE_DIR}/settings.json.template" ]; then
    sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
        -e "s/__MATRIX_ACCESS_TOKEN__/PENDING_TOKEN_SYNC/g" \
        "${TEMPLATE_DIR}/settings.json.template" > "${INSTANCE_DIR}/usr/settings.json"
    echo "📋 Generated settings.json with MCP server definitions"
fi

echo "============================================="
echo "✅ ${INSTANCE_NAME} created with flavor: ${SELECTED_PROFILE}"
echo "============================================="
