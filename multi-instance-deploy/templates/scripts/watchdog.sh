#!/usr/bin/env bash
# =============================================================================
# watchdog.sh v3.0 — Platform-Integrated Container Health Reporter (Phase 8)
# =============================================================================
# Runs inside each agent container (or --once for single cycle), queries the
# am-ctl platform API for alert_rules classification (RESTARTABLE vs
# TERMINAL_CONFIG), executes local domain checks (matrix_auth, identity,
# membership, a0_auth, mcp, process), and reports health state back to
# POST /api/v1/health/{agent_name}/report.
#
# Never restart-loops on TERMINAL_CONFIG failures (401/403, identity mismatch,
# missing required room).
# =============================================================================
set -euo pipefail

RUN_ONCE=0
WATCHDOG_INTERVAL="${WATCHDOG_INTERVAL:-120}"
AGENT_NAME="${AGENT_NAME:-$(hostname)}"
AMCTL_URL="${AMCTL_URL:-http://172.23.88.254:8077}"
AMCTL_API_KEY="${AMCTL_API_KEY:-amctl-dev-key-2026}"
LOG="/a0/usr/workdir/startup-services.log"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --once)
            RUN_ONCE=1
            shift
            ;;
        --interval)
            WATCHDOG_INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--once] [--interval SECS]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

log() {
    echo "$(date '+%F %T') WATCHDOG-v3: $*" >> "${LOG}"
}

