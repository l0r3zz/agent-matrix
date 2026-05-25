# Galadriel Agent Design Specification v2.2

**Version:** 2.2
**Date:** 2026-05-24
**Target Instance:** `agent0-2` (sovereign node on `g2s.cybertribe.com`)
**Status:** Specification only — no implementation in this document
**Primary Audience:** Frontier-model implementer + human operators
**Companion Document:** `galadriel-implementation-plan.md` (execution phases and concrete file paths)

---

## 1. Purpose

Define an implementation-ready specification for **Galadriel** as a specialized Agent Zero agent in Agent-Matrix, updated for:

- Fleet-wide durable memory through **Open Brain (OB1)**
- A Karpathy-style compiled wiki layer generated from Open Brain
- Current Agent Zero connectivity options beyond Matrix
- Mature Agent Zero platform features (A2A, MCP, projects, profiles, external API)

This document supersedes v2.1 and serves as the baseline for implementation planning.

---

## 2. Changes Since v2.1

1. **Open Brain tool surface updated** to reflect deployed enhancements:
   - Tool annotations (`readOnlyHint`, `destructiveHint`, etc.) now deployed on fleet OB1
   - Citation helpers (`thoughtTitle`, `thoughtUrl`, `CITATION_BASE_URL`) now deployed on fleet OB1
   - Deployed OB1 MCP server runs **Node.js + direct PostgreSQL**, not upstream Deno/Supabase
2. **OB1 architecture clarified**: deployed version is a custom self-hosted Node.js implementation
3. **Homeserver technology corrected**: fleet runs **conduwuite/continuwuity**, not Dendrite
4. **Implementation phasing updated** to reflect completed OB1 enhancements and remaining work
5. **Inspection findings incorporated** from the agent0-2 system audit performed 2026-05-23
6. **Three prior documents consolidated** into two: this design spec and a single implementation plan

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

- Performing implementation changes (see companion implementation plan)
- Rewriting core Agent Zero internals
- Replacing Matrix with A2A (Matrix remains foundational in Agent-Matrix)

---

## 4. System Context

### 4.1 Runtime Context

Galadriel runs as a sovereign Agent Zero instance in the existing Agent-Matrix topology and participates in:

- Agent-Matrix Matrix federation and room-based collaboration
- Shared Open Brain memory fabric (`open-brain-db` + `open-brain-mcp`)
- Optional A2A direct delegation with other Agent Zero instances

### 4.2 Infrastructure Notes

- **Homeservers** run **conduwuite/continuwuity** (not Dendrite)
- **OB1 MCP** is a self-hosted Node.js + Express + pgvector implementation at `172.23.90.2:3100`
- **agent0-2** runs Agent Zero v1.17 with macvlan networking at `172.23.88.2`
- **agent0-2 homeserver** is `agent0-2-continuwuity` with Caddy reverse proxy (`agent0-2-mhs`)

### 4.3 Memory Layers (Authoritative Model)

Galadriel MUST treat memory as a layered system:

1. **Context window (ephemeral)** — current conversation only
2. **Agent Zero local memory (per-agent)** — personal memory for `agent0-2`
3. **Open Brain collective memory (fleet-wide)** — durable shared memory across agents and IDE harnesses

Open Brain is the long-lived organizational memory of record. Local memory is not a substitute for fleet memory.

---

## 5. Communication Architecture

Galadriel supports multiple communication planes with different roles.

| Channel | Protocol | Primary Use | State/Context | Notes |
|---|---|---|---|---|
| Matrix rooms | Matrix CS + federation | Human-agent and agent-agent chat | Conversational, asynchronous | Core platform channel |
| A2A | FastA2A via Agent Zero `/a2a/...` | Direct Agent Zero to Agent Zero delegation | Full delegated chat context | Best for specialist delegation, file transfer, large JSON |
| External API | Agent Zero REST (`/api_message`, etc.) | Programmatic orchestration and bridges | Request/response + logs | Used by matrix-bot pattern |
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

- **Researcher** — conducts long-duration research at the request of humans or agents.
- **Archivist** — preserves important findings, decisions, sources, and synthesized artifacts.
- **Fleet community memory maintainer** — curates Open Brain as shared institutional memory.
- **Knowledgeable librarian** — helps humans and agents find, understand, and reuse what the fleet already knows.
- **Sub-agent manager** — coordinates spawned or delegated specialist agents for research, critique, validation, and synthesis.

