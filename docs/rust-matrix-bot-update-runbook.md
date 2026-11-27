# Rust Matrix-Bot Update Runbook

**Version:** 1.0
**Last Updated:** 2026-03-28
**Author:** agent0-1

---

## Overview

This runbook covers the full workflow for updating, rebuilding, deploying, and verifying the Rust-based matrix-bot across the Agent-Matrix fleet.

---

## Prerequisites

| Requirement | Location |
|---|---|
| Rust toolchain (cargo) installed on g2s | `/home/l0r3zz/.rustup/` |
| SSH key for g2s | `~/.ssh/id_ed25519` (local) or `/a0/usr/skills/ssh2g2s/keys/` (backup) |
| Fleet containers running | `agent0-1` through `agent0-5` on g2s (172.23.100.121) |

---

## Key Paths

| Path | Purpose |
|---|---|
| `/opt/agent-zero/multi-instance-deploy/templates/matrix-bot/rust/` | **Authoritative Rust source** (edit here) |
| `/opt/agent-zero/multi-instance-deploy/templates/matrix-bot/rust/src/main.rs` | Main bot logic |
| `/opt/agent-zero/multi-instance-deploy/templates/matrix-bot/build-rust.sh` | Compile script |
| `/opt/agent-zero/multi-instance-deploy/templates/matrix-bot/matrix-bot-rust` | Compiled binary (after build) |
| `/opt/agent-zero/multi-instance-deploy/templates/scripts/sync-fleet.sh` | Deploy script |
| `/opt/agent-zero/agent0-N/usr/workdir/matrix-bot/` | Per-instance deployed bot directory |

---

## Step 1: Edit Source Code

Always edit the **template source**, not the per-instance copies.

```bash
# Via SSH from agent0-1:
bash /a0/usr/skills/ssh2g2s/scripts/ssh2g2s.sh 'vim /opt/agent-zero/multi-instance-deploy/templates/matrix-bot/rust/src/main.rs'

# Or push a local file:
bash /a0/usr/skills/ssh2g2s/scripts/scp2g2s.sh /local/path/main.rs /opt/agent-zero/multi-instance-deploy/templates/matrix-bot/rust/src/main.rs
```

---

## Step 2: Build

Compile the Rust binary on g2s. **Cargo must be in PATH.**

```bash
bash /a0/usr/skills/ssh2g2s/scripts/ssh2g2s.sh 'source ~/.cargo/env 2>/dev/null || export PATH="$HOME/.cargo/bin:$PATH"; /opt/agent-zero/multi-instance-deploy/templates/matrix-bot/build-rust.sh'
```

### If Build Fails — Common Rust Errors

#### `error[E0384]: cannot assign twice to immutable variable`

A variable is reassigned but declared immutable.

**Fix:** Add `mut` to the declaration.
```bash
sed -i 'XXXs/let body =/let mut body =/' /opt/agent-zero/multi-instance-deploy/templates/matrix-bot/rust/src/main.rs
```
Where `XXX` is the line number from the error message.

#### `error[E0596]: cannot borrow as mutable`

A mutable borrow is attempted on an immutable reference.

**Fix:** Change `&x` to `&mut x` or add `mut` to the binding.

#### `warning: unused variable`

Variable declared but never used. Either use it or prefix with `_`.

**Fix:** `let unused_var` → `let _unused_var`

---

## Step 3: Deploy to Fleet

### Option A: Build + Deploy in one command (recommended)

```bash
cat > /tmp/build_and_deploy.sh << 'LOCALEOF'
#!/bin/bash
set -euo pipefail
export PATH="$HOME/.cargo/bin:$PATH"

# Build
echo "=== Building Rust Binary ==="
/opt/agent-zero/multi-instance-deploy/templates/matrix-bot/build-rust.sh

# Deploy + Restart
echo "=== Deploying to Fleet ==="
/opt/agent-zero/multi-instance-deploy/templates/scripts/sync-fleet.sh --restart

echo "=== Verifying (wait 10s) ==="
sleep 10
for n in 1 2 3 4 5; do
  BOTS=$(docker exec agent0-$n ps aux 2>/dev/null | grep -E 'matrix_bot|matrix-bot-rust' | grep -v grep | wc -l)
  echo "  agent0-$n: $BOTS bot process(es)"
done
LOCALEOF
chmod +x /tmp/build_and_deploy.sh
bash /a0/usr/skills/ssh2g2s/scripts/remote-exec.sh /tmp/build_and_deploy.sh
```

### Option B: Deploy specific instances only

```bash
bash /a0/usr/skills/ssh2g2s/scripts/ssh2g2s.sh '/opt/agent-zero/multi-instance-deploy/templates/scripts/sync-fleet.sh --restart --instances 2,3,4'
```

### What `sync-fleet.sh --restart` does

1. **Rsyncs** template `matrix-bot/` to each instance's `workdir/matrix-bot/` (preserves `.env`)
2. **Kills** old bot + MCP processes via `pkill -9`
3. **Restarts** MCP server (`nohup node dist/http-server.js`) and bot (`nohup ./run-matrix-bot.sh`)

