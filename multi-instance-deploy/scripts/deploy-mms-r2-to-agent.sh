#!/bin/bash
# =============================================================================
# deploy-mms-r2-to-agent.sh -- Pull matrix-mcp-server-r2 from GHCR and deploy to agent0-N
# =============================================================================
# Run on the Docker HOST (not inside a container). Does not require the Rust
# source tree -- only docker and access to the registry (public image or
# docker login ghcr.io).
#
# Environment (optional):
#   GHCR_IMAGE  -- image name without tag (default: ghcr.io/l0r3zz/matrix-mcp-server-r2)
#   MMS_R2_TAG  -- image tag / semver (default: 0.1.0)
#
# Usage (from multi-instance-deploy/templates/scripts/):
#   ./deploy-mms-r2-to-agent.sh 5
#   ./deploy-mms-r2-to-agent.sh 1 2 3
#   MMS_R2_TAG=0.1.1 ./deploy-mms-r2-to-agent.sh 5
#   ./deploy-mms-r2-to-agent.sh all
#
# What it does:
#   1. docker pull the published GHCR image
#   2. Extracts matrix-mcp-server-r2 binary from the image
#   3. Copies the binary + switch script into each agent instance
#
# After deploy, switch the running MCP to Rust:
#   docker exec agent0-N /a0/usr/workdir/switch-mcp-server.sh rust
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GHCR_IMAGE="${GHCR_IMAGE:-ghcr.io/l0r3zz/matrix-mcp-server-r2}"
MMS_R2_TAG="${MMS_R2_TAG:-0.1.0}"
FULL_IMAGE="${GHCR_IMAGE}:${MMS_R2_TAG}"
BINARY_NAME="matrix-mcp-server-r2"
EXTRACT_NAME="mcp-extract-$$"

log() { echo "[deploy] $*"; }

# ---- Parse arguments ----
if [ $# -eq 0 ]; then
    echo "Usage: $0 {N|all} [N ...]"
    echo "  $0 5          -- deploy to agent0-5"
    echo "  $0 1 2 3      -- deploy to agent0-1, -2, -3"
    echo "  $0 all        -- deploy to agent0-1 through agent0-5"
    echo ""
    echo "Env: GHCR_IMAGE (default $GHCR_IMAGE), MMS_R2_TAG (default $MMS_R2_TAG)"
    exit 1
fi

INSTANCES=()
for arg in "$@"; do
    if [ "$arg" = "all" ]; then
        INSTANCES=(1 2 3 4 5)
        break
    else
        INSTANCES+=("$arg")
    fi
done

# ---- Step 1: Pull image from GHCR ----
log "Pulling ${FULL_IMAGE}..."
docker pull "$FULL_IMAGE"

# ---- Step 2: Extract binary ----
TMPDIR=$(mktemp -d)
cleanup_extract() {
    rm -rf "$TMPDIR"
    if [ -n "${EXTRACT_NAME:-}" ]; then
        docker rm -f "$EXTRACT_NAME" >/dev/null 2>&1 || true
    fi
}
trap cleanup_extract EXIT

log "Extracting binary from image..."
docker create --name "$EXTRACT_NAME" "$FULL_IMAGE" >/dev/null
docker cp "${EXTRACT_NAME}:/usr/local/bin/${BINARY_NAME}" "$TMPDIR/$BINARY_NAME"
docker rm "$EXTRACT_NAME" >/dev/null
EXTRACT_NAME=""

chmod +x "$TMPDIR/$BINARY_NAME"
log "Binary extracted: $(ls -lh "$TMPDIR/$BINARY_NAME" | awk '{print $5}') (${FULL_IMAGE})"

# ---- Step 3: Deploy to each instance ----
for N in "${INSTANCES[@]}"; do
    CONTAINER="agent0-${N}"
    MCP_PATH="/a0/usr/workdir/matrix-mcp-server"

    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        log "WARNING: Container $CONTAINER is not running, skipping"
        continue
    fi

    log "Deploying to $CONTAINER..."

    docker cp "$TMPDIR/$BINARY_NAME" "${CONTAINER}:${MCP_PATH}/${BINARY_NAME}"
    docker exec "$CONTAINER" chmod +x "${MCP_PATH}/${BINARY_NAME}"

    docker cp "$SCRIPT_DIR/switch-mcp-server.sh" "${CONTAINER}:/a0/usr/workdir/switch-mcp-server.sh"
    docker exec "$CONTAINER" chmod +x "/a0/usr/workdir/switch-mcp-server.sh"

    log "$CONTAINER: Binary and switch script deployed"
    log "$CONTAINER: Switch with: docker exec $CONTAINER /a0/usr/workdir/switch-mcp-server.sh rust"
done

log "Done. To switch an agent to Rust:"
log "  docker exec agent0-N /a0/usr/workdir/switch-mcp-server.sh rust"
log "To switch back:"
log "  docker exec agent0-N /a0/usr/workdir/switch-mcp-server.sh ts"
