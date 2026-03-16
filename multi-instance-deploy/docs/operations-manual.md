# Agent-Matrix Operations Manual

**Version:** 2.0  
**Date:** March 16, 2026  
**Audience:** Operators managing Agent-Matrix agents (create, remove, migrate, troubleshoot)  
**Companion Documents:** [agent-matrix-design.md](agent-matrix-design.md) | [theory-of-operations.md](theory-of-operations.md)

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
cat > /etc/systemd/system/agent-bridge.service << EOF
[Unit]
Description=Agent-Matrix Host Bridge (mac0)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'ip link set $NIC promisc on; ip link add mac0 link $NIC type macvlan mode bridge || true; ip addr add 172.23.88.254/32 dev mac0 || true; ip link set mac0 up; ip route add 172.23.88.0/24 dev mac0 || true; ip route add 172.23.89.0/24 dev mac0 || true'
ExecStop=/bin/bash -c 'ip link del mac0'

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now agent-bridge.service
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

- SSH access to g2s (primary Docker host)
- SSH access to tarnover (step-ca PKI, certificate issuance)
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

Agent creation uses `create-instance.sh`, which generates a complete 3-container stack (Agent Zero + Continuwuity + Caddy) from templates.

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
- `docker-compose.yml` -- 3-container stack (Agent Zero + Continuwuity + Caddy)
- `.env` -- API keys, auth credentials, agent profile
- `mhs/Caddyfile` -- Caddy reverse proxy configuration
- `mhs/continuwuity-data/` -- Continuwuity RocksDB data directory
- `mhs/matrix_key.pem` -- Matrix signing key (auto-generated)
- `usr/` -- Agent Zero persistent data

### 2.2 Issue TLS Certificates (for Federation)

Each agent's Caddy sidecar needs a TLS certificate signed by the step-ca PKI:

```bash
# On tarnover (where step-ca runs)
step ca certificate "agent0-N-mhs.cybertribe.com" \
  server.crt server.key \
  --ca-url https://localhost:9000 \
  --root /home/l0r3zz/cybertribe-ca/step-store/certs/root_ca.crt \
  --san agent0-N-mhs.cybertribe.com \
  --not-after=8760h

# Append the CA chain (Synapse requires the full chain)
cat /home/l0r3zz/cybertribe-ca/step-store/certs/intermediate_ca.crt >> server.crt

# Copy to the instance directory on g2s
scp server.crt server.key g2s:/opt/agent-zero/agent0-N/mhs/
ssh g2s "chmod 600 /opt/agent-zero/agent0-N/mhs/server.key"
```

> **Note:** Use `--not-after=8760h` (equals syntax). Step CLI v0.29.x misparses `--not-after 8760h` (space-separated) as a positional arg.

### 2.3 Start the Agent

```bash
cd /opt/agent-zero/agent0-N
docker compose up -d
```

Verify three containers are running:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep agent0-N
```

You should see: `agent0-N`, `agent0-N-continuwuity`, `agent0-N-mhs`.

### 2.4 Register Matrix Account on Continuwuity

Continuwuity uses a one-time registration token (not a `create-account` binary).

**Step 1:** Extract the registration token from container logs:
```bash
docker logs agent0-N-continuwuity 2>&1 | tr -d '\033' | grep -oE 'token[^" ]+' | head -1
```

**Step 2:** Register the agent user:
```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "agent0-N",
    "password": "<secure-password>",
    "auth": {
      "type": "m.login.registration_token",
      "token": "<registration-token>"
    }
  }' | python3 -m json.tool
```

Save the `access_token` from the response.

### 2.5 Update Agent-Internal Configuration

After the container starts, configure the MCP server and bot with the Matrix credentials:

```bash
docker exec -it agent0-N bash

# Update MCP server token
sed -i "s/PENDING_REGISTRATION/<access-token>/" \
  /a0/usr/workdir/matrix-mcp-server/.env

# Update bot token
sed -i "s/PENDING_REGISTRATION/<access-token>/" \
  /a0/usr/workdir/matrix-bot/.env

