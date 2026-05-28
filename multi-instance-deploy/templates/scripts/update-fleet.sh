#!/bin/bash
# =============================================================================
# update-fleet.sh — Docker Image Replacement Fleet Updater (v2.2)
# =============================================================================
# Replaces the git-based self-update mechanism with direct docker image tag
# replacement and container recreation.  This avoids dependency on the
# container's internal git state after Framework v1.10+ changes.
#
# Usage:
#   ./update-fleet.sh --status
#   ./update-fleet.sh --version v1.11    # update to an explicit tag
#   ./update-fleet.sh --version latest   # resolve latest GitHub release
#   ./update-fleet.sh --instances 2,3 --version v1.11
#   ./update-fleet.sh --dry-run --version v1.11
#   ./update-fleet.sh --json --version v1.11
#   ./update-fleet.sh --force --version v1.11
#   ./update-fleet.sh --skip-restart --version v1.11  # update compose only
# =============================================================================
# v2.2 changes:
#   - Detect service name dynamically from compose file (fixes 'no such service'
#     errors when service name != instance name, e.g. 'agent-zero' vs 'agent0-N')
#   - When not using --skip-restart, compose update and container recreate are
#     now tightly coupled per-instance (eliminates drift on partial failure)
#   - --skip-restart retains original batch compose-update-only behavior
# =============================================================================

set -euo pipefail

BASE_DIR="/opt/agent-zero"
ALL_INSTANCES="1 2 3 4 5"
HEALTH_TIMEOUT=180
HEALTH_POLL_INTERVAL=5
HEALTH_URL="http://127.0.0.1:80/api/health"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

VERSION=""
INSTANCES=""
DRY_RUN=false
FORCE=false
JSON_OUTPUT=false
STATUS_MODE=false
CLEANUP_MODE=false
SKIP_RESTART=false

log() { echo -e "$(date '+%H:%M:%S') $1"; }
log_header() { echo -e "\n${CYAN}${BOLD}$1${NC}"; }

is_container_running() {
    local N=$1
    docker ps --format '{{.Names}}' | grep -qx "agent0-$N" 2>/dev/null
}

get_current_version() {
    local N=$1
    docker exec "agent0-$N" curl -s "$HEALTH_URL" 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('gitinfo',{}).get('short_tag','unknown'))" 2>/dev/null || echo "unreachable"
}

get_health_status() {
    local N=$1
    docker exec "agent0-$N" curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000"
}

resolve_latest_tag() {
    # Return the most recent tag from GitHub releases API
    curl -s https://api.github.com/repos/agent0ai/agent-zero/tags 2>/dev/null | \
        python3 -c "import sys,json; tags=json.load(sys.stdin); print(tags[0]['name'] if tags else 'v1.0')" 2>/dev/null || echo "v1.0"
}

# Detect the first service name declared in a docker-compose.yml.
# Compose files in this fleet use 'agent-zero' (instances 2-5) or
# 'agent0-N' (instance 1) as the service name — never rely on the
# instance number alone.
get_service_name() {
    local compose_file=$1
    awk '/^services:/{found=1; next} found && /^  [a-zA-Z]/{gsub(/:.*$/,""); gsub(/^  /,""); print; exit}' "$compose_file"
}

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]
Modes:
  --status              Fleet status (identical to original)
  --version TAG         Target version tag (e.g., v1.11, latest)
  --cleanup             Kill zombie/duplicate bot processes across fleet
Options:
  --instances N,N,...   Instance numbers (default: all)
  --dry-run             Show planned changes without executing
  --force               Update even if already at target version
  --json                JSON output
  --skip-restart        Update compose files only; do NOT recreate containers
  -h, --help            This help
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)     VERSION="$2"; shift 2 ;;
        --status)      STATUS_MODE=true; shift ;;
        --cleanup)      CLEANUP_MODE=true; shift ;;
        --instances)   INSTANCES=$(echo "$2" | tr ',' ' '); shift 2 ;;
        --dry-run)     DRY_RUN=true; shift ;;
        --force)       FORCE=true; shift ;;
        --json)        JSON_OUTPUT=true; shift ;;
        --skip-restart) SKIP_RESTART=true; shift ;;
        -h|--help)     usage ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

