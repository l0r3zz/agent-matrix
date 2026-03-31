# Open Brain in Agent-Matrix: Collective Memory Architecture

**Companion Document:** [open-brain-agent-zero-guide.md](open-brain-agent-zero-guide.md)  
**Date:** March 2026  
**Status:** Deployed on g2s services segment (172.23.90.0/24)

---

## 1. Vision: The Collective Unconscious

Carl Jung described the collective unconscious as a layer of the psyche shared by all humans -- not personal experience, but inherited mental structures (archetypes) that shape how we perceive and respond to the world. Every individual also has a personal unconscious: their own memories, repressions, and learned behaviors. The two layers are complementary. The personal unconscious is shaped by lived experience; the collective unconscious provides a foundation of shared patterns that new minds inherit without having to learn them from scratch.

This maps directly onto the agent-matrix deployment.

The Cybertribe lab runs five Agent Zero instances (agent0-1 through agent0-5), each with its own local vector memory -- its personal unconscious. Each agent accumulates conversation histories, task-specific learnings, project memories, and knowledge base entries. But that knowledge is siloed. Agent0-1 cannot search agent0-3's memory. If agent0-1's container is destroyed, its accumulated wisdom dies with it.

Open Brain provides the collective unconscious -- a shared PostgreSQL + pgvector knowledge store that every agent in the fleet can read from and write to. Organizational knowledge that transcends any single agent's experience.

