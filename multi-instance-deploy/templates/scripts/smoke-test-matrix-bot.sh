#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<USAGE
Usage:
  $(basename "$0") [--instance N]

Checks:
  - Selected runtime mode (python|rust)
  - Launcher presence (run-matrix-bot.sh)
  - Runtime executable availability for selected mode
  - bot.pid liveness (if present)
  - Process visibility (run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust)
  - Last bot.log lines
USAGE
}

INSTANCE=""
if [[ "${1:-}" == "--instance" ]]; then
    INSTANCE="${2:-}"
    shift 2
fi
if [[ $# -gt 0 ]]; then
    usage
    exit 2
fi

run_checks() {
    local BOT_DIR="$1"
    local fails=0

    pass() { echo "[PASS] $*"; }
    fail() { echo "[FAIL] $*"; fails=$((fails + 1)); }
    info() { echo "[INFO] $*"; }

    info "Bot dir: ${BOT_DIR}"

    local mode="python"
    if [[ -n "${MATRIX_BOT_RUNTIME:-}" ]]; then
        mode="${MATRIX_BOT_RUNTIME}"
        info "Runtime from env MATRIX_BOT_RUNTIME=${mode}"
    elif [[ -f "${BOT_DIR}/.bot_runtime" ]]; then
        mode="$(tr -d '[:space:]' < "${BOT_DIR}/.bot_runtime" || true)"
        [[ -z "$mode" ]] && mode="python"
        info "Runtime from .bot_runtime=${mode}"
    else
        info "Runtime marker not found; defaulting to python"
    fi

    [[ -x "${BOT_DIR}/run-matrix-bot.sh" ]] && pass "launcher present: run-matrix-bot.sh" || fail "launcher missing: run-matrix-bot.sh"

    case "$mode" in
        python)
            [[ -f "${BOT_DIR}/matrix_bot.py" ]] && pass "python bot present: matrix_bot.py" || fail "python bot missing: matrix_bot.py"
            ;;
        rust)
            if [[ -x "${BOT_DIR}/matrix-bot-rust" || -x "${BOT_DIR}/rust/target/release/matrix-bot-rust" ]]; then
                pass "rust bot executable present"
            else
                fail "rust bot executable missing (matrix-bot-rust)"
            fi
            ;;
        *)
            fail "invalid runtime mode: ${mode}"
            ;;
    esac

    if [[ -f "${BOT_DIR}/bot.pid" ]]; then
        local pid
        pid="$(cat "${BOT_DIR}/bot.pid" 2>/dev/null || true)"
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            pass "bot.pid is alive (pid=${pid})"
        else
            fail "bot.pid exists but process is not alive"
        fi
    else
        info "bot.pid not found"
    fi

    if ps -ef | grep -E 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust' | grep -v grep >/dev/null; then
        pass "matrix-bot process visible in ps"
        ps -ef | grep -E 'run-matrix-bot.sh|matrix_bot.py|matrix-bot-rust' | grep -v grep | sed 's/^/[INFO] /'
    else
        fail "no matrix-bot runtime process found"
    fi

    if [[ -f "${BOT_DIR}/bot.log" ]]; then
        echo "[INFO] Last bot.log lines:"
        tail -n 10 "${BOT_DIR}/bot.log" | sed 's/^/[LOG] /'
    else
        info "bot.log not found"
    fi

    echo
    if [[ $fails -eq 0 ]]; then
        echo "RESULT: PASS"
        return 0
    else
        echo "RESULT: FAIL (failures=${fails})"
        return 1
    fi
}

if [[ -n "$INSTANCE" ]]; then
    AGENT="agent0-${INSTANCE}"
    docker exec "$AGENT" sh -lc "$(typeset -f run_checks); run_checks /a0/usr/workdir/matrix-bot"
else
    run_checks "/a0/usr/workdir/matrix-bot"
fi
