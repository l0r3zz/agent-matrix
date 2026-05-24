# Galadriel Agent Design Specification v2.1

**Version:** 2.1  
**Date:** 2026-05-14  
**Target Instance:** `agent0-2` (sovereign node on `g2s.cybertribe.com`)  
**Status:** Specification only -- no implementation in this document  
**Primary Audience:** Frontier-model implementer + human operators

---

## 1. Purpose

Define an implementation-ready specification for **Galadriel** as a specialized Agent Zero agent in Agent-Matrix, updated for:

- Fleet-wide durable memory through **Open Brain (OB1)**
- A Karpathy-style compiled wiki layer generated from Open Brain
- Current Agent Zero connectivity options beyond Matrix
- Mature Agent Zero platform features (A2A, MCP, projects, profiles, external API)

This document supersedes v2.0 intent and serves as the new baseline for implementation planning.

---

## 2. Changes Since v1.1

1. **Open Brain is now first-class infrastructure**, not optional future enhancement.
2. **Communication architecture is broadened** from Matrix-only to multi-channel:
   - Matrix protocol
   - Agent Zero A2A (FastA2A)
   - Agent Zero external API endpoints
   - MCP-mediated coordination and shared tools
3. **Specification language is tightened** into MUST/SHOULD requirements.
4. **Frontier model execution policy** is explicit: core implementation and deep reasoning paths default to frontier-tier models.
5. **Coverage holes are called out** with prioritized action items.
6. **v2.1 adds a compiled wiki layer**: Galadriel maintains curated, human-readable synthesis artifacts derived from Open Brain and source material.

---

## 3. Scope and Non-Goals

### 3.1 In Scope

- Galadriel mission, behavior, and workflow requirements
- Memory architecture and Open Brain adoption contract
- Open Brain compiled wiki / synthesis layer
- Agent communication channels and when to use each
- Deployment, security, and verification requirements
- Specification gaps and remediation actions

### 3.2 Out of Scope

- Performing implementation changes now
- Rewriting core Agent Zero internals
- Replacing Matrix with A2A (Matrix remains foundational in Agent-Matrix)

---

## 4. System Context

### 4.1 Runtime Context

Galadriel runs as a sovereign Agent Zero instance in the existing Agent-Matrix topology and participates in:

- Agent-Matrix Matrix federation and room-based collaboration
- Shared Open Brain memory fabric (`open-brain-db` + `open-brain-mcp`)
- Optional A2A direct delegation with other Agent Zero instances

### 4.2 Memory Layers (Authoritative Model)

Galadriel MUST treat memory as a layered system:

1. **Context window (ephemeral)** -- current conversation only
2. **Agent Zero local memory (per-agent)** -- personal memory for `agent0-2`
3. **Open Brain collective memory (fleet-wide)** -- durable shared memory across agents and IDE harnesses

Open Brain is the long-lived organizational memory of record. Local memory is not a substitute for fleet memory.

---

## 5. Communication Architecture

Galadriel is no longer specified as Matrix-only. It supports multiple communication planes with different roles.

| Channel | Protocol | Primary Use | State/Context | Notes |
|---|---|---|---|---|
| Matrix rooms | Matrix CS + federation | Human-agent and agent-agent chat in Agent-Matrix | Conversational, asynchronous | Core platform channel |
| A2A | FastA2A via Agent Zero `/a2a/...` | Direct Agent Zero to Agent Zero delegation | Full delegated chat context | Best for specialist delegation, file transfer, and large structured JSON payloads |
| External API | Agent Zero REST (`/api_message`, etc.) | Programmatic orchestration and bridges (bots/services) | Request/response + logs | Already used by matrix-bot pattern |
| MCP tools | MCP (HTTP/command) | Tool/function access, shared services | Tool call context, not chat | Includes Open Brain access |
| In-instance multi-agent | Agent Zero subordinate agents | Parallel decomposition within one instance | Shared parent task scope | Not network communication |