This Youtube video [Is "Agent Zero" the Secret Key to Achieving AGI?](https://www.youtube.com/watch?v=B2FodNIDZDk) captures the broader pattern:

> "We are shifting from building single all-knowing oracles to designing collaborative ecosystems of specialized intelligence."

And:

> "Lateral communication between specialized agents creates a collaborative panel of experts, not a single oracle."

Agent-Matrix already provides the lateral communication layer via Matrix rooms -- agents talk to each other and to humans in real time. Open Brain adds the persistent, asynchronous dimension. Agents can not only converse; they can build and query a shared body of organizational knowledge that outlives any individual conversation or container.

**The Gandalf scenario.** Agent0-1 (Gandalf) has participated in months of agent-matrix development. Its local memory contains hard-won knowledge:

- How to debug Docker macvlan networking when containers lose LAN connectivity
- The exact steps for Continuwuity-to-Synapse federation troubleshooting
- TLS certificate renewal procedures with step-ca (the equals-syntax gotcha in `--not-after=8760h`)
- How to configure DD-WRT static routes for new agent instances
- Migration procedures from Dendrite to Continuwuity
- The DHCP Option 121 trap where `systemd-networkd` ignores Option 3

Without Open Brain, this knowledge is locked in Gandalf's personal memory. If Gandalf's container is destroyed, it is gone. Other agents cannot access it.

With Open Brain, Gandalf (or a human operator) promotes key learnings to the collective store. When agent0-6 is provisioned, it connects to Open Brain and can immediately search "how do I troubleshoot federation with Synapse?" and get Gandalf's hard-won knowledge -- without Gandalf being online, without anyone repeating the debugging process.

### Memory Layers

The agent-matrix memory architecture has three distinct layers:

```
┌─────────────────────────────────────────────┐
│  Context Window (Ephemeral)                 │  <-- Current conversation
├─────────────────────────────────────────────┤
│  Agent Zero Local Memory (Per-Agent)        │  <-- Personal unconscious
│  - Conversation history                     │
│  - Task-specific learnings                  │
│  - Project memory                           │
│  - Knowledge base entries                   │
├─────────────────────────────────────────────┤
│  Open Brain Collective Store (Shared)       │  <-- Collective unconscious
│  - Organizational knowledge                 │
│  - Cross-agent learnings                    │
│  - Best practices and patterns              │
│  - Incident post-mortems                    │
│  - Architectural decisions                  │
└─────────────────────────────────────────────┘
```

Each layer serves a different purpose, with different lifetimes and access scopes:

| Layer | Scope | Lifetime | Volume | Access |
|-------|-------|----------|--------|--------|
| Context window | Single conversation | Ephemeral | High | Current agent only |
| Agent Zero local memory | Single agent | Persistent (container lifetime) | Medium | Owning agent only |
| Open Brain collective store | All agents + humans | Persistent (database lifetime) | Curated | Any connected client |

---

## 2. Architecture on g2s

Open Brain deploys on the **172.23.90.0/24 services segment** -- a dedicated subnet for shared infrastructure, separate from the agent containers (172.23.88.0/24) and Matrix homeserver proxies (172.23.89.0/24).

```
  172.23.88.x (agents)         172.23.90.0/24 (services segment)
  ┌──────────────┐             ┌────────────────────────────────────┐
  │ agent0-1 .1  │             │  g2s Docker                        │
  │ agent0-2 .2  │◄──macvlan──►│                                    │
  │ agent0-3 .3  │             │  open-brain-mcp  172.23.90.2:3100  │
  │ agent0-4 .4  │             │  (Node.js/Express MCP server)      │
  │ agent0-5 .5  │             │       │ brain-net (bridge)          │
  └──────────────┘             │       ▼                            │
                               │  open-brain-db   172.23.90.1:5432  │
  172.23.89.x (MHS)            │  (PostgreSQL 16 + pgvector)        │
  ┌──────────────┐             └────────────────────────────────────┘
  │ agent0-N-mhs │                      │
  └──────────────┘                      ▼
                               OpenRouter API (external)
  172.23.0.0/16 (LAN)         - Embeddings (text-embedding-3-small)
  ┌──────────────┐            - Metadata extraction (gpt-4o-mini)
  │ workstations │
  │ (via DD-WRT  │──── routes 172.23.90.0/24 via g2s 172.23.100.121
  │  static rte) │
  └──────────────┘
```

### Network Segments

| Segment | CIDR | Purpose |
|---------|------|---------|
| Agent containers | 172.23.88.0/24 | Agent Zero instances |
| MHS containers | 172.23.89.0/24 | Caddy TLS proxies |
| Services segment | 172.23.90.0/24 | Open Brain DB + MCP server |

### Container Details

| Container | IP | MAC | Networks | Port |
|-----------|-----|-----|----------|------|
| open-brain-db | 172.23.90.1 | 02:42:AC:17:5A:01 | macvlan-172-23 + brain-net | 5432 |
| open-brain-mcp | 172.23.90.2 | 02:42:AC:17:5A:02 | macvlan-172-23 + brain-net | 3100 |

Both containers sit on the existing `macvlan-172-23` network (which covers the full 172.23.0.0/16 supernet), giving each a first-class LAN IP. They also share a private `brain-net` bridge so the MCP server can resolve the DB by Docker hostname (`open-brain-db`). No Docker port-mapping is needed -- external clients connect directly to the macvlan IPs.

---

## 3. Infrastructure Deployment

This section covers agent-matrix-specific infrastructure: Docker Compose, networking, and host/router configuration. For the database schema (Step 2 in the companion guide) and MCP server source code (Step 3), follow the [Open Brain for Agent Zero guide](open-brain-agent-zero-guide.md). This section covers only the infrastructure additions required to integrate Open Brain into the agent-matrix network.

### 3.1 Docker Compose

Create `/opt/agent-zero/open-brain/docker-compose.yml`:

```yaml
name: open-brain

services:
  # --- POSTGRESQL + PGVECTOR ---
  postgres:
    image: pgvector/pgvector:pg16
    container_name: open-brain-db
    hostname: open-brain-db
    mac_address: "02:42:AC:17:5A:01"
    restart: unless-stopped
    environment:
      POSTGRES_DB: open_brain
      POSTGRES_USER: openbrain
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./pgdata:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d:ro
      - ./pg-conf/pg_hba_custom.conf:/etc/postgresql/pg_hba_custom.conf:ro
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.90.1
      brain-net:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openbrain -d open_brain"]
      interval: 10s
      timeout: 5s
      retries: 5

  # --- OPEN BRAIN MCP SERVER ---
  open-brain-mcp:
    build:
      context: ./server
      dockerfile: Dockerfile
    container_name: open-brain-mcp
    hostname: open-brain-mcp
    mac_address: "02:42:AC:17:5A:02"
    restart: unless-stopped
    environment:
      DATABASE_URL: postgres://openbrain:${POSTGRES_PASSWORD}@open-brain-db:5432/open_brain
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      MCP_ACCESS_KEY: ${MCP_ACCESS_KEY}
      PORT: "3100"
    networks:
      macvlan-172-23:
        ipv4_address: 172.23.90.2
      brain-net:
    depends_on:
      postgres:
        condition: service_healthy

networks:
  brain-net:
    driver: bridge
  macvlan-172-23:
    external: true
```

The macvlan attachment means agents on 172.23.88.x, LAN workstations, and the g2s host (via mac0 shim) can all connect directly -- no Docker port-mapping required.

### 3.2 Environment File

Create `/opt/agent-zero/open-brain/.env`:

```bash
# PostgreSQL
POSTGRES_PASSWORD=<generate-a-strong-password>

# OpenRouter (embeddings + metadata extraction)
OPENROUTER_API_KEY=<your-openrouter-api-key>

# MCP Access Key (shared secret for client authentication)
MCP_ACCESS_KEY=<generate-with-openssl-rand-hex-32>
```

Generate the secrets:

```bash
openssl rand -hex 24    # POSTGRES_PASSWORD
openssl rand -hex 32    # MCP_ACCESS_KEY
```

### 3.3 PostgreSQL Client Auth (pg_hba_custom.conf)

Create `/opt/agent-zero/open-brain/pg-conf/pg_hba_custom.conf`:

```
# TYPE  DATABASE    USER        ADDRESS              METHOD
# Local socket connections
local   all         all                              trust
# Loopback
host    all         all         127.0.0.1/32         trust
host    all         all         ::1/128              trust
# Bridge network (MCP server container-to-container)
host    open_brain  openbrain   172.16.0.0/12        scram-sha-256
# Services segment (172.23.90.0/24)
host    open_brain  openbrain   172.23.90.0/24       scram-sha-256
# Agent containers (172.23.88.0/24)
host    open_brain  openbrain   172.23.88.0/24       scram-sha-256
# MHS / Caddy containers (172.23.89.0/24)
host    open_brain  openbrain   172.23.89.0/24       scram-sha-256
# g2s host via mac0 (172.23.88.254)
host    open_brain  openbrain   172.23.88.254/32     scram-sha-256
# Home LAN (workstations, other hosts)
host    open_brain  openbrain   172.23.0.0/16        scram-sha-256
# Reject everything else
host    all         all         0.0.0.0/0            reject
```

Create the init script at `/opt/agent-zero/open-brain/init-db/00-pg-hba.sh`:

```bash
#!/bin/bash
cp /etc/postgresql/pg_hba_custom.conf /var/lib/postgresql/data/pg_hba.conf
echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
```

Make it executable: `chmod +x /opt/agent-zero/open-brain/init-db/00-pg-hba.sh`

### 3.4 mac0 Shim Update (Host-to-Container Access)

The mac0 bridge interface on g2s currently routes 172.23.88.0/24 (agents) and 172.23.89.0/24 (MHS). Add the services segment so g2s itself can reach the DB and MCP server.

**One-time (immediate):**

```bash
sudo ip route add 172.23.90.0/24 dev mac0
```

**Persistent (update the systemd service):**

Edit `/etc/systemd/system/agent-bridge.service` and add the route to the `ExecStart` line:

```ini
ExecStart=/bin/bash -c 'ip link set $NIC promisc on; ip link add mac0 link $NIC type macvlan mode bridge || true; ip addr add 172.23.88.254/32 dev mac0 || true; ip link set mac0 up; ip route add 172.23.88.0/24 dev mac0 || true; ip route add 172.23.89.0/24 dev mac0 || true; ip route add 172.23.90.0/24 dev mac0 || true'
```

Then reload:

```bash
sudo systemctl daemon-reload
```

### 3.5 DD-WRT Static Routes (LAN-to-Container Access)

On kama (DD-WRT), add static routes so LAN clients can reach the services segment. In Administration > Commands > Startup, add:

```bash
ip route add 172.23.90.0/24 via 172.23.100.121   # services segment (g2s)
```

Or per-host if you prefer granularity:

```bash
ip route add 172.23.90.1/32 via 172.23.100.121   # open-brain-db (g2s)
ip route add 172.23.90.2/32 via 172.23.100.121   # open-brain-mcp (g2s)
```

### 3.6 DD-WRT Static DHCP Leases

Add entries for the new containers (Services > Services > Static Leases):

| MAC | Hostname | IP |
|-----|----------|----|
| 02:42:AC:17:5A:01 | open-brain-db | 172.23.90.1 |
| 02:42:AC:17:5A:02 | open-brain-mcp | 172.23.90.2 |

### 3.7 Network Verification

Before deploying services, confirm the routing is in place:

```bash
# On g2s -- confirm the 172.23.90.0/24 route exists via mac0
ip route show 172.23.90.0/24
# Expected: "172.23.90.0/24 dev mac0 scope link"

# From a LAN workstation -- confirm DD-WRT is routing to g2s
traceroute -n 172.23.90.1
# Expected: first hop is 172.23.1.1 (kama), next hop is 172.23.100.121 (g2s)
```

> **Note:** You cannot ping 172.23.90.1 or 172.23.90.2 yet -- no containers are listening. Full service verification comes after `docker compose up`.

### 3.8 Deploy and Verify

**Create the directory structure:**

```bash
ssh g2s
sudo mkdir -p /opt/agent-zero/open-brain/{server/src,init-db,pg-conf,pgdata}
```

**Build and start:**

```bash
cd /opt/agent-zero/open-brain
docker compose up -d --build
```

**Verify services:**

```bash
# Check services are healthy
docker compose ps

# Check PostgreSQL schema
docker exec -it open-brain-db psql -U openbrain -d open_brain \
  -c "\dt" -c "\df match_thoughts"

# Check MCP server health (via macvlan IP)
curl http://172.23.90.2:3100/health

# Check DB is reachable from g2s host (via mac0 shim)
psql -h 172.23.90.1 -U openbrain -d open_brain -c "SELECT 1"

# Test MCP tool listing
curl -X POST http://172.23.90.2:3100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "x-brain-key: <your-access-key>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

Expected response: four tools -- `search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`.

**Verify cross-network connectivity:**

```bash
# From an agent container (172.23.88.x -> 172.23.90.x via macvlan)
docker exec -it agent0-1 curl http://172.23.90.2:3100/health

# From a LAN workstation (via DD-WRT static route)
psql -h 172.23.90.1 -U openbrain -d open_brain -c "SELECT 1"
curl http://172.23.90.2:3100/health
```

---

## 4. Connecting Agent Zero Instances

### 4.1 Agent Zero MCP Configuration

Each Agent Zero instance accesses Open Brain via **Settings > MCP/A2A > External MCP Servers**. Add the following configuration:

```json
{
  "mcpServers": {
    "open-brain": {
      "url": "http://172.23.90.2:3100/mcp",
      "headers": {
        "x-brain-key": "<access-key>"
      }
    }
  }
}
```

Agents on 172.23.88.x reach 172.23.90.2 directly via the shared macvlan network -- no tunneling, proxying, or port-mapping involved. The connection stays entirely on the g2s host's virtual network fabric.

Alternatively, agents can pass the key as a query parameter:

```json
{
  "mcpServers": {
    "open-brain": {
      "url": "http://172.23.90.2:3100/mcp?key=<access-key>"
    }
  }
}
```

### 4.2 Connecting from Cursor / Workstations

Workstations on the home LAN reach 172.23.90.x via the DD-WRT static route (Section 3.5). Add to your MCP configuration (`.cursor/mcp.json` or workspace `mcp.json`):

```json
{
  "mcpServers": {
    "open-brain": {
      "url": "http://172.23.90.2:3100/mcp?key=<your-access-key>"
    }
  }
}
```

For stdio-only MCP clients that cannot make HTTP requests directly, use the `mcp-remote` bridge:

```json
{
  "mcpServers": {
    "open-brain": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://172.23.90.2:3100/mcp",
        "--header",
        "x-brain-key:${BRAIN_KEY}"
      ],
      "env": {
        "BRAIN_KEY": "<your-access-key>"
      }
    }
  }
}
```

### 4.3 Startup Services Integration

To verify Open Brain connectivity when an agent container boots, add a health check to the agent's `startup-services.sh`:

```bash
BRAIN_URL="${OPEN_BRAIN_URL:-http://172.23.90.2:3100}"
for i in $(seq 1 30); do
    if curl -sf "${BRAIN_URL}/health" > /dev/null 2>&1; then
        echo "Open Brain is available"
        break
    fi
    echo "Waiting for Open Brain... ($i/30)"
    sleep 2
