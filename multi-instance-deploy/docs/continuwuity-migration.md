# Continuwuity Migration Guide

**Version:** 1.0
**Date:** March 2026
**Scope:** Migration from Dendrite v0.15.2 to Continuwuity v0.5.6

---

## 1. Why Migrate

| Concern | Dendrite v0.15.2 | Continuwuity v0.5.6 |
|---------|-----------------|---------------------|
| Development status | Stalled since Aug 2025, no updates | Active development (Conduit/Conduwuit fork) |
| Language | Go | Rust |
| Database | SQLite (file-based, multiple .db files) | RocksDB (embedded, single data dir) |
| Memory usage | ~200-400MB | ~20-50MB |
| Known issues | DAG corruption, sync freezes, federation timeouts | Stable federation, clean sync |
| Config format | YAML file (dendrite.yaml) | Environment variables (CONTINUWUITY_ prefix) |
| Account creation | `create-account` binary inside container | REST API with one-time registration token |
| TLS for federation | Built-in `--https-bind-address :8448` | Caddy sidecar for TLS termination |

---

## 2. Architecture Change

### Before (Dendrite)
```
Per instance: 2 containers
  agent0-N         → Agent Zero (172.23.88.N)
  agent0-N-mhs     → Dendrite monolith (172.23.89.N)
                      Port 8008: Client API (HTTP)
                      Port 8448: Federation API (HTTPS, built-in TLS)
```

### After (Continuwuity)
```
Per instance: 3 containers
  agent0-N              → Agent Zero (172.23.88.N)
  agent0-N-continuwuity → Continuwuity homeserver (bridge-local only, port 6167)
  agent0-N-mhs          → Caddy reverse proxy (172.23.89.N)
                            Port 8008: Client API → proxied to continuwuity:6167
                            Port 8448: Federation API → TLS termination → continuwuity:6167
```

**Key difference:** Continuwuity does not handle TLS itself. Caddy sits in front, holding the macvlan IP and step-ca certificates. The Continuwuity container is on bridge-local only (not LAN-routable).

---

## 3. Migration Procedure

### 3.1 Prerequisites

- `create-instance.sh` v4.0+ on g2s
- Existing step-ca TLS certs for the instance (server.crt, server.key)
- Access tokens for MCP server and bot will need regeneration

### 3.2 Stop Existing Dendrite Instance

```bash
cd /opt/agent-zero/agent0-N
docker compose down
```

### 3.3 Archive Dendrite Data

```bash
# Backup old compose and data
cp docker-compose.yml docker-compose.yml.dendrite-backup
mv mhs/data mhs/data-dendrite-archive-$(date +%Y%m%d)
```

### 3.4 Deploy Continuwuity Stack

For a fresh instance, use `create-instance.sh`:
```bash
cd /opt/agent-zero/multi-instance-deploy
./create-instance.sh --profile <flavor> N
```

For an existing instance (preserving /usr/ data), replace only the compose and MHS config:

```bash
# Copy new compose template (from create-instance.sh v4.0 output or templates)
# Key elements in docker-compose.yml:
#   - continuwuity service (ghcr.io/continuwuity/continuwuity:latest)
#   - caddy service (caddy:2-alpine) with macvlan IP
#   - Caddyfile in mhs/
#   - continuwuity-data/ directory for RocksDB

mkdir -p mhs/continuwuity-data

# Generate Caddyfile
cat > mhs/Caddyfile << 'EOF'
:8008 {
    reverse_proxy agent0-N-continuwuity:6167
}

:8448 {
    tls /etc/caddy/server.crt /etc/caddy/server.key
    reverse_proxy agent0-N-continuwuity:6167
}
EOF
```

### 3.5 Start the Stack

```bash
cd /opt/agent-zero/agent0-N
docker compose up -d
```

Verify three containers are running:
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep agent0-N
# agent0-N              Up
# agent0-N-continuwuity Up
# agent0-N-mhs          Up
```

### 3.6 Register Matrix Account

**Step 1:** Get the registration token from the compose file or container env:
```bash
grep CONTINUWUITY_REGISTRATION_TOKEN /opt/agent-zero/agent0-N/docker-compose.yml
```

**Step 2:** Register via REST API:
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

### 3.7 Update Service Credentials

Update the access token in both MCP server and bot `.env` files:

```bash
docker exec agent0-N bash -c "
  sed -i 's|MATRIX_ACCESS_TOKEN=.*|MATRIX_ACCESS_TOKEN=<new-token>|' \
    /a0/usr/workdir/matrix-mcp-server/.env \
    /a0/usr/workdir/matrix-bot/.env
"
```

Restart internal services:
```bash
docker exec agent0-N bash /a0/usr/workdir/startup-services.sh
```

### 3.8 Verify Federation

```bash
# Client API
curl -s http://172.23.89.N:8008/_matrix/client/versions

# Federation (TLS via Caddy)
curl -sk https://172.23.89.N:8448/_matrix/key/v2/server
```

### 3.9 Re-establish Room Membership

Continuwuity starts with a fresh database — no room state is preserved from Dendrite. You must:

1. **Kick the old identity** from existing rooms (if the Matrix ID is the same, the room server may have stale state)
2. **Re-invite** the agent to all rooms
3. The bot will auto-join on invite

---

## 4. Gotchas

| Issue | Detail | Fix |
|-------|--------|-----|
| New access tokens required | Dendrite tokens don't carry over | Re-register account, update all .env files |
| Room membership lost | Clean-slate RocksDB has no room history | Kick old identity, re-invite agent |
| `AGENT_IDENTITY` env var | Bot needs identity context for correct persona | Verify `AGENT_IDENTITY=Agent0-N` in bot .env |
| Container name change | Homeserver container is now `agent0-N-continuwuity`, Caddy is `agent0-N-mhs` | Update monitoring/scripts referencing old container names |
| No YAML config | Continuwuity uses `CONTINUWUITY_` env vars in compose | Don't look for dendrite.yaml — it doesn't exist |
| Internal admin bot | Continuwuity has `@conduit:` admin bot (Conduit heritage) | Ignore — doesn't affect agent operation |
| Data directory | Changed from `mhs/data/` to `mhs/continuwuity-data/` | Ensure volume mounts point to new path |

---

## 5. Rollback

If migration fails:

```bash
# Stop Continuwuity stack
cd /opt/agent-zero/agent0-N
docker compose down

# Restore Dendrite compose
cp docker-compose.yml.dendrite-backup docker-compose.yml

# Restore data
mv mhs/data-dendrite-archive-* mhs/data

# Start Dendrite
docker compose up -d
```

---

## 6. Migration Status

| Instance | From | To | Date | Status |
|----------|------|----|------|--------|
| agent0-1 | Dendrite v0.15.2 | Continuwuity v0.5.6 | 2026-03-09 | ✅ Complete |
| agent0-4 | Dendrite v0.15.2 | Continuwuity v0.5.6 | 2026-03-08 | ✅ Complete |
| agent0-2 | Dendrite v0.15.2 | — | — | Pending |
| agent0-3 | Dendrite v0.15.2 | — | — | Pending |

---

*Last updated: March 2026*
