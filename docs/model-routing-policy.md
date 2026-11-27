# Galadriel Model Routing Policy v1.0

**Version:** 1.0.0  
**Date:** 2026-05-27  
**Purpose:** Single source of truth for which model/provider to use for each task type.

---

## Default Conversation

| Parameter | Value |
|-----------|-------|
| Provider | OpenRouter |
| Model | `deepseek/deepseek-v4-pro` |
| Use | All standard chat, analysis, non-research tasks |
| Notes | Set via agent profile in `usr/settings.json` |

---

## Deep Research

| Parameter | Value |
|-----------|-------|
| Provider | Perplexity MCP |
| Tool | `perplexity.perplexity_deep_research` |
| Model | Sonar Pro |
| Use | Citation-rich research requiring source verification, multi-source synthesis |
| Cost | Higher |
| Timeout | 120s |
| Trigger phrases | "research mode," "deep research on," "run research on," "deep dive on" |

---

## Quick Search

| Parameter | Value |
|-----------|-------|
| Provider | Perplexity MCP |
| Tool | `perplexity.perplexity_quick_search` |
| Model | Sonar |
| Use | Fast fact-checking, current events lookup, quick source gathering |
| Cost | Lower |
| Timeout | 60s |
| Trigger phrases | "quick search," "look up," "fact check," "what's happening with" |

---

## Web Search (Fallback)

| Parameter | Value |
|-----------|-------|
| Tool | `search_engine` (Agent Zero built-in) |
| Use | When Perplexity is unavailable, throttled, or errors out |
| Limitations | No structured citations, less synthesis capability |

---

## Drafting

| Parameter | Value |
|-----------|-------|
| Provider | OpenRouter (same as conversation) |
| Model | `deepseek/deepseek-v4-pro` |
| Notes | Drafting benefits from the same model for consistency. Can be overridden for stylistic variety. |

---

## Critique

| Parameter | Value |
|-----------|-------|
| Preference | Different model/viewpoint for fresh eyes |
| Option A | Same model with critique-specific system prompt |
| Option B | Subordinate agent with different model (Phase 6) |
| Current default | Option A (same model, different prompt framing) |

---

## Technical Validation

| Parameter | Value |
|-----------|-------|
| Provider | OpenRouter |
| Model | `deepseek/deepseek-v4-pro` |
| Notes | Technical correctness is model-agnostic; use whatever is available. May shift to specialist model in Phase 6. |

---

## Fallback Chain

```text
1. Perplexity deep research → sonar-pro
   ↓ (unavailable/timeout)
2. Perplexity quick search → sonar
   ↓ (unavailable)
3. search_engine (Agent Zero built-in)
   ↓ (all down)
4. Notify user, queue for retry
```

---

## Model Selection Decision Tree

```text
Task type?
├── Research (citation-rich, multi-source)
│   └── perplexity_deep_research (Sonar Pro)
├── Quick lookup / fact check / current events
│   └── perplexity_quick_search (Sonar)
├── Drafting / writing / analysis
│   └── Default LLM (deepseek-v4-pro via OpenRouter)
├── Critique
│   └── Default LLM with critique framing
├── Technical validation
│   └── Default LLM
└── Conversation / general
    └── Default LLM
```

---

## Cost Awareness

| Model | Approximate Cost | Use Sparingly For |
|-------|-----------------|-------------------|
| Sonar Pro (deep research) | Higher | Trivial questions, greetings, known facts |
| Sonar (quick search) | Medium | Deep multi-source research (insufficient depth) |
| DeepSeek V4 Pro | Standard OpenAI-compatible pricing | N/A (default) |

---

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-05-27 | 1.0.0 | Initial policy created. Phase 3 implementation. |
