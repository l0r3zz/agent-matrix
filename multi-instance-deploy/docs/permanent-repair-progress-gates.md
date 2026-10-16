# Permanent Repair Strategy -- Progress Gates

**Date:** 2026-10-15 (revised from 2026-10-10)
**Status:** Planning
**Parent:** [matrix-bot-auth-membership-incident-report.md](matrix-bot-auth-membership-incident-report.md)
**Scope:** Structural hardening + unified fleet management for Agent Matrix

---

## Overview

The one-time repair (2026-10-09) restored all five agents to working state. Three cron-based healthchecks provide interim external hardening. This document defines progress gates for building `am-ctl` (agent-matrix-ctl) -- a unified fleet management platform that replaces the current fragmented script ecosystem with an API-first control plane.

The platform is designed for 1000 agents. The current fleet of 5 is the proving ground.

Each phase has:

- **Preconditions** -- what must be true before starting
- **Deliverables** -- concrete artifacts or code changes
- **Progress gate** -- pass/fail criteria that must all pass before proceeding
- **Risk level** -- LOW / MEDIUM / HIGH / CRITICAL with justification
- **Blast radius** -- what breaks if the phase goes wrong
- **Rollback path** -- how to recover

Phases are ordered by dependency. Later phases depend on earlier ones.

---

## Architectural Decisions

**Decision date:** 2026-10-15

### Platform architecture

`am-ctl` is a FastAPI control-plane server backed by PostgreSQL. A thin CLI client (`am-ctl`) wraps the API. Every fleet operation goes through the API -- the CLI, a future WebGUI, agents themselves, and external orchestrators all consume the same endpoints.

```
                          ┌──────────────────────────────────────────┐
                          │           am-ctl server (FastAPI)        │
                          │                                          │
  am-ctl CLI ────────────►│  /api/v1/agents                         │
  WebGUI (future) ───────►│  /api/v1/health                         │
  Agents (future) ───────►│  /api/v1/reconcile                      │
  External systems ──────►│  /api/v1/deploy                         │
                          │  /api/v1/models                         │
                          │  /api/v1/federation                     │
                          │                                          │
                          │  ┌──────────┐  ┌──────────┐             │
                          │  │ Docker   │  │ Matrix   │             │
                          │  │ client   │  │ HTTP     │             │
                          │  └──────────┘  └──────────┘             │
                          └──────────┬───────────────────────────────┘
                                     │
                          ┌──────────▼───────────────────────────────┐
                          │  PostgreSQL 16 (172.23.90.1:5432)       │
                          │  database: fleet_ops    user: amctl     │
                          │  ┌────────────────────────────────────┐  │
                          │  │ agents          (registry)        │  │
                          │  │ health_checks   (continuous)      │  │
                          │  │ credentials     (fingerprints)    │  │
                          │  │ deployments     (release history) │  │
                          │  │ model_configs   (per-agent LLMs)  │  │
                          │  │ audit_log       (all mutations)   │  │
                          │  │ releases        (bundles + hashes)│  │
                          │  └────────────────────────────────────┘  │
                          │                                          │
                          │  database: open_brain   user: openbrain │
                          │  (unchanged -- Open Brain MCP server)   │
                          └──────────────────────────────────────────┘
```

### Database

Separate `fleet_ops` database on the existing OpenBrain PostgreSQL 16 + pgvector instance (`172.23.90.1:5432`). New user `amctl` with access only to `fleet_ops`. Requires `pg_hba.conf` update to allow `amctl` connections from g2s host and service segment.

### API versioning

All endpoints under `/api/v1/`. Breaking changes get a new version prefix. The CLI pins to the server's API version on connect.

### v1 scope (day-2 operations)

Health, monitoring, credential management, reconciliation, deployment, model configuration, federation. Provisioning (create/destroy/decommission) is deferred to v2.

### v2 scope (provisioning -- future)

Create agent, finalize agent, destroy and rebuild, decommission. These absorb `create-instance.sh`, `finalize-instance.sh`, `destroy-and-rebuild.sh`, `decommission-instance.sh`.

### Technology stack

```
Server:   Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Pydantic v2
CLI:      Python 3.11+, Click, httpx
Database: PostgreSQL 16 on existing OpenBrain instance
Auth:     API key (v1), JWT with role-based access (v2)
```

---

## Phase 1: Platform Foundation

### Why first

Nothing else can happen without the server, database, agent registry, and CLI client. This phase produces the skeleton that every subsequent phase extends.

### Preconditions

- [ ] All five agents passing current completion gates (confirmed 2026-10-09)
- [ ] Cron healthchecks running (token, federation keys, membership)
- [ ] OpenBrain Postgres instance accessible from g2s host
- [ ] No active fleet incidents

### Deliverables

#### Database

- [ ] Create `fleet_ops` database and `amctl` user on OpenBrain Postgres
- [ ] Update `pg_hba_custom.conf` to allow `amctl` connections from g2s host (`172.23.88.254/32`), services segment (`172.23.90.0/24`), and bridge networks (`172.16.0.0/12`)
- [ ] Core schema:

