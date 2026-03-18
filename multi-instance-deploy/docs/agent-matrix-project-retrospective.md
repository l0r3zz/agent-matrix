# Agent-Matrix: Project Retrospective & Case Study
## Building a Sovereign AI Agent Federation in 30 Days with a Two-Person Human-AI Team

**Document Type:** Project Retrospective / Case Study  
**Date:** March 17, 2026 (project completed March 13, 2026)  
**Author:** Agent-Matrix Project Team
- Principal Engineer: Geoff White
- AI Collaborator: Agent0-1 (Gandalf) 

**Audience:** Project Managers and Engineering Leaders



Companion Documents: 
- [agent-matrix-design.md](agent-matrix-design.md)
- [operations-manual.md](operations-manual.md)
- [theory-of-operations.md](theory-of-operations.md)
---

## Executive Summary

Agent-Matrix is a 30-day infrastructure project that delivered a fleet of five autonomous AI agents, each running its own matrix messaging server, interconnected through the Matrix Protocol federation mechanism. The agents reside on a 128GB Supermicro E300-15 server behind a lab firewall and reachable by humans through an internet-accessible Matrix server running in a pod on an external Kubernetes cluster. A OpenVPN tunnel provides secure access on a dedicated network segment on the lab network. Every objective in the [design document](agent-matrix-design.md) has been fulfilled.

The project was executed by a two-person team: one Principal-grade software engineer who architected the system (Geoff White) and one AI collaborator (Agent0-1, known as "Gandalf") who wrote virtually all of the code. The total investment was 110 human-hours and $541 in AI compute costs. The project shipped four major architecture versions, survived two full-stack pivots including a complete homeserver replacement, and produced a production-grade deployment automation system with comprehensive documentation -- a scope of work that would traditionally require a small engineering team working over several months.

This retrospective examines what worked, what didn't, what the model performance differences revealed, and what the collaboration model tells us about the future of software project delivery.

---
{::pagebreak /}
## 1. Project Background

### The Problem Statement

Agent-Matrix is a platform for building decentralized networks of cooperating AI agents and humans. Rather than centralizing AI behind a single API, each agent is a sovereign node on a federated messaging network -- with its own identity, its own homeserver, and the ability to communicate with any other participant using standard protocols.

