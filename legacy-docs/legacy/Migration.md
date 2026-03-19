# Agent0-1 Migration Guide: Tarnover → g2s

**Version:** 2.0  
**Date:** March 4, 2026  
**Source Host:** tarnover (172.23.0.103, NIC: enp36s0)  
**Target Host:** g2s (172.23.100.121, NIC: eno1)  
**Purpose:** Migrate agent0-1 and its paired Dendrite homeserver to the g2s sovereign fleet  

---

## What Changed Since v1.1 (Feb 28)

| Area | v1.1 (Feb 28) | v2.0 (Current) |
|------|---------------|------------------|
| Directory layout | `/opt/agent-zero/` (flat) | `/opt/agent-zero/agent0-1/` (multi-instance) |
| Docker Compose | Separate files for agent + dendrite | Single dual-container compose per instance |
| Dendrite federation | Not configured | `--https-bind-address :8448` + TLS mounts required |
| Dendrite YAML | `connection:` syntax | `connection_string:` syntax + `room_server` block |
| Matrix identity key | Generic format | YAML format only (not OpenSSH) |
| MCP server entry point | `node dist/index.js` | `node dist/http-server.js` |
| MCP/A2A UI type | `"type": "http"` with headers | `"type": "streamable-http"` — no headers |
| Python paths | `pip` / `python3` | `/opt/venv-a0/bin/pip` / `/opt/venv-a0/bin/python3` |
| TLS certs (Step-CA) | Not documented | `--not-after=8760h` (equals sign required for v0.29.0) |
| g2s infrastructure | Not yet deployed | macvlan + mac0 + agent-bridge.service operational |
| Synapse gateway | Not pre-wired | hostAliases + federation whitelist for slots 1-5 |

---

## Table of Contents

