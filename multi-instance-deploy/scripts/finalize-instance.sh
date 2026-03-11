#!/usr/bin/env bash
# =============================================================================
# finalize-instance.sh — Post-Deployment Automation (v4.0 Continuwuity Edition)
# =============================================================================
# Automates all manual steps after create-instance.sh:
#   1. Start containers (docker compose up -d)
#   2. Wait for Continuwuity homeserver readiness
#   3. Register Matrix account via bootstrap token (parsed from logs)
#   4. Update access tokens in bot/.env and mcp/.env
#   5. Generate Step-CA TLS certs (if step CLI available)
#   6. Pre-seed Agent Zero settings.json with MCP config
#   7. Restart stack to pick up all changes
#
# IMPORTANT: Continuwuity generates a one-time bootstrap token on first boot.
# This script automatically extracts it from container logs and uses it for
# the first account registration. The configured REGISTRATION_TOKEN only
# becomes active AFTER the first user is created.
#
# Usage: ./finalize-instance.sh <instance-number>
# Example: ./finalize-instance.sh 3
#
# Prerequisites:
#   - create-instance.sh has been run for this instance
#   - Docker is running
#   - Optional: step-ca CLI for TLS cert generation
# =============================================================================
set -euo pipefail

# --- Colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }
info() { echo -e "   $*"; }

# --- Args ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $(basename "$0") <instance-number> [OPTIONS]"
    echo "Example: $(basename "$0") 3 --api-key-openrouter sk-or-v1-..."
    echo ""
    echo "Options:"
    echo "  --api-key-openrouter KEY   OpenRouter API key"
    echo "  --api-key-openai KEY       OpenAI API key"
    echo "  --api-key-anthropic KEY    Anthropic API key"
    echo "  --api-key-google KEY       Google API key"
    echo "  --api-key-groq KEY         Groq API key"
    echo "  --api-key NAME=VALUE       Any other API key"
    exit 1
fi

INSTANCE_NUM="$1"
shift

# Parse optional named arguments
declare -A API_KEYS
while [[ $# -gt 0 ]]; do
    case "$1" in
        --api-key-openrouter) API_KEYS[OPENROUTER]="$2"; shift 2 ;;
        --api-key-openai)     API_KEYS[OPENAI]="$2"; shift 2 ;;
        --api-key-anthropic)  API_KEYS[ANTHROPIC]="$2"; shift 2 ;;
        --api-key-google)     API_KEYS[GOOGLE]="$2"; shift 2 ;;
        --api-key-groq)       API_KEYS[GROQ]="$2"; shift 2 ;;
        --api-key)
            IFS="=" read -r _KN _KV <<< "$2"
            API_KEYS[${_KN^^}]="$_KV"
            shift 2 ;;
        *) fail "Unknown argument: $1" ;;
    esac
done
BASE_DIR="/opt/agent-zero"
INSTANCE_NAME="agent0-${INSTANCE_NUM}"
INSTANCE_DIR="${BASE_DIR}/${INSTANCE_NAME}"
MHS_NAME="agent0-${INSTANCE_NUM}-mhs"
MHS_FQDN="${MHS_NAME}.cybertribe.com"
MHS_IP="172.23.89.${INSTANCE_NUM}"
CONTINUWUITY_CONTAINER="${INSTANCE_NAME}-continuwuity"
MATRIX_USER="agent0-${INSTANCE_NUM}"
BOT_ENV="${INSTANCE_DIR}/usr/workdir/matrix-bot/.env"
MCP_ENV="${INSTANCE_DIR}/usr/workdir/matrix-mcp-server/.env"
SETTINGS_JSON="${INSTANCE_DIR}/usr/settings.json"

echo "============================================="
echo "Finalizing ${INSTANCE_NAME}"
echo "   Directory: ${INSTANCE_DIR}"
echo "   MHS: ${MHS_FQDN}"
echo "============================================="
echo

# --- Preflight ---
[[ -d "${INSTANCE_DIR}" ]] || fail "Instance directory not found: ${INSTANCE_DIR}"
[[ -f "${INSTANCE_DIR}/docker-compose.yml" ]] || fail "docker-compose.yml not found. Run create-instance.sh first."
[[ -f "${BOT_ENV}" ]] || fail "Bot .env not found: ${BOT_ENV}"
[[ -f "${MCP_ENV}" ]] || fail "MCP .env not found: ${MCP_ENV}"