---

## Step 4: Verify Deployment

### Check bot process count per agent

```bash
bash /a0/usr/skills/ssh2g2s/scripts/ssh2g2s.sh '
for n in 1 2 3 4 5; do
  BOTS=$(docker exec agent0-$n ps aux 2>/dev/null | grep -E "matrix_bot|matrix-bot-rust" | grep -v grep | wc -l)
  PID=$(docker exec agent0-$n cat /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null)
  echo "agent0-$n: $BOTS process(es), active PID=$PID"
done'
```

**Expected:** 1 process per agent. If you see 2+, there are zombie processes (see cleanup below).

### Check bot logs for errors

```bash
bash /a0/usr/skills/ssh2g2s/scripts/ssh2g2s.sh '
for n in 1 2 3 4 5; do
  echo "=== agent0-$n ==="
  docker exec agent0-$n tail -5 /a0/usr/workdir/matrix-bot/bot.log 2>/dev/null || echo "  NO LOG"
  echo ""
done'
```

---

## Step 5: Cleanup Zombie Processes (if needed)

After restart, old bot processes may not fully terminate. Each agent should have exactly **1 bot process**.

### Detect zombies

Look for agents showing 2+ bot processes. The active PID is in `bot.pid`.

### Kill zombies

```bash
cat > /tmp/cleanup_bots.sh << 'LOCALEOF'
#!/bin/bash
for n in 1 2 3 4 5; do
  ACTIVE_PID=$(docker exec agent0-$n cat /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null)
  ALL_PIDS=$(docker exec agent0-$n ps aux 2>/dev/null | grep 'matrix_bot\|matrix-bot-rust' | grep -v grep | awk '{print $2}')
  for PID in $ALL_PIDS; do
    if [ "$PID" != "$ACTIVE_PID" ]; then
      echo "agent0-$n: Killing stale PID $PID"
      docker exec agent0-$n kill -9 $PID
    fi
  done
done
echo "=== Verification ==="
for n in 1 2 3 4 5; do
  BOTS=$(docker exec agent0-$n ps aux 2>/dev/null | grep 'matrix_bot\|matrix-bot-rust' | grep -v grep | wc -l)
  echo "agent0-$n: $BOTS process(es)"
done
LOCALEOF
chmod +x /tmp/cleanup_bots.sh
bash /a0/usr/skills/ssh2g2s/scripts/remote-exec.sh /tmp/cleanup_bots.sh
```

---

## Quick Reference: One-Liner Workflow

```bash
# Build + Deploy + Verify + Cleanup (all-in-one)
cat > /tmp/full_update.sh << 'LOCALEOF'
#!/bin/bash
set -euo pipefail
export PATH="$HOME/.cargo/bin:$PATH"

echo "=== Build ==="
/opt/agent-zero/multi-instance-deploy/templates/matrix-bot/build-rust.sh

echo "=== Deploy ==="
/opt/agent-zero/multi-instance-deploy/templates/scripts/sync-fleet.sh --restart

echo "=== Verify + Cleanup ==="
sleep 10
for n in 1 2 3 4 5; do
  ACTIVE=$(docker exec agent0-$n cat /a0/usr/workdir/matrix-bot/bot.pid 2>/dev/null)
  ALL_PIDS=$(docker exec agent0-$n ps aux 2>/dev/null | grep 'matrix_bot\|matrix-bot-rust' | grep -v grep | awk '{print $2}')
  KEPT=0
  for PID in $ALL_PIDS; do
    if [ "$PID" != "$ACTIVE" ]; then
      docker exec agent0-$n kill -9 $PID 2>/dev/null
    else
      KEPT=1
    fi
  done
  echo "agent0-$n: $KEPT process(es) ✅"
done
echo "=== DONE ==="
LOCALEOF
chmod +x /tmp/full_update.sh
bash /a0/usr/skills/ssh2g2s/scripts/remote-exec.sh /tmp/full_update.sh
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `cargo not found` | Rust not in SSH session PATH | Add `source ~/.cargo/env` before build |
| Build error E0384 | Immutable variable reassigned | Add `mut` to declaration |
| 2+ bot processes per agent | Zombie processes from restart | Kill stale PIDs (Step 5) |
| Bot not syncing after deploy | Restart race condition | Wait 20s, check `bot.log` |
| MCP tools show 0 count | MCP not fully restarted | `docker exec agent0-N pkill -9 -f http-server; sleep 2; docker exec -d agent0-N bash -c 'cd .../matrix-mcp-server && nohup node dist/http-server.js >> mcp-server.log 2>&1 &'` |
| `sync-fleet.sh` skips instance | Container not running | `docker start agent0-N` first |

---

## Related Documentation

- `rust/README.md` — Basic build instructions
- `multi-instance-guide.md` — Full fleet operations guide
- `operations-manual.md` — Operational procedures
- `sync-fleet.sh --help` — Deploy script options
- `switch-matrix-bot.sh` — Python/Rust runtime switching