done
```

This is non-blocking -- if Open Brain is down, the agent still starts normally. The MCP tools simply will not be available until the service recovers.

---

## 5. The Collective Memory Model

This is the core design: how agent-matrix uses Open Brain as shared organizational memory across the fleet.

### 5.1 Memory Layers

Agent-matrix operates with three memory layers, each with a distinct role:

**Context Window (Ephemeral)** -- The current conversation in Agent Zero's chat interface. This is the LLM's working memory: the prompt, the conversation history, and any tool results from the current session. It evaporates when the conversation ends. High bandwidth, zero persistence.

**Agent Zero Local Memory (Personal Unconscious)** -- Each agent's per-instance vector store. Agent Zero automatically captures memories from conversations and organizes them into four types: Conversation Memory, Knowledge Base, Learning Memory, and Project Memory. These are searchable via semantic similarity and persist across conversations within a single agent. But they are siloed -- agent0-1 cannot search agent0-3's local memory.

**Open Brain Collective Store (Collective Unconscious)** -- The shared PostgreSQL + pgvector database at 172.23.90.1. Any agent (or human) can capture thoughts to this store and any agent can search it. Knowledge here is curated, significant, and organizational in nature. It persists independently of any single agent's lifecycle.

The layers are complementary:

| Question | Where to look |
|----------|--------------|
| "What did we just discuss?" | Context window |
| "What have I learned about Docker macvlan?" | Agent Zero local memory |
| "What does the organization know about TLS certificate renewal?" | Open Brain collective store |

### 5.2 Agent Identity and Provenance

When multiple agents contribute to a shared knowledge store, provenance is essential. Each thought captured to Open Brain should include agent identity in the JSONB metadata field:

| Field | Example | Purpose |
|-------|---------|---------|
| `agent_id` | `"agent0-1"` | Machine-readable agent identifier |
| `agent_alias` | `"Gandalf"` | Optional human-readable name |
| `promotion_type` | `"manual"` | How the thought entered the collective: `manual`, `auto-sync`, or `event-driven` |
| `source_context` | `"agent-matrix-development"` | Optional project or task context |

This enables targeted queries like "what has Gandalf learned about TLS?" while still allowing cross-agent search across the entire collective. The existing Open Brain `thoughts` table already has a JSONB `metadata` column -- these fields require no schema migration, only a convention for how agents populate metadata when calling `capture_thought`.

Example `capture_thought` call with agent identity:

```
"Remember this for the team: when renewing step-ca certificates for
Continuwuity, you must restart Caddy after deploying the new cert,
not just Continuwuity. The old cert is cached in Caddy's TLS config."
```

The resulting metadata (auto-extracted by the MCP server + manually enriched):

```json
{
  "type": "reference",
  "topics": ["tls", "step-ca", "caddy", "continuwuity"],
  "agent_id": "agent0-1",
  "agent_alias": "Gandalf",
  "promotion_type": "manual",
  "source_context": "agent-matrix-operations",
  "source": "mcp"
}
```

### 5.3 Memory Promotion Pipeline

Knowledge flows from individual agents to the collective store through a promotion pipeline. Three approaches, implemented in phases:

**Manual Promotion (Phase 1 -- immediate)**

An agent or human uses the `capture_thought` MCP tool to save knowledge to the collective. This already works with the existing Open Brain deployment. The agent (or a human operator conversing with the agent) explicitly decides that a piece of knowledge is valuable to the organization and captures it.

Examples of knowledge worth promoting:

- Solutions to complex debugging sessions
- Architectural decisions and their rationale
- Operational procedures (certificate renewal, federation setup)
- Lessons learned from failures
- Configuration patterns that work

**Automated Periodic Sync (Phase 2 -- near-term)**

A sync script reads Agent Zero's local memory database and promotes significant entries to Open Brain. Run weekly or after major tasks.

Filter criteria for automatic promotion:
- Learning memories (Agent Zero's "I learned that..." entries)
- Knowledge base entries with high retrieval counts
- Entries tagged with cross-agent-relevant areas (e.g., "infrastructure", "operations")
- Entries newer than the last sync timestamp

The script would call `capture_thought` via the MCP API for each promoted entry, adding `"promotion_type": "auto-sync"` to the metadata.

**Event-Driven Promotion (Phase 3 -- future)**

A custom Agent Zero skill that triggers `capture_thought` when:
- A complex task completes successfully
- A new pattern or solution is discovered
- A human says "remember this for everyone" or "save this to the collective"
- A learning memory is created that matches organizational topic patterns

This requires extending Agent Zero's behavior patterns -- building a skill that intercepts memory creation events and evaluates them against promotion criteria.

### 5.4 Complementary Role with Agent Zero Memory

Agent Zero memory and Open Brain are not competing systems. They serve different roles in the cognitive architecture:

| Dimension | Agent Zero Local Memory | Open Brain Collective Store |
|-----------|------------------------|----------------------------|
| Scope | Per-agent | All agents |
| Volume | High (every conversation) | Curated (significant knowledge) |
| Curation | Automatic | Manual or filtered |
| Lifetime | Container lifetime | Database lifetime |
| Content | Conversations, tasks, ephemeral context | Organizational knowledge, decisions, patterns |
| Analogy | Personal diary | Team knowledge base |

The query priority when an agent needs information:

1. **Check context window** -- is the answer in the current conversation?
2. **Search Agent Zero local memory** -- have I personally encountered this before?
3. **Search Open Brain** -- does the organization know about this?

Agent Zero's Knowledge Base import feature provides a bidirectional bridge. Exported summaries from Open Brain could be placed in an agent's `knowledge/` directory for local caching -- giving frequently-needed organizational knowledge the speed of local memory access.

### 5.5 The Gandalf Scenario

A concrete walkthrough of how collective memory changes operations.

**Without Open Brain:**

Agent0-1 (Gandalf) has participated in months of agent-matrix development. Its local memory contains:

- How to debug Docker macvlan networking issues (the rootful Docker requirement, the mac0 shim, promiscuous mode)
- The exact steps for Continuwuity-to-Synapse federation troubleshooting (hostAliases, CA bundle with root + intermediate, ip_range_whitelist)
- TLS certificate renewal procedures with step-ca (the `--not-after=8760h` equals-syntax requirement)
- How to configure DD-WRT static routes for new agent instances (/32 routes via g2s)
- Migration procedures from Dendrite to Continuwuity (environment variables vs YAML, registration token flow)
- The DHCP Option 121 gotcha where `systemd-networkd` ignores Option 3

This knowledge is trapped. If a new operator asks agent0-3 "how do I troubleshoot federation?", agent0-3 has no answer -- it has never done federation troubleshooting. The operator must either ask Gandalf directly (synchronous, requires Gandalf to be available) or read the documentation (which may not capture every nuance Gandalf learned through trial and error).

If Gandalf's container is destroyed and rebuilt, the knowledge is gone entirely.

**With Open Brain:**

Gandalf (or a human operator working with Gandalf) promotes key learnings to the collective store:

```
capture_thought: "Federation 502 on room join almost always means
missing hostAliases in the Synapse K8s deployment. The invite
working proves outbound federation is fine -- it is inbound
(Synapse -> agent) that is broken. Check hostAliases first, then
federation_domain_whitelist, then CA bundle (must include root CA,
not just intermediate)."
```

Now when agent0-6 is provisioned, it connects to Open Brain and can immediately search "how do I troubleshoot federation with Synapse?" The collective returns Gandalf's hard-won knowledge -- with provenance metadata showing it came from agent0-1 during agent-matrix operations.

The knowledge survives container destruction, operator turnover, and fleet expansion. It is organizational capital, not personal experience.

### 5.6 Matrix Integration Possibilities

The agent-matrix architecture creates natural integration points between Matrix rooms and the collective store:

- **Room archival:** A Matrix bot (or an extension to the existing matrix-bot) could monitor designated rooms and capture messages tagged with a specific emoji reaction (e.g., a brain emoji) or command (e.g., `!remember`) to Open Brain.
- **Task room conclusions:** Multi-agent task rooms could auto-archive their conclusions to the collective store when the task is marked complete.
- **Operational log capture:** The operations channel (shared by all agents and humans) could feed significant announcements to Open Brain automatically.
- **Cross-agent queries via Matrix:** An agent could be asked in a Matrix room "what does the team know about X?" and search Open Brain to answer -- making the collective memory accessible through natural conversation.

These integrations are future work. The current deployment focuses on MCP-based access (direct tool calls from agents and workstations).

---

## 6. Backup and Disaster Recovery

The collective store is organizational capital. Unlike individual agent memories (which are useful but replaceable through re-learning), the collective store accumulates curated knowledge that may represent months of operational experience across the entire fleet. Treat it accordingly.

### 6.1 Daily Logical Backups

Add a cron job on g2s for daily `pg_dump`:

```bash
# Add to crontab on g2s
0 3 * * * docker exec open-brain-db pg_dump -U openbrain open_brain \
  | gzip > /opt/agent-zero/backups/open-brain-$(date +\%Y\%m\%d).sql.gz