run_watchdog_cycle() {
    # 1. Fetch agent registry record and alert_rules from platform
    local reg_json rules_json
    reg_json="$(curl -sf --max-time 10 -H "X-API-Key: ${AMCTL_API_KEY}" "${AMCTL_URL}/api/v1/agents/${AGENT_NAME}" 2>/dev/null || echo "")"
    rules_json="$(curl -sf --max-time 10 -H "X-API-Key: ${AMCTL_API_KEY}" "${AMCTL_URL}/api/v1/health/rules/all" 2>/dev/null || echo "[]")"

    if [[ -z "${reg_json}" ]]; then
        log "WARN: Platform API unreachable at ${AMCTL_URL}; skipping cycle"
        return 0
    fi

    # 2. Run local checks and build JSON report via Python
    local report_payload
    report_payload="$(REG_JSON="${reg_json}" RULES_JSON="${rules_json}" AGENT_NAME="${AGENT_NAME}" python3 - << 'PYEOF'
import hashlib, json, os, subprocess, urllib.request

reg = json.loads(os.environ["REG_JSON"])
agent_name = os.environ["AGENT_NAME"]
expected_uid = reg.get("matrix_user_id", "")
req_rooms = [r["room_id"] for r in reg.get("required_rooms", [])]

bot_env = {}
if os.path.isfile("/a0/usr/workdir/matrix-bot/.env"):
    for ln in open("/a0/usr/workdir/matrix-bot/.env"):
        if "=" in ln and not ln.strip().startswith("#"):
            k, v = ln.strip().split("=", 1)
            bot_env[k] = v.strip('"').strip("'")

hs_url = bot_env.get("MATRIX_HOMESERVER_URL", "http://localhost:8008").rstrip("/")
token = bot_env.get("MATRIX_ACCESS_TOKEN", "")

checks = []

# matrix_auth & identity
actual_uid = None
whoami_err = None
try:
    req = urllib.request.Request(
        f"{hs_url}/_matrix/client/v3/account/whoami",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode())
        actual_uid = data.get("user_id")
except urllib.error.HTTPError as e:
    whoami_err = f"http_{e.code}"
except Exception as e:
    whoami_err = str(e)

if actual_uid:
    checks.append({"check_type": "matrix_auth", "status": "pass", "detail": {"user_id": actual_uid}})
else:
    checks.append({"check_type": "matrix_auth", "status": "fail", "detail": {"error": whoami_err or "whoami_failed"}})

if actual_uid and actual_uid == expected_uid:
    checks.append({"check_type": "identity", "status": "pass", "detail": {"actual": actual_uid, "expected": expected_uid}})
else:
    checks.append({"check_type": "identity", "status": "fail", "detail": {"actual": actual_uid, "expected": expected_uid, "error": whoami_err or "identity_mismatch"}})

# membership
try:
    req = urllib.request.Request(
        f"{hs_url}/_matrix/client/v3/joined_rooms",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        jdata = json.loads(resp.read().decode())
        joined = set(jdata.get("joined_rooms", []))
    missing = [r for r in req_rooms if r not in joined]
    if not missing:
        checks.append({"check_type": "membership", "status": "pass", "detail": {"joined_required": req_rooms, "total_joined": len(joined)}})
    else:
        checks.append({"check_type": "membership", "status": "fail", "detail": {"missing_rooms": missing}})
except Exception as e:
    checks.append({"check_type": "membership", "status": "fail", "detail": {"error": str(e)}})

# a0_auth
secret_path = "/a0/usr/workdir/matrix-bot/.a0-api-key"
if os.path.isfile(secret_path):
    a0_key = open(secret_path).read().strip()
    fp = hashlib.sha256(a0_key.encode()).hexdigest()[:12]
    try:
        req = urllib.request.Request(
            "http://localhost:80/api/api_message",
            data=b"{}",
            headers={"Content-Type": "application/json", "X-API-KEY": a0_key},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = 0
    if code in (200, 400, 422):
        checks.append({"check_type": "a0_auth", "status": "pass", "detail": {"http_code": code, "fingerprint": fp, "source": "secret_file"}})
    elif code in (401, 403):
        checks.append({"check_type": "a0_auth", "status": "fail", "detail": {"error": f"unauthorized_{code}", "fingerprint": fp}})
    else:
        checks.append({"check_type": "a0_auth", "status": "warn", "detail": {"error": f"http_{code}", "fingerprint": fp}})
else:
    checks.append({"check_type": "a0_auth", "status": "fail", "detail": {"error": "missing_secret_file"}})

# mcp
try:
    with urllib.request.urlopen("http://localhost:3000/health", timeout=5) as resp:
        mdata = json.loads(resp.read().decode())
        if mdata.get("status") == "healthy":
            checks.append({"check_type": "mcp", "status": "pass", "detail": mdata})
        else:
            checks.append({"check_type": "mcp", "status": "fail", "detail": mdata})
except Exception as e:
    checks.append({"check_type": "mcp", "status": "fail", "detail": {"error": str(e)}})

# process
bot_cnt_out = subprocess.getoutput("pgrep -fc '[m]atrix-bot-rust' || true").strip()
bot_cnt = int(bot_cnt_out) if bot_cnt_out.isdigit() else 0
if bot_cnt == 1:
    checks.append({"check_type": "process", "status": "pass", "detail": {"bot_count": 1, "bot_runtime": "rust", "supervisord": True}})
else:
    checks.append({"check_type": "process", "status": "fail", "detail": {"bot_count": bot_cnt, "supervisord": True}})

print(json.dumps({"reporter": f"watchdog:v3:{agent_name}", "checks": checks}))
PYEOF
)"

    # 3. Post health state to platform API (platform applies alert_rules classification)
    curl -sf --max-time 10 -X POST "${AMCTL_URL}/api/v1/health/${AGENT_NAME}/report" \
        -H "X-API-Key: ${AMCTL_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "${report_payload}" >/dev/null 2>&1 || log "WARN: Failed to report health to ${AMCTL_URL}"

    log "Reported health cycle for ${AGENT_NAME}"
}

if [[ "${RUN_ONCE}" -eq 1 ]]; then
    run_watchdog_cycle
    exit 0
fi

log "Starting watchdog v3.0 loop (interval=${WATCHDOG_INTERVAL}s)"
while true; do
    run_watchdog_cycle
    sleep "${WATCHDOG_INTERVAL}"
done
