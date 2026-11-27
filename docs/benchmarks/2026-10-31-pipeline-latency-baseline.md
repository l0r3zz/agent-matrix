# Pipeline Latency Baseline — Element ↔ Agent Round Trip

**Date:** 2026-10-31 (UTC)  
**Status:** Verified from live traffic  
**Author:** agent0-1  
**Purpose:** Baseline benchmarks for future performance tuning of the
Agent-Matrix message pipeline.

---

## 1. Environment Under Test

| Component | Identity / Version |
| --- | --- |
| Federation gateway | Synapse on K8s (`v-site-cluster`, Contabo), pod `matrix-synapse-8699bf6b8f-5zv6h`, container `matrix` |
| Agent homeserver | conduwuite `0.5.8+b9989f1` (`agent0-1-mhs.cybertribe.com`) |
| Agent bot | `matrix-bot-rust` instrumented build, md5 `29bab066a5945aa6e590c99d19def325` (trace.jsonl v1) |
| Agent | agent0-1 "Gandalf" (`@agent0-1:agent0-1-mhs.cybertribe.com`) |
| Client | Element 1.12.29 (Electron, desktop) as `@admin:v-site.net` |
| Room | `!OwVrRzvrSzqHCrZqVz:v-site.net` (Admins) |
| Agent Zero API | `http://localhost:80/api_message` (per-instance, loopback) |

Log clocks: Synapse logs in UTC; bot traces in epoch ms (host-independent).

---

## 2. Pipeline Stages and Data Sources

| # | Stage | Source |
| --- | --- | --- |
| 1 | `client PUT start (gateway)` | Synapse access log (`PUT /rooms/.../send/m.room.message`, start = completion − proc time) |
| 2 | `event created (origin_server_ts)` | event field, via bot trace |
| 3 | `federation transmit (gw→MHS)` | Synapse `matrixfederationclient` `{PUT-O-n}` completions (queue wait + flight duration) |
| 4 | `bot received (sync)` | bot trace.jsonl |
| 5 | `A0 request sent / response received` | bot trace.jsonl |
| 6 | `reply sent to room` | bot trace.jsonl |
| 7 | `reply at gateway (fed recv)` | Synapse `Received txn ... (PDUs>0)` lines; exact reply `event_id` confirmed via `handling received PDU` lines |

Not yet instrumented: final gateway → Element `/sync` delivery of the reply
(observed ~0.9 s after stage 7 in sample A raw logs — not included in totals).

Correlation: bot stages by Matrix `event_id`; gateway stages by room+time
window (exact at lab traffic, ambiguous under bursts) except stage 7, which
is exact by reply `event_id`.

---

## 3. Verified Samples

### Sample A — LLM path (2026-10-31 00:39:24 UTC)

User message: `Gandalf: ping.` — trailing period misses the exact-match
built-in, so it exercised the full Agent Zero/LLM path.
Event `$mmDzz0MbX3w7RKl_-8IRb5pumdtYkZTi2zFgB3OzqIE`

```
  client PUT start (gateway)    : 17:39:24.335   req=PUT-235958
  event created (origin_server_ts): 17:39:24.566  +   231 ms
  federation transmit (gw->MHS) : 17:39:25.984  +  1418 ms  synapse fed queue [flight 230ms]
  bot received (sync)           : 17:39:26.117  +   133 ms
  A0 request sent               : 17:39:26.120  +     3 ms
  A0 response received          : 17:39:33.093  +  6973 ms  [reply_len=53]
  reply sent to room            : 17:39:33.097  +     4 ms  [1 chunk]
  reply at gateway (fed recv)   : 17:39:33.278  +   181 ms  [reply_event=$i52wE2DB0oMRgWE-kmzZ8aFMvqELA4RfocUJGNO8Kxk]
  TOTAL                         :   8943 ms
```

### Sample B — built-in path (2026-10-31 00:51:43 UTC)

User message: `@gandalf: ping` (exact `ping`) — built-in response, no LLM.
Event `$tBNBRzUXcZSaaKEkMn5L8EgvSR8pNsocYGccgNIsbvE`

