# Agent Zero Multi-Instance Deployment Guide

**Version:** 3.10 (Fleet-Ready Edition)
**Date:** 2026-03-04
**Primary Host:** g2s.cybertribe.com (128GB RAM)

---

## What's New in v3.10

| Change | Detail |
| :--- | :--- |
| **Matrix key generation** | Replaced broken `ssh-keygen` / Docker `generate-keys` with Python-based generator that creates Dendrite-native `MATRIX PRIVATE KEY` format |
| **Variable safety** | All variables pre-declared to prevent `set -u` unbound variable crashes |
| **Database syntax patch** | Auto-applies `connection_string:` fix after dendrite.yaml generation |
| **Gold standard template** | `dendrite.yaml.template` replaced with working agent0-2 config (includes `relay_api`, `room_server` blocks) |
| **Federation-ready compose** | `docker-compose.yml.template` now includes `--https-bind-address :8448` command flag and TLS cert volume mounts |
| **Self-signed TLS certs** | Script auto-generates placeholder certs so Dendrite starts cleanly; replace with step-ca certs for real federation |
| **Matrix credentials** | Auto-generates random password, stores in `.env`, prints registration command with pre-filled password |
| **Step-CA compatibility** | Documented `--not-after=8760h` (equals syntax required for Smallstep CLI v0.29.0), `--bundle` flag not supported |

---

## 1. Quick Start: Deploying a New Agent

The v3.8 script handles everything — directory creation, config generation, API key injection, and Matrix identity key generation — in a single command.

```bash
# 1. Export keys (auto-injected into .env)
export API_KEY_OPENROUTER="sk-or-v1-..."

# 2. Generate the full instance scaffold
cd /opt/agent-zero/multi-instance-deploy
./create-instance.sh 3                    # Standard agent0-3
./create-instance.sh --profile hacker 4    # Hacker-flavored agent0-4

# 3. Start the stack
cd /opt/agent-zero/agent0-3
docker compose up -d

# 4. Verify Dendrite is running clean
docker compose logs -f dendrite
# Expected: jetstream + MSC2946 warnings only, NO fatal errors
```

> **Note:** Steps 3-5 from v3.4 (manual key generation) are no longer needed.  
> The script auto-generates a valid Matrix identity key AND self-signed TLS certs.  
> Dendrite starts with federation listener on port 8448 immediately.  
> Replace self-signed certs with step-ca certs (Section 6) for real federation.

---

## 2. Available Flavors (Profiles)

| CLI Value | Profile Name | Description |
| :--- | :--- | :--- |
| `agent0` | Standard | Balanced assistant (Default) |
| `hacker` | Security | Cybersecurity & Pentesting specialist |
| `developer` | Coding | Software Engineering & Architecture specialist |
| `researcher` | Analysis | Data Analysis & Reporting specialist |

---

## 3. Help Menu & Discovery

Run `./create-instance.sh --help` at any time to see valid flavors, descriptions, port mappings, and IP patterns.

---

## 4. Zero-Touch Environment

The script automatically:
1. **Creates directory structure** — `usr/`, `mhs/`, `mhs/data/`
2. **Generates docker-compose.yml** — from template with correct IPs, MACs, ports
3. **Injects API Keys** — exported in your current shell
4. **Sets the Profile** — via `A0_SET_agent_profile` in `.env`
5. **Configures Models** — defaults to `gemini-2.0-flash-001` (Fast & Cheap)
6. **Generates dendrite.yaml** — from gold standard template with `connection_string:` safety patch
7. **Generates Matrix identity key** — native Dendrite `MATRIX PRIVATE KEY` format via Python
8. **Generates self-signed TLS certs** — placeholder certs so Dendrite starts with port 8448 listener
9. **Federation-ready compose** — `--https-bind-address :8448` command flag and TLS cert volume mounts baked in

### 4.1 Matrix Identity Key Format

Dendrite requires a proprietary PEM format — **NOT** OpenSSH or standard PKCS8:

```
-----BEGIN MATRIX PRIVATE KEY-----
Key-ID: ed25519:<random6chars>

<base64_encoded_32_byte_seed>
-----END MATRIX PRIVATE KEY-----
```

**Important:**
- `ssh-keygen -t ed25519` produces `OPENSSH PRIVATE KEY` → **REJECTED** by Dendrite (`keyBlock is nil`)
- Dendrite's own `generate-keys` tool has a chicken-and-egg problem (needs config which needs key)
- The v3.8 script uses a Python generator that creates the correct format directly
- Each instance **MUST** have a unique key — never copy keys between agents

