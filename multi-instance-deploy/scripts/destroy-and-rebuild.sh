#!/usr/bin/env bash
# =============================================================================
# destroy-and-rebuild.sh — Full Instance Lifecycle (v4.0 Continuwuity Edition)
# =============================================================================
# Completely destroys an agent instance and rebuilds it from scratch.
# Handles federation key cache clearing on Synapse and peer agents.
#
# Usage: ./destroy-and-rebuild.sh <instance-number> [OPTIONS]
# Example: ./destroy-and-rebuild.sh 3 --api-key-openrouter sk-or-v1-...
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }
info() { echo -e "${CYAN}ℹ️  $*${NC}"; }
step() { echo -e "\n${CYAN}━━━ Step $1: $2 ━━━${NC}"; }

if [[ $# -lt 1 ]]; then
    echo "Usage: $(basename "$0") <instance-number> [OPTIONS]"
    echo "Example: $(basename "$0") 3 --api-key-openrouter sk-or-v1-..."
    echo ""
    echo "Options (passed through to finalize-instance.sh):"
    echo "  --api-key-openrouter KEY   OpenRouter API key"
    echo "  --api-key-openai KEY       OpenAI API key"
    echo "  --api-key NAME=VALUE       Any other API key"
    echo "  --skip-synapse-purge       Skip Synapse key cache purge"
    echo "  --no-confirm               Skip confirmation prompt"
    exit 1
fi

INSTANCE_NUM="$1"
shift

SKIP_SYNAPSE_PURGE=false
NO_CONFIRM=false
FINALIZE_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-synapse-purge) SKIP_SYNAPSE_PURGE=true; shift ;;
        --no-confirm)         NO_CONFIRM=true; shift ;;
        --api-key-openrouter|--api-key-openai|--api-key-anthropic|--api-key-google|--api-key-groq|--api-key)
            FINALIZE_ARGS+=("$1" "$2"); shift 2 ;;
        *) fail "Unknown argument: $1" ;;
    esac
done

BASE_DIR="/opt/agent-zero"
DEPLOY_DIR="${BASE_DIR}/multi-instance-deploy"
INSTANCE_NAME="agent0-${INSTANCE_NUM}"
INSTANCE_DIR="${BASE_DIR}/${INSTANCE_NAME}"
MHS_NAME="${INSTANCE_NAME}-mhs"
MHS_FQDN="${MHS_NAME}.cybertribe.com"
MHS_IP="172.23.89.${INSTANCE_NUM}"
ARCHIVE_DIR="${BASE_DIR}/archive"

echo "================================================"
echo " DESTROY AND REBUILD: ${INSTANCE_NAME}"
echo "   Instance dir: ${INSTANCE_DIR}"
echo "   Homeserver:   ${MHS_FQDN}"
echo "   MHS IP:       ${MHS_IP}"
echo "================================================"
echo

if [[ "${NO_CONFIRM}" != "true" ]]; then
    echo -e "${RED}⚠️  This will COMPLETELY DESTROY ${INSTANCE_NAME}!${NC}"
    echo "   - All containers and volumes will be removed"
    echo "   - All agent data, memories, and chat history will be lost"
    echo "   - Matrix identity and signing keys will be regenerated"
    echo
    read -p "Type '${INSTANCE_NAME}' to confirm: " CONFIRM
    [[ "${CONFIRM}" == "${INSTANCE_NAME}" ]] || fail "Aborted."
    echo
fi

# =============================================
# PHASE 1: DESTROY
# =============================================

