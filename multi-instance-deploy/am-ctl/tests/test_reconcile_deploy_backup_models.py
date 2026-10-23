"""Tests for Phase 4 Reconciler, Phase 5 Backups, Phase 6 Deployer, and Phase 7 Model Manager."""

import hashlib
import json
from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.schemas.agent import ContainerStatus, MatrixIdentity, ProcessInfo
from amctl.services import backup, deployer, model_manager, reconciler
from tests.conftest import API_HEADERS


def _setup_fake_filesystem(tmp_path: Path, monkeypatch) -> tuple[Path, Path, Path]:
    """Create temporary template, instance, release, and backup directories for safe testing."""
    tpl_base = tmp_path / "templates"
    inst_base = tmp_path / "instances"
    rel_dir = tmp_path / "releases"
    bak_dir = tmp_path / "backups"

    (tpl_base / "matrix-bot").mkdir(parents=True)
    (tpl_base / "scripts").mkdir(parents=True)
    rel_dir.mkdir(parents=True)
    bak_dir.mkdir(parents=True)

    tracked = {
        "matrix-bot-rust": (tpl_base / "matrix-bot" / "matrix-bot-rust", "usr/workdir/matrix-bot/matrix-bot-rust"),
        "run-bot-wrapper.sh": (tpl_base / "matrix-bot" / "run-bot-wrapper.sh", "usr/workdir/matrix-bot/run-bot-wrapper.sh"),
        "run-matrix-bot.sh": (tpl_base / "matrix-bot" / "run-matrix-bot.sh", "usr/workdir/matrix-bot/run-matrix-bot.sh"),
        "derive-a0-token.sh": (tpl_base / "scripts" / "derive-a0-token.sh", "usr/workdir/derive-a0-token.sh"),
        "preflight-check.sh": (tpl_base / "scripts" / "preflight-check.sh", "usr/workdir/preflight-check.sh"),
        "watchdog.sh": (tpl_base / "scripts" / "watchdog.sh", "usr/workdir/watchdog.sh"),
        "startup-services.sh": (tpl_base / "scripts" / "startup-services.sh", "usr/workdir/startup-services.sh"),
    }

    for label, (src, _) in tracked.items():
        src.write_text(f"#!/bin/bash\n# canonical {label}\n")
        src.chmod(0o755)

    for idx in (1, 2):
        aname = f"agent0-{idx}"
        adir = inst_base / aname
        (adir / "usr" / "workdir" / "matrix-bot").mkdir(parents=True)
        (adir / "usr" / "workdir" / "matrix-mcp-server").mkdir(parents=True)
        (adir / "mhs").mkdir(parents=True)
        (adir / ".env").write_text(
            f"A0_SET_agent_profile=agent0\nAPI_KEY_OPENROUTER=sk-or-test\nAPI_KEY_ANTHROPIC=sk-ant-test\n"
        )
        (adir / "docker-compose.yml").write_text(
            f"services:\n  agent-zero:\n    image: agent0ai/agent-zero:v2.14\n"
        )
        (adir / "usr" / "settings.json").write_text("{}")
        (adir / "usr" / "workdir" / "matrix-bot" / ".env").write_text("MATRIX_ACCESS_TOKEN=syt_tok\n")
        (adir / "usr" / "workdir" / "matrix-bot" / "room_contexts.json").write_text('{"!r:v-site.net": "ctx-1"}\n')
        (adir / "usr" / "workdir" / "matrix-mcp-server" / ".env").write_text("MATRIX_ACCESS_TOKEN=syt_tok\n")
        for label, (src, rel_dst) in tracked.items():
            dst = adir / rel_dst
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    monkeypatch.setattr(reconciler, "TEMPLATE_BASE", tpl_base)
    monkeypatch.setattr(reconciler, "INSTANCE_BASE", inst_base)
    monkeypatch.setattr(reconciler, "TRACKED_ARTIFACTS", tracked)
    monkeypatch.setattr(deployer, "RELEASES_DIR", rel_dir)
    monkeypatch.setattr(deployer, "INSTANCE_BASE", inst_base)
    monkeypatch.setattr(deployer, "TRACKED_ARTIFACTS", tracked)
    monkeypatch.setattr(model_manager, "INSTANCE_BASE", inst_base)
    monkeypatch.setattr(backup, "BACKUP_ROOT", bak_dir)

    return tpl_base, inst_base, bak_dir


