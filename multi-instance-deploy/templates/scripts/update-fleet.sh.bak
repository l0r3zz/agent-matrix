#!/bin/bash
# =============================================================================
# update-fleet.sh — Zero-Touch Agent Zero Fleet Updater (v1.4)
# =============================================================================
# Programmatically triggers Agent Zero's built-in self-update mechanism across
# the fleet, waits for completion, verifies health, and cleans up.
#
# Usage:
#   ./update-fleet.sh --status
#   ./update-fleet.sh --status --instances 2,3
#   ./update-fleet.sh --status --json
#   ./update-fleet.sh --version v1.3
#   ./update-fleet.sh --version v1.3 --instances 2,3
#   ./update-fleet.sh --version latest --no-backup
#   ./update-fleet.sh --version v1.3 --dry-run
#   ./update-fleet.sh --version v1.3 --json
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
JSON_OUTPUT=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Modes:
  --status              Show current fleet status (no update)
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
  --json                Output in JSON format (applies to --status, --cleanup, --version)
  --health-timeout SEC  Seconds to wait for health (default: $HEALTH_TIMEOUT)
  --update-timeout SEC  Seconds to wait for update (default: $UPDATE_TIMEOUT)
  -h, --help            Show this help

Examples:
  $(basename "$0") --status
  $(basename "$0") --status --instances 2,3
  $(basename "$0") --status --json
  $(basename "$0") --cleanup
  $(basename "$0") --cleanup --instances 4,5
  $(basename "$0") --version v1.3
  $(basename "$0") --version v1.3 --instances 2,3
  $(basename "$0") --version latest --no-backup
  $(basename "$0") --version v1.3 --dry-run
  $(basename "$0") --version v1.3 --json
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)         VERSION="$2"; shift 2 ;;
        --status)          STATUS_MODE=true; shift ;;
        --cleanup)         CLEANUP_MODE=true; shift ;;
        --branch)          BRANCH="$2"; shift 2 ;;
        --instances)       INSTANCES=$(echo "$2" | tr ',' ' '); shift 2 ;;
        --no-backup)       NO_BACKUP=true; shift ;;
        --skip-restart)    SKIP_RESTART=true; shift ;;
        --force)           FORCE=true; shift ;;
        --dry-run)         DRY_RUN=true; shift ;;
        --verbose)         VERBOSE=true; shift ;;
        --json)            JSON_OUTPUT=true; shift ;;
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