### 4.2 Manual Key Generation (if needed)

If you ever need to regenerate a key outside the script:

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
with open('/opt/agent-zero/agent0-N/mhs/matrix_key.pem', 'w') as f:
    f.write(chr(10).join(lines) + chr(10))
print('Key generated: ed25519:' + key_id)
"
chmod 600 /opt/agent-zero/agent0-N/mhs/matrix_key.pem
```

---

## 5. Post-Deploy: Federation Setup (The "Passport" Steps)

After `create-instance.sh` and `docker compose up -d`, federation requires TLS certificates and gateway registration.

### 5.1 Register Matrix Account

The `create-instance.sh` script auto-generates a random password and prints the exact registration command. After `docker compose up -d`, run it:

```bash
docker exec -it agent0-N-mhs /usr/bin/create-account \
  -config /etc/dendrite/dendrite.yaml \
  -username agent0-N -password <auto-generated-password> -admin
```

The password is stored in `/opt/agent-zero/agent0-N/.env` as `MATRIX_PASSWORD`.
The returned `AccessToken` should also be saved to `.env` as `MATRIX_ACCESS_TOKEN` for the MCP server.

### 5.2 TLS Transport (The Secure Envelope)

The `create-instance.sh` script generates **self-signed placeholder certificates** so Dendrite can start immediately with the federation listener on port 8448. However, real federation with Synapse requires trusted certificates from your `step-ca` infrastructure.

**To upgrade from self-signed to step-ca certs:**

1. **Generate**: Request a certificate for `agent0-N-mhs.cybertribe.com` (see Section 6)
2. **Deploy**: Overwrite `server.crt` and `server.key` inside the `mhs/` directory
3. **Permissions**: `chmod 600 server.key`
4. **Restart**: `docker compose restart dendrite`
5. **Verify**: `curl -k https://172.23.89.N:8448/_matrix/key/v2/server`

### 5.3 Synapse Gateway Whitelisting

Your central Synapse hub (v-site.net) must trust the new node:

1. **Whitelist**: Add the new FQDN to the `federation_domain_whitelist` in Synapse config
2. **DNS/HostAlias**: Ensure Synapse knows that `agent0-N-mhs.cybertribe.com` resolves to your g2s VPN IP

### 5.4 Deploy Matrix MCP Server (Outbound Matrix Tools)

The matrix-mcp-server is a Node.js application that gives the agent Matrix
capabilities (send messages, list rooms, manage invites, etc.) via the Model
Context Protocol. It is **automatically deployed** by `create-instance.sh` v3.11+.

#### What create-instance.sh does automatically

- Copies the `matrix-mcp-server` template from `templates/matrix-mcp-server/`
  into the instance's `usr/workdir/matrix-mcp-server/`
- Generates a configured `.env` from `.env.template` with instance-specific
  homeserver URL, user ID, and domain
- Sets `MATRIX_ACCESS_TOKEN=PENDING_REGISTRATION` (updated after Step 5.1)

#### Post-deployment steps

##### Step 1: Update the access token

After registering the Matrix account (Step 5.1), update the token:
```bash
# Replace PENDING_REGISTRATION with the actual token from create-account output
sed -i 's/PENDING_REGISTRATION/<actual_access_token>/' \
  /opt/agent-zero/agent0-N/usr/workdir/matrix-mcp-server/.env
```

##### Step 2: Install dependencies and start (first time)
```bash
docker exec -it agent0-N bash
cd /a0/usr/workdir/matrix-mcp-server
npm install
node dist/http-server.js &

# Verify it is listening
curl -s http://localhost:3000/mcp | head -c 200
```

##### Step 3: Configure in Agent Zero UI

1. Open the Agent Zero dashboard at `http://agent0-N.cybertribe.com/`
2. Click **Settings** (gear icon) in the left sidebar
3. Click the **MCP/A2A** tab
4. In the JSON editor, **replace** the empty `{}` with:

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

> **Note:** No headers or credentials are needed in this JSON. The MCP server
> reads all Matrix credentials from its own `.env` file (configured in Step 1).

5. Click **Save**
6. The agent should now show ~20 Matrix tools in its tool list

#### MCP/A2A JSON Field Reference

| JSON Field | Value | Notes |
| :--- | :--- | :--- |
| `type` | `"streamable-http"` | Required — must be `streamable-http`, NOT `http` or `sse` |
| `url` | `http://localhost:3000/mcp` | MCP server runs inside the agent container |
| `description` | Free text | Optional description shown in the UI |

#### Verification

