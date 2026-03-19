# Agent0-1 Migration Context Bundle
## For Cursor Terminal Orchestration
**Date:** 2026-03-05
**Prepared by:** Agent0-1 (the agent being migrated)
**Purpose:** Self-contained context for Cursor to orchestrate Agent0-1 migration from tarnover to g2s

---

## 1. YOUR ROLE (CURSOR)

You are orchestrating the migration of Agent Zero instance "agent0-1" from host "tarnover" to host "g2s". Agent0-1 will be **offline** during this process — it cannot help you. You have:
- SSH access to both `tarnover` and `g2s`
- `kubectl` access to the Synapse K8s cluster
- This document as your complete reference

**Critical rule:** Do NOT use `create-instance.sh` for this migration. That script generates new identities and overwrites data. This is a **data-preserving migration** — follow the manual procedure below.

---

## 2. WHAT IS AGENT-MATRIX?

A decentralized lab of AI agents, each with:
- **Agent Zero container** — the AI reasoning engine (Python, web UI on port 80)
- **Dendrite container** — a dedicated Matrix homeserver per agent (ports 8008 + 8448)
- **Matrix MCP Server** — Node.js bridge providing ~20 Matrix tools to the agent
- **Matrix Bot** — Python listener that routes inbound Matrix messages to the agent

All agents connect via Matrix federation through a Synapse gateway at `matrix.v-site.net`.

---

## 3. CURRENT FLEET STATUS

| Instance | Host | Agent IP | MHS IP | Federation | Status |
|---|---|---|---|---|---|
| **agent0-1** | **tarnover** (MIGRATING) | 172.23.88.1 | 172.23.89.1 | Broken | Legacy |
| agent0-2 | g2s | 172.23.88.2 | 172.23.89.2 | Verified | Sovereign |
| agent0-3 | g2s | 172.23.88.3 | 172.23.89.3 | Verified | Sovereign |

---

## 4. ACCESS CREDENTIALS

### SSH
| Host | IP | User | Password |
|---|---|---|---|
| tarnover | (resolve via DNS or known IP) | l0r3zz | (use existing SSH key/session) |
| g2s | 172.23.100.121 | l0r3zz | earthstation |

### Agent0-1 Current Matrix Identity
| Field | Value |
|---|---|
| Current Matrix ID | @agent:agent0-1-mhs.cybertribe.com |
| Target Matrix ID | @agent0-1:agent0-1-mhs.cybertribe.com (NEW) |
| Current access token | MhUEgCvHIRplWdKc_Ta5ETyNdhBmkVAtSEBit5UzrHI |
| Homeserver URL | http://172.23.89.1:8008 |
| Registration shared secret | cybertribe_secret |

### SMTP (preserve in migration)
| Field | Value |
|---|---|
| SMTP_HOST | smtp.gmail.com |
| SMTP_PORT | 587 |
| SMTP_USER | agent0.1.vsite@gmail.com |
| SMTP_PASS | qjvxqfbxginqoxpq |
| SMTP_FROM | agent0.1.vsite@gmail.com |
| FORCE_TLS | true |
| SYNC_TIMEOUT_MS | 30000 |

### Agent Zero Dashboard Auth
Set in .env file:
```
AUTH_LOGIN=admin
AUTH_PASSWORD=<choose a password>
```

---

## 5. NETWORK TOPOLOGY

### IP Addressing Scheme
| Component | IP | MAC | Ports |
|---|---|---|---|
| Agent0-1 (agent) | 172.23.88.1 | 02:42:AC:17:58:01 | 80 (Web UI) |
| Agent0-1 (dendrite) | 172.23.89.1 | 02:42:AC:17:59:01 | 8008, 8448 (TLS) |

### DNS Records (already configured)
- agent0-1.cybertribe.com -> 172.23.88.1
- agent0-1-mhs.cybertribe.com -> 172.23.89.1

### Host Networking on g2s
- **Physical NIC:** eno1
- **Docker network:** macvlan-172-23 (already exists, shared by agent0-2 and agent0-3)
- **Host bridge:** mac0 at 172.23.88.254/32 (for host-to-container comms)
- **Promiscuous mode:** enabled via agent-bridge.service (systemd, already running)
- **Subnets:** 172.23.88.0/24 (agents), 172.23.89.0/24 (homeservers)

### DD-WRT Router (Kama: 172.23.1.1)
After migration, update static routes to point agent0-1 subnets to g2s instead of tarnover:
```bash
ip route del 172.23.88.1/32 2>/dev/null
ip route del 172.23.89.1/32 2>/dev/null
ip route add 172.23.88.1/32 via 172.23.100.121
ip route add 172.23.89.1/32 via 172.23.100.121
```

