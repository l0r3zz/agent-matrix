# Galadriel Implementation Plan

**Version:** 0.1  
**Date:** 2026-05-23  
**Related spec:** [Galadriel Agent Design Specification v2.1](galadriel-agent-design.md)  
**Status:** Planning document -- no implementation performed here

---

## 1. Purpose

This document turns the Galadriel design specification into an implementation sequence for retooling `agent0-2` as the specialized Galadriel agent.

The design specification remains the architectural source of truth. This plan records concrete implementation decisions, sequencing, file paths, and acceptance checks.

---

## 2. Phase 0 Decisions

### 2.1 Agent Zero Profile

Implement a dedicated `galadriel` Agent Zero profile.

Do not leave the profile as generic `Researcher`. Galadriel should inherit Researcher behavior but add:

- Archivist behavior
- Fleet community memory maintenance
- Open Brain write/read policy
- Compiled wiki maintenance
- Matrix/A2A channel arbitration
- Long-duration research coordination
- Sub-agent management

### 2.2 Research Model Route

Use an MCP-accessible Perplexity research tool as the first task-scoped model route.

The starting behavior should be based on `Cursor-Writing-Assistant-repo/agents/research-agent.mdc`, especially:

- Use Perplexity `sonar-pro`
- Request citations
- Prefer research-mode parameters over chat/ask mode
- Save structured research notes

Galadriel-specific additions:

- Support history, science, geopolitics, philosophy, and current events
- Store reusable findings in Open Brain
- Compile wiki pages when a topic matures
- Record model/tool provenance in artifacts

### 2.3 Open Brain Tools

Target the 6-tool Open Brain profile:

- Core required tools:
  - `search_thoughts`
  - `list_thoughts`
  - `thought_stats`
  - `capture_thought`
- Extended optional tools:
  - `search_by_date`
  - `get_search_protocol`

Clients must gracefully fall back to the core 4 if the extended tools are not available.

### 2.4 Wiki Storage

Store compiled wiki pages at:

```text
/a0/usr/workdir/galadriel-workspace/wiki/
```

Use repository mirroring only when a wiki page should become durable project documentation.

### 2.5 Long-Running Research State

Start with file-backed JSON job manifests.

Preferred path:

```text
/a0/usr/workdir/galadriel-workspace/jobs/
```

Database-backed scheduling can come later if the file-backed version proves useful.

---

## 3. Implementation Phases

### Phase 1 -- Profile Scaffold

Goal: make `agent0-2` load as Galadriel.

Tasks:

1. Create the `galadriel` Agent Zero profile.
2. Add Galadriel system prompt content from the design spec.
3. Add prompt extras for memory, channel arbitration, and role modes.
4. Configure default workspace directories:
   - `research/`
   - `drafts/`
   - `critiques/`
   - `validations/`
   - `wiki/`
   - `jobs/`
   - `logs/`
5. Verify Galadriel can state its mission and operating rules.

Acceptance checks:

- `agent0-2` starts with the `galadriel` profile.
- Galadriel identifies itself as researcher, archivist, librarian, and fleet memory maintainer.
- Galadriel knows Matrix is collaboration-first and A2A is preferred for file / large JSON handoff.

### Phase 2 -- Research Mode

Goal: implement the Researcher-derived mode.

Tasks:

1. Translate `research-agent.mdc` into a Galadriel research skill or prompt module.
2. Configure Perplexity MCP access.
3. Use `sonar-pro` with citations by default.
4. Save research artifacts with model/tool provenance.
5. Add Open Brain capture prompts for durable findings.

Acceptance checks:

- Galadriel can run "research mode" without changing its main Agent Zero model.
- Research output includes sources, dates, gaps, next steps, and provenance.
- Important findings can be written to Open Brain.

### Phase 3 -- Open Brain Memory Integration

Goal: make Open Brain the fleet memory system Galadriel actively maintains.

Tasks:

1. Verify Open Brain MCP connectivity.
2. Confirm available tools and classify server as core-4 or extended-6.
3. Add provenance metadata to all writes.
4. Define first-pass promotion rules.
5. Add graceful fallback if Open Brain is unavailable.

Acceptance checks:

- `search_thoughts` and `capture_thought` work from Galadriel.
- Galadriel records `agent_id`, `agent_alias`, `promotion_type`, and `source_context`.
- Galadriel reports degraded mode if Open Brain is unavailable.

### Phase 4 -- Compiled Wiki

Goal: build the first useful Open Brain compiled wiki workflow.

Tasks:

1. Define wiki page frontmatter.
2. Define topic slug rules.
3. Implement manual compile flow: "compile wiki page for X."
4. Pull source material from Open Brain and local research artifacts.
5. Record contradictions, open questions, and source provenance.

Acceptance checks:

- Galadriel can compile one wiki page into `/a0/usr/workdir/galadriel-workspace/wiki/`.
- The page includes timestamp, summary, claims, sources, contradictions, gaps, and related topics.
- The page does not claim to be the source of truth; it points back to Open Brain/source artifacts.

### Phase 5 -- Long-Running Research Jobs

Goal: support durable research tasks across sessions.

Tasks:

1. Define job manifest schema.
2. Store jobs under `/a0/usr/workdir/galadriel-workspace/jobs/`.
3. Implement states: `queued`, `scoping`, `researching`, `synthesizing`, `validating`, `wiki-compiling`, `completed`, `paused`, `failed`, `cancelled`.
4. Add checkpointing after each phase.
5. Add human-readable status summaries.

Acceptance checks:

- A research job can be paused and resumed.
- Partial findings survive restart/session loss.
- Completed jobs produce research notes, Open Brain captures, and optional wiki pages.

### Phase 6 -- Delegated Specialist Roles

Goal: expose borrowed Cursor-Writing-Assistant roles as Galadriel-managed workflow modes.

Tasks:

1. Convert role definitions into skills or prompt modules:
   - Research
   - Writing
   - Critique
   - Technical Validation
2. Define task packets and expected output schemas.
3. Use A2A delegation only when isolated long-running context or different model configuration is needed.
4. Add merge rules for delegated outputs.

Acceptance checks:

- User can ask Galadriel to run research, draft, critique, or validation mode.
- Galadriel can explain which role/mode was used.
- Delegated work includes provenance and is not silently merged without attribution.

---

## 4. Open Questions

1. Exact Agent Zero profile file layout on the deployed `agent0-2` version.
2. Exact Perplexity MCP server/tool name available in Agent Zero.
3. Whether Open Brain currently exposes the extended 6-tool profile or only the core 4.
4. Whether wiki pages should be mirrored into the Git repository automatically or only on human request.
5. What size threshold defines "large JSON" for A2A handoff.

---

## 5. First Frontier-Model Assignment

Give the implementer this instruction:

```text
Using galadriel-agent-design.md and galadriel-implementation-plan.md, inspect agent0-2's current Agent Zero profile and MCP configuration. Produce a concrete implementation diff plan for Phase 1 and Phase 2 only. Do not modify files until the plan is reviewed.
```

---

*Prepared as the first implementation companion to the Galadriel v2.1 design specification.*
