# AGENTS.md -- Agent Matrix

Decentralized, federated AI agent platform where each agent has a real Matrix identity (Continuwuity homeserver + Caddy TLS), with Agent Zero as the reasoning stack. Humans use normal Matrix clients. On v0.94, matrix-mcp-server-r2 0.4.0 serves the MCP tools and the inbound Matrix replies. matrix-bot-rust stays installed and stopped.

Not production-ready -- lab for agentic architectures on open standards.

## Stack

| Layer | Technology |
|-------|------------|
| Agent runtime | Agent Zero (Docker) |
| Homeserver | Continuwuity (Rust, per-agent instance) |
| Reverse proxy | Caddy (per-agent TLS) |
| Federation hub | Synapse on K8s (public) |
| MCP server | TypeScript (Express, matrix-js-sdk, OAuth/Keycloak) |
| Matrix bot | matrix-mcp-server-r2 0.4.0 when BOT_ENABLED=true; matrix-bot-rust stays installed and stopped |
| Networking | macvlan Docker, OpenVPN, DD-WRT edge router |
| Orchestration | Docker Compose (agents), K8s (federation/monitoring) |
| Automation | Bash, Python helpers |

## Project Structure

```
docs/                         -- Operator and design docs (peer of multi-instance-deploy)
  operations-manual.md        -- Step-by-step deploy procedures
  upgrade-to-v0.93.md         -- v0.92 to v0.93 plan for matrix-mcp-server-r2 0.3.1
  upgrade-to-v0.94.md         -- v0.93 to v0.94 plan for matrix-mcp-server-r2 0.4.0
  agent-matrix-design.md      -- Living architecture doc
  theory-of-operations.md     -- Deeper ops theory
  legacy-docs/                -- Retired Synapse-era material
  sessions/                   -- Captured terminal and debug sessions
multi-instance-deploy/
  create-instance.sh          -- Wrapper for the Python provisioner (plugged agent0-N)
  templates/
    docker-compose.yml.template
    Caddyfile.template
    matrix-mcp-server/        -- TypeScript MCP server (has its own package.json, CLAUDE.md)
    matrix-bot/               -- Rust bot + legacy Python bot
    scripts/                  -- Fleet/sync/switch/smoke-test scripts
    clear-rules/              -- CLEAR writing skill source
    clear-rules.zip           -- Agent Zero skill import (Settings, Skills, Import)
    repo-spec-audit/          -- Read-only repo + Spec Kit audit skill (SKILL.md, install.sh)
  scripts/                    -- Host-side helpers, including upgrade-v0.92-to-v0.93.sh and upgrade-v0.93-to-v0.94.sh
migration/
  tarnover-refresh/           -- Host OS refresh runbook + scripts
  README-agent0-1-g2s.md     -- Agent relocation runbook
networking/                   -- Router/OpenVPN/DNS docs, DD-WRT config
```

## Key Commands

```bash
# Provision a plugged agent (triplet + matrix-mcp-server-r2 0.4.0, run_bot stopped)
./multi-instance-deploy/create-instance.sh <instance-number>
am-ctl create <instance-number>

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
- **matrix-mcp-server-r2 (Rust)**: Sibling repo. v0.94 uses image tag `0.4.0` as the only Matrix client. `run_bot` stays stopped.

## Boundaries

### Always Do
- Use `create-instance.sh` or `am-ctl create` for new agents. Both call `multi-instance-deploy/am-ctl/amctl/provision.py`. Do not hand-build triplets and do not run `finalize-instance.sh` afterward.
- Consult `docs/operations-manual.md` before deploying
- Run collect scripts before migration restore scripts
- Keep deterministic IP/port scheme consistent with instance numbers

### Ask First
- Before modifying `create-instance.sh` or `amctl/provision.py` (affects all future instances)
- Before changing Caddy or Continuwuity templates (affects existing agents)
- Before running `destroy-and-rebuild.sh` scripts

### Never Do
- Commit real credentials (some examples show rotated secrets -- keep it that way)
- Manually assign IPs outside the deterministic scheme
- Run restore scripts without first running the matching collect script

## Key Documentation
- `docs/agent-matrix-design.md` -- Architecture (v5.1+)
- `docs/operations-manual.md` -- Deploy procedures
- `docs/upgrade-to-v0.93.md` -- v0.92 to v0.93 upgrade plan
- `docs/upgrade-to-v0.94.md` -- v0.93 to v0.94 upgrade plan (matrix-mcp-server-r2 0.4.0)
- `docs/theory-of-operations.md` -- Ops theory
- `migration/tarnover-refresh/RUNBOOK.md` -- Host refresh runbook