### Synapse Gateway (matrix.v-site.net)
K8s Synapse deployment already has hostAliases and federation_domain_whitelist for agent0-1-mhs.cybertribe.com.

---

## 6. STEP-BY-STEP MIGRATION PROCEDURE

### Phase 1: Backup (on tarnover)

```bash
# Find the agent0-1 container and volume paths
docker ps | grep agent0
docker inspect agent0-1 | grep -A5 Mounts

# The instance is likely at /opt/agent-zero/ on tarnover
# Stop the container
cd /opt/agent-zero/
docker compose down

# Create tarball of the usr directory
tar czf /tmp/agent0-1-backup.tar.gz -C /opt/agent-zero/ usr/

# Also backup mhs/ if it exists
tar czf /tmp/agent0-1-mhs-backup.tar.gz -C /opt/agent-zero/ mhs/ 2>/dev/null || echo "No mhs dir"

# Transfer to g2s
scp /tmp/agent0-1-backup.tar.gz l0r3zz@172.23.100.121:/tmp/
scp /tmp/agent0-1-mhs-backup.tar.gz l0r3zz@172.23.100.121:/tmp/ 2>/dev/null
```

### Phase 2: Scaffold on g2s

```bash
ssh l0r3zz@172.23.100.121

# Create instance directory (MANUALLY, NOT via create-instance.sh)
sudo mkdir -p /opt/agent-zero/agent0-1/{usr,mhs}
sudo chown -R l0r3zz:l0r3zz /opt/agent-zero/agent0-1/

# Restore the backup
cd /opt/agent-zero/agent0-1/
tar xzf /tmp/agent0-1-backup.tar.gz

# Verify
ls -la usr/
```

### Phase 3: Create docker-compose.yml

Create /opt/agent-zero/agent0-1/docker-compose.yml:

```yaml
version: "3.8"

services:
  agent0-1:
    image: frdel/agent-zero:latest
    container_name: agent0-1
    hostname: agent0-1
    restart: unless-stopped
    env_file: usr/.env
    ports:
      - "50001:80"
    volumes:
      - ./usr:/a0/usr
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.88.1
    mac_address: "02:42:AC:17:58:01"
    extra_hosts:
      - "agent0-1-mhs:172.23.89.1"

  dendrite:
    image: ghcr.io/element-hq/dendrite-monolith:v0.15.2
    container_name: agent0-1-mhs
    hostname: agent0-1-mhs
    restart: unless-stopped
    command: ["--https-bind-address", ":8448"]
    volumes:
      - ./mhs/dendrite.yaml:/etc/dendrite/dendrite.yaml:ro
      - ./mhs/matrix_key.pem:/etc/dendrite/matrix_key.pem:ro
      - ./mhs/server.crt:/etc/dendrite/server.crt:ro
      - ./mhs/server.key:/etc/dendrite/server.key:ro
      - ./mhs/data:/var/dendrite/
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.89.1
    mac_address: "02:42:AC:17:59:01"

networks:
  macvlan-172-23:
    external: true
```

### Phase 4: Generate Matrix Identity Key

Generate a NEW matrix_key.pem (new identity @agent0-1):

```bash
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
with open('/opt/agent-zero/agent0-1/mhs/matrix_key.pem', 'w') as f:
    f.write(chr(10).join(lines) + chr(10))
print('Key generated: ed25519:' + key_id)
"

chmod 600 /opt/agent-zero/agent0-1/mhs/matrix_key.pem
chown 65534:65534 /opt/agent-zero/agent0-1/mhs/matrix_key.pem
```

**CRITICAL:** Key MUST start with `-----BEGIN MATRIX PRIVATE KEY-----`, NOT `-----BEGIN OPENSSH PRIVATE KEY-----`. OpenSSH format causes "keyBlock is nil" crash.

### Phase 5: Generate TLS Certificates

On tarnover (where step-ca runs):

```bash
step ca certificate \
  agent0-1-mhs.cybertribe.com \
  /tmp/agent0-1-server.crt \
  /tmp/agent0-1-server.key \
  --not-after=8760h

# NOTE: Use = with --not-after (Smallstep CLI v0.29.0 quirk)
# NOTE: --bundle flag does NOT work in v0.29.0

# Manually bundle cert chain:
step ca root /tmp/root.pem
cat /tmp/agent0-1-server.crt /tmp/root.pem > /tmp/agent0-1-server-bundled.crt

# Transfer to g2s:
scp /tmp/agent0-1-server-bundled.crt l0r3zz@172.23.100.121:/opt/agent-zero/agent0-1/mhs/server.crt
scp /tmp/agent0-1-server.key l0r3zz@172.23.100.121:/opt/agent-zero/agent0-1/mhs/server.key

# On g2s:
chmod 644 /opt/agent-zero/agent0-1/mhs/server.crt
chmod 600 /opt/agent-zero/agent0-1/mhs/server.key
chown 65534:65534 /opt/agent-zero/agent0-1/mhs/server.crt /opt/agent-zero/agent0-1/mhs/server.key
```

