import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { query } from "./db.js";
import { getEmbedding, extractMetadata } from "./openrouter.js";

const CITATION_BASE_URL =
  process.env.OPEN_BRAIN_CITATION_BASE_URL || "https://openbrain.local/thoughts";

function thoughtTitle(content: string, createdAt?: string): string {
  const firstLine = content.replace(/\s+/g, " ").trim().slice(0, 80);
  const datePrefix = createdAt ? new Date(createdAt).toLocaleDateString() : "Open Brain";
  return firstLine ? `${datePrefix} - ${firstLine}` : `${datePrefix} thought`;
}

function thoughtUrl(id: string): string {
  return `${CITATION_BASE_URL.replace(/\/$/, "")}/${id}`;
}

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
      annotations: {
        readOnlyHint: true,
      },
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
            `ID: ${t.id}`,
            `URL: ${thoughtUrl(t.id)}`,
            `Title: ${thoughtTitle(t.content, t.created_at)}`,
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
      annotations: {
        readOnlyHint: true,
      },
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
          SELECT id, content, metadata, created_at
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
          return `${i + 1}. [${new Date(t.created_at).toLocaleDateString()}] (${m.type || "??"}${tags ? " - " + tags : ""})\n   ${thoughtTitle(t.content, t.created_at)}\n   ${thoughtUrl(t.id)}\n   ${t.content}`;
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
      annotations: {
        readOnlyHint: true,
      },
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
          "SELECT id, content, metadata, created_at FROM thoughts ORDER BY created_at DESC"
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

        if (verbose) {
          lines.push("", `Citation base URL: ${CITATION_BASE_URL}`);
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
      annotations: {
        readOnlyHint: false,
        openWorldHint: false,
        destructiveHint: false,
        idempotentHint: false,
      },
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
