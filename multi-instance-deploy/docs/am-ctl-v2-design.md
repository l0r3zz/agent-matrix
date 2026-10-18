# am-ctl v2 Design Specification: Provisioning Lifecycle & Multi-Host Readiness

**Status:** Approved (Phase 9 Deliverable)
**Date:** 2026-10-18
**Parent:** [permanent-repair-progress-gates.md](permanent-repair-progress-gates.md)
**Target Version:** `am-ctl` v2.0 (`/api/v2/`)

---

## 1. Overview & Scope

`am-ctl` v1 (`/api/v1/`) established the PostgreSQL-backed control plane (`fleet_ops`) and absorbed day-2 operations across the 5-agent proving ground:
- Registry & live inspection (Phase 1)
- Continuous 8-domain health monitoring & membership auto-repair (Phase 2)
- Canonical Agent Zero credential authority via `.a0-api-key` (Phase 3)
- Idempotent reconciliation engine (`check` / `plan` / `apply`) (Phase 4)
- Automated `open_brain` + `fleet_ops` backups with scratch-DB restore verification (Phase 5)
- Release bundle & Docker image deployment (Phase 6)
- Preset-aware LLM model management (Phase 7)
- Fail-closed startup preflight, Watchdog v3.0, and trusted auto-join (Phase 8)
- Reproducible immutable release bundles (Phase 9)

**`am-ctl` v2 (`/api/v2/`)** completes the lifecycle by absorbing the remaining four day-0/day-N provisioning scripts (`create-instance.sh`, `finalize-instance.sh`, `decommission-instance.sh`, `destroy-and-rebuild.sh`), introducing multi-host node management for scaling toward 1,000 agents, and upgrading authentication to JWT role-based access control (RBAC).

---

## 2. Provisioning Lifecycle API (`/api/v2/provision`)

### 2.1 Deterministic Addressing & Port Scheme

Every agent instance `N` (`1..999`) is deterministically mapped from its `instance_num`:

| Resource | Formula | Example (`N = 6`) |
|----------|---------|-------------------|
| Agent Name | `agent0-{N}` | `agent0-6` |
| Matrix User ID | `@agent0-{N}:agent0-{N}-mhs.cybertribe.com` | `@agent0-6:agent0-6-mhs.cybertribe.com` |
| Homeserver FQDN | `agent0-{N}-mhs.cybertribe.com` | `agent0-6-mhs.cybertribe.com` |
| Agent Container IP (macvlan) | `172.23.88.{N}` (or `/20` pool for `N > 250`) | `172.23.88.6` |
| Homeserver/Caddy IP (macvlan) | `172.23.89.{N}` | `172.23.89.6` |
| Web UI Port | `50000 + N` | `50006` |
| SSH Port | `50021 + N` | `50027` |
| Agent MAC Address | `02:42:AC:17:58:{hex(N)}` | `02:42:AC:17:58:06` |
| MHS MAC Address | `02:42:AC:17:59:{hex(N)}` | `02:42:AC:17:59:06` |

### 2.2 Endpoints

#### `POST /api/v2/agents/create` (Absorbs `create-instance.sh`)

Creates the instance directory structure, renders `docker-compose.yml`, `Caddyfile`, `.env`, and `settings.json` from golden templates, installs the latest immutable release bundle (`am-release-vX.Y.Z.tar.gz`), and registers the agent in `fleet_ops.agents` with `status = 'provisioning'`.

- **Request Body:**
  ```json
  {
    "instance_num": 6,
    "host_id": "g2s",
    "profile": "agent0",
    "model_preset": "Default",
    "release_version": "v1.2.0",
    "required_rooms": [
      {"room_id": "!gahcrWFWAUJQPPkuQy:v-site.net", "room_name": "Fleet HQ Clean"}
    ]
  }
  ```
- **Invariants Enforced:**
  - Never generates a random `A0_API_KEY` in `.env` (Phase 3 invariant).
  - Never overwrites an existing instance directory unless `force_rebuild=true`.
  - Records `provision_create` in `audit_log`.

#### `POST /api/v2/agents/{name}/finalize` (Absorbs `finalize-instance.sh`)

Executes the post-creation bootstrap sequence asynchronously and idempotently:
1. Starts the triplet (`docker compose up -d`).
2. Polls Continuwuity (`http://172.23.89.N:8008/_matrix/client/versions`) until ready.
3. Extracts the one-time Continuwuity bootstrap token from container logs (or logs in if already registered) and completes UIAA registration for `@agent0-N`.
4. Requests a Step-CA certificate (`server.crt` + `server.key` full chain) from `tarnover` Step-CA provisioner and reloads Caddy.
5. Writes `MATRIX_ACCESS_TOKEN` to `matrix-bot/.env` and `matrix-mcp-server/.env`, and runs `sync-mcp-token-into-settings.py`.
6. Derives the canonical `.a0-api-key` via `derive-a0-token.sh` and records its SHA-256 fingerprint in `credential_fingerprints`.
7. Runs `preflight-check.sh`, starts `run_mcp` and `run_bot` under `supervisord`, triggers Synapse notary key fetch + room auto-repair for `required_rooms`, and transitions `agents.status` from `'provisioning'` to `'active'`.

