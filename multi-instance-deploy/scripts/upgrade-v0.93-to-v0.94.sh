#!/usr/bin/env bash
# Upgrade one or more Agent-Matrix v0.93 agents to v0.94.
# Installs ghcr.io/l0r3zz/matrix-mcp-server-r2:0.4.0 and restarts only run_mcp.
# Does not restart the agent container. Does not start run_bot.
# Does not change the crypto store, the recovery key, or the Matrix access token.
#
#   ./upgrade-v0.93-to-v0.94.sh --dry-run 5
#   ./upgrade-v0.93-to-v0.94.sh 5
#   ./upgrade-v0.93-to-v0.94.sh --keep-maintenance 5
#
# There is no default of every agent. Pass instance numbers.
# The published binary sha256 is from matrix-mcp-server-r2 docs/upgrade-to-v0.4.0.md.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE="ghcr.io/l0r3zz/matrix-mcp-server-r2:0.4.0"
TAG="0.4.0"
EXPECTED_SHA="4e3c5bc89ddacd72b782d9230f6bedf18a352b8774640f74e18e9237ac899dc5"
DEPLOY="${SCRIPT_DIR}/../templates/scripts/deploy-mms-r2-to-agent.sh"
AMCTL_URL="${AMCTL_URL:-http://127.0.0.1:8077}"
AMCTL_ENV_FILE="${AMCTL_ENV_FILE:-/opt/agent-zero/multi-instance-deploy/am-ctl/.env}"
BINARY="/a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2"
DRY=0
KEEP_MAINT=0
INSTANCES=()

log() { echo "[v0.94] $*"; }
die() { echo "[v0.94] ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY=1; shift ;;
        --keep-maintenance) KEEP_MAINT=1; shift ;;
        --) shift; break ;;
        -*) die "Unknown option: $1" ;;
        *) INSTANCES+=("$1"); shift ;;
    esac
done