# Restart services
bash /a0/usr/workdir/startup-services.sh
```

> **Note:** When manually running pip or python, use the virtual environment: `/opt/venv-a0/bin/pip` and `/opt/venv-a0/bin/python3`. The system Python lacks required packages.

### 2.6 Finalize with finalize-instance.sh (Alternative)

For automated registration and credential injection:

```bash
cd /opt/agent-zero/multi-instance-deploy
./finalize-instance.sh N
```

This script extracts the registration token, registers the user, and updates all `.env` files automatically.

---

## 3. Post-Creation: Federation Setup

After the agent containers are running, three external systems need to be updated for federation to work.

### 3.1 DD-WRT Router (kama) -- Routes and DNS

**Add static DHCP leases** (GUI: Services > Services > Static Leases):

| MAC | Hostname | IP |
|-----|----------|----|
| `02:42:AC:17:58:NN` | agent0-N | 172.23.88.N |
| `02:42:AC:17:59:NN` | agent0-N-mhs | 172.23.89.N |

Where `NN` is the hex value of the instance number (e.g., instance 3 = `03`).

**Add static routes** (GUI: Administration > Commands > Save Startup):

```bash
ip route add 172.23.88.N/32 via 172.23.100.121   # agent0-N via g2s
ip route add 172.23.89.N/32 via 172.23.100.121   # agent0-N-mhs via g2s
```

Apply routes immediately:

```bash
ssh root@172.23.1.1
ip route add 172.23.88.N/32 via 172.23.100.121
ip route add 172.23.89.N/32 via 172.23.100.121
```

### 3.2 Synapse Gateway (K8s) -- Federation Whitelist

**Add to `federation_domain_whitelist`:**

Edit the Synapse ConfigMap (or Helm values) to include the new domain:

```yaml
federation_domain_whitelist:
  - agent0-1-mhs.cybertribe.com
  - agent0-2-mhs.cybertribe.com
  - agent0-3-mhs.cybertribe.com
  - agent0-4-mhs.cybertribe.com
  - agent0-5-mhs.cybertribe.com
  - agent0-N-mhs.cybertribe.com    # NEW
```

**Add `hostAliases`** to the Synapse pod spec:

```bash
kubectl patch deployment matrix-synapse -n matrix --type=json -p '[
  {"op": "add", "path": "/spec/template/spec/hostAliases/-",
   "value": {"ip": "172.23.89.N", "hostnames": ["agent0-N-mhs.cybertribe.com"]}}
]'
```

> **CRITICAL:** The `hostAliases` step is the most commonly missed step when adding a new agent. Without it, Synapse cannot resolve the new agent hostname, causing **502 Bad Gateway** on federation room joins. Invites may appear to work (outbound federation succeeds) but join acceptance fails (inbound federation is broken).

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
```

---

## 4. Verifying an Agent

Run these checks after creating or restarting an agent.

### 4.1 Container Health

```bash
# All three containers running
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep agent0-N

# Client-Server API (via Caddy)
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
# From the openvpn sidecar in the Synapse pod, test TLS to the agent
kubectl exec -it -n matrix <synapse-pod> -c openvpn -- \
  wget -qO- --no-check-certificate https://agent0-N-mhs.cybertribe.com:8448/_matrix/key/v2/server
```

### 4.4 Full Round-Trip Test

The definitive test: a human on Element sends a message, the agent receives it, processes it, and responds.

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

Or use the decommission script:

```bash
cd /opt/agent-zero/multi-instance-deploy
./decommission-instance.sh N
```

### 5.2 Remove Router Configuration (kama)

```bash
ssh root@172.23.1.1
ip route del 172.23.88.N/32
ip route del 172.23.89.N/32
```

Update the DD-WRT startup script (Administration > Commands) to remove the lines. Remove the DHCP static leases (Services > Services > Static Leases).

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
rm -rf /opt/agent-zero/agent0-N
```

---

## 6. Migrating an Agent

Migration moves an agent from one Docker host to another while preserving its identity, data, and Matrix rooms.

### 6.1 Pre-Migration

```bash
# On the source host -- backup all data
mkdir -p ~/migration-backup

# Agent Zero persistent data
tar -czvf ~/migration-backup/agent0-N-data.tar.gz -C /opt/agent-zero/agent0-N usr/

# Homeserver data and Caddy config
tar -czvf ~/migration-backup/agent0-N-mhs-data.tar.gz -C /opt/agent-zero/agent0-N mhs/

