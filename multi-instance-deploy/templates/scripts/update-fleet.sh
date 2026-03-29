#!/bin/bash
# =============================================================================
# update-fleet.sh — Zero-Touch Agent Zero Fleet Updater (v1.3)
# =============================================================================
# Programmatically triggers Agent Zero's built-in self-update mechanism across
# the fleet, waits for completion, verifies health, and cleans up.
#
# Usage:
#   ./update-fleet.sh --status
#   ./update-fleet.sh --status --instances 2,3
#   ./update-fleet.sh --version v1.3
#   ./update-fleet.sh --version v1.3 --instances 2,3
#   ./update-fleet.sh --version latest --no-backup
#   ./update-fleet.sh --version v1.3 --dry-run
#   ./update-fleet.sh --version v1.3 --skip-restart   # trigger only
#
# Requires: docker, python3 (with PyYAML) on host, curl
# Runs on: g2s host (172.23.100.121)
# =============================================================================

set -euo pipefail

# --- Configuration ---
BASE_DIR="/opt/agent-zero"
ALL_INSTANCES="1 2 3 4 5"
DEFAULT_BRANCH="main"
DEFAULT_TAG="latest"
HEALTH_TIMEOUT=180
HEALTH_POLL_INTERVAL=5
UPDATE_TIMEOUT=300
UPDATE_POLL_INTERVAL=10
VENV_PYTHON="/opt/venv-a0/bin/python3"
TRIGGER_SCRIPT="/exe/self_update_manager.py"
STATUS_FILE="/exe/a0-self-update-status.yaml"
LOG_FILE="/exe/a0-self-update.log"
HEALTH_URL="http://127.0.0.1:80/api/health"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Parse arguments ---
VERSION=""
BRANCH="$DEFAULT_BRANCH"
INSTANCES="$ALL_INSTANCES"
DRY_RUN=false
NO_BACKUP=false
SKIP_RESTART=false
FORCE=false
VERBOSE=false
STATUS_MODE=false
CLEANUP_MODE=false
CLEANUP_MODE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Modes:
  --status              Show current fleet status (no update)
  --cleanup             Kill zombie bot processes across the fleet
  --cleanup             Kill zombie bot processes across the fleet
  --version TAG         Target version tag for update (e.g., v1.3, latest)

Optional:
  --branch BRANCH       Git branch (default: main)
  --instances N,N,...    Comma-separated instance numbers (default: all)
  --no-backup           Skip usr backup before update
  --skip-restart        Queue update but don't restart (manual restart later)
  --force               Proceed even if target matches current version
  --dry-run             Show what would be done without executing
  --verbose             Show detailed output including logs
  --health-timeout SEC  Seconds to wait for health (default: $HEALTH_TIMEOUT)
  --update-timeout SEC  Seconds to wait for update (default: $UPDATE_TIMEOUT)
  -h, --help            Show this help

Examples:
  $(basename "$0") --status
  $(basename "$0") --status --instances 2,3
  $(basename "$0") --cleanup
  $(basename "$0") --cleanup --instances 4,5
  $(basename "$0") --cleanup
  $(basename "$0") --cleanup --instances 4,5
  $(basename "$0") --version v1.3
  $(basename "$0") --version v1.3 --instances 2,3
  $(basename "$0") --version latest --no-backup
  $(basename "$0") --version v1.3 --dry-run
EOF
    exit 0

}
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)         VERSION="$2"; shift 2 ;;
        --status)          STATUS_MODE=true; shift ;;
        --cleanup)         CLEANUP_MODE=true; shift ;;
        --cleanup)         CLEANUP_MODE=true; shift ;;
        --branch)          BRANCH="$2"; shift 2 ;;
        --instances)       INSTANCES=$(echo "$2" | tr ',' ' '); shift 2 ;;
        --no-backup)       NO_BACKUP=true; shift ;;
        --skip-restart)    SKIP_RESTART=true; shift ;;
        --force)           FORCE=true; shift ;;
        --dry-run)         DRY_RUN=true; shift ;;
        --verbose)         VERBOSE=true; shift ;;
        --health-timeout)  HEALTH_TIMEOUT="$2"; shift 2 ;;
        --update-timeout)  UPDATE_TIMEOUT="$2"; shift 2 ;;
        -h|--help)         usage ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; echo "Use --help for usage."; exit 1 ;;
    esac