```

Create the backup directory:

```bash
sudo mkdir -p /opt/agent-zero/backups
```

Retention policy -- keep 30 days of backups:

```bash
# Add to crontab, runs after the backup
15 3 * * * find /opt/agent-zero/backups -name "open-brain-*.sql.gz" -mtime +30 -delete
```

### 6.2 Restore Procedure

To restore from a logical backup:

```bash
# Stop the MCP server (prevents writes during restore)
docker stop open-brain-mcp

# Drop and recreate the database
docker exec -it open-brain-db psql -U openbrain -c "DROP DATABASE open_brain;"
docker exec -it open-brain-db psql -U openbrain -c "CREATE DATABASE open_brain;"

# Restore from backup
gunzip -c /opt/agent-zero/backups/open-brain-20260324.sql.gz \
  | docker exec -i open-brain-db psql -U openbrain -d open_brain

# Restart the MCP server
docker start open-brain-mcp

# Verify
curl -X POST http://172.23.90.2:3100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "x-brain-key: <your-access-key>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"thought_stats","arguments":{}}}'
```

The HNSW vector index is rebuilt automatically from the table data on restore -- only the table data needs to be in the backup.

### 6.3 WAL Archiving (Production)

For point-in-time recovery (PITR), enable WAL archiving. This allows recovery to any timestamp -- not just the most recent daily backup.

Add to `postgresql.conf` (via a custom init script or config mount):

```
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal-archive/%f'
```

Take a base backup:

```bash
docker exec open-brain-db pg_basebackup -U openbrain \
  -D /var/lib/postgresql/basebackup -Ft -z
