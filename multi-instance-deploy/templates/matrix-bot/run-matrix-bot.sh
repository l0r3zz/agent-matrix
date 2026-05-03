#!/bin/bash

# ============================================================================
# Agent-Matrix run-matrix-bot.sh (Golden Template)
# ============================================================================
#
# Usage: ./run-matrix-bot.sh [--restart]
#
# This script handles the lifecycle of matrix-bot-rust for a sovereign agent.
#
# Features:
#   - Pre-start duplicate guard (pkill existing matrix-bot-rust before launch)
#   - Reads .bot_runtime from the bot directory to switch between Python/Rust
#   - Falls back to Rust if .bot_runtime is not set or invalid
#   - Supports --restart flag to kill existing and restart
# ============================================================================

set -euo pipefail

# Resolve script directory (the bot working directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------
# Helper: load environment
# ------------------------------------------------------------
load_env() {
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    fi
}

# ------------------------------------------------------------
# Determine runtime (.bot_runtime file or default to rust)
# ------------------------------------------------------------
get_runtime() {
    local runtime="rust"
    if [ -f ".bot_runtime" ]; then
        runtime="$(head -n1 .bot_runtime | tr '[:upper:]' '[:lower:]' | xargs)"
    fi
    # Validate; fall back to rust if unknown
    case "$runtime" in
        python|rust) ;;
        *) runtime="rust" ;;
    esac
    echo "$runtime"
}

# ------------------------------------------------------------
# Pre-start duplicate guard: kill any existing matrix-bot-rust
# ------------------------------------------------------------
kill_existing() {
    echo "Checking for existing matrix-bot-rust processes..."
    if pkill -f "matrix-bot-rust" 2>/dev/null; then
        echo "Killed existing matrix-bot-rust process(es)."
        sleep 1
    else
        echo "No existing matrix-bot-rust found."
    fi
}

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
main() {
    local restart_flag=false
    if [ "${1:-}" = "--restart" ]; then
        restart_flag=true
    fi

    load_env

    if $restart_flag; then
        kill_existing
    fi

    local runtime="$(get_runtime)"
    echo "Selected runtime: $runtime"

    if [ "$runtime" = "rust" ]; then
        # Pre-start guard: kill any existing matrix-bot-rust (only if not already done by --restart)
        if ! $restart_flag; then
            kill_existing
        fi

        if [ ! -x ./matrix-bot-rust ]; then
            echo "ERROR: matrix-bot-rust binary not found or not executable"
            exit 1
        fi

        echo "Starting matrix-bot-rust..."
        exec ./matrix-bot-rust
    else
        echo "Python bot started via matrix_bot.py – ensure dependencies are installed"
        exec python3 matrix_bot.py
    fi
}

main "$@"