#### `POST /api/v2/agents/{name}/decommission` (Absorbs `decommission-instance.sh`)

Gracefully retires an agent without losing historical audit or memory state:
1. Takes a pre-decommission snapshot (`am-ctl backup run --type pre_deploy`).
2. Leaves all joined Matrix rooms cleanly via the agent's Continuwuity homeserver.
3. Stops and removes the 3 triplet containers (`docker compose down`).
4. Archives `/opt/agent-zero/agent0-N` to `/opt/agent-zero/backups/decommissioned/agent0-N-<timestamp>.tar.gz` (with off-site sync to `tarnover`).
5. Marks `agents.status = 'decommissioned'` in `fleet_ops` (suppressing background health checks while preserving `audit_log` and `health_checks` history).

#### `POST /api/v2/agents/{name}/rebuild` (Absorbs `destroy-and-rebuild.sh`)

Performs a controlled teardown and clean re-provisioning of a corrupted instance:
1. Requires explicit confirmation token (`confirm_destroy: "agent0-N"`) and a verified backup within the last 1 hour.
2. Executes `decommission` (archiving prior state), optionally preserves `mhs/continuwuity-data` and `server.{crt,key}` so Matrix federation identity and signing keys are retained, and re-runs `create` + `finalize` using the latest immutable release bundle.

### 2.3 CLI Mapping

```bash
am-ctl create 6 --profile researcher --release v1.2.0
am-ctl finalize agent0-6
am-ctl decommission agent0-6 --yes
am-ctl rebuild agent0-6 --preserve-mhs --yes
```

---

## 3. Multi-Host Readiness Architecture

Currently, all 5 agent triplets and `open-brain-db` reside on `g2s` (`172.23.100.121`), and `am-ctl` invokes `docker` via local subprocesses (`amctl/services/docker.py`). When the fleet scales across multiple Docker hosts (`g2s`, `g3s`, `g4s`, ...), the following 4 changes enable seamless multi-host operation:

### 3.1 Schema Addition: `hosts` Table

```sql
CREATE TABLE hosts (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,           -- e.g. 'g2s', 'g3s'
    lan_ip          TEXT UNIQUE NOT NULL,           -- e.g. '172.23.100.121'
    macvlan_shim_ip TEXT NOT NULL,                  -- e.g. '172.23.88.254'
    docker_endpoint TEXT NOT NULL DEFAULT 'unix:///var/run/docker.sock',
    max_agents      INT NOT NULL DEFAULT 50,
    status          TEXT NOT NULL DEFAULT 'active', -- 'active' | 'draining' | 'offline'
    created_at      TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE agents ADD COLUMN host_id INT REFERENCES hosts(id);
```

### 3.2 Host Agent / Remote Docker Transport

Each secondary Docker host runs either:
1. **mTLS Docker Engine API** (`tcp://172.23.100.X:2376`, signed by CyberTribe Step-CA), or
2. **`am-node-agent`**: a lightweight stateless FastAPI worker on each host exposing local container inspection, `docker exec`, and release extraction over mTLS to the central `am-ctl` control plane.

`amctl/services/docker.py` resolves `agent.host_id` and routes container commands to the owning host's endpoint instead of assuming local `unix:///var/run/docker.sock`.

### 3.3 Network & Federation Routing Across Hosts

Because the Agent Matrix network uses per-agent `/32` static routes on the edge router (`kama`) rather than pinning an entire `/24` to a single physical box:
- Moving `agent0-N` from `g2s` (`172.23.100.121`) to `g3s` (`172.23.100.122`) requires only updating the two `/32` routes (`172.23.88.N/32` and `172.23.89.N/32`) on `kama` and the Kubernetes `hostAliases` entry on the Synapse hub pod.
- Inside-container scripts (`preflight-check.sh`, `watchdog.sh`, and `matrix-bot-rust`) already read `AMCTL_URL` from environment (defaulting to `http://172.23.88.254:8077`); on secondary hosts, `AMCTL_URL` points to the central `am-ctl` service IP on the services segment (`172.23.90.3:8077`).

---

## 4. Role-Based Access Control (v2 Auth)

In v2, the single static `X-API-Key` is supplemented by short-lived JWTs with three roles:
- **`viewer`**: Read-only (`GET /api/v2/agents`, `/health`, `/models`, `/reconcile/check`, `/reconcile/plan`).
- **`agent_node`**: Scoped per-container token allowing only `GET /api/v2/agents/{self}`, `GET /api/v2/trusted-senders`, and `POST /api/v2/health/{self}/report`.
- **`admin`**: Full mutation authority (`reconcile/apply`, `deploy`, `models/set`, `backup/run`, `provision/*`).