```

To recover to a specific timestamp:

```bash
# In recovery.conf (or postgresql.conf on PG 12+)
restore_command = 'cp /var/lib/postgresql/wal-archive/%f %p'
recovery_target_time = '2026-03-24 14:30:00'
```

This is recommended for production deployments where the collective knowledge represents significant organizational investment.

### 6.4 Off-site Backup

Copy backups to tarnover or an off-site location. The collective knowledge is irreplaceable organizational memory -- a single disk failure on g2s should not be a catastrophic loss.

```bash
# rsync daily backups to tarnover
0 4 * * * rsync -az /opt/agent-zero/backups/open-brain-*.sql.gz \
  tarnover:/opt/backups/open-brain/
```

---

## 7. Future Directions

The following enhancements are planned or under consideration:

- **Memory curator agent** -- a dedicated Agent Zero instance (or skill) that periodically reviews the collective store, identifies duplicate or contradictory entries, merges related thoughts, and maintains overall quality. The curator would use `search_thoughts` to find similar entries, evaluate them, and consolidate.

- **Cross-agent memory search in Agent Zero's default behavior** -- modifying Agent Zero's prompt or behavior patterns to automatically check Open Brain when the local memory does not contain a relevant answer. This would make the collective memory seamlessly accessible without explicit tool invocation.

- **Matrix room archival to Open Brain** -- a bot or integration that captures tagged messages from Matrix rooms to the collective store. Significant discussions, decisions, and incident resolutions would be automatically preserved.

- **Local LLM for embedding generation** -- replacing the OpenRouter dependency for `text-embedding-3-small` with a locally-hosted embedding model (e.g., via Ollama or vLLM on g2s). This removes the external API dependency and keeps all data on-premises.

- **TLS for the Open Brain MCP server** -- adding a Caddy reverse proxy in front of `open-brain-mcp` with a step-ca certificate, following the same pattern used for agent homeservers. This encrypts MCP traffic on the LAN.

- **Per-agent JWT authentication via Keycloak** -- replacing the shared `x-brain-key` access key with per-agent JWT tokens issued by Keycloak. This provides proper identity, auditing, and revocation capabilities.

- **Integration with the Rust Matrix MCP server** -- when the planned Rust-based Matrix MCP server (with E2EE support) replaces the current Node.js implementation, it could include native Open Brain integration for E2EE-aware memory capture from encrypted Matrix rooms.

---

## Appendix: Network Segment Reference

Complete network segment table for the Cybertribe lab:

| Segment | CIDR | Purpose |
|---------|------|---------|
| Home LAN | 172.23.0.0/16 | All lab hosts and containers |
| Agent containers | 172.23.88.0/24 | Agent Zero instances (agent0-1 through agent0-5) |
| MHS containers | 172.23.89.0/24 | Caddy TLS proxies (federation endpoints) |
| Services segment | 172.23.90.0/24 | Open Brain DB + MCP server |
| VPN tunnel | 172.23.200.0/24 | Contabo K8s cluster <-> home lab |

Key hosts:

| Host | IP | Role |
|------|----|------|
| kama (DD-WRT) | 172.23.1.1 | Gateway, DHCP, DNS, VPN server |
| tarnover | 172.23.0.103 | step-ca PKI, admin workstation, off-site backup target |
| g2s | 172.23.100.121 | Primary Docker host (all agents + Open Brain) |
| mac0 (g2s) | 172.23.88.254 | macvlan bridge interface (host-local) |
| open-brain-db | 172.23.90.1 | PostgreSQL 16 + pgvector |
| open-brain-mcp | 172.23.90.2 | Open Brain MCP server (Node.js) |

---

*Last updated: March 24, 2026*
