#!/usr/bin/env bash
# =============================================================================
# create-instance.sh — Agent Zero + Matrix Sovereign (v3.16 Full-Stack Edition)
# Host: g2s.cybertribe.com
# =============================================================================
set -euo pipefail

# --- Initialization (Prevents Unbound Variable errors) ---
BASE_DIR="/opt/agent-zero"
TEMPLATE_DIR="$(cd "$(dirname "$0")" && pwd)/templates"
SELECTED_PROFILE="agent0"
INSTANCE_NUM=""
INSTANCE_NAME=""
INSTANCE_DIR=""

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
  Network: Agent IP .88.N, Dendrite IP .89.N

Deployment includes:
  - Docker Compose (agent + Dendrite homeserver)
  - Matrix identity key + self-signed TLS certs
  - matrix-mcp-server (outbound Matrix tools)
  - matrix-bot (inbound Matrix message routing)
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

if [[ -z "${INSTANCE_NUM}" ]]; then usage; fi

# --- Derived Values ---
INSTANCE_NAME="agent0-${INSTANCE_NUM}"
INSTANCE_DIR="${BASE_DIR}/${INSTANCE_NAME}"
MAC_SUFFIX=$(printf '%02X' "$INSTANCE_NUM")
WEB_PORT=$((50000 + INSTANCE_NUM))
SSH_PORT=$((50021 + INSTANCE_NUM))

echo "============================================="
echo "Creating ${INSTANCE_NAME} (profile: ${SELECTED_PROFILE})"
echo "   Directory: ${INSTANCE_DIR}"
echo "============================================="

# --- Directories ---
mkdir -p "${INSTANCE_DIR}/usr/workdir" "${INSTANCE_DIR}/mhs/data"

# --- 1. Compose Generation ---
echo "[1/8] Generating docker-compose.yml..."
sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
    -e "s/__MAC_SUFFIX__/${MAC_SUFFIX}/g" \
    -e "s/__WEB_PORT__/${WEB_PORT}/g" \
    -e "s/__SSH_PORT__/${SSH_PORT}/g" \
    "${TEMPLATE_DIR}/docker-compose.yml.template" > "${INSTANCE_DIR}/docker-compose.yml"

# --- 2. .env Generation & Key Injection ---
echo "[2/8] Generating .env file..."
cp "${TEMPLATE_DIR}/env.template" "${INSTANCE_DIR}/.env"
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

# --- 3. Matrix Config & Identity Key ---
echo "[3/8] Configuring Matrix homeserver..."
sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
    "${TEMPLATE_DIR}/dendrite.yaml.template" > "${INSTANCE_DIR}/mhs/dendrite.yaml"
sed -i 's/connection:/connection_string:/g' "${INSTANCE_DIR}/mhs/dendrite.yaml"

# --- 4. Matrix Identity Key ---
echo "[4/8] Generating Matrix identity key..."
KEY_FILE="${INSTANCE_DIR}/mhs/matrix_key.pem"
python3 -c "
import base64, os, string, random
seed = os.urandom(32)
chars = string.ascii_letters + string.digits
key_id = ''.join(random.choices(chars, k=6))
key_b64 = base64.b64encode(seed).decode()
lines = []
lines.append('-----BEGIN MATRIX PRIVATE KEY-----')
lines.append('Key-ID: ed25519:' + key_id)
lines.append('')
lines.append(key_b64)
lines.append('-----END MATRIX PRIVATE KEY-----')
with open('$KEY_FILE', 'w') as f:
    f.write(chr(10).join(lines) + chr(10))
print('  Key generated: ed25519:' + key_id)
"
chmod 600 "${KEY_FILE}"

# --- 5. Self-signed TLS Certs ---
echo "[5/8] Generating placeholder TLS certificates..."
openssl req -x509 -newkey ed25519 -keyout "${INSTANCE_DIR}/mhs/server.key" \
  -out "${INSTANCE_DIR}/mhs/server.crt" -days 365 -nodes \
  -subj "/CN=agent0-${INSTANCE_NUM}-mhs.cybertribe.com" 2>/dev/null
chmod 600 "${INSTANCE_DIR}/mhs/server.key"
echo "  (Self-signed — replace with step-ca certs for federation)"

# --- 6. Matrix Account Credentials ---
echo "[6/8] Generating Matrix account credentials..."
MATRIX_USER="agent0-${INSTANCE_NUM}"
MATRIX_PASS=$(openssl rand -base64 24)
A0_API_KEY=$(openssl rand -base64 12 | tr -d '/+=' | head -c 16)
echo "  User: @${MATRIX_USER}:agent0-${INSTANCE_NUM}-mhs.cybertribe.com"

cat << MATRIX_ENV >> "${INSTANCE_DIR}/.env"

# --- Matrix Account (auto-generated) ---
MATRIX_USERNAME=${MATRIX_USER}
MATRIX_PASSWORD=${MATRIX_PASS}
MATRIX_HOMESERVER_URL=http://agent0-${INSTANCE_NUM}-mhs:8008
MATRIX_USER_ID=@${MATRIX_USER}:agent0-${INSTANCE_NUM}-mhs.cybertribe.com

# --- Agent Zero API Key (for matrix-bot) ---
A0_API_KEY=${A0_API_KEY}
MATRIX_ENV

