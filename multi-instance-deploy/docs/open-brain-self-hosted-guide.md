# Open Brain (OB1) -- Self-Hosted PostgreSQL Guide for Agent Matrix

## Overview

This guide replaces every Supabase dependency in the [OB1 Open Brain](https://github.com/NateBJones-Projects/OB1) project with self-hosted equivalents running on **g2s** within the agent-matrix infrastructure. The result is a fully local knowledge-base MCP server backed by PostgreSQL + pgvector, accessible to all agent instances and external MCP clients.

### What OB1 Provides (and What We're Replacing)

| OB1 / Supabase Component | Self-Hosted Replacement |
|---|---|
| Supabase PostgreSQL | **PostgreSQL 16 + pgvector** Docker container on g2s |
| Supabase JS Client (`.from()`, `.rpc()`) | **node-postgres (`pg`)** with direct SQL |
| Supabase Edge Function (Deno runtime) | **Node.js / Express** server (matches existing matrix-mcp-server pattern) |
| Supabase Row Level Security | PostgreSQL roles + application-level access key |
| Supabase PostgREST (auto REST API) | Not needed -- MCP server talks to PG directly |
| OpenRouter (embeddings + LLM) | **Kept as-is** -- external API, no Supabase dependency |

### Architecture on g2s

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

Both containers sit on the **172.23.90.0/24 services segment** (macvlan) with first-class LAN IPs, plus a private bridge network (`brain-net`) for container-to-container DB access. The macvlan attachment means the DB accepts connections from agents (172.23.88.x), the g2s host (via mac0 shim), and LAN workstations (via DD-WRT static routes) -- no Docker port-mapping needed.

---

## Step 1: PostgreSQL + pgvector Docker Service

### 1.1 Docker Compose Addition

Add this to your infrastructure on g2s. This can be a standalone compose file or merged into the agent template. Since the brain is shared across agents, a standalone deployment is recommended.

Create the file `/opt/agent-zero/open-brain/docker-compose.yml`:

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

> **Networking design:** Both the DB and MCP server live on the **172.23.90.0/24 services segment** via the existing `macvlan-172-23` network (which covers the full 172.23.0.0/16 supernet). They also share a private `brain-net` bridge so the MCP server can resolve the DB by Docker hostname (`open-brain-db`). The macvlan attachment gives each container a first-class LAN IP, so external clients (LAN hosts, agents on 172.23.88.x, workstations) can connect directly -- no Docker port-mapping required. See **Step 1.3** below for the host and router changes needed to make this routable.

### 1.2 Environment File

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
# Generate POSTGRES_PASSWORD
openssl rand -hex 24

# Generate MCP_ACCESS_KEY
openssl rand -hex 32
```

### 1.3 Network Plumbing (g2s Host + DD-WRT)

Placing the DB on macvlan means three things need updating so traffic can reach 172.23.90.x from outside the container:

#### 1.3a PostgreSQL Client Auth (`pg_hba.conf`)

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

Then add this line to the init script so PostgreSQL loads the custom `pg_hba.conf`. Create `/opt/agent-zero/open-brain/init-dbba.sh`:

```bash
#!/bin/bash
# Copy custom pg_hba.conf into the data directory, overriding the default.
# This runs before schema init because files are processed in alphabetical order.
cp /etc/postgresql/pg_hba_custom.conf /var/lib/postgresql/data/pg_hba.conf
echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
```

> Make it executable: `chmod +x /opt/agent-zero/open-brain/init-db/00-pg-hba.sh`

#### 1.3b mac0 Shim on g2s (Host-to-Container Access)

The mac0 bridge interface currently routes 172.23.88.0/24 and 172.23.89.0/24. Add 172.23.90.0/24 so g2s itself can reach the DB:

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

#### 1.3c DD-WRT Static Routes (LAN-to-Container Access)

On kama (DD-WRT), add static routes so LAN clients (workstations, other hosts) can reach the services segment. In Administration > Commands > Startup, add:

```bash
ip route add 172.23.90.1/32 via 172.23.100.121   # open-brain-db (g2s)
ip route add 172.23.90.2/32 via 172.23.100.121   # open-brain-mcp (g2s)
```

Or if you expect more services on the segment, route the whole /24:

```bash
ip route add 172.23.90.0/24 via 172.23.100.121   # services segment (g2s)
```

#### 1.3d DD-WRT Static DHCP Leases

Add entries for the new containers (Services > Services > Static Leases):

| MAC | Hostname | IP |
|-----|----------|----|
| 02:42:AC:17:5A:01 | open-brain-db | 172.23.90.1 |
| 02:42:AC:17:5A:02 | open-brain-mcp | 172.23.90.2 |

#### 1.3e Verify Network Plumbing

Before deploying services, confirm the routing is in place. The services aren't running yet (that happens in Step 4), so you're only checking that the network path exists.

```bash
# On g2s -- confirm the 172.23.90.0/24 route exists via mac0
ip route show 172.23.90.0/24
# Expected: "172.23.90.0/24 dev mac0 scope link"

# From a LAN workstation -- confirm DD-WRT is routing to g2s
traceroute -n 172.23.90.1
# Expected: first hop is your gateway (172.23.1.1), next hop is g2s (172.23.100.121)
```

> **Note:** You won't be able to ping 172.23.90.1 or 172.23.90.2 yet -- no containers are listening on those IPs. Full service verification comes in Step 4.3 after `docker compose up`.

---

## Step 2: Database Schema (pgvector)

This replicates the Supabase SQL from OB1's getting-started guide but for a bare PostgreSQL instance with pgvector.

Create the file `/opt/agent-zero/open-brain/init-db/01-schema.sql`:

```sql
-- =============================================================================
-- Open Brain Schema for PostgreSQL 16 + pgvector
-- Replaces: Supabase table creation, search function, RLS, grants
-- =============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main thoughts table
CREATE TABLE IF NOT EXISTS thoughts (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    metadata    JSONB DEFAULT '{}'::JSONB,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- Index for fast vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS thoughts_embedding_idx
    ON thoughts USING hnsw (embedding vector_cosine_ops);

-- Index for JSONB metadata filtering
CREATE INDEX IF NOT EXISTS thoughts_metadata_idx
    ON thoughts USING gin (metadata);

-- Index for date-range queries
CREATE INDEX IF NOT EXISTS thoughts_created_at_idx
    ON thoughts (created_at DESC);

-- Auto-update the updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS thoughts_updated_at ON thoughts;
CREATE TRIGGER thoughts_updated_at
    BEFORE UPDATE ON thoughts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Semantic search function (replaces Supabase's match_thoughts RPC)
-- =============================================================================
-- Usage from Node: SELECT * FROM match_thoughts($1::vector, $2::float, $3::int, $4::jsonb)
CREATE OR REPLACE FUNCTION match_thoughts(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE (
    id          UUID,
    content     TEXT,
    metadata    JSONB,
    similarity  FLOAT,
    created_at  TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.content,
        t.metadata,
        (1 - (t.embedding <=> query_embedding))::FLOAT AS similarity,
        t.created_at
    FROM thoughts t
    WHERE (1 - (t.embedding <=> query_embedding)) > match_threshold
      AND (filter = '{}'::JSONB OR t.metadata @> filter)
    ORDER BY t.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

This file is automatically executed by PostgreSQL on first container start (via the `docker-entrypoint-initdb.d` mount). For subsequent schema changes, apply them manually or use a migration tool.

---

## Step 3: Open Brain MCP Server (Node.js / Express)

This is the core replacement for the Supabase Edge Function. It's a Node.js server that:
- Exposes MCP tools via the `@modelcontextprotocol/sdk`
- Talks directly to PostgreSQL using `pg` (node-postgres)
- Calls OpenRouter for embeddings and metadata extraction
- Authenticates via `x-brain-key` header or `?key=` query parameter

### 3.1 Project Structure

```
/opt/agent-zero/open-brain/server/
  ├── Dockerfile
  ├── package.json
  ├── tsconfig.json
  └── src/
      ├── http-server.ts       # Express entry point + auth middleware
      ├── mcp-server.ts        # MCP server with 4 tools
      ├── db.ts                # PostgreSQL connection pool
      ├── openrouter.ts        # Embedding + metadata extraction
      └── route-handlers.ts    # MCP transport wiring
```

### 3.2 package.json

```json
{
  "name": "open-brain-mcp",
  "version": "1.0.0",
  "description": "Self-hosted Open Brain MCP server (PostgreSQL + pgvector)",
  "main": "dist/http-server.js",
  "type": "module",
  "scripts": {
    "start": "node dist/http-server.js",
    "build": "tsc",
    "dev": "tsx watch src/http-server.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.16.0",
    "cors": "^2.8.5",
    "dotenv": "^17.2.0",
    "express": "^5.1.0",
    "pg": "^8.13.0",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "@types/cors": "^2.8.19",
    "@types/express": "^5.0.1",
    "@types/node": "^22.15.0",
    "@types/pg": "^8.11.0",
    "tsx": "^4.19.4",
    "typescript": "^5.8.0"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}
```

### 3.3 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "resolveJsonModule": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### 3.4 src/db.ts -- PostgreSQL Connection

```typescript
import pg from "pg";

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on("error", (err) => {
  console.error("Unexpected PostgreSQL pool error:", err);
});

export async function query<T extends pg.QueryResultRow = any>(
  text: string,
  params?: any[]
): Promise<pg.QueryResult<T>> {
  return pool.query<T>(text, params);
}

export async function shutdown(): Promise<void> {
  await pool.end();
}

export default pool;
```

### 3.5 src/openrouter.ts -- Embeddings & Metadata

```typescript
const OPENROUTER_BASE = "https://openrouter.ai/api/v1";
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY!;

export async function getEmbedding(text: string): Promise<number[]> {
  const r = await fetch(`${OPENROUTER_BASE}/embeddings`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "openai/text-embedding-3-small",
      input: text,
    }),
  });

  if (!r.ok) {
    const msg = await r.text().catch(() => "");
    throw new Error(`OpenRouter embeddings failed: ${r.status} ${msg}`);
  }

  const d = await r.json();
  return d.data[0].embedding;
}

export async function extractMetadata(
  text: string
): Promise<Record<string, unknown>> {
  const r = await fetch(`${OPENROUTER_BASE}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "openai/gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `Extract metadata from the user's captured thought. Return JSON with:
- "people": array of people mentioned (empty if none)
- "action_items": array of implied to-dos (empty if none)
- "dates_mentioned": array of dates YYYY-MM-DD (empty if none)
- "topics": array of 1-3 short topic tags (always at least one)
- "type": one of "observation", "task", "idea", "reference", "person_note"
Only extract what's explicitly there.`,
        },
        { role: "user", content: text },
      ],
    }),
  });

  const d = await r.json();
  try {
    return JSON.parse(d.choices[0].message.content);
  } catch {
    return { topics: ["uncategorized"], type: "observation" };
  }
}
```

### 3.6 src/mcp-server.ts -- MCP Server with 4 Tools

This is the core logic -- a direct port of OB1's `index.ts` from Supabase client calls to raw SQL via `pg`.

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { query } from "./db.js";
import { getEmbedding, extractMetadata } from "./openrouter.js";

export function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "open-brain",
    version: "1.0.0",
  });

  // ── Tool 1: Semantic Search ──────────────────────────────────────────
  server.registerTool(
    "search_thoughts",
    {
      title: "Search Thoughts",
      description:
        "Search captured thoughts by meaning. Use this when the user asks about a topic, person, or idea they've previously captured.",
      inputSchema: {
        query: z.string().describe("What to search for"),
        limit: z.number().optional().default(10),
        threshold: z.number().optional().default(0.5),
      },
    },
    async ({ query: searchQuery, limit, threshold }) => {
      try {
        const qEmb = await getEmbedding(searchQuery);
        const vectorStr = `[${qEmb.join(",")}]`;

        const { rows } = await query(
          `SELECT * FROM match_thoughts($1::vector, $2, $3, $4::jsonb)`,
          [vectorStr, threshold, limit, "{}"]
        );

        if (!rows.length) {
          return {
            content: [
              {
                type: "text" as const,
                text: `No thoughts found matching "${searchQuery}".`,
              },
            ],
          };
        }

        const results = rows.map((t, i) => {
          const m = t.metadata || {};
          const parts = [
            `--- Result ${i + 1} (${(t.similarity * 100).toFixed(1)}% match) ---`,
            `Captured: ${new Date(t.created_at).toLocaleDateString()}`,
            `Type: ${m.type || "unknown"}`,
          ];
          if (Array.isArray(m.topics) && m.topics.length)
            parts.push(`Topics: ${m.topics.join(", ")}`);
          if (Array.isArray(m.people) && m.people.length)
            parts.push(`People: ${m.people.join(", ")}`);
          if (Array.isArray(m.action_items) && m.action_items.length)
            parts.push(`Actions: ${m.action_items.join("; ")}`);
          parts.push(`\n${t.content}`);
          return parts.join("\n");
        });

        return {
          content: [
            {
              type: "text" as const,
              text: `Found ${rows.length} thought(s):\n\n${results.join("\n\n")}`,
            },
          ],
        };
      } catch (err: unknown) {
        return {
          content: [
            { type: "text" as const, text: `Error: ${(err as Error).message}` },
          ],
          isError: true,
        };
      }
    }
  );

  // ── Tool 2: List Recent Thoughts ─────────────────────────────────────
  server.registerTool(
    "list_thoughts",
    {
      title: "List Recent Thoughts",
      description:
        "List recently captured thoughts with optional filters by type, topic, person, or time range.",
      inputSchema: {
        limit: z.number().optional().default(10),
        type: z
          .string()
          .optional()
          .describe(
            "Filter by type: observation, task, idea, reference, person_note"
          ),
        topic: z.string().optional().describe("Filter by topic tag"),
        person: z.string().optional().describe("Filter by person mentioned"),
        days: z
          .number()
          .optional()
          .describe("Only thoughts from the last N days"),
      },
    },
    async ({ limit, type, topic, person, days }) => {
      try {
        const conditions: string[] = [];
        const params: any[] = [];
        let paramIdx = 1;

        if (type) {
          conditions.push(`metadata @> $${paramIdx}::jsonb`);
          params.push(JSON.stringify({ type }));
          paramIdx++;
        }
        if (topic) {
          conditions.push(`metadata @> $${paramIdx}::jsonb`);
          params.push(JSON.stringify({ topics: [topic] }));
          paramIdx++;
        }
        if (person) {
          conditions.push(`metadata @> $${paramIdx}::jsonb`);
          params.push(JSON.stringify({ people: [person] }));
          paramIdx++;
        }
        if (days) {
          conditions.push(`created_at >= now() - interval '1 day' * $${paramIdx}`);
          params.push(days);
          paramIdx++;
        }

        const whereClause =
          conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

        params.push(limit);
        const sql = `
          SELECT content, metadata, created_at
          FROM thoughts
          ${whereClause}
          ORDER BY created_at DESC
          LIMIT $${paramIdx}
        `;

        const { rows } = await query(sql, params);

        if (!rows.length) {
          return {
            content: [{ type: "text" as const, text: "No thoughts found." }],
          };
        }

        const results = rows.map((t, i) => {
          const m = t.metadata || {};
          const tags = Array.isArray(m.topics) ? m.topics.join(", ") : "";
          return `${i + 1}. [${new Date(t.created_at).toLocaleDateString()}] (${m.type || "??"}${tags ? " - " + tags : ""})\n   ${t.content}`;
        });

        return {
          content: [
            {
              type: "text" as const,
              text: `${rows.length} recent thought(s):\n\n${results.join("\n\n")}`,
            },
          ],
        };
      } catch (err: unknown) {
        return {
          content: [
            { type: "text" as const, text: `Error: ${(err as Error).message}` },
          ],
          isError: true,
        };
      }
    }
  );

  // ── Tool 3: Statistics ───────────────────────────────────────────────
  server.registerTool(
    "thought_stats",
    {
      title: "Thought Statistics",
      description:
        "Get a summary of all captured thoughts: totals, types, top topics, and people.",
      inputSchema: {
        verbose: z.boolean().optional().default(false).describe("Include detailed breakdown"),
      },
    },
    async ({ verbose }) => {
      try {
        const countResult = await query(
          "SELECT COUNT(*) AS total FROM thoughts"
        );
        const total = parseInt(countResult.rows[0].total, 10);

        const { rows } = await query(
          "SELECT metadata, created_at FROM thoughts ORDER BY created_at DESC"
        );

        const types: Record<string, number> = {};
        const topics: Record<string, number> = {};
        const people: Record<string, number> = {};

        for (const r of rows) {
          const m = r.metadata || {};
          if (m.type) types[m.type] = (types[m.type] || 0) + 1;
          if (Array.isArray(m.topics))
            for (const t of m.topics) topics[t] = (topics[t] || 0) + 1;
          if (Array.isArray(m.people))
            for (const p of m.people) people[p] = (people[p] || 0) + 1;
        }

        const sort = (o: Record<string, number>): [string, number][] =>
          Object.entries(o)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        const lines: string[] = [
          `Total thoughts: ${total}`,
          `Date range: ${
            rows.length
              ? new Date(rows[rows.length - 1].created_at).toLocaleDateString() +
                " -> " +
                new Date(rows[0].created_at).toLocaleDateString()
              : "N/A"
          }`,
          "",
          "Types:",
          ...sort(types).map(([k, v]) => `  ${k}: ${v}`),
        ];

        if (Object.keys(topics).length) {
          lines.push("", "Top topics:");
          for (const [k, v] of sort(topics)) lines.push(`  ${k}: ${v}`);
        }

        if (Object.keys(people).length) {
          lines.push("", "People mentioned:");
          for (const [k, v] of sort(people)) lines.push(`  ${k}: ${v}`);
        }

        return { content: [{ type: "text" as const, text: lines.join("\n") }] };
      } catch (err: unknown) {
        return {
          content: [
            { type: "text" as const, text: `Error: ${(err as Error).message}` },
          ],
          isError: true,
        };
      }
    }
  );

  // ── Tool 4: Capture Thought ──────────────────────────────────────────
  server.registerTool(
    "capture_thought",
    {
      title: "Capture Thought",
      description:
        "Save a new thought to the Open Brain. Generates an embedding and extracts metadata automatically. Use this when the user wants to save something to their brain -- notes, insights, decisions, or migrated content from other systems.",
      inputSchema: {
        content: z
          .string()
          .describe(
            "The thought to capture -- a clear, standalone statement that will make sense when retrieved later by any AI"
          ),
      },
    },
    async ({ content }) => {
      try {
        const [embedding, metadata] = await Promise.all([
          getEmbedding(content),
          extractMetadata(content),
        ]);

        const vectorStr = `[${embedding.join(",")}]`;
        const metaWithSource = { ...metadata, source: "mcp" };

        await query(
          `INSERT INTO thoughts (content, embedding, metadata)
           VALUES ($1, $2::vector, $3::jsonb)`,
          [content, vectorStr, JSON.stringify(metaWithSource)]
        );

        const meta = metadata as Record<string, unknown>;
        let confirmation = `Captured as ${meta.type || "thought"}`;
        if (Array.isArray(meta.topics) && meta.topics.length)
          confirmation += ` -- ${meta.topics.join(", ")}`;
        if (Array.isArray(meta.people) && meta.people.length)
          confirmation += ` | People: ${meta.people.join(", ")}`;
        if (Array.isArray(meta.action_items) && meta.action_items.length)
          confirmation += ` | Actions: ${meta.action_items.join("; ")}`;

        return {
          content: [{ type: "text" as const, text: confirmation }],
        };
      } catch (err: unknown) {
        return {
          content: [
            { type: "text" as const, text: `Error: ${(err as Error).message}` },
          ],
          isError: true,
        };
      }
    }
  );

  return server;
}
```