done

# --- Helper Functions ---

log() {
    echo -e "$(date '+%H:%M:%S') $1"
}

log_header() {
    echo -e "\n${CYAN}${BOLD}$1${NC}"
}

get_current_version() {
    local N=$1
    docker exec "agent0-$N" curl -s "$HEALTH_URL" 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('gitinfo',{}).get('short_tag','unknown'))" 2>/dev/null || echo "unreachable"
}

get_health_status() {
    local N=$1
    local CODE
    CODE=$(docker exec "agent0-$N" curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    echo "$CODE"
}

get_update_status() {
    local N=$1
    docker exec "agent0-$N" cat "$STATUS_FILE" 2>/dev/null | \
        python3 -c "
import sys, yaml
try:
    d = yaml.safe_load(sys.stdin.read())
    print(d.get('status', 'unknown') if d else 'none')
except:
    print('none')
" 2>/dev/null || echo "none"
}

is_container_running() {
    local N=$1
    docker ps --format '{{.Names}}' | grep -qx "agent0-$N" 2>/dev/null
}

cleanup_zombie_bots() {
    local N=$1
    local ACTIVE_PID
    ACTIVE_PID=$(docker exec "agent0-$N" cat /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null || echo "")
    if [ -z "$ACTIVE_PID" ]; then return; fi
    local ALL_PIDS
    ALL_PIDS=$(docker exec "agent0-$N" ps aux 2>/dev/null | grep -E 'matrix_bot|matrix-bot-rust' | grep -v grep | awk '{print $2}')
    for PID in $ALL_PIDS; do
        if [ "$PID" != "$ACTIVE_PID" ]; then
            docker exec "agent0-$N" kill -9 "$PID" 2>/dev/null || true
            [ "$VERBOSE" = true ] && log "  [agent0-$N] Killed zombie bot PID $PID"
        fi
    done
}

wait_for_container_up() {
    local N=$1
    local ELAPSED=0
    while [ $ELAPSED -lt 60 ]; do
        if is_container_running "$N"; then
            return 0
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
    return 1
}

wait_for_health() {
    local N=$1
    local ELAPSED=0
    while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
        local CODE
        CODE=$(get_health_status "$N")
        if [ "$CODE" = "200" ]; then
            return 0
        fi
        [ "$VERBOSE" = true ] && log "  [agent0-$N] Health poll: HTTP $CODE ($ELAPSED/${HEALTH_TIMEOUT}s)"
        sleep $HEALTH_POLL_INTERVAL
        ELAPSED=$((ELAPSED + HEALTH_POLL_INTERVAL))
    done
    return 1
}

wait_for_update_complete() {
    local N=$1
    local ELAPSED=0
    while [ $ELAPSED -lt $UPDATE_TIMEOUT ]; do
        local STATUS
        STATUS=$(get_update_status "$N")
        case "$STATUS" in
            success|skipped|failed) return 0 ;;
            none|unknown) ;;
            *) [ "$VERBOSE" = true ] && log "  [agent0-$N] Update status: $STATUS ($ELAPSED/${UPDATE_TIMEOUT}s)" ;;
        esac
        sleep $UPDATE_POLL_INTERVAL
        ELAPSED=$((ELAPSED + UPDATE_POLL_INTERVAL))
    done
    return 1
}

get_bot_runtime() {
    local N=$1
    local PY_COUNT RUST_COUNT
    PY_COUNT=$(docker exec "agent0-$N" pgrep -c -f 'python.*matrix_bot' 2>/dev/null | tr -d '[:space:]' || echo "0"); [ -z "$PY_COUNT" ] && PY_COUNT=0
    RUST_COUNT=$(docker exec "agent0-$N" pgrep -c -f 'matrix-bot-rust' 2>/dev/null | tr -d '[:space:]' || echo "0"); [ -z "$RUST_COUNT" ] && RUST_COUNT=0
    if [ "$PY_COUNT" -ge 1 ] && [ "$RUST_COUNT" -ge 1 ]; then
        echo "both!"
    elif [ "$PY_COUNT" -ge 1 ]; then
        echo "python"
    elif [ "$RUST_COUNT" -ge 1 ]; then
        echo "rust"
    else
        echo "none"
    fi
}