# --- 7. Deploy matrix-mcp-server ---
echo "[7/9] Deploying matrix-mcp-server template..."
MCP_DIR="${INSTANCE_DIR}/usr/workdir/matrix-mcp-server"
if [ -d "${TEMPLATE_DIR}/matrix-mcp-server" ]; then
    cp -r "${TEMPLATE_DIR}/matrix-mcp-server" "${MCP_DIR}"
    # Configure .env from template
    if [ -f "${MCP_DIR}/.env.template" ]; then
        sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
            -e "s/__MATRIX_ACCESS_TOKEN__/PENDING_REGISTRATION/g" \
            "${MCP_DIR}/.env.template" > "${MCP_DIR}/.env"
        rm -f "${MCP_DIR}/.env.template"
    fi
    echo "  Deployed to usr/workdir/matrix-mcp-server/"
else
    echo "  WARNING: matrix-mcp-server template not found, skipping"
fi

# --- 8. Deploy matrix-bot ---
echo "[8/9] Deploying matrix-bot template..."
BOT_DIR="${INSTANCE_DIR}/usr/workdir/matrix-bot"
if [ -d "${TEMPLATE_DIR}/matrix-bot" ]; then
    cp -r "${TEMPLATE_DIR}/matrix-bot" "${BOT_DIR}"
    # Configure .env from template
    if [ -f "${BOT_DIR}/.env.template" ]; then
        sed -e "s/__INSTANCE_NUM__/${INSTANCE_NUM}/g" \
            -e "s/__MATRIX_ACCESS_TOKEN__/PENDING_REGISTRATION/g" \
            -e "s/__A0_API_KEY__/${A0_API_KEY}/g" \
            "${BOT_DIR}/.env.template" > "${BOT_DIR}/.env"
        rm -f "${BOT_DIR}/.env.template"
    fi
    echo "  Deployed to usr/workdir/matrix-bot/"
else
    echo "  WARNING: matrix-bot template not found, skipping"
fi

# --- 9. Deploy startup-services.sh ---
echo "[9/9] Deploying startup-services.sh..."
if [ -f "${TEMPLATE_DIR}/scripts/startup-services.sh" ]; then
    cp "${TEMPLATE_DIR}/scripts/startup-services.sh" "${INSTANCE_DIR}/usr/workdir/startup-services.sh"
    chmod +x "${INSTANCE_DIR}/usr/workdir/startup-services.sh"
    echo "  Deployed to usr/workdir/startup-services.sh"
else
    echo "  WARNING: startup-services.sh template not found, skipping"
fi

# --- Summary ---
echo ""
echo "============================================="
echo "${INSTANCE_NAME} created (v3.16 Full-Stack)!"
echo "   Profile:  ${SELECTED_PROFILE}"
echo "   Web UI:   port ${WEB_PORT}"
echo "   SSH:      port ${SSH_PORT}"
echo "   Agent IP: 172.23.88.${INSTANCE_NUM}"
echo "   MHS IP:   172.23.89.${INSTANCE_NUM}"
echo "============================================="
echo ""
echo "Next steps:"
echo "  1. cd ${INSTANCE_DIR} && docker compose up -d"
echo ""
echo "  2. Register Matrix account:"
echo "     docker exec -it ${INSTANCE_NAME}-mhs /usr/bin/create-account \\"
echo "       -config /etc/dendrite/dendrite.yaml \\"
echo "       -username ${MATRIX_USER} -password '${MATRIX_PASS}' -admin"
echo ""
echo "  3. Update access token in MCP & bot configs:"
echo "     # After step 2, copy the AccessToken from the output and run:"
echo "     sed -i 's/PENDING_REGISTRATION/<token>/' ${MCP_DIR}/.env"
echo "     sed -i 's/PENDING_REGISTRATION/<token>/' ${BOT_DIR}/.env"
echo ""
echo "  4. Replace self-signed TLS certs with step-ca certs:"
echo "     scp server.crt server.key g2s:${INSTANCE_DIR}/mhs/"
echo ""
echo "  5. Install deps & start services inside agent container:"
echo "     docker exec -it ${INSTANCE_NAME} bash"
echo "     cd /a0/usr/workdir/matrix-mcp-server && npm install && node dist/index.js &"
echo "     cd /a0/usr/workdir/matrix-bot && pip install -r requirements.txt && python3 matrix_bot.py &"
echo "     cd /a0/usr/workdir/matrix-bot && /opt/venv-a0/bin/pip install -r requirements.txt && /opt/venv-a0/bin/python3 matrix_bot.py &"
echo ""
echo "  6. Configure MCP/A2A in Agent Zero UI (Settings > MCP/A2A):"
echo "     Paste this JSON (replace <token> with actual AccessToken):"
echo '     {'
echo '       "mcpServers": {'
echo '         "matrix": {'
echo '           "type": "streamable-http",'
echo '           "url": "http://localhost:3000/mcp",'
echo '           "headers": {'
echo "             \"matrix_user_id\": \"@${MATRIX_USER}:agent0-${INSTANCE_NUM}-mhs.cybertribe.com\","
echo '             "matrix_access_token": "<token>",'
echo "             \"matrix_homeserver_url\": \"http://agent0-${INSTANCE_NUM}-mhs:8008\""
echo '           }'
echo '         }'
echo '       }'
echo '     }'
echo "============================================="
