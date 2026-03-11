#!/bin/bash
# =============================================================================
# startup-services.sh — Golden Template (v4.0 Continuwuity Edition)
# =============================================================================
set -euo pipefail

A0_PYTHON="/opt/venv-a0/bin/python3"
if [ ! -x "$A0_PYTHON" ]; then
  A0_PYTHON="$(command -v python3 || echo python3)"
fi

LOG="/a0/usr/workdir/startup-services.log"
BOT_DIR="/a0/usr/workdir/matrix-bot"
MCP_DIR="/a0/usr/workdir/matrix-mcp-server"
BOT_ENV="$BOT_DIR/.env"
MCP_ENV="$MCP_DIR/.env"
SETTINGS_JSON="/a0/usr/settings.json"

log() { echo "$(date '+%F %T') $*" | tee -a "$LOG" >/dev/null; }

set_env_kv() {
  local file="$1" key="$2" val="$3"
  [ -f "$file" ] || touch "$file"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$file"
  else
    printf "%s=%s\n" "$key" "$val" >> "$file"
  fi
}

env_val() {
  local file="$1" key="$2"
  grep -E "^${key}=" "$file" 2>/dev/null | tail -n1 | cut -d= -f2-
}

ensure_token_in_settings() {
  local token="$1"
  python3 - <<PY
import json
from pathlib import Path
p = Path("$SETTINGS_JSON")
if p.exists():
    try:
        data = json.loads(p.read_text() or "{}")
    except Exception:
        data = {}
else:
    data = {}
data["mcp_server_token"] = "$token"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2))
print("settings token synced")
PY
}

log "========== startup-services.sh starting =========="

# Phase 0: deterministic auth/key sync
log "Phase 0: validating env files"
[ -f "$BOT_ENV" ] || { log "ERROR: missing $BOT_ENV"; exit 1; }
[ -f "$MCP_ENV" ] || { log "ERROR: missing $MCP_ENV"; exit 1; }

A0_KEY="$(env_val "$BOT_ENV" A0_API_KEY)"
if [ -z "$A0_KEY" ] || [ "$A0_KEY" = "__A0_API_KEY__" ]; then
  A0_KEY="$(openssl rand -base64 12 | tr -d '/+=' | head -c 16)"
  log "Phase 0: generated new A0_API_KEY"
else
  log "Phase 0: using existing A0_API_KEY"
fi
set_env_kv "$BOT_ENV" A0_API_KEY "$A0_KEY"
set_env_kv "$MCP_ENV" A0_API_KEY "$A0_KEY"
ensure_token_in_settings "$A0_KEY"

TRIGGER="$(env_val "$BOT_ENV" TRIGGER_PREFIX)"
if [ -z "$TRIGGER" ]; then
  MXID="$(env_val "$BOT_ENV" MATRIX_USER_ID)"
  LOCAL="${MXID#@}"; LOCAL="${LOCAL%%:*}"
  [ -n "$LOCAL" ] || LOCAL="agent0"
  TRIGGER="${LOCAL}:"
  set_env_kv "$BOT_ENV" TRIGGER_PREFIX "$TRIGGER"
  log "Phase 0: set TRIGGER_PREFIX=$TRIGGER"
else
  log "Phase 0: TRIGGER_PREFIX already set ($TRIGGER)"
fi

# Phase 1: start MCP server
if ! pgrep -f 'node dist/http-server.js' >/dev/null; then
  log "Phase 1: starting matrix-mcp-server"
  cd "$MCP_DIR"
  [ -d node_modules ] || npm install --production --silent >>"$LOG" 2>&1 || true
  nohup node dist/http-server.js >> mcp-server.log 2>&1 &
  log "Phase 1: matrix-mcp-server pid=$!"
else
  log "Phase 1: matrix-mcp-server already running"
fi

# Phase 2: wait for Agent Zero API
log "Phase 2: waiting for Agent Zero API"
READY=0
for i in $(seq 1 60); do
  if curl -s -o /dev/null http://localhost:80; then READY=1; log "Phase 2: API ready at attempt $i"; break; fi
  sleep 2
done
[ "$READY" -eq 1 ] || { log "ERROR: Agent Zero API never became ready"; exit 1; }

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:80/api_message \
  -H 'Content-Type: application/json' -H "X-API-KEY: $A0_KEY" \
  -d '{"text":"startup-health-check"}' || true)
case "$HTTP_CODE" in
  200|400|422) log "Phase 2: API auth smoke passed (HTTP $HTTP_CODE)" ;;
  *) log "WARNING: API auth smoke unexpected HTTP $HTTP_CODE" ;;
esac

# Phase 3: deps
log "Phase 3: ensuring matrix-bot dependencies"
cd "$BOT_DIR"
if [ -f requirements.txt ]; then
  /opt/venv-a0/bin/pip install -q -r requirements.txt >>"$LOG" 2>&1 || true
else
  /opt/venv-a0/bin/pip install -q matrix-nio markdown aiohttp python-dotenv >>"$LOG" 2>&1 || true
fi

# Phase 4: start bot
TOKEN="$(env_val "$BOT_ENV" MATRIX_ACCESS_TOKEN)"
if [ -z "$TOKEN" ] || [ "$TOKEN" = "PENDING_REGISTRATION" ]; then
  log "Phase 4: MATRIX_ACCESS_TOKEN pending; bot start deferred"
else
  if ! pgrep -f 'matrix_bot.py' >/dev/null; then
    log "Phase 4: starting matrix-bot"
    cd "$BOT_DIR"
    nohup /opt/venv-a0/bin/python -u matrix_bot.py >> bot.log 2>&1 &
    log "Phase 4: matrix-bot pid=$!"
  else
    log "Phase 4: matrix-bot already running"
  fi
fi

log "========== startup-services.sh complete =========="
