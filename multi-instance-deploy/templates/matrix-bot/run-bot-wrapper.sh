#!/usr/bin/env bash
set -euo pipefail

cd /a0/usr/workdir/matrix-bot

# 1. Derive canonical Agent Zero API credential into .a0-api-key (mode 0600)
if [[ -x /a0/usr/workdir/derive-a0-token.sh ]]; then
    FP="$(/a0/usr/workdir/derive-a0-token.sh --output /a0/usr/workdir/matrix-bot/.a0-api-key)"
    echo "[run-bot-wrapper] Derived canonical A0 credential (fingerprint=${FP})"
elif [[ ! -s /a0/usr/workdir/matrix-bot/.a0-api-key ]]; then
    echo "[run-bot-wrapper] ERROR: derive-a0-token.sh missing and no .a0-api-key present; failing closed" >&2
    exit 1
fi

# 2. Run startup preflight gate against am-ctl platform API (Phase 8)
if [[ -x /a0/usr/workdir/preflight-check.sh ]]; then
    if [[ "${SKIP_PREFLIGHT:-0}" == "1" ]]; then
        /a0/usr/workdir/preflight-check.sh --skip-preflight
    else
        /a0/usr/workdir/preflight-check.sh
    fi
fi

set -a
source .env
set +a
unset A0_API_KEY

exec ./matrix-bot-rust
