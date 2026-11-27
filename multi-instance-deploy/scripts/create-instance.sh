#!/usr/bin/env bash
# create-instance.sh -- provision a plugged agent0-N.
#
# The previous bash body has not been a working install path. This wrapper
# calls the Python provisioner, which renders the triplet, registers the
# Matrix user, and installs matrix-mcp-server-r2 0.4.0. run_bot stays stopped.
#
#   ./create-instance.sh 6
#   ./create-instance.sh --render-only 6
#   ./create-instance.sh --profile researcher 6
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
if [[ "$(basename "${HERE}")" == "scripts" ]]; then
    DEPLOY_ROOT="$(cd "${HERE}/.." && pwd)"
else
    DEPLOY_ROOT="${HERE}"
fi

export PYTHONPATH="${DEPLOY_ROOT}/am-ctl${PYTHONPATH:+:${PYTHONPATH}}"
if [[ -n "${AMCTL_PYTHON:-}" ]]; then
    PYTHON="${AMCTL_PYTHON}"
elif [[ -x "${DEPLOY_ROOT}/am-ctl/.venv/bin/python" ]]; then
    PYTHON="${DEPLOY_ROOT}/am-ctl/.venv/bin/python"
else
    PYTHON="python3"
fi
exec "${PYTHON}" -m amctl.provision "$@"