Ask the agent in the chat: *"What is your Matrix identity?"*
The agent should respond with `@agent0-N:agent0-N-mhs.cybertribe.com`.

---

### 5.5 Deploy Matrix Bot (Inbound Message Routing)

The matrix-bot is a Python application that listens on Matrix rooms for incoming
messages and routes them through the Agent Zero API for intelligent responses.
This enables humans and other agents to communicate with the agent via any Matrix
client (Element, FluffyChat, etc.). It is **automatically deployed** by
`create-instance.sh` v3.11+.

#### How it works

1. The bot connects to the agent's Dendrite homeserver using `matrix-nio`
2. When invited to a room, it auto-joins
3. When a message arrives, it forwards it to the Agent Zero `/api_message` endpoint
4. The agent's response is posted back into the Matrix room
5. Each room gets its own Agent Zero conversation context (stored in `room_contexts.json`)

#### What create-instance.sh does automatically

- Copies the `matrix-bot` template from `templates/matrix-bot/` into the
  instance's `usr/workdir/matrix-bot/`
- Generates a configured `.env` from `.env.template` with instance-specific
  homeserver URL, user ID, display name, and API key
- Sets `MATRIX_ACCESS_TOKEN=PENDING_REGISTRATION` (updated after Step 5.1)

#### Post-deployment steps

##### Step 1: Update the access token

After registering the Matrix account (Step 5.1), update the token:
```bash
sed -i 's/PENDING_REGISTRATION/<actual_access_token>/' \
  /opt/agent-zero/agent0-N/usr/workdir/matrix-bot/.env
```

##### Step 2: Install dependencies and start (first time)
```bash
docker exec -it agent0-N bash
cd /a0/usr/workdir/matrix-bot
/opt/venv-a0/bin/pip install -r requirements.txt
/opt/venv-a0/bin/python3 matrix_bot.py &

# Check the log
tail -f bot.log
```

##### Step 3: Test from Element

1. Open Element (or any Matrix client) connected to `matrix.v-site.net`
2. Start a new direct message with `@agent0-N:agent0-N-mhs.cybertribe.com`
3. Send a message — the bot should auto-join and respond via Agent Zero

#### Matrix Bot `.env` Reference

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `MATRIX_HOMESERVER_URL` | `http://agent0-N-mhs:8008` | Dendrite client API (Docker DNS) |
| `MATRIX_USER_ID` | `@agent0-N:agent0-N-mhs.cybertribe.com` | Bot's Matrix identity |
| `MATRIX_ACCESS_TOKEN` | Token string | From `create-account` (Step 5.1) |
| `MATRIX_DEVICE_ID` | `AgentZeroBot` | Device identifier for sync |
| `A0_API_URL` | `http://localhost:80/api_message` | Agent Zero API endpoint |
| `A0_API_KEY` | Auto-generated | API key for Agent Zero authentication |
| `BOT_DISPLAY_NAME` | `Agent0-N` | Display name in Matrix rooms |
| `TRIGGER_PREFIX` | (empty) | Optional prefix to filter messages |
| `SYNC_TIMEOUT_MS` | `30000` | Matrix sync polling interval |

#### Verification

From Element, invite `@agent0-N:agent0-N-mhs.cybertribe.com` to a room and send
a message. You should see the bot join and respond within a few seconds.



### 5.6 Email (SMTP) Configuration (Optional)

Agent Zero can send emails via Gmail SMTP. This requires a Google account with
2-Step Verification and an App Password.

#### Prerequisites

- A Gmail account with **2-Step Verification** enabled
- A **16-character App Password** (not the regular account password)
  - Generate at: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
  - Select: Mail > Other > name it "Agent0-N"

> **Regular Gmail passwords will NOT work.** SMTP login requires an App Password.
> The error `535 5.7.8 Username and Password not accepted` always means wrong
> credentials or missing App Password.

#### Configuration

Append the following to the matrix-bot `.env` file at
`/opt/agent-zero/agent0-N/usr/workdir/matrix-bot/.env`:

```env
# Sync timeout in milliseconds
SYNC_TIMEOUT_MS=30000
# Gmail SMTP configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<gmail-address>@gmail.com
SMTP_PASS=<16-char-app-password-no-spaces>
SMTP_FROM=<gmail-address>@gmail.com
FORCE_TLS=true
```

