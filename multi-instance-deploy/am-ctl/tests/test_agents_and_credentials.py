"""Tests for Phase 1 & Phase 3 API endpoints: auth, agents, status, and credentials."""

import hashlib
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.audit import AuditLog
from amctl.models.credential import CredentialFingerprint
from amctl.schemas.agent import ContainerStatus, MatrixIdentity, ProcessInfo
from tests.conftest import API_HEADERS


@pytest.mark.asyncio
async def test_health_unauthenticated_and_api_key_enforcement(client: AsyncClient):
    # /api/v1/health is public
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Protected endpoint without key -> 422/401, with bad key -> 401
    r_bad = await client.get("/api/v1/agents", headers={"X-API-Key": "wrong-key"})
    assert r_bad.status_code == 401

    # Protected endpoint with valid key -> 200
    r_ok = await client.get("/api/v1/agents", headers=API_HEADERS)
    assert r_ok.status_code == 200
    assert len(r_ok.json()) == 2


@pytest.mark.asyncio
async def test_agents_crud_and_audit_log(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    # Get single agent
    r = await client.get("/api/v1/agents/agent0-1", headers=API_HEADERS)
    assert r.status_code == 200
    assert r.json()["matrix_user_id"] == "@agent0-1:agent0-1-mhs.cybertribe.com"

    # 404 on unknown agent
    r404 = await client.get("/api/v1/agents/agent0-99", headers=API_HEADERS)
    assert r404.status_code == 404

    # Update agent release_version & verify audit_log entry
    r_upd = await client.put(
        "/api/v1/agents/agent0-2",
        headers=API_HEADERS,
        json={"release_version": "v1.2.1", "status": "active"},
    )
    assert r_upd.status_code == 200
    assert r_upd.json()["release_version"] == "v1.2.1"

    audits = (await db_session.execute(select(AuditLog).where(AuditLog.action == "agent_update"))).scalars().all()
    assert len(audits) == 1
    assert audits[0].detail["changes"]["release_version"]["new"] == "v1.2.1"

    # Mock live status dependencies for /agents/{name}/status and /status
    async def mock_containers(name: str):
        return [
            ContainerStatus(name=name, running=True, uptime="running"),
            ContainerStatus(name=f"{name}-continuwuity", running=True, uptime="running"),
            ContainerStatus(name=f"{name}-mhs", running=True, uptime="running"),
        ]

    async def mock_proc(name: str):
        return ProcessInfo(bot_count=1, bot_runtime="rust", mcp_running=True, watchdog_running=True, supervisord_running=True)

    async def mock_whoami(name: str, url: str):
        return MatrixIdentity(user_id=f"@{name}:{name}-mhs.cybertribe.com", device_id="DEV1")

    monkeypatch.setattr("amctl.routers.agents.get_container_status", mock_containers)
    monkeypatch.setattr("amctl.routers.agents.get_process_info", mock_proc)
    monkeypatch.setattr("amctl.routers.agents.get_whoami", mock_whoami)

    r_live = await client.get("/api/v1/agents/agent0-1/status", headers=API_HEADERS)
    assert r_live.status_code == 200
    assert r_live.json()["processes"]["bot_count"] == 1

    r_fleet = await client.get("/api/v1/status", headers=API_HEADERS)
    assert r_fleet.status_code == 200
    assert r_fleet.json()["containers_running"] == 2


@pytest.mark.asyncio
async def test_credentials_verify_collisions_and_trusted_senders(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    # Get credentials
    r_cred = await client.get("/api/v1/agents/agent0-1/credentials", headers=API_HEADERS)
    assert r_cred.status_code == 200
    assert r_cred.json()["credentials"][0]["fingerprint"] == "fp0000000001"

    # Verify credentials (matching canonical & deployed key + sync registry)
    raw_token = "canonical-secret-token-value"
    expected_fp = hashlib.sha256(raw_token.encode()).hexdigest()[:12]

    async def mock_derive(name: str):
        return expected_fp, None

    async def mock_read_key(name: str):
        return raw_token, "secret_file"

    async def mock_check_a0(name: str, expected_fingerprint=None):
        return "pass", {"http_code": 400, "fingerprint": expected_fp, "source": "secret_file"}

    monkeypatch.setattr("amctl.routers.credentials.derive_canonical_a0_fingerprint", mock_derive)
    monkeypatch.setattr("amctl.routers.credentials._read_bot_a0_key", mock_read_key)
    monkeypatch.setattr("amctl.routers.credentials.check_a0_auth", mock_check_a0)

    r_ver = await client.post("/api/v1/agents/agent0-1/credentials/verify?sync_registry=true", headers=API_HEADERS)
    assert r_ver.status_code == 200
    assert r_ver.json()["valid"] is True
    assert r_ver.json()["registry_fingerprint"] == expected_fp

    # Introduce a collision across agent0-1 and agent0-2 and test /credentials/collisions
    fps = (await db_session.execute(select(CredentialFingerprint))).scalars().all()
    for fp in fps:
        fp.fingerprint = "colliding_fp1"
    await db_session.commit()

    r_col = await client.get("/api/v1/credentials/collisions", headers=API_HEADERS)
    assert r_col.status_code == 200
    assert r_col.json()["has_collisions"] is True
    assert r_col.json()["collisions"][0]["agents"] == ["agent0-1", "agent0-2"]

    # Trusted senders list
    r_ts = await client.get("/api/v1/trusted-senders", headers=API_HEADERS)
    assert r_ts.status_code == 200
    assert len(r_ts.json()) == 2
