#!/bin/bash
# =============================================================================
# sync-fleet.sh — Push golden template updates to all running instances (v3.16)
# =============================================================================
# Run from the g2s host to synchronize code and scripts across the fleet.
# Preserves instance-specific .env files (never overwrites secrets/tokens).
#
# Usage:
#   ./sync-fleet.sh                   # Sync all instances, don't restart
#   ./sync-fleet.sh --restart          # Sync all instances and restart bots
#   ./sync-fleet.sh --instances 2,3    # Sync specific instances only
#   ./sync-fleet.sh --dry-run          # Show what would be changed
# =============================================================================

set -euo pipefail

# --- Configuration ---
BASE_DIR="/opt/agent-zero"
TEMPLATE_DIR="${BASE_DIR}/agent0-1/usr/projects/agent-matrix/multi-instance-deploy/templates"
ALL_INSTANCES="1 2 3 4 5"

# --- Parse arguments ---
RESTART=false
DRY_RUN=false
INSTANCES="$ALL_INSTANCES"

while [[ $# -gt 0 ]]; do
    case $1 in
        --restart)   RESTART=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --instances) INSTANCES=$(echo "$2" | tr ',' ' '); shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--restart] [--dry-run] [--instances N,N,...]"
            echo "  --restart      Restart bot processes after sync"
            echo "  --dry-run      Show what would be synced without changing files"
            echo "  --instances    Comma-separated instance numbers (default: all)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# --- Preflight checks ---
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "ERROR: Template directory not found: $TEMPLATE_DIR"
    exit 1
fi

echo "============================================="
echo "  sync-fleet.sh — Fleet Synchronization"
echo "============================================="
echo "  Template source: $TEMPLATE_DIR"
echo "  Target instances: $INSTANCES"
echo "  Restart bots: $RESTART"
echo "  Dry run: $DRY_RUN"
echo "============================================="
echo ""

SYNCED=0
SKIPPED=0

