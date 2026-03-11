#!/usr/bin/env bash
set -euo pipefail

# Decommission an Agent-Matrix instance safely.
# - Does NOT touch networking constructs (routes, DNS, firewall, etc.)
# - Stops/removes instance containers
# - Optional: save creds/certs/keys
# - Optional: archive instance data and docker volumes

SCRIPT_NAME="$(basename "$0")"
BASE_DIR="/opt/agent-zero"
ARTIFACT_ROOT="${BASE_DIR}/decommission-artifacts"
ASSUME_YES=false
SAVE_CREDS=false
ARCHIVE=false

red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }
yel()   { printf '\033[1;33m%s\033[0m\n' "$*"; }
grn()   { printf '\033[1;32m%s\033[0m\n' "$*"; }
blu()   { printf '\033[1;34m%s\033[0m\n' "$*"; }

usage() {
  cat <<USAGE
Usage: $SCRIPT_NAME [options] N

Decommission instance N (agent0-N / agent0-N-mhs).

Options:
  -y, --yes         Skip interactive confirmation prompt
  --save-creds      Save certs/keys and env files to artifact bundle
  --archive         Archive instance directory and attached docker volumes
  --base-dir PATH   Base instances directory (default: /opt/agent-zero)
  -h, --help        Show help

Examples:
  $SCRIPT_NAME 2
  $SCRIPT_NAME --save-creds --archive 3
  $SCRIPT_NAME -y --save-creds --archive --base-dir /opt/agent-zero 4
USAGE
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { red "Missing required command: $1"; exit 1; }
}

archive_volume() {
  local volume_name="$1"
  local out_file="$2"

  docker run --rm \
    -v "${volume_name}:/src:ro" \
    alpine:3.20 sh -c 'cd /src && tar -czf - . 2>/dev/null || true' > "$out_file"
}

collect_creds() {
  local instance_dir="$1"
  local out_dir="$2"

  mkdir -p "$out_dir"

  local roots=(
    "$instance_dir/mhs"
    "$instance_dir"
    "$instance_dir/usr/workdir/matrix-bot"
    "$instance_dir/usr/workdir/matrix-mcp-server"
  )

  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r -d '' f; do
      local rel
      rel="${f#${instance_dir}/}"
      mkdir -p "$out_dir/$(dirname "$rel")"
      cp -a "$f" "$out_dir/$rel"
    done < <(
      find "$root" -type f \( \
        -iname "*.crt" -o -iname "*.key" -o -iname "*.pem" -o \
        -iname "*matrix*key*" -o -iname "*sign*key*" -o \
        -name ".env" -o -name "*.env" \
      \) -print0 2>/dev/null
    )
  done
}

