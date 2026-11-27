# Upgrade plan: Agent-Matrix v0.93 to v0.94

**Date**: 2026-11-26
**Branch**: `release/v0.94` (from `origin/main` at `7e05404`)
**Target image**: `ghcr.io/l0r3zz/matrix-mcp-server-r2:0.4.0`
**Binary sha256**: `4e3c5bc89ddacd72b782d9230f6bedf18a352b8774640f74e18e9237ac899dc5`

v0.94 keeps the v0.93 Matrix client. That client is still `run_mcp` (`matrix-mcp-server-r2`) with `BOT_ENABLED=true`. `run_bot` stays installed and stays stopped. The binary changes from 0.3.x to 0.4.0. The device id, crypto store, recovery key, and Matrix access token stay the same.

0.4.0 adds `list_invitations`, joins a trusted invite that arrived while `run_mcp` was stopped, and retries a not-yet-invited HTTP 403 while the invite remains. One image on a triggered prompt is sent to the model only when `MODEL_ACCEPTS_IMAGES=true`. Leave that variable unset unless the model accepts images.

This document is the plan. The script does not run until someone passes instance numbers on the Docker host.

## What the install path uses

Both copies of `deploy-mms-r2-to-agent.sh` default to image tag `0.4.0`:

- `multi-instance-deploy/templates/scripts/deploy-mms-r2-to-agent.sh`
- `multi-instance-deploy/scripts/deploy-mms-r2-to-agent.sh`

The script pulls that image, stops `run_mcp`, copies the binary, and starts `run_mcp` only. It does not start `run_bot` and it does not restart the agent container.

`scripts/upgrade-v0.92-to-v0.93.sh` still passes `MMS_R2_TAG=0.3.1`. A v0.92 upgrade does not jump to 0.4.0.

## Rules

- Do not run `switch-mcp-server.sh rust` or `rust-restart`. A second opener of the crypto store fails with `KeyStoreUnavailableError`.
- Do not `docker restart` the agent container.
- Do not start `run_bot`.
- Do not change `CRYPTO_STORE_PATH`, the recovery key, or the Matrix access token.
- Keep the previous binary. The upgrade script copies it to `matrix-mcp-server-r2.bak-pre-040` only when that file is absent. It does not overwrite `bak-v092` or an existing `bak-pre-040`.
- Do not set `MODEL_ACCEPTS_IMAGES` as part of this upgrade.

## Upgrade one agent

Run on the Docker host. There is no default of every agent. Upgrade one agent and read `/health` before the next.

```bash
multi-instance-deploy/scripts/upgrade-v0.93-to-v0.94.sh --dry-run 5
multi-instance-deploy/scripts/upgrade-v0.93-to-v0.94.sh --keep-maintenance 5
multi-instance-deploy/scripts/upgrade-v0.93-to-v0.94.sh 5
```

The script refuses to start when `ghcr.io/l0r3zz/matrix-mcp-server-r2:0.4.0` is missing. For each instance it:

1. Requires `run_bot` to already be stopped. It does not start `run_bot` in order to stop it.
2. Requires `/health` to report a healthy 0.3.0, 0.3.1, or 0.4.0 with `e2ee`, `crossSigned`, and `botEnabled` true. An agent that already runs the published 0.4.0 binary is left as it is. A 0.4.0 binary with a different sha256 is replaced.
3. Sets am-ctl status to `maintenance`.
4. Backs up the binary, then runs the deploy script with `MMS_R2_TAG=0.4.0`.
5. Requires `--version` to print `matrix-mcp-server-r2 0.4.0` and the sha256 above.
6. Requires the device id to be unchanged.
7. Waits up to 120 seconds for `/health` to report `version` `0.4.0`, `e2ee` true, `crossSigned` true, and `botEnabled` true.
8. Requires `run_bot` to still be stopped, then sets the agent back to `active` unless `--keep-maintenance` was passed.

## Rollback

Stop `run_mcp`, copy `matrix-mcp-server-r2.bak-pre-040` back to `matrix-mcp-server-r2`, and start `run_mcp`. The device id must still match. `/health` then reports the version that backup was taken from.

## Out of scope

- Creating a new agent. `create-instance.sh` and `am-ctl create` install 0.4.0. This upgrade script does not create agents.
- Setting `MODEL_ACCEPTS_IMAGES`.
- Upgrading Synapse, Continuwuity, Caddy, or Agent Zero.