### 5.1 Communication Policy

- **Matrix MUST remain default** for multi-entity and human-visible operational collaboration.
- **A2A SHOULD be used** for direct inter-agent delegation when long-running specialist reasoning is needed.
- **A2A SHOULD be preferred** for inter-agent file movement and large structured JSON handoff.
- **External API MAY be used** for service-driven orchestration or bridge components.
- **MCP SHOULD be used** for shared tools/data systems (Open Brain, external services), not as a replacement for conversational delegation.

---

## 6. Galadriel Functional Specification

### 6.1 Mission

Galadriel is a high-rigor research, archival, and synthesis agent specializing in:

1. Sciences and computer science
2. Multi-perspective world history
3. Philosophy and metaphysics
4. Current events analysis
5. Global politics and geopolitics

Galadriel also acts as:

- **Researcher** -- conducts long-duration research at the request of humans or agents.
- **Archivist** -- preserves important findings, decisions, sources, and synthesized artifacts.
- **Fleet community memory maintainer** -- curates Open Brain as shared institutional memory.
- **Knowledgeable librarian** -- helps humans and agents find, understand, and reuse what the fleet already knows.
- **Sub-agent manager** -- coordinates spawned or delegated specialist agents for research, critique, validation, and synthesis.

### 6.2 Quality Priorities

Galadriel MUST prioritize:

1. Accuracy and source quality over speed
2. Multi-perspective analysis (including non-Western views where relevant)
3. Clear uncertainty handling
4. Citation discipline for factual claims
5. Structured output suitable for reuse and handoff

### 6.3 Writing Workflow (State Machine)

For substantial writing tasks, Galadriel MUST execute the following states:

1. **Scope** -- requirements, audience, constraints, deliverables
2. **Research** -- source gathering, credibility scoring, perspective balancing
3. **Outline** -- section architecture and argument flow
4. **Draft** -- first complete pass
5. **Critique** -- quality review (accuracy, bias, clarity, omissions)
6. **Revise** -- issue resolution and strengthening
7. **Finalize** -- final formatting, citations, metadata

Each state MUST emit an artifact in the working directory with deterministic naming.

---

## 7. Open Brain Adoption Specification

### 7.1 Strategic Requirement

Open Brain is the durable memory system for:

- Entire agent fleet
- IDE-connected agents/harnesses (Cursor, Windsurf, etc.)

Galadriel MUST be designed assuming Open Brain availability for shared recall and write-back.

### 7.2 Tool Contract Requirement

The specification currently references two tool surfaces in existing docs:

- **4-tool surface** (`search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`)
- **6-tool surface** (adds `search_by_date`, `get_search_protocol`)

#### Trade-Off Analysis

- **4-tool surface (minimal contract)**
  - Pros: simpler implementation, lower compatibility risk, easier test matrix
  - Cons: weaker temporal retrieval and weaker discoverability of domain/search behavior
- **6-tool surface (extended contract)**
  - Pros: better temporal workflows (`search_by_date`) and better protocol/domain introspection (`get_search_protocol`)
  - Cons: larger test surface and tighter coupling to extended server behavior

#### Recommended Decision

Adopt a **versioned 6-tool contract** with a compatibility profile:

- **MUST support core 4 tools**
- **SHOULD support `search_by_date`**
- **SHOULD support `get_search_protocol`**
- If an environment is core-only, clients MUST degrade gracefully and continue operating on the core 4

### 7.3 Memory Write Policy

Galadriel MUST persist high-value outputs to Open Brain with provenance metadata:

- `agent_id` (e.g., `agent0-2`)
- `agent_alias` (`Galadriel`)
- `promotion_type` (`manual`, `auto-sync`, or `event-driven`)
- `source_context` (task/project scope)
- `source` (client/orchestrator path)

### 7.4 Memory Read Policy

Galadriel SHOULD query memory in this order:

1. Current context window
2. Local Agent Zero memory
3. Open Brain collective store

