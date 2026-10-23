"""Matrix HTTP and Synapse admin client for identity, membership, and federation queries."""

import json
import logging
import time
import urllib.parse
from pathlib import Path

import httpx

from amctl.schemas.agent import MatrixIdentity
from amctl.services.docker import _run

logger = logging.getLogger(__name__)

SYNAPSE_ADMIN_TOKEN_FILE = Path("/home/l0r3zz/agent-matrix-repo/multi-instance-deploy/scripts/synapse_admin_token")


async def _get_bot_token(agent_name: str) -> str | None:
    """Read the bot's Matrix access token from inside the container."""
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c",
        "grep '^MATRIX_ACCESS_TOKEN=' /a0/usr/workdir/matrix-bot/.env 2>/dev/null | cut -d= -f2",
    ])
    token = out.strip() if rc == 0 else None
    if token and token != "PENDING_REGISTRATION":
        return token
    return None


async def _get_mcp_token(agent_name: str) -> str | None:
    """Read the MCP server's Matrix access token from inside the container."""
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c",
        "grep '^MATRIX_ACCESS_TOKEN=' /a0/usr/workdir/matrix-mcp-server/.env 2>/dev/null | cut -d= -f2",
    ])
    token = out.strip() if rc == 0 else None
    if token and token != "PENDING_REGISTRATION":
        return token
    return None


def _internal_hs_url(homeserver_url: str) -> str:
    """Use the internal HTTP port (8008) for direct access, not the TLS port."""
    return homeserver_url.replace("https://", "http://").replace(":8448", ":8008")


