#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<USAGE
Usage:
  $(basename "$0") [--instance N] [--restart] <python|rust>

Examples:
  $(basename "$0") rust
  $(basename "$0") --restart python
  $(basename "$0") --instance 3 --restart rust

Behavior:
  - Updates /a0/usr/workdir/matrix-bot/.bot_runtime
  - Optional restart via /a0/usr/workdir/matrix-bot/run-matrix-bot.sh
USAGE
}

INSTANCE=""
RESTART=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --instance)
            INSTANCE="${2:-}"
            shift 2
            ;;
        --restart)
            RESTART=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        python|rust)
            MODE="$1"
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
done

MODE="${MODE:-}"
if [[ -z "$MODE" ]]; then
    echo "ERROR: Missing mode (python|rust)" >&2
    usage
    exit 2
fi

if [[ -n "$INSTANCE" ]]; then
    AGENT="agent0-${INSTANCE}"
    BOT_DIR="/a0/usr/workdir/matrix-bot"
    docker exec "$AGENT" sh -lc "printf '%s\n' '$MODE' > '${BOT_DIR}/.bot_runtime'"
    echo "[$AGENT] runtime mode set to: $MODE"

    if [[ "$RESTART" == true ]]; then
        docker exec "$AGENT" sh -lc "pkill -9 -f 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust' 2>/dev/null || true"
        docker exec -d "$AGENT" sh -lc "cd '${BOT_DIR}' && nohup ./run-matrix-bot.sh >> bot.log 2>&1 &"
        echo "[$AGENT] bot restarted"
    fi
    exit 0
fi

BOT_DIR="/a0/usr/workdir/matrix-bot"
if [[ ! -d "$BOT_DIR" ]]; then
    echo "ERROR: ${BOT_DIR} not found (run inside container or use --instance N)." >&2
    exit 1
fi

printf '%s\n' "$MODE" > "${BOT_DIR}/.bot_runtime"
echo "runtime mode set to: $MODE"

if [[ "$RESTART" == true ]]; then
    pkill -9 -f 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust' 2>/dev/null || true
    cd "$BOT_DIR"
    nohup ./run-matrix-bot.sh >> bot.log 2>&1 &
    echo "bot restarted"
fi
