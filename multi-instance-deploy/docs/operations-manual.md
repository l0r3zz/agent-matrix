# Agent-Matrix Operations Manual

**Version:** 1.1  
**Date:** March 5, 2026  
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

Agent creation uses the `create-instance.sh` script, which generates a complete Agent Zero + Continuwuity homeserver pair from templates.

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
- `docker-compose.yml` — unified Agent Zero + Continuwuity stack
- `.env` — API keys, auth credentials, agent profile
- `mhs/Continuwuity.yaml` — Continuwuity homeserver configuration
- `mhs/data/` — Continuwuity data directory
- `usr/` — Agent Zero persistent data

### 2.2 Generate a Matrix Signing Key

Continuwuity requires a signing key for federation. Generate one before starting:

The `create-instance.sh` script generates the key automatically using a Python one-liner. If you need to generate one manually:

```bash
cd /opt/agent-zero/agent0-N
python3 -c "
import base64, hashlib, os
raw = os.urandom(32)
key_id = 'ed25519:' + base64.urlsafe_b64encode(hashlib.sha256(raw).digest())[:6].decode()
b64_key = base64.b64encode(raw).decode()
with open('mhs/matrix_key.pem', 'w') as f:
    f.write(f'-----BEGIN MATRIX PRIVATE KEY-----\nKey-ID: {key_id}\n{b64_key}\n-----END MATRIX PRIVATE KEY-----\n')
print(f'Generated {key_id}')
"
```

> **⚠️ WARNING:** Do NOT use `ssh-keygen` — Continuwuity requires YAML-formatted Matrix keys, not OpenSSH format. Using the wrong format causes a fatal "keyBlock is nil" error.

Alternatively, use the Continuwuity container's built-in generator (note: the image must be the correct one):

```bash
docker run --rm -v $(pwd)/mhs:/etc/Continuwuity \
  ghcr.io/element-hq/Continuwuity-monolith:v0.15.2 \
  /usr/bin/generate-keys --private-key /etc/Continuwuity/matrix_key.pem
```

### 2.3 Issue TLS Certificates (for Federation)

Each Continuwuity instance needs a TLS certificate signed by the step-ca PKI:

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

### 2.4 Start the Agent

```bash
cd /opt/agent-zero/agent0-N
docker compose up -d
```

Verify both containers are running:

```bash
docker ps | grep agent0-N
```

You should see two containers: `agent0-N` (Agent Zero) and `agent0-N-mhs` (Continuwuity).

### 2.5 Create Matrix Users on Continuwuity

```bash
# Create the agent's primary user
docker exec agent0-N-mhs /usr/bin/one-time bootstrap token from logs \
  -config /etc/Continuwuity/Continuwuity.yaml \
  -username agent0-N -password <secure-password>

# Create an admin user (for password resets and management)
docker exec agent0-N-mhs /usr/bin/one-time bootstrap token from logs \
  -config /etc/Continuwuity/Continuwuity.yaml \
  -username agentadmin -password <admin-password> -admin
```

Save the access token returned by the `one-time bootstrap token from logs` command — you will need it for MCP server configuration.

### 2.6 Obtain an Access Token

If you need to obtain a fresh access token:

```bash
curl -s -X POST http://172.23.89.N:8008/_matrix/client/v3/login \
  -H 'Content-Type: application/json' \
  -d '{"type":"m.login.password","identifier":{"type":"m.id.user","user":"agent0-N"},"password":"<password>","device_id":"AgentZeroBot"}' | python3 -m json.tool
```

Copy the `access_token` from the response.

### 2.7 Update Agent-Internal Configuration

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
MATRIX_ACCESS_TOKEN=<token-from-step-2.6>
EOF

# Configure matrix-bot
cat > /a0/usr/workdir/matrix-bot/.env << EOF
MATRIX_HOMESERVER=http://agent0-N-mhs:8008
MATRIX_USER_ID=@agent0-N:agent0-N-mhs.cybertribe.com
MATRIX_ACCESS_TOKEN=<token-from-step-2.6>
A0_BASE_URL=http://localhost
A0_API_KEY=<will-be-set-by-startup-patch>
EOF