for N in $INSTANCES; do
    INSTANCE_DIR="${BASE_DIR}/agent0-${N}"
    WORKDIR="${INSTANCE_DIR}/usr/workdir"

    # Skip if instance doesn't exist
    if [ ! -d "$INSTANCE_DIR" ]; then
        echo "[agent0-$N] Instance directory not found, skipping"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Skip if container isn't running
    if ! docker ps --format '{{.Names}}' | grep -q "^agent0-${N}$"; then
        echo "[agent0-$N] Container not running, skipping"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "[agent0-$N] Syncing..."

    # --- Sync matrix-bot (preserve .env) ---
    BOT_SRC="${TEMPLATE_DIR}/matrix-bot"
    BOT_DST="${WORKDIR}/matrix-bot"
    if [ -d "$BOT_SRC" ] && [ -d "$BOT_DST" ]; then
        # Backup instance .env
        if [ -f "${BOT_DST}/.env" ]; then
            cp "${BOT_DST}/.env" "${BOT_DST}/.env.sync-backup"
        fi
        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] Would sync matrix-bot template (python + optional rust runtime files)"
        else
            rsync -a \
                --exclude='.env' \
                --exclude='.env.sync-backup' \
                --exclude='room_contexts.json' \
                --exclude='bot.log' \
                --exclude='bot.log.prev' \
                --exclude='crash.log' \
                --exclude='bot.pid' \
                --exclude='.bot_runtime' \
                "${BOT_SRC}/" "${BOT_DST}/"
            chmod +x "${BOT_DST}/run-matrix-bot.sh" 2>/dev/null || true
            chmod +x "${BOT_DST}/run-set-display-name.sh" 2>/dev/null || true
            chmod +x "${BOT_DST}/build-rust.sh" 2>/dev/null || true
            # Restore instance .env (never overwrite)
            if [ -f "${BOT_DST}/.env.sync-backup" ]; then
                mv "${BOT_DST}/.env.sync-backup" "${BOT_DST}/.env"
            fi
            echo "  ✅ matrix-bot synced (python + rust optional runtime assets)"
        fi
    else
        echo "  ⚠️  matrix-bot: source or dest missing, skipping"
    fi

    # --- Sync matrix-mcp-server (preserve .env) ---
    MCP_SRC="${TEMPLATE_DIR}/matrix-mcp-server"
    MCP_DST="${WORKDIR}/matrix-mcp-server"
    if [ -d "$MCP_SRC" ] && [ -d "$MCP_DST" ]; then
        if [ -f "${MCP_DST}/.env" ]; then
            cp "${MCP_DST}/.env" "${MCP_DST}/.env.sync-backup"
        fi
        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] Would sync matrix-mcp-server/dist/, package.json"
        else
            rsync -a --exclude='.env' --exclude='node_modules' --exclude='.env.sync-backup' \
                --exclude='mcp-server.log' --exclude='mcp.log' \
                "${MCP_SRC}/" "${MCP_DST}/"
            # Restore instance .env
            if [ -f "${MCP_DST}/.env.sync-backup" ]; then
                mv "${MCP_DST}/.env.sync-backup" "${MCP_DST}/.env"
            fi
            echo "  ✅ matrix-mcp-server synced (dist/, package.json, src/)"
        fi
    else
        echo "  ⚠️  matrix-mcp-server: source or dest missing, skipping"
    fi

    # --- Sync startup-services.sh ---
    STARTUP_SRC="${TEMPLATE_DIR}/scripts/startup-services.sh"
    STARTUP_DST="${WORKDIR}/startup-services.sh"
    if [ -f "$STARTUP_SRC" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] Would sync startup-services.sh"
        else
            cp "$STARTUP_SRC" "$STARTUP_DST"
            chmod +x "$STARTUP_DST"
            echo "  ✅ startup-services.sh synced"
        fi
    fi

    # --- Sync switch-matrix-bot.sh ---
    SWITCH_SRC="${TEMPLATE_DIR}/scripts/switch-matrix-bot.sh"
    SWITCH_DST="${WORKDIR}/switch-matrix-bot.sh"
    if [ -f "$SWITCH_SRC" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] Would sync switch-matrix-bot.sh"
        else
            cp "$SWITCH_SRC" "$SWITCH_DST"
            chmod +x "$SWITCH_DST"
            echo "  ✅ switch-matrix-bot.sh synced"
        fi
    fi

    # --- Sync smoke-test-matrix-bot.sh ---
    SMOKE_SRC="${TEMPLATE_DIR}/scripts/smoke-test-matrix-bot.sh"
    SMOKE_DST="${WORKDIR}/smoke-test-matrix-bot.sh"
    if [ -f "$SMOKE_SRC" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] Would sync smoke-test-matrix-bot.sh"
        else
            cp "$SMOKE_SRC" "$SMOKE_DST"
            chmod +x "$SMOKE_DST"
            echo "  ✅ smoke-test-matrix-bot.sh synced"
        fi
    fi

    # --- Restart bots if requested ---
    if [ "$RESTART" = true ] && [ "$DRY_RUN" = false ]; then
        echo "  Restarting services..."
        docker exec agent0-$N pkill -9 -f 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust' 2>/dev/null || true
        docker exec agent0-$N pkill -9 -f 'node.*http-server' 2>/dev/null || true
        sleep 2
        docker exec -d agent0-$N bash -c 'cd /a0/usr/workdir/matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &'
        docker exec -d agent0-$N bash -c 'cd /a0/usr/workdir/matrix-bot && nohup ./run-matrix-bot.sh >> bot.log 2>&1 &'
        echo "  ✅ Services restarted"
    fi

    SYNCED=$((SYNCED + 1))
    echo ""
done

echo "============================================="
echo "  Sync complete: $SYNCED synced, $SKIPPED skipped"
if [ "$RESTART" = true ]; then
    echo "  Bot processes restarted"
    echo "  Wait ~20s then verify:"
    echo "    for N in $INSTANCES; do docker exec agent0-\$N tail -3 /a0/usr/workdir/matrix-bot/bot.log; done"
fi
echo "============================================="
