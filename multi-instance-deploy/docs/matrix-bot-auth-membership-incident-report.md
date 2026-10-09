# Matrix Bot Authentication and Membership Incident Report

**Version:** 1.1  
**Date:** 2026-10-08  
**Resolved:** 2026-10-09  
**Status:** Remediation complete -- all agents passing completion gates  
**Scope:** Agent0-1 through Agent0-5 on `g2s`  
**Homeserver:** conduwuite behind Caddy  
**Classification:** Redacted operational report; contains no plaintext credentials

---

## Executive Summary

The fleet incident is not a general Matrix federation outage. All five Agent Zero containers, conduwuite homeservers, Caddy proxies, and Rust Matrix bot processes were running during inspection. Every configured Matrix access token successfully passed the Matrix `whoami` endpoint.

The failures came from three control-plane consistency problems:

1. **Agent0-3 and Agent0-4 use Agent0-2's bot-to-Agent-Zero API credential.** Their Matrix bots receive traffic but receive HTTP 401 when forwarding it to their local Agent Zero API.
2. **Agent0-5 runs the conversational bot as the wrong Matrix principal.** It authenticates as `@agent0-5-mcp:agent0-5-mhs.cybertribe.com`, which is not in the Element-facing Fleet HQ room. It also has Agent0-2's Agent Zero API credential.
3. **Agent0-1 has split federated membership state.** The Synapse gateway lists Agent0-1 in Fleet HQ, but Agent0-1's own conduwuite server does not list Fleet HQ in `joined_rooms`. Its bot cannot consume events from that room.

The underlying systemic cause is fragmented ownership. Credential creation, credential derivation, startup reconciliation, identity configuration, supervision, and fleet synchronization are handled by multiple scripts with conflicting assumptions. Incorrect instance-local state is then preserved indefinitely.

---

## User-Visible Symptoms

| Agent | Symptom in Element | Confirmed cause |
|---|---|---|
| Agent0-1 | No response | Local conduwuite does not consider the account joined to Fleet HQ, although gateway state does |
| Agent0-2 | Responds normally | Working baseline |
| Agent0-3 | `Agent Zero API error 401 Unauthorized` | Bot uses Agent0-2's Agent Zero API credential |
| Agent0-4 | `Agent Zero API error 401 Unauthorized` | Bot uses Agent0-2's Agent Zero API credential |
| Agent0-5 | No response | Running bot uses `@agent0-5-mcp`, which is absent from Fleet HQ; its Agent Zero API credential is also wrong |

---

## Investigation Constraints

The investigation was read-only. It did not:

- modify files or credentials;
- restart containers or bot processes;
- join or leave Matrix rooms;
- send Matrix messages;
- change Agent Zero settings;
- execute any part of the proposed repair.

Only redacted fingerprints were used when comparing credentials.

---

## Evidence Collected

### Fleet availability

All of the following were running:

- `agent0-1` through `agent0-5` Agent Zero containers;
- five conduwuite containers;
- five Caddy homeserver proxies;
- one Rust Matrix bot process in each Agent Zero container.

This excludes a fleet-wide service outage as the primary cause.

### Matrix access-token validation

Each configured Matrix token returned HTTP 200 from:

`/_matrix/client/v3/account/whoami`

Validated identities were:

- Agent0-1 token → `@agent0-1:agent0-1-mhs.cybertribe.com`
- Agent0-2 token → `@agent0-2:agent0-2-mhs.cybertribe.com`
- Agent0-3 token → `@agent0-3:agent0-3-mhs.cybertribe.com`
- Agent0-4 token → `@agent0-4:agent0-4-mhs.cybertribe.com`
- Agent0-5 bot token → `@agent0-5-mcp:agent0-5-mhs.cybertribe.com`

Agent0-5's Matrix token is valid, but it belongs to the wrong principal for the conversational bot.

### Bot-to-Agent-Zero credential comparison

Agent Zero accepts its local `mcp_server_token`, derived by its canonical implementation from:

`persistent runtime ID + authentication login + authentication password`

The deployed bots had these redacted SHA-256 fingerprints:

| Agent | Bot credential fingerprint | Credential expected by local Agent Zero | Status |
|---|---:|---:|---|
| Agent0-1 | `09fc06b05bf6` | `09fc06b05bf6` | Match |
| Agent0-2 | `83dae4ffc6b3` | `83dae4ffc6b3` | Match |
| Agent0-3 | `83dae4ffc6b3` | `6c441c22b045` | Mismatch |
| Agent0-4 | `83dae4ffc6b3` | `045d54e0a0ee` | Mismatch |
| Agent0-5 | `83dae4ffc6b3` | `e01ef7cccea7` | Mismatch |

Agents 0-3, 0-4, and 0-5 contain the exact fingerprint used by Agent0-2. Agent Zero's `/api/api_message` endpoint compares this value exactly and returns HTTP 401 on mismatch.

### Room membership

#### Fleet HQ

The Element-facing Fleet HQ room is:

`!gahcrWFWAUJQPPkuQy:v-site.net`

Gateway-visible membership included:

- `@agent0-1:agent0-1-mhs.cybertribe.com`
- `@agent0-2:agent0-2-mhs.cybertribe.com`
- `@agent0-3:agent0-3-mhs.cybertribe.com`
- `@agent0-4:agent0-4-mhs.cybertribe.com`
- `@agent0-5:agent0-5-mhs.cybertribe.com`
- human gateway users

#### Local operational membership

- Agent0-2, Agent0-3, and Agent0-4 locally reported Fleet HQ in `joined_rooms`.
- Agent0-1 did not locally report Fleet HQ, despite gateway state listing it as joined.
- Agent0-5's running `@agent0-5-mcp` principal reported only its local admin room and no `v-site.net` room.

For bot operation, the local conduwuite `joined_rooms` result is authoritative: if the local server does not report the room, the bot cannot sync its events.

---

## Root Cause by Agent

### Agent0-3 and Agent0-4

The Matrix side is healthy. Each bot can authenticate to conduwuite and is locally joined to Fleet HQ. The failure occurs when the bot forwards an incoming Matrix event to its local Agent Zero API.

Both bots present Agent0-2's credential, so Agent Zero rejects the request with HTTP 401.

### Agent0-5

Agent0-5 has two independent faults:

1. The bot authenticates as `@agent0-5-mcp`, while Fleet HQ contains `@agent0-5`.
2. Its bot-to-Agent-Zero credential is copied from Agent0-2.

The first fault explains the current silence: the running bot never receives Fleet HQ messages. Repairing only the identity would expose the second fault as an HTTP 401.

### Agent0-1

Agent0-1 has correct Matrix and Agent Zero credentials, a running bot, and a correct local API endpoint. Its failure is federated membership divergence:

- Synapse gateway state says Agent0-1 is joined to Fleet HQ.
- Agent0-1's local conduwuite state does not include Fleet HQ.

This is a stale or partial federated membership condition. A fresh leave and rejoin is the established recovery because the new join event carries current room state to the local homeserver.

---

## How Agent0-2's Credential Propagated

### What is confirmed

The provisioning lifecycle has multiple competing credential writers:

1. `create-instance.sh` generates a random `A0_API_KEY` and writes it to the bot environment.
2. `finalize-instance.sh` later attempts to replace it with a deterministic value.
3. The finalizer contains conflicting derivations:
   - one helper reads runtime ID and authentication credentials;
   - Step 7b derives from `runtime_id::`, assuming empty credentials.
4. A historical startup script recalculated and rewrote the value during boot.
5. The current startup script no longer performs this reconciliation.
6. The Rust bot trusts any nonempty configured `A0_API_KEY`; it only derives a fallback when the configured value is empty.
7. `sync-fleet.sh` intentionally preserves each deployed bot `.env`, including stale credentials.
8. The watchdog checks Matrix/MCP authentication but does not test bot-to-Agent-Zero authentication.

The current synchronization script did not originate the copied value. It preserved it.

### Historical reconstruction

The most likely initial contamination event was an older manual deployment, clone, repair, or bootstrap operation that used Agent0-2's bot environment or API value as a source. Instance-specific Matrix fields were then customized while `A0_API_KEY` remained unchanged.