# Detect MCP server variant (Rust r2, TypeScript, or Python)
get_mcp_status() {
    local N=$1

    # 1. Rust variant
    local RUST_PID=$(docker exec "agent0-$N" ps aux 2>/dev/null | awk '/matrix-mcp-server-r2/ && !/grep/ {print $2; exit}')
    if [ -n "$RUST_PID" ]; then
        local RUST_VER=$(docker exec "agent0-$N" curl -sf --max-time 2 http://127.0.0.1:3000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','?'))" 2>/dev/null)
        echo "rust|${RUST_VER:-?}|$RUST_PID"
        return
    fi

    # 2. TypeScript variant (Node.js http-server)
    local TS_PID=$(docker exec "agent0-$N" ps aux 2>/dev/null | awk '/http-server/ && !/grep/ {print $2; exit}')
    if [ -n "$TS_PID" ]; then
        echo "typescript|ts|$TS_PID"
        return
    fi

    # 3. Python variant (uvicorn, python mcp server, etc.)
    local PY_PID=$(docker exec "agent0-$N" ps aux 2>/dev/null | awk '/[p]ython.*mcp|[u]vicorn|[f]astapi/ {print $2; exit}')
    if [ -n "$PY_PID" ]; then
        local PY_VER=$(docker exec "agent0-$N" curl -sf --max-time 2 http://127.0.0.1:3000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','?'))" 2>/dev/null)
        echo "python|${PY_VER:-?}|$PY_PID"
        return
    fi

    echo "none||"
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

# --- JSON Emitters ---

emit_json_status() {
    python3 -c "
import json, sys

instances = []
for line in sys.stdin.read().strip().split('\n'):
    if not line: continue
    parts = line.split('|')
    mcp_variant = parts[7] if len(parts) > 7 and parts[7] and parts[7] != 'none' else None
    mcp_version = parts[8] if len(parts) > 8 and parts[8] else None
    instances.append({
        'agent': parts[0],
        'container': parts[1],
        'version': parts[2],
        'compose_version': parts[3],
        'version_match': parts[4] == '1',
        'bot_count': int(parts[5]),
        'mcp_alive': parts[6] == '1',
        'mcp_variant': mcp_variant,
        'mcp_version': mcp_version,
        'watchdog_alive': parts[9] == '1' if len(parts) > 9 else False,
        'last_update': parts[10] if len(parts) > 10 else None,
        'homeserver_http': parts[11] if len(parts) > 11 else None,
        'health_http': parts[12] if len(parts) > 12 else None,
    })

print(json.dumps({'mode': 'status', 'instances': instances}, indent=2))
"
}

emit_json_cleanup() {
    python3 -c "
import json, sys

results = []
for line in sys.stdin.read().strip().split('\n'):
    if not line: continue
    parts = line.split('|')
    results.append({
        'agent': parts[0],
        'status': parts[1],
        'bot_count': int(parts[2]) if parts[2] else 0,
        'active_pid': parts[3] if parts[3] else None,
        'killed': int(parts[4]) if parts[4] else 0,
        'remaining': int(parts[5]) if parts[5] else None,
    })

print(json.dumps({'mode': 'cleanup', 'results': results}, indent=2))
"
}

emit_json_update() {
    python3 -c "
import json, sys

lines = sys.stdin.read().strip().split('\n')
meta = lines[0].split('|')
instances = []
for line in lines[1:]:
    if not line: continue
    parts = line.split('|')
    instances.append({
        'agent': parts[0],
        'before': parts[1],
        'after': parts[2],
        'status': parts[3],
        'result': parts[4],
    })

print(json.dumps({
    'mode': 'update',
    'target_version': meta[0],
    'branch': meta[1],
    'dry_run': meta[2] == '1',
    'instances': instances,
    'summary': {
        'success': int(meta[3]),
        'failed': int(meta[4]),
        'warning': int(meta[5]),
        'skipped': int(meta[6]),
    }
}, indent=2))
"
}


# --- Show Status Mode ---

if [ "$STATUS_MODE" = true ]; then
    set +e  # Disable exit-on-error for status checks

    # Collect data for both JSON and table modes
    STATUS_JSON_BUF=""
    TOTAL=0
    ONLINE=0
    OFFLINE=0

    for N in $INSTANCES; do
        TOTAL=$((TOTAL + 1))

        # Container status
        if is_container_running "$N"; then
            ONLINE=$((ONLINE + 1))
            CONTAINER="up"
            CONTAINER_CLR="${GREEN}"

            # Running version from health API
            RUN_VER=$(get_current_version "$N")

            # docker-compose.yml image tag
            COMPOSE_FILE="${BASE_DIR}/agent0-${N}/docker-compose.yml"
            COMPOSE_VER=$(grep 'image: agent0ai/agent-zero:' "$COMPOSE_FILE" 2>/dev/null | grep -oP 'v[0-9.]+' | head -1 || echo "?")

            # Version match indicator
            if [ "$RUN_VER" = "$COMPOSE_VER" ]; then
                VER_MATCH=1
                COMPOSE_TXT="$COMPOSE_VER"
                COMPOSE_CLR="${GREEN}"
            else
                VER_MATCH=0
                COMPOSE_TXT="${COMPOSE_VER} ⚠"
                COMPOSE_CLR="${YELLOW}"
            fi

            # Bot process count
            BOT_COUNT=$(docker exec "agent0-$N" ps aux 2>/dev/null | awk '/matrix_bot|matrix-bot-rust/ && !/grep/ {c++} END {print c+0}')
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

            # MCP process (Rust or TypeScript)
            MCP_STATUS=$(get_mcp_status "$N")
            MCP_VARIANT=$(echo "$MCP_STATUS" | cut -d'|' -f1)
            MCP_VERSION=$(echo "$MCP_STATUS" | cut -d'|' -f2)
            if [ "$MCP_VARIANT" = "rust" ]; then
                MCP_VAL=1
                MCP_TXT="r2:${MCP_VERSION}"
                MCP_CLR="${GREEN}"
            elif [ "$MCP_VARIANT" = "typescript" ]; then
                MCP_VAL=1
                MCP_TXT="ts ✓"
                MCP_CLR="${GREEN}"
            elif [ "$MCP_VARIANT" = "python" ]; then
                MCP_VAL=1
                MCP_TXT="py:${MCP_VERSION}"
                MCP_CLR="${GREEN}"
            else
                MCP_VAL=0
                MCP_TXT="✗"
                MCP_CLR="${RED}"
            fi

            # Watchdog
            WD_ALIVE=$(docker exec "agent0-$N" ps aux 2>/dev/null | awk '/watchdog/ && !/grep/ {c++} END {print c+0}')
            if [ "$WD_ALIVE" -ge 1 ]; then
                WD_VAL=1
                WD_TXT="✓"
                WD_CLR="${GREEN}"
            else
                WD_VAL=0
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
        print(f'{st} ({sv}->{cv})')
    else:
        print('none')
except:
    print('none')
" 2>/dev/null)
            [ -z "$LAST_UPD" ] && LAST_UPD="none"

            # Extra data for JSON
            HS_CODE=$(docker exec "agent0-$N" curl -s -o /dev/null -w "%{http_code}" "http://agent0-${N}-mhs:8008/_matrix/client/versions" 2>/dev/null || echo "000")
            HEALTH_CODE=$(get_health_status "$N")

            STATUS_JSON_BUF+="agent0-$N|$CONTAINER|$RUN_VER|$COMPOSE_VER|$VER_MATCH|$BOT_COUNT|$MCP_VAL|$MCP_VARIANT|$MCP_VERSION|$WD_VAL|$LAST_UPD|$HS_CODE|$HEALTH_CODE\n"

        else
            OFFLINE=$((OFFLINE + 1))
            CONTAINER="down"
            CONTAINER_CLR="${RED}"
            RUN_VER="-"
            COMPOSE_VER="-"
            VER_MATCH=0
            MCP_VAL=0
            MCP_VERSION=""
            WD_VAL=0
            LAST_UPD="-"
            HS_CODE="000"
            HEALTH_CODE="000"
            STATUS_JSON_BUF+="agent0-$N|$CONTAINER|$RUN_VER|$COMPOSE_VER|$VER_MATCH|$BOT_COUNT|$MCP_VAL|$MCP_VARIANT|$MCP_VERSION|$WD_VAL|$LAST_UPD|$HS_CODE|$HEALTH_CODE\n"
        fi
    done

    if [ "$JSON_OUTPUT" = true ]; then
        echo -e "$STATUS_JSON_BUF" | emit_json_status
        exit 0
    fi

    # Table output
    log_header "═══════════════════════════════════════════════════"
    log_header "  Agent-Matrix Fleet Status"
    log_header "═══════════════════════════════════════════════════"
    echo ""

    # Column widths: Instance=14, Container=11, Version=10, Compose=10, Bot=5, MCP=10(+2 UTF8), WD=6(+2 UTF8), LastUpdate=rest
    printf "  ${BOLD}%-14s %-11s %-10s %-10s %-5s %-10s %-4s %s${NC}\n" \
        "Instance" "Container" "Version" "Compose" "Bot" "MCP" "WD" "Last Update"
    printf "  %-14s %-11s %-10s %-10s %-5s %-10s %-4s %s\n" \
        "------------" "---------" "-------" "-------" "---" "----------" "--" "-----------"

    # Re-iterate to print table (re-run checks or parse from buffer)
    echo -e "$STATUS_JSON_BUF" | while IFS='|' read -r AGENT CONTAINER RUN_VER COMPOSE_VER VER_MATCH BOT_COUNT MCP_VAL MCP_VARIANT MCP_VERSION WD_VAL LAST_UPD HS_CODE HEALTH_CODE; do
        [ -z "$AGENT" ] && continue
        N=${AGENT#agent0-}

        if [ "$CONTAINER" = "up" ]; then
            CONTAINER_CLR="${GREEN}"
            if [ "$VER_MATCH" = "1" ]; then
                COMPOSE_CLR="${GREEN}"
                COMPOSE_TXT="$COMPOSE_VER"
            else
                COMPOSE_CLR="${YELLOW}"
                COMPOSE_TXT="${COMPOSE_VER} ⚠"
            fi
            if [ "$BOT_COUNT" -eq 1 ]; then
                BOT_CLR="${GREEN}"
                BOT_TXT="$BOT_COUNT"
            elif [ "$BOT_COUNT" -gt 1 ]; then
                BOT_CLR="${YELLOW}"
                BOT_TXT="${BOT_COUNT} ⚠"
            else
                BOT_CLR="${RED}"
                BOT_TXT="0"
            fi
            if [ "$MCP_VAL" = "1" ]; then
                MCP_CLR="${GREEN}"
                if [ "$MCP_VARIANT" = "rust" ]; then
                    MCP_TXT="r2:${MCP_VERSION}"
                elif [ "$MCP_VARIANT" = "typescript" ]; then
                    MCP_TXT="ts ✓"
                elif [ "$MCP_VARIANT" = "python" ]; then
                    MCP_TXT="py:${MCP_VERSION}"
            elif [ "$MCP_VARIANT" = "python" ]; then
                MCP_VAL=1
                MCP_TXT="py:${MCP_VERSION}"
                MCP_CLR="${GREEN}"
                else
                    MCP_TXT="✓"
                fi
            else
                MCP_CLR="${RED}"
                MCP_TXT="✗"
            fi
            if [ "$WD_VAL" = "1" ]; then
                WD_CLR="${GREEN}"
                WD_TXT="✓"
            else
                WD_CLR="${RED}"
                WD_TXT="✗"
            fi

            # Manual row output — pad MCP/WD fields to compensate for UTF-8 multibyte ✓/✗ (3 bytes, 1 display col)
            ROW=$(printf "  %-14s" "agent0-$N")
            ROW+=$(printf " ${CONTAINER_CLR}%-11s${NC}" "$CONTAINER")
            ROW+=$(printf " %-10s" "$RUN_VER")
            ROW+=$(printf " ${COMPOSE_CLR}%-10s${NC}" "$COMPOSE_TXT")
            ROW+=$(printf " ${BOT_CLR}%-5s${NC}" "$BOT_TXT")
            ROW+=$(printf " ${MCP_CLR}%s${NC}" "$MCP_TXT")
            ROW+="      "
            ROW+=$(printf "${WD_CLR}%s${NC}" "$WD_TXT")
            ROW+="   "
            ROW+="$LAST_UPD"
            echo -e "$ROW"

            if [ "$VERBOSE" = true ]; then
                UPTIME=$(docker ps --filter "name=^agent0-${N}$" --format '{{.Status}}' 2>/dev/null || echo "?")
                LAST_HEALTH=$(docker exec "agent0-$N" grep 'HEALTH' /a0/usr/workdir/startup-services.log 2>/dev/null | tail -1 || echo "N/A")
                echo "             Homeserver: HTTP $HS_CODE | Health API: HTTP $HEALTH_CODE"
                echo "             Uptime: $UPTIME"
                echo "             Last watchdog health: $LAST_HEALTH"
                echo ""
            fi
        else
            printf "  %-14s ${RED}%-11s${NC} %-10s %-10s %-5s %-5s %-4s %s\n" \
                "agent0-$N" "$CONTAINER" "-" "-" "-" "-" "-" "-"
        fi
    done

    echo ""
    log_header "═══════════════════════════════════════════════════"
    exit 0
fi


# --- Cleanup Mode ---

if [ "$CLEANUP_MODE" = true ]; then
    set +e  # Disable exit-on-error for cleanup checks

    CLEANUP_JSON_BUF=""
    CLEANED=0
    CLEAN=0
    ERRORS=0

    for N in $INSTANCES; do
        if ! is_container_running "$N"; then
            CLEANUP_JSON_BUF+="agent0-$N|not_running||||\n"
            continue
        fi

        ACTIVE_PID=$(docker exec "agent0-$N" cat /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null || echo "")
        ALL_PIDS=$(docker exec "agent0-$N" ps aux 2>/dev/null | grep -E 'matrix_bot|matrix-bot-rust' | grep -v grep | awk '{print $2}')
        BOT_COUNT=$(echo "$ALL_PIDS" | awk 'NF {c++} END {print c+0}')

        if [ -z "$ALL_PIDS" ] || [ "$BOT_COUNT" -eq 0 ]; then
            CLEANUP_JSON_BUF+="agent0-$N|no_processes||$ACTIVE_PID|0|0\n"
            ERRORS=$((ERRORS + 1))
            continue
        fi

        if [ "$BOT_COUNT" -eq 1 ]; then
            CLEANUP_JSON_BUF+="agent0-$N|clean|$BOT_COUNT|$ACTIVE_PID|0|1\n"
            CLEAN=$((CLEAN + 1))
            continue
        fi

        KILLED=0
        for PID in $ALL_PIDS; do
            if [ "$PID" != "$ACTIVE_PID" ]; then
                docker exec "agent0-$N" kill -9 "$PID" 2>/dev/null || true
                KILLED=$((KILLED + 1))
            fi
        done

        sleep 1
        REMAINING=$(docker exec "agent0-$N" ps aux 2>/dev/null | awk '/matrix_bot|matrix-bot-rust/ && !/grep/ {c++} END {print c+0}')
        if [ "$REMAINING" -eq 1 ]; then
            CLEANUP_JSON_BUF+="agent0-$N|cleaned_zombies|$BOT_COUNT|$ACTIVE_PID|$KILLED|$REMAINING\n"
            CLEANED=$((CLEANED + 1))
        else
            CLEANUP_JSON_BUF+="agent0-$N|failed_cleanup|$BOT_COUNT|$ACTIVE_PID|$KILLED|$REMAINING\n"
            ERRORS=$((ERRORS + 1))
        fi
    done

    if [ "$JSON_OUTPUT" = true ]; then
        echo -e "$CLEANUP_JSON_BUF" | emit_json_cleanup
        exit 0
    fi

    log_header "==============================================="
    log_header "  Agent-Matrix Fleet -- Zombie Bot Cleanup"
    log_header "==============================================="
    echo ""

    echo -e "$CLEANUP_JSON_BUF" | while IFS='|' read -r AGENT STATUS BOT_COUNT ACTIVE_PID KILLED REMAINING; do
        [ -z "$AGENT" ] && continue
        case "$STATUS" in
            not_running)
                log "  ${YELLOW}[$AGENT] Container not running -- SKIP${NC}"
                ;;
            no_processes)
                log "  ${RED}[$AGENT] No bot processes found${NC}"
                ;;
            clean)
                log "  ${GREEN}[$AGENT] Clean -- $BOT_COUNT bot process (PID $ACTIVE_PID)${NC}"
                ;;
            cleaned_zombies)
                log "  ${GREEN}[$AGENT] Cleaned $KILLED zombie(s) -- 1 process remaining (PID $ACTIVE_PID)${NC}"
                ;;
            failed_cleanup)
                log "  ${RED}[$AGENT] $REMAINING processes remaining after cleanup${NC}"
                ;;
        esac
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
log_header "  update-fleet.sh — Zero-Touch Fleet Updater v1.4"
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

