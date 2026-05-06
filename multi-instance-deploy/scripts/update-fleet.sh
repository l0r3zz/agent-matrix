#!/bin/bash
# =============================================================================
# update-fleet.sh — Docker Image Replacement Fleet Updater (v2.0)
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
  --skip-restart        Update compose files without restarting containers
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

if [ "$STATUS_MODE" = true ]; then
    # Use original script for status (unchanged)
    exec "${BASE_DIR}/multi-instance-deploy/templates/scripts/update-fleet.sh.bak" --status "$@"
fi

if [ "$CLEANUP_MODE" = true ]; then
    exec "${BASE_DIR}/multi-instance-deploy/templates/scripts/update-fleet.sh.bak" --cleanup "$@"
fi

if [ -z "$VERSION" ]; then
    echo -e "${RED}ERROR: --version is required${NC}"
    usage
fi

# Resolve "latest" to concrete tag
if [ "$VERSION" = "latest" ]; then
    log "Resolving latest GitHub tag..."
    VERSION=$(resolve_latest_tag)
    log "Resolved latest tag: $VERSION"
fi

log_header "═══════════════════════════════════════════════════"
log_header "  Docker Image Replacement Fleet Updater v2.0"
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
        INSTANCE_STATUS[$N]="skipped:not_running"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    CUR_VER=$(get_current_version "$N")
    CURRENT_VERSIONS[$N]="$CUR_VER"
    if [ "$SKIP_RESTART" = true ]; then
        # In skip-restart mode, check compose file tag, not running version
        COMPOSE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
        if [ -f "$COMPOSE" ]; then
            COMPOSE_TAG=$(grep -oP 'agent0ai/agent-zero:\Kv[0-9.]+' "$COMPOSE" | head -1)
            if [ "$COMPOSE_TAG" = "$VERSION" ]; then
                log "  ${GREEN}[agent0-$N] Compose file already at $VERSION (skip-restart) — SKIPPING${NC}"
                INSTANCE_STATUS[$N]="skipped:compose_already_current"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi
            log "  [agent0-$N] Compose: ${BOLD}$COMPOSE_TAG${NC} → Target: ${BOLD}$VERSION${NC} (running: $CUR_VER)"
        else
            log "  ${RED}[agent0-$N] No docker-compose.yml found${NC}"
            INSTANCE_STATUS[$N]="failed:missing_compose"
            continue
        fi
    elif [ "$CUR_VER" = "$VERSION" ] && [ "$FORCE" != true ]; then
        log "  ${GREEN}[agent0-$N] Already at $VERSION — SKIPPING${NC}"
        INSTANCE_STATUS[$N]="skipped:already_current"
        SKIPPED=$((SKIPPED + 1))
        continue
    else
        log "  [agent0-$N] Current: ${BOLD}$CUR_VER${NC} → Target: ${BOLD}$VERSION${NC}"
    fi
    INSTANCE_STATUS[$N]="pending"
    TARGETED=$((TARGETED + 1))
done

if [ $TARGETED -eq 0 ]; then
    log "\n${GREEN}All instances already at target version. Nothing to do.${NC}"
    exit 0
fi

if [ "$DRY_RUN" = true ]; then
    log "\n${YELLOW}DRY RUN — would update $TARGETED instance(s). Exiting.${NC}"
    exit 0
fi

# Phase 2: Switch image tags
log_header "Phase 2: Switching Docker Image Tags"