```sql
-- Agent registry: the single source of truth for fleet identity
CREATE TABLE agents (
    id                  SERIAL PRIMARY KEY,
    instance_num        INT UNIQUE NOT NULL,
    name                TEXT UNIQUE NOT NULL,           -- e.g. 'agent0-3'
    matrix_user_id      TEXT UNIQUE NOT NULL,           -- e.g. '@agent0-3:agent0-3-mhs.cybertribe.com'
    homeserver_url      TEXT NOT NULL,                  -- e.g. 'https://172.23.89.3:8448'
    homeserver_fqdn     TEXT NOT NULL,                  -- e.g. 'agent0-3-mhs.cybertribe.com'
    agent_zero_endpoint TEXT NOT NULL DEFAULT 'http://localhost:80',
    bot_runtime         TEXT NOT NULL DEFAULT 'rust',   -- 'rust' | 'python'
    status              TEXT NOT NULL DEFAULT 'active', -- 'active' | 'maintenance' | 'decommissioned'
    release_version     TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

-- Required room memberships per agent
CREATE TABLE required_rooms (
    id          SERIAL PRIMARY KEY,
    agent_id    INT REFERENCES agents(id),
    room_id     TEXT NOT NULL,      -- e.g. '!gahcrWFWAUJQPPkuQy:v-site.net'
    room_name   TEXT,               -- e.g. 'Fleet HQ Clean'
    UNIQUE(agent_id, room_id)
);

-- Credential fingerprints (never store actual credentials)
CREATE TABLE credential_fingerprints (
    id              SERIAL PRIMARY KEY,
    agent_id        INT REFERENCES agents(id),
    domain          TEXT NOT NULL,  -- 'matrix_token' | 'a0_api_key' | 'mcp_config'
    fingerprint     TEXT NOT NULL,  -- SHA-256 prefix
    recorded_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(agent_id, domain)
);

-- Health check results (time-series)
CREATE TABLE health_checks (
    id          BIGSERIAL PRIMARY KEY,
    agent_id    INT REFERENCES agents(id),
    check_type  TEXT NOT NULL,      -- 'identity' | 'membership' | 'a0_auth' | 'matrix_auth' | 'mcp' | 'process' | 'federation'
    status      TEXT NOT NULL,      -- 'pass' | 'fail' | 'warn' | 'timeout'
    detail      JSONB,
    checked_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX health_checks_agent_time ON health_checks(agent_id, checked_at DESC);

-- Audit log (append-only)
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    agent_id    INT REFERENCES agents(id),
    action      TEXT NOT NULL,      -- 'credential_rotate' | 'deploy' | 'restart' | 'reconcile_apply' | ...
    detail      JSONB,
    operator    TEXT NOT NULL,      -- 'cli:geoff' | 'api:webhook' | 'cron:health'
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX audit_log_agent_time ON audit_log(agent_id, created_at DESC);
```

#### Server

- [ ] FastAPI application in `multi-instance-deploy/am-ctl/`
- [ ] Package structure:

```
multi-instance-deploy/am-ctl/
    pyproject.toml
    amctl/
        __init__.py
        app.py                  # FastAPI app, lifespan, middleware
        config.py               # Settings (DB URL, listen addr, API key)
        db.py                   # SQLAlchemy async engine + session
        models/
            __init__.py
            agent.py            # Agent ORM model
            health.py           # HealthCheck ORM model
            audit.py            # AuditLog ORM model
            credential.py       # CredentialFingerprint ORM model
            room.py             # RequiredRoom ORM model
        schemas/
            __init__.py
            agent.py            # Pydantic request/response schemas
            health.py
            common.py           # Pagination, error responses
        routers/
            __init__.py
            agents.py           # CRUD + status for agent registry
            health.py           # Health check endpoints
        services/
            __init__.py
            docker.py           # Docker client (async, talks to containers)
            matrix.py           # Matrix HTTP client (whoami, joined_rooms, invite, join)
            agent_zero.py       # Agent Zero API client (auth probe)
        middleware/
            auth.py             # API key validation
            audit.py            # Auto-audit middleware for mutations
    amctl_cli/
        __init__.py
        cli.py                  # Click CLI: am-ctl agents list, am-ctl status, etc.
        client.py               # httpx client wrapping the API
        output.py               # Table/JSON output formatting
    tests/
        conftest.py
        test_agents.py
        test_health.py
        test_cli.py
    alembic/                    # DB migrations
        env.py
        versions/
    alembic.ini
```

- [ ] API endpoints (Phase 1):
  - `GET  /api/v1/agents` -- list all agents
  - `GET  /api/v1/agents/{name}` -- get agent detail
  - `PUT  /api/v1/agents/{name}` -- update agent metadata
  - `GET  /api/v1/agents/{name}/status` -- live status (container, processes, identity)
  - `GET  /api/v1/status` -- fleet-wide summary (replaces `update-fleet.sh --status`)
  - `GET  /api/v1/health` -- server health
- [ ] Alembic migrations for schema versioning
- [ ] Systemd service file for `am-ctl` server on g2s

#### CLI client

- [ ] `am-ctl agents list` -- tabular fleet overview
- [ ] `am-ctl agents show agent0-3` -- detailed agent info
- [ ] `am-ctl status` -- fleet-wide health summary
- [ ] `am-ctl --output json` -- JSON output for scripting

#### Bootstrap