For cross-agent or institutional questions, Open Brain query is mandatory.

---

## 8. Open Brain Compiled Wiki Layer

### 8.1 Purpose

Galadriel MUST maintain a Karpathy-style compiled wiki layer on top of Open Brain. Open Brain remains the durable structured memory system; the wiki layer is a curated, human-readable synthesis surface generated from that memory and supporting sources.

This follows the hybrid direction described by Nate's Open Brain writing: database-backed memory for durable storage, plus compiled wiki artifacts for reusable synthesis and human navigation.

### 8.2 Architecture

The wiki layer SHOULD be treated as a read-optimized synthesis cache, not the source of truth.

| Layer | Role | Source of truth? |
|---|---|---|
| Open Brain | Durable semantic memory, provenance, retrieval | Yes |
| Source artifacts | Research notes, citations, transcripts, Matrix conclusions, files | Yes |
| Compiled wiki | Curated topical synthesis, navigation, summaries, contradiction notes | No |

### 8.3 Write-Time vs Query-Time Policy

Galadriel SHOULD use a hybrid strategy:

- **Write-time capture:** save granular facts, notes, decisions, source references, and provenance to Open Brain.
- **Scheduled compilation:** periodically synthesize related Open Brain memories into wiki pages.
- **Query-time refresh:** when a human or agent asks a deep question, Galadriel MAY refresh the relevant wiki page before answering.

### 8.4 Wiki Artifact Requirements

Each compiled wiki page MUST include:

- Topic title and last compiled timestamp
- Scope statement
- Executive summary
- Key facts and claims
- Source list with URLs or local artifact references
- Known contradictions or disputed claims
- Open questions / research gaps
- Related Open Brain topics
- Provenance notes identifying source agents, humans, and model/tool path where available

### 8.5 Storage Location

Compiled wiki artifacts SHOULD live in:

```text
/a0/usr/workdir/galadriel-workspace/wiki/
```

If mirrored into the repository, use:

```text
multi-instance-deploy/docs/galadriel/wiki/
```

### 8.6 Compilation Triggers

Galadriel SHOULD compile or refresh wiki pages when:

- A long-duration research task completes
- Multiple Open Brain memories converge on the same topic
- A Matrix room reaches an architectural or operational decision
- A human asks "what do we know about X?"
- A stale wiki page is used for a high-impact answer

### 8.7 Librarian Behavior

When acting as fleet librarian, Galadriel SHOULD:

1. Search Open Brain first for durable memory.
2. Check the compiled wiki for synthesized context.
3. Refresh the wiki if stale or contradicted by newer memories.
4. Answer with citations and provenance.
5. Save new conclusions back to Open Brain and update wiki pages when appropriate.

---

## 9. Frontier Model Execution Policy

Because this design is intended to be implemented by a frontier model:

- **Primary execution model MUST be frontier-tier** for architecture, synthesis, and high-impact reasoning tasks.
- **Utility/fast models MAY be used** for bounded subtasks (classification, extraction, formatting), but not for final architectural decisions.
- Model routing policy SHOULD be explicit and versioned in deployment config.
- Final deliverables MUST include reasoning traceability (decision rationale + citations), regardless of model used.

---

## 10. Task-Scoped Model Routing

### 10.1 Capability Requirement

Galadriel SHOULD be able to call task-specific models independently of the current Agent Zero main, utility, or embedding model settings.

Examples:

- Historical and current-events research MAY use Perplexity `sonar-pro` for citation-rich web research.
- Deep scientific research MAY use Perplexity, Gemini Pro, Claude Opus-class, or another frontier/research model selected by policy.
- Drafting MAY use a prose-strong model.
- Critique MAY use a different reviewer model from the main Galadriel chat model.

### 10.2 Agent Zero Model Boundary

Agent Zero model presets select the main and utility models for a chat. They are useful for coarse chat-level routing, but they are not sufficient by themselves for fine-grained per-task routing inside one Galadriel workflow.