### 3.7 src/route-handlers.ts -- MCP Transport Wiring

```typescript
import { Request, Response } from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpServer } from "./mcp-server.js";

export async function handleMcpRequest(
  req: Request,
  res: Response
): Promise<void> {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  const server = createMcpServer();
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
  await server.close();
}
```

### 3.8 src/http-server.ts -- Express Entry Point

```typescript
import "dotenv/config";
import cors from "cors";
import express from "express";
import { handleMcpRequest } from "./route-handlers.js";
import { shutdown as shutdownDb } from "./db.js";

const app = express();
const PORT = parseInt(process.env.PORT || "3100");
const MCP_ACCESS_KEY = process.env.MCP_ACCESS_KEY!;

app.use(express.json());
app.use(cors());

app.use("/mcp", (req, res, next) => {
  const provided =
    req.headers["x-brain-key"] as string | undefined ||
    new URL(req.url, `http://${req.headers.host}`).searchParams.get("key");

  if (!provided || provided !== MCP_ACCESS_KEY) {
    res.status(401).json({ error: "Invalid or missing access key" });
    return;
  }
  next();
});

app.all("/mcp", async (req, res) => {
  await handleMcpRequest(req, res);
});

app.get("/health", async (_req, res) => {
  try {
    const { query: dbQuery } = await import("./db.js");
    await dbQuery("SELECT 1");
    res.json({ status: "ok", service: "open-brain-mcp" });
  } catch (err) {
    res.status(503).json({ status: "unhealthy", error: String(err) });
  }
});

