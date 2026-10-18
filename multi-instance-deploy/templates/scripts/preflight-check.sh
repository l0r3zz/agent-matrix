#!/usr/bin/env bash
# =============================================================================
# preflight-check.sh — Fail-Closed Startup Preflight Gate (Phase 8)
# =============================================================================
# Validates an agent's Matrix identity, required room memberships, and canonical
# Agent Zero API authentication against the am-ctl platform API BEFORE the
# Matrix bot is allowed to start syncing.
#
# Sequence:
#   1. Query platform API (/api/v1/agents/{name}) for expected identity & required rooms
#   2. Call Matrix /_matrix/client/v3/account/whoami -- require exact match
#   3. Call Matrix /_matrix/client/v3/joined_rooms -- require all required rooms present
#   4. Probe Agent Zero API (/api/api_message) with canonical .a0-api-key credential
#   5. Report check results to platform API (/api/v1/health/{name}/report);
#      fail closed (exit 1) on any mismatch unless --skip-preflight is passed.
# =============================================================================
set -euo pipefail

SKIP_PREFLIGHT=0
AGENT_NAME="${AGENT_NAME:-$(hostname)}"
AMCTL_URL="${AMCTL_URL:-http://172.23.88.254:8077}"
AMCTL_API_KEY="${AMCTL_API_KEY:-amctl-dev-key-2026}"
BOT_DIR="/a0/usr/workdir/matrix-bot"
BOT_ENV="${BOT_DIR}/.env"
SECRET_FILE="${BOT_DIR}/.a0-api-key"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-preflight)
            SKIP_PREFLIGHT=1
            shift
            ;;
        --agent)
            AGENT_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--skip-preflight] [--agent agent0-N]"
            exit 0
            ;;
        *)
            echo "[preflight] ERROR: Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ "${SKIP_PREFLIGHT}" -eq 1 ]]; then
    echo "[preflight] WARNING: --skip-preflight passed; bypassing preflight checks!" >&2
    exit 0
fi

report_to_platform() {
    local payload="$1"
    curl -sf --max-time 5 -X POST "${AMCTL_URL}/api/v1/health/${AGENT_NAME}/report" \
        -H "X-API-Key: ${AMCTL_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "${payload}" >/dev/null 2>&1 || true
}

# Load Matrix connection settings from bot .env
if [[ ! -f "${BOT_ENV}" ]]; then
    echo "[preflight] FATAL: ${BOT_ENV} not found" >&2
    exit 1
fi

HS_URL="$(grep '^MATRIX_HOMESERVER_URL=' "${BOT_ENV}" | tail -n1 | cut -d= -f2- | tr -d '\r\n"')"
MATRIX_TOKEN="$(grep '^MATRIX_ACCESS_TOKEN=' "${BOT_ENV}" | tail -n1 | cut -d= -f2- | tr -d '\r\n"')"

# 1. Query platform API for expected identity and required rooms
REG_JSON="$(curl -sf --max-time 10 -H "X-API-Key: ${AMCTL_API_KEY}" "${AMCTL_URL}/api/v1/agents/${AGENT_NAME}" 2>/dev/null || echo "")"
if [[ -z "${REG_JSON}" ]]; then
    echo "[preflight] FATAL: Cannot reach am-ctl platform API at ${AMCTL_URL}/api/v1/agents/${AGENT_NAME}" >&2
    exit 1
fi

