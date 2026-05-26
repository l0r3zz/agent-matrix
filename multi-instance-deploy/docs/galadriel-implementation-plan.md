# Galadriel Implementation Plan v1.0

**Version:** 1.0
**Date:** 2026-05-24
**Related spec:** [Galadriel Agent Design Specification v2.2](galadriel-agent-design.md)
**Status:** Actionable implementation plan for frontier-model execution
**Supersedes:** `galadriel-implementation-plan.md` v0.1 and `galadriel-agent0-2-inspection-implementation-plan.md`

---

## 1. Purpose

This document turns the Galadriel design specification v2.2 into a concrete implementation sequence for retooling `agent0-2` as the specialized Galadriel agent.

It consolidates:

- **Inspection findings** from the agent0-2 system audit (2026-05-23)
- **Implementation phasing** with completed and remaining work
- **Exact file paths, backup/rollback steps, and verification checklists**

The design specification (`galadriel-agent-design.md`) remains the architectural source of truth. This plan records concrete implementation decisions, sequencing, and acceptance checks.

---

## 2. Current State of agent0-2 (Inspection Findings)

These findings were gathered read-only on 2026-05-23. No files were modified, no services restarted, no secrets changed, no OpenBrain writes performed.

### 2.1 Profile Layout

A partial Galadriel scaffold already exists:

```text
/opt/agent-zero/agent0-2/usr/agents/galadriel/
  agent.yaml
  prompts/
    agent.system.main.specifics.md
```

**agent.yaml:**
```yaml
title: Galadriel
description: Sovereign research and analysis agent specializing in sciences, multiview history,
  philosophy, current events, and global politics.
context: Use this agent for comprehensive research, analysis, drafting, and editing tasks
  requiring deep domain knowledge, multi-perspective viewpoints, and a direct, snappy
  communication style.
```

**Active profile:** `researcher` (NOT `galadriel`)

### 2.2 Prompt Includes

```text
/opt/agent-zero/agent0-2/usr/workdir/galadriel.promptinclude.md
/opt/agent-zero/agent0-2/usr/workdir/knowledge-search.promptinclude.md
```

`galadriel.promptinclude.md` contains concise behavior rules: accuracy over speed, mandatory multiview history perspective, APA/MLA citation defaults, phase-based writing workflow, no corporate speak, dry humor/snark allowed, Taleb/Nietzsche lenses when relevant.

`knowledge-search.promptinclude.md` is OpenBrain-oriented with core OpenBrain usage patterns.

### 2.3 Agent Zero Settings

```text
agent_profile: researcher
mcp_server_enabled: false
a2a_server_enabled: true
mcp_client_init_timeout: 10
mcp_client_tool_timeout: 120
agent_knowledge_subdir: custom
chat_inherit_project: present
```

### 2.4 MCP Configuration

| MCP Server | Mechanism | Endpoint | Status |
|---|---|---|---|
| `open-brain` | `npx supergateway --streamableHttp` | `http://172.23.90.2:3100/mcp?...` | Configured; read-only verified |
| `matrix` | streamable HTTP | `http://localhost:3000/mcp` | Configured; process running |

### 2.5 Running Processes Inside agent0-2

```text
matrix-bot-rust
matrix-mcp-server-r2
```

### 2.6 Container Stack

```text
agent0-2          | agent0ai/agent-zero:v1.17 | Up | port 50002->80, 50023->22
agent0-2-mhs      | caddy:2-alpine            | Up
agent0-2-continuwuity | ghcr.io/continuwuity  | Up
```

### 2.7 OpenBrain State

- Service alive and readable
- 139 thoughts (date range 2026-04-01 to 2026-05-17)
- Core 4 tools available (now with annotations and citation helpers as of 2026-05-24)
- Extended tools (`search_by_date`, `get_search_protocol`) not implemented

### 2.8 Perplexity / Research Model

- No `PERPLEXITY_API_KEY` found
- No Perplexity MCP server or wrapper found
- No direct Perplexity tooling in agent0-2

---

## 3. Implementation Phases

### Phase Overview