def _mock_clean_agent_probes(monkeypatch):
    async def mock_whoami(name: str, url: str):
        return MatrixIdentity(user_id=f"@{name}:{name}-mhs.cybertribe.com", device_id="D1")

    async def mock_rooms(name: str, url: str):
        return True, ["!gahcrWFWAUJQPPkuQy:v-site.net"], None

    async def mock_derive_fp(name: str):
        idx = name.split("-")[-1]
        return f"fp000000000{idx}", None

    async def mock_read_key(name: str):
        # Produce a string whose sha256[:12] matches or mock check_agent_drift
        return f"key-{name}", "secret_file"

    async def mock_a0(name: str, expected_fingerprint=None):
        return "pass", {"http_code": 400}

    async def mock_mcp(name: str):
        return "pass", {"status": "healthy", "version": "0.1.1"}

    async def mock_proc(name: str):
        return ProcessInfo(bot_count=1, bot_runtime="rust", mcp_running=True, watchdog_running=True, supervisord_running=True)

    async def mock_containers(name: str):
        return [
            ContainerStatus(name=name, running=True),
            ContainerStatus(name=f"{name}-continuwuity", running=True),
            ContainerStatus(name=f"{name}-mhs", running=True),
        ]

    async def mock_secret_info(name: str):
        return {"secret_file_exists": True, "mode": "600", "owner": "root:root", "size": 16, "env_has_a0_api_key": False}

    monkeypatch.setattr(reconciler, "get_whoami", mock_whoami)
    monkeypatch.setattr(reconciler, "get_joined_rooms", mock_rooms)
    monkeypatch.setattr(reconciler, "derive_canonical_a0_fingerprint", mock_derive_fp)
    monkeypatch.setattr(reconciler, "_read_bot_a0_key", mock_read_key)
    monkeypatch.setattr(reconciler, "check_a0_auth", mock_a0)
    monkeypatch.setattr(reconciler, "check_mcp_health", mock_mcp)
    monkeypatch.setattr(reconciler, "get_process_info", mock_proc)
    monkeypatch.setattr(reconciler, "get_container_status", mock_containers)
    monkeypatch.setattr(reconciler, "_inspect_secret_delivery", mock_secret_info)


@pytest.mark.asyncio
async def test_reconciler_check_plan_apply_and_history(
    client: AsyncClient, db_session: AsyncSession, tmp_path: Path, monkeypatch
):
    _, inst_base, _ = _setup_fake_filesystem(tmp_path, monkeypatch)
    _mock_clean_agent_probes(monkeypatch)

    # Align canonical fingerprint with sha256("key-agent0-X")[:12]
    from amctl.models.credential import CredentialFingerprint
    from sqlalchemy import select

    fps = (await db_session.execute(select(CredentialFingerprint))).scalars().all()
    for fp in fps:
        aname = f"agent0-{fp.agent_id}"
        fp.fingerprint = hashlib.sha256(f"key-{aname}".encode()).hexdigest()[:12]
    await db_session.commit()

    async def mock_derive_exact(name: str):
        return hashlib.sha256(f"key-{name}".encode()).hexdigest()[:12], None

    monkeypatch.setattr(reconciler, "derive_canonical_a0_fingerprint", mock_derive_exact)

    # 1. Clean fleet check
    r_chk = await client.post("/api/v1/reconcile/check", headers=API_HEADERS)
    assert r_chk.status_code == 200
    assert r_chk.json()["clean_agents"] == 2

    # 2. Tamper with startup-services.sh on agent0-2 -> detect drift, plan, and apply
    tampered = inst_base / "agent0-2" / "usr" / "workdir" / "startup-services.sh"
    tampered.write_text("#!/bin/bash\n# tampered\n")

    r_plan = await client.post("/api/v1/reconcile/plan/agent0-2", headers=API_HEADERS)
    assert r_plan.status_code == 200
    plan_data = r_plan.json()
    assert plan_data["clean"] is False
    assert any(a["action_type"] == "sync_artifacts" for a in plan_data["actions"])

    async def mock_sup(name: str, action: str, prog: str):
        return True, "ok"

    monkeypatch.setattr(reconciler, "supervisor_action", mock_sup)
    monkeypatch.setattr("asyncio.sleep", lambda _: _noop_async())

    r_app = await client.post("/api/v1/reconcile/apply/agent0-2", headers=API_HEADERS)
    assert r_app.status_code == 200
    app_data = r_app.json()
    assert app_data["noop"] is False
    assert app_data["success"] is True
    assert app_data["post_check"]["clean"] is True

    # 3. Second apply on clean agent is a no-op
    r_noop = await client.post("/api/v1/reconcile/apply/agent0-2", headers=API_HEADERS)
    assert r_noop.status_code == 200
    assert r_noop.json()["noop"] is True

    # 4. History endpoint
    r_hist = await client.get("/api/v1/reconcile/history?agent_name=agent0-2", headers=API_HEADERS)
    assert r_hist.status_code == 200
    assert len(r_hist.json()) == 1


