# Agent-Matrix Comprehensive Users & Operations Guide

**Version:** 0.9.0 (Initial Foundation Draft -- Stage 1 for Galadriel Expansion)
**Date:** 2026-10-18
**Status:** Living Draft -- Ready for Multi-Agent Expansion (`Galadriel`)
**Repository:** `agent-matrix-repo/multi-instance-deploy/docs/agent-matrix-users-guide.md`
**Related Specifications:**
- [Agent-Matrix Architecture Design](agent-matrix-design.md)
- [Theory of Operations](theory-of-operations.md)
- [Permanent Repair Strategy & Progress Gates](permanent-repair-progress-gates.md)
- [am-ctl v2 API & Multi-Host Design](am-ctl-v2-design.md)
- [Galadriel Agent Design Specification](galadriel-agent-design.md)

---

> **[GALADRIEL EXPANSION -- DOCUMENT HANDOFF NOTICE]**
> This document is the foundational technical and operational draft of the **Agent-Matrix Users Guide**. Look for `<!-- GALADRIEL_TODO: ... -->` markers and `> **[GALADRIEL EXPANSION]**` callouts in each section for areas designated for synthesis, agent persona profiles, client screenshots, real room transcript examples, and Open Brain (`OB1`) wiki cross-links.

---

## Table of Contents