if [[ ${#INSTANCES[@]} -eq 0 ]]; then
    echo "Usage: $0 [--dry-run] [--keep-maintenance] N [N ...]"
    exit 1
fi

[[ -x "$DEPLOY" || -f "$DEPLOY" ]] || die "Missing ${DEPLOY}"

amctl_key() {
    if [[ -n "${AMCTL_API_KEY:-}" ]]; then
        printf '%s' "$AMCTL_API_KEY"
        return
    fi
    if [[ -f "$AMCTL_ENV_FILE" ]]; then
        grep -E '^AMCTL_API_KEY=' "$AMCTL_ENV_FILE" | tail -n1 | cut -d= -f2-
    fi
}

set_status() {
    local name="$1" status="$2" key
    if [[ "$DRY" -eq 1 ]]; then
        log "dry-run: set ${name} status=${status}"
        return
    fi
    key="$(amctl_key)"
    [[ -n "$key" ]] || die "AMCTL_API_KEY is empty. Status was not changed."
    curl -sf -X PUT "${AMCTL_URL}/api/v1/agents/${name}" \
        -H "X-API-Key: ${key}" \
        -H "Content-Type: application/json" \
        -d "{\"status\":\"${status}\"}" >/dev/null \
        || die "Could not set ${name} to ${status}"
}

bot_count() {
    local name="$1" count
    count="$(docker exec "$name" bash -c "pgrep -fc '[m]atrix-bot-rust' || true")"
    count="${count//$'\r'/}"
    printf '%s' "$count"
}

device_id() {
    local name="$1" id
    id="$(docker exec "$name" cat /a0/usr/workdir/matrix-mcp-server/crypto-store/.device-id)"
    id="${id//$'\r'/}"
    id="${id//$'\n'/}"
    printf '%s' "$id"
}

read_health() {
    local name="$1"
    docker exec "$name" curl -sf --max-time 10 http://127.0.0.1:3000/health
}

require_source_health() {
    local name="$1" raw
    raw="$(read_health "$name")" || die "${name} /health did not answer"
    python3 -c '
import json, sys
data = json.load(sys.stdin)
version = data.get("version")
ok = (
    data.get("status") == "healthy"
    and version in ("0.3.0", "0.3.1", "0.4.0")
    and data.get("e2ee") is True
    and data.get("crossSigned") is True
    and data.get("botEnabled") is True
)
if not ok:
    sys.exit(1)
print("version={0} e2ee={1} crossSigned={2} botEnabled={3}".format(
    version, data.get("e2ee"), data.get("crossSigned"), data.get("botEnabled")))
' <<<"$raw" || die "${name} is not a healthy 0.3.x or 0.4.0 agent with the bot enabled"
}

require_v094_health() {
    local name="$1" raw="" i
    for i in $(seq 1 24); do
        raw="$(docker exec "$name" curl -sf --max-time 5 http://127.0.0.1:3000/health || true)"
        [[ -n "$raw" ]] && break
        sleep 5
    done
    [[ -n "$raw" ]] || die "${name} /health did not answer within 120 seconds of the restart"
    python3 -c '
import json, sys
data = json.load(sys.stdin)
ok = (
    data.get("status") == "healthy"
    and data.get("version") == "0.4.0"
    and data.get("e2ee") is True
    and data.get("crossSigned") is True
    and data.get("botEnabled") is True
)
if not ok:
    sys.exit(1)
print("version={0} e2ee={1} crossSigned={2} botEnabled={3}".format(
    data.get("version"), data.get("e2ee"), data.get("crossSigned"), data.get("botEnabled")))
' <<<"$raw" || die "${name} /health is not version 0.4.0 with the bot enabled"
}

already_published() {
    local name="$1" raw got
    raw="$(read_health "$name" || true)"
    [[ -n "$raw" ]] || return 1
    python3 -c '
import json, sys
data = json.load(sys.stdin)
ok = data.get("status") == "healthy" and data.get("version") == "0.4.0"
sys.exit(0 if ok else 1)
' <<<"$raw" || return 1
    got="$(docker exec "$name" sha256sum "$BINARY" 2>/dev/null | awk '{print $1}' || true)"
    [[ "$got" == "$EXPECTED_SHA" ]]
}

upgrade_one() {
    local num="$1"
    local name="agent0-${num}" count before after got ver
    log "=== ${name} ==="
    docker ps --format '{{.Names}}' | grep -qx "$name" || die "${name} is not running"
    count="$(bot_count "$name")"
    [[ "$count" == "0" ]] || die "${name} has ${count} matrix-bot-rust processes. Finish the v0.93 upgrade first."

    if already_published "$name"; then
        log "${name} already runs the published 0.4.0 binary"
        return
    fi
    require_source_health "$name"
    before="$(device_id "$name")"
    [[ -n "$before" ]] || die "${name} has an empty device id"

    if [[ "$DRY" -eq 1 ]]; then
        log "dry-run: set ${name} to maintenance"
        log "dry-run: back up the binary to matrix-mcp-server-r2.bak-pre-040 when that file is absent"
        log "dry-run: deploy ${IMAGE}, stop and start run_mcp only"
        log "dry-run: require --version 0.4.0, sha256 ${EXPECTED_SHA}, and the same device id"
        log "dry-run: require /health version 0.4.0 and run_bot still stopped"
        if [[ "$KEEP_MAINT" -eq 1 ]]; then
            log "dry-run: leave ${name} in maintenance"
        else
            log "dry-run: set ${name} to active"
        fi
        return
    fi

    set_status "$name" maintenance
    docker exec "$name" bash -c '
        src=/a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2
        bak=/a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2.bak-pre-040
        if [ -f "$src" ] && [ ! -f "$bak" ]; then
            cp -a "$src" "$bak"
        fi
    '
    MMS_R2_TAG="$TAG" "$DEPLOY" "$num"

    ver="$(docker exec "$name" "$BINARY" --version)"
    ver="${ver//$'\r'/}"
    ver="${ver//$'\n'/}"
    [[ "$ver" == "matrix-mcp-server-r2 0.4.0" ]] || die "${name} --version is '${ver}'"
    got="$(docker exec "$name" sha256sum "$BINARY" | awk '{print $1}')"
    [[ "$got" == "$EXPECTED_SHA" ]] || die "${name} sha256 ${got} does not match the published 0.4.0 binary"
    after="$(device_id "$name")"
    [[ "$after" == "$before" ]] || die "${name} device id changed"
    require_v094_health "$name"
    count="$(bot_count "$name")"
    [[ "$count" == "0" ]] || die "${name} started matrix-bot-rust after the MCP restart"

    if [[ "$KEEP_MAINT" -eq 1 ]]; then
        log "${name} is on 0.4.0 and stays in maintenance"
        return
    fi
    set_status "$name" active
    log "${name} is active on 0.4.0"
}

log "Checking ${IMAGE}"
docker manifest inspect "$IMAGE" >/dev/null || die "${IMAGE} is not available. Tag v0.4.0 before this upgrade."
if [[ "$DRY" -eq 1 ]]; then
    log "dry-run: image tag is present. No pull and no container change."
else
    docker pull "$IMAGE" >/dev/null
fi

for n in "${INSTANCES[@]}"; do
    [[ "$n" =~ ^[0-9]+$ ]] || die "Instance must be a number: ${n}"
    upgrade_one "$n"
done

log "Done."
