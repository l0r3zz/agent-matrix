#!/bin/bash
# =============================================================================
# finalize-fleet.sh — One-shot fleet finalization (2026-03-07)
# =============================================================================
# Run on g2s host to:
#   1. Fix agent0-3 missing OpenRouter API key
#   2. Standardize .env files
#   3. Deploy all patches via sync-fleet.sh
#   4. Create bundles in /tmp for repo transfer to tarnover
# =============================================================================

set -euo pipefail

BASE_DIR="/opt/agent-zero"
TEMPLATE_DIR="${BASE_DIR}/agent0-1/usr/projects/agent-matrix/multi-instance-deploy/templates"
SCRIPTS_DIR="${TEMPLATE_DIR}/scripts"

echo "============================================="
echo "  finalize-fleet.sh — Fleet Finalization"
echo "============================================="
echo ""

# -----------------------------------------------------------------
# STEP 1: Fix agent0-3 OpenRouter API key
# -----------------------------------------------------------------
echo "[1/5] Fixing agent0-3 OpenRouter API key..."

# Get the key from agent0-2
KEY=$(grep '^API_KEY_OPENROUTER=' ${BASE_DIR}/agent0-2/.env 2>/dev/null | cut -d= -f2)
if [ -z "$KEY" ]; then
    echo "  ⚠️  Could not find API_KEY_OPENROUTER in agent0-2/.env"
    echo "  Checking agent0-1..."
    # agent0-1 may store it differently
    KEY=$(docker exec agent0-1 grep -r 'OPENROUTER' /a0/.env 2>/dev/null | head -1 | cut -d= -f2)
fi

if [ -n "$KEY" ]; then
    # Ensure agent0-3 has the key
    if grep -q '^API_KEY_OPENROUTER=' ${BASE_DIR}/agent0-3/.env 2>/dev/null; then
        sed -i "s/^API_KEY_OPENROUTER=.*/API_KEY_OPENROUTER=$KEY/" ${BASE_DIR}/agent0-3/.env
    else
        echo "API_KEY_OPENROUTER=$KEY" >> ${BASE_DIR}/agent0-3/.env
    fi
    echo "  ✅ OpenRouter key synced to agent0-3"
else
    echo "  ❌ Could not find OpenRouter key anywhere — set manually"
fi

# -----------------------------------------------------------------
# STEP 2: Standardize .env files
# -----------------------------------------------------------------
echo ""
echo "[2/5] Checking .env standardization..."

for N in 2 3; do
    ENV_FILE="${BASE_DIR}/agent0-$N/.env"
    if [ -f "$ENV_FILE" ]; then
        echo "  agent0-$N .env exists ($(wc -l < $ENV_FILE) lines)"
        # Ensure all standard keys exist
        for VAR in API_KEY_OPENROUTER API_KEY_OPENAI API_KEY_ANTHROPIC API_KEY_GOOGLE API_KEY_GROQ; do
            if ! grep -q "^${VAR}=" "$ENV_FILE"; then
                echo "${VAR}=" >> "$ENV_FILE"
                echo "    Added missing: $VAR"
            fi
        done
    else
        echo "  ⚠️  agent0-$N .env not found"
    fi
done
echo "  ✅ Env files standardized"

# -----------------------------------------------------------------
# STEP 3: Deploy patches to fleet via sync-fleet.sh
# -----------------------------------------------------------------
echo ""
echo "[3/5] Deploying golden templates to all instances..."

if [ -f "${SCRIPTS_DIR}/sync-fleet.sh" ]; then
    bash "${SCRIPTS_DIR}/sync-fleet.sh" --restart
else
    echo "  ❌ sync-fleet.sh not found at ${SCRIPTS_DIR}"
    exit 1
fi

# -----------------------------------------------------------------
# STEP 4: Verify fleet health
# -----------------------------------------------------------------
echo ""
echo "[4/5] Verifying fleet health (waiting 25s for bots)..."
sleep 25

for N in 1 2 3; do
    echo "=== agent0-$N ==="
    # Dendrite health
    HTTP=$(curl -s -o /dev/null -w '%{http_code}' http://172.23.89.$N:8008/_matrix/client/versions 2>/dev/null || echo 'FAIL')
    echo "  Dendrite: $HTTP"
    # Bot health
    docker exec agent0-$N tail -2 /a0/usr/workdir/matrix-bot/bot.log 2>/dev/null || echo "  Bot: no log"
    echo ""
done

# -----------------------------------------------------------------
# STEP 5: Create bundles in /tmp for repo transfer
# -----------------------------------------------------------------
echo ""
echo "[5/5] Creating bundles in /tmp..."

BUNDLE_DIR="/tmp/agent-matrix-bundle-$(date +%Y%m%d)"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# Bundle 1: Full multi-instance-deploy directory
MID_SRC="${BASE_DIR}/agent0-1/usr/projects/agent-matrix/multi-instance-deploy"
MID_DST="${BUNDLE_DIR}/multi-instance-deploy"
mkdir -p "$MID_DST"

# Copy templates (excluding node_modules, .env with secrets)
rsync -a \
    --exclude='node_modules' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='.a0proj' \
    "${MID_SRC}/templates/" "${MID_DST}/templates/"

# Copy scripts and docs
cp "${MID_SRC}/create-instance.sh" "${MID_DST}/"
cp "${MID_SRC}/multi-instance-guide.md" "${MID_DST}/" 2>/dev/null || true
cp "${MID_SRC}/operations-manual.md" "${MID_DST}/" 2>/dev/null || true
cp "${MID_SRC}/agent-matrix-design.md" "${MID_DST}/" 2>/dev/null || true
cp "${MID_SRC}/theory-of-operations.md" "${MID_DST}/" 2>/dev/null || true
cp "${MID_SRC}/Migration.md" "${MID_DST}/" 2>/dev/null || true
cp "${MID_SRC}/agent-matrix-design-next.md" "${MID_DST}/" 2>/dev/null || true

# Bundle 2: Create tarball
cd /tmp
tar czf "agent-matrix-bundle-$(date +%Y%m%d).tar.gz" "$(basename $BUNDLE_DIR)"

echo ""
echo "============================================="
echo "  ✅ FINALIZATION COMPLETE"
echo "============================================="
echo ""
echo "  Bundle directory: $BUNDLE_DIR"
echo "  Tarball:          /tmp/agent-matrix-bundle-$(date +%Y%m%d).tar.gz"
echo ""
echo "  Contents:"
find "$BUNDLE_DIR" -type f | head -30
echo "  ..."
echo ""
echo "  Transfer to tarnover:"
echo "    scp /tmp/agent-matrix-bundle-$(date +%Y%m%d).tar.gz tarnover:/tmp/"
echo "============================================="