# Build JSON buffer before printing table (for --json mode)
UPDATE_JSON_BUF=""
UPDATE_JSON_BUF+="$VERSION|$BRANCH|$([ $DRY_RUN = true ] && echo 1 || echo 0)|0|0|0|$SKIPPED\n"

SUCCESS=0
FAILED=0
WARNING=0

for N in $INSTANCES; do
    LOCAL_STATUS="${INSTANCE_STATUS[$N]:-unknown}"
    OLD_VER="${CURRENT_VERSIONS[$N]:-N/A}"

    case "$LOCAL_STATUS" in
        success)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="ok"
            SUCCESS=$((SUCCESS + 1))
            ;;
        skipped:*)
            NEW_VER="$OLD_VER"
            RESULT="skip"
            ;;
        failed:*)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="fail"
            FAILED=$((FAILED + 1))
            ;;
        warning:*)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="warn"
            WARNING=$((WARNING + 1))
            ;;
        uncertain:*)
            NEW_VER=$(get_current_version "$N" 2>/dev/null || echo "?")
            RESULT="uncertain"
            WARNING=$((WARNING + 1))
            ;;
        *)
            NEW_VER="?"
            RESULT="unknown"
            WARNING=$((WARNING + 1))
            ;;
    esac

    UPDATE_JSON_BUF+="agent0-$N|$OLD_VER|$NEW_VER|$LOCAL_STATUS|$RESULT\n"
