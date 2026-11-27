# Agent0-1 Migration Plan: Tarnover → g2s

**Status:** PLANNED — NOT YET SCHEDULED  
**Created:** 2026-03-05  
**Reference:** Migration.md v2.0 (detailed technical procedures)  
**Estimated Duration:** ~80 minutes  

---

## 1. Current State

| Property | Value |
|---|---|
| Host | tarnover |
| Agent IP | 172.23.88.1 |
| MHS IP | 172.23.89.1 |
| Matrix ID | `@agent:agent0-1-mhs.cybertribe.com` |
| Federation | ❌ Not configured (port 8448 TLS missing) |
| MCP Server | ✅ Running (since Feb 28) |
| Bot | ✅ Running |
| SMTP | ✅ Configured (agent0.1.vsite@gmail.com) |
| Role | Primary orchestrator / project builder |

---

## 2. Key Decisions

| Decision | Options | Recommendation | Status |
|---|---|---|---|
| **Matrix identity** | Keep `@agent` or rename to `@agent0-1` | Rename to `@agent0-1` for fleet consistency | PENDING |
| **Matrix key** | Preserve or regenerate | **Regenerate** — new identity, clean federation start | PENDING |
| **TLS certs** | Generate from step-ca on tarnover | Yes — enables federation (currently broken) | PENDING |
| **IP slot** | 172.23.88.1 / 172.23.89.1 (reserved) | Keep — already in DNS and routing tables | CONFIRMED |
| **Use create-instance.sh?** | Yes or manual | **No** — use Migration.md v2.0 to preserve data | CONFIRMED |
| **Tarnover decommission** | Immediate or phased | Phased — keep tarnover available as fallback | PENDING |

---

## 3. Data to Preserve

| Data | Source Path (in container) | Priority | Notes |
|---|---|---|---|
| Agent settings | `/a0/usr/settings.json` | 🔴 Critical | API keys, model config |
| Memory & knowledge | `/a0/usr/projects/agent-matrix/.a0proj/memory/` | 🔴 Critical | FAISS index + embeddings |
| Project files | `/a0/usr/projects/agent-matrix/` | 🔴 Critical | All docs, scripts, templates |
| Chat history | `/a0/usr/chats/` | 🟡 Important | Current conversations |
| Workdir (MCP + bot) | `/a0/usr/workdir/` | 🟡 Important | Templates exist on g2s |
| `.env` (auth + SMTP) | `/a0/usr/.env` | 🔴 Critical | AUTH_LOGIN, AUTH_PASSWORD, API keys |
| MCP server `.env` | `/a0/usr/workdir/matrix-mcp-server/.env` | 🔴 Critical | Matrix access token |
| Bot `.env` | `/a0/usr/workdir/matrix-bot/.env` | 🔴 Critical | SMTP credentials |
| Uploads | `/a0/usr/uploads/` | 🟡 Important | Screenshots, attachments |

---

## 4. Pre-Migration Checklist

```
[ ] 1. Agent0-3 verified as backup orchestrator (can handle tasks independently)
[ ] 2. Full backup: tar czf /tmp/agent0-1-backup.tar.gz -C /a0/usr .
[ ] 3. Transfer backup to g2s: scp to /opt/agent-zero/agent0-1/
[ ] 4. Step-CA TLS certs generated for agent0-1-mhs.cybertribe.com
        step ca certificate agent0-1-mhs.cybertribe.com server.crt server.key \
          --ca-url https://tarnover.cybertribe.com:9443 \
          --not-after=8760h
        cat server.crt intermediate_ca.crt > server.crt  (if --bundle fails)
[ ] 5. Instance directory prepared on g2s: /opt/agent-zero/agent0-1/
[ ] 6. docker-compose.yml created manually (NOT via create-instance.sh)
[ ] 7. dendrite.yaml prepared with connection_string syntax (not connection:)
[ ] 8. New matrix_key.pem generated (Python one-liner, NOT ssh-keygen)
[ ] 9. Synapse hostAliases verified for 172.23.89.1 (already pre-wired)
[ ] 10. DD-WRT routes: change .88.1/.89.1 from tarnover to g2s IP
[ ] 11. Document all Matrix room IDs for re-joining
```