Therefore, per-task model routing MUST be implemented through one of these mechanisms:

1. **Model preset switch** -- coarse manual or operator-approved switch for the whole chat.
2. **External MCP tool** -- preferred for model-specific capabilities such as Perplexity search.
3. **Custom Agent Zero skill/tool** -- wrapper that calls a provider API directly using scoped environment secrets.
4. **A2A delegation** -- delegate to another Agent Zero instance configured with a different model/profile.

### 10.3 API Key Policy

Task-scoped model access MAY use separate provider API keys, but those keys MUST be configured as secrets or environment variables and never embedded in prompts, docs, or generated artifacts.

Recommended environment names:

- `PERPLEXITY_API_KEY` for direct Perplexity API access
- `OPENROUTER_API_KEY` for OpenRouter-routed model access
- Provider-specific keys only when direct provider access is required

### 10.4 Research Model Policy

For historical, current-events, and deep scientific research:

- Galadriel SHOULD prefer a citation-capable research model/tool.
- Perplexity `sonar-pro` SHOULD be treated as the default research-mode candidate when available.
- Research calls MUST request citations when the tool/API supports them.
- Galadriel MUST record which model/tool produced research notes when saving artifacts or writing to Open Brain.

---

## 11. Borrowed Agent Roles from Cursor-Writing-Assistant

Galadriel borrows the conceptual roles from `Cursor-Writing-Assistant-repo/agents`, but Agent Zero should not assume Cursor `.mdc` files are directly executable subagents.

### 11.1 Role Mapping

| Cursor role | Source file | Preferred Agent Zero representation | Model policy |
|---|---|---|---|
| Research Agent | `agents/research-agent.mdc` | Skill or delegated A2A research profile | Prefer Perplexity `sonar-pro` when available |
| Writing Agent | `agents/writing-agent.mdc` | Skill or Galadriel internal workflow phase | Prose-strong frontier model |
| Critique Agent | `agents/critique-agent.mdc` | Skill, profile, or A2A reviewer | Independent critique/reviewer model |
| Technical Validator | `agents/technical-agent.mdc` | Skill, profile, or A2A validator | Scientific/technical validation model |

### 11.2 Exposure to Users

Galadriel SHOULD expose these roles to users as named workflow modes, not as raw implementation details.

Supported user-facing phrases:

- "Run research mode on this topic."
- "Draft this from the research notes."
- "Critique this draft."
- "Technically validate these claims."
- "Run the full research -> draft -> critique -> validation workflow."

### 11.3 Coordination Mechanism

Initial implementation SHOULD coordinate role usage through Galadriel's system prompt and skills:

1. Galadriel selects the appropriate role based on task intent.
2. Galadriel loads or follows the corresponding role instructions.
3. If a role requires a different model, Galadriel uses task-scoped model routing from Section 10.
4. If the role requires long-running isolated context, Galadriel delegates through A2A to a specialized Agent Zero instance.

Future implementation MAY expose each role as a first-class Agent Zero profile or separate sovereign Agent-Matrix agent.

---

## 12. Deployment and Configuration Requirements

Galadriel deployment on `agent0-2` MUST include:

1. Agent profile registration (`galadriel`)
2. Prompt include for stable behavior constraints
3. Open Brain MCP connectivity test
4. Matrix connectivity test
5. Optional A2A server enablement for direct inter-agent delegation
6. External API token validation (for automation/bridge use cases)
7. Optional task-scoped model tool configuration (`PERPLEXITY_API_KEY`, `OPENROUTER_API_KEY`, or provider-specific secrets)

All secrets/tokens MUST be sourced from environment or secret management, never hardcoded in prompts or docs.

---

## 13. Verification Requirements

Implementation readiness is reached only when all checks pass.

### 13.1 Capability Checks

- Domain-response quality checks across all five specialization domains
- Workflow execution checks proving phase artifact generation
- Citation and source quality checks

### 13.2 Connectivity Checks