| Variable | Value | Notes |
|----------|-------|-------|
| SMTP_HOST | smtp.gmail.com | Gmail SMTP server |
| SMTP_PORT | 587 | STARTTLS port |
| SMTP_USER | your-agent@gmail.com | Gmail address |
| SMTP_PASS | 16-char App Password | **No spaces** - remove spaces from the displayed format |
| SMTP_FROM | your-agent@gmail.com | Usually same as SMTP_USER |
| FORCE_TLS | true | Enforce TLS encryption |
| SYNC_TIMEOUT_MS | 30000 | Bot sync timeout (optional) |

After updating `.env`, restart the matrix-bot:

```bash
docker exec agent0-N bash -c 'pkill -f matrix_bot.py; sleep 2; cd /a0/usr/workdir/matrix-bot && nohup /opt/venv-a0/bin/python3 matrix_bot.py > bot.log 2>&1 &'
```

#### Verification

Test SMTP from inside the agent container:

```bash
docker exec agent0-N /opt/venv-a0/bin/python3 << 'TEST'
import smtplib
from email.mime.text import MIMEText
server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
server.starttls()
server.login("<gmail-address>@gmail.com", "<app-password-no-spaces>")
msg = MIMEText("SMTP test from Agent0-N")
msg["Subject"] = "Agent0-N SMTP Test"
msg["From"] = "<gmail-address>@gmail.com"
msg["To"] = "<your-email>@gmail.com"
server.sendmail(msg["From"], msg["To"], msg.as_string())
server.quit()
print("SUCCESS: Email sent!")
TEST
```

> **Note:** Use `/opt/venv-a0/bin/python3` - bare `python3` resolves to the
> system Python which lacks required packages.


## 6. Step-CA Certificate Procedures (on Tarnover)

Since the CA lives on **Tarnover**, you must run these commands there to generate the TLS layer for your nodes on g2s.

> **Important:** Smallstep CLI v0.29.0 quirks:
> - The `--not-after` flag requires equals syntax: `--not-after=8760h` (space-separated causes "too many positional arguments" error)
> - The `--bundle` flag is NOT supported in this version despite being documented
> - Use the two-step approach below to bundle the CA chain

### 6.1 Generate Node Certificate
```bash
# Run on Tarnover (note the = syntax for --not-after)
step ca certificate "agent0-N-mhs.cybertribe.com" server.crt server.key --not-after=8760h
```

You will be prompted for the provisioner password.

### 6.2 Bundle the CA Chain
Synapse requires the full chain (leaf + intermediate + root). Append your `ca-bundle.pem`:
```bash
cat ca-bundle.pem >> server.crt
```

Verify the chain contains multiple certs:
```bash
openssl crl2pkcs7 -nocrl -certfile server.crt | openssl pkcs7 -print_certs -noout
```

### 6.3 Deploy to g2s
```bash
scp server.crt server.key g2s:/opt/agent-zero/agent0-N/mhs/
```

### 6.4 File Permissions & Restart (on g2s)
```bash
chmod 600 /opt/agent-zero/agent0-N/mhs/server.key
cd /opt/agent-zero/agent0-N && docker compose down && docker compose up -d
```

### 6.5 Verify Federation Locally
```bash
docker exec agent0-N-mhs wget -qO- --no-check-certificate https://localhost:8448/_matrix/key/v2/server
```

### 6.6 Verify Federation from Synapse Gateway

The Synapse pod requires `hostAliases` to resolve agent homeserver hostnames over the VPN tunnel.

**Check current hostAliases:**
```bash
kubectl get deployment -n matrix matrix-synapse -o jsonpath='{.spec.template.spec.hostAliases}' | python3 -m json.tool
```

**Patch to add missing agents (can pre-populate slots 3-5 in one shot):**
```bash
kubectl patch deployment -n matrix matrix-synapse --type=json -p '[
  {"op": "add", "path": "/spec/template/spec/hostAliases/-", "value": {"ip": "172.23.89.3", "hostnames": ["agent0-3-mhs.cybertribe.com"]}},
  {"op": "add", "path": "/spec/template/spec/hostAliases/-", "value": {"ip": "172.23.89.4", "hostnames": ["agent0-4-mhs.cybertribe.com"]}},
  {"op": "add", "path": "/spec/template/spec/hostAliases/-", "value": {"ip": "172.23.89.5", "hostnames": ["agent0-5-mhs.cybertribe.com"]}}]'
```

> **Note:** This triggers a rolling pod restart. Wait for the new pod before testing.

**Test from the openvpn sidecar** (the `matrix` container does NOT have `wget`):
```bash
kubectl exec -it -n matrix <synapse-pod> -c openvpn -- wget -qO- --no-check-certificate https://agent0-N-mhs.cybertribe.com:8448/_matrix/key/v2/server
```

