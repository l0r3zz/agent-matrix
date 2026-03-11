# Agent-Matrix Operations Manual

**Version:** 2.0
**Date:** March 8, 2026
**Audience:** Operators managing Agent-Matrix agents (create, remove, migrate, troubleshoot)
**Companion Documents:** [agent-matrix-design.md](agent-matrix-design.md) | [theory-of-operations.md](theory-of-operations.md)

> **Note:** Updated for Continuwuity v0.5.6 architecture. This version replaces Dendrite v0.15.2 with Continuwuity (a Rust-based Conduit fork) and adds a Caddy TLS sidecar for federation.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Creating a New Agent](#2-creating-a-new-agent)
3. [Post-Creation: Federation Setup](#3-post-creation-federation-setup)
4. [Verifying an Agent](#4-verifying-an-agent)
5. [Removing an Agent](#5-removing-an-agent)
6. [Migrating an Agent](#6-migrating-an-agent)
7. [Common Operational Tasks](#7-common-operational-tasks)
8. [Quick Troubleshooting](#8-quick-troubleshooting)
9. [Reference: Port and IP Allocation](#9-reference-port-and-ip-allocation)

---

## 1. Prerequisites

Before creating or managing agents, ensure the following are in place.

### 1.1 Docker Host Requirements

| Requirement | Detail |
|-------------|--------|
| OS | Ubuntu 22.04+ or Pop!_OS (System76) |
| Docker | Engine 24.x+, **rootful mode** (macvlan requires it) |
| Docker Compose | v2+ |
| Network | Connected to 172.23.0.0/16 LAN via kama |
| NIC | Promiscuous mode capable |

**Verify Docker is rootful** (macvlan will silently fail with rootless):

```bash
docker info | grep -i rootless
```

If "rootless" appears in Security Options, switch to rootful:

```bash
systemctl --user stop docker.service
systemctl --user disable docker.service
dockerd-rootless-setuptool.sh uninstall
unset DOCKER_HOST
sed -i '/DOCKER_HOST/d' ~/.bashrc ~/.profile 2>/dev/null
sudo systemctl enable --now docker.service
sudo usermod -aG docker $USER && newgrp docker
```

### 1.2 Network Setup on the Docker Host

These one-time steps must be done on each new Docker host before deploying agents.

**Create the macvlan network:**

```bash
NIC=$(ip -o -4 addr show scope global | awk '{print $2}' | head -1)
docker network create --driver macvlan \
  --subnet=172.23.0.0/16 \
  --gateway=172.23.1.1 \
  -o parent=$NIC \
  macvlan-172-23
```

**Create the mac0 bridge** (allows host-to-container communication):

```bash
NIC=$(ip -o -4 addr show scope global | awk '{print $2}' | head -1)
sudo ip link add mac0 link $NIC type macvlan mode bridge
sudo ip addr add 172.23.88.254/32 dev mac0
sudo ip link set mac0 up
sudo ip route add 172.23.88.0/24 dev mac0
sudo ip route add 172.23.89.0/24 dev mac0
sudo ip link set $NIC promisc on
```

**Make mac0 persistent** (create a systemd service):

```bash
NIC=$(ip -o -4 addr show scope global | awk '{print $2}' | head -1)
cat > /etc/systemd/system/mac0-macvlan.service << EOF
[Unit]
Description=macvlan bridge mac0 for container access
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'ip link add mac0 link $NIC type macvlan mode bridge; ip addr add 172.23.88.254/32 dev mac0; ip link set mac0 up; ip route add 172.23.88.0/24 dev mac0; ip route add 172.23.89.0/24 dev mac0'
ExecStop=/bin/bash -c 'ip link del mac0'

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mac0-macvlan.service
```

**Configure iptables forwarding:**

```bash
iptables -I FORWARD -s 172.23.0.0/16 -d 172.23.88.0/24 -j ACCEPT
iptables -I FORWARD -s 172.23.0.0/16 -d 172.23.89.0/24 -j ACCEPT
iptables -I FORWARD -s 172.23.88.0/24 -d 172.23.0.0/16 -j ACCEPT
iptables -I FORWARD -s 172.23.89.0/24 -d 172.23.0.0/16 -j ACCEPT
apt-get install -y iptables-persistent
netfilter-persistent save
```

### 1.3 Required Access

- SSH access to the Docker host
- SSH access to kama (DD-WRT router at 172.23.1.1)
- `kubectl` configured for the Contabo K8s cluster (for Synapse federation setup)
- API keys for at least one LLM provider (exported in your shell environment)

### 1.4 API Keys

Export keys in your shell before running the instance creation script:

```bash
export API_KEY_OPENROUTER="sk-or-..."
export API_KEY_OPENAI="sk-..."
export API_KEY_ANTHROPIC="sk-ant-..."
export API_KEY_GOOGLE="..."
```

---

## 2. Creating a New Agent

Agent creation uses the `create-instance.sh` script, which generates a complete 3-container stack: Agent Zero + Continuwuity homeserver + Caddy TLS proxy.

### 2.1 Run the Creation Script

```bash
cd /opt/agent-zero/multi-instance-deploy
./create-instance.sh --profile <flavor> <instance-number>
```

**Available profiles:**

| CLI Value | Specialization |
|-----------|---------------|
| `agent0` | Standard balanced assistant (default) |
| `hacker` | Cybersecurity and penetration testing |
| `developer` | Software engineering and architecture |
| `researcher` | Data analysis and reporting |

**Examples:**

```bash
./create-instance.sh --profile hacker 3      # agent0-3, Hacker persona
./create-instance.sh --profile developer 4   # agent0-4, Developer persona
./create-instance.sh 5                       # agent0-5, Standard persona
```

The script creates `/opt/agent-zero/agent0-N/` with:
- `docker-compose.yml` — unified Agent Zero + Continuwuity + Caddy stack
- `.env` — API keys, auth credentials, agent profile
- `mhs/Caddyfile` — Caddy reverse proxy configuration (8008→6167 HTTP, 8448→6167 TLS)
- `mhs/continuwuity-data/` — Continuwuity RocksDB data directory
- `usr/` — Agent Zero persistent data

### 2.2 Issue TLS Certificates (for Federation)

Each instance needs a TLS certificate signed by the step-ca PKI. Caddy uses these certs to terminate TLS on the federation port (8448).

```bash
# On tarnover (where step-ca runs)
step ca certificate "agent0-N-mhs.cybertribe.com" \
  agent0-N-mhs.crt agent0-N-mhs.key \
  --ca-url https://localhost:9000 \
  --root /home/l0r3zz/cybertribe-ca/step-store/certs/root_ca.crt \
  --san agent0-N-mhs.cybertribe.com \
  --not-after=8760h

# IMPORTANT: Use --not-after=8760h (with equals sign).
# Step CLI v0.29.x misparses --not-after 8760h (with space) as a positional arg.

# If --bundle flag fails with "too many positional arguments", generate the
# cert without --bundle and manually append the CA chain:
#   cat agent0-N-mhs.crt /path/to/intermediate_ca.crt > server.crt

# Copy to the instance directory on the Docker host
scp agent0-N-mhs.crt agent0-N-mhs.key <docker-host>:/opt/agent-zero/agent0-N/mhs/
# Rename to match expected filenames
ssh <docker-host> "cd /opt/agent-zero/agent0-N/mhs && mv agent0-N-mhs.crt server.crt && mv agent0-N-mhs.key server.key"
```

After updating certs on a running instance, restart the Caddy container:

```bash
docker compose restart caddy
```

> **Note:** Continuwuity auto-generates its own Matrix signing key on first startup. No manual key generation is required.

### 2.3 Start the Agent

```bash
cd /opt/agent-zero/agent0-N
docker compose up -d
```

Verify all three containers are running:

```bash
docker ps | grep agent0-N
```

You should see three containers:
- `agent0-N` — Agent Zero (core reasoning engine)
- `agent0-N-continuwuity` — Continuwuity homeserver (internal, port 6167)
- `agent0-N-mhs` — Caddy TLS proxy (macvlan IP, ports 8008/8448)

### 2.4 Register a Matrix User

Continuwuity uses REST API registration with a token (not a CLI binary).

```bash
# Get the registration token from the compose file
grep CONTINUWUITY_REGISTRATION_TOKEN /opt/agent-zero/agent0-N/docker-compose.yml

# Register the agent's primary user
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "agent0-N",
    "password": "<secure-password>",
    "auth": {
      "type": "m.login.registration_token",
      "token": "<token-from-compose>"
    }
  }'
```

The response includes an `access_token` — save it for MCP server and bot configuration.

> **Note:** To create an admin user, register the account and then promote it via the Continuwuity admin bot (`@conduit:<server_name>`) or the admin REST API.

### 2.5 Obtain an Access Token

If you need to obtain a fresh access token:

```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/login \
  -H 'Content-Type: application/json' \
  -d '{"type":"m.login.password","identifier":{"type":"m.id.user","user":"agent0-N"},"password":"<password>","device_id":"AgentZeroBot"}' | python3 -m json.tool
```

Copy the `access_token` from the response.

### 2.6 Update Agent-Internal Configuration

After the container starts, the matrix-mcp-server and matrix-bot inside the Agent Zero container need to be configured. For new instances created by `create-instance.sh`, the startup-services.sh script handles initial setup. However, first-time Matrix credentials must be set:

```bash
# SSH into the Agent Zero container
docker exec -it agent0-N bash

# Configure MCP server
cat > /a0/usr/workdir/matrix-mcp-server/.env << EOF
PORT=3000
ENABLE_HTTPS=false
MCP_SERVER_URL=http://localhost:3000/mcp
MATRIX_HOMESERVER_URL=http://agent0-N-mhs:8008
MATRIX_DOMAIN=agent0-N-mhs.cybertribe.com
MATRIX_USER_ID=@agent0-N:agent0-N-mhs.cybertribe.com
MATRIX_ACCESS_TOKEN=<token-from-step-2.4-or-2.5>
EOF

# Configure matrix-bot
cat > /a0/usr/workdir/matrix-bot/.env << EOF
MATRIX_HOMESERVER=http://agent0-N-mhs:8008
MATRIX_USER_ID=@agent0-N:agent0-N-mhs.cybertribe.com
MATRIX_ACCESS_TOKEN=<token-from-step-2.4-or-2.5>
A0_BASE_URL=http://localhost
A0_API_KEY=<will-be-set-by-startup-patch>
AGENT_IDENTITY=Agent0-N
EOF

# Restart services
bash /a0/usr/workdir/startup-services.sh
```

> **Note:** When manually starting the bot or installing pip packages, use the virtual environment:
> - `/opt/venv-a0/bin/pip install -r requirements.txt`
> - `/opt/venv-a0/bin/python3 matrix_bot.py`
>
> The system `python3` and `pip` lack required packages.

---

## 3. Post-Creation: Federation Setup

After the agent containers are running, three external systems need to be updated for federation to work.

### 3.1 DD-WRT Router (kama) — Routes and DNS

**Add static DHCP leases** (GUI: Services > Services > Static Leases):

| MAC | Hostname | IP |
|-----|----------|----|
| `02:42:AC:17:58:NN` | agent0-N | 172.23.88.N |
| `02:42:AC:17:59:NN` | agent0-N-mhs | 172.23.89.N |

Where `NN` is the hex value of the instance number (e.g., instance 3 = `03`).

**Add static routes** (GUI: Administration > Commands > Save Startup):

```bash
ip route add 172.23.88.N/32 via <docker-host-ip>   # agent0-N via Docker host
ip route add 172.23.89.N/32 via <docker-host-ip>   # agent0-N-mhs via Docker host
```

Alternatively, apply routes immediately:

```bash
ssh root@172.23.1.1
ip route add 172.23.88.N/32 via <docker-host-ip>
ip route add 172.23.89.N/32 via <docker-host-ip>
```

### 3.2 Synapse Gateway (K8s) — Federation Whitelist

**Add to `federation_domain_whitelist`:**

Edit the Synapse ConfigMap (or Helm values) to include the new domain:

```yaml
federation_domain_whitelist:
  - agent0-1-mhs.cybertribe.com
  - agent0-2-mhs.cybertribe.com
  - agent0-3-mhs.cybertribe.com
  - agent0-N-mhs.cybertribe.com    # NEW
```

**Add `hostAliases`** to the Synapse pod spec:

```bash
kubectl patch deployment matrix-synapse -n matrix --type strategic -p '{
  "spec": {"template": {"spec": {"hostAliases": [
    {"ip": "172.23.89.1", "hostnames": ["agent0-1-mhs.cybertribe.com"]},
    {"ip": "172.23.89.2", "hostnames": ["agent0-2-mhs.cybertribe.com"]},
    {"ip": "172.23.89.3", "hostnames": ["agent0-3-mhs.cybertribe.com"]},
    {"ip": "172.23.89.N", "hostnames": ["agent0-N-mhs.cybertribe.com"]}
  ]}}}
}'
```

> **CRITICAL:** The `hostAliases` step is the most commonly missed step when adding a new agent. Without it, Synapse cannot resolve the agent's homeserver hostname, causing **502 Bad Gateway** on federation room joins. Invites may appear to work (outbound federation succeeds) but join acceptance fails (inbound federation is broken).

**Restart Synapse:**

```bash
kubectl rollout restart deployment matrix-synapse -n matrix
```

### 3.3 Verification Checklist

After completing all three steps, verify:

```bash
# Synapse can resolve the new hostname
kubectl exec -n matrix $(kubectl get pods -n matrix -l app.kubernetes.io/name=synapse -o name | head -1) \
  -c matrix -- python3 -c "import socket; print(socket.gethostbyname('agent0-N-mhs.cybertribe.com'))"

# Routes on kama
ssh root@172.23.1.1 ip route show | grep 172.23.89.N

# All three containers healthy
docker ps --filter name=agent0-N --format 'table {{.Names}}\t{{.Status}}'

# Continuwuity responding
docker logs agent0-N-continuwuity --tail=5

# Caddy proxy healthy
docker logs agent0-N-mhs --tail=5
```

---

## 4. Verifying an Agent

Run these checks after creating or restarting an agent.

### 4.1 Container Health

```bash
# All three containers running
docker ps | grep agent0-N

# Expected: agent0-N, agent0-N-continuwuity, agent0-N-mhs

# Continuwuity homeserver logs
docker logs agent0-N-continuwuity --tail=20

# Caddy proxy logs
docker logs agent0-N-mhs --tail=20

# Client API responding (via Caddy)
curl -s http://172.23.89.N:8008/_matrix/client/versions | python3 -m json.tool

# Federation API (TLS via Caddy)
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version

# Agent Zero Web UI
curl -s -o /dev/null -w "%{http_code}" http://172.23.88.N
```

### 4.2 Internal Services

```bash
# Check matrix-mcp-server and matrix-bot are running
docker exec agent0-N ps aux | grep -E 'http-server.js|matrix_bot' | grep -v grep

# MCP endpoint responding
docker exec agent0-N curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | grep -c 'name'

# Check startup log
docker exec agent0-N cat /a0/usr/workdir/startup-services.log
```

### 4.3 Federation Test

```bash
# From inside the Agent Zero container, create a test room
docker exec agent0-N curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "matrix_homeserver_url: http://agent0-N-mhs:8008" \
  -H "matrix_user_id: @agent0-N:agent0-N-mhs.cybertribe.com" \
  -H "matrix_access_token: <TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"create-room","arguments":{"name":"federation-test","topic":"Testing federation"}},"id":1}'
```

Then from an Element client connected to matrix.v-site.net, try joining the room and sending a message. Verify the agent responds.

### 4.4 Full Round-Trip Test

The definitive test: a human on Element sends a message, the agent receives it through the matrix-bot, processes it through Agent Zero, and the response appears back in the Element room.

| Step | What to Check |
|------|--------------|
| Room creation on Continuwuity | Agent creates room via MCP tools |
| Invite sent to human | Human receives invite in Element |
| Human joins room | Join succeeds (no 502 error) |
| Human sends message | Message appears in bot.log |
| Agent responds | Response appears in Element room |
| Bot auto-join | Bot joins new rooms on invite |

---

## 5. Removing an Agent

### 5.1 Stop and Remove Containers

```bash
cd /opt/agent-zero/agent0-N
docker compose down
```

This stops all three containers: `agent0-N`, `agent0-N-continuwuity`, and `agent0-N-mhs`.

### 5.2 Remove Router Configuration (kama)

```bash
ssh root@172.23.1.1
ip route del 172.23.88.N/32
ip route del 172.23.89.N/32
```

Update the DD-WRT startup script (Administration > Commands) to remove the lines.
Remove the DHCP static leases (Services > Services > Static Leases).

### 5.3 Remove Synapse Federation Entry

Remove `agent0-N-mhs.cybertribe.com` from:
- `federation_domain_whitelist` in the Synapse ConfigMap/Helm values
- `hostAliases` in the Synapse deployment spec

Restart Synapse:

```bash
kubectl rollout restart deployment matrix-synapse -n matrix
```

### 5.4 Clean Up Host Data (Optional)

```bash
# Only after confirming the agent is no longer needed
rm -rf /opt/agent-zero/agent0-N
```

---

## 6. Migrating an Agent

Migration moves an agent from one Docker host to another while preserving its identity, data, and Matrix rooms.

### 6.1 Pre-Migration

```bash
# On the source host — backup all data
mkdir -p ~/migration-backup

# Agent Zero persistent data
tar -czvf ~/migration-backup/agent0-N-data.tar.gz /opt/agent-zero/agent0-N/usr/

# Homeserver data (Continuwuity RocksDB + Caddyfile + TLS certs)
tar -czvf ~/migration-backup/agent0-N-mhs-data.tar.gz /opt/agent-zero/agent0-N/mhs/

# Docker compose and env
cp /opt/agent-zero/agent0-N/docker-compose.yml ~/migration-backup/
cp /opt/agent-zero/agent0-N/.env ~/migration-backup/

# Record current IP/MAC (should remain the same after migration)
docker inspect agent0-N --format '{{.NetworkSettings.Networks}}' > ~/migration-backup/network-config.txt
```

> **Key paths to preserve:**
> - `mhs/continuwuity-data/` — Continuwuity RocksDB database
> - `mhs/Caddyfile` — Caddy proxy configuration
> - `mhs/server.crt`, `mhs/server.key` — TLS certificates

### 6.2 Stop Containers on Source Host

```bash
cd /opt/agent-zero/agent0-N
docker compose down
```

### 6.3 Transfer to Destination Host

```bash
scp -r ~/migration-backup/* <dest-host>:/tmp/migration/
```

### 6.4 Deploy on Destination Host

Ensure the destination host has completed the [prerequisites](#1-prerequisites) (macvlan, mac0, iptables).

```bash
# On destination host
mkdir -p /opt/agent-zero/agent0-N
cd /opt/agent-zero/agent0-N

# Restore files
cp /tmp/migration/docker-compose.yml .
cp /tmp/migration/.env .
mkdir -p usr mhs/continuwuity-data
tar -xzvf /tmp/migration/agent0-N-data.tar.gz -C /
tar -xzvf /tmp/migration/agent0-N-mhs-data.tar.gz -C /

# Start
docker compose up -d
```

### 6.5 Update Router (kama)

The container IPs stay the same; only the next-hop changes:

```bash
ssh root@172.23.1.1
# Remove old routes (via source host)
ip route del 172.23.88.N/32 via <source-host-ip>
ip route del 172.23.89.N/32 via <source-host-ip>

# Add new routes (via destination host)
ip route add 172.23.88.N/32 via <dest-host-ip>
ip route add 172.23.89.N/32 via <dest-host-ip>
```

Update the DD-WRT startup script to reflect the new host IP.

### 6.6 Reset Synapse Federation Cache

After migration, Synapse may have cached the old route. Reset the federation connection:

```bash
kubectl exec -n matrix $(kubectl get pods -n matrix -l app.kubernetes.io/name=synapse -o name | head -1) \
  -c matrix -- curl -s -X POST \
  "http://localhost:8008/_synapse/admin/v1/federation/destinations/agent0-N-mhs.cybertribe.com/reset_connection" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 6.7 Verify

Run the full [verification checklist](#4-verifying-an-agent) on the destination host.

### 6.8 Rollback

If migration fails, restore on the source host:

```bash
# On source host
cd /opt/agent-zero/agent0-N
docker compose up -d

# Restore kama routes to source host
ssh root@172.23.1.1
ip route del 172.23.88.N/32 via <dest-host-ip>
ip route del 172.23.89.N/32 via <dest-host-ip>
ip route add 172.23.88.N/32 via <source-host-ip>
ip route add 172.23.89.N/32 via <source-host-ip>
```

---

## 7. Common Operational Tasks

### 7.1 Restart an Agent

```bash
cd /opt/agent-zero/agent0-N
docker compose restart
```

Matrix services (MCP server and bot) auto-start via startup-services.sh. Allow ~30-60 seconds for pip dependencies to install and services to come online.

### 7.2 Check Agent Logs

```bash
# Startup log (shows boot sequence phases)
docker exec agent0-N cat /a0/usr/workdir/startup-services.log

# Matrix bot log
docker exec agent0-N tail -50 /a0/usr/workdir/matrix-bot/bot.log

# MCP server log
docker exec agent0-N tail -50 /a0/usr/workdir/matrix-mcp-server/mcp-server.log

# Continuwuity homeserver logs
docker logs agent0-N-continuwuity --tail=50

# Caddy proxy logs
docker logs agent0-N-mhs --tail=50
```

### 7.3 Restart Matrix Services Only

```bash
docker exec agent0-N bash -c "
  kill \$(pgrep -f http-server.js) 2>/dev/null
  kill \$(pgrep -f matrix_bot.py) 2>/dev/null
  bash /a0/usr/workdir/startup-services.sh
"
```

### 7.4 Rotate API Tokens

If the Agent Zero container restarts and the bot loses authentication:

```bash
# Inside the Agent Zero container
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh

# Then restart the bot
docker exec agent0-N bash -c "
  kill \$(pgrep -f matrix_bot.py) 2>/dev/null
  cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python matrix_bot.py >> bot.log 2>&1 &
"
```

### 7.5 Continuwuity Admin

Continuwuity provides administration through the `@conduit:<server_name>` admin bot and REST API (heritage from the Conduit project).

**Common admin tasks:**

```bash
# Check server status via admin API
curl -s http://172.23.89.N:8008/_conduit/server_version

# For user management and other admin operations, interact with the
# @conduit:agent0-N-mhs.cybertribe.com bot in a Matrix room.
# Send "!admin help" for available commands.
```

> **Note:** Synapse admin commands (`register_new_matrix_user`, `/_synapse/admin/`, etc.) do **not** work with Continuwuity. Use the `@conduit:` admin bot or Continuwuity's own REST API endpoints.

### 7.6 Check Federation Status

```bash
# Federation endpoint (via Caddy TLS)
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version

# Synapse federation destinations (requires port-forward)
kubectl port-forward -n matrix svc/matrix-synapse 8008:80 &
curl -s "http://localhost:8008/_synapse/admin/v1/federation/destinations" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" | python3 -m json.tool
```

### 7.7 View Joined Rooms

```bash
docker exec agent0-N curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list-joined-rooms","arguments":{}}}' | python3 -m json.tool
```

---



## 7.5 Email (SMTP) Configuration

Agents can send email via Gmail SMTP. This is an optional per-instance configuration.

### Prerequisites

- A Gmail account with **2-Step Verification** enabled
- A **16-character App Password** (regular passwords will NOT work)
- Generate at: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

### Configuration

Append these variables to the matrix-bot `.env` file:

```bash
cat >> /a0/usr/workdir/matrix-bot/.env << 'EOF'

# Email (SMTP) Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<gmail-address>
SMTP_PASS=<16-char-app-password>
SMTP_FROM=<gmail-address>
FORCE_TLS=true
EOF
```

Restart the bot after updating:

```bash
kill $(pgrep -f matrix_bot.py) 2>/dev/null
cd /a0/usr/workdir/matrix-bot
/opt/venv-a0/bin/python3 matrix_bot.py &
```

### Verification

```bash
/opt/venv-a0/bin/python3 -c "
import smtplib
from email.mime.text import MIMEText
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('<gmail-address>', '<app-password>')
msg = MIMEText('SMTP test from Agent Zero')
msg['Subject'] = 'Agent SMTP Test'
msg['From'] = '<gmail-address>'
msg['To'] = '<test-recipient>'
smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
smtp.quit()
print('Email sent successfully!')
"
```

> **⚠️ Common pitfall:** Regular Gmail passwords fail with `535 Username and Password not accepted`. You MUST use an App Password.

## 8. Quick Troubleshooting

### 502 Bad Gateway on Federation Room Join

**Symptom:** User receives invite from agent but gets 502 when accepting.

**Root cause:** Missing `hostAliases` in the Synapse K8s deployment. Synapse cannot resolve the homeserver hostname.

**Fix:**
```bash
# Verify the hostname is missing
kubectl exec -n matrix <synapse-pod> -c matrix -- \
  python3 -c "import socket; print(socket.gethostbyname('agent0-N-mhs.cybertribe.com'))"

# Add it (see Section 3.2) and restart Synapse
kubectl rollout restart deployment matrix-synapse -n matrix
```

### 401 Unauthorized from Agent Zero API

**Symptom:** Bot logs show `401 - {"error": "Invalid API key"}`.

**Root cause:** `A0_API_KEY` in the bot's `.env` does not match Agent Zero's computed `mcp_server_token`.

**Fix:**
```bash
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh
docker exec agent0-N bash -c "kill \$(pgrep -f matrix_bot.py); cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python matrix_bot.py >> bot.log 2>&1 &"
```

### Continuwuity Not Federating

**Symptom:** Messages don't flow between agent and Synapse.

**Check list:**
1. Caddy TLS certificate valid? `step certificate inspect /opt/agent-zero/agent0-N/mhs/server.crt --short`
2. Caddy container running? `docker ps | grep agent0-N-mhs`
3. Caddy logs show errors? `docker logs agent0-N-mhs --tail=20`
4. Continuwuity healthy? `docker logs agent0-N-continuwuity --tail=20`
5. Routes exist on kama? `ssh root@172.23.1.1 ip route | grep 172.23.89.N`
6. Synapse whitelist includes domain? Check the ConfigMap
7. VPN tunnel up? `ping 172.23.200.1` from kama
8. iptables FORWARD rules allow traffic? `iptables -L FORWARD -n | grep 172.23`

### Caddy TLS Errors

**Symptom:** Federation endpoint returns TLS errors; `curl -sk https://...:8448/` fails.

**Check list:**
1. Cert files exist? `ls -la /opt/agent-zero/agent0-N/mhs/server.crt /opt/agent-zero/agent0-N/mhs/server.key`
2. Cert not expired? `step certificate inspect /opt/agent-zero/agent0-N/mhs/server.crt --short`
3. Caddy logs? `docker logs agent0-N-mhs --tail=30`
4. Caddyfile syntax valid? `docker exec agent0-N-mhs caddy validate --config /etc/caddy/Caddyfile`
5. Restart Caddy after cert update: `docker compose restart caddy`

### Registration Fails

**Symptom:** REST API registration returns an error.

**Check list:**
1. Token correct? `grep CONTINUWUITY_REGISTRATION_TOKEN /opt/agent-zero/agent0-N/docker-compose.yml`
2. Token-based registration enabled? Verify `CONTINUWUITY_REGISTRATION_TOKEN` is set in the compose environment
3. Continuwuity running? `docker logs agent0-N-continuwuity --tail=20`
4. Client API reachable? `curl -s http://172.23.89.N:8008/_matrix/client/versions`
5. Username already taken? Try a different username or check existing accounts

### Docker macvlan Creation Fails

**Symptom:** `invalid subinterface vlan name`

**Root cause:** Docker is in rootless mode.

**Fix:** See [Prerequisites Section 1.1](#11-docker-host-requirements) for switching to rootful.

### MCP Server Not Responding

**Symptom:** Agent cannot use Matrix tools.

```bash
# Check if running
docker exec agent0-N ps aux | grep http-server.js

# Check logs
docker exec agent0-N cat /a0/usr/workdir/matrix-mcp-server/mcp-server.log

# Restart
docker exec agent0-N bash -c "kill \$(pgrep -f http-server.js); cd /a0/usr/workdir/matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &"
```

> **Note:** Ensure matrix-js-sdk version is compatible with Continuwuity. Check `package.json` for version constraints if sync issues occur.

### Bot Not Processing Messages

**Symptom:** Messages appear in Matrix room but agent doesn't respond.

```bash
# Check if running
docker exec agent0-N ps aux | grep matrix_bot

# Check bot log for errors
docker exec agent0-N tail -20 /a0/usr/workdir/matrix-bot/bot.log

# Restart bot
docker exec agent0-N bash -c "kill \$(pgrep -f matrix_bot.py); cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python matrix_bot.py >> bot.log 2>&1 &"
```

### K8s DNS / Cilium / OpenVPN Issues

For deeper infrastructure issues (K8s cross-node DNS failures, Cilium BPF issues, or OpenVPN tunnel problems), see the [Theory of Operations](theory-of-operations.md) sections on Kubernetes Cluster (Section 3) and Network Deep Dive (Section 2).

---

## 9. Reference: Port and IP Allocation

### IP Addressing Scheme

| Instance N | Agent Zero IP | Homeserver IP (Caddy) | Agent MAC | Homeserver MAC |
|-----------|--------------|----------------------|-----------|---------------|
| 1 | 172.23.88.1 | 172.23.89.1 | 02:42:AC:17:58:01 | 02:42:AC:17:59:01 |
| 2 | 172.23.88.2 | 172.23.89.2 | 02:42:AC:17:58:02 | 02:42:AC:17:59:02 |
| 3 | 172.23.88.3 | 172.23.89.3 | 02:42:AC:17:58:03 | 02:42:AC:17:59:03 |
| N | 172.23.88.N | 172.23.89.N | 02:42:AC:17:58:NN | 02:42:AC:17:59:NN |

MAC suffix `NN` is the hex representation of the instance number.

> **Note:** The macvlan IP (172.23.89.N) is held by the Caddy container (`agent0-N-mhs`), which is the external-facing proxy. Continuwuity (`agent0-N-continuwuity`) runs on an internal bridge-local network only and is not directly reachable from the LAN.

### Port Allocation

| Instance N | Web UI (host) | SSH (host) | MCP Server (container-internal) | Client API (Caddy) | Federation (Caddy TLS) |
|-----------|--------------|------------|--------------------------------|-------------------|----------------------|
| 1 | 50001 | 50022 | 3000 | 172.23.89.1:8008 | 172.23.89.1:8448 |
| 2 | 50002 | 50023 | 3000 | 172.23.89.2:8008 | 172.23.89.2:8448 |
| N | 5000N | 5002(N+1) | 3000 | 172.23.89.N:8008 | 172.23.89.N:8448 |

Caddy proxies both ports to Continuwuity's internal port 6167.

### Matrix Identity Convention

| Instance N | Matrix User ID | Homeserver Domain |
|-----------|---------------|-------------------|
| 1 | @agent:agent0-1-mhs.cybertribe.com | agent0-1-mhs.cybertribe.com |
| 2 | @agent0-2:agent0-2-mhs.cybertribe.com | agent0-2-mhs.cybertribe.com |
| N | @agent0-N:agent0-N-mhs.cybertribe.com | agent0-N-mhs.cybertribe.com |

> agent0-1 uses localpart `agent` (created manually during Phase 1). New agents follow the `agent0-N` convention.

### Shared Infrastructure

| Service | Address | Purpose |
|---------|---------|---------|
| kama (DD-WRT) | 172.23.1.1 | Gateway, DHCP, DNS, VPN, routing |
| step-ca | 172.23.0.103:9000 | Certificate authority |
| Synapse (K8s) | matrix.v-site.net (147.93.135.115) | Public Matrix gateway |
| VPN tunnel | 172.23.200.0/24 | Contabo ↔ home lab |

### Key File Locations

| File | Location |
|------|----------|
| Agent Zero docker-compose | `/opt/agent-zero/agent0-N/docker-compose.yml` |
| Agent Zero .env | `/opt/agent-zero/agent0-N/.env` |
| Agent Zero persistent data | `/opt/agent-zero/agent0-N/usr/` |
| Caddyfile | `/opt/agent-zero/agent0-N/mhs/Caddyfile` |
| Continuwuity data (RocksDB) | `/opt/agent-zero/agent0-N/mhs/continuwuity-data/` |
| TLS cert/key | `/opt/agent-zero/agent0-N/mhs/server.crt`, `server.key` |
| MCP server (in container) | `/a0/usr/workdir/matrix-mcp-server/` |
| Matrix bot (in container) | `/a0/usr/workdir/matrix-bot/` |
| Startup script (in container) | `/a0/usr/workdir/startup-services.sh` |
| API token patch (in container) | `/a0/usr/workdir/startup-patch.sh` |
| Bot log (in container) | `/a0/usr/workdir/matrix-bot/bot.log` |
| Instance creation script | `/opt/agent-zero/multi-instance-deploy/create-instance.sh` |

---

*Last updated: March 8, 2026*


## Zero-Touch Hardening v3.17
See: ./zero-touch-hardening-v3.17.md


## Instance Acceptance Validation
See: ./validate-instance-guide.md
# Appendix A: Architecture — Dendrite vs. Continuwity + Caddy

## Overview

This appendix explains the architectural difference between the original 2-container setup (Dendrite) and the current 3-container setup (Continuwity + Caddy).

---

## Before: 2 Containers Per Instance (Dendrite v0.15.2)

```
┌─────────────────────────────────────────────────────────────────┐
│  Instance (e.g., g2s:agent0-4)                                  │
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │  agent-zero (N)      │    │  dendrite (N-mhs)    │          │
│  │  Container           │    │  Container           │          │
│  │                      │    │                      │          │
│  │  Matrix Bot          │    │  Matrix Homeserver   │          │
│  │  Agent Zero Core     │    │  (Dendrite v0.15.2)  │          │
│  │                      │    │                      │          │
│  │  Port: 80 (Web UI)   │    │  Port: 8008 (HTTP)   │          │
│  │                      │    │  Port: 8448 (TLS)    │          │
│  │                      │    │                      │          │
│  │  IP: 172.23.88.N     │    │  IP: 172.23.89.N     │          │
│  └──────────┬───────────┘    └──────────┬───────────┘          │
│             │                           │                         │
│             └───────────┬───────────────┘                         │
│                         │                                         │
│              macvlan-172-23 (Host LAN)                            │
└─────────────────────────────────────────────────────────────────┘
```

**What Dendrite did:
- Single process handling **all** Matrix functions:
  - Client API (users sync, send messages)
  - Federation API (talk to other homeservers)
  - Internal TLS certificate management
  - SQLite or PostgreSQL database backend (external dependency)

**Problems that emerged:
- ❌ Development stalled (last update: Aug 2025)
- ❌ Distributed Acyclic Graph (DAG) corruption caused sync freezes
- ❌ Failed to deliver events to joined rooms
- ❌ Complex YAML configuration (`dendrite.yaml`)
- ❌ External database required (SQLite/Postgres)

---

## After: 3 Containers Per Instance (Continuwity v0.5.6 + Caddy)

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Instance (e.g., g2s:agent0-4)                                            │
│                                                                           │
│  ┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐     │
│  │ agent-zero  │       │ continuwuity    │       │ caddy           │     │
│  │ (N)         │       │ (N-continuwity) │       │ (N-mhs)         │     │
│  │             │       │                 │       │                 │     │
│  │ Agent Zero  │       │ Homeserver      │       │ TLS Proxy       │     │
│  │ Core        │       │ (logic only)    │       │                 │     │
│  │             │       │                 │       │ ┌─────────────┐  │     │
│  │ Port: 80    │       │ Internal: 6167  │       │ │ 8008 → 6167 │  │     │
│  │             │       │                 │       │ │ 8448 → 6167 │  │     │
│  │ IP:         │       │ Bridge-only     │       │ TLS Certs     │  │     │
│  │ 172.23.88.N │       │ container       │       │ (step-ca)     │  │     │
│  └──────┬──────┘       └────────┬────────┘       │ IP:           │     │
│         │                       │                │ 172.23.89.N   │     │
│         │   bridge-local        │                └────────┬──────┘     │
│         └───────────────────────┼─────────────────────────┘           │
│                                 │                                     │
│              Internal container network                             │
│                                 │                                     │
│              External-facing (macvlan)                              │
│                                                                           │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                           │
│  Caddy is the "front door" to your homeserver:                          │
│  - Terminate TLS/SSL certificates                                        │
│  - Reverse proxy to Continuwity (port 6167)                              │
│  - Handle HTTP (8008) and HTTPS (8448) on same IP                        │
│                                                                           │
│  Continuwity is the "back office":                                      │
│  - Matrix homeserver logic (user sync, messaging)                        │
│  - No network exposure (internal only)                                   │
│  - Uses embedded RocksDB (no external DB)                                 │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Why Caddy is Separate (Key Design Decision)

**The question: Why not run TLS inside Continuwity itself?**

Continuwity **can** do TLS, but we chose a **sidecar pattern** (Caddy separate container) for these reasons:

| Reason | Why it matters |
|--------|----------------|
| **Separation of concerns** | Homeserver logic ≠ TLS management |
| **Simpler configs** | Continuwity uses env vars, Caddy uses Caddyfile |
| **Easier updates** | Upgrade Caddy without touching homeserver |
| **Better security** | TLS certs live in container, not inside homeserver |
| **Flexibility** | Could swap Caddy for Traefik/Nginx later without touching homeserver |

**What Caddy actually does:**

```
Caddyfile (automatically generated from template):
- :8008 { reverse_proxy agent0-N-continuwuity:6167 }
- :8448 { tls server.crt server.key; reverse_proxy agent0-N-continuwuity:6167 }

Result:
- Incoming :8008 → proxy to Continuwity internal port 6167 (Client API)
- Incoming :8448 → terminate TLS → proxy to Continuwity port 6167 (Federation)
```

**Analogy:**
- **Dendrite (old)** = Restaurant with kitchen + dining room in one room  
- **Continuwity + Caddy (new)** = Kitchen (Continuwity) + Waitstaff/Reception (Caddy)  

The waitstaff don't cook — they just handle the customers, present food, and manage the flow.

---

## Container Comparison Table

| # | Old (Dendrite) | New (Continuwity + Caddy) |
|---|----------------|---------------------------|
| 1 | `dendrite` | `agent0-N-mhs` (Caddy proxy) |
| 2 | `agent-zero` | `agent0-N-continuwity` (Homeserver) |
|   |                | `agent-zero` (unchanged) |

**Container naming:**
- `agent0-N`: Agent Zero instance (unchanged)
- `agent0-N-continuwuity`: Matrix homeserver logic (internal only)
- `agent0-N-mhs`: Caddy TLS proxy (external-facing)

---

## Key Changes for Operators

| Task | Dendrite | Continuwity + Caddy |
|------|----------|---------------------|
| **Start** | `docker compose up -d` | Same command (3 containers)
| **Check status** | `docker ps | grep dendrite` | `docker ps | grep -E continuwity|caddy` |
| **View logs** | `docker logs agent0-N-mhs` | `docker logs agent0-N-continuwity` |
| **Config** | `dendrite.yaml` (complex YAML) | `CONTINUWUITY_` env vars (simple) |
| **Database** | `mhs/data/` (SQLite files) | `mhs/continuwuity-data/` (RocksDB) |
| **TLS certs** | Mounted to Dendrite container | Mounted to Caddy container |
| **Registration** | `dendrite-create-account` binary | REST API: `curl POST /_matrix/client/v3/register` |

---

## Why This Was Worth It

| Metric | Before (Dendrite) | After (Continuwity + Caddy) |
|--------|-------------------|----------------------------|
| **Development** | ❌ Stall (Aug 2025) | ✅ Active (6 contributors last month) |
| **RAM usage** | 50-150 MB | 20-50 MB |
| **Federation** | ❌ DAG corruption, sync freezes | ✅ RocksDB, no DAG issues |
| **TLS** | Fragile internal handling | ✅ Caddy (battle-tested) |
| **DB backend** | SQLite (external) | ✅ RocksDB (embedded) |
| **Config** | Complex `dendrite.yaml` | ✅ Simple env vars |
| **Bot compatibility** | ✅ | ✅ (drop-in replacement) |
| **Sync stability** | ❌ (intermittent freezes) | ✅ (no hangs after 24h soak) |

**Bottom line:** The extra container adds **deployment complexity** (3 containers instead of 2) but removes **operational friction** (no more debugging federation sync freezes or DAG corruption).

---

## Visual: Data Flow in Current Setup

```
User (Element, bot, MCP server)
        ↓
    172.23.89.N:8008 (Caddy container)
        ↓ (HTTP proxy)
172.23.89.N:8448 (Caddy container, TLS terminated)
        ↓
172.23.99.N:6167 (Continuwity internal port via bridge-local)
        ↓
Continuwity homeserver logic (user rooms, sync, federation)
        ↓
RocksDB (embedded database, mhs/continuwuity-data/)
```

The bot (`matrix_bot.py`) doesn't know about this complexity — it just connects to `http://agent0-N-mhs:8008` exactly like it always did. From the bot's perspective, **nothing changed**, only the backend got more stable.

---

## Summary

The migration from Dendrite to Continuwity + Caddy:

1. **Swapped homeserver software** from Dendrite (Go, stalled) to Continuwity (Rust, active)
2. **Added Caddy as TLS front door** (separate, battle-tested reverse proxy)
3. **Simplified configuration** (env vars instead of complex YAML)
4. **Removed database dependency** (RocksDB embedded, no SQLite/Postgres)
5. **Achieved 24-hour stability** (no sync freezes after soak test)

The 3-container model is the new baseline for all fresh deployments (v4.0).
