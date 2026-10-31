# Performance Improvement Proposals — Agent-Matrix Pipeline

**Date:** 2026-10-31  
**Basis:** `2026-10-31-pipeline-latency-baseline.md` (Samples A–D, verified live)  
**Author:** agent0-1

Every proposal cites measured evidence from the baseline. Each includes an
expected gain, effort estimate, and the verification method — the benchmark
harness (`trace_report.py --synapse`) is reused for before/after proof.

---

## P1 — Fix the sync stall (highest reliability + latency impact)

**Evidence (Sample D2):** sync delivery stalls of **16–49 s** on 4 of 5 agents
during the loaded window. agent0-1's stall was **49.2 s ≈ exactly one 45 s
sync-timeout cycle + redelivery**, and its ping was released **11 ms after its
A0 turn ended**. Stalls hit agents whose A0 had been idle 45+ s, so it is not
own-A0 busyness. The 2026-03-07 `sync-freeze-investigation-report.md` root
cause (server accepts the /sync connection but never responds) is consistent:
the Rust bot's 45 s client-side timeout now *rescues* the hang — converting a
forever-freeze into a ≤45 s stall.

| # | Proposal | Expected gain | Effort | Verify |
| --- | --- | --- | --- | --- |
| P1a | Reduce Rust bot sync timeout wrapper 45 s → **10–15 s** (with small jitter) | worst-case stall 45 s → ~12 s (3–4× better) | one-line change + rebuild/deploy | rerun Sample D; stall p95 |
| P1b | Investigate **why conduwuite /sync hangs under clustered load**: capture g2s `load` + conduwuite logs during the next workload run (exact stall windows already in Sample D data); check conduwuite version parity (agent0-3 answered federation in 80 ms while 1/2/4/5 took 5–7 s — something differs) | root-cause fix; potentially eliminates stalls entirely | medium | stall count per test run → 0 |

---

## P2 — LLM latency (dominant end-to-end cost)

**Evidence:** idle LLM-path total 8943 ms of which **6973 ms (78%) is A0/LLM**.
Under 5-way concurrency A0 inflated **1.4×–5.2×** (9.5–36 s); agent0-3 is a
**3× outlier** (36 s vs siblings' 9.5–18 s); agent0-1's solo follow-up hit
**84.6 s**.

| # | Proposal | Expected gain | Effort | Verify |
| --- | --- | --- | --- | --- |
| P2a | **Per-agent model/provider audit** — run `templates/scripts/fleet-models.sh`; align agent0-3 (and any slow outlier) with the fast cohort | outlier 36 s → cohort norm ~10–18 s under load | low | rerun Sample D1; a0_latency per agent |
| P2b | **Streaming or interim replies** (typing indicator exists; add progress/streamed text) | perceived latency −70%+ on LLM path | medium | UX review; no pipe change expected |
| P2c | **Concurrency policy on g2s** — stagger or cap concurrent embedding-heavy A0 turns (embeddings are local CPU; 5 A0 cores share one host) | reduce the 1.4–5.2× inflation multiplier | medium | D1 a0_latency spread narrows |
| P2d | Prompt/context hygiene — trim per-turn system banners and keep contexts small | shave fixed per-turn token cost | low | a0_latency at idle |

---

## P3 — Federation transport tuning

**Evidence:** queue wait 592–1418 ms solo → **~500 ms flat under burst**
(batching confirmed). Federation txn HTTP completion: **80 ms (agent0-3) vs
5.16–6.9 s (agents 1/2/4/5)** — same VPN path. conduwuite reply flush:
151 ms (agent0-4) vs **7.7 s (agent0-1)** idle; under load all of it collapsed
to **32–303 ms** (warm connections).

| # | Proposal | Expected gain | Effort | Verify |
| --- | --- | --- | --- | --- |
| P3a | **Per-MHS connection audit** — TLS session reuse / keepalive / conduwuite version on the synapse→MHS path; bring 1/2/4/5 to agent0-3's profile | forward leg → ~500–600 ms consistently; burst totals 5.8–8.4 s → ~1–2 s | medium | rerun Sample C; flight per MHS |
| P3b | **conduwuite outbound flush config** — why did agent0-4 flush in 151 ms while agent0-1 held a reply 7.7 s? | reply leg 7.7 s → sub-second | low-medium | Sample C reply-at-gateway gap |
| P3c | Optional: lightweight **federation keepalive** so the first message after idle doesn't pay the cold-path tax (alternative: document the warm-up tax as known behavior) | solo first-message latency → warm levels | low | Sample B rerun after idle |

---

## P4 — Ops hygiene that protects the measurements

| # | Proposal | Why |
| --- | --- | --- |
| P4a | **NTP/chrony audit** (g2s + Contabo) | cross-host legs still uncertified; sub-100 ms claims need it |
| P4b | Fix `fed_send` matcher artifact in `trace_report.py` (stale txn in busy windows) | clean automated reports under load |
| P4c | **Fleet lifecycle repair**: rust-aware watchdog + `sync-fleet.sh` update (current script is stale, launches the Python bot; supervisord/watchdog disagree; duplicate bot procs on 2–5) | every future benchmark depends on a known fleet state |
| P4d | Add `@room:` as broadcast trigger | natural Matrix convention; avoids silent drops |
| P4e | Instrument the final hop (gateway→Element `/sync` delivery) | completes the true end-to-end figure |
| P4f | Adopt the status one-liner as `templates/scripts/fleet-status.sh` | standardized per-agent health snapshot for every test run |

---

## Suggested sequencing

1. **P1a** (minutes, huge stall improvement) → verify with Sample D rerun
2. **P2a** (fleet models audit; fixes the 36 s outlier)
3. **P3a/P3b** (the federation connection audits; biggest transport wins)
4. **P1b** (root-cause the residual stall)
5. P4 batch alongside; P2b/P2c as engineering time allows

Each step is independently verifiable with the existing harness:
capture → `trace_report.py --synapse --mhs` → diff against this baseline.
