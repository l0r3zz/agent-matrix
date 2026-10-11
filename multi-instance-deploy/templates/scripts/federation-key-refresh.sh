#!/bin/bash
# =============================================================================
# federation-key-refresh.sh -- Keep Synapse signing key cache warm
# =============================================================================
# Queries Synapse notary for each agent homeserver signing key.
# This forces Synapse to re-fetch keys before cached ones expire,
# preventing "failed to find any key to satisfy" federation failures
# during Continuwuity automatic key rotations.
#
# Run via cron every 6 hours alongside fleet-token-healthcheck.sh
# =============================================================================

set -uo pipefail

LOGFILE="/opt/agent-zero/multi-instance-deploy/logs/federation-key-refresh.log"
ADMIN_TOKEN_FILE="/home/l0r3zz/agent-matrix-repo/multi-instance-deploy/scripts/synapse_admin_token"
AGENTS="1 2 3 4 5"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOGFILE"; }

SYNAPSE_POD=$(kubectl get pods -n matrix \
  -l app.kubernetes.io/instance=matrix-synapse,app.kubernetes.io/name=matrix \
  -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)

if [ -z "$SYNAPSE_POD" ]; then
    log "ERROR: Synapse pod not found"
    exit 1
fi

if [ ! -f "$ADMIN_TOKEN_FILE" ]; then
    log "ERROR: Admin token file not found: $ADMIN_TOKEN_FILE"
    exit 1
fi
ADMIN_TOKEN=$(cat "$ADMIN_TOKEN_FILE")

log "Starting key refresh (pod: $SYNAPSE_POD)"

PASS=0
FAIL=0
for N in $AGENTS; do
    DEST="agent0-${N}-mhs.cybertribe.com"
    RESULT=$(kubectl exec -n matrix "$SYNAPSE_POD" -c matrix -- \
        curl -sf --max-time 15 \
        "http://localhost:8008/_matrix/key/v2/query/${DEST}" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" 2>/dev/null) || true

    if [ -n "$RESULT" ]; then
        KEYS=$(echo "$RESULT" | python3 -c "
import sys,json,time
d=json.load(sys.stdin)
parts=[]
for k in d.get('server_keys',[]):
    for kid in k.get('verify_keys',{}):
        vu = k.get('valid_until_ts',0)
        exp = time.strftime('%Y-%m-%d', time.gmtime(vu/1000)) if vu else '?'
        days = (vu/1000 - time.time()) / 86400 if vu else 0
        warn = ' EXPIRING_SOON' if 0 < days < 2 else ''
        parts.append(f'{kid} valid_until={exp}{warn}')
print('; '.join(parts))
" 2>/dev/null) || true
        log "OK ${DEST}: ${KEYS}"
        PASS=$((PASS + 1))
    else
        log "FAIL ${DEST}: notary query returned empty (token expired?)"
        FAIL=$((FAIL + 1))
    fi
done

log "Complete: ${PASS} ok, ${FAIL} failed"

if [ "$FAIL" -gt 0 ] && [ "$PASS" -eq 0 ]; then
    log "WARNING: All queries failed -- admin token may have expired. Regenerate via register API."
fi