### 6.2 Quality Priorities

Galadriel MUST prioritize:

1. Accuracy and source quality over speed
2. Multi-perspective analysis (including non-Western views where relevant)
3. Clear uncertainty handling
4. Citation discipline for factual claims
5. Structured output suitable for reuse and handoff

### 6.3 Writing Workflow (State Machine)

For substantial writing tasks, Galadriel MUST execute the following states:

1. **Scope** — requirements, audience, constraints, deliverables
2. **Research** — source gathering, credibility scoring, perspective balancing
3. **Outline** — section architecture and argument flow
4. **Draft** — first complete pass
5. **Critique** — quality review (accuracy, bias, clarity, omissions)
6. **Revise** — issue resolution and strengthening
7. **Finalize** — final formatting, citations, metadata

Each state MUST emit an artifact in the working directory with deterministic naming.

---

## 7. Open Brain Adoption Specification

### 7.1 Strategic Requirement

Open Brain is the durable memory system for:

- Entire agent fleet
- IDE-connected agents/harnesses (Cursor, Windsurf, etc.)

Galadriel MUST be designed assuming Open Brain availability for shared recall and write-back.

### 7.2 Deployed OB1 Architecture (as of 2026-05-24)

The fleet OB1 is a **custom self-hosted implementation**, not the upstream Deno/Supabase version:

| Aspect | Deployed Fleet OB1 |
|---|---|
| Runtime | Node.js 20+ |
| Web framework | Express |
| Database | Direct PostgreSQL + pgvector |
| Container | `open-brain-mcp` at `172.23.90.2:3100` |
| Auth | `MCP_ACCESS_KEY` via header or URL param |
| Transport | Custom HTTP request/response (not StreamableHTTPTransport) |

### 7.3 Tool Contract (Current Deployed Surface)

The deployed OB1 exposes **4 core tools** with enhancements:

| Tool | Type | Annotations | Citation Output |
|---|---|---|---|
| `search_thoughts` | Read | `readOnlyHint: true` | ID, URL, Title per result |
| `list_thoughts` | Read | `readOnlyHint: true` | Title, URL per result |
| `thought_stats` | Read | `readOnlyHint: true` | Citation base URL in verbose mode |
| `capture_thought` | Write | `readOnlyHint: false, destructiveHint: false` | N/A |

**Extended tools not yet implemented:**

| Tool | Purpose | Status |
|---|---|---|
| `search_by_date` | Temporal retrieval | Design-phase only |
| `get_search_protocol` | Dynamic domain/search protocol generation | Design-phase only |

#### Versioned Compatibility Contract

- **MUST support core 4 tools**
- **SHOULD support `search_by_date`** when available
- **SHOULD support `get_search_protocol`** when available
- **MUST degrade gracefully** when only core 4 is available

### 7.4 Memory Write Policy

Galadriel MUST persist high-value outputs to Open Brain with provenance metadata:

- `agent_id` (e.g., `agent0-2`)
- `agent_alias` (`Galadriel`)
- `promotion_type` (`manual`, `auto-sync`, or `event-driven`)
- `source_context` (task/project scope)
- `source` (client/orchestrator path)

### 7.5 Memory Read Policy

Galadriel SHOULD query memory in this order:

1. Current context window
2. Local Agent Zero memory
3. Open Brain collective store

For cross-agent or institutional questions, Open Brain query is mandatory.

---

## 8. Open Brain Compiled Wiki Layer

### 8.1 Purpose

Galadriel MUST maintain a Karpathy-style compiled wiki layer on top of Open Brain. Open Brain remains the durable structured memory system; the wiki layer is a curated, human-readable synthesis surface generated from that memory and supporting sources.

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
- Source list with URLs or local artifact references (using OB1 citation URLs when available)
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
- Deep scientific research MAY use Perplexity, Gemini Pro, Claude Opus-class, or another frontier/research model.
- Drafting MAY use a prose-strong model.
- Critique MAY use a different reviewer model from the main Galadriel chat model.

### 10.2 Agent Zero Model Boundary

Agent Zero model presets select the main and utility models for a chat. They are not sufficient for fine-grained per-task routing inside one Galadriel workflow.

Per-task model routing MUST be implemented through one of these mechanisms:

1. **Model preset switch** — coarse manual or operator-approved switch for the whole chat.
2. **External MCP tool** — preferred for model-specific capabilities such as Perplexity search.
3. **Custom Agent Zero skill/tool** — wrapper that calls a provider API directly using scoped environment secrets.
4. **A2A delegation** — delegate to another Agent Zero instance configured with a different model/profile.

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

Galadriel SHOULD expose these roles as named workflow modes:

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
4. If the role requires long-running isolated context, Galadriel delegates through A2A.

---

## 12. Deployment and Configuration Requirements

Galadriel deployment on `agent0-2` MUST include:

1. Agent profile registration (`galadriel`)
2. Prompt include for stable behavior constraints
3. Open Brain MCP connectivity test
4. Matrix connectivity test
5. A2A server enablement for direct inter-agent delegation
6. External API token validation (for automation/bridge use cases)
7. Optional task-scoped model tool configuration

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
- Task-scoped model/API call round-trip (e.g., Perplexity `sonar-pro`)

### 13.3 Memory Checks

- Provenance fields present on Open Brain writes
- Cross-agent recall succeeds
- Local-memory-only fallback behavior documented when Open Brain unavailable
- Compiled wiki page generated from Open Brain memories with source provenance
- Citation URLs present in search/list results (OB1 enhancement verified 2026-05-24)

---

## 14. Implementation Contracts

Detailed execution steps are in the companion `galadriel-implementation-plan.md`.

### 14.1 Profile Contract

- Profile directory path and file layout
- System prompt file contents
- Promptinclude file names and injection order
- Default enabled skills and model preset
- Required project context and secrets
- Upgrade procedure when the profile changes

### 14.2 Task-Scoped Model Tool Contract

- Mechanism: external MCP tool, custom skill/tool, A2A delegate, or model preset switch
- Tool names and input/output schemas
- Supported providers and model IDs
- Required environment variables and secret names
- Citation return format and error/fallback behavior

### 14.3 Long-Running Research Job Contract

- Job states: `queued`, `scoping`, `researching`, `synthesizing`, `validating`, `wiki-compiling`, `completed`, `paused`, `failed`, `cancelled`
- Job metadata schema, checkpoint interval, progress reporting
- Resume, cancellation, and failure recovery behavior

### 14.4 Sub-Agent Delegation Contract

- Delegation channel: in-instance sub-agent, A2A, Matrix room, or API bridge
- Task packet schema, output schema, timeout/retry policy
- Merge strategy for multiple sub-agent outputs

### 14.5 Compiled Wiki Compiler Contract

- Wiki page naming and topic ID scheme
- Page template and required frontmatter
- Source selection, staleness threshold, conflict handling
- Link-back format to Open Brain IDs and source artifacts

### 14.6 Memory Governance Contract

- Promotion criteria for fleet-wide memory
- Redaction rules for secrets and sensitive data
- Retention, deletion, and correction policy

### 14.7 Channel Payload Contract

- Size threshold for "large JSON"
- File transfer limits and preferred path
- Sensitive data channel restrictions

### 14.8 Observability Contract

- Events to log: model calls, Open Brain writes, wiki compiles, sub-agent delegations
- Log destination, retention, cost accounting

---

## 15. Identified Specification Holes

| # | Hole | Risk | Status |
|---|---|---|---|
| 1 | Open Brain tool surface drift | Implementer targets wrong API contract | **Partially resolved** — core 4 with annotations/citations deployed; extended 2 remain design-phase |
| 2 | Promotion policy ambiguity | Memory noise or missing institutional knowledge | Open |
| 3 | Channel arbitration rules | Inconsistent collaboration behavior | Open |
| 4 | Failure semantics | Fragile runtime behavior | Open |
| 5 | Security boundary detail | Avoidable security exposure | Open |
| 6 | Test corpus definition | Subjective acceptance criteria | Open |
| 7 | Task-scoped model tooling | Model-routing policy on paper only | Open — no Perplexity key/MCP found |
| 8 | Compiled wiki compiler | Cannot turn memories into reusable knowledge | Open |
| 9 | Long-running job lifecycle | Research can lose state across sessions | Open |
| 10 | Sub-agent delegation semantics | Cannot manage delegated work predictably | Open |
| 11 | Memory governance | Fleet memory accumulates stale/unsafe material | Open |
| 12 | Observability and cost accounting | Cannot debug behavior or control spend | Open |

---

## 16. Action Items

### P0 (Required Before Implementation)

