"""AgentZero and MCP server probes inside agent containers."""

import hashlib
import json
import logging

from amctl.services.docker import _run

logger = logging.getLogger(__name__)


async def _read_bot_a0_key(agent_name: str) -> tuple[str, str]:
    """Read the bot's Agent Zero API credential inside the container.
    Prefers /a0/usr/workdir/matrix-bot/.a0-api-key (Phase 3), falling back
    to /a0/usr/workdir/matrix-bot/.env only for not-yet-migrated nodes.
    Returns (token, source: 'secret_file' | 'env' | 'missing').
    """
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c",
        "if [ -s /a0/usr/workdir/matrix-bot/.a0-api-key ]; then "
        "  cat /a0/usr/workdir/matrix-bot/.a0-api-key && echo '::secret_file'; "
        "elif grep -q '^A0_API_KEY=' /a0/usr/workdir/matrix-bot/.env 2>/dev/null; then "
        "  grep '^A0_API_KEY=' /a0/usr/workdir/matrix-bot/.env | tail -n1 | cut -d= -f2- | tr -d '\\r\\n' && echo '::env'; "
        "fi",
    ])
    raw = out.strip() if rc == 0 else ""
    if "::secret_file" in raw:
        return raw.split("::secret_file")[0].strip(), "secret_file"
    if "::env" in raw:
        return raw.split("::env")[0].strip(), "env"
    return "", "missing"


async def derive_canonical_a0_fingerprint(agent_name: str) -> tuple[str | None, str | None]:
    """Derive the canonical Agent Zero token fingerprint directly via /opt/venv-a0
    create_auth_token() inside the container without exposing the plaintext secret.
    Returns (fingerprint, error).
    """
    rc, out = await _run([
        "docker", "exec", agent_name,
        "/opt/venv-a0/bin/python", "-c",
        "import sys, hashlib; sys.path.insert(0, '/a0'); "
        "from helpers.settings import create_auth_token; "
        "tok = create_auth_token(); "
        "print(hashlib.sha256(tok.encode()).hexdigest()[:12])",
    ], timeout=20.0)
    if rc == 0 and out.strip():
        return out.strip().splitlines()[-1].strip(), None
    return None, out or "derive_failed"


async def check_a0_auth(agent_name: str, expected_fingerprint: str | None = None) -> tuple[str, dict]:
    """Probe Agent Zero API inside the container using the bot's configured A0 credential.
    Returns (status: 'pass' | 'warn' | 'fail', detail).
    """
    bot_key, key_source = await _read_bot_a0_key(agent_name)
    if not bot_key:
        return "fail", {"error": "missing_a0_api_key", "source": key_source}

    fingerprint = hashlib.sha256(bot_key.encode()).hexdigest()[:12]
    if expected_fingerprint and fingerprint != expected_fingerprint:
        return "fail", {
            "error": "fingerprint_mismatch",
            "source": key_source,
            "actual_fingerprint": fingerprint,
            "expected_fingerprint": expected_fingerprint,
        }

    # Probe /api/api_message with empty body:
    # - 401/403 means invalid credential
    # - 400/422/200 means credential passed authentication gate
    rc, code_out = await _run([
        "docker", "exec", agent_name,
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "-X", "POST", "http://localhost:80/api/api_message",
        "-H", "Content-Type: application/json",
        "-H", f"X-API-KEY: {bot_key}",
        "-d", "{}",
    ])
    http_code = code_out.strip()
    if http_code in ("200", "400", "422"):
        return "pass", {"http_code": int(http_code), "fingerprint": fingerprint, "source": key_source}
    if http_code in ("401", "403"):
        return "fail", {"error": f"unauthorized_http_{http_code}", "fingerprint": fingerprint, "source": key_source}
    if http_code in ("000", "502", "503", "504", ""):
        return "warn", {"error": f"transient_http_{http_code or 'timeout'}", "fingerprint": fingerprint, "source": key_source}
    return "fail", {"error": f"unexpected_http_{http_code}", "fingerprint": fingerprint, "source": key_source}


async def check_mcp_health(agent_name: str) -> tuple[str, dict]:
    """Probe the MCP server /health endpoint inside the agent container."""
    rc, out = await _run([
        "docker", "exec", agent_name,
        "curl", "-sf", "--max-time", "10", "http://localhost:3000/health",
    ])
    if rc != 0 or not out:
        return "fail", {"error": "mcp_health_unreachable"}

    try:
        data = json.loads(out)
        if data.get("status") == "healthy":
            return "pass", data
        return "fail", {"error": "unhealthy_status", "response": data}
    except json.JSONDecodeError:
        if "healthy" in out:
            return "pass", {"raw": out}
        return "fail", {"error": "invalid_health_response", "raw": out[:200]}