1. [Pre-Migration Checklist](#1-pre-migration-checklist)
2. [g2s Host — Verify Infrastructure](#2-g2s-host--verify-infrastructure)
3. [Backup agent0-1 on Tarnover](#3-backup-agent0-1-on-tarnover)
4. [Create Instance Directory on g2s](#4-create-instance-directory-on-g2s)
5. [Restore Dendrite Identity and Data](#5-restore-dendrite-identity-and-data)
6. [Restore Agent Zero Data](#6-restore-agent-zero-data)
7. [Deploy Matrix Services](#7-deploy-matrix-services)
8. [Update Router (kama)](#8-update-router-kama)
9. [Update Synapse Gateway](#9-update-synapse-gateway)
10. [Post-Migration Verification](#10-post-migration-verification)
11. [Cleanup Tarnover](#11-cleanup-tarnover)
12. [Rollback Procedure](#12-rollback-procedure)

---

## 1. Pre-Migration Checklist

### 1a. Confirm g2s Infrastructure is Running

```bash
# On g2s — verify agent-bridge.service
systemctl status agent-bridge.service

# Verify mac0 bridge
ip addr show mac0
# Expected: 172.23.88.254/32

# Verify macvlan network exists
docker network inspect macvlan-172-23 --format '{{.IPAM.Config}}'
# Expected: [{172.23.0.0/16  172.23.1.1 map[]}]

# Verify existing fleet is unaffected
ping -c 1 -I mac0 172.23.88.2   # agent0-2
ping -c 1 -I mac0 172.23.88.3   # agent0-3
```

### 1b. Record Current agent0-1 State on Tarnover

| Component | Value |
|-----------|-------|
| Agent container | agent0-1 at 172.23.88.1 |
| Dendrite container | agent0-1-mhs at 172.23.89.1 |
| Matrix ID | `@agent:agent0-1-mhs.cybertribe.com` |
| Matrix access token | (retrieve from MCP server `.env`) |
| Server name | `agent0-1-mhs.cybertribe.com` |
| NIC | enp36s0 |

### 1c. Notify Dependent Services

- Pause any scheduled tasks on agent0-1
- Inform Matrix room users of temporary downtime
- Note: Synapse gateway already has hostAliases pre-wired for agent0-1-mhs

---

## 2. g2s Host — Verify Infrastructure

The g2s host should already have the following from prior fleet deployments. **Do not recreate** — just verify.

### 2a. Docker (Rootful)

```bash
docker info | grep -i rootless
# Must NOT show 'rootless' — macvlan requires rootful Docker
```

### 2b. macvlan Network

```bash
docker network ls | grep macvlan-172-23
# Should exist from agent0-2/agent0-3 deployment
```

### 2c. agent-bridge.service

This systemd unit manages promiscuous mode, mac0 bridge, and subnet routes. It was created during the initial g2s setup and persists across reboots.

```bash
systemctl is-active agent-bridge.service
# Expected: active
```

### 2d. iptables FORWARD Rules

```bash
iptables -L FORWARD -n | grep -E '172.23.88|172.23.89'
# Should show ACCEPT rules for .88.0/24 and .89.0/24 subnets
```

> **If any of the above are missing**, refer to `multi-instance-guide.md` Section 2 (Host Infrastructure).

---

## 3. Backup agent0-1 on Tarnover

### 3a. Create Backup Directory

```bash
# On tarnover
mkdir -p ~/migration-backup
```

### 3b. Capture Container Configuration

```bash
docker inspect agent0-1 > ~/migration-backup/agent0-1-inspect.json
docker inspect agent0-1-mhs > ~/migration-backup/dendrite-inspect.json
```

### 3c. Backup Agent Zero Persistent Data

```bash
# This includes settings, memories, knowledge, workdir, matrix-bot, matrix-mcp-server
tar -czvf ~/migration-backup/agent0-1-usr.tar.gz -C /opt/agent-zero usr/
```

### 3d. Backup Dendrite Data

```bash
# Identify Dendrite mount points
docker inspect agent0-1-mhs --format '{{range .Mounts}}{{.Source}}:{{.Destination}}
{{end}}'

# Key files to preserve:
# - matrix_key.pem (server identity — MUST be preserved for federation)
# - dendrite.db or media_store (if using SQLite)
# - server.crt + server.key (TLS certs — can be regenerated via Step-CA)
# - dendrite.yaml (will be regenerated from template)

# Backup everything
DENDRITE_DIR=$(docker inspect agent0-1-mhs --format '{{range .Mounts}}{{if eq .Destination "/etc/dendrite"}}{{.Source}}{{end}}{{end}}')
tar -czvf ~/migration-backup/dendrite-data.tar.gz -C "$DENDRITE_DIR" .
```

### 3e. Backup Docker Compose Files

```bash
cp ~/Agent0/docker-compose.yml ~/migration-backup/agent0-1-compose.yml
find /opt -name 'docker-compose.yml' -path '*dendrite*' -exec cp {} ~/migration-backup/dendrite-compose.yml \;
```

### 3f. Stop Services on Tarnover

```bash
# Stop both containers (agent first, then homeserver)
docker stop agent0-1
docker stop agent0-1-mhs
```

---

## 4. Create Instance Directory on g2s

Do **NOT** use `create-instance.sh` for migrations — it generates new identities. Instead, create the directory structure manually and restore data into it.

### 4a. Create Directory Layout

```bash
# On g2s
mkdir -p /opt/agent-zero/agent0-1/{usr,mhs}
```

### 4b. Generate Docker Compose from Template

Use the v3.11 template but substitute N=1:

```bash
cd /opt/agent-zero/multi-instance-deploy

sed -e 's/__INSTANCE_NUM__/1/g' \
    -e 's/__AGENT_IP__/172.23.88.1/g' \
    -e 's/__AGENT_MAC__/02:42:AC:17:58:01/g' \
    -e 's/__MHS_IP__/172.23.89.1/g' \
    -e 's/__MHS_MAC__/02:42:AC:17:59:01/g' \
    -e 's/__WEB_PORT__/50001/g' \
    templates/docker-compose.yml.template > /opt/agent-zero/agent0-1/docker-compose.yml
```

### 4c. Generate .env File

Copy the `.env` template and populate with agent0-1's existing API keys and credentials:

```bash
cp templates/env.template /opt/agent-zero/agent0-1/.env

# Edit with actual values — preserve agent0-1's original AUTH credentials
nano /opt/agent-zero/agent0-1/.env
```

Key fields to set:
```env
AUTH_LOGIN=<original agent0-1 login>
AUTH_PASSWORD=<original agent0-1 password>
A0_SET_chat_model_name=<original model>
A0_SET_chat_model_provider=<original provider>
# API keys — copy from tarnover's .env or set fresh
```

---

## 5. Restore Dendrite Identity and Data

### 5a. Transfer Backups to g2s

```bash
# On tarnover
scp ~/migration-backup/dendrite-data.tar.gz l0r3zz@g2s.cybertribe.com:/tmp/
scp ~/migration-backup/agent0-1-usr.tar.gz l0r3zz@g2s.cybertribe.com:/tmp/
```

### 5b. Restore Dendrite Files

```bash
# On g2s
cd /opt/agent-zero/agent0-1/mhs
tar -xzvf /tmp/dendrite-data.tar.gz -C .
```

### 5c. Verify Critical Identity Files

```bash
# matrix_key.pem — MUST be in YAML format (not OpenSSH)
head -3 /opt/agent-zero/agent0-1/mhs/matrix_key.pem
# Expected format:
#   Key ID: ed25519:<random>
#   Key: <base64 string>
# NOT: -----BEGIN OPENSSH PRIVATE KEY-----

# If wrong format, DO NOT regenerate — copy the original from tarnover
```

> ⚠️ **CRITICAL:** The `matrix_key.pem` is the server's federation identity.
> Regenerating it will break all existing room memberships and federation
> trust. Always preserve the original key during migration.

### 5d. Generate Dendrite Config from Template

```bash
sed -e 's/__INSTANCE_NUM__/1/g' \
    templates/dendrite.yaml.template > /opt/agent-zero/agent0-1/mhs/dendrite.yaml
```

Verify the generated config:
```bash
# Check server_name
grep 'server_name:' /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# Expected: server_name: agent0-1-mhs.cybertribe.com

# Check all database entries use connection_string (NOT connection:)
grep -c 'connection_string:' /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# Expected: 9 (one per database block)

# Check room_server block exists
grep 'room_server:' /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# Must exist — Dendrite crashes without it
```

### 5e. TLS Certificates

You have two options:

**Option A: Reuse existing certs from tarnover** (if not expired)
```bash
# Certs should already be in mhs/ from the backup
ls -la /opt/agent-zero/agent0-1/mhs/server.crt
ls -la /opt/agent-zero/agent0-1/mhs/server.key
openssl x509 -in /opt/agent-zero/agent0-1/mhs/server.crt -noout -enddate
```

**Option B: Generate new certs via Step-CA** (recommended)
```bash
# On tarnover (where Step-CA runs)
step ca certificate \
    "agent0-1-mhs.cybertribe.com" \
    agent0-1-mhs.crt agent0-1-mhs.key \
    --san "agent0-1-mhs.cybertribe.com" \
    --not-after=8760h

# Append CA chain for full bundle
step ca root >> agent0-1-mhs.crt

# Transfer to g2s
scp agent0-1-mhs.crt l0r3zz@g2s.cybertribe.com:/opt/agent-zero/agent0-1/mhs/server.crt
scp agent0-1-mhs.key l0r3zz@g2s.cybertribe.com:/opt/agent-zero/agent0-1/mhs/server.key

# Set permissions on g2s
chmod 644 /opt/agent-zero/agent0-1/mhs/server.crt
chmod 600 /opt/agent-zero/agent0-1/mhs/server.key
```

> **Note:** Step-CA v0.29.0 requires `--not-after=8760h` with equals sign.
> The `--bundle` flag is not supported in this version — append the CA chain manually.

---

## 6. Restore Agent Zero Data

### 6a. Extract Persistent Data

```bash
# On g2s
cd /opt/agent-zero/agent0-1
tar -xzvf /tmp/agent0-1-usr.tar.gz

# Verify key directories
ls usr/workdir/matrix-mcp-server/.env
ls usr/workdir/matrix-bot/.env
ls usr/workdir/startup-services.sh
```

### 6b. Update Matrix Service Configs for New Host

The `.env` files inside matrix-mcp-server and matrix-bot may reference old hostnames or IPs. Verify they point to the Docker internal DNS name:

```bash
# matrix-mcp-server .env — homeserver URL should use Docker DNS
grep MATRIX_HOMESERVER_URL /opt/agent-zero/agent0-1/usr/workdir/matrix-mcp-server/.env
# Expected: MATRIX_HOMESERVER_URL=http://agent0-1-mhs:8008
# If it shows an IP like 172.23.89.1, update it:
# sed -i 's|MATRIX_HOMESERVER_URL=.*|MATRIX_HOMESERVER_URL=http://agent0-1-mhs:8008|' \
#   /opt/agent-zero/agent0-1/usr/workdir/matrix-mcp-server/.env

# matrix-bot .env — same check
grep MATRIX_HOMESERVER_URL /opt/agent-zero/agent0-1/usr/workdir/matrix-bot/.env
```

---


> **SMTP Credentials:** If SMTP was configured on the source instance,
> the credentials are stored in `usr/workdir/matrix-bot/.env`. These are
> preserved automatically by the `usr/` backup. Verify `SMTP_PASS` and
> `SMTP_USER` values after restore - see multi-instance-guide Section 5.6.

## 7. Deploy Matrix Services

### 7a. Start Containers

```bash
cd /opt/agent-zero/agent0-1
docker compose up -d

# Wait for containers to initialize
sleep 10

# Verify both containers are running
docker compose ps
# Expected: agent0-1 (Up), agent0-1-mhs (Up)
```

### 7b. Verify Dendrite

```bash
# Check logs for clean startup
docker logs agent0-1-mhs --tail=20

# Test client API
curl -s http://172.23.89.1:8008/_matrix/client/versions | head

# Test federation endpoint
curl -sk https://172.23.89.1:8448/_matrix/key/v2/server | python3 -m json.tool
# Expected: JSON with server_name and verify_keys
```

### 7c. Install and Start MCP Server (inside agent container)

```bash
docker exec -it agent0-1 bash

cd /a0/usr/workdir/matrix-mcp-server
npm install
node dist/http-server.js &

# Verify
curl -s http://localhost:3000/mcp | head -c 200
```

> **Entry point is `dist/http-server.js`** — NOT `dist/index.js` (which is just an export module).

### 7d. Install and Start Matrix Bot (inside agent container)

```bash
cd /a0/usr/workdir/matrix-bot
/opt/venv-a0/bin/pip install -r requirements.txt
/opt/venv-a0/bin/python3 matrix_bot.py &

# Verify
tail -5 bot.log
# Expected: "Starting sync loop — bot is live!"
```

> **Use full venv paths:** `/opt/venv-a0/bin/pip` and `/opt/venv-a0/bin/python3`.
> Bare `pip` and `python3` resolve to system Python which has no packages.

### 7e. Configure MCP/A2A in Agent Zero UI

Open `http://agent0-1.cybertribe.com/` → Settings → MCP/A2A tab.

Paste:
```json
{
    "mcpServers": {
        "matrix": {
            "description": "Matrix homeserver bridge for agent-to-agent and human-agent communication",
            "url": "http://localhost:3000/mcp",
            "type": "streamable-http"
        }
    }
}
```

Click **Save** — should show ~20 Matrix tools.

> **Type must be `streamable-http`** — NOT `http`. No headers block needed;
> the MCP server reads credentials from its own `.env` file.

---

## 8. Update Router (kama)

### 8a. Update /32 Static Routes

Agent0-1's container IPs now originate from g2s instead of tarnover:

```bash
# SSH to kama (DD-WRT router)
ssh root@172.23.1.1

# Remove old routes pointing to tarnover
ip route del 172.23.88.1/32 via 172.23.0.103 2>/dev/null || true
ip route del 172.23.89.1/32 via 172.23.0.103 2>/dev/null || true

# Add new routes pointing to g2s
ip route add 172.23.88.1/32 via 172.23.100.121
ip route add 172.23.89.1/32 via 172.23.100.121

# Verify all agent routes point to g2s
ip route show | grep -E '172.23.88|172.23.89'
```

### 8b. Update DD-WRT Startup Script

Navigation: **Administration → Commands → Startup**

Update the startup script so all agent routes point to g2s:

```bash
#!/bin/sh
# Agent fleet routes — all on g2s (172.23.100.121)
ip route add 172.23.88.1/32 via 172.23.100.121   # agent0-1
ip route add 172.23.89.1/32 via 172.23.100.121   # agent0-1-mhs
ip route add 172.23.88.2/32 via 172.23.100.121   # agent0-2
ip route add 172.23.89.2/32 via 172.23.100.121   # agent0-2-mhs
ip route add 172.23.88.3/32 via 172.23.100.121   # agent0-3
ip route add 172.23.89.3/32 via 172.23.100.121   # agent0-3-mhs
```

Click **Save Startup**.

---

## 9. Update Synapse Gateway

The Synapse gateway at `matrix.v-site.net` should already have agent0-1-mhs in its hostAliases and federation whitelist (pre-wired for slots 1-5). Verify:

```bash
# From the K8s environment
kubectl get deploy matrix -n matrix -o jsonpath='{.spec.template.spec.hostAliases}' | python3 -m json.tool
# Should include: {"ip": "172.23.89.1", "hostnames": ["agent0-1-mhs.cybertribe.com"]}
```

If agent0-1-mhs is missing from hostAliases:
```bash
kubectl patch deploy matrix -n matrix --type=json -p '[
  {"op": "add", "path": "/spec/template/spec/hostAliases/-",
   "value": {"ip": "172.23.89.1", "hostnames": ["agent0-1-mhs.cybertribe.com"]}}
]'
```

After migration, reset Synapse's federation cache for agent0-1-mhs:
```bash
kubectl exec -n matrix <synapse-pod> -c matrix -- curl -s -X POST \
  "http://localhost:8008/_synapse/admin/v1/federation/destinations/agent0-1-mhs.cybertribe.com/reset_connection" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

## 10. Post-Migration Verification

### 10a. Container Connectivity

```bash
# From g2s host
ping -c 1 -I mac0 172.23.88.1   # Agent Zero
ping -c 1 -I mac0 172.23.89.1   # Dendrite

# From kama
ssh root@172.23.1.1 ping -c 1 172.23.88.1
ssh root@172.23.1.1 ping -c 1 172.23.89.1
```

### 10b. Dendrite Federation

```bash
# From Synapse K8s pod via VPN
kubectl exec -n matrix <synapse-pod> -c openvpn -- \
  wget -qO- --no-check-certificate https://agent0-1-mhs.cybertribe.com:8448/_matrix/key/v2/server
```

### 10c. Agent Zero Dashboard

Open `http://agent0-1.cybertribe.com/` — should reach the login page.

### 10d. Matrix MCP Tools

In the Agent Zero dashboard, verify ~20 Matrix tools are available. Ask the agent:
> "What is your Matrix identity?"

Expected response: `@agent:agent0-1-mhs.cybertribe.com`

### 10e. Matrix Bot

From Element (logged into matrix.v-site.net), send a message in a room with agent0-1. The bot should respond.

### 10f. Full Fleet Ping

```bash
# From g2s — verify migration didn't break other instances
for N in 1 2 3; do
  echo -n "agent0-$N: "
  curl -so /dev/null -w "%{http_code}" http://172.23.88.$N/
  echo -n "  mhs: "
  curl -so /dev/null -w "%{http_code}" http://172.23.89.$N:8008/_matrix/client/versions
  echo
done
```

---

## 11. Cleanup Tarnover

> ⚠️ **Only after ALL verification checks pass.**

### 11a. Remove Containers

```bash
# On tarnover
docker rm agent0-1
docker rm agent0-1-mhs
```

### 11b. Remove Docker Network (if no other containers use it)

```bash
docker network inspect macvlan-172-23 --format '{{range .Containers}}{{.Name}} {{end}}'
# If empty:
docker network rm macvlan-172-23
```

### 11c. Remove mac0 Bridge

```bash
systemctl stop mac0-macvlan.service 2>/dev/null || true
systemctl disable mac0-macvlan.service 2>/dev/null || true
rm -f /etc/systemd/system/mac0-macvlan.service
systemctl daemon-reload
ip link del mac0 2>/dev/null || true
```

### 11d. Remove iptables Rules

```bash
iptables -D FORWARD -s 172.23.0.0/16 -d 172.23.88.0/24 -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -s 172.23.0.0/16 -d 172.23.89.0/24 -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -s 172.23.88.0/24 -d 172.23.0.0/16 -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -s 172.23.89.0/24 -d 172.23.0.0/16 -j ACCEPT 2>/dev/null || true
netfilter-persistent save
```

### 11e. Disable Promiscuous Mode

```bash
ip link set enp36s0 promisc off
```

### 11f. Archive Data (Optional)

```bash
# Keep backups but remove active data
# rm -rf /opt/agent-zero   # DANGER — only if backup confirmed
```

### 11g. Verify Clean State

```bash
ip route | grep -E '172.23.88|172.23.89'         # Should be empty
ip link show mac0 2>&1                            # "does not exist"
iptables -L FORWARD -n | grep -E '172.23.88|89'  # Should be empty
docker network ls | grep macvlan                  # Should be empty
```

---

## 12. Rollback Procedure

If migration fails, restore on tarnover:

### 12a. Restore Infrastructure

```bash
# On tarnover
# Recreate macvlan
docker network create -d macvlan \
  --subnet=172.23.0.0/16 --gateway=172.23.1.1 \
  -o parent=enp36s0 macvlan-172-23

# Restore mac0
systemctl enable --now mac0-macvlan.service

# Restore iptables
iptables -I FORWARD -s 172.23.0.0/16 -d 172.23.88.0/24 -j ACCEPT
iptables -I FORWARD -s 172.23.0.0/16 -d 172.23.89.0/24 -j ACCEPT
iptables -I FORWARD -s 172.23.88.0/24 -d 172.23.0.0/16 -j ACCEPT
iptables -I FORWARD -s 172.23.89.0/24 -d 172.23.0.0/16 -j ACCEPT
netfilter-persistent save
```

### 12b. Restore Data and Start

```bash
tar -xzvf ~/migration-backup/agent0-1-usr.tar.gz -C /opt/agent-zero/
tar -xzvf ~/migration-backup/dendrite-data.tar.gz -C /opt/dendrite/

# Start containers
docker compose -f /opt/dendrite/docker-compose.yml up -d
docker compose -f ~/Agent0/docker-compose.yml up -d
```

### 12c. Restore kama Routes

```bash
ssh root@172.23.1.1
ip route del 172.23.88.1/32 via 172.23.100.121 2>/dev/null || true
ip route del 172.23.89.1/32 via 172.23.100.121 2>/dev/null || true
ip route add 172.23.88.1/32 via 172.23.0.103
ip route add 172.23.89.1/32 via 172.23.0.103
```

---

## Quick Reference

### IP Assignments

| Component | IP | MAC | Port |
|-----------|-----|-----|------|
| agent0-1 | 172.23.88.1 | 02:42:AC:17:58:01 | 80 (Web UI) |
| agent0-1-mhs | 172.23.89.1 | 02:42:AC:17:59:01 | 8008, 8448 (TLS) |
| mac0 bridge | 172.23.88.254 | — | — |

### Key Files to Preserve

| File | Purpose | Regenerate? |
|------|---------|-------------|
| `mhs/matrix_key.pem` | Server federation identity | ❌ **NEVER** — breaks rooms |
| `mhs/server.crt` + `server.key` | TLS for federation | ✅ Via Step-CA |
| `mhs/dendrite.yaml` | Server config | ✅ From template |
| `usr/` directory | All agent data, memories, settings | ❌ Preserve |
| `matrix-mcp-server/.env` | MCP credentials + access token | ❌ Preserve |
| `matrix-bot/.env` | Bot credentials + API key | ❌ Preserve |

### Battle-Tested Gotchas

| Issue | Fix |
|-------|-----|
| `node dist/index.js` exits silently | Use `node dist/http-server.js` |
| `pip: command not found` | Use `/opt/venv-a0/bin/pip` |
| MCP shows 405 Method Not Allowed | Change type to `streamable-http` |
| `keyBlock is nil` on Dendrite start | `matrix_key.pem` must be YAML format, not OpenSSH |
| Dendrite crashes on start | Check for `connection_string:` (not `connection:`) and `room_server:` block |
| Federation port 8448 unreachable | Ensure `--https-bind-address :8448` in compose command |
| Step-CA `too many positional arguments` | Use `--not-after=8760h` (with equals sign) |

---

**End of Migration Guide v2.0**