# Restart services
bash /a0/usr/workdir/startup-services.sh
```

> **Note:** When manually starting the bot or installing pip packages, use the virtual environment:
> - `/opt/venv-a0/bin/pip install -r requirements.txt`
> - `/opt/venv-a0/bin/python3 matrix_bot.py`
>
> The system `python3` and `pip` lack required packages.
```

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

> **CRITICAL:** The `hostAliases` step is the most commonly missed step when adding a new agent. Without it, Synapse cannot resolve the new Continuwuity hostname, causing **502 Bad Gateway** on federation room joins. Invites may appear to work (outbound federation succeeds) but join acceptance fails (inbound federation is broken).

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
# Both containers running
docker ps | grep agent0-N

# Continuwuity CS API responding
curl -s http://172.23.89.N:8008/_matrix/client/versions | python3 -m json.tool

# Continuwuity Federation API (TLS)
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

# Continuwuity data
tar -czvf ~/migration-backup/agent0-N-mhs-data.tar.gz /opt/agent-zero/agent0-N/mhs/

# Docker compose and env
cp /opt/agent-zero/agent0-N/docker-compose.yml ~/migration-backup/
cp /opt/agent-zero/agent0-N/.env ~/migration-backup/

# Record current IP/MAC (should remain the same after migration)
docker inspect agent0-N --format '{{.NetworkSettings.Networks}}' > ~/migration-backup/network-config.txt
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
# On destination host
mkdir -p /opt/agent-zero/agent0-N
cd /opt/agent-zero/agent0-N

# Restore files
cp /tmp/migration/docker-compose.yml .
cp /tmp/migration/.env .
mkdir -p usr mhs/data
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

# Continuwuity logs
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

### 7.5 Continuwuity Admin: Reset a User Password

```bash
# Get an admin access token first
docker exec agent0-N-mhs /usr/bin/one-time bootstrap token from logs \
  -config /etc/Continuwuity/Continuwuity.yaml \
  -username agentadmin -password <admin-pw> -admin

# Reset password
curl -s -X POST http://172.23.89.N:8008/_Continuwuity/admin/resetPassword/<username> \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <admin_access_token>' \
  -d '{"password": "<new_password>"}'
```

> Continuwuity uses `/_Continuwuity/admin/` prefix. Synapse admin commands (`register_new_matrix_user`, etc.) do **not** work with Continuwuity.

### 7.6 Check Federation Status

```bash
# Continuwuity federation endpoint
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

### 7.8 Check Fleet Model Configuration

Report which LLM models each agent is currently using (reads actual runtime config from inside each container):

```bash
cd /opt/agent-zero/multi-instance-deploy/templates/scripts

# Standard table view
./fleet-models.sh

# With provider details and context window sizes
./fleet-models.sh --verbose

# Diagnostic checks (Change Detection, Config Sync)
./fleet-models.sh --diagnose

# JSON output (for scripting)
./fleet-models.sh --json

# Specific agents only
./fleet-models.sh --instances 2,3
```

| Flag | Description |
|------|-------------|
| `--verbose` | Show providers, context window sizes, and full model names |
| `--diagnose` | Run Change Detection and MCP Config Sync Check |
| `--json` | Machine-readable JSON output |
| `--instances N,N,...` | Comma-separated instance numbers (default: all) |

**Sample Output:**
```
  Agent        Profile      Main Model               Utility Model            Embedding
  agent0-1     agent0       xiaomi/mimo-v2-pro       openai/gpt-5.4-nano      sentence-transform
  agent0-2     agent0       perplexity/sonar         google/gemini-3-flash-   sentence-transform
  agent0-4     hacker       minimax/minimax-m2.7     google/gemini-3-flash-   sentence-transform
