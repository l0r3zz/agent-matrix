# Decommission Guide

This guide documents how to safely decommission an Agent-Matrix instance using:

- `multi-instance-deploy/decommission-instance.sh`

---

## Scope

The decommission script handles **instance teardown only**:

- Stops/removes instance containers (`agent0-N`, `agent0-N-mhs`)
- Removes instance directory (`/opt/agent-zero/agent0-N`)
- Optionally saves credentials/certs/keys (`--save-creds`)
- Optionally archives data + docker volumes (`--archive`)

### Explicit non-goals

The script **does not** modify networking constructs:

- static routes
- DNS entries / host aliases
- firewall rules
- VPN/OpenVPN settings
- DD-WRT startup scripts

Networking decommission is intentionally a separate concern.

---

## Script location

```bash
/a0/usr/projects/agent-matrix/multi-instance-deploy/decommission-instance.sh
```

Compatibility alias:

```bash
/a0/usr/projects/agent-matrix/multi-instance-deploy/decommission-instance.sh
```

---

## Usage

```bash
decommission-instance.sh [options] N
```

Where `N` is the instance number (`agent0-N`).

### Options

- `-y`, `--yes`  
  Skip interactive confirmation.

- `--save-creds`  
  Save certs/keys/env files into artifact bundle.

- `--archive`  
  Archive instance directory and attached Docker volumes.

- `--base-dir PATH`  
  Override default base directory (`/opt/agent-zero`).

- `-h`, `--help`  
  Show help.

---

## Confirmation behavior

Without `-y`, script requires exact confirmation:

```text
Type 'yes' to permanently decommission agent0-N:
```

Only `yes` is accepted (`y` is rejected).

---

## Artifact output

When `--save-creds` and/or `--archive` are used, artifacts are saved to:

```bash
/opt/agent-zero/decommission-artifacts/agent0-N-<timestamp>/
```

Typical contents:

- `creds/` (certs/keys/env files)
- `agent0-N-instance-dir.tar.gz`
- `volumes/<volume>.tar.gz`

---

## Recommended commands

### Interactive decommission (safe prompt)

```bash
/a0/usr/projects/agent-matrix/multi-instance-deploy/decommission-instance.sh 2
```

### Non-interactive decommission

```bash
/a0/usr/projects/agent-matrix/multi-instance-deploy/decommission-instance.sh -y 2
```

### Decommission with full backup artifacts

```bash
/a0/usr/projects/agent-matrix/multi-instance-deploy/decommission-instance.sh -y --save-creds --archive 2
```


```bash
/a0/usr/projects/agent-matrix/multi-instance-deploy/decommission-instance.sh -y --save-creds --archive 3
```

---

## Suggested workflow for rebuild testing

1. Keep `agent0-1` untouched as baseline.
2. Decommission target instance with `--save-creds --archive`.
3. Rebuild using latest `create-instance.sh` into a fresh slot.
4. Validate Matrix auth, sync, invite/join, and response behavior.

---

## Troubleshooting

### Script says instance dir missing

Instance may already be partially removed. Container cleanup still proceeds.

### Volume archive fails

Script continues and reports failed volume(s). Check Docker volume names and permissions.

### Need dry-run behavior

Current script executes directly. Add a `--dry-run` option in a future revision if needed.

---

## Change control note

Because decommission is destructive, keep this guide and script in sync whenever:

- artifact layout changes,
- new flags are added,
- decommission scope expands (e.g., networking teardown phase).