INSTANCES="${INSTANCES:-$ALL_INSTANCES}"

# --- Status Mode: Fleet-wide health report ---
if [ "$STATUS_MODE" = true ]; then
    echo ""
    printf "  ${BOLD}%-14s %-11s %-12s %-12s %-7s %-10s %-4s %s${NC}\n" \
        "Instance" "Container" "Version" "Compose" "Bot" "MCP" "WD" "Last Update"
    printf "  %-14s %-11s %-12s %-12s %-7s %-10s %-4s %s\n" \
        "------------" "---------" "-------" "-------" "-----" "--------" "--" "-----------"
    for N in $INSTANCES; do
        CONT="down"
        CUR_VER="—"
        COMPOSE_TAG="—"
        COMPOSE_CLR=""
        COMPOSE_DRIFT=""
        BOT_CNT=0
        BOT_CLR=""
        MCP_TXT="—"
        WD="✗"
        LAST_UPDATE="none"
        if is_container_running "$N"; then
            CONT="up"
            CUR_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            COMPOSE_YML="${BASE_DIR}/agent0-${N}/docker-compose.yml"
            if [ -f "$COMPOSE_YML" ]; then
                COMPOSE_TAG=$(grep 'image: agent0ai/agent-zero:' "$COMPOSE_YML" 2>/dev/null | grep -oP 'v[0-9.]+' | head -1 || echo "?")
            fi
            # --- Drift detection: version vs compose ---
            if [ -n "$COMPOSE_TAG" ] && [ "$COMPOSE_TAG" != "?" ] && [ "$COMPOSE_TAG" != "$CUR_VER" ]; then
                COMPOSE_CLR="${YELLOW}"
                COMPOSE_DRIFT=" ⚠"
            fi
            BOT_CNT=$(docker exec "agent0-$N" pgrep -f matrix-bot-rust 2>/dev/null | wc -l) || true
            # --- Drift detection: bot count != 1 ---
            if [ "$BOT_CNT" -ne 1 ]; then
                BOT_CLR="${YELLOW}"
            fi
            # MCP detection: check for bot process first, then MCP server as fallback
            MCP_PID=$(docker exec "agent0-$N" pgrep -f matrix-bot-rust 2>/dev/null | head -1) || true
            if [ -n "$MCP_PID" ]; then
                MCP_TXT="r2:0.1.1"
            elif docker exec "agent0-$N" pgrep -f python3.*matrix_bot 2>/dev/null >/dev/null; then
                MCP_TXT="py"
            elif docker exec "agent0-$N" pgrep -f matrix-mcp-server 2>/dev/null >/dev/null; then
                MCP_TXT="r2:0.1.1"
            elif docker exec "agent0-$N" pgrep -f http-server 2>/dev/null >/dev/null; then
                MCP_TXT="ts"
            fi
            if docker exec "agent0-$N" pgrep -f watchdog >/dev/null 2>&1; then WD="✓"; fi
            # Last Update: try host-side persistent status first, then legacy container-internal
            HOST_STATUS="${BASE_DIR}/agent0-${N}/update-status.yaml"
            if [ -f "$HOST_STATUS" ]; then
                LAST_UPDATE=$(awk '
                    /^status:/ {gsub(/^[^:]*: */,""); status=$0}
                    /^source_version:/ {gsub(/^[^:]*: */,""); src=$0}
                    /^current_version:/ {gsub(/^[^:]*: */,""); cur=$0}
                    END {if(status) print status " (" src "->" cur ")"; else print "none"}
                ' "$HOST_STATUS")
            elif docker exec "agent0-$N" test -f /exe/a0-self-update-status.yaml >/dev/null 2>&1; then
                LAST_UPDATE=$(docker exec "agent0-$N" cat /exe/a0-self-update-status.yaml | awk '
                    /^status:/ {gsub(/^[^:]*: */,""); status=$0}
                    /^source_version:/ {gsub(/^[^:]*: */,""); src=$0}
                    /^current_version:/ {gsub(/^[^:]*: */,""); cur=$0}
                    END {if(status) print status " (" src "->" cur ")"; else print "none"}
                ')
            else
                LAST_UPDATE="none"
            fi
        fi
        ROW=$(printf "  %-14s" "agent0-$N")
        ROW+=$(printf " %-11s" "$CONT")
        ROW+=$(printf " %-12s" "$CUR_VER")
        ROW+=$(printf " ${COMPOSE_CLR}%-12s${NC}" "${COMPOSE_TAG}${COMPOSE_DRIFT}")
        ROW+=$(printf " ${BOT_CLR}%-7s${NC}" "$BOT_CNT")
        ROW+=$(printf " %-10s" "$MCP_TXT")
        ROW+=$(printf " %-4s" "$WD")
        ROW+=$(printf " %s" "$LAST_UPDATE")
        echo "$ROW"
    done
    echo ""
    exit 0
fi

# --- Cleanup Mode: Kill zombie/duplicate bot processes ---
if [ "$CLEANUP_MODE" = true ]; then
    echo ""
    echo "  Killing duplicate/zombie bot processes fleet-wide..."
    CLEANED=0
    ERRORS=0
    for N in $INSTANCES; do
        if ! is_container_running "$N"; then
            echo "  [agent0-$N] Container not running — skipping"
            continue
        fi
        BOT_CNT=$(docker exec "agent0-$N" pgrep -f matrix-bot-rust 2>/dev/null | wc -l) || true
        if [ "$BOT_CNT" -le 1 ]; then
            echo "  [agent0-$N] Bot count $BOT_CNT — clean, skipping"
        else
            echo "  [agent0-$N] Bot count $BOT_CNT — killing all, will restart one"
            docker exec "agent0-$N" pkill -9 -f matrix-bot-rust 2>/dev/null || true
            sleep 2
            docker exec -d "agent0-$N" bash -c '
                cd /a0/usr/workdir/matrix-bot
                nohup ./run-matrix-bot.sh >> bot.log 2>&1 &
                NEW_PID=$!
                echo $NEW_PID > /a0/usr/workdir/matrix-bot/bot.pid
                echo $NEW_PID
            ' 2>/dev/null
            sleep 3
            NEW_CNT=$(docker exec "agent0-$N" pgrep -f matrix-bot-rust 2>/dev/null | wc -l)
            if [ "$NEW_CNT" -eq 1 ]; then
                echo "  [agent0-$N] ✓ Cleaned — now 1 bot"
                CLEANED=$((CLEANED + 1))
            else
                echo "  [agent0-$N] ✗ Restart issue — now $NEW_CNT bots"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    done
    echo ""
    echo "  Cleaned: $CLEANED | Errors: $ERRORS"
    echo ""
    exit 0
fi

if [ -z "$VERSION" ]; then
    usage
fi

# Resolve "latest" to concrete tag
if [ "$VERSION" = "latest" ]; then
    log "Resolving latest GitHub tag..."
    VERSION=$(resolve_latest_tag)
    log "Resolved latest tag: $VERSION"
fi

log_header "═══════════════════════════════════════════════════"
log_header "  Docker Image Replacement Fleet Updater v2.2"
log_header "═══════════════════════════════════════════════════"
echo ""
log "  Target version:  ${BOLD}${VERSION}${NC}"
log "  Instances:       ${BOLD}${INSTANCES}${NC}"
log "  Dry run:         ${BOLD}${DRY_RUN}${NC}"
log "  Skip restart:    ${BOLD}${SKIP_RESTART}${NC}"
echo ""

# Phase 1: Pre-flight version check
log_header "Phase 1: Pre-flight Version Check"
declare -A CURRENT_VERSIONS
declare -A INSTANCE_STATUS
SKIPPED=0
TARGETED=0

for N in $INSTANCES; do
    if ! is_container_running "$N"; then
        log "  ${YELLOW}[agent0-$N] Container not running — SKIPPING${NC}"
        CURRENT_VERSIONS[$N]="unreachable"
        INSTANCE_STATUS[$N]="skipped"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    CUR_VER=$(get_current_version "$N")
    CURRENT_VERSIONS[$N]="$CUR_VER"

    if [ "$CUR_VER" = "$VERSION" ] && [ "$FORCE" = false ]; then
        log "  ${GREEN}[agent0-$N] Already at ${VERSION} — skipping${NC}"
        INSTANCE_STATUS[$N]="current"
        SKIPPED=$((SKIPPED + 1))
    else
        log "  ${CYAN}[agent0-$N] ${CUR_VER} → ${VERSION} (target)${NC}"
        INSTANCE_STATUS[$N]="target"
        TARGETED=$((TARGETED + 1))
    fi
done

if [ "$TARGETED" -eq 0 ]; then
    if [ "$SKIP_RESTART" = true ]; then
        log_header "All instances already at ${VERSION}, but --skip-restart will refresh compose files."
    else
        log_header "All instances already at ${VERSION}. Use --force to override."
        echo ""
        exit 0
    fi
fi

if [ "$JSON_OUTPUT" = true ]; then
    printf '{"skipped":%d,"targeted":%d,instances:{"' "$SKIPPED"
    FIRST=true
    for N in $INSTANCES; do
        [ "$FIRST" = true ] || printf ','
        FIRST=false
        printf '%s":"%s"' "$N" "${INSTANCE_STATUS[$N]}"
    done
    printf '}}\n'
fi

if [ "$DRY_RUN" = true ]; then
    log_header "DRY RUN — no changes made."
    echo ""
    exit 0
fi

# =============================================================================
# --skip-restart mode: batch-update compose files only, no container restart.
# This is the only mode where compose update runs as a separate upfront phase.
# =============================================================================
if [ "$SKIP_RESTART" = true ]; then
    log_header "Phase 2 (skip-restart): Update docker-compose.yml files only"
    UPDATED=0
    FAILED=0
    for N in $INSTANCES; do
        if [ "${INSTANCE_STATUS[$N]}" != "target" ] && [ "${INSTANCE_STATUS[$N]}" != "current" ]; then
            continue
        fi
        COMPOSE_FILE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
        if [ ! -f "$COMPOSE_FILE" ]; then
            log "  ${RED}[agent0-$N] Missing ${COMPOSE_FILE}${NC}"
            FAILED=$((FAILED + 1))
            continue
        fi
        cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%s)" 2>/dev/null || true
        sed -i "s|agent0ai/agent-zero:.*|agent0ai/agent-zero:${VERSION}|" "$COMPOSE_FILE"
        NEW_TAG=$(grep 'image: agent0ai/agent-zero:' "$COMPOSE_FILE" 2>/dev/null | grep -oP 'v[0-9.]+' | head -1 || echo "?")
        if [ "$NEW_TAG" = "$VERSION" ]; then
            log "  ${GREEN}[agent0-$N] Updated compose to ${VERSION}${NC}"
            UPDATED=$((UPDATED + 1))
        else
            log "  ${RED}[agent0-$N] Compose tag mismatch after sed: ${NEW_TAG}${NC}"
            FAILED=$((FAILED + 1))
        fi
    done
    log "  Updated: ${UPDATED} | Failed: ${FAILED}"
    log_header "SKIP-RESTART mode — compose files updated, containers NOT restarted."
    echo ""
    exit 0
fi

# =============================================================================
# Normal mode: update compose + recreate are tightly coupled per-instance.
# The compose file is updated immediately before recreating that container,
# so a failure mid-fleet never leaves compose/container versions out of sync.
# Service name is detected dynamically from the compose file — do NOT assume
# it matches the instance name (e.g. instances 2-5 use 'agent-zero', not
# 'agent0-N').
# =============================================================================
log_header "Phase 2+3: Update compose and recreate containers (per-instance)"
UPDATED=0
RECREATED=0
FAILED=0

for N in $INSTANCES; do
    if [ "${INSTANCE_STATUS[$N]}" != "target" ] && [ "${INSTANCE_STATUS[$N]}" != "current" ]; then
        continue
    fi

    CUR_VER="${CURRENT_VERSIONS[$N]}"
    COMPOSE_FILE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
    COMPOSE_DIR="${BASE_DIR}/agent0-${N}"

    if [ ! -f "$COMPOSE_FILE" ]; then
        log "  ${RED}[agent0-$N] Missing ${COMPOSE_FILE} — skipping${NC}"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Detect the actual service name from the compose file
    SERVICE_NAME=$(get_service_name "$COMPOSE_FILE")
    if [ -z "$SERVICE_NAME" ]; then
        log "  ${RED}[agent0-$N] Could not detect service name in ${COMPOSE_FILE} — skipping${NC}"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Update compose file
    cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%s)" 2>/dev/null || true
    sed -i "s|agent0ai/agent-zero:.*|agent0ai/agent-zero:${VERSION}|" "$COMPOSE_FILE"
    NEW_TAG=$(grep 'image: agent0ai/agent-zero:' "$COMPOSE_FILE" 2>/dev/null | grep -oP 'v[0-9.]+' | head -1 || echo "?")
    if [ "$NEW_TAG" != "$VERSION" ]; then
        log "  ${RED}[agent0-$N] Compose tag mismatch after sed: ${NEW_TAG} — skipping recreate${NC}"
        FAILED=$((FAILED + 1))
        continue
    fi
    log "  ${GREEN}[agent0-$N] Compose updated to ${VERSION} (service: ${SERVICE_NAME})${NC}"
    UPDATED=$((UPDATED + 1))

    # Recreate container using the detected service name
    log "  [agent0-$N] docker compose up -d --no-deps --force-recreate ${SERVICE_NAME}"
    if (cd "$COMPOSE_DIR" && docker compose up -d --no-deps --force-recreate "$SERVICE_NAME" 2>&1); then
        log "  ${GREEN}[agent0-$N] Container recreated${NC}"
        RECREATED=$((RECREATED + 1))
    else
        log "  ${RED}[agent0-$N] Failed to recreate${NC}"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Wait for health
    log "  [agent0-$N] Waiting for health..."
    HEALTHY=false
    ELAPSED=0
    while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
        CODE=$(get_health_status "$N")
        if [ "$CODE" = "200" ]; then
            HEALTHY=true
            break
        fi
        sleep $HEALTH_POLL_INTERVAL
        ELAPSED=$((ELAPSED + HEALTH_POLL_INTERVAL))
    done

    if [ "$HEALTHY" = true ]; then
        NEW_VER=$(get_current_version "$N")
        log "  ${GREEN}[agent0-$N] Healthy — ${NEW_VER}${NC}"
        # Persist update status on host so it survives future recreations
        cat > "${BASE_DIR}/agent0-${N}/update-status.yaml" <<EOF
status: success
message: Updated Agent Zero to ${NEW_VER}
source_version: ${CUR_VER}
current_version: ${NEW_VER}
updated_at: $(date -Iseconds)
EOF
    else
        log "  ${YELLOW}[agent0-$N] Health check timed out${NC}"
    fi
done

echo ""
log_header "═══════════════════════════════════════════════════"
log_header "  Done: Updated ${UPDATED} | Recreated ${RECREATED} | Failed ${FAILED}"
log_header "═══════════════════════════════════════════════════"
echo ""