```

> **Note:** This script reads `/a0/usr/plugins/_model_config/config.json` inside each container — the actual runtime configuration, not `.env` template defaults.
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

## 7.6 Token Mismatch Prevention System

The MCP server authenticates to Matrix using an access token. This token exists in **two locations**:
1. The MCP server's `.env` file (`MATRIX_ACCESS_TOKEN`)
2. Agent Zero's `settings.json` (`mcp_servers` > matrix > headers > `matrix_access_token`)

If these drift apart (e.g., after a token rotation or re-login), the MCP server receives a stale token from A0 headers and fails with `M_UNKNOWN_TOKEN`. A three-layer prevention system guards against this.

### Layer 1: Watchdog v2.0 (Boot & Runtime Guard)

The watchdog script monitors both the bot and MCP server processes and performs periodic health checks.

- **Location**: `/a0/usr/workdir/watchdog.sh`
- **Template**: `templates/scripts/watchdog.sh`
- **Process check interval**: 30 seconds
- **Deep health check interval**: 300 seconds (5 minutes)

Health checks include:
- Matrix auth validation via `/account/whoami`
- Token sync comparison between `.env` and `settings.json`
- Auto-restart of MCP server on auth failure

Helper script: `check-token-sync.py` (in same directory) compares both token sources.

### Layer 2: TOKEN-GUARD (Code-Level Fallback)

The MCP server's `getAccessToken()` function (in `src/utils/server-helpers.ts`) treats the `.env` token as **authoritative**. If the header token differs from `.env`, it logs a warning and silently falls back to the `.env` value.

This prevents stale A0 headers from causing authentication failures at runtime.

### Layer 3: Scheduled Health Probe (Monitoring)

A scheduled task runs every 30 minutes and performs:
1. MCP process alive check
2. Matrix auth validation
3. Token sync verification
4. MCP tool response test (`list-joined-rooms`)
5. User notification on failure

Create via A0 scheduler or verify with `scheduler:list_tasks`.

### Manual Token Refresh Procedure

If all three layers fail or tokens need manual rotation:

```bash
# 1. Get a new token (inside agent container)
curl -s -X POST http://agent0-N-mhs:8008/_matrix/client/v3/login \
  -H "Content-Type: application/json" \
  -d '{"type":"m.login.password","user":"@agent0-N:agent0-N-mhs.cybertribe.com","password":"YOUR_PASSWORD"}' \
  | jq -r '.access_token'

# 2. Update .env
sed -i "s/^MATRIX_ACCESS_TOKEN=.*/MATRIX_ACCESS_TOKEN=NEW_TOKEN/" /a0/usr/workdir/matrix-mcp-server/.env

# 3. Update A0 settings.json (MCP headers)
# Edit /a0/usr/settings.json -> mcp_servers -> matrix -> headers -> matrix_access_token

# 4. Restart MCP server
kill $(pgrep -f http-server.js)
cd /a0/usr/workdir/matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &

# 5. Verify
curl -s http://localhost:3000/health
```

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| `watchdog.sh` | `templates/scripts/` | Process monitoring + health checks |
| `check-token-sync.py` | `templates/scripts/` | Token comparison helper |
| `server-helpers.ts` | `templates/matrix-mcp-server/src/utils/` | TOKEN-GUARD fallback logic |

## 8. Quick Troubleshooting

### 502 Bad Gateway on Federation Room Join

**Symptom:** User receives invite from agent but gets 502 when accepting.

**Root cause:** Missing `hostAliases` in the Synapse K8s deployment. Synapse cannot resolve the Continuwuity hostname.

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
1. TLS certificate valid? `step certificate inspect /opt/agent-zero/agent0-N/mhs/server.crt --short`
2. Routes exist on kama? `ssh root@172.23.1.1 ip route | grep 172.23.89.N`
3. Synapse whitelist includes domain? Check the ConfigMap
4. VPN tunnel up? `ping 172.23.200.1` from kama
5. iptables FORWARD rules allow traffic? `iptables -L FORWARD -n | grep 172.23`

### Docker macvlan Creation Fails

**Symptom:** `invalid subinterface vlan name`

**Root cause:** Docker is in rootless mode.

**Fix:** See [Prerequisites Section 1.1](#11-docker-host-requirements) for switching to rootful.

### MCP Server Not Responding

**Symptom:** Agent cannot use Matrix tools.

**First:** Check if this is a token mismatch issue (most common cause). See **Section 7.6 Token Mismatch Prevention System**.

```bash
# Quick token sync check
docker exec agent0-N python3 /a0/usr/workdir/check-token-sync.py