const server = app.listen(PORT, "0.0.0.0", () => {
  console.log(`Open Brain MCP server listening on port ${PORT}`);
  console.log(`MCP endpoint: http://0.0.0.0:${PORT}/mcp`);
  console.log(`Health check: http://0.0.0.0:${PORT}/health`);
});

const gracefulShutdown = (signal: string) => {
  console.log(`${signal} received, shutting down...`);
  shutdownDb();
  server.close(() => {
    console.log("Server closed");
    process.exit(0);
  });
};

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
```

### 3.9 Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY tsconfig.json ./
COPY src/ ./src/

RUN npm run build
RUN npm prune --production

EXPOSE 3100

CMD ["node", "dist/http-server.js"]
```

---

## Step 4: Deploy on g2s

### 4.1 Create the Directory Structure

```bash
ssh g2s

sudo mkdir -p /opt/agent-zero/open-brain/{server/src,init-db,pg-conf,pgdata}
```

Copy the files from this guide into the appropriate paths:

```
/opt/agent-zero/open-brain/
├── .env                          # Step 1.2
├── docker-compose.yml            # Step 1.1
├── init-db/
│   ├── 00-pg-hba.sh            # Step 1.3a
│   └── 01-schema.sql            # Step 2
├── pg-conf/
│   └── pg_hba_custom.conf       # Step 1.3a
├── pgdata/                       # (auto-populated by PostgreSQL)
└── server/
    ├── Dockerfile                # Step 3.9
    ├── package.json              # Step 3.2
    ├── tsconfig.json             # Step 3.3
    └── src/
        ├── db.ts                 # Step 3.4
        ├── openrouter.ts         # Step 3.5
        ├── mcp-server.ts         # Step 3.6
        ├── route-handlers.ts     # Step 3.7
        └── http-server.ts        # Step 3.8
```

