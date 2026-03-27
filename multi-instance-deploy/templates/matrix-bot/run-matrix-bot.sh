#!/bin/bash
set -euo pipefail

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE_FILE="${BOT_DIR}/.bot_runtime"

# Runtime selection precedence:
# 1) MATRIX_BOT_RUNTIME env var
# 2) .bot_runtime file
# 3) default: python
MODE="${MATRIX_BOT_RUNTIME:-}"
if [ -z "$MODE" ] && [ -f "$MODE_FILE" ]; then
    MODE="$(tr -d '[:space:]' < "$MODE_FILE" || true)"
fi
[ -z "$MODE" ] && MODE="python"

case "$MODE" in
    python)
        exec /opt/venv-a0/bin/python "${BOT_DIR}/matrix_bot.py"
        ;;
    rust)
        if [ -x "${BOT_DIR}/matrix-bot-rust" ]; then
            exec "${BOT_DIR}/matrix-bot-rust"
        elif [ -x "${BOT_DIR}/rust/target/release/matrix-bot-rust" ]; then
            exec "${BOT_DIR}/rust/target/release/matrix-bot-rust"
        else
            echo "ERROR: Rust runtime selected but no executable found." >&2
            echo "Expected one of:" >&2
            echo "  ${BOT_DIR}/matrix-bot-rust" >&2
            echo "  ${BOT_DIR}/rust/target/release/matrix-bot-rust" >&2
            echo "Build with: ${BOT_DIR}/build-rust.sh" >&2
            exit 1
        fi
        ;;
    *)
        echo "ERROR: Unsupported bot runtime mode: ${MODE}" >&2
        echo "Valid modes: python | rust" >&2
        exit 1
        ;;
esac
