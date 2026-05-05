#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--room-id ROOM_ID] <instance-number>

Checks:
  1) Containers running (agent0-N and agent0-N-mhs)
  2) Dendrite endpoints healthy (:8008 client versions, :8448 server key)
  3) startup-services completed latest cycle
  4) Processes up (run_ui.py, http-server.js, matrix-bot runtime)
  5) Env invariants:
     - TRIGGER_PREFIX=agent0-N:
     - A0_API_KEY exists and matches bot/mcp env files
  6) Agent API auth smoke (X-API-KEY not 401)
  7) Matrix /sync with bot token returns next_batch
  8) Optional: room membership check if --room-id supplied

Exit code: non-zero on failure.
USAGE
}

ROOM_ID=""
if [[ ${1:-} == "--room-id" ]]; then
  ROOM_ID="${2:-}"
  shift 2
fi
[[ ${1:-} =~ ^[0-9]+$ ]] || { usage; exit 2; }
N="$1"
AGENT="agent0-${N}"
MHS="agent0-${N}-mhs"
MHS_IP="172.23.89.${N}"
BOT_ENV="/a0/usr/workdir/matrix-bot/.env"
MCP_ENV="/a0/usr/workdir/matrix-mcp-server/.env"

fails=0
pass() { echo "[PASS] $*"; }
fail() { echo "[FAIL] $*"; fails=$((fails+1)); }
info() { echo "[INFO] $*"; }

# 1) Containers
if docker ps --format '{{.Names}}' | grep -qx "$AGENT"; then pass "$AGENT running"; else fail "$AGENT not running"; fi
if docker ps --format '{{.Names}}' | grep -qx "$MHS"; then pass "$MHS running"; else fail "$MHS not running"; fi

# 2) Dendrite endpoints
if curl -fsS "http://${MHS_IP}:8008/_matrix/client/versions" >/tmp/v.json 2>/dev/null; then
  pass "Dendrite client endpoint healthy"
else
  fail "Dendrite client endpoint failed"
fi
if curl -kfsS "https://${MHS_IP}:8448/_matrix/key/v2/server" >/tmp/k.json 2>/dev/null; then
  pass "Dendrite federation key endpoint healthy"
else
  fail "Dendrite federation key endpoint failed"
fi

# 3) startup latest cycle
if docker exec "$AGENT" sh -lc 'tail -n 80 /a0/usr/workdir/startup-services.log 2>/dev/null | grep -q "startup-services.sh complete"'; then
  pass "startup-services completed"
else
  fail "startup-services completion marker missing"
fi

# 4) process checks
for p in "python /a0/run_ui.py" "node dist/http-server.js"; do
  if docker exec "$AGENT" sh -lc "ps -ef | grep -F '$p' | grep -v grep >/dev/null"; then
    pass "process present: $p"
  else
    fail "process missing: $p"
  fi
done

if docker exec "$AGENT" sh -lc "ps -ef | grep -E 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust' | grep -v grep >/dev/null"; then
  pass "process present: matrix-bot runtime"
else
  fail "process missing: matrix-bot runtime"
fi

# 5) env invariants
BOT_KEY=$(docker exec "$AGENT" sh -lc "grep '^A0_API_KEY=' $BOT_ENV | tail -n1 | cut -d= -f2-" || true)
MCP_KEY=$(docker exec "$AGENT" sh -lc "grep '^A0_API_KEY=' $MCP_ENV | tail -n1 | cut -d= -f2-" || true)
TRIG=$(docker exec "$AGENT" sh -lc "grep '^TRIGGER_PREFIX=' $BOT_ENV | tail -n1 | cut -d= -f2-" || true)
TOK=$(docker exec "$AGENT" sh -lc "grep '^MATRIX_ACCESS_TOKEN=' $BOT_ENV | tail -n1 | cut -d= -f2-" || true)
HOMEURL=$(docker exec "$AGENT" sh -lc "grep '^MATRIX_HOMESERVER_URL=' $BOT_ENV | tail -n1 | cut -d= -f2-" || true)

[[ -n "$BOT_KEY" ]] && pass "bot A0_API_KEY present" || fail "bot A0_API_KEY missing"
[[ -n "$MCP_KEY" ]] && pass "mcp A0_API_KEY present" || fail "mcp A0_API_KEY missing"
[[ "$BOT_KEY" == "$MCP_KEY" && -n "$BOT_KEY" ]] && pass "A0_API_KEY parity bot==mcp" || fail "A0_API_KEY mismatch bot vs mcp"
[[ "$TRIG" == "agent0-${N}:" ]] && pass "TRIGGER_PREFIX correct ($TRIG)" || fail "TRIGGER_PREFIX invalid ($TRIG)"
[[ -n "$TOK" && "$TOK" != "PENDING_REGISTRATION" ]] && pass "MATRIX_ACCESS_TOKEN present" || fail "MATRIX_ACCESS_TOKEN missing/pending"
[[ -n "$HOMEURL" ]] && pass "MATRIX_HOMESERVER_URL present" || fail "MATRIX_HOMESERVER_URL missing"

# 6) Agent API auth smoke
HTTP_CODE=$(docker exec "$AGENT" sh -lc "curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:80/api_message -H 'Content-Type: application/json' -H 'X-API-KEY: ${BOT_KEY}' -d '{\"text\":\"health\"}'" || true)
case "$HTTP_CODE" in
  200|400|422) pass "Agent API auth smoke ok (HTTP $HTTP_CODE)" ;;
  401) fail "Agent API rejected key (401)" ;;
  *) fail "Agent API unexpected HTTP $HTTP_CODE" ;;
esac

# 7) Matrix sync check
SYNC_OK=$(docker exec "$AGENT" sh -lc "curl -sS -H 'Authorization: Bearer ${TOK}' '${HOMEURL}/_matrix/client/v3/sync?timeout=1' | grep -c 'next_batch'" || true)
[[ "$SYNC_OK" -ge 1 ]] && pass "Matrix sync returns next_batch" || fail "Matrix sync missing next_batch"

# 8) Optional room check
if [[ -n "$ROOM_ID" ]]; then
  if docker exec "$AGENT" sh -lc "curl -sS -H 'Authorization: Bearer ${TOK}' '${HOMEURL}/_matrix/client/v3/joined_rooms' | grep -q '"${ROOM_ID//\//\\/}"'"; then
    pass "Joined room present: $ROOM_ID"
  else
    fail "Room not joined: $ROOM_ID"
  fi
fi

echo
if [[ "$fails" -eq 0 ]]; then
  echo "RESULT: PASS (instance $N)"
  exit 0
else
  echo "RESULT: FAIL (instance $N) - failures=$fails"
  exit 1
fi