### 4.2 Build and Start

```bash
cd /opt/agent-zero/open-brain
docker compose up -d --build
```

### 4.3 Verify

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

You should see a response listing all four tools: `search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`.

### 4.4 Verify Cross-Network Connectivity

Once the services are confirmed healthy, test reachability from the other network segments:

```bash
# From an agent container (172.23.88.x -> 172.23.90.x via macvlan)
docker exec -it agent0-1 curl http://172.23.90.2:3100/health

# From a LAN workstation (via DD-WRT static route)
psql -h 172.23.90.1 -U openbrain -d open_brain -c "SELECT 1"
curl http://172.23.90.2:3100/health
```

---

## Step 5: Connect MCP Clients

### 5.1 From Agent Zero Instances (on g2s)

All agents on 172.23.88.x can reach the MCP server directly via the services segment macvlan IP:

```
URL: http://172.23.90.2:3100/mcp?key=<your-access-key>
```

Agents can also connect directly to PostgreSQL if needed (e.g., for bulk operations):

```
postgresql://openbrain:<password>@172.23.90.1:5432/open_brain
```

### 5.2 From Cursor (Local Workstation)

Your workstation reaches 172.23.90.x via the DD-WRT route (Step 1.3c). Add to your MCP configuration (`.cursor/mcp.json` or workspace `mcp.json`):