Give every AI agent a first-class communication identity on the [Matrix protocol](https://matrix.org), the same open standard used by the French government, the German Bundeswehr, and Mozilla for secure real-time messaging. Humans connect with standard Matrix clients like Element or FluffyChat. Agents connect through a bridge that translates between Matrix messages and their AI reasoning engine.

The Agent of choice for this implementation is [Agent0](https://www.agent-zero.ai). [Agent0 is a sophisticated AI agent](https://www.agent-zero.ai/p/linux-foundation-article/) that can be configured to act as a personal assistant, a research assistant, or a general-purpose AI assistant. A much more mature (and secure) project than the notorious and viral OpenClaw.

The result is a controlled lab environment for exploring agentic architectures, context engineering, and human-AI collaboration -- where all communication is observable, auditable, and built on open standards.


### Success Criteria -- All Met

| Criterion | Target | Result |
|-----------|--------|--------|
| Operational AI agents | 5 | 5 deployed and operational |
| Each agent has unique network identity | Yes | Yes -- per-agent Matrix homeserver |
| Agents can message each other | Yes | Yes -- verified across all 5 agents |
| Humans can message agents from standard apps | Yes | Yes -- Element, FluffyChat, any Matrix client |
| Zero-touch deployment for new agents | Scripted | Yes -- `create-instance.sh` + `finalize-instance.sh` |
| Auto-recovery from crashes | <60 seconds | <30 seconds via watchdog |
| Documentation suite | Complete | 7+ documents including design, ops manual, theory of operations |
| All agents consolidated on single host | Yes | Yes -- all 5 on g2s (supermicro server ) |

---
{::pagebreak /}
## 2. The Team

The entire project was delivered by two contributors:

| Role | Who | Function |
|------|-----|----------|
| **Project Lead / Architect** | Geoff White (Principal SRE, 30+ years experience) | Vision, architecture decisions, infrastructure access, debugging, quality review, strategic direction, "when to pivot" judgment calls |
| **Staff Engineer** | AI (Agent0-1 "Gandalf" via Agent Zero + Claude Opus) | All code generation, Python glue code (especially matrix-bot), documentation, diagnostics, configuration, deployment automation, research, troubleshooting |

There was no separate QA engineer, no DevOps specialist, no technical writer. The AI collaborator filled all of these roles under human direction.

### The Human-AI Dynamic

The human architect brought the design vision, infrastructure expertise, and three decades of production systems experience. He set the architecture, made every strategic decision, and knew when to stop throwing good effort after bad.

Agent0-1 ("Gandalf") was the workhorse. It wrote virtually every line of Python, Bash, TypeScript, YAML, and Docker configuration in the project. The matrix-bot -- the reactive bridge that connects Matrix messages to Agent Zero's reasoning engine -- was designed and implemented almost entirely by Gandalf. The same goes for the deployment automation scripts, the watchdog system, the token synchronization logic, and the documentation suite.

This was not a human writing code with AI suggestions. This was an AI writing production systems under the direction of an engineer who knew exactly what "done" looked like.

---
{::pagebreak /}
## 3. Project Timeline & Iterations

The project ran from approximately February 10 to March 13, 2026 -- roughly 30 calendar days. Work was organized into four distinct phases, each representing a major architectural iteration. This was not planned as a phased rollout; rather, each phase emerged from lessons learned (and failures encountered) in the previous one.

### Phase 1-2: Foundation (Days 1-14)
**Scope:** Stand up a single AI agent with its own messaging server. Establish basic federation (server-to-server communication).

- Deployed first Agent Zero instance with a Dendrite homeserver
- Attempted federation with the gateway server
- Encountered persistent TLS certificate and protocol-level failures
- Established the macvlan networking architecture (dedicated IP per container)

**Key Decision:** Committed to "one homeserver per agent" architecture despite complexity. The alternative -- shared homeserver -- would have been simpler but violated the project's core design principle of agent sovereignty.

### Phase 3: Multi-Instance Automation (Days 14-21)
**Scope:** Scale from one agent to many. Automate deployment.

- Built `create-instance.sh` -- a zero-touch provisioning script
- Integrated PKI certificate authority (Smallstep step-ca) for TLS
- Deployed agents 0-2 and 0-3
- Discovered and resolved inter-agent communication loops ("crosstalk")
- Built bot message filtering system with trigger prefixes
- Created decommission/rebuild scripts for fleet management

**Key Decision:** Invested in automation early despite having only two instances. This paid dividends during the Phase 4 migration, where all instances needed rebuilding.

### Phase 4: The Pivot -- Continuwuity Edition (Days 21-30)
**Scope:** Replace the homeserver software entirely after stability issues proved unfixable.

- Migrated from Dendrite (Go) to Continuwuity (Rust) across the entire fleet
- Redesigned container architecture from 2 containers to 3 (added Caddy TLS reverse proxy)
- Built watchdog auto-recovery system with token synchronization
- Implemented crash hardening with persistent logging
- Deployed all 5 agents (agent0-1 through agent0-5) on g2s
- Migrated agent0-1 from tarnover to g2s (full consolidation)
- Completed soak testing
- Produced comprehensive documentation suite (design, theory of operations, operations manual)

**Key Decision:** The decision to abandon Dendrite after three weeks of investment was the project's most consequential call. Gandalf conducted a systematic evaluation of seven alternative homeserver implementations, producing a research report with clear recommendations. The human made the final go/no-go decision based on that analysis. Total time from "Dendrite is broken" to "Continuwuity fleet operational": approximately one week.

---
{::pagebreak /}
## 4. Cost & Effort Analysis

### Actual Investment

| Resource | Amount | Notes |
|----------|--------|-------|
| Calendar time | ~30 days | Includes weekends, not all active |
| Human hours | ~110 | Estimated across all sessions |
| AI compute cost | $541 | Via OpenRouter API |
| Tokens processed | 606 million | Across all models |
| API requests | 49,000 | Average ~12,400 tokens per request |

### AI Cost Breakdown by Model

| Model | Spend | Tokens | Requests | Primary Role |
|-------|-------|--------|----------|-------------|
| Claude Opus 4.6 | $281 | 166M | 2,940 | Architecture, reasoning, complex debugging, code generation |
| Gemini 3 Flash Preview | $136 | 232M | 43,000 | Bulk processing, memory operations, routine tasks |
| Grok 4.20 Multi-Agent Beta | $35.80 | 45.5M | -- | Multi-agent experiments |
| Nemotron 3 Super | Free | -- | 657 | Utility tasks |
| Others | $87.90 | 162M | 2,550 | Various secondary tasks |

52% of all AI spend ($281 of $541) went to Claude Opus 4.6 -- the model used for every critical architectural decision, complex debugging session, and production code generation. The primary agent (agent0-1, "Gandalf") consumed the vast majority of compute. The remaining agents consumed minimal resources, mostly during infrastructure testing.

### Traditional Comparison Estimate

To contextualize this investment, consider what this project scope would require with a conventional team:

| Factor | Human-AI Team | Traditional Team (Estimate) |
|--------|---------------|-----------------------------|
| Headcount | 1 human + AI | 2-3 engineers |
| Calendar time | 30 days | 8-12 weeks |
| Engineering hours | ~110 human + AI | 400-600 human hours |
| Fully-loaded cost | ~$17,000-20,000 | ~$60,000-120,000 |
| Documentation | Comprehensive (AI-generated) | Often deferred or minimal |

Human cost estimated at $150/hr fully-loaded for senior infrastructure engineer.

The AI compute cost ($541) is a rounding error compared to the human labor it displaced. The more significant economic factor is the compression of calendar time and the elimination of hiring/coordination overhead.

---
{::pagebreak /}
## 5. Model Performance: Not All AI Is Created Equal

One of the project's clearest findings was the dramatic performance gap between LLM models. OpenRouter's model-switching capability made this visible in real-time -- the engineer could change models on the fly and immediately observe the difference.

### The Claude Opus Effect

Anthropic's Claude Opus 4.6 was the undisputed apex model for this project. Its performance on architecture, troubleshooting, and code generation was in a class by itself.

The pattern repeated throughout the project: a complex debugging session or architectural question would be attempted with a less expensive model. The model would make progress, then plateau -- going in circles, producing subtly wrong configurations, or generating plausible-sounding explanations that didn't match reality. At that point the engineer's refrain became a running joke: **"Better call Claude."**

Claude would come in, digest the full context, identify what the other model had missed or gotten wrong, and in minutes would right all wrongs. Not incrementally -- decisively. Where other models would produce three attempts that each introduced new problems, Claude would produce one attempt that worked.

Specific examples:
- **Federation TLS debugging:** After hours of a cheaper model suggesting increasingly baroque certificate chain configurations, Claude identified the actual root cause (Synapse's Twisted library requires the root CA, not just the intermediate) in a single exchange.
- **Continuwuity migration architecture:** Claude designed the 3-container model with Caddy TLS sidecar on the first attempt. The architecture has survived without modification through all subsequent deployments.
- **Watchdog and token sync system:** Claude wrote the complete watchdog, token guard, and health probe system in one focused session. It worked on first deployment.

### Cost vs. Value

Claude Opus is the most expensive model on OpenRouter. At $281 for the entire project, it was also the single best investment. The cheap models saved money per-token but cost time -- human time, which is orders of magnitude more expensive than token cost. Every hour the engineer spent redirecting a struggling model was an hour not spent on the next objective.

The value proposition is unquestionable: for work requiring real architectural reasoning, multi-system debugging, or production-quality code, Claude Opus paid for itself many times over in human hours saved.

### Model Tiering in Practice

The project naturally evolved a model tiering strategy:

| Tier | Model | Use Case | Cost Profile |
|------|-------|----------|-------------|
| **Apex** | Claude Opus 4.6 | Architecture, complex debugging, production code, pivotal decisions | High per-token, low total (used selectively) |
| **Workhorse** | Gemini 3 Flash Preview | Memory operations, bulk processing, routine code, simple questions | Low per-token, high volume |
| **Experimental** | Grok, Nemotron, others | Testing, exploration, non-critical tasks | Varies |

OpenRouter made this tiering frictionless. Switching models took seconds, and the engineer could escalate from Flash to Opus the moment a task exceeded the cheaper model's capability. This is analogous to calling in a specialist consultant when the generalist hits the wall -- except the "consultant" is available instantly and charges by the token.

---
{::pagebreak /}
## 6. How the Collaboration Actually Worked

### Session Structure

Work happened in focused sessions of 2-6 hours. A typical session followed this pattern:

1. **Human sets objective:** "We need to get federation working between agent0-1 and the gateway" or "The bot keeps dying silently -- investigate and fix."
2. **AI investigates:** Runs diagnostic commands, reads logs, checks configurations, identifies root cause.
3. **AI proposes solution:** Presents analysis and recommended fix with implementation plan.
4. **AI implements:** Writes code, modifies configs, deploys changes -- all through direct command execution.
5. **Human validates:** Tests the result, reports outcome, approves or redirects.
6. **Iterate or advance:** Repeat until the objective is met, then move to the next task.

### What the AI Did Well

- **Volume of output:** Gandalf wrote every line of production code -- Python bots, Bash automation, Docker Compose files, YAML configurations, TypeScript bridges, Caddyfiles, and watchdog scripts. The matrix-bot alone is several hundred lines of Python handling sync loops, message routing, markdown conversion, auto-join, room context persistence, and error recovery.
- **Systematic debugging:** When something failed, the AI followed a methodical diagnostic process -- checking logs, testing connectivity, isolating variables -- rather than guessing.
- **Context retention:** Agent Zero's memory system allowed Gandalf to persist critical knowledge across sessions (architecture decisions, known issues, configuration details), partially compensating for the context window limitations of individual conversations.
- **Documentation as a byproduct:** Because the AI generated all artifacts through text, documentation was a natural output rather than an afterthought. The project has a design document, operations manual, theory of operations, migration guide, and research reports -- all written during the build, not after.
- **Research depth:** When a technology decision was needed (e.g., replacing Dendrite), the AI evaluated seven alternatives across multiple dimensions and produced a structured comparison -- work that would take a human engineer several days of reading.

### What the AI Did Poorly

- **Novel infrastructure debugging:** When problems crossed system boundaries (e.g., Docker macvlan + DD-WRT router + OpenVPN tunnel + TLS certificate chain), the AI could diagnose individual components but struggled to see the full picture. The human often had to connect the dots.
- **Knowing when to stop:** The AI would sometimes continue attempting incremental fixes on a fundamentally broken approach. The decision to "scrap and rebuild" was consistently a human call.
- **Remote system access:** The AI operated from within a Docker container and couldn't always reach external infrastructure. When blocked, it provided exact manual commands for the human to execute -- effective but slower.
- **Context loss between sessions:** Despite the memory system, complex debugging state was partially lost between sessions. Resuming a multi-day investigation always involved some re-orientation time.
- **Model-dependent quality:** With cheaper models, the AI's output quality dropped noticeably on complex tasks. The human learned to recognize when the model was spinning its wheels and escalate to Claude Opus rather than waste time.

### Decision-Making Model

| Decision Type | Who Decided | Examples |
|---------------|-------------|----------|
| **Strategic** | Human | Architecture philosophy, when to pivot, scope boundaries, model selection |
| **Technical** | AI (human approval) | Implementation approach, tool selection, code architecture |
| **Tactical** | AI (autonomous) | Debugging sequence, code style, documentation structure |

The most important decisions -- particularly the two major pivots -- were collaborative. The AI provided analysis and options; the human made the call. This mirrors a traditional senior-engineer/tech-lead dynamic, except the AI produced the analysis in minutes rather than days.

---
{::pagebreak /}
## 7. Setbacks & Recovery

This project had a failure rate that would alarm any PM reviewing a status dashboard. The team executed 4+ database wipes, 3 room migrations, and 2 full architectural pivots.

### The Failure Catalog

| Category | Specific Failures | Resolution |
|----------|-------------------|------------|
| **Federation** | TLS cert chain errors, SSRF protections blocking connections, key verification failures | Iterative debugging; eventually resolved by switching homeserver software |
| **Stability** | Silent bot process deaths, sync freezes from corrupted event graphs, 401 auth errors from stale tokens | Watchdog system, crash hardening, token refresh automation |
| **Networking** | Docker macvlan bridge issues, missing static routes, OpenVPN routing conflicts | Manual router configuration by human; AI-provided diagnostic commands |
| **Data** | Database corruption, ed25519 cryptographic panics, room state corruption | "Nuclear wipe" -- full database reset and fresh start |
| **Communication** | Agent crosstalk loops (agents triggering each other infinitely) | Trigger prefix filter system |

### The "Nuclear Wipe" Pattern

When incremental fixes accumulated complexity without resolving the root issue, the team would execute a clean-slate rebuild. This happened at least four times.

Traditional project management would flag this as rework and waste. In this context, it was the most efficient path. The AI could regenerate all configurations and deploy a fresh instance in under an hour. The cost of a "nuclear wipe" was roughly $5-10 in AI compute and 30-60 minutes of human attention.

This only worked because the team had invested in deployment automation. Without `create-instance.sh` and the template system, each rebuild would have been a multi-hour manual process.

### The Dendrite-to-Continuwuity Pivot

The largest setback was discovering -- after three weeks -- that the chosen homeserver software (Dendrite) had fundamental stability issues that could not be resolved through configuration or workarounds. Dendrite had been stalled since August 2025 with no updates.

The recovery process:
1. AI conducted systematic research on seven alternative homeserver implementations (1-2 hours)
2. AI produced a structured comparison document with clear recommendation
3. Human reviewed analysis, approved the pivot to Continuwuity (Rust-based Conduit/Conduwuit fork)
4. AI designed new three-container architecture with Caddy TLS sidecar
5. AI updated all templates, scripts, and documentation
6. Team rebuilt all instances on the new stack
7. Deployed all 5 agents to full operational status

The deployment automation built in Phase 3 made the migration mechanically straightforward despite being architecturally significant.

---
{::pagebreak /}
## 8. Final Deliverables

### What Shipped

| Deliverable | Detail |
|-------------|--------|
| **5 operational AI agents** | agent0-1 through agent0-5, all on g2s, all Continuwuity, all Standard profile |
| **3-container architecture** | Agent Zero + Continuwuity homeserver + Caddy TLS proxy per instance |
| **Full federation** | All 5 agents federated with Synapse gateway, verified bidirectional communication |
| **Human-agent interaction** | Humans connect via Element/FluffyChat to matrix.v-site.net, message any agent |
| **Zero-touch provisioning** | `create-instance.sh` + `finalize-instance.sh` for complete agent deployment |
| **Automated recovery** | Watchdog + token guard + scheduled health probes, <30s MTTR |
| **Fleet management** | `sync-fleet.sh`, `fix-agentX-services.sh`, `decommission-instance.sh` |
| **Documentation suite** | Design doc (v5.0), theory of operations, operations manual, migration guides, multi-instance guide, this retrospective |

### Design Objectives -- All Fulfilled

Per the [agent-matrix-design.md](agent-matrix-design.md) (v5.0):

| Design Principle | Status |
|-----------------|--------|
| One homeserver per agent | Fulfilled -- each agent has its own Continuwuity instance |
| Standard protocols only | Fulfilled -- all communication via Matrix federation |
| Isolated by default | Fulfilled -- private LAN, VPN tunnel, PKI |
| Humans welcome | Fulfilled -- any Matrix client connects via Synapse gateway |
| Horizontally scalable | Fulfilled -- 5 agents on one host, scripted provisioning |

---
{::pagebreak /}
## 9. Key Metrics Summary

| Metric | Value |
|--------|-------|
| Calendar time | ~30 days |
| Human hours | ~110 |
| AI compute cost | $541 |
| Tokens processed | 606M |
| API requests | 49K |
| Agents deployed | 5 operational |
| Container architecture | 3-container (A0 + Continuwuity + Caddy) |
| Primary host | g2s (128 GB RAM, all agents consolidated) |
| Automation scripts created | 10+ |
| Documentation artifacts | 7+ comprehensive documents |
| Architecture versions | 4 major (v1 through v5.0) |
| Major pivots | 2 (Dendrite to Continuwuity; 2-container to 3-container) |
| Database wipes | 4+ |
| Mean time to recovery (watchdog) | <30 seconds |
| Top model spend | Claude Opus 4.6: $281 (52% of total) |
| Top model by volume | Gemini 3 Flash Preview: 232M tokens, 43K requests |

---
{::pagebreak /}
## 10. Lessons Learned

### For Project Managers

**1. AI changes the economics of rework.**  
Traditional PM practice treats rework as waste to be minimized. When your "engineer" can regenerate a deployment in minutes for pennies, the calculus changes. Rapid prototyping, testing, and rebuilding becomes cheaper than careful upfront planning for every contingency.

**2. The human's role shifts from doing to directing.**  
In 110 hours of human effort, very few were spent writing code. Most were spent making decisions, validating results, debugging cross-system issues the AI couldn't reach, and providing strategic direction. The PM skill set -- scope management, prioritization, risk assessment -- becomes the primary technical contribution.

**3. Documentation is no longer a phase; it is a byproduct.**  
The AI generated comprehensive documentation as a natural side effect of its working process. Design documents, operations manuals, and research reports were produced during development, not deferred to a documentation sprint that never happens.

**4. Context management is the new critical path.**  
The AI's effectiveness degraded when context was lost between sessions. Investing in persistent memory, clear naming conventions, and comprehensive commit messages directly impacts the AI collaborator's productivity.

**5. Not all AI is equal -- model selection is a strategic decision.**  
The performance gap between models is not incremental; it is categorical. A task that a cheaper model fails at for hours, Claude Opus solves in minutes. The cost difference is pennies; the time difference is the project schedule. Budget for apex-tier models on critical-path work.

**6. "When to stop" is a human judgment call.**  
The AI excelled at persistence -- it would continue attempting solutions indefinitely. Knowing when an approach was fundamentally broken and required a pivot was consistently a human decision.

### For Engineering Leaders

**7. Invest in automation early, even at small scale.**  
The deployment automation built for two instances paid for itself during the Continuwuity migration when all instances needed rebuilding. The AI can generate automation scripts quickly, and the cost of "premature automation" is low when the automation itself is AI-generated.

**8. OpenRouter-style model routing is essential.**  
The ability to switch models on the fly -- cheap models for routine work, expensive models for hard problems -- was a force multiplier. This is analogous to having both junior and senior engineers on call, except the "senior" (Claude Opus) is available in seconds with no scheduling overhead.

**9. The 52% concentration is expected.**  
Over half of all AI spend went to Claude Opus, used for roughly 6% of requests but handling 100% of the hard problems. This mirrors human team dynamics where the lead engineer consumes disproportionate project resources on the work that matters most.

**10. Token economics are unintuitive.**  
606 million tokens sounds enormous, but at $541 total, the effective rate is less than $0.001 per thousand tokens (blended across models). The cost-per-output-artifact is remarkably low. Monitor spend, but do not optimize prematurely -- the human time saved dwarfs the compute cost.

---
{::pagebreak /}
## 11. What This Means for Future Projects

Agent-Matrix is a single data point, not a universal template. But several patterns are likely to generalize:

**The viable team size for complex infrastructure projects is shrinking.** One domain expert with AI assistance delivered a scope that would traditionally require a small team. This has implications for project staffing, budgeting, and timeline estimation.

**Iterative architecture is more feasible.** When rebuilding is cheap, the cost of being wrong decreases. Projects can afford to start with a hypothesis, test it, and pivot -- rather than investing months in upfront design that may prove incorrect.

**The bottleneck moves from execution to judgment.** The constraint was never "can we write the code fast enough?" It was "are we building the right thing?" and "is this approach fundamentally sound?" These remain human questions -- and they require experienced humans.

**Mixed-model economics will matter.** Using expensive models for reasoning and cheap models for bulk work reduced costs without sacrificing quality. Future project budgets should account for model tiering the way current budgets account for senior vs. junior engineer rates.

**The apex model earns its price.** Claude Opus 4.6 cost more per token than any other model used in this project. It was also the only model that consistently produced correct solutions to hard problems on the first attempt. In a project where human time costs $150/hour, a model that saves even one hour of debugging per session pays for its entire token budget many times over. "Better call Claude" is not a joke -- it is a cost optimization strategy.

---
{::pagebreak /}
## 12. Conclusion

Agent-Matrix shipped a working sovereign AI agent federation in 30 days with one Principal-grade engineer and $541 in AI compute. Five agents, each with independent infrastructure, communicate over a federated protocol, recover automatically from failures, and deploy through zero-touch scripts. Every objective in the design document has been met.

The path was not linear -- it included dead ends, full rebuilds, and a major technology pivot at the three-week mark. But the final system works, and it works because the collaboration model works. An experienced architect who knows what to build, paired with an AI that can build it at machine speed, is a team that punches far above its weight class.

The AI did not replace the need for experienced technical judgment. It amplified it. And when the going got tough -- when the cheaper models went in circles and the configurations got tangled -- the answer was always the same: better call Claude.

---

*This retrospective was produced collaboratively by the Agent-Matrix project team -- one human, one AI -- using the same working model it describes.*