### Phase 6: Create Dendrite Configuration

```bash
# Copy from working agent0-2 and modify:
cp /opt/agent-zero/agent0-2/mhs/dendrite.yaml /opt/agent-zero/agent0-1/mhs/dendrite.yaml
sed -i 's/agent0-2/agent0-1/g' /opt/agent-zero/agent0-1/mhs/dendrite.yaml

# Verify:
grep server_name /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# Must show: agent0-1-mhs.cybertribe.com

grep connection_string /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# Must show connection_string: (NOT connection:)

grep tls_cert /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# Must show /etc/dendrite/server.crt
```

**CRITICAL:** Use `connection_string:` not `connection:` — wrong syntax causes silent crash loops.

### Phase 7: Update .env File

Verify /opt/agent-zero/agent0-1/usr/.env has AUTH_LOGIN and AUTH_PASSWORD set.

### Phase 8: Launch Containers

```bash
cd /opt/agent-zero/agent0-1/
docker compose up -d
docker compose ps
# Both agent0-1 and agent0-1-mhs should be running

docker logs agent0-1-mhs 2>&1 | tail -20
# Good: "Dendrite version ..."
# Bad: "keyBlock is nil" or "missing config key"

# Verify federation port:
docker exec agent0-1-mhs netstat -tlnp 2>/dev/null || docker exec agent0-1-mhs ss -tlnp
# Should show :8008 AND :8448
```

### Phase 9: Register New Matrix Account

```bash
# Ensure registration_shared_secret is in dendrite.yaml
grep registration_shared_secret /opt/agent-zero/agent0-1/mhs/dendrite.yaml
# If missing: add "registration_shared_secret: cybertribe_secret" then restart

docker exec -it agent0-1-mhs \
  /usr/bin/create-account \
  -config /etc/dendrite/dendrite.yaml \
  -username agent0-1 \
  -admin
# Enter a STRONG password - SAVE IT

# Get access token:
curl -s -X POST http://172.23.89.1:8008/_matrix/client/r0/login \
  -H "Content-Type: application/json" \
  -d '{"type":"m.login.password","user":"agent0-1","password":"YOUR_PASSWORD"}' \
  | python3 -m json.tool
# SAVE the access_token
```

### Phase 10: Deploy Matrix MCP Server + Bot

```bash
docker exec -it agent0-1 bash

# --- MCP Server ---
cd /a0/usr/workdir/matrix-mcp-server/
# Update .env with NEW credentials:
cat > .env << 'MCPEOF'
MATRIX_HOMESERVER_URL=http://agent0-1-mhs:8008
MATRIX_USER_ID=@agent0-1:agent0-1-mhs.cybertribe.com
MATRIX_ACCESS_TOKEN=<PASTE_TOKEN_FROM_PHASE_9>
MATRIX_DEVICE_ID=AGENTDEVICE
PORT=3000
MCPEOF

npm install 2>/dev/null
node dist/http-server.js &
curl -s http://localhost:3000/mcp | head -c 100

# --- Matrix Bot ---
cd /a0/usr/workdir/matrix-bot/
cat > .env << 'BOTEOF'
MATRIX_HOMESERVER_URL=http://agent0-1-mhs:8008
MATRIX_BOT_USER=@agent0-1:agent0-1-mhs.cybertribe.com
MATRIX_BOT_PASSWORD=<PASSWORD_FROM_PHASE_9>
AGENT_API_URL=http://localhost:80
AGENT_API_KEY=
SYNC_TIMEOUT_MS=30000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=agent0.1.vsite@gmail.com
SMTP_PASS=qjvxqfbxginqoxpq
SMTP_FROM=agent0.1.vsite@gmail.com
FORCE_TLS=true
BOTEOF

/opt/venv-a0/bin/pip install -r requirements.txt 2>/dev/null
/opt/venv-a0/bin/python3 matrix_bot.py &
```

**CRITICAL PATHS:**
- MCP entry point: `node dist/http-server.js` (NOT `dist/index.js`)
- Python/pip: `/opt/venv-a0/bin/python3` and `/opt/venv-a0/bin/pip` (NOT system python)

### Phase 11: Configure Agent Zero Dashboard

Open http://agent0-1.cybertribe.com/ or http://172.23.88.1/

