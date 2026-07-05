# Open Brain — Changelog

## 2026-07-05 — Disk Cleanup & Permission Fix Session

### docker-compose.yml

**Change:** Added `user: "1000:1000"` to the `postgres` service.

```diff
 services:
   # --- POSTGRESQL + PGVECTOR ---
   postgres:
+    user: "1000:1000"
     image: pgvector/pgvector:pg16
     container_name: open-brain-db
```

**Rationale:** The `./pgdata` bind mount is owned by UID 1000 (host user `l0r3zz`)
on g2s. Previously, the container ran as the default `postgres` user (UID 999),
which could not read files owned by 1000. This caused recurring
`FATAL: could not open file "global/pg_filenode.map": Permission denied`
errors. Setting `user: "1000:1000"` makes the container process run as UID 1000,
matching the bind mount ownership and eliminating the permission drift.

**Backup:** `docker-compose.yml.bak.1783263582`

### Data Directory Ownership

**Change:** `chown -R 1000:1000 /var/lib/postgresql/data` (inside container)

Previously chowned to 999:999 as a temporary fix. Reverted to 1000:1000
to match the new `user:` directive in docker-compose.yml.

### Container Recreation

Both containers were recreated via `docker compose up -d`:
- `open-brain-db`: Recreated with new `user:` directive. Healthy.
- `open-brain-mcp`: Restarted to reconnect to fresh DB. Running.

### Verification

- PostgreSQL logs: clean startup, `database system is ready to accept connections`
- `open_brain.thought_stats` (read): 177 thoughts returned successfully
- `open_brain.capture_thought` (write): Session findings captured successfully
- No permission errors in logs post-fix

### Root Cause Analysis

The `pgdata` directory on g2s is owned by `l0r3zz` (UID 1000). When Docker
bind-mounts this into the container, the host ownership is preserved. The
pgvector image's default `postgres` user (UID 999) cannot read files owned
by 1000 due to `rwx------` permissions. This was a recurring issue that
manifested whenever the data directory was touched by a host process or
the container was recreated without explicit chown.

The permanent fix (`user: "1000:1000"`) ensures the container process
always matches the host bind mount ownership, regardless of what happens
on the host side.
