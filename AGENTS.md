# AGENTS.md -- Agent Matrix

Decentralized, federated AI agent platform where each agent has a real Matrix identity (Continuwuity homeserver + Caddy TLS), with Agent Zero as the reasoning stack. Humans use normal Matrix clients; agents communicate via matrix-bot (inbound) and matrix-mcp-server (MCP tools for Cursor/IDEs).

Not production-ready -- lab for agentic architectures on open standards.

## Stack

| Layer | Technology |
|-------|------------|
| Agent runtime | Agent Zero (Docker) |
| Homeserver | Continuwuity (Rust, per-agent instance) |
| Reverse proxy | Caddy (per-agent TLS) |
| Federation hub | Synapse on K8s (public) |
| MCP server | TypeScript (Express, matrix-js-sdk, OAuth/Keycloak) |
| Matrix bot | Rust (primary), Python (legacy) |
| Networking | macvlan Docker, OpenVPN, DD-WRT edge router |
| Orchestration | Docker Compose (agents), K8s (federation/monitoring) |
| Automation | Bash, Python helpers |

## Project Structure

```
multi-instance-deploy/
  create-instance.sh          -- Provisions agent triplet (Agent Zero + Continuwuity + Caddy)
  docs/
    operations-manual.md      -- Step-by-step deploy procedures
    agent-matrix-design.md    -- Living architecture doc
    theory-of-operations.md   -- Deeper ops theory
  templates/
    docker-compose.yml.template
    Caddyfile.template
    matrix-mcp-server/        -- TypeScript MCP server (has its own package.json, CLAUDE.md)
    matrix-bot/               -- Rust bot + legacy Python bot
    scripts/                  -- Fleet/sync/switch/smoke-test scripts
  scripts/                    -- Host-side helpers (destroy-and-rebuild, fix-agentX-services)
migration/
  tarnover-refresh/           -- Host OS refresh runbook + scripts
  README-agent0-1-g2s.md     -- Agent relocation runbook
networking/                   -- Router/OpenVPN/DNS docs, DD-WRT config
legacy-docs/                  -- Retired Synapse-era material
```

## Key Commands

```bash
# Provision a new agent instance (triplet: Agent Zero + Continuwuity + Caddy)
./multi-instance-deploy/create-instance.sh <instance-number>

# MCP server (inside templates/matrix-mcp-server/)
npm install && npm run build
npm run dev                    # Dev with hot reload
ENABLE_OAUTH=true npm run dev  # Dev with OAuth

# Rust bot build
cd multi-instance-deploy/templates/matrix-bot/rust && cargo build --release


```

## Architecture Decisions

- **One homeserver per agent**: Continuwuity + Caddy triplet with deterministic IPs/ports from instance number (172.23.88.N / 172.23.89.N)
- **macvlan networking**: Docker containers appear as real LAN devices; per-agent /32 routes
- **MCP tool tiers**: tier0 (read: rooms, messages, users) vs tier1 (write: room-admin, messaging) -- capability layering
- **Federation via public K8s Synapse**: Private LAN agents federate through OpenVPN to public hub
- **matrix-mcp-server-r2 (Rust)**: Sibling repo, recommended for production; this repo's TS MCP is the reference

## Boundaries

### Always Do
- Use `create-instance.sh` for new agents -- don't hand-build triplets
- Consult `docs/operations-manual.md` before deploying
- Run collect scripts before migration restore scripts
- Keep deterministic IP/port scheme consistent with instance numbers

### Ask First
- Before modifying `create-instance.sh` (affects all future instances)
- Before changing Caddy or Continuwuity templates (affects existing agents)
- Before running `destroy-and-rebuild.sh` scripts

### Never Do
- Commit real credentials (some examples show rotated secrets -- keep it that way)
- Manually assign IPs outside the deterministic scheme
- Run restore scripts without first running the matching collect script

## Key Documentation
- `multi-instance-deploy/docs/agent-matrix-design.md` -- Architecture (v5.1+)
- `multi-instance-deploy/docs/operations-manual.md` -- Deploy procedures
- `multi-instance-deploy/docs/theory-of-operations.md` -- Ops theory
- `migration/tarnover-refresh/RUNBOOK.md` -- Host refresh runbook