**Also verify the federation whitelist** includes the agent domain:
```bash
kubectl exec -it -n matrix <synapse-pod> -c matrix -- cat /data/homeserver.yaml | grep -A20 federation_domain_whitelist
```

---

## 7. Host Infrastructure Setup (One-Time per Server)

Before deploying any containers on **g2s**, the host networking must be configured to allow 'macvlan' traffic to reach the physical network through `eno1`.

### 7.1 Permanent Bridge Service (Systemd)
Instead of manual `ip link` commands, use the `agent-bridge.service` to survive reboots:

```bash
cat << 'EOF' | sudo tee /etc/systemd/system/agent-bridge.service
[Unit]
Description=Agent-Matrix Host Bridge (mac0)
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/bash -c "\
  ip link set eno1 promisc on && \
  ip link add mac0 link eno1 type macvlan mode bridge || true && \
  ip addr add 172.23.88.254/32 dev mac0 || true && \
  ip link set mac0 up && \
  ip route add 172.23.88.0/24 dev mac0 || true && \
  ip route add 172.23.89.0/24 dev mac0 || true"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now agent-bridge.service
```

---

## 8. Router Configuration (kama.cybertribe.com)

The DD-WRT router must be aware of the new MAC addresses to correctly assign IPs and provide internal DNS resolution.

### 8.1 Static Leases (Services -> Services)
For each new instance **N**, add two entries in the Static Leases table:

| Device Name | MAC Address | IP Address | Hostname |
| :--- | :--- | :--- | :--- |
| agent0-N | 02:42:AC:17:58:0N | 172.23.88.N | agent0-N.cybertribe.com |
| agent0-N-mhs | 02:42:AC:17:59:0N | 172.23.89.N | agent0-N-mhs.cybertribe.com |

### 8.2 Internal DNS (Services -> DNSMasq)
To ensure full-mesh resolution, add these local DNS entries to the DNSMasq box if they aren't auto-populated by the leases:
```text
address=/agent0-N.cybertribe.com/172.23.88.N
address=/agent0-N-mhs.cybertribe.com/172.23.89.N
```

---

## 9. Fleet Registry

| Instance | Host | Agent IP | MHS IP | Profile | Federation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| agent0-1 | tarnover | 172.23.88.1 | 172.23.89.1 | standard | TBD | Legacy |
| agent0-2 | g2s | 172.23.88.2 | 172.23.89.2 | standard | ✅ Verified | Sovereign |
| agent0-3 | g2s | 172.23.88.3 | 172.23.89.3 | standard | ✅ Verified | Sovereign |
| agent0-4 | g2s | 172.23.88.4 | 172.23.89.4 | — | Pre-wired | Available |
| agent0-5 | g2s | 172.23.88.5 | 172.23.89.5 | — | Pre-wired | Available |

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `keyBlock is nil` | Wrong key format (OpenSSH instead of MATRIX PRIVATE KEY) | Regenerate with Python generator (Section 4.2) |
| `unbound variable` | Script variable used before declaration | Ensure all vars initialized at top of script |
| `connection: unsupported` | Old `connection:` key in dendrite.yaml | Run `sed -i 's/connection:/connection_string:/g'` on the file |
| Missing `relay_api` / `room_server` | Outdated dendrite.yaml.template | Replace template with gold standard from agent0-2 |
| Port 8448 unreachable | No TLS listener configured | Add `--https-bind-address :8448` to docker-compose command + mount certs |
| Container can't read key | Permission mismatch | `chmod 600` + `chown 1000:1000` on matrix_key.pem |

---

## Bot Display Names (Matrix Aliases)

Matrix bots can have custom display names ("aliases") that show up in Element rooms next to their messages.

### Configuration

Set in your `.env` file:
```bash
BOT_DISPLAY_NAME=My Awesome Bot    # Shows as "My Awesome Bot" in all rooms
AGENT_IDENTITY=Agent Zero          # Used in system prompts
```

The bot automatically sets this name on startup.

### Runtime Changes

Use the `set_display_name.py` utility to change names without restarting:

```bash
# Set global display name (all rooms)
python3 set_display_name.py "New Name"

# Set per-room display name
python3 set_display_name.py "Room Helper" --room '!roomid:server.com'

# Reset to default
python3 set_display_name.py --reset

# Show configuration
python3 set_display_name.py --list
```

### Technical Details

| Method | Scope | API Call |
|--------|-------|----------|
| Global | All rooms | `client.set_displayname()` |
| Per-room | Specific room | `client.room_put_state(m.room.member)` |

