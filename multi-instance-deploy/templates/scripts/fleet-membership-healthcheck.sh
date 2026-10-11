#!/bin/bash
# =============================================================================
# fleet-membership-healthcheck.sh -- Verify and repair fleet room membership
# =============================================================================
# Ensures all agents are joined in required rooms. If an agent is missing,
# sends an invite from @admin:v-site.net and accepts from the agent side.
#
# Repairs the full federation join handshake:
#   1. Invite via Synapse admin (client API as @admin)
#   2. Accept via agent's Continuwuity (client API as @agent0-N)
#
# Requires:
#   - kubectl access to Synapse pod
#   - curl access to agent homeservers (172.23.89.N:8448)
#   - Admin token for Synapse (@admin_repair2 or equivalent)
#   - Bot tokens readable from agent containers
#
# Run via cron every 6 hours, offset from other fleet crons.
# =============================================================================

set -uo pipefail

LOGFILE="/opt/agent-zero/multi-instance-deploy/logs/fleet-membership-healthcheck.log"
ADMIN_TOKEN_FILE="/home/l0r3zz/agent-matrix-repo/multi-instance-deploy/scripts/synapse_admin_token"
AGENTS="1 2 3 4 5"

# Required rooms: name -> room_id
declare -A REQUIRED_ROOMS
REQUIRED_ROOMS["Fleet HQ Clean"]="!gahcrWFWAUJQPPkuQy:v-site.net"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOGFILE"; }

# ---------------------------------------------------------------------------
# Locate Synapse pod
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Get @admin:v-site.net token (needed for invites -- must be a room member)
# ---------------------------------------------------------------------------
get_admin_invite_token() {
    local RESULT
    RESULT=$(kubectl exec -n matrix "$SYNAPSE_POD" -c matrix -- \
        curl -s --max-time 10 -X POST \
        "http://localhost:8008/_synapse/admin/v1/users/%40admin%3Av-site.net/login" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null) || true

    echo "$RESULT" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get('access_token',''))
except:
    pass
" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Get bot token from agent container
# ---------------------------------------------------------------------------
get_bot_token() {
    local N=$1
    docker exec "agent0-${N}" bash -c \
        "grep '^MATRIX_ACCESS_TOKEN=' /a0/usr/workdir/matrix-bot/.env 2>/dev/null | cut -d= -f2" \
        2>/dev/null
}

# ---------------------------------------------------------------------------
# Check room membership via Synapse admin API
# ---------------------------------------------------------------------------
check_membership() {
    local ROOM_ID=$1
    local ENCODED_ROOM
    ENCODED_ROOM=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${ROOM_ID}', safe=''))")

    kubectl exec -n matrix "$SYNAPSE_POD" -c matrix -- \
        curl -s --max-time 10 \
        "http://localhost:8008/_synapse/admin/v1/rooms/${ENCODED_ROOM}/members" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Invite user via @admin:v-site.net
# ---------------------------------------------------------------------------
invite_user() {
    local ROOM_ID=$1
    local USER_ID=$2
    local INVITE_TOKEN=$3

    kubectl exec -n matrix "$SYNAPSE_POD" -c matrix -- \
        curl -s --max-time 30 -X POST \
        "http://localhost:8008/_matrix/client/v3/rooms/${ROOM_ID}/invite" \
        -H "Authorization: Bearer ${INVITE_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"user_id\": \"${USER_ID}\"}" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Accept invite from agent homeserver
# ---------------------------------------------------------------------------
accept_invite() {
    local N=$1
    local ROOM_ID=$2
    local BOT_TOKEN=$3
    local MHS_IP="172.23.89.${N}"
    local ENCODED_ROOM
    ENCODED_ROOM=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${ROOM_ID}', safe=''))")

    curl -sk --max-time 30 -X POST \
        "https://${MHS_IP}:8448/_matrix/client/v3/join/${ENCODED_ROOM}" \
        -H "Authorization: Bearer ${BOT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null
}

# ===========================================================================
# Main
# ===========================================================================
log "Starting fleet membership healthcheck"

TOTAL_REPAIRS=0
TOTAL_FAILURES=0

for ROOM_NAME in "${!REQUIRED_ROOMS[@]}"; do
    ROOM_ID="${REQUIRED_ROOMS[$ROOM_NAME]}"
    log "Checking room: ${ROOM_NAME} (${ROOM_ID})"

    MEMBERS_JSON=$(check_membership "$ROOM_ID")
    if [ -z "$MEMBERS_JSON" ]; then
        log "ERROR: Could not query room members for ${ROOM_NAME}"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
        continue
    fi

    ADMIN_INVITE_TOKEN=""

    for N in $AGENTS; do
        USER_ID="@agent0-${N}:agent0-${N}-mhs.cybertribe.com"
        IS_MEMBER=$(echo "$MEMBERS_JSON" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print('yes' if '${USER_ID}' in d.get('members',[]) else 'no')
except:
    print('error')
" 2>/dev/null)

        if [ "$IS_MEMBER" = "yes" ]; then
            log "  OK agent0-${N}: joined in ${ROOM_NAME}"
            continue
        fi

        log "  MISSING agent0-${N}: not in ${ROOM_NAME} -- attempting repair"

        # Get @admin token (lazy, once per run)
        if [ -z "$ADMIN_INVITE_TOKEN" ]; then
            ADMIN_INVITE_TOKEN=$(get_admin_invite_token)
            if [ -z "$ADMIN_INVITE_TOKEN" ]; then
                log "  ERROR: Could not get @admin:v-site.net token for invites"
                TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
                continue
            fi
        fi

        # Get bot token
        BOT_TOKEN=$(get_bot_token "$N")
        if [ -z "$BOT_TOKEN" ]; then
            log "  ERROR: Could not get bot token for agent0-${N}"
            TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
            continue
        fi

        # Step 1: Send invite
        INVITE_RESULT=$(invite_user "$ROOM_ID" "$USER_ID" "$ADMIN_INVITE_TOKEN")
        INVITE_ERR=$(echo "$INVITE_RESULT" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get('errcode',''))
except:
    pass
" 2>/dev/null)

        if [ -n "$INVITE_ERR" ]; then
            log "  ERROR: Invite failed for agent0-${N}: ${INVITE_RESULT}"
            TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
            continue
        fi

        # Step 2: Accept invite from agent side
        sleep 2
        JOIN_RESULT=$(accept_invite "$N" "$ROOM_ID" "$BOT_TOKEN")
        JOIN_ROOM=$(echo "$JOIN_RESULT" | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get('room_id',''))
except:
    pass
" 2>/dev/null)

        if [ -n "$JOIN_ROOM" ]; then
            log "  REPAIRED agent0-${N}: rejoined ${ROOM_NAME}"
            TOTAL_REPAIRS=$((TOTAL_REPAIRS + 1))
        else
            log "  ERROR: Join failed for agent0-${N}: ${JOIN_RESULT}"
            TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
        fi
    done
done

log "Complete: ${TOTAL_REPAIRS} repairs, ${TOTAL_FAILURES} failures"

if [ "$TOTAL_FAILURES" -gt 0 ]; then
    log "WARNING: Some membership repairs failed. Manual intervention may be needed."
    log "  If joins fail with stale state, try: leave + forget + restart Continuwuity + re-invite"
fi
