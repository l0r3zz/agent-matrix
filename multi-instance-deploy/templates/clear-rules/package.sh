#!/usr/bin/env bash
# Build the Agent Zero import zip. The zip's top folder is clear-rules/.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PARENT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
NAME="$(basename "${SCRIPT_DIR}")"
ARCHIVE="${PARENT}/${NAME}.zip"

rm -f "${ARCHIVE}"
(
  cd "${PARENT}"
  zip -r "${ARCHIVE}" "${NAME}" \
    -x "${NAME}/package.sh" \
    -x "${NAME}/*.zip" \
    -x "*/__pycache__/*"
)
echo "Wrote ${ARCHIVE}"