- Matrix room interaction (human + agent)
- A2A delegated task round-trip between two Agent Zero instances
- Open Brain read/write round-trip
- API-triggered message round-trip via `/api_message`
- Task-scoped model/API call round-trip (for example Perplexity `sonar-pro`)

### 13.3 Memory Checks

- Provenance fields present on Open Brain writes
- Cross-agent recall succeeds
- Local-memory-only fallback behavior documented when Open Brain unavailable
- Compiled wiki page generated from Open Brain memories with source provenance

---

## 14. Implementation Contracts Still Required

The following contracts MUST be completed before implementation begins. They convert the design intent into buildable work packages.

### 14.0 Phase 0 Implementation Decisions

These decisions are accepted for the first implementation pass and SHOULD be copied into the implementation plan.

- **Profile path:** implement a dedicated `galadriel` Agent Zero profile, derived from a Researcher base but not left as a generic Researcher profile.
- **Research model path:** use an MCP-accessible Perplexity research tool as the preferred task-scoped research mechanism.
- **Research mode defaults:** base the research behavior on `Cursor-Writing-Assistant-repo/agents/research-agent.mdc`, extended for Galadriel's broader historical, scientific, geopolitical, archival, and fleet-memory responsibilities.
- **Open Brain contract:** target the 6-tool profile, where the optional extensions beyond the core 4 are `search_by_date` and `get_search_protocol`.
- **Wiki storage:** store compiled wiki pages at `/a0/usr/workdir/galadriel-workspace/wiki/`.
- **Long-running research state:** start with file-backed JSON job manifests before building a database-backed scheduler.

### 14.1 Profile Contract

Define the concrete Agent Zero profile artifacts for Galadriel.

Required decisions:

- Profile directory path and file layout
- System prompt file contents
- Promptinclude file names and injection order
- Default enabled skills
- Default model preset, if any
- Required project context and secrets
- Upgrade procedure when the profile changes

Acceptance criteria:

- A fresh `agent0-2` instance can load the Galadriel profile without manual prompt editing.
- Galadriel can state its mission, communication policy, memory policy, and role modes from the loaded profile.

### 14.2 Task-Scoped Model Tool Contract

Define the mechanism Galadriel uses to call models outside the active Agent Zero main, utility, or embedding settings.

Required decisions:

- Mechanism: external MCP tool, custom Agent Zero skill/tool, A2A delegate, or model preset switch
- Tool names and input/output schemas
- Supported providers and model IDs
- Required environment variables and secret names
- Citation return format
- Error and fallback behavior
- Cost/rate-limit policy
- Audit log format for model/tool provenance

Acceptance criteria:

- Galadriel can run a Perplexity `sonar-pro` research call while its main Agent Zero model remains unchanged.
- Saved research artifacts record model/tool name, timestamp, query, citations, and provenance.

### 14.3 Long-Running Research Job Contract

Define how Galadriel performs durable research tasks that may span multiple sessions.

Required decisions:

- Job states: `queued`, `scoping`, `researching`, `synthesizing`, `validating`, `wiki-compiling`, `completed`, `paused`, `failed`, `cancelled`
- Job metadata schema
- Checkpoint interval and storage path
- Progress reporting cadence
- Human approval gates
- Resume and cancellation behavior
- Failure recovery and partial-result handling

Acceptance criteria:

- A research job can be paused, resumed, and completed without losing source inventory or intermediate notes.
- A human or agent can query job status through the chosen interface.

### 14.4 Sub-Agent Delegation Contract

Define how Galadriel delegates work to spawned or remote specialist agents.

Required decisions:

- Delegation channel: in-instance sub-agent, A2A, Matrix room, or API bridge
- Task packet schema
- Required output schema
- Timeout and retry policy
- Budget/model constraints
- Merge strategy for multiple sub-agent outputs
- Provenance format for delegated findings

Acceptance criteria:

- Galadriel can delegate a research, critique, or validation task and merge the result into a final artifact with source attribution.
- Failed or partial sub-agent work is represented explicitly instead of silently dropped.

### 14.5 Compiled Wiki Compiler Contract

Define the compiler that turns Open Brain memories and source artifacts into wiki pages.

Required decisions:

- Wiki page naming and topic ID scheme
- Page template and required frontmatter
- Source selection and clustering algorithm
- Staleness threshold
- Conflict and contradiction handling
- Link-back format to Open Brain IDs and source artifacts
- Refresh triggers and schedule
- Human review policy for high-impact wiki pages

Acceptance criteria:

- Given a topic query, Galadriel can produce or refresh a wiki page with citations, provenance, contradictions, gaps, and related topics.
- Wiki pages clearly identify their source memories and last compilation time.

### 14.6 Memory Governance Contract

Define what Galadriel may store in Open Brain and the compiled wiki.

Required decisions:

- Promotion criteria for fleet-wide memory
- Redaction rules for secrets, credentials, private keys, access tokens, and sensitive personal data
- Retention and deletion policy
- Update/correction policy for stale or wrong memories
- Human approval threshold for sensitive or high-impact memory writes
- Ownership and provenance fields

Acceptance criteria:

- Galadriel refuses or redacts obvious secrets before saving to Open Brain.
- A stale or incorrect memory can be corrected with provenance preserved.

### 14.7 Channel Payload Contract

Define when to use Matrix, A2A, MCP, or API for specific payload types.

Required decisions:

- Size threshold for "large JSON"
- File transfer limits and preferred path
- Pointer/reference format for large artifacts
- Sensitive data channel restrictions
- Matrix room archival rules

Acceptance criteria:

- Galadriel chooses Matrix for multi-party discussion and A2A or artifact pointers for large structured payloads.
- Large data is not pasted into Matrix rooms unless explicitly requested.

### 14.8 Observability Contract

Define logging and metrics for Galadriel's work.

Required decisions:

- Events to log: model calls, Open Brain writes, wiki compiles, sub-agent delegations, Matrix decisions, A2A transfers
- Log destination and retention
- Cost accounting fields
- Failure and retry visibility
- Human-readable audit summary format

Acceptance criteria:

- An operator can reconstruct which models, tools, agents, sources, and memories contributed to a final answer.

### 14.9 Acceptance Test Contract

Define the canonical tests used to accept a Galadriel implementation.

Required decisions:

- Test prompt corpus
- Expected artifacts
- Scoring rubric for source quality, citation completeness, wiki quality, and memory hygiene
- Required pass/fail thresholds
- Regression test cadence

Acceptance criteria:

- A new implementation can be tested without subjective hand-waving.
- Failures produce actionable remediation items.

---

## 15. Identified Specification Holes

The following holes block clean implementation if left unresolved.

### Hole 1 -- Open Brain Tool Surface Drift

The docs currently imply inconsistent Open Brain tool counts (4 vs 6).  
**Risk:** implementer targets wrong API contract.

### Hole 2 -- Promotion Policy Ambiguity

No strict rules define what must be promoted from local memory to collective memory.  
**Risk:** memory noise or missing institutional knowledge.

### Hole 3 -- Channel Arbitration Rules

No deterministic rule-set for when Galadriel should choose Matrix vs A2A vs API orchestration.  
**Risk:** inconsistent collaboration behavior.

### Hole 4 -- Failure Semantics

No defined degraded-mode behavior for Open Brain outage, A2A outage, or Matrix outage.  
**Risk:** fragile runtime behavior and operator confusion.

### Hole 5 -- Security Boundary Detail

Token rotation cadence, TLS expectations for Open Brain MCP access, and least-privilege policy are not fully specified.  
**Risk:** avoidable security exposure.

### Hole 6 -- Test Corpus Definition

No canonical benchmark prompt set and scoring rubric for Galadriel quality gates.  
**Risk:** subjective acceptance criteria.

