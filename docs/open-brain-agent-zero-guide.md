# Open Brain for Agent Zero -- Self-Hosted Persistent Memory

## Overview

[Open Brain (OB1)](https://github.com/NateBJones-Projects/OB1) is an open-source "second brain" MCP server that gives AI agents persistent, searchable memory. The upstream project uses Supabase for its database layer. This guide replaces Supabase with a self-hosted **PostgreSQL 16 + pgvector** stack running in Docker, then connects it to **Agent Zero** so your agents can remember things across sessions.

The result: a fully local knowledge base your agents can search semantically, capture thoughts into, and query for statistics -- all without depending on Supabase or any cloud database.

### What OB1 Provides (and What We're Replacing)

| OB1 / Supabase Component | Self-Hosted Replacement |
|---|---|
| Supabase PostgreSQL | **PostgreSQL 16 + pgvector** Docker container |
| Supabase JS Client (`.from()`, `.rpc()`) | **node-postgres (`pg`)** with direct SQL |
| Supabase Edge Function (Deno runtime) | **Node.js / Express** server |
| Supabase Row Level Security | PostgreSQL roles + application-level access key |
| Supabase PostgREST (auto REST API) | Not needed -- MCP server talks to PG directly |
| OpenRouter (embeddings + LLM) | **Kept as-is** -- external API, no Supabase dependency |

### Why Pair Open Brain with Agent Zero?

- **Persistent memory** -- thoughts survive across agent restarts and conversations
- **Semantic search** -- agents find relevant memories by meaning, not keyword matching
- **Shared knowledge** -- multiple Agent Zero instances can share one brain
- **Self-hosted** -- your data stays on your infrastructure, no cloud dependencies
- **Low cost** -- OpenRouter embeddings cost fractions of a cent per thought

---

## Architecture

```
  Agent Zero (Docker)             Open Brain Stack (Docker)
  ┌──────────────┐               ┌────────────────────────────────────┐
  │              │               │  open-brain-mcp    localhost:3100  │
  │  Agent Zero  │──── HTTP ────►│  (Node.js/Express MCP server)      │
  │  instance(s) │               │       │ brain-net (bridge)         │
  │              │               │       ▼                            │
  └──────────────┘               │  open-brain-db     localhost:5433  │
                                 │  (PostgreSQL 16 + pgvector)        │
                                 └────────────────────────────────────┘
                                                │
                                                ▼
                                      OpenRouter API (external)
                                      - Embeddings (text-embedding-3-small)
                                      - Metadata extraction (gpt-4o-mini)
```

The two Open Brain containers communicate over a private Docker bridge network (`brain-net`). The MCP server is exposed on port 3100 and PostgreSQL on port 5433 (mapped from the container's 5432) for external access. Agent Zero connects to the MCP server over HTTP.

---

## Prerequisites

- **Docker** and **Docker Compose** (v2) installed
- An **OpenRouter API key** -- sign up at [openrouter.ai](https://openrouter.ai). $5 in credits will last months for embedding and metadata extraction calls.
- **Agent Zero** running (Docker or native). See the [Agent Zero documentation](https://www.agent-zero.ai/p/docs/) for installation.

---

## Step 1: Deploy Open Brain

### 1.1 Docker Compose

Create the file `./open-brain/docker-compose.yml`:

```yaml
name: open-brain

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: open-brain-db
    hostname: open-brain-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: open_brain
      POSTGRES_USER: openbrain
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./pgdata:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d:ro
    ports:
      - "5433:5432"
    networks:
      - brain-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openbrain -d open_brain"]
      interval: 10s
      timeout: 5s
      retries: 5

  open-brain-mcp:
    build:
      context: ./server
      dockerfile: Dockerfile
    container_name: open-brain-mcp
    hostname: open-brain-mcp
    restart: unless-stopped
    environment:
      DATABASE_URL: postgres://openbrain:${POSTGRES_PASSWORD}@open-brain-db:5432/open_brain
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      MCP_ACCESS_KEY: ${MCP_ACCESS_KEY}
      PORT: "3100"
    ports:
      - "3100:3100"
    networks:
      - brain-net
    depends_on:
      postgres:
        condition: service_healthy

networks:
  brain-net:
    driver: bridge
```

The two containers share a private `brain-net` bridge so the MCP server can resolve the database by Docker hostname (`open-brain-db`). Port 3100 is exposed for MCP client connections and port 5433 maps to PostgreSQL for direct database access if needed.

### 1.2 Environment File

Create `./open-brain/.env`:

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

Paste the generated values into `.env`. Get your OpenRouter API key from [openrouter.ai/keys](https://openrouter.ai/keys).

### 1.3 Directory Structure

Create the directory tree:

```bash
mkdir -p ./open-brain/{server/src,init-db,pgdata}
```

The final layout will be:

```
./open-brain/
├── .env                          # Step 1.2
├── docker-compose.yml            # Step 1.1
├── init-db/
│   └── 01-schema.sql            # Step 2
├── pgdata/                       # (auto-populated by PostgreSQL)
└── server/
    ├── Dockerfile                # Step 3 (Dockerfile)
    ├── package.json              # Step 3 (package.json)
    ├── tsconfig.json             # Step 3 (tsconfig.json)
    └── src/
        ├── db.ts                 # Step 3 (db.ts)
        ├── openrouter.ts         # Step 3 (openrouter.ts)
        ├── mcp-server.ts         # Step 3 (mcp-server.ts)
        ├── route-handlers.ts     # Step 3 (route-handlers.ts)
        └── http-server.ts        # Step 3 (http-server.ts)
```

---

## Step 2: Database Schema

This creates the `thoughts` table with pgvector support and a semantic search function. PostgreSQL automatically executes `.sql` files placed in `docker-entrypoint-initdb.d` on first container start.

Create the file `./open-brain/init-db/01-schema.sql`:

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

For subsequent schema changes after the initial deployment, apply them manually via `psql` or use a migration tool -- `docker-entrypoint-initdb.d` only runs on first start when the data directory is empty.

---

## Step 3: MCP Server

The MCP server is a Node.js / Express application that exposes four tools via the Model Context Protocol. It talks directly to PostgreSQL using `pg` (node-postgres) and calls OpenRouter for embeddings and metadata extraction. Client authentication uses an `x-brain-key` header or `?key=` query parameter.

### 3.1 package.json

Create `./open-brain/server/package.json`:

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

### 3.2 tsconfig.json

Create `./open-brain/server/tsconfig.json`:

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

### 3.3 src/db.ts

Create `./open-brain/server/src/db.ts`:

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

### 3.4 src/openrouter.ts

Create `./open-brain/server/src/openrouter.ts`:

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

### 3.5 src/mcp-server.ts

Create `./open-brain/server/src/mcp-server.ts`:

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
      inputSchema: {},
    },
    async () => {
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

### 3.6 src/route-handlers.ts

Create `./open-brain/server/src/route-handlers.ts`:

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

### 3.7 src/http-server.ts

Create `./open-brain/server/src/http-server.ts`:

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

app.post("/mcp", async (req, res) => {
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

app.all("/mcp", (_req, res) => {
  res.status(405).json({ error: "Method not allowed. Use POST for MCP." });
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

### 3.8 Dockerfile

Create `./open-brain/server/Dockerfile`:

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

## Step 4: Build and Verify

### 4.1 Build and Start

```bash
cd ./open-brain
docker compose up -d --build
```

### 4.2 Verify Services

```bash
# Check both containers are running and healthy
docker compose ps
```

You should see both `open-brain-db` (healthy) and `open-brain-mcp` (running).

### 4.3 Verify Database Schema

```bash
docker exec -it open-brain-db psql -U openbrain -d open_brain \
  -c "\dt" -c "\df match_thoughts"
```

You should see the `thoughts` table and the `match_thoughts` function listed.

### 4.4 Verify MCP Server Health

```bash
curl http://localhost:3100/health
```

Expected response:

```json
{"status":"ok","service":"open-brain-mcp"}
```

### 4.5 Test MCP Tool Listing

```bash
curl -X POST http://localhost:3100/mcp \
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

---

## Step 5: Connect to Agent Zero

### 5.1 Via Agent Zero Settings UI

Agent Zero supports external MCP servers configured through its settings interface. See the [Agent Zero MCP documentation](https://www.agent-zero.ai/p/docs/mcp-a2a/#mcp-setup) for full details.

1. Click **Settings** in the Agent Zero sidebar
2. Navigate to the **MCP/A2A** tab
3. Click on **External MCP Servers**
4. Click the **Open** button to access the JSON configuration editor
5. Add the following configuration:

```json
{
  "mcpServers": {
    "open-brain": {
      "url": "http://<DBHOST>:3100/mcp",
      "headers": {
        "x-brain-key": "your-mcp-access-key-here"
      }
    }
  }
}
```

6. Click **Save** and verify the server shows a green connected status with 4 tools available.

**What to use for HOST:**

| Agent Zero Setup | DBHOST Value |
|---|---|
| Docker on **macOS or Windows** | `host.docker.internal` |
| Docker on **Linux**, same Docker network as Open Brain | `open-brain-mcp` (container hostname) |
| Docker on **Linux**, different Docker network | The host machine's IP address (e.g., `192.168.1.100`) |
| Native (non-Docker) Agent Zero on same machine | `localhost` |
| Agent Zero on a different machine | The Open Brain host's LAN IP address |

**Docker networking note (Linux):** If Agent Zero and Open Brain are in separate Docker Compose projects, the simplest approach is to add Agent Zero's network as an external network in the Open Brain compose file (or vice versa), or use the host machine's IP. Alternatively, you can attach both to a shared external network:

```bash
docker network create shared-mcp
```

Then add `shared-mcp` as an external network in both Compose files and use the container hostname (`open-brain-mcp`) as the HOST.

### 5.2 Using Open Brain Tools

Once connected, Agent Zero automatically discovers the four Open Brain tools. You don't need to call them by name -- just use natural language and Agent Zero will pick the right tool.

| What You Say | Tool Used |
|---|---|
| "Remember that the deploy deadline is next Friday" | `capture_thought` |
| "What do I know about Kubernetes networking?" | `search_thoughts` |
| "Show me my recent notes from this week" | `list_thoughts` |
| "How many thoughts have I captured? What topics come up most?" | `thought_stats` |
| "Save this: We decided to use PostgreSQL instead of MongoDB for the user service" | `capture_thought` |
| "What decisions have we made about the database?" | `search_thoughts` |
| "List all my ideas from the last 30 days" | `list_thoughts` (with `days: 30`, `type: idea`) |
| "Who have I mentioned most in my notes?" | `thought_stats` |

Each captured thought is automatically:
- **Embedded** using OpenRouter's `text-embedding-3-small` model (1536-dimensional vector)
- **Enriched** with extracted metadata: type classification, topic tags, people mentioned, action items, and dates
- **Stored** in PostgreSQL with full-text and vector indexes for fast retrieval

### 5.3 Connecting Multiple Agents

If you run multiple Agent Zero instances, all of them can connect to the same Open Brain server. Each instance gets the same four tools and reads from / writes to the same `thoughts` table, creating a shared knowledge base.

To connect multiple instances:

1. Configure each Agent Zero instance with the same Open Brain MCP server JSON (Step 5.1)
2. All agents share the same `MCP_ACCESS_KEY` for authentication
3. Thoughts captured by any agent are immediately searchable by all others

The `source: "mcp"` field in each thought's metadata tracks that it came from an MCP client. If you need to identify which agent captured a thought, you can extend the metadata extraction or add a wrapper that tags thoughts with an agent identifier.

> **Note:** If you are running Agent Zero in a multi-agent infrastructure with advanced networking requirements (macvlan, custom subnets, dedicated service segments), see the companion document [agent-matrix-open-brain-design.md](agent-matrix-open-brain-design.md) for configuration specific to that environment.

---

## Step 6: Backup and Restore

### 6.1 Manual Backup

```bash
docker exec open-brain-db pg_dump -U openbrain open_brain | gzip > open-brain-backup-$(date +%Y%m%d).sql.gz
```

### 6.2 Scheduled Backups

Add a cron job for daily backups at 3:00 AM:

```bash
crontab -e
```

Add this line:

```
0 3 * * * docker exec open-brain-db pg_dump -U openbrain open_brain | gzip > /path/to/backups/open-brain-$(date +\%Y\%m\%d).sql.gz
```

Replace `/path/to/backups/` with your preferred backup directory.

### 6.3 Restore from Backup

```bash
# Stop the MCP server to prevent writes during restore
docker compose stop open-brain-mcp

# Restore the database
gunzip -c open-brain-backup-20260324.sql.gz | docker exec -i open-brain-db psql -U openbrain open_brain

# Restart the MCP server
docker compose start open-brain-mcp
```

For a full restore into a fresh database (e.g., after deleting `pgdata/`):

```bash
# Start only postgres
docker compose up -d postgres

# Wait for healthy status
docker compose ps

# Restore
gunzip -c open-brain-backup-20260324.sql.gz | docker exec -i open-brain-db psql -U openbrain open_brain

# Start the MCP server
docker compose up -d open-brain-mcp
```

### 6.4 Backup Best Practices

- **Daily logical backups** at minimum (the cron job above)
- **Retain at least 7 days** of backups -- add cleanup to your cron: `find /path/to/backups/ -name "open-brain-*.sql.gz" -mtime +7 -delete`
- **Test restores periodically** -- a backup you've never restored from is a backup you can't trust
- **For production deployments**: consider WAL archiving for point-in-time recovery. This requires mounting a WAL archive volume and configuring `archive_mode = on` in `postgresql.conf`. See the [PostgreSQL WAL documentation](https://www.postgresql.org/docs/16/continuous-archiving.html) for details.

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

## Appendix C: Connecting Other MCP Clients

Open Brain is a standard MCP server accessible over HTTP. Any MCP-compatible client can connect to it.

### Cursor

Add to your MCP configuration (`.cursor/mcp.json` or workspace `mcp.json`):

```json
{
  "mcpServers": {
    "open-brain": {
      "url": "http://localhost:3100/mcp?key=<your-access-key>"
    }
  }
}
```

If Cursor can't reach the server directly (e.g., it's on a remote host), use the `mcp-remote` bridge:

```json
{
  "mcpServers": {
    "open-brain": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://HOST:3100/mcp",
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

### Claude Desktop

Settings > Connectors > Add custom connector:
- **Name:** `Open Brain`
- **URL:** `http://HOST:3100/mcp?key=<your-access-key>`

Replace `HOST` with `localhost` if running on the same machine, or the appropriate IP/hostname.

### ChatGPT

Follow the standard OB1 instructions for ChatGPT but use your self-hosted URL (`http://HOST:3100/mcp?key=<your-access-key>`) instead of the Supabase-backed URL.
