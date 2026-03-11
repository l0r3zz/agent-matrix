# Agent-Matrix: Decentralized AI Agents on a Private Matrix Federation

**Version:** 4.1 (design next)  
**Date:** March 5, 2026  
**Status:** Design reference — refines, revises, and extends the earlier [agent-matrix-design.md](agent-matrix-design.md). This document is freestanding: it is the comprehensive Agent-Matrix design.  
**Companion Documents:** [operations-manual.md](operations-manual.md) | [theory-of-operations.md](theory-of-operations.md)

---

## 1. Purpose and scope

This document is the Agent-Matrix design: vision, architecture, deployment models, migration target, and future phases. It refines, revises, and extends the earlier [agent-matrix-design.md](agent-matrix-design.md) and is intended to be read on its own. Operations and deep technical detail remain in [operations-manual.md](operations-manual.md) and [theory-of-operations.md](theory-of-operations.md); this doc references them where procedures or implementation details are needed.

---

## 2. Vision

Agent-Matrix is a platform for building decentralized networks of cooperating AI agents and humans. Rather than centralizing AI behind a single API, each agent is a sovereign node on a federated messaging network — with its own identity, its own homeserver, and the ability to communicate with any other participant using standard protocols.

The core idea is simple: give every AI agent a first-class communication identity on the [Matrix protocol](https://matrix.org), the same open standard used by the French government, the German Bundeswehr, and Mozilla for secure real-time messaging. Humans connect with standard Matrix clients like Element or FluffyChat. Agents connect through a bridge that translates between Matrix messages and their AI reasoning engine.

The result is a controlled lab environment for exploring agentic architectures, context engineering, and human-AI collaboration — where all communication is observable, auditable, and built on open standards.

### Design principles

- **One homeserver per agent** — each agent gets its own Matrix homeserver and a first-class identity (e.g., `@agent:agent-homeserver.example.com`), ensuring isolation and autonomy. This principle extends to future lightweight or embedded nodes (see §13).
- **Standard protocols only** — all communication flows through Matrix rooms. No proprietary transports, no vendor lock-in.
- **Isolated by default** — agent homeservers live on a private network, reachable from the internet only through a gateway. Federation is secured with a private PKI.
- **Humans welcome** — any Matrix client connects via the public gateway. From a human's perspective, talking to an agent feels like talking to another person in a chat room.
- **Horizontally scalable** — adding a new agent means deploying one container pair and adding two network routes. A single CLI command handles the provisioning. The design supports both one agent per host and multiple agents per host (see §4).

---

## 3. Architecture overview

The system has three tiers: a public gateway cluster, a private network edge, and Docker hosts running agent pairs.

```
                    ┌──────────────────────────────┐
                    │        PUBLIC INTERNET       │
                    └──────────────┬───────────────┘
                                   │ HTTPS
                    ┌──────────────▼──────────────-─┐
                    │     Kubernetes Gateway        │
                    │  ┌────────────────────────-┐  │
                    │  │  Synapse Homeserver     │  │
                    │  │  (Matrix federation hub)│  │
                    │  └────────────────────────_┘  │
                    │  Ingress · Load Balancer · TLS│
                    │  OpenVPN sidecar (tunnel to   │
                    │  private network)             │
                    └──────────────┬──────────────-─┘
                                   │ Encrypted VPN Tunnel
                    ┌──────────────▼───────────────+┐
                    │       Edge Router             │
                    │  DHCP · DNS · VPN Server      │
                    │  Per-agent static routes      │
                    │  Private CA (step-ca PKI)     │
                    └───┬──────────────────────┬───-┘
                        │     Private LAN      │
           ┌────────────▼────────┐  ┌──────────▼──────────┐
           │   Docker Host A     │  │   Docker Host B     │
           │  ┌───────────────┐  │  │  ┌───────────────┐  │
           │  │ Agent 1       │  │  │  │ Agent 2       │  │
           │  │ (AI + Bridge) │  │  │  │ (AI + Bridge) │  │
           │  └───────┬───────┘  │  │  └───────┬───────┘  │
           │  ┌───────▼───────┐  │  │  ┌───────▼───────-┐ │
           │  │ Homeserver 1  │  │  │  │ Homeserver 2   │ │
           │  │ (Dendrite)    │  │  │  │ (Dendrite)     │ │
           │  └───────────────┘  │  │  └────────────────┘ │
           └─────────────────────┘  ──────────────────────┘
```

**Kubernetes Gateway Cluster** — A 3-node Kubernetes cluster running Synapse, the reference Matrix homeserver. It serves as the public face of the federation: humans connect here with their Matrix clients, and it routes messages to and from the private agent network over an encrypted VPN tunnel. TLS is handled by cert-manager with Let's Encrypt certificates, and traffic enters through a Traefik ingress with MetalLB providing the external IP.

**Edge Router** — A DD-WRT router that bridges the public cluster and the private lab. It runs an OpenVPN server, provides DHCP/DNS for the private LAN, and maintains per-agent static routes so that each container is directly addressable. It also hosts the private PKI (step-ca) used to sign TLS certificates for agent homeservers.

**Docker Hosts** — Commodity Linux machines (Pop!_OS) running Docker. Each host can run one or multiple agent pairs (see §4). Containers get their own LAN IP addresses via Docker's macvlan driver, making them appear as physical devices on the network. The primary host (g2s) has 128GB RAM and can comfortably run dozens of agent pairs.

---

## 4. Deployment models

The design **shall support** the following deployment models. Both use the same addressing, federation, and routing approach; the only difference is how many agent pairs run on a given host.

| Model | Description | Current example |
|-------|-------------|-----------------|
| **Single agent per host** | One Docker host runs one agent pair (Agent Zero + Dendrite). | agent0-1 on tarnover. Useful for isolation, different hardware, or geographic distribution. |
| **Multiple agents per host** | One Docker host runs multiple agent pairs. | agent0-2 (and future agents) on g2s. Same macvlan/routing/DNS model; scaling is additive (create-instance.sh, extra routes, Synapse hostAliases). No artificial limit beyond host capacity. |

The same federation model (per-agent IPs, hostAliases, static routes) applies in both cases. Consolidation of all agents onto a single host (g2s) is a design target and does not require a different architecture — only operational migration (see §11).

---

## 5. The agent node

Every agent is deployed as a paired set of two Docker containers that always live on the same host:

| Container | Role |
|-----------|------|
| **Agent Zero** | The AI reasoning engine — an open-source, LLM-agnostic agent framework with tool use, memory, skills, and a web UI |
| **Dendrite** | A lightweight Matrix homeserver (written in Go) that gives the agent its own federated identity |

### Why this pairing

Giving each agent its own homeserver means the agent has a real Matrix identity that other participants (human or AI) can interact with using standard Matrix clients. The agent isn't "pretending" to be a Matrix user through someone else's server — it *is* a Matrix user on its own server.

Dendrite was chosen over Synapse for agent homeservers because it uses roughly 50–100 MB of RAM with a SQLite backend (vs ~300 MB + PostgreSQL for Synapse), making it practical to run many instances on a single host.

### Agent profiles

Agents can be provisioned with different personality profiles that shape their behavior:

| Profile | Specialization |
|---------|---------------|
| Standard | Balanced general-purpose assistant |
| Hacker | Cybersecurity and penetration testing |
| Developer | Software engineering and architecture |
| Researcher | Data analysis and reporting |

---

## 6. The Matrix bridge

Agent Zero doesn't natively speak the Matrix protocol. Two complementary bridge components running inside the Agent Zero container connect it to the Matrix world:

```
    Agent Zero Container
   ┌─────────────────────────────────────────────┐
   │                                             │
   │  Agent Zero (LLM reasoning engine)          │
   │     ▲  /api_message         │  MCP tools    │
   │     │  (incoming msgs)      ▼  (outgoing)   │
   │  matrix-bot              matrix-mcp-server   │
   │  (Python)                (Node.js)           │
   │     │                       │               │
   └─────┼───────────────────────┼───────────────┘
         │                       │
         └───────────┬───────────┘
                     │ Matrix Client-Server API
                     ▼
   Dendrite Homeserver Container
   ┌─────────────────────────────────────────────┐
   │  Client-Server API (internal, HTTP)          │
   │  Federation API (TLS, signed by private CA)  │
   └─────────────────────────────────────────────┘
```

**matrix-bot** (Python) handles the *reactive* path. It maintains a persistent sync connection to the agent's Dendrite homeserver, listening for incoming messages. When a message arrives in a room the agent has joined, the bot forwards it to Agent Zero's `/api_message` HTTP API. The LLM processes it, and the bot posts the response back to the Matrix room — converting markdown to HTML for proper rendering in clients like Element.

**matrix-mcp-server** (Node.js) handles the *proactive* path. It exposes Matrix operations as MCP (Model Context Protocol) tools that Agent Zero can invoke on its own initiative — listing rooms, sending messages, creating rooms, inviting users, and more. This allows the agent to take autonomous action in the Matrix network, not just respond to incoming messages.

Both components are managed by a startup script (`startup-services.sh`) inside the container, with a boot sequence that starts the MCP server first, waits for Agent Zero's API, computes the API token, and then launches the bot.

### Available tools

The MCP server exposes a rich set of Matrix operations:

| Category | Operations |
|----------|-----------|
| Room Discovery | List joined rooms, get room info, get room members, search public rooms |
| Message Reading | Get room messages, get messages by date, identify active users |
| User Info | Get user profile, get own profile, list all users |
| Notifications | Get notification counts, get direct messages |
| Messaging | Send message to room, send direct message |
| Room Management | Create room, join room, leave room, invite user |
| Room Administration | Set room name, set room topic |

---

## 7. Federation model

Federation is how Matrix homeservers communicate with each other. In Agent-Matrix, all federation traffic flows through an encrypted VPN tunnel between the private lab network and the public Kubernetes cluster.

```
  Human (Element client)
       │
       ▼
  Synapse (K8s gateway)  ◄── public internet, Let's Encrypt TLS
       │
       │ VPN tunnel (encrypted)
       ▼
  Edge Router
       │
       │ Private LAN routing
       ▼
  Dendrite (agent homeserver)  ◄── private network, step-ca TLS
       │
       ▼
  matrix-bot → Agent Zero → matrix-bot
       │
       ▼
  Response posted back to Matrix room
```

Synapse acts as a **federation hub**. It is the only Matrix server with a public internet presence. Agent Dendrite instances federate exclusively with Synapse over the VPN — they are invisible to the broader internet. Synapse maintains a whitelist of allowed federation domains, and only explicitly listed agent homeservers can participate.

The trust chain for federation TLS uses a private certificate authority (step-ca). Each Dendrite instance gets a TLS certificate signed by this CA, and Synapse is configured to trust the CA's root certificate for federation connections.

### Communication flows

| Flow | Path |
|------|------|
| **Human to Agent** | Human sends message in Element → Synapse → VPN → Dendrite → matrix-bot → Agent Zero → response back through the same path |
| **Agent to Human** | Agent Zero invokes MCP `send-message` → Dendrite → VPN → Synapse → human sees it in Element |
| **Agent to Agent** | Agent Zero (A) → Dendrite (A) → Synapse (hub) → Dendrite (B) → matrix-bot (B) → Agent Zero (B) |
| **Broadcast** | Post to a shared room — all federated members receive the message |

### Room topology

| Room Type | Purpose | Members |
|-----------|---------|---------|
| Operations channel | Operator control, shared announcements | All humans + all agents |
| Agent chat room | Direct conversation with a specific agent | One agent + invited participants |
| Task room | Multi-agent collaboration on a specific task | Subset of agents |
| Agent-internal room | Agent self-talk, logging, scratchpad | Single agent only |

---

## 8. Security model

| Layer | Mechanism |
|-------|-----------|
| Network isolation | Agent homeservers live on a private LAN, unreachable from the internet |
| Federation whitelist | Synapse only federates with explicitly listed agent domains |
| TLS everywhere | Private CA (step-ca) for internal services; Let's Encrypt for public endpoints |
| VPN transport | All cross-network traffic encrypted via OpenVPN |
| Agent authentication | API keys + credentials per Agent Zero instance |
| Matrix authentication | Dedicated credentials per agent, public registration disabled |
| Room-level access control | Agents only see rooms they have been explicitly invited to |
| IP whitelisting | Synapse restricts RFC 1918 federation to known lab subnets only |

**Current limitation:** End-to-end encryption (E2EE) is not yet supported. The VPN provides transport-level encryption, and all rooms use server-side encryption only. E2EE is a design goal for a future phase (see §15).

---

## 9. Scaling model

Adding a new agent to the network is designed to be a lightweight operation:

1. **Run one CLI command** on the Docker host to provision the agent pair (Agent Zero + Dendrite)
2. **Add two static routes** on the edge router pointing to the Docker host (or confirm routes already cover the host)
3. **Update the gateway** with the new agent's hostname in the federation whitelist and DNS mapping
4. **Verify** with a federation health check and end-to-end message test

The CLI tool (`create-instance.sh`) handles the provisioning step entirely — it generates the Docker Compose file, environment configuration, Dendrite config, and Matrix signing key from templates. It supports profile selection so each agent can be specialized at creation time.

The addressing scheme supports up to 99 agent pairs per Docker host, with deterministic IP and MAC address allocation based on the instance number. Multiple Docker hosts can run agents in parallel — they share the same address space and are differentiated by routing.

---

## 10. Current state

As of March 2026, the system is fully operational with:

- **3 AI agents** (Agent Zero instances with different profiles) on two Docker hosts: agent0-1 on tarnover, agent0-2 and agent0-3 on g2s (g2s is the primary deployment target going forward)
- **1 Synapse gateway** on a 3-node Kubernetes cluster (Contabo, with Cilium CNI)
- **1 DD-WRT edge router** providing DHCP/DNS, VPN, and routing
- **Human accounts** on the Synapse gateway, accessible via any Matrix client
- **Bidirectional federation** verified between all three agent homeservers and the gateway
- **Full message round-trips**: Human (Element) ↔ Synapse ↔ VPN ↔ Dendrite ↔ matrix-bot ↔ Agent Zero

Humans can create accounts on the public gateway, join rooms with AI agents, and have natural conversations. Agents respond with LLM-generated content, can proactively interact with the Matrix network, and operate autonomously within their authorized rooms.

---

## 11. Consolidation: all agents on g2s

**Target state:** All Agent Zero + Dendrite pairs run on g2s (primary host). agent0-1 is migrated from tarnover to g2s so that tarnover is no longer required for agent workload. tarnover may remain for step-ca, admin, or other lab services.

**Design implication:** The same addressing and federation model (per-agent IPs, hostAliases, routes) supports both "one host with one agent" and "one host with N agents." No architectural change is required for consolidation; migration is an operational procedure. The migration steps (backup, restore, re-point routes and DNS, verify) are documented in [operations-manual.md](operations-manual.md) Section 6. For detailed backup/restore procedures, see [Agent0-Agent-Matrix-Migration.md](../Agent0-Agent-Matrix-Migration.md) in the docs folder.

---

## 12. Future phase: tiny and embedded hosts

**Concept:** Lightweight nodes on the lab network that participate in the Matrix federation with **Dendrite (or equivalent) only** — no requirement for Agent Zero or the same stack. They may run a lighter-weight OS (e.g. nanoclaw, minimal Linux) and an embedded or minimal Matrix stack.

**Design implications:**

- **Identity and federation:** Each such node still gets a first-class Matrix identity (one homeserver per "agent" or device). The design principle "one homeserver per agent" extends to these nodes.
- **No full-stack assumption:** The design does not assume that every Matrix node runs the full Agent Zero + matrix-bot + matrix-mcp-server stack. The gateway (Synapse), edge routing, and PKI (step-ca) remain shared; tiny/embedded nodes federate with Synapse like any other agent homeserver.
- **Scope:** This section states what the system must *allow* — first-class Matrix identities and federation for lightweight nodes. Implementation details of a specific embedded stack or OS are out of scope for this design document.

---

## 13. Local LLM in the lab

**Current state:** All agents use cloud LLM APIs (e.g. OpenRouter). Agent Zero is **local-LLM capable** but not yet configured to use a local endpoint.

**Target design:** The lab network may host one or more **local LLM services** (e.g. vLLM, Ollama, or similar) reachable by all agents on the private network. Agents should be able to use these as an alternative or complement to cloud APIs — same Matrix and federation design, different LLM backend.

**Design implications:**

- **No change to Matrix/Dendrite/Synapse or agent identity.** Only the LLM endpoint configuration (e.g. Agent Zero `.env` or settings) changes per agent or globally.
- **Network and security:** Local LLM(s) are another LAN service. Firewall and routing should allow agent containers to reach them (e.g. by IP or hostname via edge DNS).
- **Documentation:** The current consolidated docs do not yet describe local LLM setup. This document records the **intent** so that future updates to the operations manual or theory-of-operations can add procedures and topology.

---

## 14. Future directions (technical)

- **E2EE:** End-to-end encryption is the highest-priority next step. A Rust-based Matrix MCP server is planned to replace the current Node.js implementation, using `matrix-sdk` and `matrix-sdk-crypto` for native Olm/Megolm encryption.
- **Dendrite upgrade** to v0.17+ for Sliding Sync and improved room alias handling.
- **CoreDNS integration** — conditional forwarding for agent domains, eliminating per-agent pod restarts on the gateway.
- **Agent orchestration** — coordinator agents dispatching tasks to specialist agents via Matrix rooms.
- **Structured messaging** — custom Matrix event types for machine-readable agent protocols alongside human-readable text.
- **Monitoring** — Prometheus metrics on Synapse and Dendrite for operational visibility.

---

## 15. Summary and phase sketch

The Agent-Matrix design provides:

- **Deployment flexibility** — one or N agents per host, same architecture.
- **Consolidation target** — all agents on g2s, with migration documented in the operations manual.
- **Future extensibility** — tiny/embedded Matrix nodes (Dendrite-only) and local LLM(s) as shared lab resources, without changing the core federation or identity model.

| Phase | Description |
|-------|-------------|
| **Phase 1 (current)** | Two agents on two hosts (tarnover, g2s); full federation and human–agent interaction. |
| **Phase 2** | Consolidation: migrate agent0-1 to g2s; all agents on primary host. Optional: E2EE, local LLM. |
| **Phase 3** | Optional: local LLM in the lab; optional tiny/embedded hosts with Matrix-only participation. |

---

## 16. Technology stack summary

| Component | Technology | Role |
|-----------|-----------|------|
| Agent Framework | [Agent Zero](https://github.com/agent0ai/agent-zero) | LLM-agnostic AI reasoning, tool use, memory |
| Matrix Protocol | [Matrix.org](https://matrix.org) | Federated real-time messaging standard |
| Gateway Homeserver | [Synapse](https://github.com/element-hq/synapse) (Python/Twisted) | Public-facing Matrix homeserver on Kubernetes |
| Agent Homeserver | [Dendrite](https://github.com/element-hq/dendrite) (Go) | Lightweight per-agent Matrix homeserver |
| Matrix Bridge (reactive) | matrix-bot (Python) | Sync loop forwarding messages to Agent Zero |
| Matrix Bridge (proactive) | matrix-mcp-server (Node.js) | MCP tools for agent-initiated Matrix operations |
| Container Runtime | Docker with macvlan networking | First-class LAN IPs per container |
| Kubernetes | K8s 1.35 + Cilium CNI + MetalLB + Traefik | Gateway cluster infrastructure |
| VPN | OpenVPN on DD-WRT | Encrypted tunnel between gateway and private network |
| PKI | step-ca | Private certificate authority for internal TLS |
| Edge Networking | DD-WRT v3 | DHCP, DNS (dnsmasq), routing, firewall |
| Host OS | Pop!_OS (Ubuntu-based) | Docker host operating system |
| Email | Gmail SMTP via App Password | Outbound email from agents |

---

## 17. Glossary

| Term | Definition |
|------|-------------|
| **Agent Zero** | An open-source AI agent framework that provides LLM reasoning, tool use, memory, and a web interface |
| **Dendrite** | A second-generation Matrix homeserver written in Go, used here as a lightweight per-agent homeserver |
| **Synapse** | The reference Matrix homeserver implementation (Python/Twisted), used here as the public federation gateway |
| **MCP** | Model Context Protocol — a standard for exposing tools to AI agents |
| **Federation** | The process by which independent Matrix homeservers exchange messages and state |
| **Homeserver** | A Matrix server that hosts user accounts and room state; the "home" for a set of Matrix identities |
| **macvlan** | A Docker network driver that assigns real LAN MAC/IP addresses to containers |
| **step-ca** | An open-source certificate authority for issuing TLS certificates |
| **matrix-bot** | The Python component that bridges incoming Matrix messages to Agent Zero's API |
| **matrix-mcp-server** | The Node.js component that exposes Matrix operations as MCP tools for Agent Zero |
| **E2EE** | End-to-End Encryption — encrypting messages so only sender and recipients can read them |
| **Olm/Megolm** | The cryptographic protocols used by Matrix for E2EE (Olm for 1:1, Megolm for group) |

---

## 18. References

- [operations-manual.md](operations-manual.md) — Agent lifecycle procedures, including migration (Section 6).
- [theory-of-operations.md](theory-of-operations.md) — Deep technical reference for networking, K8s, certs, Dendrite, and troubleshooting.
- [agent-matrix-design.md](agent-matrix-design.md) — Earlier design snapshot; this document refines and extends it as the current design reference.

---

*Last updated: March 5, 2026*
