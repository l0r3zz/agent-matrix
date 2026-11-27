# Cursor Context: Agent-Matrix Documentation Update Brief
# Date: 2026-03-05
# Purpose: Update golden docs on tarnover with post-migration lessons learned
# Author: Agent0-1 (post-migration to g2s)

---

## 1. What Happened

Agent0-1 was successfully migrated from tarnover to g2s on 2026-03-05.
During migration and subsequent testing, several documentation gaps and
corrections were identified that need to be applied to the golden docs.

The golden docs live on tarnover at:
`/a0/usr/projects/agent-matrix/multi-instance-deploy/`

Updated consolidated docs were also pushed to g2s at:
`g2s:/tmp/consolidated/` (agent-matrix-design.md, agent-matrix-design-next.md, operations-manual.md, theory-of-operations.md)

---

## 2. Fleet Status (Current)

| Instance  | Host | Agent IP    | MHS IP      | Matrix ID                                    | Federation | Status    |
|-----------|------|-------------|-------------|----------------------------------------------|------------|-----------|
| agent0-1  | g2s  | 172.23.88.1 | 172.23.89.1 | @agent0-1:agent0-1-mhs.cybertribe.com        | Verified   | Sovereign |
| agent0-2  | g2s  | 172.23.88.2 | 172.23.89.2 | @agent0-2:agent0-2-mhs.cybertribe.com        | Verified   | Sovereign |
| agent0-3  | g2s  | 172.23.88.3 | 172.23.89.3 | @agent0-3:agent0-3-mhs.cybertribe.com        | Verified   | Sovereign |
| agent0-4  | g2s  | 172.23.88.4 | 172.23.89.4 | -                                            | Pre-wired  | Available |
| agent0-5  | g2s  | 172.23.88.5 | 172.23.89.5 | -                                            | Pre-wired  | Available |

agent0-1 was formerly on tarnover with identity @agent (not @agent0-1). After migration it was given the correct fleet-standard name.

---

## 3. NEW Corrections Required (Post-Migration Gotchas)

### Gotcha #13 - settings.json MCP headers override MCP server .env
**Problem:** Agent Zero sends MCP headers from the `settings.json` `mcp_servers` config on every MCP request. If headers contain `matrix_user_id` and `matrix_access_token`, these OVERRIDE whatever is in the MCP server's own `.env` file.

**Impact:** During migration, the MCP server .env was updated with new credentials, but Agent Zero kept sending the old credentials from settings.json. The MCP server appeared broken with M_UNKNOWN_TOKEN errors.

**Fix:** When changing Matrix credentials, update BOTH:
1. The MCP server `.env` file
2. The Agent Zero UI: Settings > MCP/A2A > headers block

**Alternative:** Remove the headers block entirely from the MCP config in settings.json. Only works if the MCP server .env has all credentials set.

**Applies to docs:** multi-instance-guide.md (Section 5.4), operations-manual.md, theory-of-operations.md

---

### Gotcha #14 - Docker image name
**Problem:** Migration context bundle and some templates specified `frdel/agent-zero:latest` as the Docker image. The correct fleet-standard image is `agent0ai/agent-zero`.

**Fix:** All templates and docs must use `agent0ai/agent-zero`.

**Applies to docs:** docker-compose.yml.template, create-instance.sh, multi-instance-guide.md, Migration.md, operations-manual.md

---

## 4. New Pattern: startup-services.sh

During the migration, a persistent auto-start script was created. This is now the standard pattern for all agent instances.

### docker-compose.yml command override
```yaml
services:
  agent0-N:
    image: agent0ai/agent-zero
    command: /bin/bash -c '/a0/usr/workdir/startup-services.sh & exec /usr/bin/python3 /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf'
```

### startup-services.sh (lives at /a0/usr/workdir/startup-services.sh)
Four-phase boot sequence:
1. **Phase 1:** Start MCP server immediately (`node dist/http-server.js`) - must be up before Agent Zero preloads MCP tools
2. **Phase 2:** Wait for Agent Zero API at localhost:80 (up to 120 seconds) - bot needs the API
3. **Phase 3:** Install Python dependencies (`matrix-nio markdown aiohttp`) - these are wiped on container restart
4. **Phase 4:** Start matrix-bot (`/opt/venv-a0/bin/python matrix_bot.py`)

Logs to: `/a0/usr/workdir/startup-services.log`

**Applies to docs:** docker-compose.yml.template (add command), create-instance.sh (generate startup-services.sh), multi-instance-guide.md (new section), operations-manual.md

---

## 5. Previously Identified Corrections (already applied to g2s consolidated docs)

These were applied to the consolidated docs pushed to g2s:/tmp/consolidated/ but should also be verified in the tarnover golden copies:

| #  | Correction              | Details |
|----|-------------------------|---------|
| 1  | MCP entry point         | `node dist/index.js` -> `node dist/http-server.js` |
| 2  | MCP transport type      | `"type": "http"` -> `"type": "streamable-http"` |
| 3  | MCP headers             | Can be omitted if not in settings.json (server reads .env) |
| 4  | Step-CA syntax          | `--not-after 8760h` -> `--not-after=8760h` (equals sign required for v0.29.x) |
| 5  | Dendrite Docker image   | `matrixdotorg/dendrite:latest` -> `ghcr.io/element-hq/dendrite-monolith:v0.15.2` |
| 6  | Python venv path        | System python won't work; use `/opt/venv-a0/bin/python3` and `/opt/venv-a0/bin/pip` |
| 7  | agent0-3 added          | All topology/fleet/IP tables updated for 3 active agents |
| 8  | SMTP Section 5.6        | Added to multi-instance-guide.md |
| 9  | SMTP note               | Added to Migration.md |
| 10 | Dendrite key gen        | Python fallback method added (ssh-keygen keys cause "keyBlock is nil") |
| 11 | Supervisord claim       | Corrected to startup-services.sh in design-next.md |