---

## 5. Execution Sequence

### Phase 1: Backup (on tarnover)
```bash
# Inside agent0-1 container on tarnover
tar czf /tmp/agent0-1-usr-backup.tar.gz -C /a0/usr .

# From tarnover host
docker cp agent0-1:/tmp/agent0-1-usr-backup.tar.gz /tmp/
scp /tmp/agent0-1-usr-backup.tar.gz l0r3zz@g2s.cybertribe.com:/tmp/
```

### Phase 2: Scaffold (on g2s)
```bash
# Create instance directory structure manually
mkdir -p /opt/agent-zero/agent0-1/{usr,mhs}

# Extract backup
tar xzf /tmp/agent0-1-usr-backup.tar.gz -C /opt/agent-zero/agent0-1/usr/

# Create docker-compose.yml from template (edit for N=1)
# Create dendrite.yaml from working agent0-2 config (change server_name)
# Generate matrix_key.pem via Python one-liner
# Copy TLS certs to mhs/
```

### Phase 3: Configure
```bash
# Update .env files with correct paths/credentials
# Register new Matrix account: @agent0-1:agent0-1-mhs.cybertribe.com
# Deploy matrix-mcp-server and matrix-bot from golden templates
# Update MCP .env with new access token
```

### Phase 4: Launch & Verify
```bash
cd /opt/agent-zero/agent0-1
docker compose up -d

# Verify
curl http://172.23.88.1/          # Agent Zero UI
curl http://172.23.89.1:8008/_matrix/client/versions  # Dendrite CS API
curl -k https://172.23.89.1:8448/_matrix/key/v2/server  # Federation
```

### Phase 5: Cutover
```bash
# Update DD-WRT routes
ip route del 172.23.88.1/32 via <tarnover-ip>
ip route add 172.23.88.1/32 via 172.23.100.121  # g2s
ip route del 172.23.89.1/32 via <tarnover-ip>
ip route add 172.23.89.1/32 via 172.23.100.121  # g2s

# Re-join Matrix rooms
# Test federation end-to-end
# Test MCP tools + bot
# Test SMTP
```

### Phase 6: Decommission (tarnover)
```bash
# On tarnover — only after g2s instance fully verified
docker compose -f /opt/agent-zero/agent0-1/docker-compose.yml down
# Keep backup for 7 days minimum
```

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Primary agent offline during migration | No orchestrator | Verify agent0-3 can handle tasks beforehand |
| Matrix room memberships lost | Need re-invites | Document all room IDs pre-migration |
| Memory/knowledge corruption | Agent loses context | Verify backup integrity; keep tarnover as fallback |
| DNS propagation delay | Briefly unreachable | Update DD-WRT routes + DNS simultaneously |
| New Matrix identity rejected | Can't federate | Test federation before cutover; keep old identity as fallback |
| SMTP credentials invalidated | Can't send email | Verify .env transferred correctly; test before cutover |

---

## 7. Time Estimates

| Phase | Duration |
|---|---|
| Pre-migration prep + checklist | ~30 min |
| Backup + transfer | ~10 min |
| Instance scaffold + config | ~20 min |
| Launch + verify | ~15 min |
| DNS/route cutover | ~5 min |
| **Total** | **~80 min** |

---

## 8. Post-Migration Verification

```
[ ] Agent Zero UI accessible at http://agent0-1.cybertribe.com/
[ ] Dendrite CS API responding on :8008
[ ] Federation endpoint responding on :8448
[ ] Matrix MCP server: 20 tools visible in dashboard
[ ] Matrix bot: syncing and auto-joining rooms
[ ] SMTP: test email sends successfully
[ ] Memory: agent recalls previous conversations
[ ] All Matrix rooms re-joined
[ ] Federation verified from Synapse pod
[ ] Tarnover containers stopped
```

---

*This plan follows Migration.md v2.0 procedures. Do NOT use create-instance.sh — it generates new identities and overwrites data.*