async def get_whoami(agent_name: str, homeserver_url: str) -> MatrixIdentity:
    """Call /whoami on the agent's homeserver using its bot token."""
    token = await _get_bot_token(agent_name)
    if not token:
        return MatrixIdentity(error="no_token")

    internal_url = _internal_hs_url(homeserver_url)

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(
                f"{internal_url}/_matrix/client/v3/account/whoami",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return MatrixIdentity(
                    user_id=data.get("user_id"),
                    device_id=data.get("device_id"),
                )
            return MatrixIdentity(error=f"http_{resp.status_code}")
    except httpx.HTTPError as e:
        logger.warning("whoami failed for %s: %s", agent_name, e)
        return MatrixIdentity(error=str(e))


async def get_joined_rooms(agent_name: str, homeserver_url: str) -> tuple[bool, list[str], str | None]:
    """Return (ok, room_ids, error) from the agent's local Continuwuity homeserver."""
    token = await _get_bot_token(agent_name)
    if not token:
        return False, [], "no_token"

    internal_url = _internal_hs_url(homeserver_url)
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(
                f"{internal_url}/_matrix/client/v3/joined_rooms",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return True, data.get("joined_rooms", []), None
            return False, [], f"http_{resp.status_code}"
    except httpx.HTTPError as e:
        return False, [], str(e)


async def check_sync_cursor(agent_name: str, homeserver_url: str) -> tuple[bool, dict]:
    """Verify Matrix /sync endpoint responds with a valid next_batch cursor."""
    token = await _get_bot_token(agent_name)
    if not token:
        return False, {"error": "no_token"}

    internal_url = _internal_hs_url(homeserver_url)
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(
                f"{internal_url}/_matrix/client/v3/sync?timeout=0",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                next_batch = data.get("next_batch")
                if next_batch is not None:
                    return True, {"next_batch": str(next_batch)}
                return False, {"error": "missing_next_batch"}
            return False, {"error": f"http_{resp.status_code}"}
    except httpx.HTTPError as e:
        return False, {"error": str(e)}


async def _get_synapse_pod_and_token() -> tuple[str | None, str | None]:
    """Locate the Synapse pod in K8s and read the admin token."""
    if not SYNAPSE_ADMIN_TOKEN_FILE.exists():
        return None, None
    admin_token = SYNAPSE_ADMIN_TOKEN_FILE.read_text().strip()
    rc, pod = await _run([
        "kubectl", "get", "pods", "-n", "matrix",
        "-l", "app.kubernetes.io/instance=matrix-synapse,app.kubernetes.io/name=matrix",
        "-o", "jsonpath={.items[0].metadata.name}",
    ])
    if rc != 0 or not pod:
        return None, None
    return pod.strip(), admin_token


async def check_and_refresh_federation_keys(homeserver_fqdn: str) -> tuple[str, dict]:
    """Query Synapse notary for the agent homeserver's signing keys.
    Uses minimum_valid_until_ts (now + 2 days) to force Synapse to refresh its
    cached keys from Continuwuity before the 2-day warning threshold is crossed.
    Returns (status: 'pass' | 'warn' | 'fail', detail).
    """
    pod, admin_token = await _get_synapse_pod_and_token()
    if not pod or not admin_token:
        return "warn", {"error": "synapse_pod_or_token_unavailable"}

    min_valid_ms = int((time.time() + 2 * 86400) * 1000)
    rc, out = await _run([
        "kubectl", "exec", "-n", "matrix", pod, "-c", "matrix", "--",
        "curl", "-sf", "--max-time", "15",
        f"http://localhost:8008/_matrix/key/v2/query/{homeserver_fqdn}?minimum_valid_until_ts={min_valid_ms}",
        "-H", f"Authorization: Bearer {admin_token}",
    ], timeout=20.0)

    if rc != 0 or not out:
        return "fail", {"error": "notary_query_failed", "fqdn": homeserver_fqdn}

    try:
        data = json.loads(out)
        server_keys = data.get("server_keys", [])
        if not server_keys:
            return "fail", {"error": "no_server_keys", "fqdn": homeserver_fqdn}

        keys_info = []
        expiring_soon = False
        now = time.time()
        for k in server_keys:
            vu = k.get("valid_until_ts", 0)
            days_left = (vu / 1000.0 - now) / 86400.0 if vu else 0
            if 0 < days_left < 2:
                expiring_soon = True
            for kid in k.get("verify_keys", {}):
                keys_info.append({
                    "key_id": kid,
                    "valid_until_ts": vu,
                    "days_remaining": round(days_left, 2),
                })

        status = "warn" if expiring_soon else "pass"
        return status, {"fqdn": homeserver_fqdn, "keys": keys_info}
    except json.JSONDecodeError:
        return "fail", {"error": "invalid_notary_json", "fqdn": homeserver_fqdn}


async def repair_room_membership(
    agent_name: str,
    matrix_user_id: str,
    homeserver_url: str,
    room_id: str,
) -> tuple[bool, dict]:
    """Auto-repair missing room membership:
    1. Obtain @admin:v-site.net token via Synapse admin API
    2. Send room invite from @admin:v-site.net to matrix_user_id
    3. Accept invite on agent's Continuwuity homeserver using bot token
    """
    pod, admin_token = await _get_synapse_pod_and_token()
    if not pod or not admin_token:
        return False, {"error": "synapse_pod_or_token_unavailable"}

    bot_token = await _get_bot_token(agent_name)
    if not bot_token:
        return False, {"error": "no_bot_token"}

    # Step 1: Obtain @admin:v-site.net access token
    rc, login_out = await _run([
        "kubectl", "exec", "-n", "matrix", pod, "-c", "matrix", "--",
        "curl", "-s", "--max-time", "10", "-X", "POST",
        "http://localhost:8008/_synapse/admin/v1/users/%40admin%3Av-site.net/login",
        "-H", f"Authorization: Bearer {admin_token}",
        "-H", "Content-Type: application/json",
        "-d", "{}",
    ])
    if rc != 0 or not login_out:
        return False, {"error": "admin_login_failed"}

    try:
        invite_token = json.loads(login_out).get("access_token")
    except json.JSONDecodeError:
        invite_token = None

    if not invite_token:
        return False, {"error": "no_admin_invite_token"}

    # Step 2: Send invite from @admin:v-site.net
    encoded_room = urllib.parse.quote(room_id, safe="")
    rc, invite_out = await _run([
        "kubectl", "exec", "-n", "matrix", pod, "-c", "matrix", "--",
        "curl", "-s", "--max-time", "30", "-X", "POST",
        f"http://localhost:8008/_matrix/client/v3/rooms/{encoded_room}/invite",
        "-H", f"Authorization: Bearer {invite_token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"user_id": matrix_user_id}),
    ], timeout=35.0)

    invite_err = None
    if invite_out:
        try:
            invite_data = json.loads(invite_out)
            invite_err = invite_data.get("errcode")
        except json.JSONDecodeError:
            pass

    # M_FORBIDDEN "already in the room" on Synapse side can happen during split membership;
    # still attempt local join in case invite is already pending or state is recoverable.
    if invite_err and invite_err != "M_FORBIDDEN":
        return False, {"error": "invite_failed", "errcode": invite_err, "raw": invite_out}

    # Step 3: Accept invite on agent's Continuwuity homeserver
    internal_url = _internal_hs_url(homeserver_url)
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.post(
                f"{internal_url}/_matrix/client/v3/join/{encoded_room}",
                headers={"Authorization": f"Bearer {bot_token}"},
                json={},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("room_id"):
                    return True, {"repaired_room": data["room_id"], "user_id": matrix_user_id}
            return False, {"error": f"join_http_{resp.status_code}", "body": resp.text[:200]}
    except httpx.HTTPError as e:
        return False, {"error": f"join_exception: {e}"}


async def leave_room_as_agent(agent_name: str, homeserver_url: str, room_id: str) -> tuple[bool, str]:
    """Helper to make an agent leave a room on its homeserver."""
    bot_token = await _get_bot_token(agent_name)
    if not bot_token:
        return False, "no_bot_token"
    encoded_room = urllib.parse.quote(room_id, safe="")
    internal_url = _internal_hs_url(homeserver_url)
    try:
        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            resp = await client.post(
                f"{internal_url}/_matrix/client/v3/rooms/{encoded_room}/leave",
                headers={"Authorization": f"Bearer {bot_token}"},
                json={},
            )
            return resp.status_code == 200, resp.text
    except httpx.HTTPError as e:
        return False, str(e)
