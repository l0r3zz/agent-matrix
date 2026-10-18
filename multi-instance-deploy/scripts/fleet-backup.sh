#!/usr/bin/env bash
# =============================================================================
# fleet-backup.sh — Automated DB & Infrastructure Backup Runner (Phase 5)
# =============================================================================
# Triggers a full backup of OpenBrain + fleet_ops + globals + infra_configs via
# the am-ctl API (with off-site rsync to tarnover Dropbox backup store) and
# optionally runs non-destructive scratch-DB restore verification.
#
# Usage:
#   ./fleet-backup.sh [--type daily_full|pre_deploy|manual] [--verify]
# =============================================================================
set -euo pipefail

BACKUP_TYPE="daily_full"
RUN_VERIFY=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        --verify)
            RUN_VERIFY=1
            shift
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--type daily_full|pre_deploy|manual] [--verify]"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

AMCTL_BIN="${AMCTL_BIN:-/usr/local/bin/am-ctl}"
if [[ ! -x "${AMCTL_BIN}" ]]; then
    AMCTL_BIN="/opt/agent-zero/multi-instance-deploy/am-ctl/.venv/bin/am-ctl"
fi

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Starting fleet backup (type=${BACKUP_TYPE})..."
"${AMCTL_BIN}" backup run --type "${BACKUP_TYPE}"

if [[ "${RUN_VERIFY}" -eq 1 ]]; then
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Running scratch-DB restore verification..."
    "${AMCTL_BIN}" backup verify
fi

echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] Fleet backup complete."