async def _noop_async():
    return None


@pytest.mark.asyncio
async def test_deployer_releases_deploy_version_and_status(
    client: AsyncClient, db_session: AsyncSession, tmp_path: Path, monkeypatch
):
    _, inst_base, _ = _setup_fake_filesystem(tmp_path, monkeypatch)
    _mock_clean_agent_probes(monkeypatch)

    from amctl.models.credential import CredentialFingerprint
    from sqlalchemy import select

    fps = (await db_session.execute(select(CredentialFingerprint))).scalars().all()
    for fp in fps:
        aname = f"agent0-{fp.agent_id}"
        fp.fingerprint = hashlib.sha256(f"key-{aname}".encode()).hexdigest()[:12]
    await db_session.commit()

    async def mock_derive_exact(name: str):
        return hashlib.sha256(f"key-{name}".encode()).hexdigest()[:12], None

    monkeypatch.setattr(reconciler, "derive_canonical_a0_fingerprint", mock_derive_exact)

    async def mock_sup(name: str, action: str, prog: str):
        return True, "ok"

    async def mock_run(cmd: list[str], timeout: float = 15.0):
        return 0, "v2.14"

    async def mock_health(session, agent, include_federation=False, operator="test"):
        return {"matrix_auth": {"status": "pass"}, "identity": {"status": "pass"}}

    monkeypatch.setattr(deployer, "supervisor_action", mock_sup)
    monkeypatch.setattr(deployer, "_run", mock_run)
    monkeypatch.setattr(deployer, "get_process_info", reconciler.get_process_info)
    monkeypatch.setattr(deployer, "get_container_status", reconciler.get_container_status)
    monkeypatch.setattr(deployer, "check_mcp_health", reconciler.check_mcp_health)
    monkeypatch.setattr(deployer, "run_agent_health_checks", mock_health)
    monkeypatch.setattr("asyncio.sleep", lambda _: _noop_async())

    # 1. Build and register release v1.2.1
    r_rel = await client.post("/api/v1/releases", headers=API_HEADERS, json={"version": "v1.2.1"})
    assert r_rel.status_code == 200
    assert r_rel.json()["version"] == "v1.2.1"

    r_list = await client.get("/api/v1/releases", headers=API_HEADERS)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1

    # 2. Deploy release v1.2.1 to agent0-2 (verifying instance-local state preserved)
    r_dep = await client.post(
        "/api/v1/deploy/agent0-2",
        headers=API_HEADERS,
        json={"version": "v1.2.1", "operator": "pytest"},
    )
    assert r_dep.status_code == 200
    dep_data = r_dep.json()
    assert dep_data["status"] == "success"
    assert dep_data["preserved_state"]["bot_env_preserved"] is True
    assert dep_data["preserved_state"]["room_contexts_preserved"] is True

    # 3. Update Docker image version (--skip-restart)
    r_ver = await client.post(
        "/api/v1/deploy/agent0-2/version",
        headers=API_HEADERS,
        json={"image_version": "v2.15", "skip_restart": True, "force": False, "operator": "pytest"},
    )
    assert r_ver.status_code == 200
    assert r_ver.json()["compose_updated"] is True
    assert "agent0ai/agent-zero:v2.15" in (inst_base / "agent0-2" / "docker-compose.yml").read_text()

    # 4. Fleet deploy status
    r_st = await client.get("/api/v1/deploy/status", headers=API_HEADERS)
    assert r_st.status_code == 200
    assert r_st.json()["latest_release"] == "v1.2.1"


