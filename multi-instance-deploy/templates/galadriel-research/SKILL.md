# galadriel-research

**Version:** 1.0.0  
**Author:** Galadriel / agent0-2  
**Tags:** research, deep-research, perplexity, writing-workflow, citations  
**Triggers:** research mode, deep research on, run research on, do deep research on, research this topic, gather sources on, look up, fact check  

---

## Description

Task-scoped deep research skill that wraps Perplexity Sonar Pro (`perplexity.perplexity_deep_research`) and Sonar (`perplexity.perplexity_quick_search`) with Galadriel's workflow contract: deterministic artifact naming, citation extraction, provenance metadata, and 7-phase writing workflow integration.

## Trigger Detection

The skill fires when the user says any trigger phrase followed by a topic—for example:

```text
"Run research mode on X"
"Deep research on the history of X"
"Gather sources on X and draft from them"
"Research this topic for me"
"Do a deep dive on X"
```

## Workflow

### Step 1: Check Model Routing Policy

Read `/a0/usr/workdir/galadriel-workspace/model-routing-policy.md` to determine:

- Which tool to use for research (default: `perplexity.perplexity_deep_research` for deep, `perplexity.perplexity_quick_search` for quick)
- Fallback tool if primary is unavailable (default: `search_engine`)

### Step 2: Build a Structured Query

Transform the user's topic into a structured research query that includes:

- The explicit research question or scope
- Request for multiple perspectives (Western, non-Western, academic, practitioner)
- Explicit instruction to cite sources
- Relevant time range if the topic is time-sensitive
- Subgroup breakdowns if the topic involves demographics or comparative analysis

**Example:** User says "research BRICS steel tariffs" → query becomes:

```text
Comprehensive analysis of BRICS steel tariff policies and their impact on global trade. Cover: current tariff structures by country (China, India, Russia, Brazil, South Africa), CBAM interactions, WTO disputes, impact on EU and US steel markets, economic modeling of tariff scenarios. Include multiple perspectives (BRICS bloc, EU, US, developing nations). Cite sources.
```

### Step 3: Execute Research

Call the tool determined in Step 1:

- **Deep research:** `perplexity.perplexity_deep_research(query=formatted_query)` — for substantive, multi-source research
- **Quick search:** `perplexity.perplexity_quick_search(query=formatted_query)` — for fact-checks, current events, quick lookups
- **Fallback:** `search_engine(query=``keyword query``)` — if Perplexity is unavailable

### Step 4: Save Artifact

Extract the `content` field from the result and structure it using the template at `galadriel-workspace/templates/research-mode.md`. Save to:

```text
galadriel-workspace/artifacts/YYYYMMDD-HHMMSS-{slug}-10-research.md
```

Where `{slug}` is a lowercase, hyphen-separated topic slug (e.g., `brics-steel-tariffs`).

### Step 5: Add Provenance Block

Append to the artifact:

```markdown
---

## Provenance

| Field | Value |
|-------|-------|
| Source model | Perplexity Sonar Pro (deep) / Sonar (quick) |
| Agent | Galadriel / agent0-2 |
| Research date | {YYYY-MM-DDTHH:MM:SS} |
| Confidence | {high|medium|low|mixed} |
| Perspective coverage | Western, non-Western, academic, practitioner |
| Artifact path | galadriel-workspace/artifacts/{filename} |
```

### Step 6: Report Back

Respond with:

- Executive summary (3-5 bullet points)
- Artifact path
- Confidence assessment
- Notable gaps or contradictions
- Suggested next steps (`"Ready for drafting," "Needs more research on X," etc.`)

---

## Integration Points

### 7-Phase Writing Workflow

After research completes (`10-research.md`), user can trigger the next phases:

```text
"Draft from this research"  → 30-draft.md
"Critique this draft"       → 40-critique.md
"Revise this"               → 50-revise.md
"Finalize this"             → 60-final.md
```

### Open Brain Capture (Phase 5)

When Phase 5 wiki compiler is active, key findings from research should be captured to Open Brain:

```text
open_brain.capture_thought(content="[Galadriel/agent0-2] {key finding with source context}")
```

### Wiki Compilation (Phase 5)

When Phase 5 wiki compiler is active, compiled wiki pages pull from research artifacts.

---

## Quality Standards

1. **Citation integrity:** All factual claims sourced. URLs preserved.
2. **Perspective coverage:** Non-Western perspectives included for historical/political topics.
3. **Confidence flags:** State clearly what is well-established vs. contested vs. speculative.
4. **No-leak:** Never include API keys, tokens, or credentials in artifacts.
5. **Provenance always:** Every artifact must have provenance metadata.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This skill definition |
| No additional script files required — uses existing MCP tools |

## Dependencies

- `perplexity.perplexity_deep_research` — MCP tool (required)
- `perplexity.perplexity_quick_search` — MCP tool (required)
- `search_engine` — Agent Zero built-in (fallback)
- `text_editor` — For saving artifacts (Agent Zero built-in)

## Model Routing

Delegates model selection to `/a0/usr/workdir/galadriel-workspace/model-routing-policy.md`.