```
  client PUT start (gateway)    : 17:51:43.830   req=PUT-236169
  event created (origin_server_ts): 17:51:43.889  +    59 ms
  federation transmit (gw->MHS) : 17:51:44.481  +   592 ms  synapse fed queue [flight 130ms]
  bot received (sync)           : 17:51:44.554  +    73 ms
  reply sent to room            : 17:51:44.559  +     5 ms  [built-in, no LLM]
  reply at gateway (fed recv)   : 17:51:44.735  +   176 ms  [reply_event=$6bQswhdaTM3YBC9nvzn-UXh1TMts5n1WSttmpSzMWF0]
  TOTAL                         :    905 ms
```

### Sample C — 5-way broadcast burst (2026-10-31 01:03:49 UTC)

User message: `@all-agents: ping` in Fleet HQ Clean
(`!gahcrWFWAUJQPPkuQy:v-site.net`, 6 members: agents 1–5 + Admin). All five
agents fired the built-in PONG. Event
`$ftdXYHy9X0vwnrfCqk52ZoYWNDskQcIlLqrDQQaUZx0`.
Rendered per agent with `--mhs agent0-N-mhs.cybertribe.com` (burst-safe
federation matching; naive time-window matching cross-correlates between
agents under bursts).

Gaps relative to event creation (01:03:49.180 UTC); "txn flight" = full HTTP
completion of the synapse→MHS PUT.

| Agent | fed txn start | txn flight | bot received | bot reply sent | reply at gateway | TOTAL |
| --- | --- | --- | --- | --- | --- | --- |
| agent0-4 | +505 ms | 5160 ms | +5177 ms | +5 ms | +151 ms | **5853 ms** |
| agent0-3 | +497 ms | **80 ms** | +84 ms | +12 ms | **+6759 ms** | **7367 ms** |
| agent0-5 | +496 ms | 6900 ms | +5184 ms | +7 ms | +2438 ms | **8140 ms** |
| agent0-1 | +494 ms | 5420 ms | +90 ms (mid-txn!) | +3 ms | **+7728 ms** | **8330 ms** |
| agent0-2 | +500 ms | 6900 ms | +5169 ms | +5 ms | +2693 ms | **8382 ms** |

Reply event IDs (exact, nearest-PDU match): agent0-1 `$0MgFQNgYmm_sqw8ZLE-L7bu`,
agent0-2 `$J5R-ZVAcnRFAQkY1EqljXmC`, agent0-3 `$nMznfrNQsLWNnRVbYAm8G8y`,
agent0-4 `$J9Z5StvavS76vphR_uSqZCe`, agent0-5 `$6bYgB_R95Phyx2wceykzSnP`.

**Burst findings:**

1. **Queue wait collapsed under batching** — all five outbound txns started
   within 11 ms of each other, ~500 ms after event creation (vs 592–1418 ms
   solo). Confirmed: the Synapse transmit loop batches.
2. **Federation txn HTTP completion is slow on 4 of 5 homeservers** — 5.16–6.9 s
   for the PUT to return, vs 80 ms on agent0-3. Not event processing:
   agent0-1's bot saw the event +90 ms *into* its 5.4 s txn. Points at
   connection-level cost (TLS keepalive / OpenVPN path) per MHS.
3. **Event visibility vs txn completion diverges per instance** — agent0-1/3
   bots received via sync mid-txn (+84–90 ms); agents 2/4/5 only at
   ~completion (+5.2 s).
4. **conduwuite reply flush is the hidden burst whale** — 151 ms (agent0-4) to
   7.7 s (agent0-1) for the reply txn to reach the gateway. Per-destination
   outbound scheduling on the conduwuite side.
5. Bot processing stayed at noise floor (3–12 ms) across all five.

### Sample D — LLM workload + probes (2026-10-31 01:22–01:24 UTC)

User applied LLM workload to the fleet, then probed mid-flight:
18:22:16 PDT `@all-agents` LLM-path broadcast; 18:22:57 extra LLM task for
agent0-2; 18:23:06 LLM task for agent0-1; 18:23:42 `@all-agents: ping`
built-in probe. Room: Fleet HQ Clean. Rendered with `--mhs` per agent.

**D1. LLM broadcast under 5-way concurrency** (all A0 cores started within
2 ms of each other; idle reference a0=6973 ms, TOTAL=8943 ms):

| Agent | A0 latency | TOTAL | vs idle A0 |
| --- | --- | --- | --- |
| agent0-2 | 9462 ms | 10915 ms | +36% |
| agent0-1 | 12155 ms | 13476 ms | +74% |
| agent0-4 | 17425 ms | 18847 ms | +150% |
| agent0-5 | 18011 ms | 19513 ms | +158% |
| agent0-3 | 36066 ms | 37573 ms | **+417%** |

