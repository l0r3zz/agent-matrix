#!/usr/bin/env bash
# =============================================================================
# Split matrix-bot onto its own Matrix device (v0.92)
#
# matrix-mcp-server-r2 binds its E2EE crypto store to the device of the MCP
# token. If matrix-bot syncs with that same token, the bot's /sync consumes
# the device's to-device messages (Megolm room keys), and inbound E2EE fails
# with missing_key. This script gives the bot its own device (AgentZeroBot)
# and restarts only run_bot. The MCP token, device, and crypto store are never
# touched.
#
# Idempotent: agents that already use separate devices are left alone.
#
# Usage: ./split-bot-device.sh [--dry-run] <agent-number> [agent-number ...]
# Example: ./split-bot-device.sh 5
# =============================================================================
set -euo pipefail

AGENT_ZERO_DIR="${AGENT_ZERO_DIR:-/opt/agent-zero}"
BOT_DEVICE_ID="AgentZeroBot"
BOT_ENV="/a0/usr/workdir/matrix-bot/.env"
MCP_ENV="/a0/usr/workdir/matrix-mcp-server/.env"

usage() {
    echo "Usage: $0 [--dry-run] <agent-number> [agent-number ...]" >&2
    exit 64
}

DRY_RUN=0
AGENTS=()
for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help) usage ;;
        ''|*[!0-9]*) echo "Invalid agent number: ${arg}" >&2; usage ;;
        *) AGENTS+=("${arg}") ;;
    esac
done
[[ ${#AGENTS[@]} -ge 1 ]] || usage
command -v docker >/dev/null || { echo "docker not found" >&2; exit 69; }

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

env_value() {
    local agent="$1" file="$2" key="$3"
    docker exec "${agent}" sh -c "grep '^${key}=' '${file}' 2>/dev/null | tail -n1 | cut -d= -f2-" | tr -d '\r\n"'
}

token_device() {
    local agent="$1" hs="$2" token="$3"
    docker exec "${agent}" curl -s -H "Authorization: Bearer ${token}" \
        "${hs}/_matrix/client/v3/account/whoami" 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('device_id',''))" 2>/dev/null || true
}

login_bot_device() {
    local agent="$1" hs="$2" user="$3" password="$4"
    USER_NAME="${user}" PASSWORD="${password}" DEVICE="${BOT_DEVICE_ID}" python3 -c '
import json, os
print(json.dumps({
    "type": "m.login.password",
    "identifier": {"type": "m.id.user", "user": os.environ["USER_NAME"]},
    "password": os.environ["PASSWORD"],
    "device_id": os.environ["DEVICE"],
    "initial_device_display_name": os.environ["DEVICE"],
}))' | docker exec -i "${agent}" curl -s -X POST -H "Content-Type: application/json" \
        --data-binary @- "${hs}/_matrix/client/v3/login" 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || true
}

split_agent() {
    local num="$1"
    local agent="agent0-${num}"
    log "--- ${agent} ---"

    local hs mcp_token bot_token mcp_device bot_device
    hs="$(env_value "${agent}" "${MCP_ENV}" MATRIX_HOMESERVER_URL)"
    mcp_token="$(env_value "${agent}" "${MCP_ENV}" MATRIX_ACCESS_TOKEN)"
    bot_token="$(env_value "${agent}" "${BOT_ENV}" MATRIX_ACCESS_TOKEN)"
    [[ -n "${hs}" && -n "${mcp_token}" ]] || { log "  FAIL: MCP .env has no homeserver or token"; return 1; }

    mcp_device="$(token_device "${agent}" "${hs}" "${mcp_token}")"
    bot_device="$(token_device "${agent}" "${hs}" "${bot_token}")"
    [[ -n "${mcp_device}" ]] || { log "  FAIL: MCP token is not valid (whoami failed)"; return 1; }
    log "  MCP device: ${mcp_device}  bot device: ${bot_device:-<invalid>}"

    if [[ -n "${bot_device}" && "${bot_device}" != "${mcp_device}" ]]; then
        log "  OK: already on separate devices"
        return 0
    fi
    if [[ "${mcp_device}" == "${BOT_DEVICE_ID}" ]]; then
        log "  FAIL: MCP itself uses device ${BOT_DEVICE_ID}; resolve manually"
        return 1
    fi

    if [[ "${DRY_RUN}" -eq 1 ]]; then
        log "  DRY-RUN: would log the bot in as ${BOT_DEVICE_ID} and restart run_bot"
        return 0
    fi

    local user_id user password new_token new_device
    user_id="$(env_value "${agent}" "${MCP_ENV}" MATRIX_USER_ID)"
    user="${user_id#@}"; user="${user%%:*}"
    password="$(grep '^MATRIX_PASSWORD=' "${AGENT_ZERO_DIR}/${agent}/.env" 2>/dev/null | tail -n1 | cut -d= -f2- | tr -d '\r\n"')"
    [[ -n "${user}" && -n "${password}" ]] || { log "  FAIL: missing user or MATRIX_PASSWORD in ${AGENT_ZERO_DIR}/${agent}/.env"; return 1; }

    log "  Logging bot in as device ${BOT_DEVICE_ID}"
    new_token="$(login_bot_device "${agent}" "${hs}" "${user}" "${password}")"
    [[ -n "${new_token}" ]] || { log "  FAIL: bot login failed"; return 1; }
    new_device="$(token_device "${agent}" "${hs}" "${new_token}")"
    if [[ "${new_device}" != "${BOT_DEVICE_ID}" || "${new_device}" == "${mcp_device}" ]]; then
        log "  FAIL: new bot token resolves to device ${new_device:-?}"
        return 1
    fi

    log "  Writing bot .env and restarting run_bot"
    docker exec "${agent}" cp "${BOT_ENV}" "${BOT_ENV}.bak.pre-split"
    printf '%s\n' "${new_token}" | docker exec -i "${agent}" python3 -c '
import re, sys
path, device = sys.argv[1], sys.argv[2]
token = sys.stdin.readline().strip()
text = open(path).read()
for key, val in (("MATRIX_ACCESS_TOKEN", token), ("MATRIX_DEVICE_ID", device)):
    if re.search(rf"^{key}=", text, flags=re.M):
        text = re.sub(rf"^{key}=.*$", f"{key}={val}", text, flags=re.M)
    else:
        text = text.rstrip("\n") + f"\n{key}={val}\n"
open(path, "w").write(text)' "${BOT_ENV}" "${BOT_DEVICE_ID}"
    docker exec "${agent}" supervisorctl restart run_bot >/dev/null

    bot_device="$(token_device "${agent}" "${hs}" "$(env_value "${agent}" "${BOT_ENV}" MATRIX_ACCESS_TOKEN)")"
    [[ "${bot_device}" == "${BOT_DEVICE_ID}" ]] || { log "  FAIL: bot .env verification failed"; return 1; }
    log "  OK: bot on ${BOT_DEVICE_ID}, MCP on ${mcp_device}"
}

rc=0
for num in "${AGENTS[@]}"; do
    split_agent "${num}" || rc=1
done
exit "${rc}"