# Docker compose and env
cp /opt/agent-zero/agent0-N/docker-compose.yml ~/migration-backup/
cp /opt/agent-zero/agent0-N/.env ~/migration-backup/
```

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
mkdir -p /opt/agent-zero/agent0-N
cd /opt/agent-zero/agent0-N
cp /tmp/migration/docker-compose.yml .
cp /tmp/migration/.env .
tar -xzvf /tmp/migration/agent0-N-data.tar.gz
tar -xzvf /tmp/migration/agent0-N-mhs-data.tar.gz
docker compose up -d
```

### 6.5 Update Router (kama)

The container IPs stay the same; only the next-hop changes:

```bash
ssh root@172.23.1.1
ip route del 172.23.88.N/32 via <source-host-ip>
ip route del 172.23.89.N/32 via <source-host-ip>
ip route add 172.23.88.N/32 via <dest-host-ip>
ip route add 172.23.89.N/32 via <dest-host-ip>
```

Update the DD-WRT startup script to reflect the new host IP.

### 6.6 Reset Synapse Federation Cache

After migration, Synapse may have cached the old route. Reset the connection:

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
cd /opt/agent-zero/agent0-N
docker compose up -d

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

# Continuwuity logs
docker logs agent0-N-continuwuity --tail=50

# Caddy logs
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
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh

docker exec agent0-N bash -c "
  kill \$(pgrep -f matrix_bot.py) 2>/dev/null
  cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python3 matrix_bot.py >> bot.log 2>&1 &
"
```

### 7.5 Check Federation Status

```bash
# Agent federation endpoint (TLS via Caddy)
curl -sk https://agent0-N-mhs.cybertribe.com:8448/_matrix/federation/v1/version

# Synapse federation destinations (requires port-forward)
kubectl port-forward -n matrix svc/matrix-synapse 8008:80 &
curl -s "http://localhost:8008/_synapse/admin/v1/federation/destinations" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" | python3 -m json.tool
```

### 7.6 Token Mismatch Prevention System

The MCP server authenticates to Matrix using an access token. This token exists in **two locations**:
1. The MCP server's `.env` file (`MATRIX_ACCESS_TOKEN`)
2. Agent Zero's `settings.json` (`mcp_servers` > matrix > headers > `matrix_access_token`)

If these drift apart (e.g., after a token rotation or re-login), the MCP server receives a stale token and fails with `M_UNKNOWN_TOKEN`. A three-layer prevention system guards against this.

**Layer 1: Watchdog (Boot and Runtime Guard)**
- `watchdog.sh` monitors both the bot and MCP server processes
- Performs periodic health checks (Matrix auth validation, token sync comparison)
- Auto-restarts MCP server on auth failure
- Helper: `check-token-sync.py` compares both token sources

**Layer 2: TOKEN-GUARD (Code-Level Fallback)**
- The MCP server's `getAccessToken()` function treats the `.env` token as authoritative
- If the header token differs from `.env`, it silently falls back to the `.env` value

**Layer 3: Scheduled Health Probe**
- Runs every 30 minutes: MCP alive check, auth validation, token sync, tool response test

**Manual Token Refresh:**

```bash
# 1. Get a new token
curl -s -X POST http://agent0-N-mhs:8008/_matrix/client/v3/login \
  -H "Content-Type: application/json" \
  -d '{"type":"m.login.password","user":"@agent0-N:agent0-N-mhs.cybertribe.com","password":"<pw>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"

# 2. Update .env
sed -i "s/^MATRIX_ACCESS_TOKEN=.*/MATRIX_ACCESS_TOKEN=<new-token>/" \
  /a0/usr/workdir/matrix-mcp-server/.env

# 3. Restart MCP server
kill $(pgrep -f http-server.js)
cd /a0/usr/workdir/matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &
```

### 7.7 Email (SMTP) Configuration

Agents can send email via Gmail SMTP. Per-instance, optional.

**Prerequisites:** Gmail account with 2-Step Verification + App Password from [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

**Configuration** (append to matrix-bot `.env`):

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<gmail-address>
SMTP_PASS=<16-char-app-password>
SMTP_FROM=<gmail-address>
FORCE_TLS=true
```

Restart the bot after updating:

```bash
kill $(pgrep -f matrix_bot.py) 2>/dev/null
cd /a0/usr/workdir/matrix-bot
/opt/venv-a0/bin/python3 matrix_bot.py &
```

> Regular Gmail passwords fail with `535 Username and Password not accepted`. You MUST use an App Password.

### 7.8 View Joined Rooms

```bash
docker exec agent0-N curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list-joined-rooms","arguments":{}}}' | python3 -m json.tool
```