```text
1. GALADRIEL PHASE 1 — Profile Scaffold (next)
   +-- Backup agent0-2 usr/
   +-- Update profile scaffold
   +-- Activate galadriel profile
   +-- Verify (domain sanity, Matrix, MCP, A2A)

2. OB1 LOW-RISK ENHANCEMENTS — COMPLETED 2026-05-24
   +-- Tool annotations (readOnlyHint, etc.) — DONE
   +-- Citation helpers (thoughtTitle, thoughtUrl) — DONE
   +-- CITATION_BASE_URL env var — DONE

3. GALADRIEL PHASE 2 — Research Mode (blockers must be resolved first)
   +-- Perplexity secret & routing decision
   +-- Implement research tool/skill
   +-- Test citation-rich research -> OpenBrain -> wiki flow

4. OB1 MEDIUM-RISK UPGRADES (if needed, after Phase 2 stable)
   +-- JSON-RPC error compliance
   +-- Claude Desktop Accept-header fix
   +-- ChatGPT compat layer (only if requested)

5. GALADRIEL PHASE 3 — Compiled Wiki + Long-Running Jobs
   +-- Wiki compiler implementation
   +-- Job manifest schema and lifecycle
   +-- Sub-agent delegation contract

6. GALADRIEL PHASE 4 — Delegated Specialist Roles
   +-- Research, Writing, Critique, Technical Validation skills/profiles
   +-- A2A delegation for isolated long-running context
   +-- Merge rules for delegated outputs
```

---

## 4. Phase 1 — Profile Scaffold

**Goal:** Make `agent0-2` load and operate as Galadriel with v2.2 behavior.

### 4.1 Pre-Change Backup

Run on g2s before any edits:

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR=/opt/agent-zero/backups/agent0-2-galadriel-${TS}
mkdir -p "$BACKUP_DIR"

# Core Agent Zero user state
tar -czf "$BACKUP_DIR/agent0-2-usr-config-profile-workdir.tar.gz" \
  -C /opt/agent-zero/agent0-2 \
  usr/settings.json \
  usr/.env \
  usr/secrets.env \
  usr/agents \
  usr/workdir/galadriel.promptinclude.md \
  usr/workdir/knowledge-search.promptinclude.md \
  usr/workdir/galadriel-workspace \
  2>/dev/null || true

# Matrix bridge configs (reference only)
tar -czf "$BACKUP_DIR/agent0-2-matrix-bridge-configs.tar.gz" \
  -C /opt/agent-zero/agent0-2 \
  usr/workdir/matrix-bot/.env \
  usr/workdir/matrix-bot/room_contexts.json \
  usr/workdir/matrix-mcp-server/.env \
  2>/dev/null || true

