# Sync Loop Freeze Investigation — Research Report
## Date: 2026-03-07
## Author: Agent0-1 (offline research while Geoff is away)

---

## Executive Summary

After exhaustive comparison, all visible components (bot code, nio version, aiohttp
version, Dendrite version, startup scripts) are **identical** across agents. However,
research uncovered two significant findings:

1. **Missing client-side HTTP timeout** — the probable root cause of the sync freeze
2. **Missing template files** — startup-patch.sh and startup-services.sh are NOT in the golden templates

---

## Finding 1: Missing Client-Side HTTP Timeout (PROBABLE ROOT CAUSE)

### The Problem
In `matrix_bot.py`, the sync call looks like this:

```python
sync_response = await client.sync(
    timeout=SYNC_TIMEOUT_MS,   # 30000 = 30 seconds
    full_state=False,
    set_presence="online",
)
```

The `timeout=30000` parameter is a **server-side** timeout — it tells Dendrite:
"If there are no new events, wait up to 30 seconds before returning an empty response."

But there is **NO client-side HTTP timeout** configured. The nio `AsyncClient` uses
aiohttp under the hood, and by default aiohttp will wait **indefinitely** for a response.

If Dendrite accepts the HTTP connection but never sends a response (due to a bug,
connection state issue, or internal error), the bot will hang **forever**.

### Why Agent0-1 Works
Agent0-1's bot has been running since container boot. Its aiohttp session has a
healthy, established TCP connection to Dendrite. The long-poll works because the
connection was established clean and has been maintained continuously.

Agent0-2/3 establish fresh connections on each restart. If Dendrite has any issue
with fresh sync sessions (e.g., connection reuse bug, state initialization delay),
the bot hangs because there's no timeout to recover.

### Proposed Fix
Add `asyncio.wait_for()` around the sync call:

```python
# Main sync loop
while not stop.is_set():
    try:
        sync_response = await asyncio.wait_for(
            client.sync(
                timeout=SYNC_TIMEOUT_MS,
                full_state=False,
                set_presence="online",
            ),
            timeout=(SYNC_TIMEOUT_MS / 1000) + 30,  # server timeout + 30s grace
        )
        if isinstance(sync_response, SyncError):
            log.warning(f"Sync error: {sync_response.message} — retrying in 5s")
            await asyncio.sleep(5)
    except asyncio.TimeoutError:
        log.warning("Sync timed out (client-side) — reconnecting...")
        continue
    except asyncio.CancelledError:
        break
    except Exception as e:
        log.exception(f"Sync loop error: {e} — retrying in 10s")
        await asyncio.sleep(10)
```

### Verification Test
Before patching, the **definitive test** is to restart agent0-1's bot process and
see if it ALSO freezes. If yes, this confirms the issue is systemic and the fix
is needed. If no, there's something specific to agent0-2/3's Dendrite state.

---

## Finding 2: Missing Template Files

### The Problem
The following critical files are **NOT in the golden templates** at
`multi-instance-deploy/templates/`:

1. `startup-services.sh` — the boot orchestrator
2. `startup-patch.sh` — the API token sync + run_ui.py patch

This means `create-instance.sh` deploys agents **without** these scripts. They
were manually created and copied to each instance individually.

### Impact
- Any new instance (agent0-4) deployed via `create-instance.sh` will NOT have
  automatic MCP server startup, API readiness checks, dependency installation,
  or bot auto-start.
- The token synchronization (Patch 2) won't run automatically.

### Recommendation
Add both scripts to `multi-instance-deploy/templates/` and update
`create-instance.sh` to copy them into the instance's `usr/workdir/` directory.

---

## Finding 3: Patch Drift Between Instances

### Agent0-1 startup-patch.sh (v1 — original, 2 patches)
- **Patch 1**: Modifies `/a0/run_ui.py` to bypass API auth when `mcp_server_token`
  is empty (loopback access). Currently NOT active — the container was rebuilt and
  the patch was lost.
- **Patch 2**: Auto-computes A0_API_KEY from runtime_id:username:password hash
  and updates the bot .env file.

### Agent0-2/3 startup-patch.sh (v2 — derived from agent0-1)
- Only contains a version of **Patch 2** (token sync)
- Based on log output: "Computing API token...", "Updated A0_API_KEY..."
- Patch 1 was NOT included

### Agent0-1 startup-services.sh (v1 — original, 4 phases)
1. Start MCP server
2. Wait for Agent Zero API
3. Install pip dependencies
4. Start matrix-bot

### Agent0-2/3 startup-services.sh (v2 — 5 phases, adds Phase 2.5)
1. Start MCP server
2. Wait for Agent Zero API
**2.5. Run startup-patch.sh (token sync)**
3. Install pip dependencies
4. Start matrix-bot

### Recommended Unified Version
Merge v1 and v2 into a single canonical version for the templates. The v2
addition (Phase 2.5) is useful and should be kept.

---

## Finding 4: Agent0-1 .env Has SMTP Config

Agent0-1's matrix-bot `.env` includes Gmail SMTP settings that are not in the
template. This doesn't affect sync behavior but should be noted for completeness.

---

## Recommended Next Steps (Priority Order)

1. **Add `asyncio.wait_for()` timeout to the sync loop** — highest priority fix
2. **Test by restarting agent0-1's bot** — confirms whether issue is systemic
3. **Add startup-services.sh and startup-patch.sh to golden templates**
4. **Deploy agent0-4 from updated templates** — validates full pipeline
5. **Merge startup scripts into canonical v3** — single unified version

---

## Appendix: File Comparison Summary

| File | agent0-1 | agent0-2 | agent0-3 | Template |
|---|---|---|---|---|
| matrix_bot.py | 8fbd94cb | 8fbd94cb | 8fbd94cb | 8fbd94cb |
| requirements.txt | identical | identical | identical | identical |
| startup-services.sh | v1 (2113B) | v2 (2378B) | v2 (2378B) | ❌ MISSING |
| startup-patch.sh | Patch 1+2 | Patch 2 only | Patch 2 only | ❌ MISSING |
| matrix-nio | 0.25.2 | 0.25.2 | 0.25.2 | — |
| aiohttp | 3.13.3 | 3.13.3 | 3.13.3 | — |
| Dendrite | v0.15.2 | v0.15.2 | v0.15.2 | — |
| .env SMTP | ✅ Gmail | ❌ | ❌ | ❌ |
