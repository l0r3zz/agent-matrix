# Upgrade plan: Agent-Matrix v0.92 to v0.93

**Date**: 2026-11-08
**Branch**: `release/v0.93` (from `main` at `b34517b`)
**Target image**: `ghcr.io/l0r3zz/matrix-mcp-server-r2:0.3.0`
**Lab canary**: `@agent0-5` on g2s. Do not use another agent as the first live target.

This plan changes Agent-Matrix so a new install and an upgraded v0.92 agent both run one Matrix client. That client is `matrix-mcp-server-r2` 0.3.0. It serves the MCP tools and answers Matrix triggers. The separate `run_bot` program stays installed and stays stopped.

This document is the plan. It does not change the running fleet.

## What v0.93 means

v0.92 keeps two programs under one Matrix user:

- `run_mcp` opens `CRYPTO_STORE_PATH` and the device in `.device-id`.
- `run_bot` is `matrix-bot-rust` on a second device, `AgentZeroBot`.

`matrix-bot-rust` cannot read encrypted rooms. A second process on the same crypto store fails with `KeyStoreUnavailableError`. v0.3.0 of `matrix-mcp-server-r2` takes the inbound job on the existing MCP device when `BOT_ENABLED=true`. The default in the binary is still false. Agent-Matrix v0.93 is what turns the flag on and stops the old program from coming back.

Synapse is already `1.164.2` on `matrix.v-site.net`. This plan does not upgrade Synapse, Continuwuity, or Caddy.

## Prerequisite

Do not run the live upgrade until GitHub has image tag `0.3.0`.

That tag is created on `matrix-mcp-server-r2` `main` after pull request #2 merges. The tag publishes the image and moves `:latest`. Until that tag exists, the Agent-Matrix code can still land on `release/v0.93`. The upgrade script must refuse to copy a binary when the tag is missing.

The fleet script `deploy-mms-r2-to-agent.sh` still defaults to `0.2.0`. v0.93 changes that default to `0.3.0`.

## Rules for every path

These rules apply to a new install and to an upgrade:

- Keep the MCP access token, `.device-id`, crypto store, and recovery key. Do not log them.
- Do not copy `MATRIX_ACCESS_TOKEN` from `matrix-bot/.env` into the MCP `.env`.
- Do not call logout. Do not reset the Matrix password.
- Do not run `switch-mcp-server.sh rust-restart` while `run_mcp` is already running.
- Do not `docker restart` the agent container until `run_bot` has `autostart=false` and `autorestart=false`.
- Stop `run_bot` before `BOT_ENABLED=true`.
- Restart only `run_mcp` after the binary or the MCP `.env` changes.
- Leave `matrix-bot-rust` on disk so a v0.92 rollback can start it again.
- `@agent0-5` stays in maintenance until this agent's own checks pass. Then it can return to `active`.

## New installs

A new agent comes from `create-instance.sh`, then `scripts/finalize-instance.sh`, then the supervisord block in `startup-services.sh`.

v0.93 new installs must:

1. Install `matrix-mcp-server-r2` from image tag `0.3.0`.
2. Keep `E2EE_ENABLED=true` for a normal fleet agent.
3. Write these lines into `/a0/usr/workdir/matrix-mcp-server/.env` when they are missing:
   - `BOT_ENABLED=true`
   - `BOT_DISPLAY_NAME` and `AGENT_IDENTITY`, using the agent's display name when one already exists
   - `A0_API_URL=http://localhost:80/api/api_message`
   - `AMCTL_API_KEY` from the am-ctl key already used on that host, without printing the key
4. Register `[program:run_bot]` with `autostart=false` and `autorestart=false`.
5. Register `[program:run_mcp]` with `autorestart=true`, and start only that program.
6. Install the v0.93 `watchdog.sh` so a stopped `run_bot` is a pass.
7. Do not run `split-bot-device.sh`. That script mints `AgentZeroBot`. v0.93 does not use that device.