- [ ] Import existing fleet state into the `agents` table (5 agents from incident report completion gates)
- [ ] Import required rooms (Fleet HQ Clean for all agents)
- [ ] Import credential fingerprints from one-time repair records

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | `fleet_ops` database exists with all tables | `psql -U amctl -d fleet_ops -c '\dt'` shows 5 tables |
| 2 | All 5 agents in the registry | `am-ctl agents list` shows 5 agents with correct identities |
| 3 | Agent status endpoint returns live data | `am-ctl agents show agent0-2` shows container status, process count, identity |
| 4 | API key authentication works | Unauthenticated request returns 401; authenticated returns 200 |
| 5 | Audit log captures mutations | `PUT /api/v1/agents/agent0-2` creates an audit entry |
| 6 | Server runs as systemd service | `systemctl status am-ctl` shows active |
| 7 | CLI output matches direct API call | `am-ctl agents list --output json` equals `curl /api/v1/agents` |
| 8 | No impact on running fleet | All 5 agents still passing completion gates after platform deploy |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **LOW** | Additive -- new service alongside existing scripts; nothing removed yet |
| Blast radius | None | Platform observes the fleet; doesn't control it yet |
| Rollback | `systemctl stop am-ctl`; fleet continues with existing scripts |
| Failure mode | Incorrect registry data could mislead operators; mitigate by verifying imports against live state |

### Caution

The `pg_hba.conf` change requires a Postgres reload. Coordinate with OpenBrain to avoid disrupting its connections. Test the HBA change on a non-production database first.

---

## Phase 2: Health & Continuous Monitoring

### Why second

Replace the three external cron healthchecks with continuous API-driven monitoring. This gives the platform real-time fleet awareness and builds the health state that reconciliation (Phase 4) depends on.

### Script impact

- `fleet-token-healthcheck.sh` -- **absorbed** into continuous Matrix auth monitoring
- `federation-key-refresh.sh` -- **absorbed** into continuous federation monitoring
- `fleet-membership-healthcheck.sh` -- **absorbed** into continuous membership monitoring
- `validate-instance.sh` -- **absorbed** into per-agent health check API

### Preconditions

- [ ] Phase 1 platform running with all 5 agents in registry
- [ ] Server can reach all agent homeservers and containers

### Deliverables

- [ ] **Health check engine**: background async tasks running per-agent checks on configurable intervals
- [ ] **Check types**:
  - `matrix_auth` -- `/whoami` returns 200 with correct identity (replaces `fleet-token-healthcheck.sh`)
  - `identity` -- `/whoami` result matches registry `matrix_user_id`
  - `membership` -- `joined_rooms` includes all `required_rooms` for this agent
  - `a0_auth` -- Agent Zero API probe with canonical credential succeeds
  - `mcp` -- MCP server `/health` endpoint returns healthy
  - `process` -- exactly 1 bot process, supervisord managing it
  - `federation` -- Synapse notary returns valid signing keys (replaces `federation-key-refresh.sh`)
  - `sync_cursor` -- bot sync cursor age within threshold
- [ ] **Failure classification**:
  - `RESTARTABLE` -- process crash, transient timeout -> bounded auto-restart via API
  - `TERMINAL_CONFIG` -- HTTP 401/403, identity mismatch, missing room -> stop bot, alert, no restart
- [ ] **Auto-repair for membership** (replaces `fleet-membership-healthcheck.sh`):
  - Detect missing member -> get admin token -> invite -> accept from agent side
  - Logged as repair action in audit log
- [ ] **Health state tables** (additions to schema):

```sql
-- Current health state (materialized, one row per agent per check type)
CREATE TABLE health_state (
    agent_id    INT REFERENCES agents(id),
    check_type  TEXT NOT NULL,
    status      TEXT NOT NULL,          -- 'pass' | 'fail' | 'warn'
    detail      JSONB,
    since       TIMESTAMPTZ NOT NULL,   -- when this status began
    last_check  TIMESTAMPTZ NOT NULL,
    fail_count  INT DEFAULT 0,          -- consecutive failures
    PRIMARY KEY (agent_id, check_type)
);

-- Alert configuration
CREATE TABLE alert_rules (
    id              SERIAL PRIMARY KEY,
    check_type      TEXT NOT NULL,
    classification  TEXT NOT NULL,      -- 'restartable' | 'terminal_config'
    action          TEXT NOT NULL,      -- 'restart' | 'stop_and_alert' | 'log_only'
    max_retries     INT DEFAULT 3,
    cooldown_secs   INT DEFAULT 300
);
```

- [ ] **API endpoints**:
  - `GET  /api/v1/health/fleet` -- fleet-wide health matrix
  - `GET  /api/v1/health/{agent_name}` -- per-agent health detail
  - `GET  /api/v1/health/{agent_name}/history` -- health check time-series
  - `POST /api/v1/health/{agent_name}/check` -- trigger immediate check
  - `GET  /api/v1/alerts` -- active alerts
  - `POST /api/v1/alerts/{id}/ack` -- acknowledge alert
- [ ] **CLI commands**:
  - `am-ctl health` -- fleet health matrix (colored pass/fail table)
  - `am-ctl health agent0-3` -- detailed health for one agent
  - `am-ctl health --check agent0-3` -- trigger immediate check

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | All 7 check types produce accurate results for all 5 agents | Compare `am-ctl health` with manual verification |
| 2 | Health state persists across server restarts | Restart `am-ctl` server; state still in DB |
| 3 | Membership auto-repair works | Leave a room from agent side; observe auto-repair in audit log within one check cycle |
| 4 | Terminal config failure stops bot and alerts | Corrupt identity; observe `TERMINAL_CONFIG` in health state; bot stays down |
| 5 | Federation key refresh works | Observe fresh signing keys fetched for all agents |
| 6 | Cron healthchecks disabled with no regression | Disable 3 cron scripts; verify platform monitoring catches all issues within its check interval |
| 7 | Health API responds within 500ms for fleet query | `time curl /api/v1/health/fleet` |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **MEDIUM** | Replacing 3 proven cron scripts with new monitoring; gap if the platform goes down |
| Blast radius | Fleet-wide monitoring gap if server crashes; agents themselves keep running |
| Rollback | Re-enable cron scripts; they're idempotent |
| Failure mode | Monitoring stops -> drift goes undetected -> membership loss or auth failure persists longer |

