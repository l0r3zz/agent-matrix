#!/usr/bin/env bash
# Upgrade one or more v0.92 agents to Agent-Matrix v0.93.
# The live fleet change waits until ghcr.io/l0r3zz/matrix-mcp-server-r2:0.3.0 exists.
# Run on the Docker host. Pass instance numbers. There is no default of every agent.
#
#   ./upgrade-v0.92-to-v0.93.sh --dry-run 5
#   ./upgrade-v0.92-to-v0.93.sh 5
#   ./upgrade-v0.92-to-v0.93.sh 1 2 3 4
#   ./upgrade-v0.92-to-v0.93.sh --keep-maintenance 3 4
#
# Agent 5 is the canary. Upgrade it before agents 1-4.
# Use --keep-maintenance while the host am-ctl still runs v0.92 code.
# v0.92 am-ctl expects one run_bot process and can start run_bot on an active agent.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE="ghcr.io/l0r3zz/matrix-mcp-server-r2:0.3.0"
WATCHDOG="${SCRIPT_DIR}/../templates/scripts/watchdog.sh"
STARTUP="${SCRIPT_DIR}/../templates/scripts/startup-services.sh"
DEPLOY="${SCRIPT_DIR}/../templates/scripts/deploy-mms-r2-to-agent.sh"
AMCTL_URL="${AMCTL_URL:-http://127.0.0.1:8077}"
AMCTL_ENV_FILE="${AMCTL_ENV_FILE:-/opt/agent-zero/multi-instance-deploy/am-ctl/.env}"
DRY=0
KEEP_MAINT=0
INSTANCES=()

log() { echo "[v0.93] $*"; }
die() { echo "[v0.93] ERROR: $*" >&2; exit 1; }

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

[[ -x "$WATCHDOG" || -f "$WATCHDOG" ]] || die "Missing ${WATCHDOG}"
[[ -f "$STARTUP" ]] || die "Missing ${STARTUP}"
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

require_current_health() {
    local name="$1" raw
    raw="$(docker exec "$name" curl -sf --max-time 10 http://127.0.0.1:3000/health)" \
        || die "${name} /health did not answer"
    python3 -c '
import json, sys
data = json.load(sys.stdin)
ok = data.get("status") == "healthy" and data.get("crossSigned") is True
if not ok:
    sys.exit(1)
print("healthy crossSigned={0} version={1} botEnabled={2}".format(
    data.get("crossSigned"), data.get("version"), data.get("botEnabled")))
' <<<"$raw" || die "${name} is not healthy and cross-signed. Upgrade stopped."
}

require_v093_health() {
    local name="$1" raw="" i
    # The first Matrix sync blocks /health for about 30 seconds.
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
    and data.get("version") == "0.3.0"
    and data.get("e2ee") is True
    and data.get("crossSigned") is True
    and data.get("botEnabled") is True
)
if not ok:
    sys.exit(1)
print("version={0} e2ee={1} crossSigned={2} botEnabled={3}".format(
    data.get("version"), data.get("e2ee"), data.get("crossSigned"), data.get("botEnabled")))
' <<<"$raw" || die "${name} /health is not version 0.3.0 with the bot enabled"
}

patch_supervisord() {
    local name="$1"
    docker exec -i "$name" python3 - /etc/supervisor/conf.d/supervisord.conf << 'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
lines = path.read_text().splitlines(keepends=True)
out = []
in_bot = False
seen_auto = False
seen_restart = False

def close_bot():
    if not seen_auto:
        out.append("autostart=false\n")
    if not seen_restart:
        out.append("autorestart=false\n")

for line in lines:
    if line.startswith("["):
        if in_bot:
            close_bot()
        in_bot = line.strip() == "[program:run_bot]"
        seen_auto = False
        seen_restart = False
        out.append(line if line.endswith("\n") else line + "\n")
        continue
    if in_bot and line.startswith("autostart="):
        out.append("autostart=false\n")
        seen_auto = True
        continue
    if in_bot and line.startswith("autorestart="):
        out.append("autorestart=false\n")
        seen_restart = True
        continue
    out.append(line if line.endswith("\n") else line + "\n")
if in_bot:
    close_bot()
path.write_text("".join(out))
PY
}

write_mcp_env() {
    local name="$1" num="$2" key="$3"
    docker exec -i -e "INSTANCE_NUM=${num}" -e "AMCTL_API_KEY=${key}" "$name" python3 - << 'PY'
import os
from pathlib import Path

mcp = Path("/a0/usr/workdir/matrix-mcp-server/.env")
bot = Path("/a0/usr/workdir/matrix-bot/.env")
text = mcp.read_text() if mcp.exists() else ""
lines = text.splitlines()
have = set()
for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        have.add(line.split("=", 1)[0])

def bot_val(name):
    if not bot.exists():
        return ""
    for line in bot.read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1]
    return ""