sha256sum "$BACKUP_DIR"/*.tar.gz > "$BACKUP_DIR/SHA256SUMS"
ls -lah "$BACKUP_DIR"
```

### 4.2 Profile Scaffold Updates

Update existing files — do NOT create new random locations:

#### 4.2.1 `agent.yaml`

**Path:** `/opt/agent-zero/agent0-2/usr/agents/galadriel/agent.yaml`

Update to align with v2.2 design spec:

```yaml
title: Galadriel
description: >-
  Sovereign research, archival, and synthesis agent specializing in sciences, multiview
  history, philosophy, current events, and global politics. Maintains fleet community
  memory through Open Brain, compiles wiki synthesis layers, and coordinates delegated
  specialist workflows.
context: >-
  Use this agent for comprehensive research, analysis, drafting, editing, and fleet
  memory maintenance tasks. Supports multi-phase writing workflows, citation-rich
  research, Open Brain read/write, compiled wiki synthesis, and A2A delegation to
  specialist agents.
```

#### 4.2.2 `agent.system.main.specifics.md`

**Path:** `/opt/agent-zero/agent0-2/usr/agents/galadriel/prompts/agent.system.main.specifics.md`

Add missing v2.2 requirements to the existing prompt:

- Explicit layered memory model (context window -> local memory -> Open Brain)
- OpenBrain read/write policy with graceful core-4 fallback
- Compiled wiki behavior and storage path
- Matrix/A2A/API/MCP communication policy
- Deterministic writing workflow artifact naming
- Provenance policy for research notes and OpenBrain writes
- Current-events live-search requirement
- Conduwuite wording (not Continuwuity)
- Citation URL format using OB1 citation helpers

#### 4.2.3 `galadriel.promptinclude.md`

**Path:** `/opt/agent-zero/agent0-2/usr/workdir/galadriel.promptinclude.md`

Update with stable behavioral constraints from v2.2:

- Accuracy over speed
- Mandatory multiview history perspective
- APA/MLA citation defaults
- Phase-based writing workflow
- No corporate speak; dry humor/snark allowed
- Taleb/Nietzsche lenses when relevant
- OpenBrain-first for institutional questions
- Citation URLs from OB1 citation helpers

#### 4.2.4 `knowledge-search.promptinclude.md`

**Path:** `/opt/agent-zero/agent0-2/usr/workdir/knowledge-search.promptinclude.md`

Refresh with versioned OpenBrain contract:

- Core 4 tools: `search_thoughts`, `list_thoughts`, `thought_stats`, `capture_thought`
- Extended tools (graceful fallback): `search_by_date`, `get_search_protocol`
- Citation output format: ID, URL, Title per result
- Citation base URL: `https://openbrain.local/thoughts`
- Provenance metadata requirements for writes

### 4.3 Workspace Scaffold

Create/verify directories:

```text
/opt/agent-zero/agent0-2/usr/workdir/galadriel-workspace/
  research/
  artifacts/
  wiki/
  templates/
  jobs/
  logs/
```

Deterministic artifact naming:

```text
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-00-scope.md
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-10-research.md
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-20-outline.md
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-30-draft.md
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-40-critique.md
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-50-revise.md
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-60-final.md
```

Wiki page naming:

```text
galadriel-workspace/wiki/{topic-slug}.md
```

### 4.4 Activate Profile

**Path:** `/opt/agent-zero/agent0-2/usr/settings.json`

Change:

```json
"agent_profile": "galadriel"
```

Determine whether Agent Zero v1.17 hot-reloads this setting or requires container restart / UI reload.

### 4.5 Verification Checklist

```text
[ ] Active profile shows Galadriel
[ ] Galadriel identifies itself correctly (mission, communication policy, memory policy)
[ ] Domain sanity checks:
    [ ] Science / computer science
    [ ] Multiview history
    [ ] Philosophy / metaphysics
    [ ] Current events
    [ ] Geopolitics
[ ] OpenBrain search works (search_thoughts returns results with citations)
[ ] OpenBrain capture works (capture_thought with provenance)
[ ] Matrix bot still responds
[ ] Matrix MCP tools still load
[ ] A2A endpoint remains enabled
[ ] No secrets appear in generated artifacts
```

---

## 5. Phase 2 — OB1 Low-Risk Enhancements

### Status: COMPLETED (2026-05-24)

These enhancements were deployed and verified:

| Enhancement | Status | Evidence |
|---|---|---|
| Tool annotations (`readOnlyHint`, etc.) | DONE | 4 annotation blocks in `mcp-server.ts` |
| Citation helpers (`thoughtTitle`, `thoughtUrl`) | DONE | `search_thoughts` returns ID/URL/Title per result |
| `CITATION_BASE_URL` env var | DONE | `thought_stats` shows `Citation base URL: https://openbrain.local/thoughts` |

**Build:** 0 errors, 0 vulnerabilities
**Container:** `open-brain-mcp` restarted and healthy
**Backup:** `/opt/agent-zero/backups/open-brain-pre-enhance-20260525T002358Z`

**Fleet impact:** All agents receive enhancements automatically (shared infrastructure). Zero per-agent changes required.

### Verification Results

| Test | Result |
|---|---|
| Build | PASS |
| Container startup | PASS |
| `thought_stats` verbose | PASS — shows citation base URL |
| `search_thoughts` citations | PASS — ID/URL/Title present |
| `list_thoughts` citations | PASS — Title/URL present |
| `capture_thought` | PASS — metadata extraction works |
| Tool annotations | VERIFIED — 4 annotation blocks in source |

---

## 6. Phase 3 — Research Mode + Perplexity Routing

**Goal:** Add task-scoped research capability using Perplexity `sonar-pro` or approved equivalent.

### 6.0 Blockers (Must Resolve Before Implementation)

| Blocker | Question | Decision Needed |
|---|---|---|
| Perplexity API key | Is there an approved key? | Where to store: `.env`, `secrets.env`, or other? |
| Routing mechanism | Direct Perplexity API, OpenRouter, or MCP? | Preferred: MCP tool or scoped skill wrapper |
| Secret management | How to inject key into agent0-2? | Environment variable name: `PERPLEXITY_API_KEY` |
| No-leak policy | How to prevent key leakage? | Define artifact/logging sanitization rules |

### 6.1 Choose Implementation Mechanism

Preferred order:

1. **Perplexity MCP server/tool** — clean separation of tool capability from prompt/persona
2. **Agent Zero skill/tool wrapper** — local skill that calls Perplexity REST API with scoped env secret
3. **OpenRouter route** — use existing `API_KEY_OPENROUTER` if Perplexity models are available
4. **A2A delegation** — delegate to a specialist agent with Perplexity configured

### 6.2 Research Mode Contract

User-facing mode phrases:

```text
Run research mode on this topic.
Draft this from the research notes.
Critique this draft.
Technically validate these claims.
Run the full research -> draft -> critique -> validation workflow.
```

Research output artifact:

```text
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-10-research.md
```

Research notes MUST include:

- Research question
- Search/tool/model used
- Timestamp
- Source list with URLs
- Key claims
- Confidence/uncertainty
- Perspective coverage
- Gaps and contradictions
- Suggested next searches

### 6.3 Model Routing Policy

**Path:** `/opt/agent-zero/agent0-2/usr/workdir/galadriel-workspace/model-routing-policy.md`

Contents:

- Default main model behavior
- Research mode model/tool preference
- Drafting model preference
- Critique model preference
- Technical validation model preference
- Fallback behavior when Perplexity unavailable

### 6.4 Verification

```text
[ ] Perplexity call returns citations
[ ] Source URLs preserved in artifact
[ ] No API key leakage in logs/artifacts
[ ] Timeout handling works
[ ] Fallback to normal web search if Perplexity unavailable
[ ] Research artifact saved with provenance
[ ] Distilled findings saved to OpenBrain (after write policy approval)
[ ] Wiki page generated/refreshed when appropriate
```

---

## 7. Phase 4 — OB1 Medium-Risk Upgrades

**Goal:** Improve OB1 MCP protocol compliance for broader client compatibility.

**Trigger:** Only implement if needed (e.g., Claude Desktop connectivity required, or ChatGPT compat requested).

| Enhancement | Benefit | Risk | Effort |
|---|---|---|---|
| JSON-RPC error compliance (`-32001` for auth) | Strict MCP clients stay connected | Low — changes error response shape | 30 min |
| Claude Desktop Accept-header fix | Fixes known connection bug | Low-to-moderate — touches request parsing | 30 min |
| ChatGPT compat layer (`search`, `fetch` aliases) | ChatGPT/Claude Code can use OB1 | Low — pure aliases | 20 min |

---

## 8. Phase 5 — Compiled Wiki + Long-Running Jobs

**Goal:** Build the first useful Open Brain compiled wiki workflow and durable research job lifecycle.

### 8.1 Compiled Wiki

- Define wiki page frontmatter and topic slug rules
- Implement manual compile flow: "compile wiki page for X"
- Pull source material from Open Brain and local research artifacts
- Record contradictions, open questions, and source provenance

### 8.2 Long-Running Research Jobs

- Define job manifest schema
- Store jobs under `/a0/usr/workdir/galadriel-workspace/jobs/`
- Implement states: `queued`, `scoping`, `researching`, `synthesizing`, `validating`, `wiki-compiling`, `completed`, `paused`, `failed`, `cancelled`
- Add checkpointing after each phase
- Add human-readable status summaries

### 8.3 Acceptance Checks

```text
[ ] Wiki page compiles from OpenBrain memories
[ ] Wiki page includes: timestamp, summary, claims, sources, contradictions, gaps
[ ] Research job can be paused and resumed
[ ] Partial findings survive restart/session loss
[ ] Completed jobs produce research notes, OpenBrain captures, and optional wiki pages
```

---

## 9. Phase 6 — Delegated Specialist Roles

**Goal:** Expose borrowed Cursor-Writing-Assistant roles as Galadriel-managed workflow modes.

### 9.1 Role Conversion

Convert role definitions into skills or prompt modules:

| Role | Source | Agent Zero Representation |
|---|---|---|
| Research | `research-agent.mdc` | Skill with Perplexity routing |
| Writing | `writing-agent.mdc` | Skill or internal workflow phase |
| Critique | `critique-agent.mdc` | Skill, profile, or A2A reviewer |
| Technical Validation | `technical-agent.mdc` | Skill, profile, or A2A validator |

### 9.2 Acceptance Checks

```text
[ ] User can ask Galadriel to run research, draft, critique, or validation mode
[ ] Galadriel explains which role/mode was used
[ ] Delegated work includes provenance and is not silently merged without attribution
```

---

## 10. Files / Paths Changed by Phase

### Phase 1 (agent0-2 profile scaffold)

```text
/opt/agent-zero/agent0-2/usr/agents/galadriel/agent.yaml
/opt/agent-zero/agent0-2/usr/agents/galadriel/prompts/agent.system.main.specifics.md
/opt/agent-zero/agent0-2/usr/workdir/galadriel.promptinclude.md
/opt/agent-zero/agent0-2/usr/workdir/knowledge-search.promptinclude.md
/opt/agent-zero/agent0-2/usr/settings.json
/opt/agent-zero/agent0-2/usr/workdir/galadriel-workspace/  (create dirs)
```

### Phase 2 (OB1 enhancements — COMPLETED)

```text
/opt/agent-zero/open-brain/server/src/mcp-server.ts  (DONE)
/opt/agent-zero/open-brain/server/src/http-server.ts  (DONE)
/home/l0r3zz/agent-matrix-repo/open-brain/server/src/mcp-server.ts  (DONE)
/home/l0r3zz/agent-matrix-repo/open-brain/server/src/http-server.ts  (DONE)
```

### Phase 3 (research mode — depends on blocker resolution)

```text
/opt/agent-zero/agent0-2/usr/.env  (add PERPLEXITY_API_KEY)
/opt/agent-zero/agent0-2/usr/settings.json  (MCP config if using Perplexity MCP)
/opt/agent-zero/agent0-2/usr/skills/perplexity-research/SKILL.md  (if using skill wrapper)
/opt/agent-zero/agent0-2/usr/workdir/galadriel-workspace/model-routing-policy.md
/opt/agent-zero/agent0-2/usr/workdir/galadriel-workspace/templates/research-mode.md
```

---

## 11. Files / Paths NOT to Touch Without Approval

```text
/opt/agent-zero/agent0-2/docker-compose.yml
/opt/agent-zero/agent0-2/mhs/
/opt/agent-zero/agent0-2/usr/workdir/matrix-bot/.env
/opt/agent-zero/agent0-2/usr/workdir/matrix-mcp-server/.env
/opt/agent-zero/agent0-2/usr/memory/
/opt/agent-zero/agent0-2/usr/chats/
/opt/agent-zero/agent0-2/usr/email/state.json
/opt/agent-zero/agent0-2/usr/scheduler/tasks.json
```

Do NOT restart without approval:

```text
agent0-2
agent0-2-mhs
agent0-2-continuwuity
matrix-bot-rust
matrix-mcp-server-r2
```

---

## 12. Rollback Procedures

### Phase 1 Rollback (profile change)

```bash
BACKUP_DIR=/opt/agent-zero/backups/agent0-2-galadriel-YYYYMMDDTHHMMSSZ
tar -xzf "$BACKUP_DIR/agent0-2-usr-config-profile-workdir.tar.gz" -C /opt/agent-zero/agent0-2
# If hot reload is sufficient: refresh Agent Zero UI/session
# If restart required (and approved): docker restart agent0-2
```

### Phase 2 Rollback (OB1 enhancements)

```bash
BACKUP_DIR=/opt/agent-zero/backups/open-brain-pre-enhance-20260525T002358Z
cp "$BACKUP_DIR/mcp-server.ts" /opt/agent-zero/open-brain/server/src/
cp "$BACKUP_DIR/http-server.ts" /opt/agent-zero/open-brain/server/src/
cd /opt/agent-zero/open-brain && docker compose build open-brain-mcp && docker compose up -d open-brain-mcp
```

### Rollback Validation

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep agent0-2
docker exec agent0-2 sh -lc 'ps aux | grep -Ei "matrix-bot-rust|matrix-mcp-server-r2" | grep -v grep || true'
docker exec agent0-2 sh -lc 'python3 -c "import json; d=json.load(open(\"/a0/usr/settings.json\")); print(d.get(\"agent_profile\")); print(\"a2a\", d.get(\"a2a_server_enabled\"), \"mcp_server\", d.get(\"mcp_server_enabled\"))"'
```

---

## 13. Open Questions / Blockers

| # | Question | Impact | Status |
|---|---|---|---|
| 1 | Does Agent Zero v1.17 hot-reload `agent_profile` changes? | Determines whether restart needed | Unknown |
| 2 | Should Galadriel auto-write to OpenBrain or ask before every write? | Memory governance | Decision needed |
| 3 | Is there an approved Perplexity API key? | Blocks Phase 3 | Unknown |
| 4 | Use direct Perplexity MCP, skill wrapper, or OpenRouter routing? | Blocks Phase 3 | Decision needed |
| 5 | Should wiki artifacts mirror into the git repo? | Storage policy | Decision needed |
| 6 | Matrix display name change to "Galadriel"? | Past evidence says unreliable | Defer |
| 7 | Should Galadriel become a reusable fleet template? | Template propagation | After validation |

---

## 14. Go / No-Go Recommendation

### Phase 1: CONDITIONAL GO

Proceed after:

- Human approves this plan
- Backup taken and checksummed
- Restart/hot-reload behavior confirmed

**Rationale:** Existing Galadriel scaffold can be aligned with v2.2 using low-risk profile/prompt/workdir changes. Matrix, MCP, OpenBrain, and A2A are already present.

### Phase 2: COMPLETED

OB1 tool annotations and citation helpers deployed 2026-05-24. All fleet agents receive enhancements automatically.

### Phase 3: NO-GO until blockers resolved

Do not implement Research Mode until:

- Perplexity/OpenRouter routing decision made
- API key/secret path approved
- MCP vs skill wrapper decision made
- No-leak logging/artifact policy defined

**Rationale:** No Perplexity key, MCP, or wrapper exists. Implementing without clarity would be speculative plumbing.

### Phases 4-6: DEFERRED

Sequence after Phase 3 is stable.

---

## 15. Frontier-Model Assignment

### 15.1 P0 Action Item Scoping

The design spec (Section 16) lists P0 action items. These are now **phase-gated**, not blanket prerequisites:

- **Phase 1 has NO unresolved P0 blockers.** The Open Brain API contract is locked for core 4 tools, and the communication policy in design spec Section 5.1 is sufficient.
- **Phase 3 is blocked** by: task-scoped model mechanism choice + Perplexity API key availability.
- **Phase 5 is blocked** by: compiled wiki schema definition.

Do not delay Phase 1 waiting for Phase 3+ prerequisites.

### 15.2 Frontier-Model Assignment

Give the implementer this instruction:

```text
You are retooling agent0-2 as Galadriel.

Read these two documents:
- galadriel-agent-design.md (v2.2 design specification)
- galadriel-implementation-plan.md (this plan, v1.0)

Phase 1 has no unresolved P0 blockers. Execute Phase 1 only:
1. Take backup per Section 4.1.
2. Update profile files per Section 4.2.
3. Create workspace directories per Section 4.3.
4. Activate profile per Section 4.4.
5. Run verification checklist per Section 4.5.

Constraints:
- Do NOT touch files listed in Section 11.
- Do NOT restart services without explicit approval.
- Do NOT implement Phase 3+ until blockers in Section 13 are resolved.
- Use existing Agent-Matrix patterns; do not invent new deployment layouts.
- Record all changes made for review.
- P0 action items in the design spec Section 16 are phase-gated, not blanket
  prerequisites. Phase 1 has no unresolved P0 blockers.
```

---

*Prepared as the consolidated implementation companion to the Galadriel v2.2 design specification.*
