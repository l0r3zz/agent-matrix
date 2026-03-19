# Zero-Touch Hardening v3.17

This document defines the mandatory invariants for fast and repeatable instance bring-up.

## Invariants
1. `TRIGGER_PREFIX` must be set to `agent0-N:`
2. `A0_API_KEY` must exist in both:
   - `usr/workdir/matrix-bot/.env`
   - `usr/workdir/matrix-mcp-server/.env`
3. Agent Zero `mcp_server_token` must match the same key.
4. Startup order is strict: MCP -> Agent Zero API ready -> bot.

## Template changes in v3.17
- `create-instance.sh` now injects `__A0_API_KEY__` into matrix-mcp `.env`.
- `create-instance.sh` sets `A0_SET_mcp_server_token` in generated `.env`.
- `docker-compose.yml.template` passes `A0_SET_*` env vars to container.
- `matrix-bot/.env.template` sets deterministic trigger prefix.
- `startup-services.sh` now performs deterministic key sync + API auth smoke check.

## Validation commands
```bash
# inside instance container
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:80/api_message \
  -H "Content-Type: application/json" -H "X-API-KEY: $A0_API_KEY" \
  -d '{"text":"health"}'
```
Expected: HTTP 200/400/422 (not 401).

## Deterministic ping fast-path
- Matrix bot now handles `ping` / `ping <token>` locally with `pong` / `pong <token>`.
- This bypasses LLM for acceptance checks, making tests deterministic.
- Recommended fleet policy: strict per-agent trigger prefix (`agent0-N:`).