# Get the configured bot runtime (what SHOULD start)
get_bot_configured_runtime() {
    local N=$1
    docker exec "agent0-$N" bash -c '
        R=$(grep "^MATRIX_BOT_RUNTIME=" /a0/usr/workdir/matrix-bot/.env 2>/dev/null | cut -d= -f2)
        if [ -z "$R" ] && [ -f /a0/usr/workdir/matrix-bot/.bot_runtime ]; then
            R=$(tr -d "[:space:]" < /a0/usr/workdir/matrix-bot/.bot_runtime)
        fi
        echo "${R:-python}"
    ' 2>/dev/null || echo "?"
}

# Get bot code fingerprint (short md5)
get_bot_version_hash() {
    local N=$1
    local RUNTIME=$2
    local HASH
    if [ "$RUNTIME" = "rust" ]; then
        HASH=$(docker exec "agent0-$N" md5sum /a0/usr/workdir/matrix-bot/matrix-bot-rust 2>/dev/null | cut -c1-8)
    else
        HASH=$(docker exec "agent0-$N" md5sum /a0/usr/workdir/matrix-bot/matrix_bot.py 2>/dev/null | cut -c1-8)
    fi
    echo "${HASH:-????????}"
}

# Get golden template bot code fingerprint for drift detection
# NOTE: This reads the template on the g2s host (not inside container)
get_template_bot_hash() {
    local RUNTIME=$1
    local TMPL_DIR="/opt/agent-zero/multi-instance-deploy/templates/matrix-bot"
    if [ "$RUNTIME" = "rust" ]; then
        md5sum "${TMPL_DIR}/matrix-bot-rust" 2>/dev/null | cut -c1-8 || echo "no-tmpl"
    else
        md5sum "${TMPL_DIR}/matrix_bot.py" 2>/dev/null | cut -c1-8 || echo "no-tmpl"
    fi
}





# --- Show Status Mode ---