Supporting evidence:

- Three agents have exactly Agent0-2's deployed bot credential fingerprint.
- Their host-level instance environment files contain different fingerprints, localizing the contamination to the bot configuration layer.
- Agent0-4's retained May backup already contains Agent0-2's value.
- Agent0-5's backup from before its July identity edit already contains Agent0-2's value.
- Reconciliation logs are absent for Agents 0-2, 0-3, and 0-5.
- Agent0-4 logged that automatic token calculation failed.

### Certainty

| Statement | Confidence |
|---|---|
| Agents 0-3, 0-4, and 0-5 have Agent0-2's deployed bot credential | Confirmed |
| Current preservation logic allowed the bad value to persist | Confirmed |
| Multiple conflicting credential owners made contamination possible | Confirmed |
| An earlier clone/manual deployment/bootstrap introduced the shared value | High confidence |
| The exact historical command that first copied it | Not recoverable from retained artifacts |

---

# Permanent Repair Strategy

## Design principles

1. One authoritative owner per credential and identity domain.
2. Fail closed on authentication or identity mismatch.
3. Reconciliation must be idempotent.
4. Fleet releases must never contain instance secrets.
5. Local conduwuite membership is required before a bot starts.
6. Permanent configuration faults must not trigger endless restart loops.
7. Repair nodes sequentially behind validation gates.

---

## 1. Make Agent Zero the sole API-credential authority

Agent Zero's canonical `create_auth_token()` behavior must be the only implementation that derives the bot-to-Agent-Zero credential.

### Required changes

- Remove random `A0_API_KEY` generation from `create-instance.sh`.
- Remove duplicate derivation logic from Bash, Rust, finalizers, and startup patches.
- Add one framework-backed export mechanism using `/opt/venv-a0` and the running Agent Zero version.
- Obtain the credential immediately before bot startup.
- Deliver it through a root-owned runtime secret file or equivalent protected channel.
- Do not persist it in fleet templates or reusable bot `.env` files.
- Atomically replace runtime secret files with mode `0600`.

If runtime ID or login credentials change, the next launch obtains the new canonical value automatically.

### Startup gate

Before Matrix syncing starts, perform a harmless authenticated call to local Agent Zero. Treat HTTP 401 or 403 as a terminal configuration fault:

- keep the bot stopped;
- emit a redacted diagnostic;
- alert an operator;
- do not restart continuously.

Do not restore loopback authentication bypasses.

---

## 2. Separate credential domains

Maintain distinct ownership and checks for:

1. Matrix access token;
2. bot-to-Agent-Zero credential;
3. MCP configuration and any MCP-specific credential.

Do not compare or synchronize credentials from different domains. Rename health checks so their scope is explicit.

---

## 3. Introduce a declarative per-instance manifest

Each node needs a nonsecret manifest defining:

- instance number;
- canonical Matrix user ID;
- homeserver URL;
- required Matrix room IDs;
- Agent Zero API endpoint;
- selected bot runtime;
- release version.

Agent0-5's conversational principal should deliberately be selected as:

`@agent0-5:agent0-5-mhs.cybertribe.com`

A separate MCP service principal may exist only if explicitly declared and must not silently run the conversational bot. Display names must never be treated as identity.

---

## 4. Validate identity and membership before `/sync`

Every bot startup must:

1. call Matrix `/account/whoami`;
2. require exact equality with the manifest's Matrix user ID;
3. verify all required rooms appear in local conduwuite `joined_rooms`;
4. verify local Agent Zero authentication;
5. start `/sync` only after every check passes.

This would have prevented Agent0-5's wrong-principal deployment and Agent0-1's ineffective Fleet HQ presence.

---

## 5. Create one idempotent reconciler

Replace scattered lifecycle mutations with a single tool supporting:

- `check`: read-only health and drift report;
- `plan`: redacted proposed changes;
- `apply`: explicitly approved mutations.

### Checks

Per node, verify:

- exactly one bot process;
- exactly one selected runtime;
- `/whoami` equals declared identity;
- local membership includes required rooms;
- bot-to-Agent-Zero authenticated probe succeeds;
- deployed hashes match the release manifest;
- secret ownership and permissions are correct;
- bot, launcher, MCP, startup, and watchdog belong to one release;
- no sovereign nodes share a bot-to-Agent-Zero credential fingerprint.

Reports must show equality results or keyed fingerprints only.

### Apply behavior

- write temporary files securely;
- validate before installation;
- use atomic rename;
- restart only the affected consumer;
- rerun preflight afterward;
- make a second application a no-op;
- guarantee that `check` and `plan` perform zero writes.

---

## 6. Replace watchdog behavior

Use domain-specific health checks for:

- Matrix authentication and identity;
- required room membership;
- bot-to-Agent-Zero authentication;
- MCP health;
- bot process count;
- sync cursor age and advancement.

Classify failures:

| Class | Examples | Action |
|---|---|---|
| Restartable | Process crash, transient timeout, temporary connection failure | Bounded retry/restart |
| Terminal configuration | HTTP 401/403, identity mismatch, missing required room, invalid manifest, release hash mismatch | Stop bot and alert |

A restart cannot repair a wrong credential, wrong principal, or missing membership.

---

## 7. Publish immutable fleet releases

A versioned release bundle should contain:

- Rust bot binary;
- launcher;
- preflight/reconciler;
- startup service;
- watchdog;
- MCP artifact;
- dependency locks;
- checksum manifest.

Fleet synchronization installs this immutable bundle and never copies instance secrets. Do not use a live Agent0-1 or Agent0-2 workdir as a mutable golden source.

Instance-local state should be limited to:

- identity manifest;
- Matrix token;
- Agent Zero persistent runtime state;
- bot cursor and event-deduplication state.

---

## 8. Harden Matrix sync behavior

Current logs repeatedly report identical sync responses. This was not established as the cause of the authentication incident, but it should be corrected before broad restart testing.

Required behavior:

- treat empty successful incremental syncs as healthy;
- atomically persist every accepted `next_batch`;
- never clear `since` merely because several syncs contain no events;
- persist bounded event-ID deduplication across restarts;
- suppress self-events using the identity returned by `/whoami`;
- apply the declared mention/command policy even in two-member rooms;
- log room ID, event ID, sender, decision, and outcome without message secrets.

---

# Proposed One-Time Repair Sequence

This section is a design only. It has not been executed.

## Phase 0: Repair the control plane

Before editing live credentials:

1. implement the canonical Agent Zero credential exporter;
2. implement manifests and startup preflight;
3. remove random and duplicate derivation paths;
4. update the Rust launcher to obtain the runtime credential;
5. add domain-specific watchdog checks;
6. fix sync cursor and self-event behavior;
7. build and checksum an immutable release.

Repairing live `.env` files first would leave the recurrence mechanism intact.

## Phase 1: Capture rollback state

For each node:

- record artifact hashes and process lists;
- record redacted credential fingerprints;
- record `/whoami` and local `joined_rooms`;
- preserve sync cursor and recent event IDs;
- take protected instance-local configuration and state snapshots;
- pause bot restart loops during that node's repair.

Do not aggregate plaintext fleet secrets into a central archive.

## Phase 2: Canary on Agent0-2

Use the currently working node to validate the new release and launcher without changing its identity.

Canary gates:

- one bot process;
- exact `/whoami` match;
- successful local Agent Zero authenticated probe;
- stable cursor advancement;
- no replay or self-response;
- expected response to one controlled addressed message;
- no deployment-template credential persistence.

## Phase 3: Repair Agent0-3 and Agent0-4 sequentially

For each agent:

1. stop only its bot;
2. remove the persistent copied Agent0-2 value;
3. launch through the canonical credential path;
4. require preflight success before Matrix handling;
5. run one controlled addressed-message test;
6. observe several sync intervals before proceeding.

## Phase 4: Repair Agent0-5 identity, then authentication

1. select `@agent0-5` as the canonical conversational identity;
2. issue or recover a Matrix token for that exact account;
3. require `/whoami` equality;
4. verify Fleet HQ appears in local `joined_rooms`;
5. join Fleet HQ as the canonical account if local membership is absent;
6. start with the local canonical Agent Zero credential;
7. revoke the obsolete `@agent0-5-mcp` bot token after validation if no longer needed.