for N in $INSTANCES; do
    [ "${INSTANCE_STATUS[$N]:-}" != "pending" ] && continue

    COMPOSE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
    if [ ! -f "$COMPOSE" ]; then
        log "  ${RED}[agent0-$N] No docker-compose.yml found${NC}"
        INSTANCE_STATUS[$N]="failed:missing_compose"
        continue
    fi

    OLD_TAG=$(grep -oP 'agent0ai/agent-zero:\Kv[0-9.]+' "$COMPOSE" | head -1)
    if [ -z "$OLD_TAG" ]; then
        log "  ${RED}[agent0-$N] Could not extract current image tag${NC}"
        INSTANCE_STATUS[$N]="failed:no_image_tag"
        continue
    fi

    log "  [agent0-$N] Switching image: ${OLD_TAG} → ${VERSION}"
    sed -i "s|image: agent0ai/agent-zero:${OLD_TAG}|image: agent0ai/agent-zero:${VERSION}|" "$COMPOSE"

    # Verify replacement
    NEW_TAG=$(grep -oP 'agent0ai/agent-zero:\Kv[0-9.]+' "$COMPOSE" | head -1)
    if [ "$NEW_TAG" != "$VERSION" ]; then
        log "  ${RED}[agent0-$N] Tag replacement failed (found: $NEW_TAG)${NC}"
        INSTANCE_STATUS[$N]="failed:tag_mismatch"
        continue
    fi

    INSTANCE_STATUS[$N]="tagged"
    log "  ${GREEN}[agent0-$N] Compose file updated.${NC}"
done

if [ "$SKIP_RESTART" = true ]; then
    log "\n${YELLOW}Compose files updated. Restart containers manually.${NC}"
    exit 0
fi

# Phase 3: Recreate containers
log_header "Phase 3: Recreating Containers"

SUCCESS=0
FAILED=0
WARNING=0

for N in $INSTANCES; do
    [ "${INSTANCE_STATUS[$N]:-}" != "tagged" ] && continue

    log "  [agent0-$N] Pulling new image..."
    (cd "${BASE_DIR}/agent0-${N}" && docker compose pull --quiet) || {
        log "  ${RED}[agent0-$N] Image pull failed${NC}"
        INSTANCE_STATUS[$N]="failed:pull"
        FAILED=$((FAILED + 1))
        continue
    }

    log "  [agent0-$N] Recreating container with new image..."
    (cd "${BASE_DIR}/agent0-${N}" && docker compose up -d --force-recreate) || {
        log "  ${RED}[agent0-$N] Container recreation failed${NC}"
        INSTANCE_STATUS[$N]="failed:recreate"
        FAILED=$((FAILED + 1))
        continue
    }

    # Wait for health
    log "  [agent0-$N] Waiting for healthy status..."
    ELAPSED=0
    HEALTHY=false
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
        OLD_VER="${CURRENT_VERSIONS[$N]:-unknown}"
        if [ "$NEW_VER" = "$VERSION" ]; then
            log "  ${GREEN}[agent0-$N] ✅ Updated: $OLD_VER → $NEW_VER${NC}"
            INSTANCE_STATUS[$N]="success"
            SUCCESS=$((SUCCESS + 1))
        else
            log "  ${YELLOW}[agent0-$N] ⚠️ Version mismatch: expected $VERSION, got $NEW_VER${NC}"
            INSTANCE_STATUS[$N]="warning:version_mismatch"
            WARNING=$((WARNING + 1))
        fi
    else
        log "  ${RED}[agent0-$N] Health check timeout${NC}"
        INSTANCE_STATUS[$N]="failed:health"
        FAILED=$((FAILED + 1))
    fi
done

# Phase 3.5: Sync Bot API Tokens
# After container recreation, the runtime mcp_server_token may have changed.
# This phase reads the actual runtime token and updates each bot's .env.
log_header "Phase 3.5: Syncing Bot API Tokens"

TOKEN_SYNCED=0
TOKEN_SKIPPED=0
TOKEN_FAILED=0