### Mitigation

- Run platform monitoring and cron scripts in parallel for 2 weeks before disabling crons.
- Add a "monitoring heartbeat" -- if the platform hasn't checked an agent in 2x its interval, emit a server-level alert.
- Server crash doesn't affect agents; only monitoring and auto-repair stop.

---

## Phase 3: Credential Authority & Identity

**Repair Strategy Items:** #1 (sole API-credential authority), #2 (separate credential domains), #3 (declarative identity -- now in DB, not manifest files)

### Why third

The credential contamination was the root cause of the incident. With the platform and health monitoring in place, this phase eliminates competing credential writers and validates identity through the API.

### Script impact

- `create-instance.sh` -- **modified** (remove `A0_API_KEY` random generation)
- `finalize-instance.sh` -- **modified** (remove Step 7b duplicate derivation; call API for credential registration)

### Preconditions

- [ ] Phase 2 health monitoring operational
- [ ] Agent Zero `create_auth_token()` derivation algorithm documented and verified
- [ ] Platform can reach Agent Zero API inside each container

### Deliverables

- [ ] **Canonical credential exporter** (`derive-a0-token.sh`): single-source script using `/opt/venv-a0` to call `create_auth_token()` directly. Called by the bot launcher, not by fleet scripts.
- [ ] **Remove** `A0_API_KEY` generation from `create-instance.sh`
- [ ] **Remove** Step 7b derivation from `finalize-instance.sh`
- [ ] **Remove** any other duplicate derivation paths
- [ ] **Runtime secret file**: credential delivered via `/a0/usr/workdir/matrix-bot/.a0-api-key` (mode `0600`, atomic rename)
- [ ] **Rust bot update**: read from secret file as primary; no fallback to `.env`
- [ ] **Credential fingerprint tracking** in platform DB:
  - After each credential derivation, bot reports fingerprint to platform API
  - Platform detects cross-fleet fingerprint collisions (the original incident)
- [ ] **Schema addition**:

```sql
-- Trusted senders for auto-join (used by Phase 7 auto-join)
CREATE TABLE trusted_senders (
    id          SERIAL PRIMARY KEY,
    matrix_user_id  TEXT UNIQUE NOT NULL,
    trust_level     TEXT NOT NULL DEFAULT 'fleet_member'  -- 'admin' | 'fleet_member'
);
```

- [ ] **API endpoints**:
  - `GET  /api/v1/agents/{name}/credentials` -- credential fingerprints (never values)
  - `POST /api/v1/agents/{name}/credentials/verify` -- validate credential matches Agent Zero
  - `GET  /api/v1/credentials/collisions` -- cross-fleet fingerprint collision check
- [ ] **CLI commands**:
  - `am-ctl credentials verify agent0-3` -- verify agent's credential is valid
  - `am-ctl credentials check-collisions` -- fleet-wide fingerprint collision check

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Only one code path derives the A0 credential | `rg 'A0_API_KEY.*sha256\|create_auth_token' --type sh` returns only the exporter |
| 2 | Canary on Agent0-2: bot starts with derived credential, responds to message | Manual test in Element |
| 3 | Credential fingerprints recorded in platform DB | `am-ctl credentials verify agent0-2` shows matching fingerprint |
| 4 | Cross-fleet collision detected | Give two agents the same fingerprint; `am-ctl credentials check-collisions` flags it |
| 5 | `create-instance.sh` has no `A0_API_KEY` generation | `grep` confirms |
| 6 | `finalize-instance.sh` Step 7b removed | Code review confirms |
| 7 | Bot `.env` no longer contains `A0_API_KEY` | Verified on canary |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **HIGH** | Modifying credential delivery on a live fleet; errors = total bot silence |
| Blast radius | Per-node (sequential rollout) |
| Rollback | Restore `.env.sync-backup` + `supervisorctl restart run_bot` |
| Failure mode | Identical to original incident -- bot gets 401 from Agent Zero |

### Mitigation

- Canary on Agent0-2 for 24 hours before expanding.
- Platform health monitoring (Phase 2) immediately detects `a0_auth` failure.
- Exporter failure = bot refuses to start (fail closed).

---

## Phase 4: Reconciliation Engine

**Repair Strategy Item:** #5 (idempotent reconciler)

### Why fourth

With agent registry (Phase 1), continuous health (Phase 2), and credential authority (Phase 3) in place, the reconciler can detect drift and repair it through the API. This is where the platform becomes the operational tool, not just an observer.

### Script impact

- `sync-fleet.sh` -- **superseded** by `am-ctl reconcile apply`
- `validate-instance.sh` -- **superseded** by `am-ctl reconcile check` (strict superset)
- `fix-agentX-services.sh` -- **superseded** by `am-ctl reconcile apply`
- `finalize-fleet.sh` -- **retired** (one-shot March 2026, no longer relevant)