step 1 "Leave Matrix rooms gracefully"
if [[ -d "${INSTANCE_DIR}" ]] && docker ps --format '{{.Names}}' | grep -q "^${INSTANCE_NAME}$"; then
    BOT_ENV="${INSTANCE_DIR}/usr/workdir/matrix-bot/.env"
    if [[ -f "${BOT_ENV}" ]]; then
    set +e
    source "${BOT_ENV}" 2>/dev/null
    set -e
        MX_TOKEN="${MATRIX_ACCESS_TOKEN:-}"
        if [[ -n "${MX_TOKEN}" ]]; then
            info "Fetching joined rooms..."
            ROOMS=$(curl -sf "http://${MHS_IP}:8008/_matrix/client/v3/joined_rooms" \
                -H "Authorization: Bearer ${MX_TOKEN}" 2>/dev/null | \
                python3 -c "import sys,json; [print(r) for r in json.load(sys.stdin).get('joined_rooms',[])]" 2>/dev/null) || true
            if [[ -n "${ROOMS}" ]]; then
                while IFS= read -r ROOM_ID; do
                    info "Leaving ${ROOM_ID}..."
                    curl -sf -X POST "http://${MHS_IP}:8008/_matrix/client/v3/rooms/${ROOM_ID}/leave" \
                        -H "Authorization: Bearer ${MX_TOKEN}" \
                        -H "Content-Type: application/json" -d '{}' >/dev/null 2>&1 || true
                done <<< "${ROOMS}"
                ok "Left all rooms"
            else
                warn "No rooms found or could not query"
            fi
        else
            warn "No access token found, skipping room leave"
        fi
    else
        warn "Bot .env not found, skipping room leave"
    fi
else
    warn "Instance not running, skipping room leave"
fi

step 2 "Stop and remove containers + volumes"
if [[ -d "${INSTANCE_DIR}" ]] && [[ -f "${INSTANCE_DIR}/docker-compose.yml" ]]; then
    cd "${INSTANCE_DIR}"
    set -a && source .env 2>/dev/null && set +a
    docker compose down -v --remove-orphans 2>&1 | tail -5
    ok "Containers and volumes removed"
else
    warn "No docker-compose.yml found, cleaning up containers manually..."
    for C in "${INSTANCE_NAME}" "${INSTANCE_NAME}-continuwuity" "${INSTANCE_NAME}-mhs"; do
        docker rm -f "${C}" 2>/dev/null || true
    done
fi

step 3 "Archive and delete instance directory"
if [[ -d "${INSTANCE_DIR}" ]]; then
    mkdir -p "${ARCHIVE_DIR}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ARCHIVE_FILE="${ARCHIVE_DIR}/${INSTANCE_NAME}_${TIMESTAMP}.tar.gz"
    # Docker creates root-owned files inside instance dirs.
    # Use a throwaway Alpine container so archive+delete works
    # regardless of which user runs this script (no sudo needed).
    info "Archiving to ${ARCHIVE_FILE} (via Docker)..."
    docker run --rm \
        -v "${BASE_DIR}:/host" \
        -v "${ARCHIVE_DIR}:/archive" \
        alpine:3.19 \
        tar -czf "/archive/${INSTANCE_NAME}_${TIMESTAMP}.tar.gz" \
            -C /host "${INSTANCE_NAME}" 2>/dev/null || true

    info "Removing ${INSTANCE_DIR} (via Docker)..."
    docker run --rm \
        -v "${BASE_DIR}:/host" \
        alpine:3.19 \
        rm -rf "/host/${INSTANCE_NAME}"
    ok "Archived and deleted ${INSTANCE_DIR}"
else
    warn "Instance directory not found: ${INSTANCE_DIR}"
fi

step 4 "Purge Synapse federation key cache"
if [[ "${SKIP_SYNAPSE_PURGE}" == "true" ]]; then
    warn "Skipping Synapse purge (--skip-synapse-purge)"