# Check if running
docker exec agent0-N ps aux | grep http-server.js

# Check logs (look for M_UNKNOWN_TOKEN)
docker exec agent0-N tail -50 /a0/usr/workdir/matrix-mcp-server/mcp-server.log

# Restart
docker exec agent0-N bash -c "kill \$(pgrep -f http-server.js); cd /a0/usr/workdir/matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &"
```

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

### Room Alias Join Fails (500 Error)

**Symptom:** Joining by `#room:server` fails with 500.

**Root cause:** Continuwuity v0.15.x bug with federated room alias resolution.

**Workaround:** Always join by room ID (`!id:server`) instead of alias.

### K8s DNS / Cilium / OpenVPN Issues

For deeper infrastructure issues (K8s cross-node DNS failures, Cilium BPF issues, or OpenVPN tunnel problems), see the [Theory of Operations](theory-of-operations.md) sections on Kubernetes Cluster (Section 3) and Network Deep Dive (Section 2).

---

## 9. Reference: Port and IP Allocation

### IP Addressing Scheme

| Instance N | Agent Zero IP | Continuwuity IP | Agent MAC | Continuwuity MAC |
|-----------|--------------|-------------|-----------|-------------|
| 1 | 172.23.88.1 | 172.23.89.1 | 02:42:AC:17:58:01 | 02:42:AC:17:59:01 |
| 2 | 172.23.88.2 | 172.23.89.2 | 02:42:AC:17:58:02 | 02:42:AC:17:59:02 |
| 3 | 172.23.88.3 | 172.23.89.3 | 02:42:AC:17:58:03 | 02:42:AC:17:59:03 |
| N | 172.23.88.N | 172.23.89.N | 02:42:AC:17:58:NN | 02:42:AC:17:59:NN |

MAC suffix `NN` is the hex representation of the instance number.

### Port Allocation

| Instance N | Web UI (host) | SSH (host) | MCP Server (container-internal) | Continuwuity CS API | Continuwuity Federation |
|-----------|--------------|------------|--------------------------------|----------------|-------------------|
| 1 | 50001 | 50022 | 3000 | 172.23.89.1:8008 | 172.23.89.1:8448 |
| 2 | 50002 | 50023 | 3000 | 172.23.89.2:8008 | 172.23.89.2:8448 |
| N | 5000N | 5002(N+1) | 3000 | 172.23.89.N:8008 | 172.23.89.N:8448 |

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
| Continuwuity config | `/opt/agent-zero/agent0-N/mhs/Continuwuity.yaml` |
| Continuwuity data | `/opt/agent-zero/agent0-N/mhs/data/` |
| TLS cert/key | `/opt/agent-zero/agent0-N/mhs/server.crt`, `server.key` |
| Matrix signing key | `/opt/agent-zero/agent0-N/mhs/matrix_key.pem` |
| MCP server (in container) | `/a0/usr/workdir/matrix-mcp-server/` |
| Matrix bot (in container) | `/a0/usr/workdir/matrix-bot/` |
| Startup script (in container) | `/a0/usr/workdir/startup-services.sh` |
| API token patch (in container) | `/a0/usr/workdir/startup-patch.sh` |
| Bot log (in container) | `/a0/usr/workdir/matrix-bot/bot.log` |
| Instance creation script | `/opt/agent-zero/multi-instance-deploy/create-instance.sh` |

---

*Last updated: March 2, 2026*

---

## Appendix: Bot Display Name Configuration

### Environment Variable
```bash
BOT_DISPLAY_NAME=Agent0-N    # How bot appears in Matrix Element
```

### Files
- `matrix_bot.py` - Automatically sets name on startup
- `set_display_name.py` - Runtime display name management utility

### Usage Examples
```bash
# Inside Matrix bot directory
cd /opt/agent-zero/agent0-N/matrix-bot

# Change display name
python3 set_display_name.py "Cyber Agent"

# Room-specific alias
python3 set_display_name.py "Support Bot" --room '!abc123:v-site.net'
```



