#!/bin/bash
set -euo pipefail

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUST_DIR="${BOT_DIR}/rust"

if ! command -v cargo >/dev/null 2>&1; then
    echo "ERROR: cargo not found. Install Rust toolchain first." >&2
    exit 1
fi

if [ ! -d "$RUST_DIR" ]; then
    echo "ERROR: Rust project not found at ${RUST_DIR}" >&2
    exit 1
fi

cd "$RUST_DIR"
cargo build --release

cp -f "${RUST_DIR}/target/release/matrix-bot-rust" "${BOT_DIR}/matrix-bot-rust"
cp -f "${RUST_DIR}/target/release/set-display-name-rust" "${BOT_DIR}/set-display-name-rust"
chmod +x "${BOT_DIR}/matrix-bot-rust" "${BOT_DIR}/set-display-name-rust"

echo "Built:"
echo "  ${BOT_DIR}/matrix-bot-rust"
echo "  ${BOT_DIR}/set-display-name-rust"