```json
{
  "mcpServers": {
    "open-brain": {
      "url": "http://172.23.90.2:3100/mcp?key=<your-access-key>"
    }
  }
}
```

If your workstation can't reach g2s directly, use the `mcp-remote` bridge:

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

### 5.3 From Claude Desktop

Settings -> Connectors -> Add custom connector:
- Name: `Open Brain`
- URL: `http://172.23.90.2:3100/mcp?key=<your-access-key>`

### 5.4 From ChatGPT

Follow the standard OB1 instructions for ChatGPT but use your self-hosted URL instead of the Supabase one.

---

## Step 6: Integration with Agent-Matrix Infrastructure

### 6.1 Shared Brain vs Per-Agent Brains

The default setup creates a single shared brain. If you want per-agent isolation:

**Option A: Schema-based isolation** -- create a schema per agent:

```sql
CREATE SCHEMA agent0_1;
CREATE SCHEMA agent0_2;
-- ... replicate the thoughts table + functions in each schema
```

Then pass `BRAIN_SCHEMA=agent0_1` to each agent's MCP config and prefix table names.

**Option B: Metadata-based isolation** -- add an `agent_id` field to the metadata:

```sql
ALTER TABLE thoughts ADD COLUMN agent_id TEXT;
CREATE INDEX thoughts_agent_id_idx ON thoughts (agent_id);
```