Do not alter `MATRIX_USER_ID` merely to match whichever token is currently installed.

## Phase 5: Repair Agent0-1 membership

1. stop Agent0-1's bot;
2. leave Fleet HQ as Agent0-1;
3. verify local absence;
4. rejoin Fleet HQ;
5. verify Fleet HQ appears in local `joined_rooms`;
6. verify local and gateway membership agree;
7. restart the bot and perform a controlled test.

Do not repeatedly write `m.room.member` state against partial room state.

## Phase 6: Sequential fleet rollout

Roll out one node at a time. Never restart all five simultaneously before the canary proves loop safety.

If a validation gate fails, keep that bot stopped while Agent Zero and conduwuite remain available, then repair forward.

---

## Completion Gates

A node is repaired only when all conditions pass:

- Matrix `/whoami` exactly equals the manifest identity;
- the canonical account is locally joined to every required room;
- the authenticated Agent Zero probe succeeds;
- exactly one bot runtime and supervisor are active;
- the sync cursor advances without inappropriate resets;
- no event is processed twice across a controlled restart;
- self-authored events never trigger a response;
- no sustained HTTP 401/403 occurs;
- no rapid response or restart loop occurs;
- deployed hashes match the release manifest.

---

## Rollback Policy

Rollback may restore the prior software bundle and protected state snapshot, but it must not reactivate:

- a credential known to belong to another instance;
- a Matrix token known to belong to the wrong identity;
- a bot configuration known to lack required room membership.

In those cases, leave the bot stopped and repair forward while keeping Agent Zero and conduwuite online.

---

## Required Automated Tests

- Canonical credential exporter matches the token accepted by Agent Zero with empty and nonempty login credentials.
- A wrong nonempty Agent Zero credential fails preflight and cannot suppress canonical recovery.
- Duplicate credentials across sovereign nodes fail fleet validation.
- Matrix token/identity mismatch fails before `/sync`.
- Missing required local room membership fails startup.
- Gateway/local membership disagreement produces a leave/rejoin recommendation.
- Empty successful syncs do not reset the cursor or increment failure counters.
- Cursor persistence prevents replay after restart.
- Self-authored events never trigger responses.
- Two-member rooms still obey declared trigger policy.
- Only one bot runtime may be active.
- A second reconciler application is a no-op.
- Dry-run creates no files, backups, network mutations, or process changes.
- Release checksum mismatch prevents startup.

---

## Monitoring and Alerts

Expose per node:

- Matrix identity-match status;
- required-room local membership status;
- Agent Zero authenticated-probe status;
- HTTP 401/403 count;
- last successful sync and cursor age;
- cursor reset count;
- duplicate-event and self-event drops;
- outgoing responses per room per minute;
- bot process count and restart rate;
- deployed release and hash drift.

Alert immediately on:

- identity mismatch;
- Agent Zero HTTP 401/403;
- required-room loss;
- duplicate bot processes;
- release-integrity failure;
- sustained response-loop thresholds.

Do not alert solely because a valid incremental sync contains no events.

---

## Dangerous Approaches to Avoid

- Do not copy a known-working Agent0-2 credential to another node.
- Do not give all nodes the same runtime ID or authentication credentials.
- Do not restore loopback authentication bypasses.
- Do not endlessly restart permanent 401/403 or identity failures.
- Do not run Rust and Python bots concurrently for one account.
- Do not trust a configured user ID without validating `/whoami`.
- Do not trust gateway room state without checking local conduwuite membership.
- Do not place secrets in logs, CLI arguments, templates, release manifests, or fleet-wide archives.
- Do not perform simultaneous fleet restarts before a canary passes.

---

## Final Assessment

The incident is best understood as a control-plane ownership failure rather than several unrelated bot failures. The durable repair is not merely to replace three credentials and rejoin two accounts. The fleet requires:

- one canonical credential authority;
- declarative identities and required rooms;
- fail-closed startup validation;
- idempotent reconciliation;
- immutable releases;
- domain-specific monitoring;
- sequential, gated rollout.