Settings -> MCP/A2A tab, paste:
```json
{
    "mcpServers": {
        "matrix": {
            "description": "Matrix homeserver bridge",
            "url": "http://localhost:3000/mcp",
            "type": "streamable-http"
        }
    }
}
```

**CRITICAL:** Type MUST be "streamable-http", NOT "http" (causes 405 errors).
**CRITICAL:** Do NOT add headers. MCP server reads from its own .env.

### Phase 12: Update DD-WRT Routes

Point .88.1 and .89.1 to g2s (172.23.100.121) instead of tarnover.

### Phase 13: Verify Federation

```bash
# From g2s:
curl --interface mac0 -sk https://172.23.89.1:8448/_matrix/key/v2/server | python3 -m json.tool

# From Synapse K8s pod:
kubectl exec -it <synapse-pod> -c openvpn -- \
  wget -q -O - --no-check-certificate \
  https://agent0-1-mhs.cybertribe.com:8448/_matrix/key/v2/server
```

### Phase 14: Test Messaging

From Element: invite @agent0-1:agent0-1-mhs.cybertribe.com to a room and send a message.

---

## 7. BATTLE-TESTED GOTCHAS

| # | Gotcha | Fix |
|---|---|---|
| 1 | Dendrite "keyBlock is nil" | matrix_key.pem must be MATRIX PEM, not OpenSSH |
| 2 | Dendrite "missing config key" | Use connection_string: not connection: |
| 3 | MCP server 405 error | Use type: streamable-http not http |
| 4 | MCP server wont start | Entry point: dist/http-server.js not dist/index.js |
| 5 | pip/python not found | Use /opt/venv-a0/bin/pip and python3 |
| 6 | Step-CA "too many arguments" | Use --not-after=8760h (with equals) |
| 7 | Step-CA --bundle fails | Manually: cat cert root.pem > bundled.crt |
| 8 | Port 8448 not listening | Need command: ["--https-bind-address", ":8448"] |
| 9 | TLS permission denied | chown 65534:65534 on cert files |
| 10 | Host cant reach containers | mac0 bridge + promiscuous mode (already on g2s) |
| 11 | Gmail SMTP 535 | Must use 16-char App Password |
| 12 | Wrong server name in YAML | Must be agent0-1-mhs.cybertribe.com everywhere |

---

## 8. REFERENCE DOCUMENTS ON g2s

| File | Location |
|---|---|
| Multi-instance guide | /tmp/multi-instance-deploy/multi-instance-guide.md |
| Migration guide v2.0 | /tmp/multi-instance-deploy/Migration.md |
| Migration plan | /tmp/multi-instance-deploy/agent0-1-migration-plan.md |
| Working dendrite.yaml | /opt/agent-zero/agent0-2/mhs/dendrite.yaml (gold standard) |
| Working docker-compose | /opt/agent-zero/agent0-2/docker-compose.yml (reference) |
| Consolidated docs | /tmp/consolidated/ |

---

## 9. POST-MIGRATION VERIFICATION CHECKLIST

```
[ ] docker compose ps - both containers running
[ ] docker logs agent0-1-mhs - no errors
[ ] curl http://172.23.88.1/ - Agent Zero UI loads
[ ] curl http://172.23.89.1:8008/_matrix/client/versions - Dendrite responds
[ ] curl -sk https://172.23.89.1:8448/_matrix/key/v2/server - Federation
[ ] kubectl exec synapse - wget federation via VPN
[ ] MCP server on :3000 - 20 tools visible in dashboard
[ ] Matrix bot running - auto-joins, responds
[ ] SMTP test - can send email
[ ] Agent0-2 and agent0-3 unaffected
[ ] DD-WRT routes updated
```

---

## 10. ROLLBACK PLAN

1. Stop on g2s: cd /opt/agent-zero/agent0-1 && docker compose down
2. Restore DD-WRT routes to tarnover
3. Restart on tarnover: cd /opt/agent-zero/ && docker compose up -d

---

## 11. MATRIX ROOM MEMBERSHIPS (re-join after migration)

| Room | ID |
|---|---|
| Matrix test center | !NaOOusPqTqGjTpyfki:v-site.net |
| Federation Test 2 | !UNHdBMUgbildrzjKvU:v-site.net |
| smoke-test | !VAUAmLduvCOUorFrID:v-site.net |
| #agent-test | !fPBTLiXvvpmrHipVAH:v-site.net |

Invite @agent0-1:agent0-1-mhs.cybertribe.com from Element.

---

## 12. TARNOVER HOST NOTES

- Agent0-1 on tarnover is at /opt/agent-zero/ (single-instance layout)
- Tarnover also runs Step-CA (certificate authority)
- After migration keep tarnover files until fully verified
- Tarnover remains important as the CA host

---

**END OF CONTEXT BUNDLE**