# --- Read credentials from .env ---
source_env() {
    local file="$1" key="$2"
    grep -E "^${key}=" "$file" 2>/dev/null | tail -n1 | cut -d= -f2-
}

MATRIX_PASS=$(source_env "${INSTANCE_DIR}/.env" MATRIX_PASSWORD)
# A0_API_KEY computed after container startup (see Step 6.5)

[[ -n "$MATRIX_PASS" ]] || fail "MATRIX_PASSWORD not found in .env"

echo "Credentials loaded from .env files."

# Deploy API keys to instance .env if provided via CLI
if [[ ${#API_KEYS[@]} -gt 0 ]]; then
    info "Deploying ${#API_KEYS[@]} API key(s) to instance .env..."
    for _KEYNAME in "${!API_KEYS[@]}"; do
        _KEYVAR="API_KEY_${_KEYNAME}"
        _KEYVAL="${API_KEYS[$_KEYNAME]}"
        sed -i "/^${_KEYVAR}=/d;/^# ${_KEYVAR}=/d" "${INSTANCE_DIR}/.env"
        echo "${_KEYVAR}=${_KEYVAL}" >> "${INSTANCE_DIR}/.env"
        ok "Set ${_KEYVAR}=${_KEYVAL:0:15}..."
    done
fi

# Compute the mcp_server_token the same way Agent Zero does
compute_a0_token() {
    local instance_dir="$1"
    # Wait for runtime ID to be generated
    local RUNTIME_ID=""
    for i in $(seq 1 30); do
        RUNTIME_ID=$(docker exec ${INSTANCE_NAME} grep -oP 'A0_PERSISTENT_RUNTIME_ID=\K.*' /a0/usr/.env 2>/dev/null)
        if [[ -n "$RUNTIME_ID" ]]; then break; fi
        sleep 2
    done
    if [[ -z "$RUNTIME_ID" ]]; then
        fail "Could not read A0_PERSISTENT_RUNTIME_ID from container"
        return 1
    fi
    # Read auth credentials (empty for bot-only instances)
    local AUTH_USER=$(docker exec ${INSTANCE_NAME} grep -oP 'AUTH_LOGIN=\K.*' /a0/usr/.env 2>/dev/null || echo "")
    local AUTH_PASS=$(docker exec ${INSTANCE_NAME} grep -oP 'AUTH_PASSWORD=\K.*' /a0/usr/.env 2>/dev/null || echo "")
    # Compute token: base64url(sha256(runtime_id:user:pass))[:16]
    local TOKEN=$(python3 -c "
import hashlib, base64
hash_bytes = hashlib.sha256(f'${RUNTIME_ID}:${AUTH_USER}:${AUTH_PASS}'.encode()).digest()
b64 = base64.urlsafe_b64encode(hash_bytes).decode().replace('=', '')
print(b64[:16])
")
    echo "$TOKEN"
}
echo

# =========================================================================
# STEP 1: Start containers
# =========================================================================
echo "[1/7] Starting containers..."
cd "${INSTANCE_DIR}"

# Export API keys from .env so docker compose doesn't warn
set -a
[[ -f .env ]] && source .env
set +a

docker compose up -d 2>&1 | grep -v "^$"
ok "Containers started"
echo

# =========================================================================
# STEP 2: Wait for Continuwuity homeserver
# =========================================================================
echo "[2/7] Waiting for Continuwuity homeserver..."
READY=0
for i in $(seq 1 30); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${MHS_IP}:8008/_matrix/client/versions" 2>/dev/null)
    if [[ "${HTTP_CODE}" == "200" ]]; then
        READY=1
        break
    fi
    echo -n "."
    sleep 2
done
echo
[[ "$READY" -eq 1 ]] || fail "Homeserver did not become ready after 60s"
ok "Homeserver ready (attempt ${i})"
echo

# =========================================================================
# STEP 3: Register Matrix account
# =========================================================================
echo "[3/7] Registering Matrix account: @${MATRIX_USER}:${MHS_FQDN}"

# Check if already registered by attempting login
LOGIN_RESP=$(curl -s -X POST "http://${MHS_IP}:8008/_matrix/client/v3/login" \
    -H 'Content-Type: application/json' \
    -d "{\"type\": \"m.login.password\", \"identifier\": {\"type\": \"m.id.user\", \"user\": \"${MATRIX_USER}\"}, \"password\": \"${MATRIX_PASS}\"}" 2>/dev/null)

if echo "$LOGIN_RESP" | grep -q '"access_token"'; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
    ok "Account already registered — logged in successfully"
else
    info "Account not yet registered. Extracting bootstrap token from Continuwuity logs..."

    # --- Continuwuity Bootstrap Token Discovery ---
    # Continuwuity generates a one-time bootstrap token on first boot.
    # The configured REGISTRATION_TOKEN only becomes active AFTER the
    # first account is created using this bootstrap token.
    BOOTSTRAP_TOKEN=""
    for attempt in $(seq 1 10); do
        BOOTSTRAP_TOKEN=$(docker logs "${CONTINUWUITY_CONTAINER}" 2>&1 | \
            grep -oP 'registration token \K[A-Za-z0-9]+' | tail -1)
        if [[ -n "$BOOTSTRAP_TOKEN" ]]; then
            break
        fi
        echo -n "."
        sleep 2
    done
    echo

    [[ -n "$BOOTSTRAP_TOKEN" ]] || fail "Could not extract bootstrap token from Continuwuity logs"
    info "Bootstrap token: ${BOOTSTRAP_TOKEN}"

    # --- UIAA Registration Flow ---
    # Step 3a: Get UIAA session (no auth)
    REG_RESP1=$(curl -s -X POST "http://${MHS_IP}:8008/_matrix/client/v3/register" \
        -H 'Content-Type: application/json' \
        -d "{\"username\": \"${MATRIX_USER}\", \"password\": \"${MATRIX_PASS}\"}" 2>/dev/null)

    if echo "$REG_RESP1" | grep -q '"access_token"'; then
        # Open registration — got token directly
        ACCESS_TOKEN=$(echo "$REG_RESP1" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
        ok "Account registered (open registration)"
    elif echo "$REG_RESP1" | grep -q '"session"'; then
        SESSION_ID=$(echo "$REG_RESP1" | python3 -c "import sys,json; print(json.load(sys.stdin)['session'])")
        info "Got UIAA session: ${SESSION_ID}"

        # Step 3b: Complete registration with bootstrap token + session
        REG_RESP2=$(curl -s -X POST "http://${MHS_IP}:8008/_matrix/client/v3/register" \
            -H 'Content-Type: application/json' \
            -d "{\"username\": \"${MATRIX_USER}\", \"password\": \"${MATRIX_PASS}\", \"auth\": {\"type\": \"m.login.registration_token\", \"token\": \"${BOOTSTRAP_TOKEN}\", \"session\": \"${SESSION_ID}\"}}" 2>/dev/null)

        if echo "$REG_RESP2" | grep -q '"access_token"'; then
            ACCESS_TOKEN=$(echo "$REG_RESP2" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
            ok "Account registered (UIAA + bootstrap token)"
        else
            echo "$REG_RESP2"
            fail "Registration failed. Check response above."
        fi
    else
        echo "$REG_RESP1"
        fail "Registration failed. Check response above."
    fi
fi

info "Access token: ${ACCESS_TOKEN:0:20}..."
echo

# =========================================================================
# STEP 4: Update access tokens in bot and MCP configs
# =========================================================================
echo "[4/7] Updating access tokens..."

# Update bot .env
sed -i "s|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${ACCESS_TOKEN}|" "${BOT_ENV}"
ok "Bot .env updated"

# Update MCP .env
sed -i "s|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${ACCESS_TOKEN}|" "${MCP_ENV}"
ok "MCP .env updated"

# Also update main .env for reference
if grep -q "^MATRIX_ACCESS_TOKEN=" "${INSTANCE_DIR}/.env"; then
    sed -i "s|^MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=${ACCESS_TOKEN}|" "${INSTANCE_DIR}/.env"
else
    echo "MATRIX_ACCESS_TOKEN=${ACCESS_TOKEN}" >> "${INSTANCE_DIR}/.env"
fi
ok "Main .env updated"
echo

# =========================================================================
# STEP 5: Generate Step-CA TLS certs (automated)
# =========================================================================
echo "[5/7] TLS certificate generation..."

STEP_CA_PASSWD_FILE="${BASE_DIR}/multi-instance-deploy/scripts/step_ca_provisioner_passwd"

if command -v step &>/dev/null; then
    info "step CLI found — checking existing certificates"

    # Check if certs already exist and are CA-signed
    EXISTING_ISSUER=$(openssl x509 -in "${INSTANCE_DIR}/mhs/server.crt" -noout -issuer 2>/dev/null || echo "")
    if echo "$EXISTING_ISSUER" | grep -q "CyberTribe CA"; then
        CERT_COUNT=$(grep -c 'BEGIN CERTIFICATE' "${INSTANCE_DIR}/mhs/server.crt" 2>/dev/null || echo 0)
        ok "Step-CA certificates already present (${CERT_COUNT} certs in bundle) — skipping"
    else
        info "Generating Step-CA certificate for ${MHS_FQDN}..."

        # Build step ca certificate command
        STEP_ARGS=("${MHS_FQDN}"
            "${INSTANCE_DIR}/mhs/server.crt"
            "${INSTANCE_DIR}/mhs/server.key"
            --san "${MHS_FQDN}"
            --not-after=8760h
            --force)

        # Use provisioner password file if available (non-interactive)
        if [[ -f "${STEP_CA_PASSWD_FILE}" ]]; then
            STEP_ARGS+=(--provisioner-password-file "${STEP_CA_PASSWD_FILE}")
            info "Using provisioner password file for non-interactive generation"
        else
            info "No provisioner password file — step will prompt interactively"
        fi

        step ca certificate "${STEP_ARGS[@]}" 2>&1 || warn "Step-CA cert generation failed — using self-signed"

        if [[ -f "${INSTANCE_DIR}/mhs/server.crt" ]]; then
            CERT_COUNT=$(grep -c 'BEGIN CERTIFICATE' "${INSTANCE_DIR}/mhs/server.crt" 2>/dev/null || echo 0)

            # step v0.29.0+ auto-bundles the chain (leaf + intermediate + root)
            # Verify we have at least 3 certs; if not, append root CA manually
            if [[ "$CERT_COUNT" -lt 3 ]]; then
                STEP_CA_ROOT=$(step path)/certs/root_ca.crt
                if [[ -f "$STEP_CA_ROOT" ]]; then
                    cat "$STEP_CA_ROOT" >> "${INSTANCE_DIR}/mhs/server.crt"
                    CERT_COUNT=$(grep -c 'BEGIN CERTIFICATE' "${INSTANCE_DIR}/mhs/server.crt")
                    info "Appended root CA — bundle now has ${CERT_COUNT} certs"
                fi
            fi

            chmod 600 "${INSTANCE_DIR}/mhs/server.key"
            ok "Step-CA certificates generated (${CERT_COUNT} certs in bundle)"

            # Verify chain
            LEAF_ISSUER=$(openssl x509 -in "${INSTANCE_DIR}/mhs/server.crt" -noout -issuer 2>/dev/null)
            info "Cert issuer: ${LEAF_ISSUER}"
        fi
    fi
else
    warn "step CLI not found — using self-signed placeholder certs"
    info "Install step-ca and re-run, or manually copy certs to ${INSTANCE_DIR}/mhs/"
fi
echo

# =========================================================================
# STEP 6: Pre-seed Agent Zero settings.json with MCP config
# =========================================================================
echo "[6/7] Pre-seeding MCP configuration..."

python3 - <<PYEOF
import json
from pathlib import Path

settings_path = Path("${SETTINGS_JSON}")
if settings_path.exists():
    try:
        data = json.loads(settings_path.read_text() or "{}")
    except Exception:
        data = {}
else:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    data = {}

# Set mcp_server_token for API auth
if "${A0_API_KEY}":
    data["mcp_server_token"] = "${A0_API_KEY}"

# Set MCP servers config — NO headers (server reads from own .env)
mcp_config = {
    "matrix": {
        "type": "streamable-http",
        "url": "http://localhost:3000/mcp"
    }
}

# Only set if not already configured (don't overwrite user customizations)
if "mcp_servers" not in data or not data["mcp_servers"]:
    data["mcp_servers"] = json.dumps(mcp_config)
    print("MCP config pre-seeded")
else:
    print("MCP config already exists — preserving")

settings_path.write_text(json.dumps(data, indent=2))
print("settings.json updated")
PYEOF

ok "Settings pre-seeded"
echo

# =========================================================================
# STEP 7: Restart stack to pick up all changes
# =========================================================================
echo "[7/7] Restarting stack with final configuration..."
cd "${INSTANCE_DIR}"

# Export API keys from .env so docker compose doesn't warn
set -a
source .env
set +a

docker compose down 2>&1 | tail -5
sleep 3
docker compose up -d 2>&1 | tail -5

# Wait for services to stabilize
echo "Waiting 30s for services to stabilize..."
sleep 30

# =========================================================================
# STEP 7b: Compute and deploy correct A0 API token
# =========================================================================
echo "[7b] Computing A0 API token from runtime ID..."
RUNTIME_ID=""
for i in $(seq 1 15); do
    RUNTIME_ID=$(docker exec ${INSTANCE_NAME} grep -oP 'A0_PERSISTENT_RUNTIME_ID=\K.*' /a0/usr/.env 2>/dev/null)
    [[ -n "$RUNTIME_ID" ]] && break
    sleep 2
done
if [[ -z "$RUNTIME_ID" ]]; then
    warn "Could not read runtime ID - bot may need manual token sync"
else
    COMPUTED_TOKEN=$(python3 -c "
import hashlib, base64
hash_bytes = hashlib.sha256(f'${RUNTIME_ID}::'.encode()).digest()
print(base64.urlsafe_b64encode(hash_bytes).decode().replace('=','')[:16])
")
    info "Runtime ID: $RUNTIME_ID"
    info "Computed token: $COMPUTED_TOKEN"
    sed -i "s|^A0_API_KEY=.*|A0_API_KEY=${COMPUTED_TOKEN}|" "${BOT_ENV}"
    sed -i "s|^A0_API_KEY=.*|A0_API_KEY=${COMPUTED_TOKEN}|" "${MCP_ENV}"
    ok "API token deployed to bot and MCP .env files"
fi

# Quick health check
echo
echo "============================================="
echo "Post-finalization health check"
echo "============================================="

# Check containers
for c in "${INSTANCE_NAME}" "${CONTINUWUITY_CONTAINER}" "${INSTANCE_NAME}-mhs"; do
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
        ok "Container ${c} running"
    else
        warn "Container ${c} NOT running"
    fi
done

# Check homeserver
HS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${MHS_IP}:8008/_matrix/client/versions" 2>/dev/null)
if [[ "$HS_CODE" == "200" ]]; then
    ok "Homeserver client API (8008): ${HS_CODE}"
else
    warn "Homeserver client API (8008): ${HS_CODE}"
fi

# Check federation
FED_CODE=$(curl -ks -o /dev/null -w "%{http_code}" "https://${MHS_IP}:8448/_matrix/key/v2/server" 2>/dev/null)
if [[ "$FED_CODE" == "200" ]]; then
    ok "Federation API (8448 TLS): ${FED_CODE}"
else
    warn "Federation API (8448 TLS): ${FED_CODE}"
fi

# Check services inside container
BOT_RUNNING=$(docker exec "${INSTANCE_NAME}" pgrep -f matrix_bot.py 2>/dev/null || echo "")
MCP_RUNNING=$(docker exec "${INSTANCE_NAME}" pgrep -f 'node dist/http-server.js' 2>/dev/null || echo "")

if [[ -n "$MCP_RUNNING" ]]; then
    ok "MCP server running (PID ${MCP_RUNNING})"
else
    warn "MCP server NOT running"
fi

if [[ -n "$BOT_RUNNING" ]]; then
    ok "Matrix bot running (PID ${BOT_RUNNING})"
else
    warn "Matrix bot NOT running (may need startup time)"
fi

echo
echo "============================================="
echo "${INSTANCE_NAME} finalization complete!"
echo "============================================="
echo
echo "Matrix ID: @${MATRIX_USER}:${MHS_FQDN}"
echo "Agent IP:  172.23.88.${INSTANCE_NUM}"
echo "MHS IP:    ${MHS_IP}"
echo "Access:    ${ACCESS_TOKEN:0:20}..."
echo
echo "Remaining manual step:"
echo "  → Invite @${MATRIX_USER}:${MHS_FQDN} to Fleet HQ room from Element"
echo
echo "============================================="
