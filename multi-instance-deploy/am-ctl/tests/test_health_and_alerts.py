"""Tests for Phase 2 health engine, docker/matrix/agent_zero probes, auto-repair, and alerts."""

import json
import time
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.schemas.agent import ContainerStatus, MatrixIdentity, ProcessInfo
from amctl.services import agent_zero, docker, matrix
from tests.conftest import API_HEADERS


@pytest.mark.asyncio
async def test_low_level_docker_agent_zero_and_matrix_probes(monkeypatch, tmp_path):
    # Test docker.get_container_status and get_process_info
    async def fake_run(cmd: list[str], timeout: float = 15.0):
        cmd_str = " ".join(cmd)
        if "docker inspect --format" in cmd_str:
            return 0, '{"running": true, "status": "running", "started": "2026-10-18T00:00:00Z"}'
        if "docker ps" in cmd_str:
            return 0, "agent0-1"
        if "pgrep -fc '[m]atrix-bot-rust'" in cmd_str:
            return 0, "1"
        if "pgrep -fc '[m]atrix-mcp-server-r2" in cmd_str:
            return 0, "1"
        if "pgrep -fc '[w]atchdog'" in cmd_str:
            return 0, "1"
        if "/proc/1/cmdline" in cmd_str:
            return 0, "/usr/bin/supervisord -n"
        if "supervisorctl" in cmd_str:
            return 0, "run_bot: started"
        if ".a0-api-key" in cmd_str:
            return 0, "secret123::secret_file"
        if "create_auth_token" in cmd_str:
            return 0, "fcf730b6d952"
        if "http://localhost:80/api/api_message" in cmd_str:
            return 0, "400"
        if "http://localhost:3000/health" in cmd_str:
            return 0, '{"status": "healthy", "version": "0.1.1"}'
        if "kubectl get pods" in cmd_str:
            return 0, "matrix-synapse-0"
        if "_matrix/key/v2/query/" in cmd_str:
            # Verify minimum_valid_until_ts parameter is included
            assert "minimum_valid_until_ts=" in cmd_str
            future_ts = int((time.time() + 5 * 86400) * 1000)
            return 0, json.dumps({
                "server_keys": [{
                    "valid_until_ts": future_ts,
                    "verify_keys": {"ed25519:key1": {"key": "abc"}},
                }]
            })
        return 0, ""

    monkeypatch.setattr(docker, "_run", fake_run)
    monkeypatch.setattr(agent_zero, "_run", fake_run)
    monkeypatch.setattr(matrix, "_run", fake_run)

    tok_file = tmp_path / "synapse_admin_token"
    tok_file.write_text("synapse-admin-tok")
    monkeypatch.setattr(matrix, "SYNAPSE_ADMIN_TOKEN_FILE", tok_file)

    c_status = await docker.get_container_status("agent0-1")
    assert len(c_status) == 3 and all(c.running for c in c_status)

    p_info = await docker.get_process_info("agent0-1")
    assert p_info is not None and p_info.bot_count == 1 and p_info.supervisord_running

    sup_ok, _ = await docker.supervisor_action("agent0-1", "restart", "run_bot")
    assert sup_ok is True

    fp, err = await agent_zero.derive_canonical_a0_fingerprint("agent0-1")
    assert fp == "fcf730b6d952" and err is None

    a0_st, a0_det = await agent_zero.check_a0_auth("agent0-1")
    assert a0_st == "pass" and a0_det["http_code"] == 400

    mcp_st, mcp_det = await agent_zero.check_mcp_health("agent0-1")
    assert mcp_st == "pass"

    fed_st, fed_det = await matrix.check_and_refresh_federation_keys("agent0-1-mhs.cybertribe.com")
    assert fed_st == "pass"
    assert fed_det["keys"][0]["days_remaining"] > 2.0


