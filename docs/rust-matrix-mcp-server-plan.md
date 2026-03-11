# Compressed Roadmap for Rust Matrix MCP Server (Phase 2)

You have 4–6 hours/day and AI will do most of the coding. Your time should focus on specs, reviews, and debugging, while AI executes most implementation and test scaffolding.

---

## Your role vs. AI’s role

**You focus on:**

- Writing and refining the spec‑kit specs for:
  - v1 API compatibility with `matrix-mcp-server`.
  - v2 E2EE (encrypted private rooms, Olm/Megolm behavior).
- Architectural decisions:
  - Crypto model, device identity, key storage, rollout strategy.
- Code review and debugging:
  - Integration with Agent‑Matrix, Dendrite, networking, and federation.

**AI focuses on:**

- Generating Rust MCP server code around the Rust MCP SDK.
- Wiring Matrix client + E2EE using `matrix-sdk` / `matrix-sdk-crypto` per your specs.
- Filling in tests, glue code, and scaffolding under spec‑kit guidance.

The main loop is: **spec → plan → tasks → implement (AI) → review/debug (you)**.

---

## Week 1 – Specs and API Parity (your heaviest thinking week)

Focus your daily time on capturing intent and constraints, not code.

### Day 1–2: v1 compatibility spec

- Lock down the **v1 compatibility spec**:
  - Enumerate all tools from the existing `matrix-mcp-server` (rooms, messages, users, room mgmt, admin).
  - Capture: tool name, parameters, response shape, auth, and error semantics.
- Use spec‑kit to scaffold a spec file that describes these tools exactly as they work now.
- Output: `matrix-mcp-v1.yml` (or similar) as the contract for both TS and Rust implementations.

### Day 3–4: v2 E2EE spec stub

- Create a **v2 E2EE spec stub**:
  - High‑level goals:
    - Encrypted private rooms for agents and humans.
    - MCP server acts as a Matrix device with its own keys.
    - Encrypted agent‑internal rooms (self‑talk, logs).
  - List new tools/behaviors, for example:
    - `bootstrap_e2ee`
    - `create_encrypted_private_room`
    - `get_encryption_status`
    - E2EE‑aware `send_message` / `get_room_messages` semantics.
- Don’t worry about exact Rust code yet; focus on API shapes and behavior.
- Use spec‑kit’s planning features to break v1 and v2 into small tasks for AI.

### Day 5: Align with Agent‑Matrix design

- Cross‑check both specs against the Agent‑Matrix design document:
  - Per‑agent Dendrite homeserver.
  - VPN and TLS/PKI constraints.
  - Phase‑2 requirement “E2EE support, Olm crypto store in matrix-mcp-server.”
- Make these constraints explicit in the specs as non‑functional requirements.

**Outcome by end of Week 1**

- Spec‑kit specs ready for AI:
  - One for **v1 parity**.
  - One for **v2 E2EE**.
- A task list (from spec‑kit) you can feed to AI in small, focused chunks.

---

## Week 2 – Rust MCP + Matrix (unencrypted) with v1 subset

Now your time is mostly review and integration.

### AI tasks (driven by your specs)

- Scaffold a Rust MCP server:
  - Use the official Rust MCP SDK and reference examples.
- Integrate `matrix-sdk` as a Matrix client talking to your Dendrite homeserver:
  - Initially handle **only unencrypted** rooms.
- Implement a **core v1 subset**:
  - `list_joined_rooms`
  - `get_room_messages` (unencrypted only)
  - `send_message`
  - `create_room`

### Your 4–6 hours/day

- Use spec‑kit to verify that each implemented tool matches the v1 spec exactly:
  - Names, parameters, responses, error patterns.
- Integrate the Rust MCP server into a single Agent Zero instance:
  - Replace or run alongside the TS `matrix-mcp-server`.
  - Keep existing macvlan networking and Dendrite topology.
- Run the **Phase‑1 unencrypted flows** end‑to‑end:
  - Human in Element → Synapse → Dendrite → Rust MCP → Agent Zero → back.

