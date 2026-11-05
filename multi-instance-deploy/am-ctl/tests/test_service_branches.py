"""Additional unit tests for deep branch coverage across matrix, backup, deployer, reconciler, and health_engine."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tarfile
import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.agent import Agent
from amctl.models.backup import BackupRun
from amctl.models.health import AlertRule
from amctl.schemas.agent import ContainerStatus, MatrixIdentity, ProcessInfo
from amctl.services import agent_zero, backup, deployer, docker, health_engine, matrix, model_manager, reconciler
from tests.conftest import API_HEADERS
from tests.test_reconcile_deploy_backup_models import _setup_fake_filesystem


@pytest.mark.asyncio
async def test_matrix_service_branches(monkeypatch, tmp_path):
    # 1. _get_bot_token and _get_mcp_token
    async def fake_run(cmd: list[str], timeout: float = 15.0):
        s = " ".join(cmd)
        if "matrix-bot/.env" in s:
            return 0, "syt_bot_token_123"
        if "matrix-mcp-server/.env" in s:
            return 0, "syt_mcp_token_456"
        if "kubectl get pods" in s:
            return 0, "synapse-0"
        if "_synapse/admin/v1/users" in s:
            return 0, '{"access_token": "syt_admin_inv"}'
        if "/invite" in s:
            return 0, '{"event_id": "$inv1"}'
        return 0, ""

    monkeypatch.setattr(matrix, "_run", fake_run)
    tok_file = tmp_path / "synapse_admin_token"
    tok_file.write_text("admin-tok")
    monkeypatch.setattr(matrix, "SYNAPSE_ADMIN_TOKEN_FILE", tok_file)

    assert await matrix._get_bot_token("agent0-1") == "syt_bot_token_123"
    assert await matrix._get_mcp_token("agent0-1") == "syt_mcp_token_456"

    # Mock httpx.AsyncClient for get_whoami, get_joined_rooms, check_sync_cursor, repair_room_membership, leave_room
    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str, headers=None):
            if "whoami" in url:
                return Response(200, json={"user_id": "@agent0-1:hs", "device_id": "D1"})
            if "joined_rooms" in url:
                return Response(200, json={"joined_rooms": ["!r1:v-site.net"]})
            if "sync" in url:
                return Response(200, json={"next_batch": "b999"})
            return Response(401, json={})

        async def post(self, url: str, headers=None, json=None):
            if "/join/" in url:
                return Response(200, json={"room_id": "!r1:v-site.net"})
            if "/leave" in url:
                return Response(200, json={})
            return Response(400, text="err")

    monkeypatch.setattr(matrix.httpx, "AsyncClient", FakeAsyncClient)

    id_res = await matrix.get_whoami("agent0-1", "https://172.23.89.1:8448")
    assert id_res.user_id == "@agent0-1:hs"

    ok_r, rooms, err_r = await matrix.get_joined_rooms("agent0-1", "https://172.23.89.1:8448")
    assert ok_r is True and rooms == ["!r1:v-site.net"] and err_r is None

    ok_s, s_det = await matrix.check_sync_cursor("agent0-1", "https://172.23.89.1:8448")
    assert ok_s is True and s_det["next_batch"] == "b999"

    rep_ok, rep_det = await matrix.repair_room_membership(
        "agent0-1", "@agent0-1:hs", "https://172.23.89.1:8448", "!r1:v-site.net"
    )
    assert rep_ok is True and rep_det["repaired_room"] == "!r1:v-site.net"

    lv_ok, _ = await matrix.leave_room_as_agent("agent0-1", "https://172.23.89.1:8448", "!r1:v-site.net")
    assert lv_ok is True


@pytest.mark.asyncio
async def test_agent_zero_and_docker_edge_cases(monkeypatch):
    # Test env fallback, missing key, 401 unauthorized, 503 transient, and unhealthy MCP
    responses = [
        (0, "legacykey::env"),
        (0, "401"),
        (0, ""),
        (0, '{"status": "unhealthy"}'),
    ]

    async def fake_run(cmd: list[str], timeout: float = 15.0):
        if responses:
            return responses.pop(0)
        return 1, ""

    monkeypatch.setattr(agent_zero, "_run", fake_run)
    st, det = await agent_zero.check_a0_auth("agent0-1")
    assert st == "fail" and "unauthorized_http_401" in det["error"]

    st2, det2 = await agent_zero.check_a0_auth("agent0-1")
    assert st2 == "fail" and det2["error"] == "missing_a0_api_key"

    mcp_st, mcp_det = await agent_zero.check_mcp_health("agent0-1")
    assert mcp_st == "fail"

    # Real subprocess _run test on `true`
    rc, out = await docker._run(["echo", "hello"])
    assert rc == 0 and out == "hello"


@pytest.mark.asyncio
async def test_health_engine_restartable_and_stale_backup_alerts(
    client: AsyncClient, db_session: AsyncSession, tmp_path: Path, monkeypatch
):
    _, _, bak_dir = _setup_fake_filesystem(tmp_path, monkeypatch)

    # Test RESTARTABLE check failure (e.g. mcp fail -> auto_restart_run_mcp, then exceed max_retries -> open alert)
    restarted = []

    async def mock_sup(name: str, action: str, prog: str):
        restarted.append((name, action, prog))
        return True, "restarted"

    monkeypatch.setattr(health_engine, "supervisor_action", mock_sup)

    for attempt in range(4):
        r = await client.post(
            "/api/v1/health/agent0-1/report",
            headers=API_HEADERS,
            json={"reporter": "watchdog.sh", "checks": [{"check_type": "mcp", "status": "fail", "detail": {"attempt": attempt}}]},
        )
        assert r.status_code == 200

    assert ("agent0-1", "restart", "run_mcp") in restarted

    # Recover mcp -> resolves alert
    r_pass = await client.post(
        "/api/v1/health/agent0-1/report",
        headers=API_HEADERS,
        json={"reporter": "watchdog.sh", "checks": [{"check_type": "mcp", "status": "pass", "detail": {}}]},
    )
    assert r_pass.status_code == 200

    # Test backup helpers: _dump_database_custom, _dump_globals, _bundle_infra_configs, prune_old_backups, sync_to_offsite
    old_dir = bak_dir / "daily" / "2020-01-01"
    old_dir.mkdir(parents=True)
    pruned = backup.prune_old_backups()
    assert str(old_dir) in pruned

    async def fake_backup_run(cmd: list[str], timeout: float = 15.0):
        s = " ".join(cmd)
        if "docker cp" in s:
            dest = Path(cmd[-1])
            dest.write_bytes(b"DUMP_CONTENT")
            return 0, "ok"
        if "pg_dumpall" in s:
            return 0, "CREATE ROLE openbrain;"
        if cmd[0] == "tar":
            dest = Path(cmd[2])
            dest.write_bytes(b"TAR_CONTENT")
            return 0, "ok"
        return 0, "ok"

    monkeypatch.setattr(backup, "_run", fake_backup_run)
    db_file = tmp_path / "test_ob.dump"
    ok_d, _ = await backup._dump_database_custom("open_brain", db_file)
    assert ok_d is True

    gl_file = tmp_path / "globals.sql"
    ok_g, _ = await backup._dump_globals(gl_file)
    assert ok_g is True

    inf_file = tmp_path / "infra.tar.gz"
    ok_i, _ = await backup._bundle_infra_configs(inf_file)
    assert ok_i is True

    ok_sync, _ = await backup.sync_to_offsite(tmp_path, "manual")
    assert ok_sync is True

    # Test stale backup freshness alert
    stale_time = datetime.now(timezone.utc) - timedelta(hours=60)
    db_session.add(BackupRun(
        backup_type="daily_full",
        target="open_brain",
        file_path="/tmp/x",
        size_bytes=10,
        checksum_sha256="abc",
        status="failed",
        created_at=stale_time,
    ))
    await db_session.commit()
    st_f, _ = await backup.check_backup_freshness(db_session)
    assert st_f == "fail"


@pytest.mark.asyncio
async def test_reconciler_and_deployer_additional_branches(
    client: AsyncClient, db_session: AsyncSession, tmp_path: Path, monkeypatch
):
    _, inst_base, _ = _setup_fake_filesystem(tmp_path, monkeypatch)

    # Test reconciler._inspect_secret_delivery directly
    async def fake_stat_run(cmd: list[str], timeout: float = 15.0):
        return 0, "600:root:root:16|0"

    monkeypatch.setattr(reconciler, "_run", fake_stat_run)
    sec_info = await reconciler._inspect_secret_delivery("agent0-1")
    assert sec_info["secret_file_exists"] is True and sec_info["mode"] == "600"

    # Test reconciler drift on secret_delivery (.env has A0_API_KEY) + missing room + process drift
    bot_env = inst_base / "agent0-1" / "usr" / "workdir" / "matrix-bot" / ".env"
    bot_env.write_text("MATRIX_ACCESS_TOKEN=syt_1\nA0_API_KEY=legacy_bad_key\n")

    async def mock_whoami(name: str, url: str):
        return MatrixIdentity(user_id=f"@{name}:{name}-mhs.cybertribe.com", device_id="D1")

    async def mock_rooms_missing(name: str, url: str):
        return True, [], None

    async def mock_derive_fp(name: str):
        return "new_canon_fp", None

    async def mock_read_key(name: str):
        return "legacy_bad_key", "env"

    async def mock_a0(name: str, expected_fingerprint=None):
        return "fail", {"error": "fingerprint_mismatch"}

    async def mock_mcp(name: str):
        return "fail", {"error": "down"}

    async def mock_proc(name: str):
        return ProcessInfo(bot_count=0, bot_runtime=None, mcp_running=False, watchdog_running=True, supervisord_running=True)

    async def mock_containers(name: str):
        return [
            ContainerStatus(name=name, running=True),
            ContainerStatus(name=f"{name}-continuwuity", running=True),
            ContainerStatus(name=f"{name}-mhs", running=True),
        ]

    async def mock_secret_bad(name: str):
        return {"secret_file_exists": False, "mode": None, "owner": None, "size": 0, "env_has_a0_api_key": True}

    monkeypatch.setattr(reconciler, "get_whoami", mock_whoami)
    monkeypatch.setattr(reconciler, "get_joined_rooms", mock_rooms_missing)
    monkeypatch.setattr(reconciler, "derive_canonical_a0_fingerprint", mock_derive_fp)
    monkeypatch.setattr(reconciler, "_read_bot_a0_key", mock_read_key)
    monkeypatch.setattr(reconciler, "check_a0_auth", mock_a0)
    monkeypatch.setattr(reconciler, "check_mcp_health", mock_mcp)
    monkeypatch.setattr(reconciler, "get_process_info", mock_proc)
    monkeypatch.setattr(reconciler, "get_container_status", mock_containers)
    monkeypatch.setattr(reconciler, "_inspect_secret_delivery", mock_secret_bad)

    r_plan = await client.post("/api/v1/reconcile/plan/agent0-1", headers=API_HEADERS)
    assert r_plan.status_code == 200
    action_types = [a["action_type"] for a in r_plan.json()["actions"]]
    assert "remove_env_a0_api_key" in action_types
    assert "derive_canonical_secret" in action_types
    assert "repair_room_membership" in action_types
    assert "restart_service" in action_types

    # Apply all those actions
    async def mock_derive_run(cmd: list[str], timeout: float = 15.0):
        return 0, "new_canon_fp"

    async def mock_repair(name: str, mxid: str, url: str, rid: str):
        return True, {"repaired_room": rid}

    async def mock_sup(name: str, action: str, prog: str):
        return True, "ok"

    monkeypatch.setattr(reconciler, "_run", mock_derive_run)
    monkeypatch.setattr(reconciler, "repair_room_membership", mock_repair)
    monkeypatch.setattr(reconciler, "supervisor_action", mock_sup)
    monkeypatch.setattr("asyncio.sleep", lambda _: _noop())

    r_app = await client.post("/api/v1/reconcile/apply/agent0-1", headers=API_HEADERS)
    assert r_app.status_code == 200
    assert "A0_API_KEY=" not in bot_env.read_text()

    # Also test uploading an existing release tarball path to deployer
    tar_path = tmp_path / "custom-bundle.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        f = tmp_path / "watchdog.sh"
        f.write_text("#!/bin/bash\necho hi\n")
        tf.add(f, arcname="watchdog.sh")

    r_up = await client.post(
        "/api/v1/releases",
        headers=API_HEADERS,
        json={"version": "v1.3.0", "bundle_path": str(tar_path)},
    )
    assert r_up.status_code == 200
    assert r_up.json()["version"] == "v1.3.0"


async def _noop():
    return None
