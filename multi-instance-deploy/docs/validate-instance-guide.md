# validate-instance.sh Guide

Path: `/opt/agent-zero/multi-instance-deploy/validate-instance.sh`

## Purpose
Run a deterministic acceptance test for a sovereign instance after create/restart.

## Usage
```bash
/opt/agent-zero/multi-instance-deploy/validate-instance.sh 4
/opt/agent-zero/multi-instance-deploy/validate-instance.sh --room-id '!roomid:v-site.net' 4
```

## Pass criteria
- Agent and homeserver containers are running (`agent0-N`, `agent0-N-continuwuity`, `agent0-N-mhs`)
- Continuwuity responds on 8008 (via Caddy) and 8448 (TLS via Caddy)
- startup-services completed
- `run_ui.py`, `http-server.js`, and `matrix_bot.py` are running
- `A0_API_KEY` exists and matches in bot + MCP env
- `AGENT_IDENTITY` is set correctly in bot .env
- API auth smoke does not return 401
- Matrix `/sync` returns `next_batch`
- (optional) room membership contains provided room id

## Validation Commands

### Container health
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep agent0-N
# Expect: agent0-N, agent0-N-continuwuity, agent0-N-mhs all "Up"
```

### Homeserver API (via Caddy)
```bash
# Client API
curl -s http://172.23.89.N:8008/_matrix/client/versions | python3 -m json.tool

# Federation API (TLS)
curl -sk https://172.23.89.N:8448/_matrix/key/v2/server | python3 -m json.tool
```

### Continuwuity logs
```bash
docker logs agent0-N-continuwuity --tail=20
# Should show startup without fatal errors
```

### Caddy logs
```bash
docker logs agent0-N-mhs --tail=20
# Should show TLS certificate loaded and listeners active
```

### Registration token check
```bash
# Verify registration token is set in compose environment
grep CONTINUWUITY_REGISTRATION_TOKEN /opt/agent-zero/agent0-N/docker-compose.yml
```

## Notes
- This script is read/verify only.
- It does not mutate networking constructs.
- Container names changed in v4.0: Caddy is `agent0-N-mhs`, homeserver is `agent0-N-continuwuity`.