for N in $INSTANCES; do
    [ "${INSTANCE_STATUS[$N]:-}" != "success" ] && [ "${INSTANCE_STATUS[$N]:-}" != "warning:version_mismatch" ] && continue

    # Get the runtime mcp_server_token from the running Agent Zero process
    RUNTIME_TOKEN=$(docker exec "agent0-$N" /opt/venv-a0/bin/python3 -c "
import sys
sys.path.insert(0, '/a0')
from helpers.settings import get_settings
print(get_settings()['mcp_server_token'])
" 2>/dev/null)

    if [ -z "$RUNTIME_TOKEN" ]; then
        log "  ${YELLOW}[agent0-$N] Could not read runtime token - skipping token sync${NC}"
        TOKEN_FAILED=$((TOKEN_FAILED + 1))
        continue
    fi

    # Get current bot A0_API_KEY
    BOT_ENV="/a0/usr/workdir/matrix-bot/.env"
    BOT_KEY=$(docker exec "agent0-$N" grep -oP 'A0_API_KEY=\K.*' "$BOT_ENV" 2>/dev/null)

    if [ -z "$BOT_KEY" ]; then
        log "  ${YELLOW}[agent0-$N] No bot .env found - skipping token sync${NC}"
        TOKEN_SKIPPED=$((TOKEN_SKIPPED + 1))
        continue
    fi

    if [ "$RUNTIME_TOKEN" = "$BOT_KEY" ]; then
        log "  ${GREEN}[agent0-$N] Bot token already matches runtime token${NC}"
        TOKEN_SKIPPED=$((TOKEN_SKIPPED + 1))
        continue
    fi

    # Update bot .env
    docker exec "agent0-$N" sed -i "s/^A0_API_KEY=.*/A0_API_KEY=$RUNTIME_TOKEN/" "$BOT_ENV" 2>/dev/null

    # Also update MCP server .env if it exists
    MCP_ENV="/a0/usr/workdir/matrix-mcp-server/.env"
    docker exec "agent0-$N" bash -c "[ -f $MCP_ENV ] && sed -i 's/^A0_API_KEY=.*/A0_API_KEY='$RUNTIME_TOKEN'/' $MCP_ENV" 2>/dev/null

    # Restart bot process
    docker exec "agent0-$N" bash -c "pkill -f matrix-bot-rust 2>/dev/null; sleep 2; cd /a0/usr/workdir/matrix-bot && nohup ./matrix-bot-rust >> bot.log 2>&1 &" 2>/dev/null

    log "  ${GREEN}[agent0-$N] Token synced: old=$BOT_KEY -> new=$RUNTIME_TOKEN (bot restarted)${NC}"
    TOKEN_SYNCED=$((TOKEN_SYNCED + 1))
done

log "  Token sync: ${GREEN}Synced=$TOKEN_SYNCED${NC} | Unchanged=$TOKEN_SKIPPED | ${RED}Failed=$TOKEN_FAILED${NC}"
# Phase 4: Report
log_header "Phase 4: Update Report"
echo ""
printf "  %-12s %-12s %-12s %-20s\n" "Instance" "Before" "After" "Status"
printf "  %-12s %-12s %-12s %-20s\n" "--------" "------" "-----" "------"

for N in $INSTANCES; do
    STATUS="${INSTANCE_STATUS[$N]:-unknown}"
    OLD="${CURRENT_VERSIONS[$N]:-N/A}"
    NEW=$(get_current_version "$N" 2>/dev/null || echo "?")
    case "$STATUS" in
        success) STATUS_COLOR="${GREEN}" ;;
        skipped:*) STATUS_COLOR="${CYAN}" ;;
        *) STATUS_COLOR="${RED}" ;;
    esac
    printf "  %-12s %-12s %-12s ${STATUS_COLOR}%-20s${NC}\n" "agent0-$N" "$OLD" "$NEW" "$STATUS"
done

echo ""
log_header "═══════════════════════════════════════════════════"
log "  ${GREEN}Success: $SUCCESS${NC}  |  ${RED}Failed: $FAILED${NC}  |  ${YELLOW}Warning: $WARNING${NC}  |  Skipped: $SKIPPED"
log_header "═══════════════════════════════════════════════════"