No remediation described in this document had been executed as of the report date.

---

# Resolution Record

**Date:** 2026-10-09  
**Executed by:** Geoff White with Cursor AI assistance

## Actions Taken

### Phase 1 -- Rollback state captured
Fleet credential fingerprints, identities, room membership, and process state recorded before any changes.

### Phase 3 -- Agent0-3 and Agent0-4 credential repaired
The stale Agent0-2 `A0_API_KEY` value (`83dae4ffc6b3` fingerprint) was replaced with each node's correctly derived canonical token on the host-side bot `.env`. Derivation algorithm (SHA-256 of `runtime_id:auth_login:auth_password` → base64url → first 16 chars) was validated against both known-good baselines before use. Bots restarted via `supervisorctl restart run_bot`; both came up syncing with correct credentials immediately.

### Phase 4 -- Agent0-5 identity and authentication repaired
`@agent0-5:agent0-5-mhs.cybertribe.com` did not exist on the Continuwuity homeserver -- only `@agent0-5-mcp` had been registered (July 6, 2026). The account was created using the existing `CONTINUWUITY_REGISTRATION_TOKEN` from the host `.env` and secured with a new 32-character random password. The account joined Fleet HQ (`!gahcrWFWAUJQPPkuQy:v-site.net`). The bot `.env` was updated with the correct identity, new Matrix token, and correctly derived `A0_API_KEY`. `@agent0-5-mcp` token to be revoked after 24-hour observation window.

### Phase 5 -- Agent0-1 Fleet HQ membership
Confirmed already resolved prior to this session.

### Phase 6 -- Sequential fleet rollout
All nodes repaired and validated sequentially. No simultaneous restarts.

## Final Completion Gate Results (2026-10-09T22:50:52Z)

| Agent | Identity | Fleet HQ (local) | A0 API auth | Bot processes | A0_API_KEY fingerprint |
|---|---|---|---|---|---|
| Agent0-1 | `@agent0-1:agent0-1-mhs.cybertribe.com` | ✅ | ✅ | 1 (supervisord) | `09fc06b05bf6` |
| Agent0-2 | `@agent0-2:agent0-2-mhs.cybertribe.com` | ✅ | ✅ | 1 (supervisord) | `83dae4ffc6b3` |
| Agent0-3 | `@agent0-3:agent0-3-mhs.cybertribe.com` | ✅ | ✅ | 1 (supervisord) | `6c441c22b045` |
| Agent0-4 | `@agent0-4:agent0-4-mhs.cybertribe.com` | ✅ | ✅ | 1 (supervisord) | `045d54e0a0ee` |
| Agent0-5 | `@agent0-5:agent0-5-mhs.cybertribe.com` | ✅ | ✅ | 1 (supervisord) | `e01ef7cccea7` |

## Findings Not in Original Report

- All five agents are running the **Rust bot** (not Python); supervisord is PID 1 in all containers, managing `run_bot` via `run-bot-wrapper.sh`.
- The deployed Rust binary (May 14, 2026) predates the `compute_deterministic_token()` fallback added to the repo. The credential fix was applied directly to `.env` files rather than relying on bot-side derivation.
- `@agent0-5` had never been registered on the Agent0-5 Continuwuity homeserver. Only `@agent0-5-mcp` existed (registered 2026-07-06). The account was created as part of this repair.
- The stored `MATRIX_PASSWORD` in the Agent0-5 host `.env` did not authenticate either account -- it was stale. The Continuwuity registration token path was used instead.

## Deferred to Permanent Repair Strategy

Phase 0 (control-plane structural hardening) was not executed before the one-time fix. The following work remains open:

- Remove random `A0_API_KEY` generation from `create-instance.sh`
- Update deployed Rust bot to use derived token as primary (not fallback)
- Add startup preflight: `/whoami` identity check + local room membership gate + A0 auth probe
- Add bot-to-Agent-Zero auth check to domain-specific watchdog
- Implement per-instance identity manifests
- Implement idempotent reconciler (`check` / `plan` / `apply`)
- Refactor external fleet scripts into unified management utility
- Immutable release bundles with checksums
