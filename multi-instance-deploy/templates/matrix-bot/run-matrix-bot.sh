#!/usr/bin/env bash
set -euo pipefail

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE_FILE="${BOT_DIR}/.bot_runtime"
SKIP_PREFLIGHT_ARG=""

if [[ "${1:-}" == "--skip-preflight" ]]; then
    SKIP_PREFLIGHT_ARG="--skip-preflight"
    shift
fi

# 1. Derive canonical Agent Zero API credential before launching bot (fail closed)
if [[ -x /a0/usr/workdir/derive-a0-token.sh ]]; then
    /a0/usr/workdir/derive-a0-token.sh --output "${BOT_DIR}/.a0-api-key" >/dev/null
fi

# 2. Run startup preflight gate before launching Rust binary (Phase 8)
if [[ -x /a0/usr/workdir/preflight-check.sh ]]; then
    if [[ -n "${SKIP_PREFLIGHT_ARG}" ]]; then
        /a0/usr/workdir/preflight-check.sh "${SKIP_PREFLIGHT_ARG}"
    else
        /a0/usr/workdir/preflight-check.sh
    fi
fi

# Runtime selection precedence:
# 1) MATRIX_BOT_RUNTIME env var
# 2) .bot_runtime file
# 3) default: rust
MODE="${MATRIX_BOT_RUNTIME:-}"
if [[ -z "${MODE}" ]] && [[ -f "${MODE_FILE}" ]]; then
    MODE="$(tr -d '[:space:]' < "${MODE_FILE}" || true)"
fi
[[ -z "${MODE}" ]] && MODE="rust"

case "${MODE}" in
    python)
        exec /opt/venv-a0/bin/python "${BOT_DIR}/matrix_bot.py"
        ;;
    rust)
        if [[ -x "${BOT_DIR}/matrix-bot-rust" ]]; then
            exec "${BOT_DIR}/matrix-bot-rust"
        elif [[ -x "${BOT_DIR}/rust/target/release/matrix-bot-rust" ]]; then
            exec "${BOT_DIR}/rust/target/release/matrix-bot-rust"
        else
            echo "ERROR: Rust runtime selected but no executable found." >&2
            exit 1
        fi
        ;;
    *)
        echo "ERROR: Unsupported bot runtime mode: ${MODE}" >&2
        exit 1
        ;;
esac