@pytest.mark.asyncio
async def test_health_engine_healthy_auto_repair_and_terminal_stop(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    # 1. All checks passing + membership auto-repair when a required room is missing
    async def mock_whoami(name: str, url: str):
        return MatrixIdentity(user_id=f"@{name}:{name}-mhs.cybertribe.com", device_id="D1")

    async def mock_joined_rooms(name: str, url: str):
        # Simulate missing required room on agent0-1 so auto-repair triggers
        if name == "agent0-1":
            return True, [], None
        return True, ["!gahcrWFWAUJQPPkuQy:v-site.net"], None

    async def mock_repair_room(name: str, mxid: str, url: str, room_id: str):
        return True, {"repaired_room": room_id, "user_id": mxid}

    async def mock_a0(name: str, expected_fingerprint=None):
        return "pass", {"http_code": 400, "fingerprint": expected_fingerprint, "source": "secret_file"}

    async def mock_mcp(name: str):
        return "pass", {"status": "healthy"}

    async def mock_proc(name: str):
        return ProcessInfo(bot_count=1, bot_runtime="rust", mcp_running=True, watchdog_running=True, supervisord_running=True)

    async def mock_containers(name: str):
        return [
            ContainerStatus(name=name, running=True),
            ContainerStatus(name=f"{name}-continuwuity", running=True),
            ContainerStatus(name=f"{name}-mhs", running=True),
        ]

    async def mock_sync(name: str, url: str):
        return True, {"next_batch": "s1234"}

    async def mock_fed(fqdn: str):
        return "pass", {"fqdn": fqdn, "keys": [{"key_id": "ed25519:1", "days_remaining": 6.5}]}

    monkeypatch.setattr("amctl.services.health_engine.get_whoami", mock_whoami)
    monkeypatch.setattr("amctl.services.health_engine.get_joined_rooms", mock_joined_rooms)
    monkeypatch.setattr("amctl.services.health_engine.repair_room_membership", mock_repair_room)
    monkeypatch.setattr("amctl.services.health_engine.check_a0_auth", mock_a0)
    monkeypatch.setattr("amctl.services.health_engine.check_mcp_health", mock_mcp)
    monkeypatch.setattr("amctl.services.health_engine.get_process_info", mock_proc)
    monkeypatch.setattr("amctl.services.health_engine.get_container_status", mock_containers)
    monkeypatch.setattr("amctl.services.health_engine.check_sync_cursor", mock_sync)
    monkeypatch.setattr("amctl.services.health_engine.check_and_refresh_federation_keys", mock_fed)

    r_chk = await client.post("/api/v1/health/agent0-1/check", headers=API_HEADERS)
    assert r_chk.status_code == 200
    body = r_chk.json()
    assert body["overall_status"] == "pass"
    assert body["checks"]["membership"]["detail"]["auto_repaired"] == ["!gahcrWFWAUJQPPkuQy:v-site.net"]

    # 2. Report a TERMINAL_CONFIG failure via POST /api/v1/health/agent0-2/report -> stops bot and opens alert
    stopped_calls = []

    async def mock_sup(name: str, action: str, prog: str):
        stopped_calls.append((name, action, prog))
        return True, "stopped"

    monkeypatch.setattr("amctl.services.health_engine.supervisor_action", mock_sup)

    r_rep = await client.post(
        "/api/v1/health/agent0-2/report",
        headers=API_HEADERS,
        json={
            "reporter": "preflight-check.sh",
            "checks": [
                {"check_type": "identity", "status": "fail", "detail": {"actual": "@agent0-2-mcp:...", "expected": "@agent0-2:..."}}
            ],
        },
    )
    assert r_rep.status_code == 200
    assert r_rep.json()["overall_status"] == "fail"
    assert ("agent0-2", "stop", "run_bot") in stopped_calls

    # Verify alert opened and can be acknowledged
    r_alerts = await client.get("/api/v1/alerts?status=open", headers=API_HEADERS)
    assert r_alerts.status_code == 200
    open_alerts = r_alerts.json()
    assert len(open_alerts) == 1
    alert_id = open_alerts[0]["id"]

    r_ack = await client.post(
        f"/api/v1/alerts/{alert_id}/ack",
        headers=API_HEADERS,
        json={"operator": "pytest"},
    )
    assert r_ack.status_code == 200
    assert r_ack.json()["status"] == "acked"

    # Fleet health endpoint & history & rules
    r_fleet = await client.get("/api/v1/health/fleet", headers=API_HEADERS)
    assert r_fleet.status_code == 200
    assert r_fleet.json()["total_agents"] == 2

    r_hist = await client.get("/api/v1/health/agent0-1/history", headers=API_HEADERS)
    assert r_hist.status_code == 200
    assert len(r_hist.json()) >= 8

    r_rules = await client.get("/api/v1/health/rules/all", headers=API_HEADERS)
    assert r_rules.status_code == 200
    assert len(r_rules.json()) == 8