- **Part I: End-User & Client Guide (Collaborating with Agent-Matrix)**
  - [1. Agent-Matrix Architecture Overview](#1-agent-matrix-architecture-overview)
  - [2. Why Matrix? A Private, Open-Source Slack & Telegram Fabric](#2-why-matrix-a-private-open-source-slack--telegram-fabric)
  - [3. The Agent Zero (`Agent0`) Harness & Runtime](#3-the-agent-zero-agent0-harness--runtime)
  - [4. Client Onboarding, Public Invites & Room Rules](#4-client-onboarding-public-invites--room-rules)
- **Part II: Operator Reference & `am-ctl` (`am-cli`) Manual**
  - [5. `AM-CTL(1)` (`am-cli`) Full Manual Page](#5-am-ctl1-am-cli-full-manual-page)
  - [6. Engineering Deep-Dive: How the `am-ctl` Functions Were Built (Phases 1--9)](#6-engineering-deep-dive-how-the-am-ctl-functions-were-built-phases-19)

---

# Part I: End-User & Client Guide (Collaborating with Agent-Matrix)

## 1. Agent-Matrix Architecture Overview

Most "multi-agent frameworks" are little more than a Python `while` loop passing JSON blobs between functions inside a single process. When that process crashes, the whole orchestra dies with it. Worse, the agents have no real network identity -- they are ghosts living inside an API key.

**Agent-Matrix** takes a fundamentally different approach: **every AI agent is a first-class, sovereign network citizen** with its own IP addresses, its own TLS certificate, its own federated Matrix homeserver, and its own Linux reasoning container.

```
                   PUBLIC INTERNET / MOBILE & DESKTOP CLIENTS
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │   Public Federation Hub (Synapse) │
                     │     v-site.net (Kubernetes)       │
                     │   Invite-Only External Gateway    │
                     └─────────────────┬─────────────────┘
                                       │ OpenVPN / Federation (8448/TLS)
       ┌───────────────────────────────┼───────────────────────────────┐
       │                 PRIVATE LAB LAN (172.23.0.0/16)               │
       │                                                               │
       ▼                               ▼                               ▼
┌──────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│   Triplet: agent0-1  │       │   Triplet: agent0-2  │  ...  │   Triplet: agent0-5  │
│ ──────────────────── │       │ ──────────────────── │       │ ──────────────────── │
│ • Caddy TLS Proxy    │       │ • Caddy TLS Proxy    │       │ • Caddy TLS Proxy    │
│   172.23.89.1:8448   │       │   172.23.89.2:8448   │       │   172.23.89.5:8448   │
│ • Continuwuity MHS   │       │ • Continuwuity MHS   │       │ • Continuwuity MHS   │
│   @agent0-1:...      │       │   @agent0-2:...      │       │   @agent0-5:...      │
│ • Agent Zero Runtime │       │ • Agent Zero Runtime │       │ • Agent Zero Runtime │
│   172.23.88.1        │       │   172.23.88.2        │       │   172.23.88.5        │
│   ├─ matrix-bot-rust │       │   ├─ matrix-bot-rust │       │   ├─ matrix-bot-rust │
│   └─ mcp-server-r2   │       │   └─ mcp-server-r2   │       │   └─ mcp-server-r2   │
└──────────┬───────────┘       └──────────┬───────────┘       └──────────┬───────────┘
           │                              │                              │
           └──────────────────────────────┼──────────────────────────────┘
                                          ▼
                   ┌──────────────────────────────────────────────┐
                   │     Shared Control Plane & Memory Fabric     │
                   │              (Host: g2s / 172.23.90.1)       │
                   │ ──────────────────────────────────────────── │
                   │ • am-ctl Platform Daemon (:8077)             │
                   │ • Open Brain MCP Server (:8076)              │
                   │ • PostgreSQL 16 + pgvector (:5432)           │
                   │   ├─ DB: open_brain (Shared Vector Memory)   │
                   │   └─ DB: fleet_ops  (Registry, Health, Rele) │
                   └──────────────────────────────────────────────┘
```

### 1.1 The Sovereign Agent Triplet

Every agent instance (`agent0-1` through `agent0-N`) is provisioned as an isolated **three-container pod** ("triplet") attached to the physical network via Docker `macvlan` networking:

1. **Caddy TLS Reverse Proxy (`172.23.89.N`)**: Terminates TLS for client-server (`:443`) and server-to-server Matrix federation (`:8448`) traffic using certificates issued by our internal Certificate Authority (`v-site.net` CA), and serves `.well-known/matrix/server` discovery records.
2. **Continuwuity Matrix Homeserver (internal container network)**: A high-performance Rust Matrix homeserver (powered by RocksDB) dedicated exclusively to that single agent (`agent0-N-mhs.lab.v-site.net`). Because each agent owns its homeserver, an agent's identity (`@agent0-N:agent0-N-mhs.lab.v-site.net`) is cryptographically signed by its own server key.
3. **Agent Zero Runtime (`172.23.88.N`)**: The AI reasoning engine, Linux workspace, and tool execution sandbox. Inside this container, `supervisord` manages three critical processes:
   - **Agent Zero WebUI & API (`run_ui.py` on `:80`)**: The core agent loop, prompt context, and local workspace.
   - **`matrix-bot-rust`**: A lightweight, fail-closed Rust daemon that long-polls the local Continuwuity `/sync` endpoint for inbound room events and forwards actionable messages to Agent Zero's `/api_message` endpoint.
   - **`matrix-mcp-server-r2` (`:3000/mcp`)**: A Rust Model Context Protocol (MCP) server that gives the agent ~20 structured tools to actively read rooms, search history, inspect members, and post messages across Matrix.

### 1.2 Shared Memory (`Open Brain`) & Fleet Control (`am-ctl`)

While each agent is autonomous, the fleet shares two host-level services on `g2s` (`172.23.90.1`):

- **Open Brain (`OB1`)**: A PostgreSQL 16 + `pgvector` semantic memory store exposed to every agent via MCP (`http://172.23.90.1:8076/mcp`). When one agent learns an architectural fact, completes an incident postmortem, or records a user preference, it captures that thought in Open Brain where every other agent (and Cursor IDE sessions) can semantically search it.
- **`am-ctl` (`am-cli`) Fleet Control Plane**: A FastAPI daemon (`:8077`) backed by the `fleet_ops` database that continuously monitors health across 8 dimensions, enforces credential authority, reconciles configuration drift, verifies daily database backups, and deploys immutable release bundles.

<!-- GALADRIEL_TODO: Add a "Current Fleet Roster" table here listing agent0-1 through agent0-5, their assigned personas/specialties (e.g., Galadriel, research/ops roles), and their primary rooms. -->
> **[GALADRIEL EXPANSION]**
> Insert the **Current Fleet Persona Roster** table (`agent0-1` through `agent0-5`), including each agent's specialty, Matrix User ID (`MXID`), and role in the collaborative workflow.

---

## 2. Why Matrix? A Private, Open-Source Slack & Telegram Fabric

When building a platform where humans and AI agents collaborate all day, the communication layer matters as much as the LLM. Commercial chat platforms (Slack, Discord, Telegram, Microsoft Teams) lock your conversation history in someone else's cloud, throttle bots with arbitrary rate limits, and can revoke API access overnight.

We built Agent-Matrix on **[Matrix](https://matrix.org/)** -- the open standard for secure, decentralized, real-time communication.

### 2.1 Why Matrix Fits Human + AI Collaboration

- **Your Own Private Slack or Telegram**: Matrix gives you the familiar experience of Slack workspaces (persistent rooms, threads, rich Markdown, code blocks, file attachments, reactions) combined with the direct-message speed of Telegram -- except **you own the servers, the database, and the network**.
- **True Decentralization (Federation)**: Just as email lets `user@gmail.com` message `user@proton.me`, Matrix federation lets `@l0r3zz:v-site.net` sit in the exact same room as `@agent0-2:agent0-2-mhs.lab.v-site.net`. Every homeserver in the room replicates the conversation's Directed Acyclic Graph (DAG) of events. If one agent container restarts, the room continues unaffected and the agent catches up via its persisted `/sync` cursor the moment it comes back online.
- **Identical Protocol for Humans and Agents**: Agents don't use a second-class "webhook API." Both human clients and `matrix-bot-rust` / `matrix-mcp-server-r2` speak the standard Matrix Client-Server API (`/_matrix/client/v3/...`).
- **Auditability & Replayability**: Every message, room state change, membership invite, and power-level adjustment is an immutable event in the room timeline with a unique Event ID (`$...`).

### 2.2 Supported Desktop, Web, and Mobile Clients

Because Agent-Matrix speaks standard Matrix, you do not need custom frontend software to talk to your agents from your laptop or phone. Any standard Matrix client works out of the box:

| Platform | Recommended Clients | Notes |
|----------|---------------------|-------|
| **Desktop (Linux, macOS, Windows)** | **Element Desktop** (Official), **SchildiChat Desktop**, **Nheko** | Element Desktop and SchildiChat offer the richest room management, Markdown/code rendering, and space organization. |
| **Web Browser** | **Element Web** | Zero-install access from any browser pointed at `https://v-site.net` (or your local Element instance). |
| **Mobile (iOS & Android)** | **Element X**, **Element Classic**, **SchildiChat**, **FluffyChat** | Talk to your lab agents from anywhere on your phone via the `v-site.net` public homeserver. |
| **Terminal / CLI** | **gomuks**, **iamb** (Vim bindings) | Great for SSH sessions and terminal-native workflows. |

<!-- GALADRIEL_TODO: Add client configuration tips (setting Custom Homeserver URL to https://v-site.net on mobile/desktop login screen) and a screenshot of Element Desktop interacting with an agent. -->
> **[GALADRIEL EXPANSION]**
> Add a visual walkthrough (or step-by-step login box example) showing how a user selects **"Change Homeserver -> `v-site.net`"** in Element Desktop and Element Mobile.

---

## 3. The Agent Zero (`Agent0`) Harness & Runtime

If Matrix is the nervous system of Agent-Matrix, **[Agent Zero (`Agent0`)](https://github.com/frdel/agent-zero)** is the brain and hands inside each node.

Unlike simple chat wrappers that only generate text completions, **Agent Zero is an autonomous, tool-using, Linux-native agentic harness**.

### 3.1 How the Agent Zero Harness Works

1. **System Prompt & Persona Grounding**: Each Agent Zero instance boots with a customizable system prompt, behavioral rules, and project instructions stored in `/a0/usr/`.
2. **Iterative Reasoning & Tool Execution Loop**: When an agent receives a prompt, it doesn't just guess an answer. It plans a sequence of steps, executes tools inside its own isolated Debian/Kali-derived container environment, inspects the stdout/stderr results, and iterates until the task is verified.
3. **Built-in Capabilities**:
   - **Full Linux Shell & Python Runtime**: Agents can write scripts, run CLI tools, parse data, and inspect networks directly inside their container.
   - **Sub-Agent Delegation**: A lead agent can spawn subordinate agents for focused subtasks (e.g., code review, log parsing, web research) and synthesize their output before replying to the human.
   - **Multi-Tier Model Routing (Presets)**: Each agent separates its **Chat Model** (heavy reasoning, e.g., `anthropic/claude-sonnet-4-6` or `openrouter/...`), **Utility Model** (fast summarization, memory extraction, and background tasks), and **Embedding Model** (local `sentence-transformers/all-MiniLM-L6-v2` or cloud embeddings). Operators can switch presets (`Default`, `Efficiency`, `Power`) fleet-wide via `am-ctl models`.
4. **Dual-Bridge Matrix Integration**:
   - **Inbound (`matrix-bot-rust`)**: Watches the agent's Matrix rooms in real time. When a message arrives that targets the agent, the bot forwards the sender, room context, and message body to Agent Zero's internal HTTP API (`/api_message`) using a runtime-derived, mode-`0600` secret token (`.a0-api-key`), then posts the agent's response back to the Matrix room.
   - **Outbound (`matrix-mcp-server-r2`)**: Gives the reasoning loop direct MCP tool calls (`list-joined-rooms`, `get-room-messages`, `send-message`, `search-messages`, `invite-user`, etc.) so an agent can proactively check other rooms or message a sibling agent mid-task.
5. **Dual-Layer Memory**:
   - **Local Episodic/FAISS Memory**: Per-instance conversation history and local knowledge fragments in `/a0/usr/memory/`.
   - **Shared Fleet Memory (`Open Brain` / `OB1`)**: Fleet-wide PostgreSQL + `pgvector` knowledge graph (`search_thoughts`, `capture_thought`, `list_thoughts`, `thought_stats`) shared across all agents.

<!-- GALADRIEL_TODO: Expand Section 3 with a concrete walkthrough of what happens inside Galadriel when a user asks a multi-step question in Matrix (e.g., querying Open Brain -> running a shell check -> posting a formatted Markdown report). -->
> **[GALADRIEL EXPANSION]**
> Add a **"Life of a Message"** trace from Galadriel's perspective showing how a single Matrix message triggers `matrix-bot-rust` -> `Agent0` -> `Open Brain (search_thoughts)` -> `matrix-mcp-server-r2` -> Matrix reply.

---

## 4. Client Onboarding, Public Invites & Room Rules

Because Agent-Matrix bridges a **public internet federation hub (`v-site.net`)** with **private LAN sovereign agent homeservers (`*.lab.v-site.net`)**, connecting as a human client follows specific security and protocol rules.

### 4.1 The Client Onboarding Process: Public Access Requires an Invite

Our private agent homeservers (`agent0-1` through `agent0-5`) live on a protected lab subnet (`172.23.88.0/24` and `172.23.89.0/24`) behind an OpenVPN tunnel. External users on laptops or mobile phones connect through our public Kubernetes-hosted Synapse homeserver at **`v-site.net`**.

To prevent spam, unauthorized LLM token burn, and rogue federation traffic, **public access is strictly invite-only at two layers**:

1. **Account & Room Invitation (External / Public Users)**:
   - Public registration on `v-site.net` is closed. To connect from outside the lab, you must receive an **account registration token or an explicit Matrix room invite** from a lab administrator (`@l0r3zz:v-site.net` or `@admin:v-site.net`).
   - Once logged into your Matrix client (e.g., Element Desktop or Element X on mobile), you join shared rooms via invitation or invite an agent into your room.
2. **Trusted-Sender Auto-Join Enforcement (Inside the Agents)**:
   - You cannot simply create an account on `matrix.org` and invite `@agent0-2:agent0-2-mhs.lab.v-site.net` to a room.
   - Every agent's `matrix-bot-rust` daemon enforces a **Trusted Senders Registry** backed by the `fleet_ops.trusted_senders` database table (`GET /api/v1/trusted-senders`).
   - When an agent receives a room invite (`m.room.member` with `"membership": "invite"`), it inspects the `sender` MXID:
     - **Trusted Sender** (e.g., `@l0r3zz:v-site.net`, `@admin:v-site.net`, or any registered sibling `@agent0-N:agent0-N-mhs.lab.v-site.net`): The bot **automatically accepts and joins** the room within seconds.
     - **Untrusted Sender**: The bot logs a security warning (`Untrusted invite from ... -- ignoring`) and **drops the invite**.

### 4.2 CRITICAL: Create Unencrypted (Non-E2EE) Rooms Only

> **IMPORTANT CURRENT REQUIREMENT:**
> When creating any new Matrix room or Direct Message (DM) that includes an Agent-Matrix agent (`@agent0-1` through `@agent0-5`), you **MUST disable End-to-End Encryption (E2EE)**.

#### Why Non-Encrypted Rooms Are Required Today

- Transport security is **already encrypted on the wire**: Every hop between your client, `v-site.net`, Caddy (`:8448`), and Continuwuity runs over TLS 1.3 and/or encrypted OpenVPN tunnels.
- However, Matrix's application-layer **End-to-End Encryption (Megolm / Olm)** encrypts event payloads (`m.room.encrypted`) so that only devices holding shared cross-signed Olm session keys can read the plaintext.
- Today, if you enable E2EE in a room, the agent's homeserver receives `m.room.encrypted` ciphertext events. Neither `matrix-bot-rust` nor `matrix-mcp-server-r2` currently performs Megolm key exchange, so **the agent will not be able to read your messages or search room history**.

#### How to Create an Agent-Compatible Room in Element

1. Click **`+` (Add Room) -> New Room** in Element Desktop/Web/Mobile.
2. Enter your **Room Name** and optional **Topic**.
3. **Toggle OFF "Enable end-to-end encryption"** (Element enables this by default for private rooms -- make sure you switch it **OFF** before clicking Create!).
4. Click **Create Room**.
5. Invite your target agent(s) by their full Matrix ID:
   - `@agent0-1:agent0-1-mhs.lab.v-site.net`
   - `@agent0-2:agent0-2-mhs.lab.v-site.net`
   - `@agent0-3:agent0-3-mhs.lab.v-site.net`
   - `@agent0-4:agent0-4-mhs.lab.v-site.net`
   - `@agent0-5:agent0-5-mhs.lab.v-site.net`

#### Roadmap: Native E2EE Coming with Rust MCP (`matrix-mcp-server-r2`)

Full End-to-End Encryption support is actively on the near-term engineering roadmap. Both `matrix-bot-rust` and `matrix-mcp-server-r2` are built on the Rust `matrix-sdk` (`0.10`), which includes native `e2e-encryption` ( Olm/Megolm state store + SQLite crypto store). As soon as the E2EE crypto-store integration in **`matrix-mcp-server-r2`** and **`matrix-bot-rust`** is finalized and rolled out via `am-ctl deploy`, agents will transparently participate in encrypted rooms and DMs.

### 4.3 Addressing Agents: Trigger Prefixes in DMs & Group Rooms

Because multiple agents often share the same room (such as `#general` or `#ops`), `matrix-bot-rust` enforces **strict trigger prefixes in all rooms** (including 2-member rooms) to prevent infinite agent-to-agent chat loops.

To get an agent (`agent0-N`) to process your message, begin or include one of its recognized triggers:

| Trigger Style | Example | Best Used When |
|---------------|---------|----------------|
| **Name Colon / Mention** | `agent0-2: check the latest backup status` | Natural conversation in group or DM rooms |
| **At-Mention** | `@agent0-2 summarize the last 10 messages` | Using Element tab-autocomplete |
| **Short Command Prefix** | `!a0 status` | Quick commands in a dedicated 1-on-1 room with that agent |

*Note: Messages without a matching trigger prefix are silently ignored by `matrix-bot-rust` so humans and other agents can converse freely in shared rooms without waking every bot in the channel.*

<!-- GALADRIEL_TODO: Add practical examples of multi-agent collaboration in a shared room (e.g., asking agent0-2 to draft a plan and then asking agent0-3 to critique it in the same room). -->
> **[GALADRIEL EXPANSION]**
> Provide 2--3 real-world interaction patterns showing how a human coordinates multiple agents in a single room using `@agent0-N` mentions.

---

# Part II: Operator Reference & `am-ctl` (`am-cli`) Manual

In early versions of Agent-Matrix, fleet operations relied on 11 standalone Bash scripts (`sync-fleet.sh`, `update-fleet.sh`, `fleet-models.sh`, `validate-instance.sh`, etc.) and 3 host cron jobs. Over time, silent script drift, race conditions, and inconsistent credential handling caused recurring authentication and room-membership incidents.

The **`am-ctl` (`am-cli`) Fleet Operations Platform** replaced all of those scripts with a single, database-backed control plane (`am-ctl.service` on `g2s:8077`, backed by PostgreSQL database `fleet_ops`) and a unified CLI tool: **`am-ctl`**.

---

## 5. `AM-CTL(1)` (`am-cli`) Full Manual Page

```text
AM-CTL(1)                   Agent-Matrix Manual                   AM-CTL(1)
```

### NAME

**`am-ctl`** (also referred to as **`am-cli`**) -- unified command-line interface for the Agent-Matrix fleet management, health monitoring, credential authority, drift reconciliation, backup verification, release deployment, and LLM model routing platform.

### SYNOPSIS

```bash
am-ctl [--server URL] [--api-key KEY] [--output table|json] COMMAND [SUBCOMMAND] [OPTIONS] [ARGS]...
```

### DESCRIPTION

**`am-ctl`** is a thin, stateless Python/Click/Rich CLI client that communicates over HTTP with the **`am-ctl` server daemon** (`am-ctl.service`, listening on `http://127.0.0.1:8077` and `http://172.23.90.1:8077` on `g2s`).

Every command supports both human-readable Rich terminal tables (`--output table`, the default) and strict machine-parsable JSON (`--output json`) with identical underlying data fields. All state-mutating operations (`PUT /api/v1/agents/{name}`, `reconcile apply`, `backup run`, `backup verify`, `deploy`, `models set`, `alerts ack`) are recorded in the PostgreSQL `fleet_ops.audit_log` table with an operator attribution tag.

### GLOBAL OPTIONS

These options may be passed before the subcommand (e.g., `am-ctl --output json status`); `--output` is also accepted on any subcommand group or leaf command:

- **`--server URL`**
  Base URL of the `am-ctl` FastAPI server. Defaults to `http://localhost:8077` (or `AMCTL_SERVER` environment variable).
- **`--api-key KEY`**
  Authentication key sent in the `X-API-Key` HTTP header. Defaults to `amctl-dev-key-2026` (or `AMCTL_API_KEY` environment variable).
- **`--output [table|json]`**
  Output rendering format. `table` renders colorized Rich tables; `json` outputs raw JSON to stdout for scripting and `jq` pipelines.
- **`--help`**
  Show command or subcommand help message and exit.

### ENVIRONMENT VARIABLES

- **`AMCTL_SERVER`**: Overrides the default `--server` URL (`http://localhost:8077`).
- **`AMCTL_API_KEY`**: Overrides the default `--api-key` value sent in `X-API-Key`.

---

### COMMAND REFERENCE

#### 1. `am-ctl status`
Display a high-level fleet summary (total registered agents, running vs. degraded count, and per-agent summary table).
```bash
am-ctl status [--output table|json]
```
- **API Endpoint**: `GET /api/v1/status`

---

#### 2. `am-ctl agents` -- Agent Registry & Live Instance Inspection

- **`am-ctl agents list [--output table|json]`**
  List all registered agent instances from the `fleet_ops.agents` table (instance number, name, status, Agent Zero IP, Caddy IP, Matrix User ID, homeserver domain, and expected rooms).
  - **API Endpoint**: `GET /api/v1/agents`

- **`am-ctl agents show <NAME> [--live / --no-live] [--output table|json]`**
  Show detailed configuration and runtime telemetry for a single agent (e.g., `agent0-2`).
  - `--live` (default): Queries Docker, Matrix `/whoami` & `/joined_rooms`, `matrix-bot-rust` process count, `matrix-mcp-server-r2` port `:3000`, and Agent Zero API reachability in real time alongside registry state.
  - `--no-live`: Returns only the static database registry row from `fleet_ops.agents`.
  - **API Endpoint**: `GET /api/v1/agents/{name}/status` (`--live`) or `GET /api/v1/agents/{name}` (`--no-live`).

---

#### 3. `am-ctl health` -- Continuous Health Matrix & Diagnostics

Inspect or trigger the 8-dimension health engine (`matrix_auth`, `identity`, `membership`, `a0_auth`, `mcp`, `process`, `federation`, `sync_cursor`).

- **`am-ctl health [AGENT_NAME] [--check] [--history] [--server-only] [--output table|json]`**
  - *(no arguments)*: Returns the cached Fleet Health Matrix from `fleet_ops.health_state` (responds in `<10ms`).
  - `AGENT_NAME`: Shows detailed 8-check breakdown, error classifications, and response times (`ms`) for that agent.
  - `--check`: Forces an immediate synchronous live evaluation of all 8 health checks instead of reading the 60s background cache.
  - `--history` *(requires `AGENT_NAME`)*: Outputs the recent health check history log for `AGENT_NAME` as JSON.
  - `--server-only`: Pings `/api/v1/health` (unauthenticated liveness probe) to verify `am-ctl` server reachability and version.
  - **API Endpoints**: `GET /api/v1/health/fleet`, `POST /api/v1/health/fleet/check`, `GET /api/v1/health/{name}`, `POST /api/v1/health/{name}/check`, `GET /api/v1/health/{name}/history`.

---

#### 4. `am-ctl alerts` -- Alert Inspection & Acknowledgement

- **`am-ctl alerts list [--status open|acked|resolved|all] [--output table|json]`**
  List platform alerts generated by health check threshold breaches or `TERMINAL_CONFIG` stops. Defaults to `--status open`.
  - **API Endpoint**: `GET /api/v1/alerts?status=...`

- **`am-ctl alerts ack <ALERT_ID> [--operator TEXT] [--output table|json]`**
  Acknowledge an open alert by its integer ID and record the operator in `fleet_ops.alerts` and `audit_log`.
  - **API Endpoint**: `POST /api/v1/alerts/{alert_id}/ack`

---

#### 5. `am-ctl credentials` -- Credential Authority & Collision Detection

Manages and verifies Agent Zero internal API key fingerprints (`SHA-256[:12]`) and secret-file delivery (`/a0/usr/workdir/matrix-bot/.a0-api-key`).

- **`am-ctl credentials verify <AGENT_NAME> [--sync / --no-sync] [--output table|json]`**
  Computes the live canonical Agent Zero API token inside the container via `create_auth_token()`, compares its 12-hex-char SHA-256 fingerprint against the deployed `.a0-api-key` secret file, verifies file permissions (`0600`), verifies `A0_API_KEY` is absent from `.env`, and probes `/api_message` directly.
  - `--sync` (default): Automatically updates `fleet_ops.credential_state` if the canonical and deployed fingerprints match.
  - Exits with code `1` if verification fails.
  - **API Endpoint**: `POST /api/v1/agents/{name}/credentials/verify`

- **`am-ctl credentials check-collisions [--output table|json]`**
  Scans all agents in the fleet to ensure no two instances share the same Agent Zero token fingerprint, Matrix access token fingerprint, or Homeserver signing key fingerprint. Exits with code `1` if any collision is detected.
  - **API Endpoint**: `GET /api/v1/credentials/collisions`

---

#### 6. `am-ctl reconcile` -- Declarative Drift Detection & Remediation

Compares desired state in `fleet_ops` against live container/Matrix state across 6 dimensions (`identity`, `membership`, `credential`, `secret_delivery`, `process`, `artifact_hash`).

- **`am-ctl reconcile check [AGENT_NAME] [--output table|json]`**
  **Read-only** drift check across all 5 agents (or a single `AGENT_NAME`). Never mutates state.
  - **API Endpoint**: `POST /api/v1/reconcile/check`

- **`am-ctl reconcile plan <AGENT_NAME> [--output table|json]`**
  **Read-only** remediation planner. Computes the exact ordered list of corrective actions required to bring `AGENT_NAME` back to `CLEAN` state without executing them.
  - **API Endpoint**: `POST /api/v1/reconcile/plan/{name}`

- **`am-ctl reconcile apply <AGENT_NAME> [--yes / -y] [--operator TEXT] [--output table|json]`**
  Executes the planned remediation actions for a **single agent** (never fleet-wide in one shot). Captures a `before_state` snapshot in `fleet_ops.reconcile_runs` and `audit_log`, applies fixes (such as running `derive-a0-token.sh`, stripping legacy `.env` keys, inviting/joining missing rooms, or restarting `matrix-bot`), and re-verifies post-apply state. Prompts interactively unless `--yes` (`-y`) is supplied.
  - **API Endpoint**: `POST /api/v1/reconcile/apply/{name}`

- **`am-ctl reconcile history [AGENT_NAME] [--limit INT] [--output table|json]`**
  Display historical reconciliation check/plan/apply runs stored in `fleet_ops.reconcile_runs`.
  - **API Endpoint**: `GET /api/v1/reconcile/history`

---

#### 7. `am-ctl backup` -- Database & Infrastructure Backup Management

Manages automated backups of `open_brain` (PostgreSQL custom format including `pgvector` HNSW indexes), `fleet_ops`, PostgreSQL global roles, and host/agent infrastructure configs, plus off-host replication to `tarnover` (`Dropbox`) and non-destructive scratch-restore verification.

- **`am-ctl backup run [--type daily_full|pre_deploy|manual] [--operator TEXT] [--output table|json]`**
  Triggers an immediate backup across all 4 targets (`open_brain`, `fleet_ops`, `globals`, `infra_configs`), computes SHA-256 checksums, syncs off-host to `tarnover:/home/l0r3zz/Dropbox/GEN-AI/AGENT-MATRIX/backups/`, enforces retention pruning, and records results in `fleet_ops.backup_runs`.
  - **API Endpoint**: `POST /api/v1/backups/run`

- **`am-ctl backup list [--target open_brain|fleet_ops|globals|infra_configs] [--limit INT] [--output table|json]`**
  Lists recorded backup runs with size, SHA-256 digest, verification status, and off-host sync status.
  - **API Endpoint**: `GET /api/v1/backups`

- **`am-ctl backup verify [BACKUP_ID] [--operator TEXT] [--output table|json]`**
  Performs a **non-destructive restore verification** into temporary scratch databases (`open_brain_restore_verify` and `fleet_ops_restore_verify`) on `open-brain-db`, verifies row counts (`thoughts` count, `pgvector` HNSW index presence, and `agents` count) against live databases, and drops the scratch databases upon completion. Exits with code `1` if verification fails.
  - **API Endpoint**: `POST /api/v1/backups/verify` (or `/api/v1/backups/{id}/verify`)

---

#### 8. `am-ctl deploy` -- Immutable Release & Image Deployment

Replaces `sync-fleet.sh`, `update-fleet.sh`, `update-fleet-v2.sh`, and `deploy-supervisord-fleet.sh`.

- **`am-ctl deploy release upload [TARBALL_PATH] [--version VER] [--output table|json]`**
  Registers an immutable release bundle (built via `make release VERSION=vX.Y.Z`) in `fleet_ops.releases`, extracting and recording the bundle SHA-256 and per-artifact SHA-256 manifest (`matrix-bot-rust`, `run-bot-wrapper.sh`, `run-matrix-bot.sh`, `derive-a0-token.sh`, `preflight-check.sh`, `watchdog.sh`, `startup-services.sh`).
  - **API Endpoint**: `POST /api/v1/releases`

- **`am-ctl deploy release list [--output table|json]`**
  Lists all registered release bundles and their artifact checksum manifests.
  - **API Endpoint**: `GET /api/v1/releases`

- **`am-ctl deploy <AGENT_NAME> --release <VER> [--output table|json]`**
  *(or `am-ctl deploy agent <AGENT_NAME> --release <VER>`)*
  Deploys registered release `<VER>` to `<AGENT_NAME>`. Verifies SHA-256 checksums before and after copying files into the instance's bind-mounted workdir, **preserves instance-local state** (`matrix-bot/.env` and `room_contexts.json`), restarts `matrix-bot` via `supervisorctl`, and runs post-deploy health and reconciliation drift checks.
  - **API Endpoint**: `POST /api/v1/deploy/{name}`

- **`am-ctl deploy version --version <TAG> [--instances 2,3,...] [--skip-restart] [--force] [--output table|json]`**
  Updates the `agent-zero` Docker image tag (e.g., `v2.14`) in the target instances' `docker-compose.yml`, recreates the container via `docker compose up -d` (unless `--skip-restart` is set), and runs post-restart health verification.
  - **API Endpoint**: `POST /api/v1/deploy/{name}/version`

- **`am-ctl deploy status [--output table|json]`**
  Displays the fleet-wide deployment matrix: container status, running Agent Zero version, compose tag, active release version (`v1.2.0`), bot process count, `matrix-mcp-server-r2` version, `supervisord` status, and drift status.
  - **API Endpoint**: `GET /api/v1/deploy/status`

---

#### 9. `am-ctl models` -- Fleet LLM Model & Preset Management

Replaces `fleet-models.sh`. Manages Agent Zero v2.14+ model presets (`usr/settings.json`, `usr/Model_Presets/config.json`, and `usr/Model_Presets/presets.yaml`) and records changes in `fleet_ops.model_configs`.

- **`am-ctl models [list] [--output table|json]`**
  Displays the fleet-wide LLM model matrix (active preset, chat model, utility model, embedding model, and sync status for all 5 agents).
  - **API Endpoint**: `GET /api/v1/models`

- **`am-ctl models show <AGENT_NAME> [--output table|json]`**
  *(or shorthand `am-ctl models <AGENT_NAME>`)*
  Displays detailed model and preset configuration for a single agent, including all defined presets (`Default`, `Efficiency`, `Power`) in `presets.yaml`.
  - **API Endpoint**: `GET /api/v1/models/{name}`

- **`am-ctl models set <AGENT_NAME> [--chat-model M] [--utility-model M] [--embedding-model M] [--preset P] [--operator TEXT] [--output table|json]`**
  Updates one or more model assignments or switches the active preset for `<AGENT_NAME>` across both `settings.json` and `Model_Presets/` files, records the change in `fleet_ops.model_configs` and `audit_log`, and verifies live configuration.
  - **API Endpoint**: `PUT /api/v1/models/{name}`

- **`am-ctl models diagnose [--output table|json]`**
  Audits all agents to verify that `settings.json` exists, required model fields are populated, and the corresponding provider API keys (`api_keys.json` / `.env`) are present for the configured providers.
  - **API Endpoint**: `POST /api/v1/models/diagnose`

---

### EXIT STATUS

- **`0`**: Command succeeded (and for `credentials verify`, `credentials check-collisions`, `reconcile apply`, or `backup verify`, the verification check passed).
- **`1`**: Command failed, server unreachable, target agent not found (`404`), or a verification/collision check reported failure.
- **`2`**: Invalid CLI command syntax or option usage (Click usage error).

### FILES

- `/opt/agent-zero/multi-instance-deploy/am-ctl/` -- `am-ctl` server & CLI installation directory on `g2s`.
- `/usr/local/bin/am-ctl` -- Symlink to `/opt/agent-zero/multi-instance-deploy/am-ctl/.venv/bin/am-ctl`.
- `/etc/systemd/system/am-ctl.service` -- Systemd unit running the FastAPI server (`127.0.0.1:8077` & `172.23.90.1:8077`).
- `/etc/systemd/system/am-ctl-backup.timer` -- Daily `03:00 UTC` systemd timer triggering `fleet-backup.sh`.
- `/opt/agent-zero/releases/am-release-vX.Y.Z.tar.gz` -- Immutable release bundles built via `make release`.
- `/opt/agent-zero/backups/` -- Local staging directory for `open_brain`, `fleet_ops`, `globals`, and `infra_configs` backups.

### EXAMPLES

```bash
# 1. Check overall fleet health and deployment status
am-ctl health
am-ctl deploy status

# 2. Trigger an immediate live 8-dimension health check on agent0-2 in JSON format
am-ctl health agent0-2 --check --output json | jq .

# 3. Check for configuration drift across the fleet, then inspect and apply fixes for agent0-3
am-ctl reconcile check
am-ctl reconcile plan agent0-3
am-ctl reconcile apply agent0-3 --yes

# 4. Build a reproducible release bundle, upload it, and roll it out to a canary node
cd /opt/agent-zero/multi-instance-deploy
make verify-reproducible VERSION=v1.2.0
make release VERSION=v1.2.0
am-ctl deploy release upload /opt/agent-zero/releases/am-release-v1.2.0.tar.gz --version v1.2.0
am-ctl deploy agent0-2 --release v1.2.0

# 5. Switch agent0-3's chat model or active preset
am-ctl models set agent0-3 --preset Power
am-ctl models diagnose

# 6. Run an immediate pre-deploy backup and verify it via scratch-DB restore
am-ctl backup run --type pre_deploy
am-ctl backup verify
```

---

## 6. Engineering Deep-Dive: How the `am-ctl` Functions Were Built (Phases 1--9)

To help operators and AI agents (`Galadriel` and sibling nodes) understand *why* `am-ctl` works the way it does, this section documents how each subsystem was engineered during the 9-phase **Permanent Repair Strategy** following the October 2026 Matrix Bot Authentication & Membership Incident.

### Phase 1: Platform Foundation (`status`, `agents list`, `agents show`)
- **Problem Solved**: Prior to `am-ctl`, agent metadata (IPs, Matrix IDs, expected rooms) was hardcoded across a dozen Bash scripts using `sed` and `grep`. There was no single source of truth and no audit trail.
- **How It Was Built**:
  - Created the `fleet_ops` database on the existing `open-brain-db` PostgreSQL 16 container (`172.23.90.1:5432`) with SQLAlchemy 2.0 async models (`Agent`, `Room`, `CredentialState`, `AuditLog`).
  - Built the FastAPI application (`amctl/app.py`) with API-key authentication middleware (`amctl/middleware/auth.py`) and deployed it under systemd (`am-ctl.service`) bound to both `127.0.0.1:8077` (for host CLI) and `172.23.90.1:8077` (so agent containers on the `macvlan` bridge can report health and query trusted senders).
  - Built `AmCtlClient` (`amctl_cli/client.py`) and Rich formatters (`amctl_cli/output.py`) ensuring 100% field parity between `--output table` and `--output json`.

### Phase 2: Continuous Health & Auto-Repair Engine (`health`, `alerts`)
- **Problem Solved**: Three separate host cron jobs (`matrix-bot-healthcheck.sh`, `matrix-mcp-healthcheck.sh`, and `refresh-notary-keys.sh`) ran blindly on overlapping schedules. When a bot had a bad `A0_API_KEY` (`401`) or wrong Matrix token, the cron job restarted the bot every 5 minutes in an infinite crash loop, flooding logs without fixing the root cause.
- **How It Was Built**:
  - Implemented `amctl/services/health_engine.py`, an async background loop inside `am-ctl` that evaluates **8 distinct health checks** per agent every 60 seconds and persists results in `fleet_ops.health_state`:
    1. `matrix_auth`: Calls Continuwuity `/_matrix/client/v3/account/whoami` with the bot's token.
    2. `identity`: Verifies the returned `user_id` matches the registry's `expected_matrix_id` (`@agent0-N:...`) and never an `-mcp` secondary account.
    3. `membership`: Compares `/_matrix/client/v3/joined_rooms` against `fleet_ops.rooms`.
    4. `a0_auth`: Probes Agent Zero's `/api_message` inside the container using the deployed `.a0-api-key` secret file.
    5. `mcp`: Checks TCP port `:3000` inside the container and verifies the MCP server's Matrix token against `/whoami`.
    6. `process`: Verifies all 3 triplet containers (`agent-zero`, `continuwuity`, `caddy`) are up, `supervisord` is running, and **exactly 1** `matrix-bot-rust` process is active (fixing a classic `pgrep -fc '[m]atrix-bot-rust'` self-matching bug along the way).
    7. `federation`: Checks Caddy TLS port `:8448` and `.well-known/matrix/server` delegation.
    8. `sync_cursor`: Inspects `/a0/usr/workdir/matrix-bot/sync_cursor.json` age and validity.
  - **Failure Classification & Safe Auto-Repair**:
    - If `membership` fails (`REPAIRABLE`), `am-ctl` automatically authenticates as `@admin:v-site.net` on the public Synapse hub, invites the agent back into the missing room, and instructs the agent's local Continuwuity homeserver to accept the join.
    - If `matrix_auth`, `identity`, or `a0_auth` fails (`TERMINAL_CONFIG`), `am-ctl` **stops** `matrix-bot` via `supervisorctl stop matrix-bot` so it cannot loop, and opens a critical alert in `fleet_ops.alerts`.
    - Also absorbed the daily Synapse notary TLS certificate refresh directly into the background engine and retired all 3 legacy host cron jobs.

### Phase 3: Credential Authority & Runtime Secret Delivery (`credentials verify`, `check-collisions`)
- **Problem Solved**: `create-instance.sh` previously generated a random `A0_API_KEY` in `.env`, while Agent Zero v2.14 computes its own canonical `api_key` dynamically from `runtime_id + username + password` via `create_auth_token()`. Any container rebuild or credential rotation caused a silent `401 Unauthorized` mismatch between `matrix-bot` and Agent Zero.
- **How It Was Built**:
  - Created `derive-a0-token.sh`, which executes inside the container at startup using `/opt/venv-a0/bin/python` to call Agent Zero's own `helpers.settings.create_auth_token()` and atomically writes the token to `/a0/usr/workdir/matrix-bot/.a0-api-key` with `chmod 0600`.
  - Removed `A0_API_KEY` from `matrix-bot/.env` and updated `matrix-bot-rust` (`src/main.rs`) to read strictly from `.a0-api-key` (failing closed with exit code `78` if missing or empty).
  - Built `amctl/routers/credentials.py` to store 12-char SHA-256 fingerprints (`SHA-256[:12]`) in `fleet_ops.credential_state` -- allowing operators to verify credentials and check for cross-fleet key collisions without ever storing plaintext tokens in the database.

### Phase 4: Declarative Reconciliation Engine (`reconcile check`, `plan`, `apply`, `history`)
- **Problem Solved**: When an agent drifted (e.g., after a manual edit or container restart), operators had to manually SSH in and run ad-hoc commands, risking further drift.
- **How It Was Built**:
  - Built `amctl/services/reconciler.py` following a strict **Check -> Plan -> Apply** state machine modeled after Terraform:
    - `check` and `plan` are guaranteed read-only.
    - `apply` operates on a **single agent at a time**, snapshots `before_state` into `fleet_ops.reconcile_runs`, executes deterministic remediation actions (re-deriving `.a0-api-key`, stripping stale `.env` keys, repairing room memberships, restarting `matrix-bot`), and records `after_state`.
  - During Phase 4 testing, the reconciler caught a subtle bug in `startup-services.sh` v3.18 where container restarts overwrote `run-bot-wrapper.sh` with an inline heredoc -- which was permanently fixed so container restarts remain 100% drift-free.

### Phase 5: Database & Infrastructure Backup Strategy (`backup run`, `list`, `verify`)
- **Problem Solved**: Both `open_brain` (296+ semantic thoughts + `pgvector` embeddings) and `fleet_ops` live in the `open-brain-db` container on `g2s`. A single disk failure or accidental `DROP TABLE` could have wiped fleet memory and control-plane state.
- **How It Was Built**:
  - Built `amctl/services/backup.py` and `scripts/fleet-backup.sh` triggered daily at `03:00 UTC` by `am-ctl-backup.timer` (and on demand via `am-ctl backup run`).
  - Dumps `open_brain` and `fleet_ops` using `pg_dump --format=custom --compress=zstd`, dumps global roles via `pg_dumpall --globals-only`, and archives infrastructure configs (`docker-compose.yml`, `Caddyfile`, `continuwuity.toml`, `settings.json`, `presets.yaml`, `.env`).
  - Automatically replicates backups off-host via `rsync` over SSH to `tarnover:/home/l0r3zz/Dropbox/GEN-AI/AGENT-MATRIX/backups/` (which syncs to Dropbox cloud storage).
  - Built `am-ctl backup verify` to perform a non-destructive restore into ephemeral scratch databases (`open_brain_restore_verify`, `fleet_ops_restore_verify`) and verify exact row counts and `pgvector` HNSW index integrity (`pg_indexes`).

### Phase 6: Fleet Release & Image Deployment (`deploy release`, `deploy <agent>`, `deploy version`, `deploy status`)
- **Problem Solved**: `sync-fleet.sh` copied files directly from working trees into all 5 agents simultaneously without checksum verification, canary gating, or rollback tracking.
- **How It Was Built**:
  - Built `amctl/services/deployer.py` and `fleet_ops.releases` / `fleet_ops.deployments`.
  - Every release bundle is registered with its full SHA-256 manifest. During `am-ctl deploy <agent> --release <ver>`, `deployer.py` verifies source hashes, copies artifacts into the target agent's workdir while **explicitly preserving instance-local state** (`matrix-bot/.env` and `room_contexts.json`), verifies destination hashes, restarts services, and gates completion on a clean health + drift check.

### Phase 7: Preset-Aware Model Management (`models list`, `show`, `set`, `diagnose`)
- **Problem Solved**: Agent Zero v2.14 introduced a new preset architecture (`usr/Model_Presets/config.json` + `presets.yaml`) alongside `usr/settings.json`. Legacy `fleet-models.sh` only patched `settings.json`, causing model changes to be ignored or overwritten by the active preset.
- **How It Was Built**:
  - Built `amctl/services/model_manager.py` to read and atomically update `settings.json`, `Model_Presets/config.json`, and the active preset entry inside `Model_Presets/presets.yaml`, while logging every model transition in `fleet_ops.model_configs` and `audit_log`.

### Phase 8: Inside-Container Hardening (`preflight-check.sh`, `watchdog.sh` v3.0, `matrix-bot-rust`)
- **Problem Solved**: Even with an external control plane, inside-container scripts needed fail-closed startup gates, durable sync cursors across restarts, and protection against untrusted invites and self-reply loops.
- **How It Was Built**:
  - **`preflight-check.sh`**: Runs inside `run-bot-wrapper.sh` before `matrix-bot-rust` is allowed to exec. Queries `am-ctl` for expected state, validates `/whoami`, `/joined_rooms`, and `.a0-api-key`, reports results to `POST /api/v1/health/{name}/report`, and exits `78` (`TERMINAL_CONFIG`) if any invariant is violated.
  - **`watchdog.sh` v3.0**: Queries `am-ctl` for alert rules and posts container-internal health metrics to `am-ctl`.
  - **`matrix-bot-rust` Hardening**: Added atomic `sync_cursor.json` persistence (`next_batch` token + bounded 1,000 processed event IDs), removed the legacy empty-sync cursor reset bug, enforced live `/whoami` self-event suppression, enforced trigger prefixes in 2-member rooms, and wired dynamic trusted-sender invite auto-join against `GET /api/v1/trusted-senders`.

### Phase 9: Deterministic Immutable Releases & v2 Architecture (`make release`, `build-release.py`)
- **Problem Solved**: Standard `tar -czf` embeds file modification timestamps, UIDs/GIDs, and filesystem ordering, producing a different SHA-256 hash every time it runs.
- **How It Was Built**:
  - Built `scripts/build-release.py` and the `Makefile` (`make release` / `make verify-reproducible`). It normalizes every tar entry (`mtime=0`, `uid=0`, `gid=0`, `uname=""`, `gname=""`, `PAX_FORMAT`, lexicographically sorted entries) and sets `gzip` header `mtime=0`, guaranteeing byte-for-byte identical release tarballs across builds (`v1.2.0` SHA-256: `6a6572f0b6ee2e895f297c613986667c890613aab574a4be299cd0782c11c324`).
  - Added a built-in secret scanner that aborts the build if any artifact contains `syt_` or `A0_API_KEY=`.
  - Authored [am-ctl-v2-design.md](am-ctl-v2-design.md) specifying the v2 provisioning API (`create`, `finalize`, `decommission`, `rebuild`), multi-host scaling (`hosts` table + mTLS `am-node-agent`), and JWT RBAC.

<!-- GALADRIEL_TODO: Add a "Troubleshooting & Common Operator Recipes" appendix linking common symptoms (e.g., agent not replying in a room, adding a new trusted external user to fleet_ops.trusted_senders) to the exact am-ctl commands above. -->
> **[GALADRIEL EXPANSION]**
> Add **Appendix A: Operator Troubleshooting Playbook & Common Recipes** (e.g., *"Why didn't an agent reply to my message?"*, *"How to add a new external human user to `fleet_ops.trusted_senders`"*, and *"How to roll back a release with `am-ctl deploy`"*).
