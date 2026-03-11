#!/bin/bash
# Agent0-1 migration: run on g2s after backup tarballs are in /tmp/
# Prereq: Phase 5 (TLS certs) must be done before Phase 8 (see instructions below)
set -e

INST=/opt/agent-zero/agent0-1

echo "=== Phase 2: Scaffold and restore ==="
sudo mkdir -p "$INST"/{usr,mhs}
sudo chown -R l0r3zz:l0r3zz "$INST"
cd "$INST"
if [[ ! -f usr/.env ]]; then
  tar xzf /tmp/agent0-1-backup.tar.gz
fi
ls -la usr/

echo "=== Phase 3: docker-compose.yml ==="
if [[ ! -f "$INST/docker-compose.yml" ]]; then
  cat > "$INST/docker-compose.yml" << 'COMPOSEEOF'
services:
  agent0-1:
    image: agent0ai/agent-zero:latest
    container_name: agent0-1
    hostname: agent0-1
    restart: unless-stopped
    env_file: usr/.env
    ports:
      - "50001:80"
      - "50022:22"
    volumes:
      - ./usr:/a0/usr
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.88.1
      bridge-local:
    mac_address: "02:42:AC:17:58:01"
    extra_hosts:
      - "agent0-1-mhs:172.23.89.1"

  dendrite:
    image: ghcr.io/element-hq/dendrite-monolith:v0.15.2
    container_name: agent0-1-mhs
    hostname: agent0-1-mhs
    restart: unless-stopped
    command:
      - "--tls-cert"
      - "/etc/dendrite/server.crt"
      - "--tls-key"
      - "/etc/dendrite/server.key"
      - "--https-bind-address"
      - ":8448"
    volumes:
      - ./mhs/dendrite.yaml:/etc/dendrite/dendrite.yaml:ro
      - ./mhs/matrix_key.pem:/etc/dendrite/matrix_key.pem:ro
      - ./mhs/server.crt:/etc/dendrite/server.crt:ro
      - ./mhs/server.key:/etc/dendrite/server.key:ro
      - ./mhs/data:/var/lib/dendrite
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.89.1
    mac_address: "02:42:AC:17:59:01"

networks:
  macvlan-172-23:
    external: true
  bridge-local:
    driver: bridge
COMPOSEEOF
  echo "Created docker-compose.yml"
else
  echo "(docker-compose.yml already present, skipping)"
fi

echo "=== Phase 4: Generate matrix_key.pem ==="
if [[ ! -f "$INST/mhs/matrix_key.pem" ]]; then
python3 -c "
import base64, os, string, random
seed = os.urandom(32)
chars = string.ascii_letters + string.digits
key_id = ''.join(random.choices(chars, k=6))
key_b64 = base64.b64encode(seed).decode()
lines = []
lines.append('-----BEGIN MATRIX PRIVATE KEY-----')
lines.append('Key-ID: ed25519:' + key_id)
lines.append('')
lines.append(key_b64)
lines.append('-----END MATRIX PRIVATE KEY-----')
with open('$INST/mhs/matrix_key.pem', 'w') as f:
    f.write(chr(10).join(lines) + chr(10))
print('Key generated: ed25519:' + key_id)
"
  chmod 600 "$INST/mhs/matrix_key.pem"
  sudo chown 65534:65534 "$INST/mhs/matrix_key.pem"
  echo "Created matrix_key.pem"
else
  echo "(matrix_key.pem already present, skipping)"
fi

echo "=== Phase 5: TLS certs (PLACEHOLDER - see below) ==="
if [[ ! -f "$INST/mhs/server.crt" || ! -f "$INST/mhs/server.key" ]]; then
  echo ">>> Run Phase 5 on TARNOVER first, then SCP certs to g2s. <<<"
  echo "On tarnover:"
  echo "  step ca certificate agent0-1-mhs.cybertribe.com /tmp/agent0-1-server.crt /tmp/agent0-1-server.key --not-after=8760h"
  echo "  step ca root /tmp/root.pem"
  echo "  cat /tmp/agent0-1-server.crt /tmp/root.pem > /tmp/agent0-1-server-bundled.crt"
  echo "  scp /tmp/agent0-1-server-bundled.crt l0r3zz@172.23.100.121:$INST/mhs/server.crt"
  echo "  scp /tmp/agent0-1-server.key l0r3zz@172.23.100.121:$INST/mhs/server.key"
  echo "Then on g2s run:"
  echo "  sudo chmod 644 $INST/mhs/server.crt"
  echo "  sudo chmod 600 $INST/mhs/server.key"
  echo "  sudo chown 65534:65534 $INST/mhs/server.crt $INST/mhs/server.key"
  echo "After certs are in place, run this script again or continue with Phase 6-8."
  exit 0
fi
sudo chmod 644 "$INST/mhs/server.crt"
sudo chmod 600 "$INST/mhs/server.key"
sudo chown 65534:65534 "$INST/mhs/server.crt" "$INST/mhs/server.key"

echo "=== Phase 6: Dendrite config ==="
cp /opt/agent-zero/agent0-2/mhs/dendrite.yaml "$INST/mhs/dendrite.yaml"
sed -i 's/agent0-2/agent0-1/g' "$INST/mhs/dendrite.yaml"
grep -q registration_shared_secret "$INST/mhs/dendrite.yaml" || echo "registration_shared_secret: cybertribe_secret" >> "$INST/mhs/dendrite.yaml"
grep server_name "$INST/mhs/dendrite.yaml"
grep connection_string "$INST/mhs/dendrite.yaml" || true

echo "=== Phase 7: .env AUTH ==="
if ! grep -q '^AUTH_LOGIN=' "$INST/usr/.env" 2>/dev/null; then
  echo "AUTH_LOGIN=admin" >> "$INST/usr/.env"
fi
if ! grep -q '^AUTH_PASSWORD=' "$INST/usr/.env" 2>/dev/null; then
  echo "AUTH_PASSWORD=changeme" >> "$INST/usr/.env"
  echo ">>> Set a real AUTH_PASSWORD in $INST/usr/.env <<<"
fi

echo "=== Phase 8: Launch containers ==="
cd "$INST"
docker compose up -d
docker compose ps
echo "Dendrite log (last 20 lines):"
docker logs agent0-1-mhs 2>&1 | tail -20
echo "Done. Next: Phase 9 (register Matrix account), Phase 10 (MCP + bot), Phase 11 (dashboard MCP config)."