### Preconditions

- [ ] Phases 1-3 operational and passing their gates
- [ ] Health monitoring producing accurate state in DB
- [ ] All fleet scripts inventoried (see Script Disposition below)

### Deliverables

- [ ] **Reconciliation engine** in `amctl/services/reconciler.py`:
  - `check` -- compare live fleet state against DB registry; return drift report; zero mutations
  - `plan` -- compute proposed actions to resolve drift; return redacted plan; zero mutations
  - `apply` -- execute one planned action at a time; audit log every mutation; recheck after
- [ ] **Drift types detected**:
  - Identity mismatch (`/whoami` != registry)
  - Missing room membership
  - Credential fingerprint mismatch or collision
  - Process count != 1
  - Release hash mismatch (Phase 8)
  - Secret file permissions wrong
- [ ] **Apply safety**:
  - One agent per `apply` call (no fleet-wide apply in v1)
  - Pre-apply snapshot captured
  - Post-apply recheck; if drift remains, report and stop
  - Second apply on clean agent is a no-op
  - All mutations logged to `audit_log`
- [ ] **Schema addition**:

```sql
CREATE TABLE reconcile_runs (
    id          BIGSERIAL PRIMARY KEY,
    agent_id    INT REFERENCES agents(id),
    mode        TEXT NOT NULL,       -- 'check' | 'plan' | 'apply'
    result      JSONB NOT NULL,      -- drift report / plan / apply result
    operator    TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

- [ ] **API endpoints**:
  - `POST /api/v1/reconcile/check` -- fleet-wide or per-agent drift check
  - `POST /api/v1/reconcile/plan/{agent_name}` -- compute plan for one agent
  - `POST /api/v1/reconcile/apply/{agent_name}` -- apply plan with confirmation
  - `GET  /api/v1/reconcile/history` -- past reconciliation runs
- [ ] **CLI commands**:
  - `am-ctl reconcile check` -- fleet-wide drift report
  - `am-ctl reconcile check agent0-3` -- per-agent drift
  - `am-ctl reconcile plan agent0-3` -- show proposed actions
  - `am-ctl reconcile apply agent0-3 [--yes]` -- apply with confirmation

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | `am-ctl reconcile check` matches manual verification for all 5 agents | Compare output with hand-verified state |
| 2 | `check` creates zero mutations (DB read-only, no Docker writes) | Audit log empty after check |
| 3 | `plan` shows correct actions for intentionally drifted agent | Drift Agent0-2; verify plan |
| 4 | `apply` fixes drift and subsequent `check` is clean | Apply on Agent0-2; verify clean |
| 5 | Second `apply` on clean agent is a no-op | Zero new audit entries |
| 6 | Cross-fleet fingerprint collision flagged | Duplicate two fingerprints; check detects |
| 7 | All `apply` actions logged to audit table | Query `audit_log` after apply |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **HIGH** | `apply` mutates live configuration; bugs can stop agents |
| Blast radius | Per-agent (v1 enforces single-agent apply) |
| Rollback | Pre-apply snapshots + `.env.sync-backup` |
| Failure mode | Corrupt config -> bot fails preflight (Phase 7) -> stays down (fail-closed, correct but impactful) |

### Mitigation

- `apply` requires `--yes` flag or interactive confirmation.
- `apply` is single-agent only in v1. Fleet-wide apply lands in v2 with canary logic.
- Platform health monitoring detects failures within seconds, not hours.
- Retain `sync-fleet.sh` as emergency fallback for 30 days.

---

## Phase 5: Fleet Deployment

**Repair Strategy Item:** #7 (immutable releases, partially)

### Why fifth

With reconciliation working, the platform can now manage code and artifact deployment -- absorbing `sync-fleet.sh`, `update-fleet.sh`, and `deploy-supervisord-fleet.sh`.

### Script impact

- `sync-fleet.sh` -- **superseded** (if not already by Phase 4)
- `update-fleet.sh` (v2.2) -- **absorbed** into `am-ctl deploy version`
- `update-fleet-v2.sh` -- **retired** (earlier version of update-fleet)
- `deploy-supervisord-fleet.sh` -- **absorbed** into deployment pipeline

### Preconditions

- [ ] Phase 4 reconciler operational
- [ ] Release bundle format defined (tarball with checksum manifest)

### Deliverables

- [ ] **Release management**:

```sql
CREATE TABLE releases (
    id              SERIAL PRIMARY KEY,
    version         TEXT UNIQUE NOT NULL,
    bundle_path     TEXT,
    checksum_sha256 TEXT NOT NULL,
    artifact_hashes JSONB NOT NULL,   -- { "matrix-bot-rust": "abc...", "watchdog.sh": "def..." }
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE deployments (
    id          BIGSERIAL PRIMARY KEY,
    agent_id    INT REFERENCES agents(id),
    release_id  INT REFERENCES releases(id),
    status      TEXT NOT NULL,        -- 'pending' | 'deploying' | 'success' | 'failed' | 'rolled_back'
    detail      JSONB,
    deployed_at TIMESTAMPTZ DEFAULT now()
);
```

- [ ] **Deployment pipeline**:
  - Upload release bundle -> verify checksums -> register in DB
  - Deploy to single agent: stop bot -> install artifacts -> preflight -> start bot -> health check
  - Sequential rollout with configurable canary window
  - Docker image version management (absorbs `update-fleet.sh` `--version` logic)
- [ ] **API endpoints**:
  - `POST /api/v1/releases` -- upload/register a release
  - `GET  /api/v1/releases` -- list releases
  - `POST /api/v1/deploy/{agent_name}` -- deploy release to agent
  - `GET  /api/v1/deploy/status` -- deployment status across fleet
  - `POST /api/v1/deploy/{agent_name}/version` -- update Agent Zero Docker image version
- [ ] **CLI commands**:
  - `am-ctl deploy release upload <tarball>` -- register release
  - `am-ctl deploy agent0-3 --release v1.0` -- deploy to agent
  - `am-ctl deploy version --version v1.12 [--instances 2,3]` -- Docker image update
  - `am-ctl deploy status` -- fleet deployment overview

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Release bundle registered with correct checksums | `am-ctl deploy release list` shows release |
| 2 | Deploy to canary (Agent0-2) succeeds and passes all health checks | Full deployment cycle observed |
| 3 | Tampered artifact detected | Modify deployed file; reconcile check flags hash mismatch |
| 4 | Docker image update works for single agent | `am-ctl deploy version --version v1.12 --instances 2` succeeds |
| 5 | Instance-local state preserved across deploy | Matrix token, cursor file, event dedup state survive |
| 6 | `update-fleet.sh --status` equivalent works | `am-ctl deploy status` shows version, health, drift |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **MEDIUM** | Replaces proven deployment scripts; bad deploy = bot outage |
| Blast radius | Per-agent (sequential); fleet-wide only if operator explicitly requests |
| Rollback | Previous release bundle + `am-ctl deploy agent0-N --release <previous>` |
| Failure mode | Bad bundle -> preflight fails -> bot stays down (correct behavior) |

---

## Phase 6: Model Management

### Why sixth

`fleet-models.sh` is a 978-line bash script that reads/writes model configuration via Docker exec and JSON parsing. Moving it into the platform gives persistent state, audit trail, and API access.

### Script impact

- `fleet-models.sh` -- **absorbed** into `am-ctl models`

### Preconditions

- [ ] Platform operational with agent registry
- [ ] Model configuration format documented

### Deliverables

- [ ] **Schema addition**:

```sql
CREATE TABLE model_configs (
    id          SERIAL PRIMARY KEY,
    agent_id    INT REFERENCES agents(id),
    config_type TEXT NOT NULL,           -- 'chat' | 'utility' | 'embedding'
    model_name  TEXT NOT NULL,           -- e.g. 'openrouter/google/gemini-2.0-flash-001'
    updated_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE(agent_id, config_type)
);
```

- [ ] **API endpoints**:
  - `GET  /api/v1/models` -- fleet-wide model matrix
  - `GET  /api/v1/models/{agent_name}` -- per-agent model config
  - `PUT  /api/v1/models/{agent_name}` -- set model config
  - `POST /api/v1/models/diagnose` -- model availability diagnostics
- [ ] **CLI commands**:
  - `am-ctl models` -- fleet model matrix (replaces `fleet-models.sh` default output)
  - `am-ctl models agent0-3` -- per-agent model detail
  - `am-ctl models set agent0-3 --chat-model openrouter/moonshotai/kimi-k2.6`
  - `am-ctl models diagnose` -- check model availability

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | `am-ctl models` output matches `fleet-models.sh` output | Side-by-side comparison |
| 2 | Model change via API reflected in container | Set model; verify via Docker exec |
| 3 | Model change logged in audit table | Query audit_log |
| 4 | `fleet-models.sh` disabled with no regression | Verify all model ops go through platform |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **LOW** | Model config changes are non-destructive; wrong model = bad responses, not outage |
| Blast radius | Per-agent |
| Rollback | `am-ctl models set agent0-N --chat-model <previous>` |

---

## Phase 7: Inside-Container Hardening

**Repair Strategy Items:** #4 (preflight), #6 (watchdog), #8 (sync), addendum (auto-join)

### Why seventh

With the platform providing the control plane, inside-container scripts can now validate against the platform API instead of local manifest files. The bot queries `am-ctl` for its expected identity and rooms.

### Script impact

- `startup-services.sh` -- **modified** (add preflight gate)
- `watchdog.sh` -- **replaced** v2.0 -> v3.0 (reports health to platform API)
- `run-matrix-bot.sh` -- **modified** (call preflight before Rust binary)
- Rust bot source -- **modified** (sync hardening, auto-join)

### Preconditions

- [ ] Platform API accessible from inside agent containers (via macvlan or Docker bridge)
- [ ] Agent registry populated with correct identities and required rooms
- [ ] Credential authority operational (Phase 3)

### Deliverables

- [ ] **Startup preflight** (`preflight-check.sh`):
  1. Query platform API for this agent's expected identity and required rooms
  2. Call `/whoami` -- require exact match
  3. Call `joined_rooms` -- require all rooms present
  4. Probe Agent Zero API with canonical credential
  5. Fail closed on any mismatch; report failure to platform API
- [ ] **Watchdog v3.0**: runs inside container, reports health state to platform API
  - Failure classification (restartable vs terminal) driven by platform `alert_rules` table
  - No restart loops on terminal config failures
- [ ] **Sync hardening** (Rust bot changes):
  - Atomic `next_batch` cursor persistence
  - Self-event suppression
  - Bounded event-ID deduplication across restarts
  - Trigger policy enforcement in two-member rooms
- [ ] **Auto-join**: Rust bot accepts invites from trusted senders (queried from platform `trusted_senders` table)

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Preflight catches wrong identity and refuses to start | Sabotage test on canary |
| 2 | Preflight catches missing room and refuses to start | Sabotage test |
| 3 | Preflight reports failure to platform API | Failure visible in `am-ctl health agent0-2` |
| 4 | Watchdog v3.0 reports health to platform | Health checks appear in DB from watchdog |
| 5 | Sync cursor survives container restart | Restart container; verify same cursor |
| 6 | Self-events never trigger responses | Test on canary |
| 7 | Auto-join accepts invite from trusted sender | Send invite; observe join within 30s |
| 8 | Auto-join rejects untrusted invite | Send invite from unknown user; verify ignored |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **MEDIUM** | Preflight gate could false-positive; watchdog replacement could regress restart behavior |
| Blast radius | Per-node; Agent Zero and Continuwuity stay up if bot stops |
| Rollback | Revert to previous `watchdog.sh` v2.0; comment out preflight in `run-matrix-bot.sh` |
| Failure mode | False preflight failure -> bot won't start; cursor corruption -> replay storm |

### Mitigation

- Include `--skip-preflight` emergency flag (logs warning).
- Run watchdog v2.0 and v3.0 in parallel on canary for 48 hours before switching.
- Cursor file format versioned for backward compatibility.

---

## Phase 8: Immutable Releases & v2 Planning

### Why last

Capstone phase. All artifacts are stable. The release system is fully platform-managed.

### Script impact

- `deploy-supervisord-fleet.sh` -- **absorbed** (if not already by Phase 5)
- All `scripts/legacy/` -- **deleted** (30-day grace period complete)

### Deliverables

- [ ] **Immutable release bundles**: built by `make release` or CI, containing all Phase 1-7 artifacts with SHA-256 checksum manifest
- [ ] **Platform-managed deployment**: `am-ctl deploy` is the only path for artifact updates
- [ ] **v2 API design document**: provisioning endpoints for `create`, `finalize`, `destroy`, `decommission`
- [ ] **Multi-host readiness**: document what changes when agents span multiple Docker hosts

### Progress gate

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Release bundle builds reproducibly | Build twice; checksums match |
| 2 | Bundle contains no secrets | `rg 'syt_\|A0_API_KEY=' bundle/` returns 0 |
| 3 | Full fleet deployment via platform succeeds | Deploy to all 5 agents sequentially; all pass |
| 4 | Tampered artifact detected by reconciler | Modify file; `am-ctl reconcile check` flags it |
| 5 | v2 API design reviewed and approved | Document complete |
| 6 | Fleet has run on platform-managed release for 7 days with zero unplanned interventions | Audit log + health history confirm |

### Risk assessment

| Dimension | Rating | Justification |
|-----------|--------|---------------|
| **Overall risk** | **MEDIUM** | Deployment pipeline change; bad bundle = bot outage (fail-closed) |
| Blast radius | Per-agent with sequential rollout |
| Rollback | Previous release bundle via `am-ctl deploy agent0-N --release <previous>` |

---

## Risk Summary

| Phase | Item | Risk | Key Danger |
|-------|------|------|------------|
| 1 | Platform foundation | **LOW** | Additive; wrong registry data misleads operators |
| 2 | Health & monitoring | **MEDIUM** | Monitoring gap if platform goes down during cron cutover |
| 3 | Credential authority | **HIGH** | Credential delivery failure = total bot silence (repeats original incident) |
| 4 | Reconciliation engine | **HIGH** | `apply` mutates live config; bugs can cascade |
| 5 | Fleet deployment | **MEDIUM** | Bad deploy = bot outage; mitigated by preflight |
| 6 | Model management | **LOW** | Non-destructive; wrong model != outage |
| 7 | Inside-container hardening | **MEDIUM** | Preflight false-positive or watchdog regression |
| 8 | Immutable releases & v2 | **MEDIUM** | Deployment pipeline change |

---

## Script Disposition

### Directly Replaced by am-ctl (v1)

| Script | Current purpose | Replaced in | Replacement |
|--------|----------------|-------------|-------------|
| `sync-fleet.sh` | Push templates, preserve `.env` | Phase 4/5 | `am-ctl reconcile apply` / `am-ctl deploy` |
| `validate-instance.sh` | Per-instance health validation | Phase 2/4 | `am-ctl health` / `am-ctl reconcile check` |
| `fix-agentX-services.sh` | SSH to g2s, restart services | Phase 4 | `am-ctl reconcile apply` |
| `deploy-supervisord-fleet.sh` | Install supervisord config | Phase 5 | `am-ctl deploy` |
| `fleet-token-healthcheck.sh` | Cron: token validation | Phase 2 | Continuous monitoring |
| `federation-key-refresh.sh` | Cron: signing key refresh | Phase 2 | Continuous monitoring |
| `fleet-membership-healthcheck.sh` | Cron: membership repair | Phase 2 | Continuous monitoring + auto-repair |
| `fleet-models.sh` | LLM model configuration | Phase 6 | `am-ctl models` |
| `update-fleet.sh` (v2.2) | Docker image version management | Phase 5 | `am-ctl deploy version` |
| `finalize-fleet.sh` | One-shot env standardization | Phase 4 | Retired (one-shot, March 2026) |
| `update-fleet-v2.sh` | Earlier version of update-fleet | Phase 5 | Retired (superseded by v2.2, then by am-ctl) |

### Modified but Kept (until v2 absorbs them)

| Script | What changes | Changed in |
|--------|-------------|------------|
| `create-instance.sh` | Remove `A0_API_KEY` generation | Phase 3 (absorbed into `am-ctl create` in v2) |
| `finalize-instance.sh` | Remove Step 7b derivation | Phase 3 (absorbed into `am-ctl finalize` in v2) |
| `startup-services.sh` | Add preflight gate | Phase 7 |
| `watchdog.sh` | Replace v2.0 with v3.0 | Phase 7 |
| `run-matrix-bot.sh` | Call preflight before Rust binary | Phase 7 |

### Retained Until v2 (Provisioning Lifecycle)

| Script | Why it stays until v2 |
|--------|----------------------|
| `destroy-and-rebuild.sh` | Teardown lifecycle -- v2 provisioning API absorbs it |
| `decommission-instance.sh` | Safe shutdown -- v2 provisioning API absorbs it |

### Retained Permanently (Utility)

| Script | Why |
|--------|-----|
| `check-token-sync.py` | Inside-container utility; watchdog v3.0 may absorb |
| `sync-mcp-token-into-settings.py` | MCP-specific; orthogonal to fleet management |

### Per-Phase Script Impact

| Phase | Scripts affected | Nature |
|-------|-----------------|--------|
| 1 | None | New platform; no scripts changed |
| 2 | 3 cron healthchecks, `validate-instance.sh` | Absorbed into continuous monitoring |
| 3 | `create-instance.sh`, `finalize-instance.sh` | Modified (remove credential code) |
| 4 | `sync-fleet.sh`, `validate-instance.sh`, `fix-agentX-services.sh` | Superseded |
| 5 | `update-fleet.sh`, `deploy-supervisord-fleet.sh` | Absorbed |
| 6 | `fleet-models.sh` | Absorbed |
| 7 | `startup-services.sh`, `watchdog.sh`, `run-matrix-bot.sh` | Modified |
| 8 | All legacy scripts | Deleted (grace period complete) |

---

## Sequential Rollout Protocol (All Phases)

Every phase follows this deployment order:

1. **Agent0-2** (canary -- known-good baseline)
2. **Agent0-3** (simplest prior failure)
3. **Agent0-4** (same class as Agent0-3)
4. **Agent0-5** (identity + credential -- most complex prior failure)
5. **Agent0-1** (membership divergence -- unique failure mode)

Between each node:

- Minimum 4-hour observation window (24 hours for HIGH-risk phases)
- All health checks passing in platform DB
- Phase-specific progress gate passes
- No active alerts

If a gate fails: **stop the rollout, keep that bot down, repair forward.**

---

## Dependency Graph

```
Phase 1: Platform Foundation ───────────────────────────────────┐
    │  (FastAPI server, Postgres, agent registry, CLI)          │
    v                                                           │
Phase 2: Health & Monitoring ───┐                               │
    │  (absorb 3 crons +        │                               │
    v   validate-instance)      │                               │
Phase 3: Credential Authority ──┤                               │
    │                           │                               │
    v                           v                               │
Phase 4: Reconciliation ────────┤                               │
    │  (check/plan/apply)       │                               │
    v                           │                               │
Phase 5: Fleet Deployment ──────┤                               │
    │                           │                               │
    v                           │                               │
Phase 6: Model Management ─────┤  (parallel with Phase 5)      │
                                │                               │
Phase 7: Inside-Container ──────┤                               │
    │  (preflight, watchdog,    │                               │
    v   sync, auto-join)        │                               │
Phase 8: Immutable Releases ────┘                               │
    │                                                           │
    v                                                           v
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
v2: Provisioning API (create, finalize, destroy, decommission)
    WebGUI dashboard
    Multi-host agent management
    Role-based access control (JWT)
```

---

## Definition of Done (v1)

The permanent repair strategy v1 is complete when:

- [ ] `am-ctl` server running as a systemd service on g2s
- [ ] `fleet_ops` database on OpenBrain Postgres with all tables populated
- [ ] All 5 agents in registry with correct identity, rooms, and credential fingerprints
- [ ] Continuous health monitoring replaces all 3 cron healthchecks
- [ ] `am-ctl reconcile check` returns clean for the entire fleet
- [ ] `am-ctl deploy` is the sole deployment path
- [ ] `am-ctl models` replaces `fleet-models.sh`
- [ ] Startup preflight catches sabotaged identity, room, and credential
- [ ] Watchdog v3.0 classifies terminal vs restartable failures correctly
- [ ] All mutations logged in `audit_log` table
- [ ] No legacy credential derivation paths remain
- [ ] Fleet has run on platform-managed operations for 7 days with zero unplanned interventions
- [ ] Test suite passes with >80% coverage on services and check logic

### Definition of Done (v2 -- future)

- [ ] `am-ctl create <instance-number>` replaces `create-instance.sh` + `finalize-instance.sh`
- [ ] `am-ctl destroy <instance-number>` replaces `destroy-and-rebuild.sh`
- [ ] `am-ctl decommission <instance-number>` replaces `decommission-instance.sh`
- [ ] WebGUI dashboard operational
- [ ] Role-based access control with JWT
- [ ] Multi-host agent management documented and tested
- [ ] Platform tested with simulated 100-agent registry