`scripts/create-instance.sh` still copies the `matrix-bot` template. Keep that copy for rollback. Do not start it.

Two copies of some scripts exist. Change both, or a new install and a host command will disagree:

- `multi-instance-deploy/templates/scripts/deploy-mms-r2-to-agent.sh`
- `multi-instance-deploy/scripts/deploy-mms-r2-to-agent.sh`
- `multi-instance-deploy/templates/scripts/startup-services.sh`
- `multi-instance-deploy/templates/startup-services.sh.template`
- `multi-instance-deploy/templates/scripts/deploy-supervisord-mcp.sh`
- `multi-instance-deploy/templates/scripts/deploy-supervisord-mcp.py`

## Upgrade existing v0.92 agents

A container restart today starts `run_bot` even when am-ctl status is `maintenance`. `startup-services.sh` writes both programs with `autorestart=true` and no `autostart=false`. After the first write, the same script sees `run_mcp` and skips the block. Editing the template does not change a live `supervisord.conf`.

The upgrade script must edit the live container. Add:

`multi-instance-deploy/scripts/upgrade-v0.92-to-v0.93.sh`

Usage:

```bash
./upgrade-v0.92-to-v0.93.sh --dry-run 5
./upgrade-v0.92-to-v0.93.sh 5
./upgrade-v0.92-to-v0.93.sh 1 2 3 4
```

`--dry-run` prints the actions and changes nothing. The script takes instance numbers. It does not default to every agent.

Order for one agent:

1. Refuse to start when `ghcr.io/l0r3zz/matrix-mcp-server-r2:0.3.0` cannot be pulled.
2. Set the agent to `maintenance` in am-ctl before stopping `run_bot`.
3. Record that `run_mcp` is healthy and `crossSigned` is true. Stop if it is not. Do not print tokens or the recovery key.
4. Stop `run_bot`. Patch the live `[program:run_bot]` to `autostart=false` and `autorestart=false`. Run `supervisorctl reread` and `supervisorctl update`.
5. Confirm `pgrep -fc '[m]atrix-bot-rust'` is 0.
6. Copy the v0.93 `watchdog.sh` into `/a0/usr/workdir/watchdog.sh`.
7. Add the MCP `.env` lines from the new-install list when they are missing. Do not change `MATRIX_ACCESS_TOKEN`, `E2EE_ENABLED`, or the crypto store.
8. Install the `0.3.0` binary with `MMS_R2_TAG=0.3.0`. Replace the binary only while `run_bot` is stopped. Restart only `run_mcp`.
9. Require `/health` to report `version` `0.3.0`, `e2ee` true, `crossSigned` true, and `botEnabled` true.
10. Require `run_bot` to still be stopped after that restart.
11. Return that agent to `active` only after steps 5, 9, and 10 pass.

`@agent0-5` already runs a hand-built 0.3.0 binary with `BOT_ENABLED=true`, and `run_bot` is already stopped. The script must accept that state. It must not start `run_bot` in order to stop it. It replaces the hand-built binary with the published `0.3.0` image only after the supervisord patch is in place.

Run agent 5 first. Run agents 1 through 4 only after agent 5 answers `ping` and `hello` in Fleet HQ Clean and in one encrypted room the agent is already in.

## Code changes on this branch

### Supervisord

In both startup scripts and both `deploy-supervisord-mcp` scripts, write `run_bot` with `autostart=false` and `autorestart=false`. Keep `run_mcp` on `autorestart=true`.

The live upgrade script patches an existing conf. The templates cover the next container that does not already have the block. Also teach `startup-services.sh` to correct an existing `run_bot` block that still has `autorestart=true`. The current skip leaves old containers unchanged across a restart.

### Watchdog

`templates/scripts/watchdog.sh` passes `check_type: process` only when `matrix-bot-rust` count is exactly 1. am-ctl treats that failure as restartable and restarts `run_bot` when the agent is `active`.

v0.93 passes `process` when either statement is true:

- The count is 1 and `/health` reports `botEnabled` false. That is the old v0.92 layout.
- The count is 0, `/health` is healthy, and `botEnabled` is true.

The check fails when the count is 1 and `botEnabled` is true. Two inbound programs would both answer. The check also fails when the count is 0 and `botEnabled` is not true.

### am-ctl

`amctl/services/health_engine.py` restarts `run_bot` for every restartable failure that is not an `mcp` check. A `process` failure must not start `run_bot` when the intended state is the integrated bot.

`amctl/services/deployer.py` stops `run_bot`, installs the release bundle, and starts `run_bot` again. v0.93 still ships `matrix-bot-rust` in the bundle. The deployer must not start `run_bot` after the install.

`amctl/services/reconciler.py` may still compare the `matrix-bot-rust` hash. It must not start `run_bot` to repair that hash.

Update the tests that require `bot_count == 1` or a `run_bot` restart after deploy. The v0.93 expectation is `bot_count == 0` while `/health` has `botEnabled: true`.

### Token healthcheck

`templates/scripts/fleet-token-healthcheck.sh` runs `supervisorctl restart run_mcp run_bot`. v0.93 restarts `run_mcp` only. It must not write a new token into `matrix-bot/.env` and it must not log the bot in as `AgentZeroBot`.

The MCP token refresh from v0.92 stays. It reuses the device already stored for `run_mcp`.

### Release bundle

`multi-instance-deploy/Makefile` still bundles `watchdog.sh`, `startup-services.sh`, and `matrix-bot-rust`. Build the v0.93 bundle with `make release VERSION=v0.93`. The new watchdog and startup script are part of that bundle. The bot binary remains in the bundle for rollback only.

### Operator docs

Update `docs/operations-manual.md` so a new install does not log in as device `AgentZeroBot` and does not describe `matrix-bot-rust` as the program that reads encrypted rooms. Point the E2EE section at r2 `0.3.0` and at this plan. Leave the v0.92 device-split notes in place as the path this release retires.

## Rollback

Rollback one agent at a time. Set it to `maintenance` first.

1. Set `BOT_ENABLED=false` in the MCP `.env`.
2. Restore the `0.2.0` binary, or the binary backed up before step 8.
3. Restart only `run_mcp`. Confirm `/health` shows `botEnabled` false and `version` `0.2.0`.
4. Set the live `run_bot` program back to `autorestart=true` and `autostart=true`.
5. Start `run_bot`. Confirm the process count is 1.
6. Restore the v0.92 watchdog if the v0.93 check would fail a running bot with `botEnabled` false. The v0.93 check allows that layout, so the old watchdog is not required for rollback.
7. Return the agent to `active` only after `ping` works in an unencrypted room. Encrypted rooms stay on `run_mcp`. The restored `run_bot` still cannot read them.

Do not restore by copying the bot token over the MCP token.

## Acceptance

An upgraded agent and a new v0.93 agent both meet these checks:

- `/health` reports `version` `0.3.0`, `e2ee` true, `crossSigned` true, and `botEnabled` true.
- `run_bot` is stopped. A `docker restart` of that container leaves it stopped and brings `run_mcp` back.
- `agent0-N: ping` returns one `PONG` in Fleet HQ Clean and in one encrypted room.
- `agent0-N: hello` returns one hello line.
- One question returns one Agent Zero reply.
- `send_message` in an encrypted room reports `Encrypted: Yes`. `get_room_messages` returns that text. Element shows the same text.
- An invite from `@admin:v-site.net` joins and greets once.
- An invite from a user who is not in the trusted set does not join, and the log contains `reject_untrusted`.
- am-ctl status `active` does not start `run_bot`.

## Out of scope

- Merging r2 pull request #2 or pushing the `v0.3.0` tag. Those happen in `matrix-mcp-server-r2`.
- Deleting the `matrix-bot` source tree.
- Changing Continuwuity, Caddy, or the Synapse Helm chart.
- A fleet-wide `docker restart` before agent 5 has passed.