else
    info "Starting kubectl port-forward to Synapse..."
    kubectl port-forward -n matrix svc/matrix-synapse 18008:80 &
    PF_PID=$!
    sleep 3

    if kill -0 ${PF_PID} 2>/dev/null; then
        SYNAPSE_ADMIN_TOKEN="${SYNAPSE_ADMIN_TOKEN:-}"
        if [[ -z "${SYNAPSE_ADMIN_TOKEN}" ]]; then
            for F in "${DEPLOY_DIR}/scripts/synapse_admin_token" \
                     "${HOME}/.synapse_admin_token"; do
                if [[ -f "${F}" ]]; then
                    SYNAPSE_ADMIN_TOKEN=$(cat "${F}")
                    info "Loaded admin token from ${F}"
                    break
                fi
            done
        fi

        if [[ -n "${SYNAPSE_ADMIN_TOKEN}" ]]; then
            info "Resetting federation destination for ${MHS_FQDN}..."
            HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' \
                -X DELETE "http://localhost:18008/_synapse/admin/v1/federation/destinations/${MHS_FQDN}" \
                -H "Authorization: Bearer ${SYNAPSE_ADMIN_TOKEN}" 2>/dev/null) || HTTP_CODE="000"

            if [[ "${HTTP_CODE}" == "200" ]]; then
                ok "Synapse federation destination cleared for ${MHS_FQDN}"
            else
                warn "Synapse returned HTTP ${HTTP_CODE} (may not have cached entry)"
            fi

            info "Purging remote signing keys cache..."
            curl -sf -X POST "http://localhost:18008/_synapse/admin/v1/purge_remote_signing_keys" \
                -H "Authorization: Bearer ${SYNAPSE_ADMIN_TOKEN}" \
                -H "Content-Type: application/json" 2>/dev/null && \
                ok "Remote signing keys purged" || warn "Purge endpoint not available"
        else
            warn "No SYNAPSE_ADMIN_TOKEN found."
            warn "Create: ${DEPLOY_DIR}/scripts/synapse_admin_token"
            warn "Or set env: export SYNAPSE_ADMIN_TOKEN=syt_..."
        fi

        kill ${PF_PID} 2>/dev/null
        wait ${PF_PID} 2>/dev/null || true
    else
        warn "kubectl port-forward failed. Is kubectl configured?"
    fi
fi

step 5 "Restart peer Continuwuity instances (flush key caches)"
for PEER_NUM in 1 2 3 4 5; do
    [[ "${PEER_NUM}" == "${INSTANCE_NUM}" ]] && continue
    PEER_CONTAINER="agent0-${PEER_NUM}-continuwuity"
    if docker ps --format '{{.Names}}' | grep -q "^${PEER_CONTAINER}$"; then
        info "Restarting ${PEER_CONTAINER}..."
        docker restart "${PEER_CONTAINER}" >/dev/null 2>&1
        ok "${PEER_CONTAINER} restarted"
    fi
done

# =============================================
# PHASE 2: REBUILD
# =============================================

step 6 "Rebuild instance with create-instance.sh"
cd "${DEPLOY_DIR}"
./create-instance.sh "${INSTANCE_NUM}"
ok "Instance scaffolded"

step 7 "Finalize instance"
if [[ ${#FINALIZE_ARGS[@]} -gt 0 ]]; then
    info "Passing to finalize: ${FINALIZE_ARGS[*]}"
fi
if [[ ${#FINALIZE_ARGS[@]} -gt 0 ]]; then
    ./scripts/finalize-instance.sh "${INSTANCE_NUM}" "${FINALIZE_ARGS[@]}"
else
    ./scripts/finalize-instance.sh "${INSTANCE_NUM}"
fi
ok "Instance finalized"

step 8 "Verify federation endpoint"
sleep 5
info "Testing federation at https://${MHS_IP}:8448..."
FED_RESPONSE=$(curl -ksf "https://${MHS_IP}:8448/_matrix/key/v2/server" 2>/dev/null) || true
if echo "${FED_RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['server_name']=='${MHS_FQDN}'" 2>/dev/null; then
    ok "Federation endpoint verified: ${MHS_FQDN}"
else
    warn "Federation not yet ready. Check TLS certs (finalize output above)."
fi

echo
echo "================================================"
echo -e "${GREEN} REBUILD COMPLETE: ${INSTANCE_NAME}${NC}"
echo "================================================"
echo
echo "Next steps:"
echo "  1. Invite @agent0-${INSTANCE_NUM}:${MHS_FQDN} to Fleet HQ Clean from Element"
echo "  2. Verify ping response in the room"
echo