---
**Refreshed 2026-03-13 for Continuwuity v0.5.6 3-Container Architecture (agent0-N, agent0-N-continuwuity, agent0-N-mhs with Caddy). TLS via Caddy. Registration via token extracted from `docker logs agent0-N-continuwuity | tr -d '\033' **. Updated startup, watchdog, decommission procedures.**

## Architecture Overview (Refreshed for v0.5.6 - 3-Container Stack)

The Agent-Matrix fleet uses a standardized **3-container architecture** per instance for Continuwuity v0.5.6:

- **agent0-N**: Main Agent Zero container (172.23.88.N) running the Agent Zero framework, MCP server, and business logic.
- **agent0-N-continuwuity**: Continuwuity v0.5.6 homeserver (internal port 6167, RocksDB backend, bridge-local networking only).
- **agent0-N-mhs**: Caddy reverse proxy container (172.23.89.N) handling TLS termination, client API on 8008, and federation on 8448 with proper certs.

TLS is fully managed by Caddy in the mhs container. All communication between agent and homeserver uses the Matrix protocol via MCP and bot.

## Updated Instance Lifecycle & Procedures

1. **Creation**: Run `./create-instance.sh -n N`
2. **Finalization & Registration**: `./finalize-instance.sh N` - automatically extracts one-time bootstrap/registration token from `docker logs agent0-N-continuwuity 2>&1 | tr -d '\033'`, registers using m.login.registration_token.
3. **Startup**: `startup-services.sh` performs 5-phase boot (install deps, start homeserver, deploy bot, start MCP, launch watchdog).
4. **Monitoring**: `docker compose logs -f`, `docker ps` (expect 3 running containers), watchdog.sh status.
5. **Decommission**: `./decommission-instance.sh N` (removes all 3 containers + associated volumes for continuwuity and mhs).

## Registration and Token Management (Updated)

The one-time bootstrap token is emitted in the continuwuity container logs on first boot. Extract with:
```bash
docker logs agent0-N-continuwuity 2>&1 | tr -d '\033' | grep -oE 'token[^" ]+' | head -1
```
No create-account command is used. See finalize-instance.sh for automation. Token sync verified by check-token-sync.py.

## Service Management

- `startup-services.sh`: Golden 5-phase boot template.
- `watchdog.sh`: Monitors matrix_bot.py, MCP, and restarts as needed.
- Bot runs in the agent0-N container with AGENT_IDENTITY context injection.

**All legacy Dendrite, 2-container references, and old registration methods have been superseded by the above.**


# Operations Manual - Agent-Matrix Sovereign Fleet (Continuwuity v0.5.6 Edition)
**Last Refreshed:** 2026-03-13 for 3-Container Architecture

## Current Architecture (3 Containers per Instance)

Each instance N consists of exactly **3 containers**:
- `agent0-N` (172.23.88.N): Agent Zero runtime + MCP server + matrix_bot.py + watchdog.
- `agent0-N-continuwuity`: Continuwuity v0.5.6 homeserver (RocksDB, internal port 6167, bridge-local only).
- `agent0-N-mhs` (172.23.89.N): Caddy reverse proxy providing TLS termination, client API (8008), federation endpoint (8448).

TLS is exclusively handled by Caddy in the mhs container using certificates from step-ca. No direct Dendrite containers or YAML-based TLS.

## Instance Creation & Finalization

```bash
cd /a0/usr/projects/agent-matrix/multi-instance-deploy
./create-instance.sh -n 4
./finalize-instance.sh 4
```

Token extraction in finalize-instance.sh:
```bash
docker logs agent0-N-continuwuity 2>&1 | tr -d '33' | grep -oE 'token[^" ]+' | head -1
```
Uses m.login.registration_token flow. No create-account binary.

## Service Lifecycle

- **Boot**: startup-services.sh (5-phase: deps, homeserver, bot, MCP, watchdog)
- **Monitoring**: `docker compose ps` (must show 3/3 running), `watchdog.sh status`
- **Logs**: `docker logs -f --tail=100 agent0-N-continuwuity`
- **Decommission**: `./decommission-instance.sh N` (handles continuwuity volume explicitly)

## Common Commands

- Status: `docker ps | grep agent0`
- Restart services: `./startup-services.sh`
- Token sync check: `python3 check-token-sync.py`

All legacy 2-container Dendrite references removed.

