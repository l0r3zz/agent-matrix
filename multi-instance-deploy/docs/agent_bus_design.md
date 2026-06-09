# Federated Agent Bus Design for Local Agent Swarms

## Overview

This document proposes a lightweight, open-source messaging and orchestration layer for a swarm of software agents running primarily on a single host, with a clear path to federation across multiple hosts. The recommended baseline architecture uses one small, always-on sidecar container per host that provides a local message fabric, security boundary, and federation gateway, rather than embedding all transport logic separately into every agent process.

There is no canonical industry-standard “agent swarm bus” today; common practice is to choose a minimal messaging substrate, define a small envelope protocol, and layer authentication, encryption, and delivery semantics on top.[cite:3][cite:6][cite:9]

## Goals

- Support direct agent-to-agent messaging on a single host.
- Preserve a simple migration path to multi-host federation.
- Keep setup and operational overhead low.
- Allow Protobuf as the application message format.
- Support encrypted communications and lightweight agent authentication.
- Prefer in-memory operation with no durability requirement.
- Avoid heavyweight brokers such as RabbitMQ.

## Non-Goals

- Long-term message retention or event sourcing.
- Cross-region WAN optimization.
- Exactly-once delivery semantics.
- Rich workflow authoring or LLM-specific planning frameworks.
- A full service mesh with policy enforcement, tracing, and mTLS issuance.

## Recommended Architecture

The recommended design is a **host-local agent bus sidecar**: one standalone container per host, exposing a small local messaging API to agents on that host, and optionally federating with peer sidecars on other hosts. NATS is the strongest default substrate for this design because it is lightweight, open source, supports pub/sub and request-reply, and includes TLS and authentication primitives in a small deployable server.[cite:3]

Each host runs:

- One `agent-bus` sidecar container.
- Many local agents connecting only to that sidecar.
- Optional federated links from the sidecar to peer sidecars on other hosts.

This creates a topology where agents do not need to know about remote agents directly. Instead, they publish to local subjects or send directed requests through the local sidecar, which can route locally or federate outward.

## Why NATS fits this pattern

NATS is designed as a lightweight messaging system with publish-subscribe and request-reply communication patterns, which map cleanly to agent broadcast, task dispatch, and direct RPC-style messaging.[cite:3] It also supports TLS-secured connections and authentication mechanisms, which reduces the amount of custom transport security code required in the agent framework.[cite:3]

Compared with brokerless libraries such as ZeroMQ, NATS introduces a small always-on server, but in return it centralizes security, naming, routing, and future federation concerns in one place.[cite:3][cite:9] Compared with libp2p pubsub, it is operationally simpler for a host-centric design, while still leaving room to expand to multi-host deployments later.[cite:3][cite:6]

## Alternatives considered

| Option | Fit for single host | Federation path | Built-in encryption/auth | Operational model | Assessment |
|---|---|---|---|---|---|
| ZeroMQ | Strong[cite:9] | Manual | Limited; generally layered separately[cite:9] | Brokerless library | Excellent for pure local IPC, weaker for host-level federation |
| nng / nanomsg family | Strong[cite:9] | Manual | Limited | Brokerless library | Similar trade-offs to ZeroMQ |
| NATS | Strong[cite:3] | Good via clustered or bridged topologies[cite:3] | Yes, via TLS/auth[cite:3] | Small sidecar/broker | Best balance for this design |
| libp2p pubsub | Acceptable[cite:6] | Strong[cite:6] | Yes; encrypted peer messaging is part of the model[cite:6] | Peer-to-peer library | Better if peer-to-peer federation is the primary requirement from day one |
| Agent orchestration frameworks | Weak as a transport substrate[cite:7][cite:8] | Varies | Framework-specific | Workflow/runtime layer | Better on top of a bus, not instead of one |

## Logical model

The sidecar should expose three logical primitives:

1. **Publish/subscribe** for broadcasts, heartbeats, capability announcements, and event fan-out.
2. **Request/reply** for direct agent-to-agent interactions and tool invocation.
3. **Directed inboxes** for addressing specific agents or logical roles.

A practical naming model is subject-based routing, for example:

- `agent.<agent_id>.inbox`
- `role.<role_name>`
- `topic.<domain_event>`
- `host.<host_id>.control`
- `federation.<remote_host_id>.*`

NATS subjects map naturally onto this style of addressing.[cite:3]

## Message envelope

Application payloads should remain opaque Protobuf bytes, while the bus envelope carries routing and control metadata. A small envelope allows transport-agnostic evolution over time.

Suggested envelope fields:

- `message_id`: unique identifier for deduplication and tracing.
- `correlation_id`: links replies to requests.
- `source_agent_id`: stable sender identity.
- `target`: agent ID, role, or topic.
- `target_kind`: enum such as `AGENT`, `ROLE`, `TOPIC`.
- `content_type`: logical schema identifier or message type.
- `payload`: serialized Protobuf message bytes.
- `deadline` or `ttl_ms`: drop-expired semantics.
- `requires_ack`: whether the receiver must acknowledge processing.
- `hops`: optional federation hop count.
- `signature` or `auth_tag`: optional message integrity field above transport security.