display = bot_val("BOT_DISPLAY_NAME") or bot_val("AGENT_IDENTITY")
if not display:
    display = "Agent0-" + os.environ.get("INSTANCE_NUM", "N")

add = []
if "BOT_ENABLED" not in have:
    add.append("BOT_ENABLED=true")
if "BOT_DISPLAY_NAME" not in have:
    add.append("BOT_DISPLAY_NAME=" + display)
if "AGENT_IDENTITY" not in have:
    add.append("AGENT_IDENTITY=" + display)
if "A0_API_URL" not in have:
    add.append("A0_API_URL=http://localhost:80/api/api_message")
key = os.environ.get("AMCTL_API_KEY", "")
if key and "AMCTL_API_KEY" not in have:
    add.append("AMCTL_API_KEY=" + key)
if not add:
    print("mcp-env unchanged")
else:
    with mcp.open("a") as fh:
        if text and not text.endswith("\n"):
            fh.write("\n")
        fh.write("\n".join(add) + "\n")
    print("mcp-env added " + ",".join(item.split("=", 1)[0] for item in add))
PY
}

bot_count() {
    local name="$1" count
    count="$(docker exec "$name" bash -c "pgrep -fc '[m]atrix-bot-rust' || true")"
    count="${count//$'\r'/}"
    printf '%s' "$count"
}

upgrade_one() {
    local num="$1"
    local name="agent0-${num}" count key
    log "=== ${name} ==="
    docker ps --format '{{.Names}}' | grep -qx "$name" || die "${name} is not running"
    require_current_health "$name"

    if [[ "$DRY" -eq 1 ]]; then
        log "dry-run: set ${name} to maintenance"
        log "dry-run: stop run_bot and set autostart=false autorestart=false"
        log "dry-run: require matrix-bot-rust count 0"
        log "dry-run: copy watchdog.sh and startup-services.sh"
        log "dry-run: add missing MCP bot lines; do not change the access token"
        log "dry-run: back up the binary, deploy ${IMAGE}, restart run_mcp only"
        log "dry-run: require /health version 0.3.0 and run_bot still stopped"
        if [[ "$KEEP_MAINT" -eq 1 ]]; then
            log "dry-run: leave ${name} in maintenance"
        else
            log "dry-run: set ${name} to active"
        fi
        return
    fi

    set_status "$name" maintenance
    docker exec "$name" supervisorctl stop run_bot >/dev/null 2>&1 || true
    patch_supervisord "$name"
    docker exec "$name" supervisorctl reread >/dev/null
    docker exec "$name" supervisorctl update >/dev/null
    docker exec "$name" supervisorctl stop run_bot >/dev/null 2>&1 || true
    count="$(bot_count "$name")"
    [[ "$count" == "0" ]] || die "${name} still has ${count} matrix-bot-rust processes"

    docker cp "$WATCHDOG" "${name}:/a0/usr/workdir/watchdog.sh"
    docker exec "$name" chmod 755 /a0/usr/workdir/watchdog.sh
    docker exec "$name" bash -c '
        f=/a0/usr/workdir/startup-services.sh
        if [ -f "$f" ] && [ ! -f "$f.bak-v092" ]; then
            cp -a "$f" "$f.bak-v092"
        fi
    '
    docker cp "$STARTUP" "${name}:/a0/usr/workdir/startup-services.sh"
    docker exec "$name" chmod 755 /a0/usr/workdir/startup-services.sh
    key="$(amctl_key || true)"
    write_mcp_env "$name" "$num" "$key"

    docker exec "$name" bash -c '
        src=/a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2
        bak=/a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2.bak-v092
        if [ -f "$src" ] && [ ! -f "$bak" ]; then
            cp -a "$src" "$bak"
        fi
    '
    MMS_R2_TAG=0.3.0 "$DEPLOY" "$num"
    docker exec "$name" supervisorctl restart run_mcp >/dev/null
    require_v093_health "$name"
    count="$(bot_count "$name")"
    [[ "$count" == "0" ]] || die "${name} started matrix-bot-rust after the MCP restart"
    if [[ "$KEEP_MAINT" -eq 1 ]]; then
        log "${name} is on 0.3.0 and stays in maintenance"
        return
    fi
    set_status "$name" active
    log "${name} is active on 0.3.0"
}

log "Checking ${IMAGE}"
docker manifest inspect "$IMAGE" >/dev/null || die "${IMAGE} is not available. Tag v0.3.0 before this upgrade."
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
