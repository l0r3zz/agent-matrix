# Galadriel Research & Knowledge System Guide

> **Version:** 1.0  
> **Agent:** Galadriel / agent0-2 (`172.23.88.2`)  
> **Last Updated:** 2026-05-27  
> **Audience:** Agent-Matrix fleet users and administrators

---

## Table of Contents

1. [Memory Architecture](#1-memory-architecture)
2. [Open Brain — Fleet Memory](#2-open-brain--fleet-memory)
3. [Wiki System](#3-wiki-system)
4. [Research Modes](#4-research-modes)
5. [Quick Reference](#5-quick-reference)

---

## 1. Memory Architecture

Galadriel operates on a **three-layer memory system**. Understanding which layer does what is key to getting the most out of the research infrastructure.

### Layer Overview

| Layer | Scope | Persistence | What Lives Here |
|-------|-------|-------------|----------------|
| **Context Window** | Current conversation | Ephemeral (gone when chat ends) | Active reasoning, task state, working memory |
| **Agent Zero Local Memory** | Per-agent instance | Persistent across sessions | Personal preferences, task history, solutions, skills learned |
| **Open Brain (OB1)** | Fleet-wide | Durable shared store | Institutional memory, research findings, architectural decisions, cross-agent knowledge |

### What Agent Zero Does

Agent Zero is the **agent framework** — it's the runtime that Galadriel (and all other agents) run on. Each Agent Zero instance provides:

- **Local vector memory** — A per-agent FAISS store for personal memories, solutions, and fragments. This is fast, local, and private to each agent instance.
- **Tool execution** — Terminal, Python, Node.js, browser automation, file editing
- **MCP integration** — Connects to external tool servers (Open Brain, Matrix, Perplexity)
- **Sub-agent delegation** — Can spawn specialized subordinate agents for parallel work
- **Conversation persistence** — Chat history saved per session

**Key point:** Agent Zero's local memory is **per-instance**. Agent0-1's memories are separate from Agent0-2's. They don't share local memory.

### What Open Brain Does

Open Brain (OB1) is the **fleet's shared knowledge base** — a PostgreSQL + pgvector semantic memory system accessible to all agents and external MCP clients.

- **Shared across all agents** — Every agent in the fleet can read from and write to OB1
- **Semantic search** — Queries are matched by meaning, not just keywords
- **Auto-extracted metadata** — Topics, people, types, and tags extracted automatically on capture
- **Durable** — Survives agent restarts, container rebuilds, and session resets
- **Citation-ready** — Every thought has a unique ID and URL: `https://openbrain.local/thoughts/{id}`

**Infrastructure:**
- Runs at `172.23.90.2:3100` on the shared services macvlan segment
- Backed by PostgreSQL with pgvector for embedding storage
- Accessible via MCP tools from any agent

### Memory Query Order

When Galadriel answers a question, she searches memory in this order:

1. **Context window** — Is the answer already in this conversation?
2. **Local Agent Zero memory** — Do I have a personal memory about this?
3. **Open Brain** — Does the fleet know about this?

For **institutional, cross-agent, or fleet knowledge questions**, Open Brain search is **mandatory** — Galadriel will always check OB1 before answering from training data alone.

---

## 2. Open Brain — Fleet Memory

### How Open Brain Gets Updated

OB1 is populated through several channels:

#### Automatic Capture (Agent-Driven)
- **After research tasks** — When Galadriel completes significant research, high-value findings are captured to OB1 with provenance metadata
- **After architectural decisions** — Fleet infrastructure decisions, deployment patterns, and operational lessons are captured
- **Wiki compilation** — When a wiki page is compiled, key claims and sources may be persisted to OB1
- **Cross-agent coordination** — Outcomes from multi-agent work are captured for fleet memory

#### Manual Capture (User-Initiated)
You can explicitly tell Galadriel to save something to Open Brain:

> *"Save this to Open Brain: [your insight/note/decision]"*  
> *"Capture to OB1: [key finding]"*  
> *"Remember this in fleet memory: [important fact]"*

All captures include **provenance metadata**:
- Which agent wrote it
- What task/research produced it
- Source URLs or references
- Confidence/uncertainty assessment
- Timestamp

#### IDE/External Capture
Open Brain is also accessible via MCP from external tools and IDE harnesses (e.g., VS Code, Cursor). Any MCP client pointing at `172.23.90.2:3100` can capture thoughts.

### How to Access Open Brain Through Chat

You don't need to use any special commands — just ask naturally:

| What You Want | What to Say |
|---|---|
| Search for knowledge | *"What do we know about X?"* / *"Search Open Brain for X"* |
| Browse recent captures | *"Show me recent Open Brain entries"* / *"List recent thoughts"* |
| Filter by topic | *"List OB1 thoughts about Docker networking"* |
| Filter by person | *"What's in OB1 about Geoff?"* |
| Filter by time | *"What was captured in the last 7 days?"* |
| Get stats | *"How many thoughts are in Open Brain?"* / *"OB1 stats"* |
| Save something | *"Save to Open Brain: [content]"* |
| Deep search | *"Search OB1 for Agent-Matrix deployment patterns"* |

### OB1 Tool Reference

| Tool | What It Does |
|---|---|
| `search_thoughts` | Semantic search — finds thoughts by meaning, not just keywords |
| `list_thoughts` | List recent thoughts with optional filters (type, topic, person, days) |
| `thought_stats` | Summary: totals, type breakdown, top topics and people |
| `capture_thought` | Save a new thought with auto-extracted metadata |

### Citation Format

When Galadriel cites Open Brain knowledge, she uses OB1 citation URLs:
```
https://openbrain.local/thoughts/{thought_id}
```
These appear in research artifacts, wiki pages, and factual claims sourced from fleet memory.

---

## 3. Wiki System

The wiki is a **compiled synthesis layer** — human-readable pages built from Open Brain thoughts, research artifacts, and web sources.

### Architecture

```
Open Brain (OB1)          ← Source of truth (durable semantic memory)
       ↓
Wiki Compiler             ← Synthesizes OB1 thoughts + artifacts + web sources
       ↓
wiki/*.md                 ← Markdown source pages with YAML frontmatter
       ↓
MkDocs (Material theme)   ← Renders to searchable HTML site
       ↓
http://agent0-2.cybertribe.com:8080/   ← Browse in your browser
```

**Important:** The wiki is a **read-optimized cache**, NOT the source of truth. Open Brain is always authoritative. Wiki pages can become stale and should be recompiled when OB1 has newer data.

### How to Access the Wiki

**In your browser:**
```
http://agent0-2.cybertribe.com:8080/
```
or directly:
```
http://172.23.88.2:8080/
```

**Features:**
- Full-text search across all wiki pages
- Navigation sidebar with all topics
- Dark/light mode toggle
- Table of contents per page
- Live-reload when pages change

### How the Index Page Gets Updated

The wiki index (`index.md`) and navigation sidebar (`mkdocs.yml`) are **auto-updated** through a post-compile hook:

1. You ask Galadriel to compile a wiki page on a new topic
2. `wiki-compiler.py` writes `wiki/{topic-slug}.md`
3. **Post-compile hook fires automatically:**
   - `wiki-index-updater.py` scans all `wiki/*.md` files
   - Reads YAML frontmatter from each page (title, status, confidence, source counts)
   - Regenerates `wiki/index.md` with an updated topic table
   - Rewrites the `nav:` section in `mkdocs.yml` with the new page
4. MkDocs dev server detects the file changes
5. Browser auto-refreshes — new page appears in index and sidebar

**No manual intervention required.** Compile a page, it shows up everywhere.

### Wiki Page Structure

Every wiki page includes:
- **YAML frontmatter** — Title, slug, status, confidence, source counts, OB1 thought IDs, provenance
- **Executive Summary** — Quick overview of the topic
- **Key Facts and Claims** — Extracted and synthesized from sources
- **Source List** — URLs and references with reliability ratings
- **Known Contradictions** — Where sources disagree
- **Open Questions** — Research gaps identified
- **Related Open Brain Topics** — Cross-references to fleet knowledge
- **Provenance Notes** — Which agent compiled it, when, from what sources

### How to Request Wiki Pages

| What You Want | What to Say |
|---|---|
| Compile a new page | *"Compile a wiki page on [topic]"* |
| Refresh an existing page | *"Refresh the wiki page for [topic]"* |
| Check what exists | *"What wiki pages do we have?"* / Browse the index |
| Compile from research | Complete a Tier 3 research job (auto-compiles) |

### Manually Running the Index Updater

```bash
# From inside the container:
python /a0/usr/workdir/galadriel-workspace/phase5_codegen_bundle/scripts/wiki-index-updater.py

# Dry-run preview:
python /a0/usr/workdir/galadriel-workspace/phase5_codegen_bundle/scripts/wiki-index-updater.py --dry-run
```

---

## 4. Research Modes

Galadriel supports **five tiers of research**, from quick answers to extended multi-session investigations. You can invoke any tier explicitly or let Galadriel select based on your phrasing.

### Tier 0 — Quick Answer

**What it is:** Direct answer from knowledge, training data, and Open Brain memory.  
**Time:** Seconds  
**Output:** Chat response

**When to use:** Simple factual questions, definitions, explanations.

**How to invoke:**
> *"What is X?"*  
> *"Explain Y"*  
> *"How does Z work?"*

**What happens:**
1. Check context window and local memory
2. Query Open Brain if the topic might have fleet knowledge
3. Synthesize answer
4. One web search if currency verification needed

---

### Tier 1 — Sourced Lookup

**What it is:** Multi-source search and synthesis with citations.  
**Time:** 1–3 minutes  
**Output:** Chat response with sources and citations

**When to use:** You need a researched answer with references, but not a full report.

**How to invoke:**
> *"Research X"*  
> *"What do we know about X?"*  
> *"Look into X for me"*  
> *"Tier 1 research on X"*

**What happens:**
1. Open Brain search for prior fleet knowledge
2. Web search for current information
3. Perplexity quick search for sourced web data
4. Cross-reference sources
5. Synthesized answer with citations

---

### Tier 2 — Deep Research

**What it is:** Intensive research using Perplexity deep research (Sonar Pro), OB1, and multi-source cross-referencing.  
**Time:** 3–10 minutes  
**Output:** Research artifact saved to `artifacts/` + chat summary with citations

**When to use:** Complex topics requiring depth, multiple perspectives, or academic rigor.

**How to invoke:**
> *"Deep research on X"*  
> *"Do a deep dive on X"*  
> *"Tier 2 research on X"*

**What happens:**
1. Open Brain search for prior fleet knowledge
2. Perplexity deep research (Sonar Pro model) — returns detailed analysis with citations
3. Web search for supplementary sources
4. Multi-perspective analysis (non-Western views where relevant)
5. Research artifact saved with provenance metadata
6. High-confidence findings optionally captured to Open Brain

---

### Tier 3 — Full Research Job

**What it is:** Complete 7-phase research and writing workflow with job tracking, critique, and wiki compilation.  
**Time:** 15–45 minutes (with checkpoints)  
**Output:** Multiple phase artifacts + final document + wiki page auto-compiled

**When to use:** You need a comprehensive, publishable analysis on a topic. The works.

**How to invoke:**
> *"Start a research job on X"*  
> *"Full research on X"*  
> *"Tier 3 research on X"*  
> *"Research job: [topic description]"*

**What happens:**

| Phase | Code | What Happens |
|-------|------|--------------|
| **Scope** | `00-scope` | Define requirements, audience, constraints, deliverables |
| **Research** | `10-research` | OB1 + Perplexity deep + web search + source credibility scoring |
| **Outline** | `20-outline` | Section architecture and argument flow |
| **Draft** | `30-draft` | First complete pass |
| **Critique** | `40-critique` | Quality review: accuracy, bias, clarity, omissions, missing perspectives |
| **Revise** | `50-revise` | Issue resolution and strengthening |
| **Finalize** | `60-final` | Final formatting, citations, metadata |
| **Wiki** | `wiki-compilation` | Auto-compile wiki page from final output |

Each phase produces a **timestamped artifact** in `galadriel-workspace/artifacts/`:
```
YYYYMMDD-HHMMSS-{topic-slug}-{phase-code}.md
```

A **job manifest** tracks all phases, timestamps, errors, and OB1 captures in `galadriel-workspace/jobs/`.

---

### Tier 4 — Extended Investigation (Future)

**What it is:** Multi-session, multi-day research with scheduled tasks and progressive refinement.  
**Time:** Days to weeks  
**Output:** Evolving wiki page, OB1 captures over time, periodic reports

**When to use:** Long-horizon topics requiring ongoing monitoring, multiple research passes, or delegated sub-agent work.

**How to invoke:**
> *"Investigate X over the next week"*  
> *"Start an ongoing investigation on X"*  
> *"Tier 4 research on X"*

**What will happen (planned):**
1. Scheduled research tasks across multiple sessions
2. Sub-agents delegated for specific angles or source types
3. Progressive refinement — wiki page updated after each pass
4. Periodic progress reports
5. Automated staleness detection and refresh triggers

*Note: Tier 4 is a planned capability. Tiers 0–3 are fully operational now.*

---

### Explicit Tier Selection

You can always specify a tier directly:

> *"Tier 0: What is CBAM?"*  
> *"Tier 2: Deep research on quantum computing error correction"*  
> *"Tier 3: Full research job on BRICS de-dollarization strategies"*

Galadriel will execute exactly the tier you request.

---

## 5. Quick Reference

### Trigger Phrases

| You Say | Research Tier |
|---|---|
| *"What is..."* / *"Explain..."* / *"How does..."* | Tier 0 — Quick Answer |
| *"Research..."* / *"Look into..."* / *"What do we know about..."* | Tier 1 — Sourced Lookup |
| *"Deep research on..."* / *"Deep dive on..."* | Tier 2 — Deep Research |
| *"Research job on..."* / *"Full research on..."* | Tier 3 — Full Research Job |
| *"Tier N: ..."* | Explicit tier selection |

### Key URLs

| Service | URL |
|---|---|
| Wiki (browser) | `http://agent0-2.cybertribe.com:8080/` |
| Wiki (direct IP) | `http://172.23.88.2:8080/` |
| Open Brain citations | `https://openbrain.local/thoughts/{id}` |
| Open Brain service | `172.23.90.2:3100` |

### Key Directories

| Path | Contents |
|---|---|
| `galadriel-workspace/wiki/` | Wiki source Markdown pages |
| `galadriel-workspace/artifacts/` | Research phase artifacts |
| `galadriel-workspace/jobs/` | Job manifests (JSON lifecycle tracking) |
| `galadriel-workspace/staging/` | Ephemeral OB1 data staging |
| `galadriel-workspace/phase5_codegen_bundle/scripts/` | Pipeline scripts |

### Open Brain Commands

| Action | What to Say |
|---|---|
| Search | *"Search Open Brain for [topic]"* |
| List recent | *"Show recent OB1 entries"* |
| Get stats | *"OB1 stats"* |
| Save knowledge | *"Save to Open Brain: [content]"* |

### Wiki Commands

| Action | What to Say |
|---|---|
| Compile new page | *"Compile a wiki page on [topic]"* |
| Refresh existing | *"Refresh the wiki for [topic]"* |
| List pages | *"What wiki pages do we have?"* |

---

*Generated by Galadriel / agent0-2 — 2026-05-27*  
*Part of the Agent-Matrix fleet documentation*