agent0-1's separate follow-up LLM task ($A_PYtx...) took **84621 ms** A0 time
(TOTAL 85293 ms) — extreme contention/queueing while siblings were mid-turn.

**D2. Built-in ping mid-workload** (18:23:42; idle baseline TOTAL=905 ms):

| Agent | sync delivery delay | TOTAL | A0 state at ping time |
| --- | --- | --- | --- |
| agent0-2 | +474 ms | **505 ms** | idle (task ended 18:23:25) — beats idle baseline; warm connections |
| agent0-5 | +15920 ms | 15951 ms | A0 idle since 18:22:35 |
| agent0-3 | +15908 ms | 15936 ms | A0 idle since 18:22:53 |
| agent0-4 | +16149 ms | 16185 ms | A0 idle since 18:22:35 |
| agent0-1 | +49209 ms | 49204 ms | A0 busy; ping delivered 11 ms after its A0 turn ended |

**Workload findings:**

1. **Concurrent LLM inflates A0 latency 1.4×–5.2×** (9.5–36 s vs 7.0 s idle);
   agent0-3 is a 3× outlier vs siblings — check its model/provider config.
2. **Sync delivery stalls of 16–49 s on 4 of 5 agents** during the loaded
   window — including agents whose A0 had been idle 45+ s (3/4/5), so it is
   not own-A0 busyness. Pattern matches the known sync-freeze issue (see
   `multi-instance-deploy/sync-freeze-investigation-report.md`); agent0-1's
   49.2 s ≈ one 45 s sync-timeout cycle + redelivery.
3. **Warm-connection effect**: agent0-2's 505 ms total beat the 905 ms idle
   baseline; reply federation under load collapsed to 32–303 ms (vs 151 ms–7.7 s
   idle burst). Traffic keeps federation paths hot.
4. Bot processing stayed at noise floor (2–12 ms) everywhere.
5. **Tooling caveat**: negative fed-queue values on some loaded-window rows are
   a `fed_send` matcher artifact (stale txn matched in multi-txn windows);
   bot-side stages are unaffected. Fix queued.

---

## 4. Baseline Metrics (provisional — n=2, one sample per path)

| Stage | Sample A (LLM) | Sample B (built-in) | Notes |
| --- | --- | --- | --- |
| Element → gateway (transit+proc) | 231 ms | 59 ms | gateway-side clock |
| Synapse federation queue wait | 1418 ms | 592 ms | **dominant variable transport cost** |
| Fed flight + conduwuite + sync delivery | 133 ms | 73 ms | flight itself 130–230 ms (overlaps) |
| Bot processing (prefix check etc.) | 3 ms | ~0 ms | |
| Agent Zero / LLM | 6973 ms | — | n=1; model/prompt dependent |
| Send path (conduwuite accept) | 4 ms | 5 ms | |
| Reply federation (conduwuite→gateway) | 181 ms | 176 ms | stable across samples |
| **TOTAL (Element PUT → reply at gateway)** | **8943 ms** | **905 ms** | excludes final gateway→Element sync |

Derived figures:

- **Pure transport floor:** ≈ **0.9 s** round trip (sample B).
- **LLM overhead:** ≈ **8.0 s** above floor for this model/prompt (sample A − B).
- **Federation queue variance:** 592–1418 ms (2.4× spread) — Synapse's
  `federation_transaction_transmission_loop` wakes on a schedule and batches;
  a message either catches the loop or waits for it.
- **Stable legs** (<2× variance): fed flight 130–230 ms, conduwuite+sync
  73–133 ms, reply federation 176–181 ms, send path 4–5 ms.

---

## 5. Caveats

1. **n=2 solo + one 5-way burst (Sample C).** Solo numbers remain provisional;
   the burst confirmed batching collapses queue wait but exposed slow per-MHS
   txn completion (5–7 s) and conduwuite reply-flush scheduling (0.15–7.7 s)
   as the dominant burst costs.
2. **Clock skew** between gateway and g2s hosts is unverified (`chronyc`
   not checked). Within-host deltas are exact; cross-host deltas absorb skew.
   Internal consistency (no negative gaps) suggests skew < ~100 ms.
3. **Final hop excluded:** gateway→Element `/sync` delivery is not in TOTALs
   (raw logs indicate ~0.9 s for sample A).
