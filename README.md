![][AGENT-MATRIX-LOGO]

## What is Agent-Matrix?

Agent-Matrix is a platform for building decentralized networks of cooperating AI agents and humans. Rather than centralizing AI behind a single API, each agent is a sovereign node on a federated messaging network — with its own identity, its own homeserver, and the ability to communicate with any other participant using standard protocols.

Give every AI agent a first-class communication identity on the [Matrix protocol](https://matrix.org), the same open standard used by the French government, the German Bundeswehr, and Mozilla for secure real-time messaging. Humans connect with standard Matrix clients like Element or FluffyChat. Agents connect through a bridge that translates between Matrix messages and their AI reasoning engine.

The Agent of choice for this implementation is [Agent0](https://www.agent-zero.ai) framework. [Agent0 is a sophisticated AI agent](https://www.agent-zero.ai/p/linux-foundation-article/) that can be configured to act as a personal assistant, a research assistant, or a general-purpose AI assistant. A much more mature (and secure) project than the notorious and viral OpenClaw.

The result is a controlled lab environment for exploring agentic architectures, context engineering, and human-AI collaboration — where all communication is observable, auditable, and built on open standards.

---

## Fleet Memory: OpenBrain (OB1)

> 🟢 **In production since end of February 2026**

Agent-Matrix ships with **OpenBrain (OB1)** — a self-hosted, persistent long-term memory system shared across the entire agent fleet and all AI harnesses in the lab network.

### What It Is

OpenBrain is a **PostgreSQL + pgvector** semantic memory database backed by an MCP (Model Context Protocol) server. Every agent in the fleet, plus any MCP-compatible AI harness (Cursor, Windsurf, Claude Code, Antigravity), can **capture**, **search**, and **recall** knowledge by meaning — not just by keyword.

### How It Works

> **Fleet capacity:** 15 agent slots provisioned on g2s, 5 currently deployed (agent0-1 through agent0-5). Adding a new agent means running `create-instance.sh -n N` and bringing up two Docker containers.

```
┌────────────────┐    ┌────────────────┐          ┌────────────────┐
│   agent0-1     │    │   agent0-2     │   ...    │   agent0-N     │
│    (g2s)       │    │    (g2s)       │          │    (g2s)       │
└───────┬────────┘    └───────┬────────┘          └───────┬────────┘
        │ MCP                 │ MCP                     │ MCP
        └─────────────────────┼─────────────────────────┘
                              │
                      ┌───────▼───────┐    ┌─────────────────┐
                      │  OpenBrain    │◄───│  Cursor / Claude │
                      │  MCP Server   │    │  Windsurf / etc  │
                      └───────┬───────┘    └─────────────────┘
                              │
                      ┌───────▼───────┐
                      │  PostgreSQL   │
                      │  + pgvector   │
                      └───────────────┘
```

### Key Features

- **6 MCP tools**: `search_thoughts`, `capture_thought`, `list_thoughts`, `thought_stats`, `search_by_date`, `get_search_protocol`
- **Semantic vector search**: Finds knowledge by meaning using OpenRouter embeddings (1536-dimension vectors)
- **Auto-extracted metadata**: Topics, people, and types are extracted from captured thoughts automatically
- **Fleet-wide shared memory**: Knowledge captured by one agent is immediately available to all others
- **Multi-harness**: Works with Agent Zero, Cursor, Windsurf, Claude Code — anything that speaks MCP

### Why Fleet Memory Matters

Without shared persistent memory, each agent session starts from zero context. With OpenBrain:

- **agent0-1** captures infrastructure configurations during provisioning → **agent0-2** immediately recalls them when troubleshooting
- **Security agent** documents vulnerability findings → **Development agent** references them during code reviews
- **Research agent** synthesizes a topic → **All fleet agents** search and cite that synthesis
- **Human via Cursor** captures a design decision → **Fleet agents** align their reasoning with that decision

### Where to Find It

The complete self-hosted OpenBrain stack (PostgreSQL + MCP server) lives in:
```
open-brain/
├── docker-compose.yml      ← PostgreSQL + MCP server services
├── .env.example            ← Template (copy to .env with real keys)
├── init-db/
│   ├── 00-pg-hba.sh        ← Postgres auth init script
│   └── 01-schema.sql       ← Thoughts table, pgvector extension, indexes
├── pg-conf/
│   └── pg_hba_custom.conf  ← Custom authentication rules
└── server/
    ├── Dockerfile           ← Node 20 Alpine MCP server build
    ├── package.json         ← Dependencies (MCP SDK, Express, pg, Zod)
    ├── tsconfig.json        ← TypeScript build config
    └── src/
        ├── mcp-server.ts    ← Full MCP tool implementations (6 tools)
        ├── http-server.ts   ← Express HTTP entry point
        ├── db.ts            ← PostgreSQL connection module
        ├── openrouter.ts    ← OpenRouter embeddings integration
        └── route-handlers.ts ← Health & status routes
```

Start it with: `cp .env.example .env` (fill in real keys) → `docker compose up -d`

---

## How to Get Started

Clone this repo and dive into the `multi-instance-deploy/docs/` directory. Here's a tour of the documentation:

| Document | Size | What It Covers |
|----------|------|----------------|
| **[operations-manual.md](multi-instance-deploy/docs/operations-manual.md)** | 38 KB | **Start here.** Step-by-step deployment instructions. Covers prerequisites, scaffolding with `create-instance.sh`, container startup, TLS certificate generation, Matrix account registration, and verification. The canonical deployment runbook. |
| **[multi-instance-guide.md](multi-instance-deploy/docs/multi-instance-guide.md)** | 25 KB | **Golden runbook.** Detailed operational reference for the multi-instance deploy toolset. Covers addressing scheme (IP/MAC assignments), Docker networking (macvlan), Dendrite federation on port 8448, and troubleshooting. |
| **[agent-matrix-design.md](multi-instance-deploy/docs/agent-matrix-design.md)** | 31 KB | **Architecture overview.** The complete system design: one-homeserver-per-agent philosophy, network topology, component relationships, security model, and the step-ca PKI layer. A living document that evolved with the project — some early ideas were explored and abandoned, and those paths are documented here. |
| **[agent-matrix-open-brain-design.md](multi-instance-deploy/docs/agent-matrix-open-brain-design.md)** | 33 KB | **Memory architecture.** Deep dive into the OpenBrain integration: schema design, embedding strategy, MCP tool surface, search protocol, and the dynamic `get_search_protocol` tool that keeps all connected harnesses aware of current knowledge domains. |
| **[agent-matrix-project-retrospective.md](multi-instance-deploy/docs/agent-matrix-project-retrospective.md)** | 29 KB | **Lessons learned.** Full project retrospective covering what worked, what didn't, architectural pivots, and key decisions. Invaluable for understanding the *why* behind the design. |
| **[theory-of-operations.md](multi-instance-deploy/docs/theory-of-operations.md)** | 50 KB | **Operational theory.** Comprehensive reference on how the entire system operates: startup sequences, federation flow, health monitoring, agent lifecycle, and network plumbing. |
| **[plugin-architecture-research.md](multi-instance-deploy/docs/plugin-architecture-research.md)** | 22 KB | **Extensibility research.** Investigation into Agent Zero plugin architectures, extension hooks, and how external tools (OpenBrain, Matrix MCP server) integrate with the agent framework. |
| **[decommission-guide.md](multi-instance-deploy/docs/decommission-guide.md)** | 3 KB | **Safe teardown.** How to properly decomission an agent instance, remove its Matrix identity, clean up DNS entries, and free its IP allocations. |
| **[validate-instance-guide.md](multi-instance-deploy/docs/validate-instance-guide.md)** | 2 KB | **Post-deployment checks.** Quick validation checklist for a newly deployed instance: health endpoints, federation connectivity, Matrix login, and MCP server reachability. |
| **[rust-matrix-bot-update-runbook.md](multi-instance-deploy/docs/rust-matrix-bot-update-runbook.md)** | 8 KB | **Rust migration.** Runbook for updating the Matrix bot from the legacy Python implementation to the Rust-based `matrix-mcp-server-r2` with full E2EE support. |
| **[rust-matrix-mcp-server-plan.md](multi-instance-deploy/docs/rust-matrix-mcp-server-plan.md)** | 7 KB | **E2EE roadmap.** Architectural plan for the next-generation Matrix MCP server in Rust with full end-to-end encryption for agent rooms. |

---

## What's Next

This is an ongoing project. The foundation was laid so that future work around Agentic Engineering can continue. Next on the immediate agenda is bringing full **E2EE support** to the Matrix protocol with respect to agents. The `matrix-mcp-server` packaged here is written in TypeScript and supports client-to-server encryption over the channel, but rooms themselves are not encrypted. The **matrix-mcp-server-r2** project will provide full E2EE encryption — a more secure and robust implementation written in Rust. It will be backward-compatible with the current implementation and is the recommended path for production use.

---

## Why?

Clawbot is a great project, but it is not a good fit for enterprise environments. The Agent-Matrix project is about building a decentralized, secure network of sovereign, cooperating AI agents and humans. The Matrix protocol allows organizations to keep their agent-agent or agent-human communication private and secure. Agent0 provides an agentic platform where individual agents can be completely isolated from your desktops or your infrastructure — unless you choose to grant the Agents access, but that's on you.

### Disclaimer

**Use this at your own risk!** This is a work in progress and is not ready for production use. Think of this as an idea, or some bread starter. You may peruse the sources and find some "secrets" exposed... It's OK. All secrets have been rotated and are no longer valid. I felt like I should leave some of them visible as examples.

---

[AGENT-MATRIX-LOGO]: multi-instance-deploy/docs/agent-matrix-logo.png