1. Lock Open Brain API contract (authoritative tool list + schema + version pin).
2. Define memory promotion rubric.
3. Define channel arbitration matrix.
4. Define degraded-mode behavior for each dependency.
5. Publish security profile.
6. Choose task-scoped model mechanism.
7. Define compiled wiki schema and compiler behavior.

### P1 (Strongly Recommended)

1. Acceptance test suite with pass/fail thresholds.
2. Task class to model class mapping.
3. Cross-agent provenance reporting format.
4. Open Brain outage playbook.
5. Convert borrowed Cursor agent roles into Agent Zero skills or profiles.

### P2 (Future Hardening)

1. Event-driven memory promotion hooks.
2. Automated quality drift detection.
3. Structured telemetry dashboard.

---

## 17. References

- [Agent Zero docs hub](https://github.com/agent0ai/agent-zero/tree/main/docs)
- [Agent Zero A2A setup](https://raw.githubusercontent.com/agent0ai/agent-zero/main/docs/guides/a2a-setup.md)
- [Agent Zero MCP setup](https://raw.githubusercontent.com/agent0ai/agent-zero/main/docs/guides/mcp-setup.md)
- [Agent Zero connectivity](https://raw.githubusercontent.com/agent0ai/agent-zero/main/docs/developer/connectivity.md)
- [Open Brain (OB1)](https://github.com/NateBJones-Projects/OB1)
- [Agent-Matrix Open Brain design](agent-matrix-open-brain-design.md)
- [Open Brain Agent Zero guide](../../open-brain/docs/open-brain-agent-zero-guide.md)
- [Open Brain self-hosted guide](../../open-brain/docs/open-brain-self-hosted-guide.md)
- [Nate's Substack: Karpathy's Memory System](https://natesnewsletter.substack.com/p/your-ai-re-derives-everything-it)
- [Nate's Substack: The Hybrid I'd Actually Build Next](https://natesnewsletter.substack.com/i/194981463/the-hybrid-id-actually-build-next)

---

## Appendix A: Decision Log

### A.1 Canonical Specification File

- **Decision:** `multi-instance-deploy/docs/galadriel-agent-design.md` is the canonical design specification.
- **Status:** Accepted.

### A.2 Communication Channel Arbitration

- **Decision:** Matrix-first for multi-entity collaboration; A2A-preferred for inter-agent file transfer and large structured JSON.
- **Status:** Accepted.

### A.3 Open Brain Tool Contract Target

- **Decision:** Versioned 6-tool target with mandatory core-4 compatibility.
- **Status:** Provisional — core 4 deployed with enhancements; extended 2 remain unimplemented.
- **Required profile:**
  - MUST: `search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`
  - SHOULD: `search_by_date`, `get_search_protocol`
  - MUST: graceful fallback when only core-4 is available

### A.4 Frontier Model Policy

- **Decision:** Frontier-tier model is primary for architecture and final reasoning; utility models limited to bounded subtasks.
- **Status:** Accepted.

### A.5 Task-Scoped Model Routing

- **Decision:** Galadriel may use task-specific models independently of the active Agent Zero main/utility/embedding models.
- **Status:** Accepted as design goal; implementation mechanism still open.
- **Preferred order:** external MCP tool, custom skill/tool, A2A delegation, then manual preset switch.

### A.6 Borrowed Cursor Agent Roles

- **Decision:** Cursor `.mdc` agents are borrowed as role definitions, not directly executable Agent Zero subagents.
- **Status:** Accepted.

### A.7 Open Brain Compiled Wiki Layer

- **Decision:** Galadriel maintains a Karpathy-style compiled wiki layer generated from Open Brain and source artifacts.
- **Status:** Accepted.

### A.8 Document Consolidation (v2.2)

- **Decision:** Three prior documents consolidated into two: this design spec and a single implementation plan.
- **Supersedes:** `galadriel-agent0-2-inspection-implementation-plan.md` (retired — findings absorbed into implementation plan).
- **Status:** Accepted.

### A.9 OB1 Enhancements (v2.2)

- **Decision:** Tool annotations and citation helpers deployed to fleet OB1 on 2026-05-24.
- **Status:** Completed and verified. All fleet agents receive enhancements automatically.
- **Backup:** `/opt/agent-zero/backups/open-brain-pre-enhance-20260525T002358Z`

---

*Prepared as v2.2 design specification for Galadriel. Companion implementation plan: `galadriel-implementation-plan.md`.*