4. **Correlation by room+time window** for gateway stages 1–3; exact event_id
   only for stage 7. Reliable at current lab traffic levels.
5. **LLM time** is a black box from the bot side (includes A0 orchestration +
   model latency); model/provider changes will dominate any tuning here.

---

## 6. Tuning Opportunities (ranked by expected impact)

1. **LLM response time (~7 s, 78% of LLM-path total).** Model/provider
   selection, prompt size, streaming replies. Biggest lever by far.
2. **Synapse federation queue wait (0.6–1.4 s).** Investigate federation
   sender scheduling/batching behavior; consider whether conduwuite-side or
   Synapse-side knobs reduce the wake-up interval. Second-largest and the
   dominant *variable* transport cost.
3. **Per-MHS federation txn slowness + conduwuite reply flush (burst,
   5–7.7 s each).** Investigate connection reuse/TLS keepalive on the
   synapse→MHS path (4 of 5 PUTs take 5–7 s; agent0-3 answers in 80 ms) and
   conduwuite's outbound per-destination flush scheduling (agent0-4 flushed in
   151 ms; agent0-1 held a reply 7.7 s).
4. **Streaming or interim replies** to mask LLM latency in UX (typing
   notifications already in place).
5. **NTP discipline audit** on all hosts before trusting sub-100 ms
   cross-host legs (`chronyc tracking` on g2s + Contabo node).
6. **Instrument the final hop** (gateway→Element sync delivery) to complete
   the true end-to-end figure.

---

## 7. Reproduction Recipe

Prerequisites: instrumented `matrix-bot-rust` deployed (binary md5
`29bab066...`), kubectl access to `v-site-cluster` from g2s.

```bash
# 1. Generate traffic: message an agent from Element (e.g. "gandalf: ping")

# 2. Capture gateway side (from agent0-1)
cd /a0/usr/projects/agent-matrix/multi-instance-deploy/templates/matrix-bot
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes l0r3zz@172.23.100.121 \
  'kubectl -n matrix logs deploy/matrix-synapse -c matrix --since=25m' \
  | python3 synapse_trace_extract.py > /tmp/syn.jsonl

# 3. Capture bot side
scp -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes \
  l0r3zz@172.23.100.121:/opt/agent-zero/agent0-1/usr/workdir/matrix-bot/trace.jsonl \
  /tmp/bot.jsonl

# 4. Render merged timeline + aggregate stats
python3 trace_report.py /tmp/bot.jsonl --synapse /tmp/syn.jsonl
python3 trace_report.py /tmp/bot.jsonl --synapse /tmp/syn.jsonl --stats
```

Tooling sources: `templates/matrix-bot/{trace_report.py, synapse_trace_extract.py}`;
bot instrumentation in `templates/matrix-bot/rust/src/main.rs`
(`trace_event`, stages `bot_received`, `a0_request_start`, `a0_request_done`,
`reply_sent`). Disable tracing with `TRACE_ENABLED=0` in the bot env.

---

## 8. Raw Data

| File | Content |
| --- | --- |
| `data/2026-10-31/bot-trace-agent0-1.jsonl` | Bot-side trace records (6 lines, both samples) |
| `data/2026-10-31/synapse-trace.jsonl` | Gateway-side extracted records (65 lines) |
| `data/2026-10-31/burst-fleet-hq-clean/bot-trace-agent0-{1..5}.jsonl` | Sample C burst bot traces, all five agents |
| `data/2026-10-31/burst-fleet-hq-clean/synapse-trace-burst.jsonl` | Sample C burst gateway records (67 lines) |

### Trace record schemas

Bot (`trace.jsonl`): `{"ts": epoch_ms, "event_id": "$...", "stage": ...}` with
stage-specific fields — `bot_received`: `room_id`, `sender`,
`origin_server_ts`, `fed_sync_latency_ms`; `a0_request_done`:
`a0_latency_ms`, `reply_len`; `reply_sent`: `builtin`, `chunks`,
`total_rtt_ms`.

Gateway (`synapse_trace_extract.py` output): `synapse_client_send`
(`room`, `user`, `proc_ms`, `start_ts`); `synapse_fed_send` (`dest`, `txn`,
`dur_ms`, `start_ts`); `synapse_fed_recv` (`origin`, `txn`, `pdus`);
`synapse_pdu` (`room`, `pdu_event_id`, `pdu_type`).