@pytest.mark.asyncio
async def test_backups_run_verify_and_freshness(
    client: AsyncClient, db_session: AsyncSession, tmp_path: Path, monkeypatch
):
    _, _, bak_dir = _setup_fake_filesystem(tmp_path, monkeypatch)

    async def fake_dump_db(db_name: str, dest_path: Path):
        dest_path.write_bytes(f"PGDMP-{db_name}".encode())
        dest_path.chmod(0o600)
        return True, "ok"

    async def fake_dump_globals(dest_path: Path):
        dest_path.write_text("-- globals\n")
        dest_path.chmod(0o600)
        return True, "ok"

    async def fake_bundle_infra(dest_path: Path):
        dest_path.write_bytes(b"TARGZ")
        dest_path.chmod(0o600)
        return True, "bundled 5 paths"

    async def fake_offsite(local_dir: Path, tier: str):
        return True, f"tarnover:/backups/{tier}/{local_dir.name}"

    async def fake_run(cmd: list[str], timeout: float = 15.0):
        cmd_str = " ".join(cmd)
        if "SELECT count(*) FROM thoughts" in cmd_str:
            return 0, "298"
        if "pg_indexes" in cmd_str:
            return 0, "1"
        if "SELECT count(*) FROM agents" in cmd_str:
            return 0, "5"
        if "pg_database" in cmd_str:
            return 0, "0"
        return 0, "ok"

    monkeypatch.setattr(backup, "_dump_database_custom", fake_dump_db)
    monkeypatch.setattr(backup, "_dump_globals", fake_dump_globals)
    monkeypatch.setattr(backup, "_bundle_infra_configs", fake_bundle_infra)
    monkeypatch.setattr(backup, "sync_to_offsite", fake_offsite)
    monkeypatch.setattr(backup, "_run", fake_run)

    # 1. Run backup suite
    r_run = await client.post("/api/v1/backups/run?backup_type=manual", headers=API_HEADERS)
    assert r_run.status_code == 200
    assert r_run.json()["offsite_synced"] is True
    assert len(r_run.json()["artifacts"]) == 4

    # 2. List backups
    r_list = await client.get("/api/v1/backups", headers=API_HEADERS)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 4

    # 3. Verify backups via scratch-DB restore
    r_ver = await client.post("/api/v1/backups/verify", headers=API_HEADERS)
    assert r_ver.status_code == 200
    vdata = r_ver.json()
    assert vdata["verified"] is True
    assert vdata["open_brain_restored_thoughts"] == 298
    assert vdata["pgvector_index_present"] is True
    assert vdata["scratch_db_cleaned"] is True

    # 4. Freshness check
    r_fresh = await client.post("/api/v1/backups/check-freshness", headers=API_HEADERS)
    assert r_fresh.status_code == 200
    assert r_fresh.json()["status"] == "pass"


@pytest.mark.asyncio
async def test_models_list_set_and_diagnose(
    client: AsyncClient, db_session: AsyncSession, tmp_path: Path, monkeypatch
):
    _setup_fake_filesystem(tmp_path, monkeypatch)

    state = {
        "selected_preset": "Default",
        "available_presets": ["Default", "Efficiency", "Power"],
        "chat_model": "openrouter/moonshotai/kimi-k2.5",
        "utility_model": "openrouter/google/gemini-2.5-flash-lite",
        "embedding_model": "huggingface/sentence-transformers/all-MiniLM-L6-v2",
        "ctx_length": 131072,
        "vision": True,
    }

    async def fake_read_live(name: str):
        return dict(state)

    async def fake_run(cmd: list[str], timeout: float = 15.0):
        return 0, "OK"

    monkeypatch.setattr(model_manager, "_read_live_agent_models", fake_read_live)
    monkeypatch.setattr(model_manager, "_run", fake_run)

    # 1. Get fleet models
    r_list = await client.get("/api/v1/models", headers=API_HEADERS)
    assert r_list.status_code == 200
    assert r_list.json()["online_agents"] == 2

    # 2. Set model & preset for agent0-1
    state["selected_preset"] = "Power"
    state["chat_model"] = "anthropic/claude-sonnet-4-6"
    r_set = await client.put(
        "/api/v1/models/agent0-1",
        headers=API_HEADERS,
        json={"preset": "Power", "chat_model": "anthropic/claude-sonnet-4-6", "operator": "pytest"},
    )
    assert r_set.status_code == 200
    assert r_set.json()["selected_preset"] == "Power"
    assert r_set.json()["chat_model"] == "anthropic/claude-sonnet-4-6"

    # Invalid model format -> 400
    r_bad = await client.put(
        "/api/v1/models/agent0-1",
        headers=API_HEADERS,
        json={"chat_model": "invalid-format-without-slash"},
    )
    assert r_bad.status_code == 400

    # 3. Diagnose fleet models
    r_diag = await client.post("/api/v1/models/diagnose", headers=API_HEADERS)
    assert r_diag.status_code == 200
    assert r_diag.json()["overall_status"] == "pass"