if [ "$STATUS_MODE" = true ]; then
    set +e  # Disable exit-on-error for status checks
    log_header "═══════════════════════════════════════════════════════════════"
    log_header "  Agent-Matrix Fleet Status"
    log_header "═══════════════════════════════════════════════════════════════"
    echo ""

    # Pre-compute template hashes for drift detection
    TMPL_HASH_PY=$(get_template_bot_hash "python")
    TMPL_HASH_RUST=$(get_template_bot_hash "rust")

    # Header row
    printf "  ${BOLD}%-14s %-11s %-10s %-10s %-7s %-8s %-10s %-5s %-4s %s${NC}\n" \
        "Instance" "Container" "Version" "Compose" "BotRT" "BotVer" "Bot" "MCP" "WD" "Last Update"
    printf "  %-14s %-11s %-10s %-10s %-7s %-8s %-10s %-5s %-4s %s\n" \
        "------------" "---------" "-------" "-------" "-----" "------" "---" "---" "--" "-----------"

    for N in $INSTANCES; do
        # Container status
        if is_container_running "$N"; then
            CONTAINER_TXT="up"
            CONTAINER_CLR="${GREEN}"
        else
            CONTAINER_TXT="down"
            CONTAINER_CLR="${RED}"
            printf "  %-14s ${CONTAINER_CLR}%-11s${NC} %-10s %-10s %-7s %-8s %-10s %-5s %-4s %s\n" \
                "agent0-$N" "$CONTAINER_TXT" "-" "-" "-" "-" "-" "-" "-" "-"
            continue
        fi

        # Running version from health API
        RUN_VER=$(get_current_version "$N")

        # docker-compose.yml image tag
        COMPOSE_FILE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
        COMPOSE_VER=$(grep 'image: agent0ai/agent-zero:' "$COMPOSE_FILE" 2>/dev/null | grep -oP 'v[0-9.]+' | head -1 || echo "?")
        if [ "$RUN_VER" = "$COMPOSE_VER" ]; then
            COMPOSE_TXT="$COMPOSE_VER"
            COMPOSE_CLR="${GREEN}"
        else
            COMPOSE_TXT="${COMPOSE_VER} ⚠"
            COMPOSE_CLR="${YELLOW}"
        fi

        # --- NEW: Bot Runtime ---
        BOT_RT=$(get_bot_runtime "$N")
        BOT_RT_CFG=$(get_bot_configured_runtime "$N")
        if [ "$BOT_RT" = "none" ]; then
            BOT_RT_TXT="none"
            BOT_RT_CLR="${RED}"
        elif [ "$BOT_RT" = "both!" ]; then
            BOT_RT_TXT="both!"
            BOT_RT_CLR="${YELLOW}"
        elif [ "$BOT_RT" != "$BOT_RT_CFG" ]; then
            # Running runtime differs from configured
            BOT_RT_TXT="${BOT_RT}⚠"
            BOT_RT_CLR="${YELLOW}"
        else
            BOT_RT_TXT="$BOT_RT"
            BOT_RT_CLR="${GREEN}"
        fi

        # --- NEW: Bot Version (code fingerprint + drift) ---
        BOT_HASH=$(get_bot_version_hash "$N" "$BOT_RT")
        if [ "$BOT_RT" = "rust" ]; then
            TMPL_CMP="$TMPL_HASH_RUST"
        else
            TMPL_CMP="$TMPL_HASH_PY"
        fi
        if [ "$BOT_HASH" = "$TMPL_CMP" ]; then
            BOT_VER_TXT="$BOT_HASH"
            BOT_VER_CLR="${GREEN}"
        elif [ "$TMPL_CMP" = "no-tmpl" ]; then
            BOT_VER_TXT="${BOT_HASH}?"
            BOT_VER_CLR="${CYAN}"
        else
            BOT_VER_TXT="${BOT_HASH}⚠"
            BOT_VER_CLR="${YELLOW}"
        fi

        # Bot process count (existing)
        BOT_COUNT=$(docker exec "agent0-$N" bash -c "ps aux 2>/dev/null | grep -E 'matrix_bot|matrix-bot-rust' | grep -v grep | wc -l" 2>/dev/null || echo "0"); BOT_COUNT=$(echo "$BOT_COUNT" | tr -d '[:space:]'); [ -z "$BOT_COUNT" ] && BOT_COUNT=0
        if [ "$BOT_COUNT" -eq 1 ]; then
            BOT_TXT="$BOT_COUNT"
            BOT_CLR="${GREEN}"
        elif [ "$BOT_COUNT" -gt 1 ]; then
            BOT_TXT="${BOT_COUNT} ⚠"
            BOT_CLR="${YELLOW}"
        else
            BOT_TXT="0"
            BOT_CLR="${RED}"
        fi

        # MCP process
        MCP_ALIVE=$(docker exec "agent0-$N" bash -c "ps aux 2>/dev/null | grep 'http-server' | grep -v grep | wc -l" 2>/dev/null || echo "0"); MCP_ALIVE=$(echo "$MCP_ALIVE" | tr -d '[:space:]'); [ -z "$MCP_ALIVE" ] && MCP_ALIVE=0
        if [ "$MCP_ALIVE" -ge 1 ]; then
            MCP_TXT="✓"
            MCP_CLR="${GREEN}"
        else
            MCP_TXT="✗"
            MCP_CLR="${RED}"
        fi

        # Watchdog
        WD_ALIVE=$(docker exec "agent0-$N" bash -c "ps aux 2>/dev/null | grep 'watchdog' | grep -v grep | wc -l" 2>/dev/null || echo "0"); WD_ALIVE=$(echo "$WD_ALIVE" | tr -d '[:space:]'); [ -z "$WD_ALIVE" ] && WD_ALIVE=0
        if [ "$WD_ALIVE" -ge 1 ]; then
            WD_TXT="✓"
            WD_CLR="${GREEN}"
        else
            WD_TXT="✗"
            WD_CLR="${RED}"
        fi

        # Last update status
        LAST_UPD=$(docker exec "agent0-$N" cat "$STATUS_FILE" 2>/dev/null | \
            python3 -c "
import sys, yaml
try:
    d = yaml.safe_load(sys.stdin.read())
    if d:
        st = d.get('status', '?')
        sv = d.get('source_version', '?')
        cv = d.get('current_version', '?')
        print(f'{st} ({sv}→{cv})')
    else:
        print('none')
except:
    print('none')
" 2>/dev/null)
        [ -z "$LAST_UPD" ] && LAST_UPD="none"

        # Build row with NEW columns
        ROW=$(printf "  %-14s" "agent0-$N")
        ROW+=$(printf " ${CONTAINER_CLR}%-11s${NC}" "$CONTAINER_TXT")
        ROW+=$(printf " %-10s" "$RUN_VER")
        ROW+=$(printf " ${COMPOSE_CLR}%-10s${NC}" "$COMPOSE_TXT")
        ROW+=$(printf " ${BOT_RT_CLR}%-7s${NC}" "$BOT_RT_TXT")
        ROW+=$(printf " ${BOT_VER_CLR}%-8s${NC}" "$BOT_VER_TXT")
        ROW+=$(printf " ${BOT_CLR}%-10s${NC}" "$BOT_TXT")
        # MCP: ✓/✗ is 3 bytes but 1 col
        ROW+=$(printf " ${MCP_CLR}%s${NC}" "$MCP_TXT")
        ROW+="      "
        ROW+=$(printf "${WD_CLR}%s${NC}" "$WD_TXT")
        ROW+="   "
        ROW+="$LAST_UPD"
        echo -e "$ROW"

        # Verbose: show more details including bot runtime info
        if [ "$VERBOSE" = true ]; then
            HS_CODE=$(docker exec "agent0-$N" curl -s -o /dev/null -w "%{http_code}" "http://agent0-${N}-mhs:8008/_matrix/client/versions" 2>/dev/null || echo "000")
            HEALTH_CODE=$(get_health_status "$N")
            UPTIME=$(docker ps --filter "name=^agent0-${N}$" --format '{{.Status}}' 2>/dev/null || echo "?")
            LAST_HEALTH=$(docker exec "agent0-$N" grep 'HEALTH' /a0/usr/workdir/startup-services.log 2>/dev/null | tail -1 || echo "N/A")

            echo "             Homeserver: HTTP $HS_CODE | Health API: HTTP $HEALTH_CODE"
            echo "             Uptime: $UPTIME"
            echo "             Bot: runtime=$BOT_RT configured=$BOT_RT_CFG hash=$BOT_HASH tmpl=$TMPL_CMP"
            echo "             Last watchdog health: $LAST_HEALTH"
            echo ""
        fi
    done

    echo ""
    log_header "  Legend: BotRT=running runtime | BotVer=code fingerprint (⚠=drift from template)"
    log_header "═══════════════════════════════════════════════════════════════"
    exit 0
fi



# --- Cleanup Mode ---

if [ "$CLEANUP_MODE" = true ]; then
    set +e  # Disable exit-on-error for cleanup checks
    log_header "==============================================="
    log_header "  Agent-Matrix Fleet -- Zombie Bot Cleanup"
    log_header "==============================================="
    echo ""

    CLEANED=0
    CLEAN=0
    ERRORS=0

    for N in $INSTANCES; do
        if ! is_container_running "$N"; then
            log "  ${YELLOW}[agent0-$N] Container not running -- SKIP${NC}"
            continue
        fi

        ACTIVE_PID=$(docker exec "agent0-$N" cat /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null || echo "")
        ALL_PIDS=$(docker exec "agent0-$N" ps aux 2>/dev/null | grep -E 'matrix_bot|matrix-bot-rust' | grep -v grep | awk '{print $2}')
        BOT_COUNT=$(echo "$ALL_PIDS" | grep -c . 2>/dev/null || echo "0")

        if [ -z "$ALL_PIDS" ] || [ "$BOT_COUNT" -eq 0 ]; then
            log "  ${RED}[agent0-$N] No bot processes found${NC}"
            ERRORS=$((ERRORS + 1))
            continue
        fi

        if [ "$BOT_COUNT" -eq 1 ]; then
            log "  ${GREEN}[agent0-$N] Clean -- 1 bot process (PID $ACTIVE_PID)${NC}"
            CLEAN=$((CLEAN + 1))
            continue
        fi

        KILLED=0
        for PID in $ALL_PIDS; do
            if [ "$PID" != "$ACTIVE_PID" ]; then
                docker exec "agent0-$N" kill -9 "$PID" 2>/dev/null || true
                log "  ${YELLOW}[agent0-$N] Killed zombie PID $PID${NC}"
                KILLED=$((KILLED + 1))
            fi
        done

        sleep 1
        REMAINING=$(docker exec "agent0-$N" ps aux 2>/dev/null | grep -E 'matrix_bot|matrix-bot-rust' | grep -v grep | wc -l || echo "0")
        REMAINING=$(echo "$REMAINING" | tr -d '[:space:]'); [ -z "$REMAINING" ] && REMAINING=0
        if [ "$REMAINING" -eq 1 ]; then
            log "  ${GREEN}[agent0-$N] Cleaned $KILLED zombie(s) -- 1 process remaining (PID $ACTIVE_PID)${NC}"
            CLEANED=$((CLEANED + 1))
        else
            log "  ${RED}[agent0-$N] $REMAINING processes remaining after cleanup${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done

    echo ""
    log_header "==============================================="
    log "  ${GREEN}Already clean: $CLEAN${NC}  |  ${YELLOW}Cleaned: $CLEANED${NC}  |  ${RED}Errors: $ERRORS${NC}"
    log_header "==============================================="
    exit 0
fi

if [ -z "$VERSION" ]; then
    echo -e "${RED}ERROR: --version is required (or use --status / --cleanup)${NC}"
    echo "Use --help for usage."
    exit 1
fi

# --- Preflight Checks ---

log_header "═══════════════════════════════════════════════════"
log_header "  update-fleet.sh — Zero-Touch Fleet Updater v1.3"
log_header "═══════════════════════════════════════════════════"
echo ""
log "  Target version:  ${BOLD}$VERSION${NC}"
log "  Branch:          ${BOLD}$BRANCH${NC}"
log "  Instances:       ${BOLD}$INSTANCES${NC}"
log "  Backup:          ${BOLD}$([ $NO_BACKUP = true ] && echo 'disabled' || echo 'enabled')${NC}"
log "  Mode:            ${BOLD}sequential (always)${NC}"
log "  Skip restart:    ${BOLD}$SKIP_RESTART${NC}"
log "  Dry run:         ${BOLD}$DRY_RUN${NC}"
echo ""

# Check host prerequisites
if ! command -v python3 >/dev/null 2>&1; then
    log "${RED}ERROR: python3 not found on host${NC}"
    exit 1
fi
python3 -c "import yaml" 2>/dev/null || {
    log "${YELLOW}WARNING: PyYAML not available on host, installing...${NC}"
    pip3 install pyyaml >/dev/null 2>&1 || {
        log "${RED}ERROR: Failed to install PyYAML. Install manually: pip3 install pyyaml${NC}"
        exit 1
    }
}

# --- Phase 1: Pre-flight version check ---

log_header "Phase 1: Pre-flight Version Check"

declare -A CURRENT_VERSIONS
declare -A INSTANCE_STATUS
SKIPPED=0
TARGETED=0

for N in $INSTANCES; do
    if ! is_container_running "$N"; then
        log "  ${YELLOW}[agent0-$N] Container not running — SKIPPING${NC}"
        INSTANCE_STATUS[$N]="skipped:not_running"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    CUR_VER=$(get_current_version "$N")
    CURRENT_VERSIONS[$N]="$CUR_VER"

    if [ "$VERSION" != "latest" ] && [ "$CUR_VER" = "$VERSION" ] && [ "$FORCE" != true ]; then
        log "  ${GREEN}[agent0-$N] Already at $VERSION — SKIPPING${NC}"
        INSTANCE_STATUS[$N]="skipped:already_current"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    log "  [agent0-$N] Current: ${BOLD}$CUR_VER${NC} → Target: ${BOLD}$VERSION${NC}"
    INSTANCE_STATUS[$N]="pending"
    TARGETED=$((TARGETED + 1))
done

if [ $TARGETED -eq 0 ]; then
    log "\n${GREEN}All instances are already at target version or skipped. Nothing to do.${NC}"
    exit 0
fi

log "\n  Targeted: $TARGETED | Skipped: $SKIPPED"

if [ "$DRY_RUN" = true ]; then
    log "\n${YELLOW}DRY RUN — would trigger update on $TARGETED instance(s). Exiting.${NC}"
    exit 0
fi

# --- Phase 2: Queue Updates (sequential — bash subshells cannot modify parent associative arrays) ---

log_header "Phase 2: Queueing Self-Updates"

BACKUP_FLAG=""
[ "$NO_BACKUP" = true ] && BACKUP_FLAG="--no-backup"

for N in $INSTANCES; do
    [ "${INSTANCE_STATUS[$N]:-}" != "pending" ] && continue

    log "  [agent0-$N] Triggering update..."

    # Clear any previous status file
    docker exec "agent0-$N" rm -f "$STATUS_FILE" 2>/dev/null || true

    # Queue the update
    OUTPUT=$(docker exec "agent0-$N" "$VENV_PYTHON" "$TRIGGER_SCRIPT" trigger-update "$BRANCH" "$VERSION" $BACKUP_FLAG 2>&1)
    RC=$?

    if [ $RC -eq 0 ]; then
        log "  ${GREEN}[agent0-$N] Update queued successfully${NC}"
        [ "$VERBOSE" = true ] && echo "$OUTPUT" | sed 's/^/    /'
        INSTANCE_STATUS[$N]="queued"
    else
        log "  ${RED}[agent0-$N] Failed to queue update (rc=$RC)${NC}"
        echo "$OUTPUT" | sed 's/^/    /'
        INSTANCE_STATUS[$N]="failed:trigger"
    fi
done

if [ "$SKIP_RESTART" = true ]; then
    log "\n${YELLOW}Updates queued. Restart containers manually to apply:${NC}"
    for N in $INSTANCES; do
        [ "${INSTANCE_STATUS[$N]:-}" = "queued" ] && echo "  docker restart agent0-$N"
    done
    exit 0
fi

# --- Phase 3: Restart Containers (sequential — need status tracking) ---

log_header "Phase 3: Restarting Containers"

for N in $INSTANCES; do
    [ "${INSTANCE_STATUS[$N]:-}" != "queued" ] && continue

    log "  [agent0-$N] Restarting container..."
    docker restart "agent0-$N" >/dev/null 2>&1

    # Wait for container to come back up
    if ! wait_for_container_up "$N"; then
        log "  ${RED}[agent0-$N] Container failed to start within 60s${NC}"
        INSTANCE_STATUS[$N]="failed:restart"
        continue
    fi
    log "  [agent0-$N] Container is back up"

    # Wait for update to process
    log "  [agent0-$N] Waiting for update to complete..."
    if ! wait_for_update_complete "$N"; then
        log "  ${YELLOW}[agent0-$N] Update status not confirmed within ${UPDATE_TIMEOUT}s${NC}"
        INSTANCE_STATUS[$N]="uncertain:timeout"
    else
        UPD_STATUS=$(get_update_status "$N")
        log "  [agent0-$N] Update status: $UPD_STATUS"
    fi

    # Wait for health
    log "  [agent0-$N] Waiting for health endpoint..."
    if ! wait_for_health "$N"; then
        log "  ${RED}[agent0-$N] Health check failed after ${HEALTH_TIMEOUT}s${NC}"
        INSTANCE_STATUS[$N]="failed:health"
        continue
    fi

    # Verify version
    NEW_VER=$(get_current_version "$N")
    OLD_VER="${CURRENT_VERSIONS[$N]:-unknown}"

    if [ "$VERSION" != "latest" ] && [ "$NEW_VER" = "$VERSION" ]; then
        log "  ${GREEN}[agent0-$N] ✅ Updated: $OLD_VER → $NEW_VER${NC}"
        INSTANCE_STATUS[$N]="success"
    elif [ "$VERSION" = "latest" ]; then
        log "  ${GREEN}[agent0-$N] ✅ Updated: $OLD_VER → $NEW_VER (latest)${NC}"
        INSTANCE_STATUS[$N]="success"
    else
        log "  ${YELLOW}[agent0-$N] ⚠️ Version mismatch: expected $VERSION, got $NEW_VER${NC}"
        INSTANCE_STATUS[$N]="warning:version_mismatch"
    fi

    # Update docker-compose.yml image tag to match actual running version
    if [[ "${INSTANCE_STATUS[$N]}" == "success" ]] && [ -n "$NEW_VER" ] && [ "$NEW_VER" != "unknown" ]; then
        COMPOSE_FILE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
        if [ -f "$COMPOSE_FILE" ]; then
            OLD_IMG=$(grep 'image: agent0ai/agent-zero:' "$COMPOSE_FILE" | grep -oP 'v[0-9.]+' | head -1)
            if [ -n "$OLD_IMG" ] && [ "$OLD_IMG" != "$NEW_VER" ]; then
                sed -i "s|image: agent0ai/agent-zero:${OLD_IMG}|image: agent0ai/agent-zero:${NEW_VER}|" "$COMPOSE_FILE"
                log "  [agent0-$N] 📦 docker-compose.yml updated: ${OLD_IMG} → ${NEW_VER}"
            fi
        fi
    fi

    # Cleanup zombie bot processes
    cleanup_zombie_bots "$N"
done

# --- Phase 4: Final Report ---

log_header "Phase 4: Fleet Update Report"
echo ""

SUCCESS=0
FAILED=0
WARNING=0

printf "  ${BOLD}%-12s %-12s %-12s %-20s %-10s${NC}\n" "Instance" "Before" "After" "Status" "Result"
printf "  %-12s %-12s %-12s %-20s %-10s\n" "--------" "------" "-----" "------" "------"

for N in $INSTANCES; do
    LOCAL_STATUS="${INSTANCE_STATUS[$N]:-unknown}"
    OLD_VER="${CURRENT_VERSIONS[$N]:-N/A}"

    case "$LOCAL_STATUS" in
        success)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="${GREEN}✅ OK${NC}"
            SUCCESS=$((SUCCESS + 1))
            ;;
        skipped:*)
            NEW_VER="$OLD_VER"
            RESULT="${CYAN}⏭️ Skip${NC}"
            ;;
        failed:*)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="${RED}❌ FAIL${NC}"
            FAILED=$((FAILED + 1))
            ;;
        warning:*)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="${YELLOW}⚠️ WARN${NC}"
            WARNING=$((WARNING + 1))
            ;;
        uncertain:*)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="${YELLOW}❓ UNCRT${NC}"
            WARNING=$((WARNING + 1))
            ;;
        *)
            NEW_VER="?"
            RESULT="${YELLOW}? UNK${NC}"
            WARNING=$((WARNING + 1))
            ;;
    esac

    printf "  %-12s %-12s %-12s %-20s %b\n" "agent0-$N" "$OLD_VER" "$NEW_VER" "$LOCAL_STATUS" "$RESULT"
done

echo ""
log_header "═══════════════════════════════════════════════════"
log "  ${GREEN}Success: $SUCCESS${NC}  |  ${RED}Failed: $FAILED${NC}  |  ${YELLOW}Warning: $WARNING${NC}  |  Skipped: $SKIPPED"
log_header "═══════════════════════════════════════════════════"

# Show update logs for failed/warning instances
if [ "$VERBOSE" = true ] || [ $FAILED -gt 0 ]; then
    for N in $INSTANCES; do
        LOCAL_STATUS="${INSTANCE_STATUS[$N]:-}"
        if [[ "$LOCAL_STATUS" == failed:* ]] || [[ "$LOCAL_STATUS" == warning:* ]] || [ "$VERBOSE" = true ]; then
            echo ""
            log "  [agent0-$N] Update log (last 20 lines):"
            docker exec "agent0-$N" tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/    /' || echo "    (no log available)"
        fi
    done
fi

# Exit code
if [ $FAILED -gt 0 ]; then
    exit 1
elif [ $WARNING -gt 0 ]; then
    exit 2
else
    exit 0
fi