done

# Patch summary line with final counts
UPDATE_JSON_BUF=$(echo -e "$UPDATE_JSON_BUF" | sed "1s/|0|0|0|/|$SUCCESS|$FAILED|$WARNING|/")

if [ "$JSON_OUTPUT" = true ]; then
    echo -e "$UPDATE_JSON_BUF" | emit_json_update

    # Show logs for failed instances even in JSON mode
    if [ $FAILED -gt 0 ]; then
        for N in $INSTANCES; do
            LOCAL_STATUS="${INSTANCE_STATUS[$N]:-}"
            if [[ "$LOCAL_STATUS" == failed:* ]]; then
                echo "" >&2
                log "  [agent0-$N] Update log (last 20 lines):" >&2
                docker exec "agent0-$N" tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/    /' || echo "    (no log available)"
            fi
        done
    fi

    # Exit codes preserved
    if [ $FAILED -gt 0 ]; then
        exit 1
    elif [ $WARNING -gt 0 ]; then
        exit 2
    else
        exit 0
    fi
fi

# Table output
log_header "Phase 4: Fleet Update Report"
echo ""

printf "  ${BOLD}%-12s %-12s %-12s %-20s %-10s${NC}\n" "Instance" "Before" "After" "Status" "Result"
printf "  %-12s %-12s %-12s %-20s %-10s\n" "--------" "------" "-----" "------" "------"

echo -e "$UPDATE_JSON_BUF" | tail -n +2 | while IFS='|' read -r AGENT OLD_VER NEW_VER LOCAL_STATUS RESULT; do
    [ -z "$AGENT" ] && continue
    case "$RESULT" in
        ok)         RESULT_FMT="${GREEN}✅ OK${NC}" ;;
        skip)       RESULT_FMT="${CYAN}⏭️ Skip${NC}" ;;
        fail)       RESULT_FMT="${RED}❌ FAIL${NC}" ;;
        warn)       RESULT_FMT="${YELLOW}⚠️ WARN${NC}" ;;
        uncertain)  RESULT_FMT="${YELLOW}❓ UNCRT${NC}" ;;
        *)          RESULT_FMT="${YELLOW}? UNK${NC}" ;;
    esac
    printf "  %-12s %-12s %-12s %-20s %b\n" "$AGENT" "$OLD_VER" "$NEW_VER" "$LOCAL_STATUS" "$RESULT_FMT"
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