---

## 6. Documents That Need Updates

### On tarnover (golden copies):

| Document                       | Path        | Updates Needed |
|-------------------------------|-------------|----------------|
| `docker-compose.yml.template` | `templates/` | Image -> `agent0ai/agent-zero`, add `command:` with startup-services.sh |
| `create-instance.sh`          | root        | Generate startup-services.sh from template, use correct image |
| `multi-instance-guide.md`     | root        | Gotcha #13 + #14, startup-services.sh section, fleet status |
| `Migration.md`                | root        | Correct image name, add startup command section, gotcha #13 |
| `operations-manual.md`        | root        | Fleet status (agent0-1 now sovereign on g2s), gotcha #13 |
| `theory-of-operations.md`     | root        | Fleet status, startup-services.sh architecture |
| `agent-matrix-design.md`      | root        | Fleet status |
| `agent-matrix-design-next.md` | root        | Fleet status, startup-services.sh |

### Reference files on g2s:
- Updated consolidated docs: `g2s:/tmp/consolidated/` (4 files)
- Updated deployment files: `g2s:/tmp/multi-instance-deploy/` (templates + guides)
- Working startup-services.sh: `g2s:/opt/agent-zero/agent0-1/usr/workdir/startup-services.sh`
- Working docker-compose.yml: `g2s:/opt/agent-zero/agent0-1/docker-compose.yml`

---

## 7. Template: startup-services.sh

For create-instance.sh to generate per-instance:

```bash
#!/bin/bash
# startup-services.sh - persistent startup script for matrix services
# Launched via docker-compose command: runs in background alongside supervisord
# Lives on bind mount: /a0/usr/workdir/startup-services.sh

LOG="/a0/usr/workdir/startup-services.log"
echo "$(date '+%F %T') startup-services.sh starting" >> "$LOG"

# Phase 1: Start MCP server IMMEDIATELY
if ! pgrep -f 'http-server.js' > /dev/null; then
    echo "$(date '+%F %T') Starting matrix-mcp-server..." >> "$LOG"
    cd /a0/usr/workdir/matrix-mcp-server
    nohup node dist/http-server.js >> mcp-server.log 2>&1 &
    echo "$(date '+%F %T') matrix-mcp-server started (pid $!)" >> "$LOG"
fi

# Phase 2: Wait for Agent Zero API
echo "$(date '+%F %T') Waiting for Agent Zero API..." >> "$LOG"
for i in $(seq 1 60); do
    curl -s -o /dev/null http://localhost:80 && break
    sleep 2
done
echo "$(date '+%F %T') Agent Zero API ready" >> "$LOG"

# Phase 3: Install Python dependencies (wiped on restart)
echo "$(date '+%F %T') Installing pip dependencies..." >> "$LOG"
/opt/venv-a0/bin/pip install matrix-nio markdown aiohttp -q 2>> "$LOG"

# Phase 4: Start matrix-bot
if ! pgrep -f 'matrix_bot.py' > /dev/null; then
    echo "$(date '+%F %T') Starting matrix-bot..." >> "$LOG"
    cd /a0/usr/workdir/matrix-bot
    nohup /opt/venv-a0/bin/python matrix_bot.py >> bot.log 2>&1 &
    echo "$(date '+%F %T') matrix-bot started (pid $!)" >> "$LOG"
fi

echo "$(date '+%F %T') startup-services.sh complete" >> "$LOG"
```

---

## 8. Correct MCP/A2A UI Configuration

```json
{
    "mcpServers": {
        "matrix": {
            "type": "streamable-http",
            "url": "http://localhost:3000/mcp"
        }
    }
}
```

NOTE: Headers are OPTIONAL. If included in settings.json, they OVERRIDE the MCP server .env.
Best practice: omit headers entirely and configure credentials in the MCP server .env only.
If headers must be used, they MUST match the current Matrix identity.

---

## 9. SMTP Configuration Reference

Already added as Section 5.6 in multi-instance-guide.md. Key details:
- Account: agent0.1.vsite@gmail.com
- Requires Gmail App Password (16-char, not regular password)
- Requires 2-Step Verification enabled on Google account
- .env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, FORCE_TLS

---

## 10. Critical Reminders for Cursor

1. **Do NOT use create-instance.sh for migrations** - it overwrites data. Use Migration.md procedures.
2. **Matrix keys:** Use Dendrite's native `generate-keys` or the Python Ed25519 generator. NEVER use `ssh-keygen` - causes "keyBlock is nil" fatal error.
3. **dendrite.yaml:** Must use `connection_string:` (not `connection:`). Must include all database blocks including `room_server`.
4. **Federation:** Requires `--https-bind-address :8448` in docker-compose command AND TLS cert/key mounts AND `tls_cert`/`tls_key` paths in dendrite.yaml global section.
5. **Synapse gateway:** hostAliases and federation_domain_whitelist on matrix.v-site.net must include all agent homeserver domains.
6. **Python in containers:** Always use `/opt/venv-a0/bin/python3`, never system python.