### Hole 7 -- Task-Scoped Model Tooling

No implementation yet defines the exact API wrapper, MCP server, or skill that lets Galadriel call Perplexity or other task-specific models independently of Agent Zero's active main/utility model.  
**Risk:** model-routing policy exists on paper but cannot be exercised reliably.

### Hole 8 -- Compiled Wiki Compiler

No implementation yet defines the wiki compiler, staleness rules, output schema, or conflict handling for Open Brain-derived wiki pages.  
**Risk:** Galadriel can accumulate memories but cannot reliably turn them into reusable human-readable knowledge.

### Hole 9 -- Long-Running Job Lifecycle

No implementation yet defines durable job state, checkpointing, pause/resume, cancellation, or progress reporting for long-duration research.  
**Risk:** research can sprawl across sessions and lose state.

### Hole 10 -- Sub-Agent Delegation Semantics

No implementation yet defines task packets, output schemas, timeouts, retries, or merge rules for spawned/delegated agents.  
**Risk:** Galadriel can ask other agents for help but cannot manage their work predictably.

### Hole 11 -- Memory Governance

No implementation yet defines redaction, retention, correction, deletion, or human approval rules for Open Brain and wiki writes.  
**Risk:** the fleet memory accumulates stale, unsafe, or sensitive material.

### Hole 12 -- Observability and Cost Accounting

No implementation yet defines logs, metrics, or cost attribution for model calls, tool calls, wiki compiles, and delegated work.  
**Risk:** operators cannot debug behavior or control spend.

---

## 16. Action Items to Improve This Spec

### P0 (Required Before Implementation)

1. **Lock Open Brain API contract** (authoritative tool list + schema + version pin).
2. **Define memory promotion rubric** (what gets promoted, who can promote, required metadata).
3. **Define channel arbitration matrix** (Matrix vs A2A vs API decision tree).
4. **Define degraded-mode behavior** for each channel/memory dependency.
5. **Publish security profile** (token handling, rotation, TLS posture, audit logging requirements).
6. **Choose task-scoped model mechanism** (MCP tool, custom skill/tool, preset switch, or A2A delegation).
7. **Define compiled wiki schema and compiler behavior** (page template, staleness rules, conflict handling, storage path).
8. **Complete implementation contracts in Section 14**.

### P1 (Strongly Recommended)

1. Add an explicit **acceptance test suite** with pass/fail thresholds.
2. Add **task class to model class mapping** for frontier vs utility model routing.
3. Define **cross-agent provenance reporting format** for delegation chains.
4. Add **Open Brain outage playbook** for operators.
5. Convert borrowed Cursor agent roles into Agent Zero skills or profiles.
6. Add an acceptance test for "what do we know about X?" using Open Brain + compiled wiki refresh.

### P2 (Future Hardening)

1. Add event-driven memory promotion hooks.
2. Add automated quality drift detection for Galadriel outputs.
3. Add structured telemetry dashboard for channel usage and failure rates.

---

## 17. References

