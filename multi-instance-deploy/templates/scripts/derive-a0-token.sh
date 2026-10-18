#!/usr/bin/env bash
# =============================================================================
# derive-a0-token.sh — Canonical Agent Zero API Credential Exporter (Phase 3)
# =============================================================================
# Single-source credential derivation using /opt/venv-a0 and Agent Zero's own
# create_auth_token() implementation. Writes the token atomically to
# /a0/usr/workdir/matrix-bot/.a0-api-key with mode 0600 and prints its
# 12-char SHA-256 fingerprint on stdout.
#
# Usage:
#   ./derive-a0-token.sh [--output /path/to/.a0-api-key] [--print-token]
# =============================================================================
set -euo pipefail

SECRET_FILE="/a0/usr/workdir/matrix-bot/.a0-api-key"
PRINT_TOKEN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)
            SECRET_FILE="$2"
            shift 2
            ;;
        --print-token)
            PRINT_TOKEN=1
            shift
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--output PATH] [--print-token]"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

PYTHON_BIN="/opt/venv-a0/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
    echo "ERROR: Canonical Python runtime not found at ${PYTHON_BIN}" >&2
    exit 1
fi

TOKEN="$("${PYTHON_BIN}" -c "
import sys
sys.path.insert(0, '/a0')
try:
    from helpers.settings import create_auth_token
except ImportError:
    from python.helpers.settings import create_auth_token
tok = create_auth_token()
if not tok:
    sys.exit(1)
print(tok, end='')
")"

if [[ -z "${TOKEN}" ]]; then
    echo "ERROR: create_auth_token() returned empty credential" >&2
    exit 1
fi

SECRET_DIR="$(dirname "${SECRET_FILE}")"
mkdir -p "${SECRET_DIR}"
TMP_FILE="${SECRET_FILE}.tmp.$$"

umask 077
printf '%s' "${TOKEN}" > "${TMP_FILE}"
chmod 0600 "${TMP_FILE}"
mv -f "${TMP_FILE}" "${SECRET_FILE}"

FINGERPRINT="$(printf '%s' "${TOKEN}" | sha256sum | cut -c1-12)"

if [[ "${PRINT_TOKEN}" -eq 1 ]]; then
    printf '%s\n' "${TOKEN}"
else
    printf '%s\n' "${FINGERPRINT}"
fi
