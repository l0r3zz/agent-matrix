"""Recorder and reader tests. They do not need a live fleet agent."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from click.testing import CliRunner
from sqlalchemy import func, select

from amctl.config import settings
from amctl.models.audit import AuditLog
from amctl.models.oplog import OperationalRun, OperationalStage
from amctl.oplog import record
from amctl.oplog.cli import main as oplog_main
from amctl.oplog.track import tracked
from amctl.provision import CmdResult, ProvisionError, Timeouts, provision_agent
from amctl.routers.credentials import verify_agent_credentials
from amctl.services.backup import execute_backup_suite
from amctl.services.deployer import deploy_release_to_agent
from amctl.services.health_engine import run_agent_health_checks
from amctl.services.matrix import repair_room_membership
from amctl.services.model_manager import set_agent_model_config
from amctl.services.reconciler import apply_agent_reconciliation
from amctl_cli.cli import main as cli_main
from amctl_cli.client import AmCtlClient
from test_provision import TEMPLATE_DIR, FakeHost

FAST = Timeouts(homeserver=1, derive=1, supervisord=1, health=1, interval=0)
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "decommission-instance.sh"
HEADERS = {"X-API-Key": settings.api_key}


@pytest.fixture(autouse=True)
def oplog_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "oplog_dir", str(tmp_path))
    return tmp_path


def test_redact_replaces_secrets_before_print(capsys):
    printed = record.terminal_line(
        "Authorization: Bearer super-secret-token syt_abc.def sk-or-v1-xyz MATRIX_PASSWORD=hunter2"
    )
    assert capsys.readouterr().out.strip() == printed
    assert "super-secret-token" not in printed
    assert "syt_abc.def" not in printed
    assert "sk-or-v1-xyz" not in printed
    assert "hunter2" not in printed
    assert "Bearer [redacted]" in printed
    assert "[redacted]" in printed
    assert "MATRIX_PASSWORD=[redacted]" in printed


def test_tail_keeps_at_most_8kib_and_marks_truncated():
    text = "a" * 9000
    kept, cut = record.bound_stream(text)
    assert cut is True
    assert len(kept.encode("utf-8")) <= record.TAIL_LIMIT


@pytest.mark.asyncio
async def test_start_is_readable_before_the_stage_finishes(db_session, client):
    run = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    await record.write_stage(db_session, run.run_id, "files_prepared", "start", "INFO", "Preparing instance files.")
    response = await client.get(f"/api/v1/runs/{run.run_id}", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] is None
    assert body["target"] == "agent0-6"
    assert body["stages"][0]["phase"] == "start"
    assert body["stages"][0]["observed_at"]
    assert "stdout_tail" not in json.dumps(
        (await client.get("/api/v1/runs", headers=HEADERS)).json()[0]
    )


@pytest.mark.asyncio
async def test_unknown_run_is_not_found_and_audit_log_is_unchanged(db_session, client):
    before = await db_session.scalar(select(func.count()).select_from(AuditLog))
    run = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    after = await db_session.scalar(select(func.count()).select_from(AuditLog))
    assert before == after
    missing = await client.get("/api/v1/runs/does-not-exist", headers=HEADERS)
    assert missing.status_code == 404
    assert missing.json() == {"outcome": "not_found", "run_id": "does-not-exist", "stages": []}
    still = await client.get(f"/api/v1/runs/{run.run_id}", headers=HEADERS)
    assert still.json()["run_id"] == run.run_id
    assert still.json()["stages"] == []


@pytest.mark.asyncio
async def test_command_failure_stores_exit_status_and_redacted_tails(db_session, client):
    run = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    await record.write_stage(
        db_session,
        run.run_id,
        "containers_started",
        "finish",
        "ERROR",
        "containers_started failed.",
        cause="exit 2",
        exit_status=2,
        stdout="ready syt_secrettoken",
        stderr="boom " + ("x" * 9000),
    )
    body = (await client.get(f"/api/v1/runs/{run.run_id}", headers=HEADERS)).json()
    stage = body["stages"][0]
    assert stage["exit_status"] == 2
    assert stage["truncated"] is True
    assert "syt_secrettoken" not in (stage["stdout_tail"] or "")
    assert "[redacted]" in stage["stdout_tail"]
    assert len(stage["stderr_tail"].encode("utf-8")) <= record.TAIL_LIMIT
    assert stage["duration_seconds"] is None


@pytest.mark.asyncio
async def test_failed_registration_stores_the_registration_error(db_session):
    run = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    await record.write_stage(
        db_session,
        run.run_id,
        "matrix_identity_registered",
        "finish",
        "ERROR",
        "Matrix registration failed (M_FORBIDDEN).",
        cause="Matrix registration failed (M_FORBIDDEN).",
    )
    stage = (
        await db_session.execute(select(OperationalStage).where(OperationalStage.run_id == run.run_id))
    ).scalar_one()
    assert stage.stage == "matrix_identity_registered"
    assert stage.cause == "Matrix registration failed (M_FORBIDDEN)."
    assert stage.exit_status is None


@pytest.mark.asyncio
async def test_second_and_overlapping_creates_keep_their_own_outcomes(db_session):
    first = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    second = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    assert first.run_id != second.run_id
    assert first.outcome is None
    assert second.outcome is None
    await record.finish_run(db_session, first.run_id, "failed")
    await db_session.refresh(first)
    await db_session.refresh(second)
    assert first.outcome == "failed"
    assert second.outcome is None
    await record.finish_run(db_session, second.run_id, "succeeded")
    await db_session.refresh(first)
    assert first.outcome == "failed"


def _events(monkeypatch):
    events = []

    def start_run_sync(**kwargs):
        events.append(("start", kwargs))
        return "run-1"

    def stage_sync(**kwargs):
        events.append(("stage", kwargs))

    def finish_sync(**kwargs):
        events.append(("finish", kwargs))

    monkeypatch.setattr("amctl.oplog.record.start_run_sync", start_run_sync)
    monkeypatch.setattr("amctl.oplog.record.stage_sync", stage_sync)
    monkeypatch.setattr("amctl.oplog.record.finish_sync", finish_sync)
    return events


def _finish_names(events):
    return [item[1]["stage"] for item in events if item[0] == "stage" and item[1]["phase"] == "finish"]


def test_successful_create_records_the_eight_stages_and_a_certificate_warning(tmp_path, monkeypatch):
    events = _events(monkeypatch)
    instance = tmp_path / "agent0-6"
    host = FakeHost(instance / "usr/workdir/matrix-mcp-server/.env")
    provision_agent(
        6,
        base_dir=tmp_path,
        template_dir=TEMPLATE_DIR,
        host=host,
        timeouts=FAST,
        sleep=lambda _seconds: None,
        environ={},
    )
    finished = _finish_names(events)
    for name in (
        "files_prepared",
        "containers_started",
        "homeserver_ready",
        "matrix_identity_registered",
        "agent_zero_credential_derived",
        "gateway_installed",
        "gateway_health_confirmed",
        "retired_bot_stopped",
    ):
        assert name in finished
    certificate = [item[1] for item in events if item[0] == "stage" and item[1]["stage"] == "certificate_issued"]
    assert certificate[-1]["severity"] == "WARN"
    assert events[0][1]["target"] == "agent0-6"
    assert events[-1] == ("finish", {"run_id": "run-1", "outcome": "succeeded", "instance_present": None})


def test_failed_compose_passes_exit_status_and_both_tails(tmp_path, monkeypatch):
    events = _events(monkeypatch)

    class ComposeFails(FakeHost):
        def run(self, args, cwd=None, check=True, env=None):
            if args[:3] == ["docker", "compose", "up"]:
                self.calls.append(args)
                return CmdResult(2, "stdout syt_secrettoken", "stderr boom")
            return super().run(args, cwd=cwd, check=check, env=env)

    instance = tmp_path / "agent0-6"
    host = ComposeFails(instance / "usr/workdir/matrix-mcp-server/.env")
    with pytest.raises(ProvisionError):
        provision_agent(
            6,
            base_dir=tmp_path,
            template_dir=TEMPLATE_DIR,
            host=host,
            timeouts=FAST,
            sleep=lambda _seconds: None,
            environ={},
        )
    failed = [item[1] for item in events if item[0] == "stage" and item[1]["phase"] == "finish"][-1]
    assert failed["stage"] == "containers_started"
    assert failed["exit_status"] == 2
    assert "syt_secrettoken" in failed["stdout"]
    assert failed["stderr"] == "stderr boom"
    assert events[-1][1]["outcome"] == "failed"


def test_failed_registration_names_that_stage(tmp_path, monkeypatch):
    events = _events(monkeypatch)

    class Denied(FakeHost):
        def request(self, method, url, body=None, headers=None):
            if url.endswith("/register"):
                return 401, {"errcode": "M_FORBIDDEN"}
            return super().request(method, url, body, headers)

    instance = tmp_path / "agent0-6"
    host = Denied(instance / "usr/workdir/matrix-mcp-server/.env")
    with pytest.raises(ProvisionError):
        provision_agent(
            6,
            base_dir=tmp_path,
            template_dir=TEMPLATE_DIR,
            host=host,
            timeouts=FAST,
            sleep=lambda _seconds: None,
            environ={},
        )
    failed = [item[1] for item in events if item[0] == "stage" and item[1]["severity"] == "ERROR"][-1]
    assert failed["stage"] == "matrix_identity_registered"
    assert "M_FORBIDDEN" in failed["cause"]


def test_wait_stores_the_stage_the_limit_and_the_last_result(tmp_path, monkeypatch):
    events = _events(monkeypatch)

    class Unreachable(FakeHost):
        def run(self, args, cwd=None, check=True, env=None):
            if args[-1:] == ["status"] and "supervisorctl" in args and args[-2:] != ["status", "run_bot"]:
                self.calls.append(args)
                return CmdResult(4, "", "refused connection")
            return super().run(args, cwd=cwd, check=check, env=env)

    instance = tmp_path / "agent0-6"
    host = Unreachable(instance / "usr/workdir/matrix-mcp-server/.env")
    with pytest.raises(ProvisionError):
        provision_agent(
            6,
            base_dir=tmp_path,
            template_dir=TEMPLATE_DIR,
            host=host,
            timeouts=FAST,
            sleep=lambda _seconds: None,
            environ={},
        )
    failed = [item[1] for item in events if item[0] == "stage" and item[1]["severity"] == "ERROR"][-1]
    assert failed["stage"] == "supervisord_ready"
    assert "stage=supervisord_ready" in failed["cause"]
    assert "limit=" in failed["cause"]
    assert "last=" in failed["cause"]
    assert failed["cause"].strip()


def test_decommission_script_calls_the_module_and_keeps_create_outcome(db_session):
    text = SCRIPT.read_text()
    assert "-m amctl.oplog" in text
    assert "containers_removed" in text
    assert "directory_removed" in text
    assert "instance-present" in text
    assert "The instance may still exist." in text


@pytest.mark.asyncio
async def test_teardown_is_a_separate_run_and_leaves_the_create_failed(db_session, client):
    created = await record.start_run(db_session, action="create", target="agent0-6", actor="operator")
    await record.finish_run(db_session, created.run_id, "failed")
    torn = await record.start_run(db_session, action="teardown", target="agent0-6", actor="operator")
    await record.write_stage(db_session, torn.run_id, "containers_removed", "start", "INFO", "Removing containers.")
    await record.write_stage(db_session, torn.run_id, "containers_removed", "finish", "INFO", "Containers are removed.")
    await record.write_stage(db_session, torn.run_id, "directory_removed", "start", "INFO", "Removing the instance directory.")
    await record.write_stage(
        db_session,
        torn.run_id,
        "directory_removed",
        "finish",
        "INFO",
        "The instance directory is absent.",
        instance_present=False,
    )
    await record.finish_run(db_session, torn.run_id, "succeeded", instance_present=False)
    body = (await client.get(f"/api/v1/runs/{torn.run_id}", headers=HEADERS)).json()
    assert body["outcome"] == "succeeded"
    assert [stage["stage"] for stage in body["stages"]] == [
        "containers_removed",
        "containers_removed",
        "directory_removed",
        "directory_removed",
    ]
    assert body["stages"][-1]["instance_present"] is False
    assert body["stages"][-1]["duration_seconds"] is not None
    created_body = (await client.get(f"/api/v1/runs/{created.run_id}", headers=HEADERS)).json()
    assert created_body["outcome"] == "failed"
    assert created.run_id != torn.run_id

    stopped = await record.start_run(db_session, action="teardown", target="agent0-6", actor="operator")
    await record.write_stage(
        db_session,
        stopped.run_id,
        "directory_removed",
        "finish",
        "ERROR",
        "Directory removal stopped.",
        cause="directory_removed stopped. The instance may still exist.",
        instance_present=True,
    )
    await record.finish_run(db_session, stopped.run_id, "failed", instance_present=True)
    failed = (await client.get(f"/api/v1/runs/{stopped.run_id}", headers=HEADERS)).json()
    assert failed["outcome"] == "failed"
    assert "may still exist" in failed["stages"][0]["cause"]
    assert failed["stages"][0]["instance_present"] is True


def test_oplog_cli_prints_only_the_run_id(monkeypatch, capsys):
    monkeypatch.setattr(
        "amctl.oplog.cli.start_run_sync",
        lambda **kwargs: kwargs["action"] and "run-9",
    )
    seen = {}

    def stage_sync(**kwargs):
        seen["stage"] = kwargs

    def finish_sync(**kwargs):
        seen["finish"] = kwargs

    monkeypatch.setattr("amctl.oplog.cli.stage_sync", stage_sync)
    monkeypatch.setattr("amctl.oplog.cli.finish_sync", finish_sync)
    assert oplog_main(["start", "--action", "teardown", "--target", "agent0-6", "--actor", "operator"]) == 0
    assert capsys.readouterr().out.strip() == "run-9"
    assert oplog_main(
        [
            "stage",
            "--run-id",
            "run-9",
            "--stage",
            "directory_removed",
            "--phase",
            "finish",
            "--instance-present",
            "false",
            "--body",
            "The instance directory is absent.",
        ]
    ) == 0
    assert seen["stage"]["instance_present"] is False
    assert oplog_main(["finish", "--run-id", "run-9", "--outcome", "succeeded", "--instance-present", "false"]) == 0
    assert seen["finish"]["instance_present"] is False


@pytest.mark.asyncio
async def test_health_and_repair_use_the_same_record_shape(db_session, oplog_dir, monkeypatch):
    monkeypatch.setenv("AMCTL_OPLOG", "on")

    @tracked(action="health_check", stage="checks")
    async def one_health(session, agent, operator="monitor:health"):
        return {"ok": True}

    @tracked(action="repair", stage="membership", target="arg0")
    async def one_repair(agent_name, session):
        return True

    for name, number in (("agent0-6", 6), ("agent0-7", 7)):
        await one_health(db_session, SimpleNamespace(name=name, instance_num=number))
    await one_repair("agent0-6", db_session)

    rows = (await db_session.execute(select(OperationalRun))).scalars().all()
    health = [row for row in rows if row.action == "health_check"]
    repair = [row for row in rows if row.action == "repair"]
    assert {row.target for row in health} == {"agent0-6", "agent0-7"}
    assert len(repair) == 1
    assert repair[0].target == "agent0-6"
    line = json.loads((oplog_dir / "oplog.jsonl").read_text().splitlines()[0])
    resource = line["resourceLogs"][0]["resource"]["attributes"]
    names = {item["key"]: item["value"].get("stringValue") for item in resource}
    assert names["service.name"] == "am-ctl"
    record_attrs = {
        item["key"]: next(iter(item["value"].values()))
        for item in line["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]["attributes"]
    }
    assert "run.id" in record_attrs
    assert record_attrs["run.action"] == "health_check"
    assert record_attrs["stage.name"] == "checks"

    @tracked(action="backup", stage="suite", target="none")
    async def one_backup(session, operator="cli:backup"):
        return {"ok": True}

    await one_backup(db_session)
    backup = (
        await db_session.execute(select(OperationalRun).where(OperationalRun.action == "backup"))
    ).scalar_one()
    assert backup.target is None

    @tracked(action="model_change", stage="configuration")
    async def change(session, agent, chat_model=None, operator="cli:models"):
        return "updated"

    await change(
        db_session,
        SimpleNamespace(name="agent0-6", instance_num=6),
        chat_model="Write a poem about the homeserver internals",
    )
    stages = (
        await db_session.execute(
            select(OperationalStage).where(OperationalStage.stage == "configuration")
        )
    ).scalars().all()
    blob = " ".join(stage.body for stage in stages)
    assert "poem" not in blob
    assert "homeserver" not in blob


def test_control_plane_entry_points_open_the_planned_actions():
    assert run_agent_health_checks._oplog_action == "health_check"
    assert apply_agent_reconciliation._oplog_action == "repair"
    assert repair_room_membership._oplog_action == "repair"
    assert deploy_release_to_agent._oplog_action == "release"
    assert execute_backup_suite._oplog_action == "backup"
    assert verify_agent_credentials._oplog_action == "credential_check"
    assert set_agent_model_config._oplog_action == "model_change"


@pytest.mark.asyncio
async def test_dead_writer_is_interrupted_and_old_rows_are_deleted(db_session, oplog_dir):
    stale = await record.start_run(
        db_session,
        action="create",
        target="agent0-6",
        actor="operator",
        writer_pid=2**30,
    )
    await record.write_stage(db_session, stale.run_id, "files_prepared", "start", "INFO", "Preparing instance files.")
    await record.interrupt_orphans(db_session)
    await db_session.refresh(stale)
    assert stale.outcome == "interrupted"
    unfinished = (
        await db_session.execute(
            select(OperationalStage)
            .where(OperationalStage.run_id == stale.run_id)
            .order_by(OperationalStage.id)
        )
    ).scalars().all()
    assert unfinished[-1].phase == "finish"
    assert unfinished[-1].body == "The stage did not finish."

    fresh = await record.start_run(db_session, action="health_check", target="agent0-7", actor="monitor:health")
    await record.write_stage(db_session, fresh.run_id, "checks", "finish", "INFO", "Health checks finished.")
    await record.finish_run(db_session, fresh.run_id, "succeeded")
    old = datetime.now(timezone.utc) - timedelta(days=31)
    stale.ended_at = old
    for stage in unfinished:
        stage.observed_at = old
    await db_session.commit()
    await record.purge_expired(db_session)
    left = (await db_session.execute(select(OperationalRun.run_id))).scalars().all()
    assert stale.run_id not in left
    assert fresh.run_id in left
    text = (oplog_dir / "oplog.jsonl").read_text()
    assert stale.run_id not in text
    assert fresh.run_id in text


def test_runs_cli_calls_the_reader(monkeypatch):
    seen = {}

    def list_runs(self, target=None, action=None, limit=20):
        seen["list"] = (target, action, limit)
        return [{"run_id": "r1", "action": "create", "target": target, "outcome": "succeeded"}]

    def get_run(self, run_id):
        seen["show"] = run_id
        return {"run_id": run_id, "outcome": "succeeded", "stages": []}

    monkeypatch.setattr(AmCtlClient, "list_runs", list_runs)
    monkeypatch.setattr(AmCtlClient, "get_run", get_run)
    listed = CliRunner().invoke(cli_main, ["--output", "json", "runs", "--target", "agent0-6", "--action", "create"])
    assert listed.exit_code == 0, listed.output
    assert seen["list"] == ("agent0-6", "create", 20)
    assert "r1" in listed.output
    shown = CliRunner().invoke(cli_main, ["runs", "r1"])
    assert shown.exit_code == 0, shown.output
    assert seen["show"] == "r1"