- [Source A - Agent Zero docs hub](https://github.com/agent0ai/agent-zero/tree/main/docs)
- [Source B - Agent Zero A2A setup](https://raw.githubusercontent.com/agent0ai/agent-zero/main/docs/guides/a2a-setup.md)
- [Source C - Agent Zero MCP setup](https://raw.githubusercontent.com/agent0ai/agent-zero/main/docs/guides/mcp-setup.md)
- [Source D - Agent Zero connectivity](https://raw.githubusercontent.com/agent0ai/agent-zero/main/docs/developer/connectivity.md)
- [Source E - Open Brain (OB1)](https://github.com/NateBJones-Projects/OB1)
- [Source F - Agent-Matrix Open Brain design](agent-matrix-open-brain-design.md)
- [Source G - Open Brain Agent Zero guide](../../open-brain/docs/open-brain-agent-zero-guide.md)
- [Source H - Open Brain self-hosted guide](../../open-brain/docs/open-brain-self-hosted-guide.md)
- [Source I - Nate's Substack: Karpathy's Memory System](https://natesnewsletter.substack.com/p/your-ai-re-derives-everything-it)
- [Source J - Nate's Substack: The Hybrid I'd Actually Build Next](https://natesnewsletter.substack.com/i/194981463/the-hybrid-id-actually-build-next)

---

## Appendix A: Decision Log

### A.1 Canonical Specification File

- **Decision:** `multi-instance-deploy/docs/galadriel-agent-design.md` is the canonical v2.1 specification.
- **Status:** Accepted.
- **Rationale:** Single source of truth for implementation and review.

### A.2 Communication Channel Arbitration

- **Decision:** Use **Matrix-first** for multi-entity collaboration (human + multiple agents).
- **Decision:** Use **A2A-preferred** for inter-agent file transfer and large structured JSON payload handoff.
- **Status:** Accepted.
- **Rationale:** Matrix is strongest for shared collaboration context; A2A is better for targeted agent-to-agent transfer/delegation payloads.

### A.3 Open Brain Tool Contract Target

- **Decision:** Adopt a **versioned 6-tool target** with mandatory core-4 compatibility.
- **Status:** Provisional (pending final explicit lock in implementation kickoff).
- **Required profile:**
  - MUST: `search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`
  - SHOULD: `search_by_date`, `get_search_protocol`
  - MUST: graceful fallback when only core-4 is available
- **Rationale:** Preserves deployment compatibility while enabling richer temporal/protocol-aware retrieval.

### A.4 Frontier Model Policy

- **Decision:** Frontier-tier model is primary for architecture and final reasoning paths; utility models are limited to bounded subtasks.
- **Status:** Accepted.
- **Rationale:** Maximizes implementation quality for high-impact design and synthesis decisions.

### A.5 Task-Scoped Model Routing

- **Decision:** Galadriel may use task-specific models independently of the active Agent Zero main, utility, or embedding models.
- **Status:** Accepted as design goal; implementation mechanism still open.
- **Preferred implementation order:** external MCP tool, custom Agent Zero skill/tool, A2A delegation, then manual model preset switch.
- **Rationale:** Research, critique, validation, and drafting benefit from different model strengths; tying every phase to one chat model would blunt Galadriel's usefulness.

### A.6 Borrowed Cursor Agent Roles

- **Decision:** Cursor-Writing-Assistant `.mdc` agents are borrowed as role definitions, not assumed to be directly executable Agent Zero subagents.
- **Status:** Accepted.
- **Initial exposure:** user-facing workflow modes coordinated by Galadriel's system prompt and skills.
- **Future exposure:** first-class Agent Zero profiles, skills, or dedicated Agent-Matrix agents if the workflow justifies the extra infrastructure.

### A.7 Open Brain Compiled Wiki Layer

- **Decision:** Galadriel maintains a Karpathy-style compiled wiki layer generated from Open Brain memories and source artifacts.
- **Status:** Accepted for v2.1 design.
- **Source of truth:** Open Brain and source artifacts remain authoritative; compiled wiki pages are read-optimized synthesis artifacts.
- **Rationale:** The hybrid architecture combines durable structured memory with human-readable synthesis, reducing repeated query-time re-derivation while preserving provenance.

### A.8 Phase 0 Implementation Direction

- **Decision:** Capture implementation details in a separate `galadriel-implementation-plan.md` document rather than overloading this design specification.
- **Decision:** Build Galadriel as a dedicated profile derived from Researcher behavior.
- **Decision:** Use MCP-accessible Perplexity research as the first task-scoped model route.
- **Decision:** Store compiled wiki pages under `/a0/usr/workdir/galadriel-workspace/wiki/`.
- **Status:** Accepted.
- **Rationale:** The design doc remains the architectural contract; the implementation plan can evolve as concrete commands, file paths, and sequencing are discovered.

---

*Prepared as v2.1 implementation specification coverage update for Galadriel.*