This keeps Protobuf as the application contract while avoiding transport lock-in.

## Reliability model

Guaranteed delivery should be defined carefully. Most lightweight buses can give reliable transport delivery to connected consumers, but true end-to-end guaranteed processing requires an application-level acknowledgment protocol.

A practical reliability model for this design is:

- At-least-once delivery.
- Message IDs for deduplication.
- Receiver acknowledgments at the application layer.
- Sender retry with timeout and backoff.
- Idempotent handlers for all side-effecting operations.

This is more realistic than attempting exactly-once semantics in a lightweight swarm fabric. NATS provides core messaging primitives, but end-to-end delivery guarantees for agent workflows should still be expressed in the application protocol.[cite:3]

## Security model

The sidecar should be the trust anchor on each host. Agents authenticate to the local sidecar, and sidecars authenticate to other sidecars.

Recommended security approach:

- Use TLS for agent-to-sidecar and sidecar-to-sidecar connections, which NATS supports natively.[cite:3]
- Give each agent a unique credential, ideally a certificate or signed token bound to an `agent_id`.[cite:3]
- Authorize publish and subscribe permissions by subject namespace, so an agent can only use its inbox, approved roles, and approved topics.[cite:3]
- Treat sidecar federation as a separate trust domain with narrower credentials and explicit host identity.

If message-level cryptographic isolation between agents is desired beyond transport encryption, encrypt the Protobuf payload itself using sender/receiver keys, and let the sidecar route opaque ciphertext. That is optional for a single administrative domain but useful when stronger compartmentalization is required.

## Federation model

The sidecar should be designed as a host gateway, not just a local broker. Federation can be introduced incrementally.

Recommended federation rules:

- Keep all agents connected only to their local host sidecar.
- Sidecars exchange only explicitly federated subjects or routed directed messages.
- Avoid full mesh broadcast across hosts unless required; start with allowlisted subject prefixes.
- Attach `host_id`, hop count, and origin metadata to federated messages.
- Enforce loop prevention and duplicate suppression using message IDs.

This model preserves local simplicity while allowing the swarm to expand host by host.

## Deployment model

A minimal deployment per host consists of one containerized sidecar and any number of local agents. On Kubernetes, the sidecar can run as a pod-level sidecar for tightly coupled agent groups or more commonly as a small per-node or per-host service. On plain Docker or systemd-managed hosts, one standalone container per host is the simplest operational shape.

Suggested host responsibilities:

- Terminate TLS.
- Expose a stable local endpoint, such as localhost TCP or Unix domain socket where supported by the client library.
- Maintain subject ACLs and credentials.
- Bridge approved traffic to remote host sidecars.
- Export health and metrics endpoints.

## Suggested subject conventions

| Purpose | Subject pattern | Notes |
|---|---|---|
| Direct inbox | `agent.<agent_id>.inbox` | Point-to-point logical addressing |
| Role dispatch | `role.<role_name>` | Multiple subscribers possible |
| Broadcast events | `topic.<event_name>` | For announcements and fan-out |
| Request/reply | `agent.<agent_id>.rpc.<method>` | Request subject plus reply inbox |
| Host control | `host.<host_id>.control` | Sidecar administration channel |
| Federation bridge | `federation.<host_id>.<scope>` | For remote routing and policy |

## Operational constraints and trade-offs

This design intentionally chooses a small broker over a pure library approach. The trade-off is one extra always-on container per host in exchange for simpler security, naming, observability, and future federation.

Key trade-offs:

- **Pros**: simple agent code, centralized auth, clean multi-host growth path, transport abstraction, easy local development.
- **Cons**: one more moving part, broker lifecycle management, subject taxonomy design, and eventual cluster/federation policy complexity.

For message sizes in the 32-byte to 2-megabyte range, opaque binary payload transport is natural and compatible with Protobuf-oriented application schemas.[cite:3] Performance is unlikely to be the limiting factor given the stated requirements, so maintainability and security should drive the design.

## Implementation guidance

A practical first version should include:

- A shared Protobuf envelope schema.
- A small client SDK for Rust and Python that wraps connection setup, auth, subject naming, retries, and acks.
- A sidecar configuration file defining host identity, certificates, federated peers, and subject ACLs.
- Health endpoints and minimal metrics for connected agents, message counts, retry counts, and federated link status.

Recommended implementation order:

1. Single-host local sidecar with direct inbox and pub/sub.
2. Request/reply plus application-level acknowledgments.
3. Per-agent credentials and ACLs.
4. Federation between two hosts with allowlisted subjects.
5. Duplicate suppression, hop limits, and observability improvements.

## Decision

The recommended baseline is **one NATS-based agent-bus sidecar container per host**, using Protobuf envelopes, TLS-secured agent authentication, subject-based routing, and application-level acknowledgments for at-least-once delivery.[cite:3] This is the simplest design that satisfies the current single-host requirement while preserving a realistic path to federated multi-host operation without committing to a heavyweight enterprise broker.[cite:3][cite:6][cite:9]