EXPECTED_USER_ID="$(echo "${REG_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('matrix_user_id',''))")"
REQUIRED_ROOMS_CSV="$(echo "${REG_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(','.join(r['room_id'] for r in d.get('required_rooms',[])))")"

# 2. Call /whoami and require exact match with registry matrix_user_id
WHOAMI_JSON="$(curl -sf --max-time 10 -H "Authorization: Bearer ${MATRIX_TOKEN}" "${HS_URL}/_matrix/client/v3/account/whoami" 2>/dev/null || echo "")"
ACTUAL_USER_ID="$(echo "${WHOAMI_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user_id',''))" 2>/dev/null || echo "")"

if [[ -z "${ACTUAL_USER_ID}" ]]; then
    echo "[preflight] FATAL: Matrix /whoami failed for ${AGENT_NAME}" >&2
    report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"matrix_auth\",\"status\":\"fail\",\"detail\":{\"error\":\"preflight_whoami_failed\"}}]}"
    exit 1
fi

if [[ "${ACTUAL_USER_ID}" != "${EXPECTED_USER_ID}" ]]; then
    echo "[preflight] FATAL: Identity mismatch! /whoami='${ACTUAL_USER_ID}' != expected='${EXPECTED_USER_ID}'" >&2
    report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"identity\",\"status\":\"fail\",\"detail\":{\"actual\":\"${ACTUAL_USER_ID}\",\"expected\":\"${EXPECTED_USER_ID}\",\"error\":\"preflight_identity_mismatch\"}}]}"
    exit 1
fi

# 3. Call joined_rooms and require all required_rooms present
JOINED_JSON="$(curl -sf --max-time 10 -H "Authorization: Bearer ${MATRIX_TOKEN}" "${HS_URL}/_matrix/client/v3/joined_rooms" 2>/dev/null || echo "")"
MISSING_ROOMS="$(JOINED_RAW="${JOINED_JSON}" REQ_CSV="${REQUIRED_ROOMS_CSV}" python3 -c "
import os, json
try:
    joined = set(json.loads(os.environ['JOINED_RAW']).get('joined_rooms', []))
except Exception:
    joined = set()
req = [r for r in os.environ['REQ_CSV'].split(',') if r]
missing = [r for r in req if r not in joined]
print(','.join(missing))
")"

if [[ -n "${MISSING_ROOMS}" ]]; then
    echo "[preflight] FATAL: Missing required room membership(s): ${MISSING_ROOMS}" >&2
    report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"membership\",\"status\":\"fail\",\"detail\":{\"missing_rooms\":[\"${MISSING_ROOMS//,/\",\"}\"],\"error\":\"preflight_missing_room\"}}]}"
    exit 1
fi

# 4. Probe local Agent Zero API with canonical .a0-api-key credential
if [[ ! -s "${SECRET_FILE}" ]]; then
    echo "[preflight] FATAL: Canonical secret file ${SECRET_FILE} missing or empty" >&2
    report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"a0_auth\",\"status\":\"fail\",\"detail\":{\"error\":\"preflight_missing_secret_file\"}}]}"
    exit 1
fi

A0_KEY="$(cat "${SECRET_FILE}" | tr -d '\r\n')"
A0_FP="$(printf '%s' "${A0_KEY}" | sha256sum | cut -c1-12)"

# Wait briefly if Agent Zero UI is still booting on container startup
A0_HTTP="000"
for _attempt in $(seq 1 15); do
    A0_HTTP="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 \
        -X POST "http://localhost:80/api/api_message" \
        -H "Content-Type: application/json" \
        -H "X-API-KEY: ${A0_KEY}" \
        -d '{}' 2>/dev/null || echo "000")"
    if [[ "${A0_HTTP}" != "000" && "${A0_HTTP}" != "502" && "${A0_HTTP}" != "503" ]]; then
        break
    fi
    sleep 2
done

if [[ "${A0_HTTP}" == "401" || "${A0_HTTP}" == "403" ]]; then
    echo "[preflight] FATAL: Agent Zero API rejected credential (HTTP ${A0_HTTP}, fp=${A0_FP})" >&2
    report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"a0_auth\",\"status\":\"fail\",\"detail\":{\"error\":\"preflight_unauthorized_${A0_HTTP}\",\"fingerprint\":\"${A0_FP}\"}}]}"
    exit 1
fi

if [[ "${A0_HTTP}" != "200" && "${A0_HTTP}" != "400" && "${A0_HTTP}" != "422" ]]; then
    echo "[preflight] FATAL: Agent Zero API unreachable or unhealthy (HTTP ${A0_HTTP})" >&2
    report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"a0_auth\",\"status\":\"warn\",\"detail\":{\"error\":\"preflight_http_${A0_HTTP}\",\"fingerprint\":\"${A0_FP}\"}}]}"
    exit 1
fi

# 5. Report clean preflight pass to platform API
report_to_platform "{\"reporter\":\"preflight:${AGENT_NAME}\",\"checks\":[{\"check_type\":\"matrix_auth\",\"status\":\"pass\",\"detail\":{\"user_id\":\"${ACTUAL_USER_ID}\"}},{\"check_type\":\"identity\",\"status\":\"pass\",\"detail\":{\"actual\":\"${ACTUAL_USER_ID}\",\"expected\":\"${EXPECTED_USER_ID}\"}},{\"check_type\":\"membership\",\"status\":\"pass\",\"detail\":{\"joined_required\":[\"${REQUIRED_ROOMS_CSV//,/\",\"}\"]}},{\"check_type\":\"a0_auth\",\"status\":\"pass\",\"detail\":{\"http_code\":${A0_HTTP},\"fingerprint\":\"${A0_FP}\",\"source\":\"secret_file\"}}]}"

echo "[preflight] PASS: identity=${ACTUAL_USER_ID}, rooms=OK, a0_auth=HTTP_${A0_HTTP} (fp=${A0_FP})"