**Outcome by end of Week 2**

- Rust MCP server in place for a **subset** of v1 tools, working in unencrypted rooms with Agent Zero.
- First contract tests green for those tools, against both TS and Rust implementations.

---

## Week 3 – Full v1 Parity and Switch‑over

You’re mainly doing reviews, test runs, and targeted fixes.

### AI tasks

- Implement all remaining v1 tools defined in `matrix-mcp-v1.yml`:
  - Room admin operations, notifications, user profile tools, etc.
- Add contract tests:
  - Run against TS `matrix-mcp-server` as the reference.
  - Run against Rust `matrix-mcp-server` as the new implementation.
  - Fix mismatches until both conform to the same spec.

### Your 4–6 hours/day

- Run contract test suites, interpret failures, and guide AI to patch them.
- Perform a **full Agent‑Matrix Phase‑1 regression**:
  - Human ↔ Agent Zero ↔ Matrix in unencrypted rooms, covering:
    - Listing rooms.
    - Sending messages.
    - Room joins/invites.
- Decide when Rust can fully replace the TS server for v1:
  - Document how to switch and how to roll back if needed.

**Outcome by end of Week 3**

- Rust implementation has **full v1 parity** and is the default MCP server in Agent‑Matrix containers.
- TS server becomes optional or removed from the primary path.

---

## Week 4 – E2EE v2 Design + Initial Implementation

Your time shifts back toward design choices and debugging crypto/integration issues.

### AI tasks

- Implement E2EE plumbing with `matrix-sdk-crypto`:
  - Persistent store for device keys and Olm/Megolm sessions.
  - Key upload and initial E2EE bootstrap.
  - Decryption of incoming encrypted events.
- Implement the first v2 tools from your spec:
  - `bootstrap_e2ee` (or equivalent):
    - Publish device identity and keys.
  - `create_encrypted_private_room`:
    - Set `m.room.encryption` state, invite relevant users.
  - E2EE‑aware `send_message` / `get_room_messages`:
    - Automatically encrypt/decrypt based on room state.

### Your 4–6 hours/day

- Refine the v2 spec as real implementation details emerge:
  - How to expose encryption state.
  - How to encode decryption failures in API responses.
- Set up **test rooms**:
  - One encrypted “agent‑internal” room per agent (replacing unencrypted self‑talk).
  - One encrypted human–agent DM.
- Debug E2EE edge cases:
  - Key storage and migration.
  - Initial sync issues.
  - “Unable to decrypt” events and device/key mismatches.

**Outcome by end of Week 4**

- Working E2EE flow for at least:
  - Creating encrypted private rooms.
  - Sending/receiving encrypted messages via MCP in those rooms.
- v2 spec refined and aligned with actual behavior.

---

## Week 5 – Hardening and Rollout (buffer week)

If things go smoothly, this is polish; if not, it’s your buffer for E2EE issues.

### AI tasks

- Expand v2 coverage:
  - Additional E2EE tools (status, optional key backup, diagnostics).
  - Tests for error paths and recovery flows.
- Improve ergonomics:
  - Logging around E2EE failures.
  - Config flags for enabling/disabling v2 features.

### Your 4–6 hours/day

- Update operations docs (e.g., `agent-matrix-ops-guide.md`):
  - Deploying the Rust MCP server.
  - Managing keys and stores.
  - Verifying E2EE works in practice.
- Define a **gradual rollout plan**:
  - Default agents to v1 tools.
  - Enable v2 E2EE per agent or per room via configuration.
- Final spec‑kit cleanup:
  - Make sure specs are clear, versioned, and ready for future AI‑driven work (e.g., Go port or new features).

**Outcome by end of Week 5**

- Phase‑2 E2EE requirement is met by the Rust MCP server with v2 API.
- You have:
  - Stable v1 and v2 specs.
  - A clear ops story.
  - A pattern for future AI‑assisted development using spec‑kit.