Then filter by agent_id in each tool. This is simpler and lets you query across agents when needed.

**Option C: Shared brain (recommended)** -- all agents share one knowledge base. The `source` metadata field already tracks which MCP client captured each thought. This is the most useful for a collective knowledge system.

### 6.2 Adding to startup-services.sh

If you want agent containers to verify brain connectivity on boot, add a health check to the agent startup script:

```bash
# Check Open Brain availability
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

### 6.3 Backup

Add PostgreSQL backups to your maintenance routine:

```bash
# Add to cron on g2s
0 3 * * * docker exec open-brain-db pg_dump -U openbrain open_brain | gzip > /opt/agent-zero/backups/open-brain-$(date +\%Y\%m\%d).sql.gz
```

---

## Appendix A: Supabase-to-PostgreSQL Translation Reference

For anyone extending the server with new tools, here's how Supabase JS client calls translate to raw SQL:

| Supabase JS | PostgreSQL (pg) |
|---|---|
| `supabase.from("thoughts").select("*")` | `query("SELECT * FROM thoughts")` |
| `supabase.from("thoughts").insert({ content, embedding, metadata })` | `query("INSERT INTO thoughts (content, embedding, metadata) VALUES ($1, $2::vector, $3::jsonb)", [content, vectorStr, JSON.stringify(metadata)])` |
| `supabase.from("thoughts").select("*", { count: "exact", head: true })` | `query("SELECT COUNT(*) AS total FROM thoughts")` |
| `supabase.rpc("match_thoughts", { query_embedding, match_threshold, ... })` | `query("SELECT * FROM match_thoughts($1::vector, $2, $3, $4::jsonb)", [...])` |
| `.order("created_at", { ascending: false })` | `ORDER BY created_at DESC` |
| `.limit(10)` | `LIMIT 10` |
| `.contains("metadata", { type: "task" })` | `WHERE metadata @> '{"type":"task"}'::jsonb` |
| `.gte("created_at", date.toISOString())` | `WHERE created_at >= $1` |

## Appendix B: OpenRouter Model Alternatives

The embedding model and metadata extraction model can be swapped by changing the model strings in `openrouter.ts`:

| Purpose | Default | Alternatives |
|---|---|---|
| Embeddings | `openai/text-embedding-3-small` (1536d) | `openai/text-embedding-3-large` (3072d -- requires schema change) |
| Metadata | `openai/gpt-4o-mini` | `anthropic/claude-3.5-haiku`, `google/gemini-2.0-flash` |

If you change embedding dimensions, update the `vector(1536)` declarations in the schema to match.

## Appendix C: Future Enhancements

- **Matrix integration**: Capture thoughts from Matrix room messages via the existing matrix-bot infrastructure
- **Bulk import**: Add a `/import` REST endpoint for batch thought ingestion
- **Watchdog integration**: Add the open-brain health check to the existing agent watchdog
- **TLS**: Add Caddy in front of the MCP server for HTTPS, using the existing step-ca PKI
- **Multi-tenant auth**: Replace the shared access key with per-agent JWT tokens via Keycloak