### 7.9 Bot Display Name

Set in the bot `.env`:
```bash
BOT_DISPLAY_NAME=Agent0-N
AGENT_IDENTITY=Agent Zero
```

The bot sets this name on startup. For runtime changes without restarting:

```bash
cd /a0/usr/workdir/matrix-bot
python3 set_display_name.py "New Name"
python3 set_display_name.py "Room Helper" --room '!roomid:server.com'
python3 set_display_name.py --reset
```

---

## 8. Quick Troubleshooting

### 502 Bad Gateway on Federation Room Join

**Symptom:** User receives invite from agent but gets 502 when accepting.

**Root cause:** Missing `hostAliases` in the Synapse K8s deployment. Synapse cannot resolve the agent hostname.

**Fix:**
```bash
kubectl exec -n matrix <synapse-pod> -c matrix -- \
  python3 -c "import socket; print(socket.gethostbyname('agent0-N-mhs.cybertribe.com'))"
# If this fails, add hostAliases (see Section 3.2) and restart Synapse
kubectl rollout restart deployment matrix-synapse -n matrix
```

### 401 Unauthorized from Agent Zero API

**Symptom:** Bot logs show `401 - {"error": "Invalid API key"}`.

**Root cause:** `A0_API_KEY` in the bot's `.env` does not match Agent Zero's computed `mcp_server_token`.

**Fix:**
```bash
docker exec agent0-N bash /a0/usr/workdir/startup-patch.sh
docker exec agent0-N bash -c "kill \$(pgrep -f matrix_bot.py); cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python3 matrix_bot.py >> bot.log 2>&1 &"
```

### Agent Not Federating

**Symptom:** Messages don't flow between agent and Synapse.

**Checklist:**
1. TLS certificate valid? `step certificate inspect /opt/agent-zero/agent0-N/mhs/server.crt --short`
2. Caddy running? `docker ps | grep agent0-N-mhs`
3. Continuwuity running? `docker ps | grep agent0-N-continuwuity`
4. Routes exist on kama? `ssh root@172.23.1.1 ip route | grep 172.23.89.N`
5. Synapse whitelist includes domain? Check the ConfigMap
6. VPN tunnel up? `ping 172.23.200.1` from kama
7. iptables FORWARD rules allow traffic? `iptables -L FORWARD -n | grep 172.23`

### Docker macvlan Creation Fails

**Symptom:** `invalid subinterface vlan name`

**Root cause:** Docker is in rootless mode.

