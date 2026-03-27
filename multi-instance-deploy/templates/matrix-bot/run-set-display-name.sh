#!/bin/bash
set -euo pipefail

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE_FILE="${BOT_DIR}/.bot_runtime"

MODE="${MATRIX_BOT_RUNTIME:-}"
if [ -z "$MODE" ] && [ -f "$MODE_FILE" ]; then
    MODE="$(tr -d '[:space:]' < "$MODE_FILE" || true)"
fi
[ -z "$MODE" ] && MODE="python"

case "$MODE" in
    python)
        exec /opt/venv-a0/bin/python "${BOT_DIR}/set_display_name.py" "$@"
        ;;
    rust)
        if [ -x "${BOT_DIR}/set-display-name-rust" ]; then
            exec "${BOT_DIR}/set-display-name-rust" "$@"
        elif [ -x "${BOT_DIR}/rust/target/release/set-display-name-rust" ]; then
            exec "${BOT_DIR}/rust/target/release/set-display-name-rust" "$@"
        else
            echo "ERROR: Rust CLI selected but no executable found." >&2
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