INSTANCE_N=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      ASSUME_YES=true
      shift
      ;;
    --save-creds)
      SAVE_CREDS=true
      shift
      ;;
    --archive)
      ARCHIVE=true
      shift
      ;;
    --base-dir)
      [[ $# -ge 2 ]] || { red "--base-dir requires a value"; exit 1; }
      BASE_DIR="$2"
      ARTIFACT_ROOT="${BASE_DIR}/decommission-artifacts"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$INSTANCE_N" ]]; then
        INSTANCE_N="$1"
        shift
      else
        red "Unexpected argument: $1"
        usage
        exit 1
      fi
      ;;
  esac
done

[[ -n "$INSTANCE_N" ]] || { red "Instance number N is required."; usage; exit 1; }
[[ "$INSTANCE_N" =~ ^[0-9]+$ ]] || { red "N must be numeric."; exit 1; }

require_cmd docker
require_cmd tar
require_cmd date

INSTANCE_NAME="agent0-${INSTANCE_N}"
MHS_NAME="agent0-${INSTANCE_N}-mhs"
INSTANCE_DIR="${BASE_DIR}/${INSTANCE_NAME}"
TS="$(date +%Y%m%d-%H%M%S)"
ARTIFACT_DIR="${ARTIFACT_ROOT}/${INSTANCE_NAME}-${TS}"

blu "=== Decommission Plan ==="
echo "Instance:       ${INSTANCE_NAME}"
echo "Homeserver:     ${MHS_NAME}"
echo "Instance dir:   ${INSTANCE_DIR}"
echo "Save creds:     ${SAVE_CREDS}"
echo "Archive:        ${ARCHIVE}"
echo "Artifact dir:   ${ARTIFACT_DIR}"
yel "NOTE: Networking constructs will NOT be modified (routes/DNS/firewall untouched)."
echo

if [[ "$ASSUME_YES" != true ]]; then
  read -r -p "Type 'yes' to permanently decommission ${INSTANCE_NAME}: " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    yel "Aborted. Confirmation must be exactly 'yes'."
    exit 0
  fi
fi

mkdir -p "$ARTIFACT_DIR"

if [[ "$SAVE_CREDS" == true ]]; then
  blu "Collecting credentials/certs/keys..."
  if [[ -d "$INSTANCE_DIR" ]]; then
    collect_creds "$INSTANCE_DIR" "$ARTIFACT_DIR/creds"
    grn "Saved credentials into: $ARTIFACT_DIR/creds"
  else
    yel "Instance directory not found, skipping creds collection: $INSTANCE_DIR"
  fi
fi

if [[ "$ARCHIVE" == true ]]; then
  blu "Archiving instance data and docker volumes..."

  if [[ -d "$INSTANCE_DIR" ]]; then
    tar -czf "$ARTIFACT_DIR/${INSTANCE_NAME}-instance-dir.tar.gz" -C "$BASE_DIR" "$INSTANCE_NAME"
    grn "Saved instance directory archive: $ARTIFACT_DIR/${INSTANCE_NAME}-instance-dir.tar.gz"
  else
    yel "Instance directory not found, skipping directory archive: $INSTANCE_DIR"
  fi

  mapfile -t VOLUMES < <(
    docker inspect "$INSTANCE_NAME" "$MHS_NAME" 2>/dev/null \
      | grep -o '"Name": "[^"]*"' \
      | sed -E 's/"Name": "([^"]*)"/\1/' \
      | sort -u || true
  )

  if [[ ${#VOLUMES[@]} -gt 0 ]]; then
    mkdir -p "$ARTIFACT_DIR/volumes"
    for v in "${VOLUMES[@]}"; do
      out="$ARTIFACT_DIR/volumes/${v}.tar.gz"
      blu "Archiving docker volume: $v"
      if archive_volume "$v" "$out"; then
        grn "  -> $out"
      else
        yel "  ! Failed to archive volume: $v"
      fi
    done
  else
    yel "No attached docker volumes discovered for $INSTANCE_NAME/$MHS_NAME"
  fi
fi

blu "Stopping/removing instance containers..."

if [[ -f "$INSTANCE_DIR/docker-compose.yml" ]]; then
  (cd "$INSTANCE_DIR" && docker compose down --remove-orphans) || yel "docker compose down reported issues; continuing"
fi

docker rm -f "$INSTANCE_NAME" >/dev/null 2>&1 || true
docker rm -f "$MHS_NAME" >/dev/null 2>&1 || true

grn "Containers removed (if present): $INSTANCE_NAME, $MHS_NAME"

if [[ -d "$INSTANCE_DIR" ]]; then
  rm -rf "$INSTANCE_DIR"
  grn "Removed instance directory: $INSTANCE_DIR"
else
  yel "Instance directory already absent: $INSTANCE_DIR"
fi

echo
blu "=== Completed ==="
grn "Decommissioned ${INSTANCE_NAME}."
yel "Networking was NOT modified."
if [[ "$SAVE_CREDS" == true || "$ARCHIVE" == true ]]; then
  grn "Artifacts: $ARTIFACT_DIR"
fi