**Fix:** See [Prerequisites Section 1.1](#11-docker-host-requirements) for switching to rootful.

### MCP Server Not Responding

**Symptom:** Agent cannot use Matrix tools.

**First:** Check if this is a token mismatch (most common cause). See Section 7.6.

```bash
docker exec agent0-N python3 /a0/usr/workdir/check-token-sync.py

docker exec agent0-N ps aux | grep http-server.js

docker exec agent0-N tail -50 /a0/usr/workdir/matrix-mcp-server/mcp-server.log

# Restart
docker exec agent0-N bash -c "kill \$(pgrep -f http-server.js); cd /a0/usr/workdir/matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &"
```

### Bot Not Processing Messages

**Symptom:** Messages appear in Matrix room but agent doesn't respond.

```bash
docker exec agent0-N ps aux | grep matrix_bot
docker exec agent0-N tail -20 /a0/usr/workdir/matrix-bot/bot.log

# Restart bot
docker exec agent0-N bash -c "kill \$(pgrep -f matrix_bot.py); cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python3 matrix_bot.py >> bot.log 2>&1 &"
```

### K8s DNS / Cilium / OpenVPN Issues

For deeper infrastructure issues (K8s cross-node DNS failures, Cilium BPF issues, or OpenVPN tunnel problems), see the [Theory of Operations](theory-of-operations.md) sections 3 and 2.

---

## 9. Reference: Port and IP Allocation

### IP Addressing Scheme

| Instance N | Agent Zero IP | Caddy (MHS) IP | Agent MAC | Caddy MAC |
|-----------|--------------|-------------|-----------|-------------|
| 1 | 172.23.88.1 | 172.23.89.1 | 02:42:AC:17:58:01 | 02:42:AC:17:59:01 |
| 2 | 172.23.88.2 | 172.23.89.2 | 02:42:AC:17:58:02 | 02:42:AC:17:59:02 |
| 3 | 172.23.88.3 | 172.23.89.3 | 02:42:AC:17:58:03 | 02:42:AC:17:59:03 |
| 4 | 172.23.88.4 | 172.23.89.4 | 02:42:AC:17:58:04 | 02:42:AC:17:59:04 |
| 5 | 172.23.88.5 | 172.23.89.5 | 02:42:AC:17:58:05 | 02:42:AC:17:59:05 |

MAC suffix `NN` is the hex representation of the instance number.

Continuwuity containers (`agent0-N-continuwuity`) are on bridge-local only -- no macvlan IP or MAC.

### Port Allocation

| Instance N | Web UI (host) | SSH (host) | MCP Server (container-internal) | CS API (Caddy) | Federation (Caddy+TLS) |
|-----------|--------------|------------|--------------------------------|----------------|----------------------|
| 1 | 50001 | 50022 | 3000 | 172.23.89.1:8008 | 172.23.89.1:8448 |
| 2 | 50002 | 50023 | 3000 | 172.23.89.2:8008 | 172.23.89.2:8448 |
| 3 | 50003 | 50024 | 3000 | 172.23.89.3:8008 | 172.23.89.3:8448 |
| 4 | 50004 | 50025 | 3000 | 172.23.89.4:8008 | 172.23.89.4:8448 |
| 5 | 50005 | 50026 | 3000 | 172.23.89.5:8008 | 172.23.89.5:8448 |

### Matrix Identity Convention

| Instance N | Matrix User ID | Homeserver Domain |
|-----------|---------------|-------------------|
| 1 | @agent:agent0-1-mhs.cybertribe.com | agent0-1-mhs.cybertribe.com |
| 2 | @agent0-2:agent0-2-mhs.cybertribe.com | agent0-2-mhs.cybertribe.com |
| 3 | @agent0-3:agent0-3-mhs.cybertribe.com | agent0-3-mhs.cybertribe.com |
| 4 | @agent0-4:agent0-4-mhs.cybertribe.com | agent0-4-mhs.cybertribe.com |
| 5 | @agent0-5:agent0-5-mhs.cybertribe.com | agent0-5-mhs.cybertribe.com |

> agent0-1 uses localpart `agent` (created manually during Phase 1). All other agents follow the `agent0-N` convention.

### Shared Infrastructure

| Service | Address | Purpose |
|---------|---------|---------|
| kama (DD-WRT) | 172.23.1.1 | Gateway, DHCP, DNS, VPN, routing |
| step-ca | 172.23.0.103:9000 | Certificate authority (on tarnover) |
| Synapse (K8s) | matrix.v-site.net (147.93.135.115) | Public Matrix gateway |
| VPN tunnel | 172.23.200.0/24 | Contabo <-> home lab |

### Key File Locations

| File | Location |
|------|----------|
| Docker Compose | `/opt/agent-zero/agent0-N/docker-compose.yml` |
| Instance .env | `/opt/agent-zero/agent0-N/.env` |
| Agent Zero persistent data | `/opt/agent-zero/agent0-N/usr/` |
| Caddyfile | `/opt/agent-zero/agent0-N/mhs/Caddyfile` |
| Continuwuity data | `/opt/agent-zero/agent0-N/mhs/continuwuity-data/` |
| TLS cert/key | `/opt/agent-zero/agent0-N/mhs/server.crt`, `server.key` |
| Matrix signing key | `/opt/agent-zero/agent0-N/mhs/matrix_key.pem` |
| MCP server (in container) | `/a0/usr/workdir/matrix-mcp-server/` |
| Matrix bot (in container) | `/a0/usr/workdir/matrix-bot/` |
| Startup script (in container) | `/a0/usr/workdir/startup-services.sh` |
| API token patch (in container) | `/a0/usr/workdir/startup-patch.sh` |
| Watchdog (in container) | `/a0/usr/workdir/watchdog.sh` |
| Token sync checker (in container) | `/a0/usr/workdir/check-token-sync.py` |
| Bot log (in container) | `/a0/usr/workdir/matrix-bot/bot.log` |
| Instance creation script | `/opt/agent-zero/multi-instance-deploy/create-instance.sh` |
| Finalize script | `/opt/agent-zero/multi-instance-deploy/finalize-instance.sh` |
| Decommission script | `/opt/agent-zero/multi-instance-deploy/decommission-instance.sh` |

---

*Last updated: March 16, 2026*
