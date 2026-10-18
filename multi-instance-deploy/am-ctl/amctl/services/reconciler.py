"""Idempotent reconciliation engine (Phase 4): read-only check and plan.

Guarantee: check_agent_drift, check_fleet_drift, and compute_agent_plan
perform ZERO mutations -- no database writes, no container/host file writes,
and no process restarts.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.models.credential import CredentialFingerprint
from amctl.models.reconcile import ReconcileRun
from amctl.schemas.reconcile import (
    AgentDriftReport,
    AppliedActionResult,
    DriftItem,
    FleetDriftReport,
    PlannedAction,
    ReconcileApplyResponse,
    ReconcilePlanResponse,
)
from amctl.services.agent_zero import (
    _read_bot_a0_key,
    check_a0_auth,
    check_mcp_health,
    derive_canonical_a0_fingerprint,
)
from amctl.services.docker import _run, get_container_status, get_process_info, supervisor_action
from amctl.services.matrix import get_joined_rooms, get_whoami, repair_room_membership

logger = logging.getLogger(__name__)

TEMPLATE_BASE = Path("/opt/agent-zero/multi-instance-deploy/templates")
INSTANCE_BASE = Path("/opt/agent-zero")

# Tracked artifacts for hash drift comparison against golden templates
TRACKED_ARTIFACTS = {
    "matrix-bot-rust": (
        TEMPLATE_BASE / "matrix-bot" / "matrix-bot-rust",
        "usr/workdir/matrix-bot/matrix-bot-rust",
    ),
    "run-bot-wrapper.sh": (
        TEMPLATE_BASE / "matrix-bot" / "run-bot-wrapper.sh",
        "usr/workdir/matrix-bot/run-bot-wrapper.sh",
    ),
    "run-matrix-bot.sh": (
        TEMPLATE_BASE / "matrix-bot" / "run-matrix-bot.sh",
        "usr/workdir/matrix-bot/run-matrix-bot.sh",
    ),
    "derive-a0-token.sh": (
        TEMPLATE_BASE / "scripts" / "derive-a0-token.sh",
        "usr/workdir/derive-a0-token.sh",
    ),
    "preflight-check.sh": (
        TEMPLATE_BASE / "scripts" / "preflight-check.sh",
        "usr/workdir/preflight-check.sh",
    ),
    "watchdog.sh": (
        TEMPLATE_BASE / "scripts" / "watchdog.sh",
        "usr/workdir/watchdog.sh",
    ),
    "startup-services.sh": (
        TEMPLATE_BASE / "scripts" / "startup-services.sh",
        "usr/workdir/startup-services.sh",
    ),
}


def _file_sha256_prefix(path: Path) -> str | None:
    """Return 12-char SHA-256 prefix of a file on the host, or None if missing."""
    try:
        if not path.is_file():
            return None
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:12]
    except OSError:
        return None


async def _inspect_secret_delivery(agent_name: str) -> dict:
    """Read-only inspection of .a0-api-key permissions/ownership and bot .env A0_API_KEY presence."""
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c",
        "stat_out=$(stat -c '%a:%U:%G:%s' /a0/usr/workdir/matrix-bot/.a0-api-key 2>/dev/null || echo 'missing'); "
        "env_key=$(grep -c '^A0_API_KEY=' /a0/usr/workdir/matrix-bot/.env 2>/dev/null || true); "
        "echo \"${stat_out}|${env_key}\"",
    ])
    if rc != 0 or "|" not in out:
        return {
            "secret_file_exists": False,
            "mode": None,
            "owner": None,
            "size": 0,
            "env_has_a0_api_key": None,
        }
    stat_part, env_part = out.strip().split("|", 1)
    env_count = int(env_part.strip()) if env_part.strip().isdigit() else 0
    if stat_part == "missing":
        return {
            "secret_file_exists": False,
            "mode": None,
            "owner": None,
            "size": 0,
            "env_has_a0_api_key": env_count > 0,
        }
    parts = stat_part.split(":")
    mode = parts[0] if len(parts) > 0 else None
    owner = f"{parts[1]}:{parts[2]}" if len(parts) > 2 else None
    size = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
    return {
        "secret_file_exists": True,
        "mode": mode,
        "owner": owner,
        "size": size,
        "env_has_a0_api_key": env_count > 0,
    }


def _inspect_artifact_hashes(agent_name: str) -> tuple[str, dict, dict]:
    """Compare deployed instance artifact hashes against golden template hashes (read-only)."""
    instance_dir = INSTANCE_BASE / agent_name
    expected_hashes = {}
    actual_hashes = {}
    mismatched = []

    for label, (tpl_path, rel_dst) in TRACKED_ARTIFACTS.items():
        exp_h = _file_sha256_prefix(tpl_path)
        act_h = _file_sha256_prefix(instance_dir / rel_dst)
        expected_hashes[label] = exp_h
        actual_hashes[label] = act_h
        if exp_h != act_h:
            mismatched.append(label)

    status = "clean" if not mismatched else "drift"
    return status, expected_hashes, {"hashes": actual_hashes, "mismatched": mismatched}


async def check_agent_drift(
    session: AsyncSession,
    agent: Agent,
    colliding_fingerprints: set[str] | None = None,
) -> AgentDriftReport:
    """Compare live agent state against DB registry and canonical Phase 3/4 invariants.
    Strictly read-only: performs zero DB or container writes.
    """
    if colliding_fingerprints is None:
        colliding_fingerprints = await _get_colliding_fingerprints(session)

    reg_a0_fp = None
    for c in agent.credential_fingerprints:
        if c.domain == "a0_api_key":
            reg_a0_fp = c.fingerprint
            break

    (
        whoami,
        rooms_res,
        canonical_fp_res,
        bot_key_res,
        a0_probe_res,
        mcp_res,
        proc_info,
        containers,
        secret_info,
    ) = await asyncio.gather(
        get_whoami(agent.name, agent.homeserver_url),
        get_joined_rooms(agent.name, agent.homeserver_url),
        derive_canonical_a0_fingerprint(agent.name),
        _read_bot_a0_key(agent.name),
        check_a0_auth(agent.name, expected_fingerprint=reg_a0_fp),
        check_mcp_health(agent.name),
        get_process_info(agent.name),
        get_container_status(agent.name),
        _inspect_secret_delivery(agent.name),
    )

    checks: list[DriftItem] = []

    # 1. Identity check (/whoami == registry.matrix_user_id)
    id_clean = bool(whoami.user_id and whoami.user_id == agent.matrix_user_id)
    checks.append(
        DriftItem(
            drift_type="identity",
            status="clean" if id_clean else "drift",
            expected=agent.matrix_user_id,
            actual=whoami.user_id or f"error:{whoami.error}",
            detail={"device_id": whoami.device_id, "error": whoami.error},
        )
    )

    # 2. Required room membership
    rooms_ok, joined_rooms, rooms_err = rooms_res
    required_rooms = sorted(r.room_id for r in agent.required_rooms)
    missing_rooms = [r for r in required_rooms if r not in joined_rooms] if rooms_ok else required_rooms
    mem_clean = rooms_ok and len(missing_rooms) == 0
    checks.append(
        DriftItem(
            drift_type="membership",
            status="clean" if mem_clean else "drift",
            expected=required_rooms,
            actual=[r for r in required_rooms if r in joined_rooms] if rooms_ok else [],
            detail={"missing_rooms": missing_rooms, "total_joined": len(joined_rooms), "error": rooms_err},
        )
    )

    # 3. Credential fingerprint & collision check
    canonical_fp, derive_err = canonical_fp_res
    deployed_key, key_source = bot_key_res
    deployed_fp = hashlib.sha256(deployed_key.encode()).hexdigest()[:12] if deployed_key else None
    a0_status, a0_detail = a0_probe_res
    has_collision = bool(
        (deployed_fp and deployed_fp in colliding_fingerprints)
        or (reg_a0_fp and reg_a0_fp in colliding_fingerprints)
    )
    cred_clean = (
        canonical_fp is not None
        and deployed_fp == canonical_fp
        and reg_a0_fp == canonical_fp
        and a0_status == "pass"
        and not has_collision
    )
    checks.append(
        DriftItem(
            drift_type="credential",
            status="clean" if cred_clean else "drift",
            expected=canonical_fp or reg_a0_fp,
            actual=deployed_fp,
            detail={
                "canonical_fingerprint": canonical_fp,
                "deployed_fingerprint": deployed_fp,
                "registry_fingerprint": reg_a0_fp,
                "a0_probe_status": a0_status,
                "collision": has_collision,
                "derive_error": derive_err,
            },
        )
    )

    # 4. Secret file delivery & permissions (.a0-api-key mode 600, no A0_API_KEY in .env)
    sec_clean = (
        secret_info["secret_file_exists"]
        and secret_info["mode"] == "600"
        and secret_info["size"] > 0
        and secret_info["env_has_a0_api_key"] is False
        and key_source == "secret_file"
    )
    checks.append(
        DriftItem(
            drift_type="secret_delivery",
            status="clean" if sec_clean else "drift",
            expected="secret_file (mode=600, .env A0_API_KEY absent)",
            actual=(
                f"{key_source} (mode={secret_info['mode']}, "
                f".env A0_API_KEY={'present' if secret_info['env_has_a0_api_key'] else 'absent'})"
            ),
            detail=secret_info,
        )
    )

    # 5. Process & container invariants (3 containers up, 1 bot process of declared runtime, supervisord, MCP healthy)
    mcp_status, _ = mcp_res
    all_containers_up = len(containers) == 3 and all(c.running for c in containers)
    proc_clean = (
        all_containers_up
        and proc_info is not None
        and proc_info.bot_count == 1
        and proc_info.bot_runtime == agent.bot_runtime
        and proc_info.supervisord_running
        and mcp_status == "pass"
    )
    checks.append(
        DriftItem(
            drift_type="process",
            status="clean" if proc_clean else "drift",
            expected=f"containers=3/3, bot=1 ({agent.bot_runtime}), supervisord=True, mcp=pass",
            actual=(
                f"containers={sum(1 for c in containers if c.running)}/{len(containers)}, "
                f"bot={proc_info.bot_count if proc_info else 0} ({proc_info.bot_runtime if proc_info else None}), "
                f"supervisord={proc_info.supervisord_running if proc_info else False}, mcp={mcp_status}"
            ),
            detail={
                "containers": {c.name: c.running for c in containers},
                "bot_count": proc_info.bot_count if proc_info else 0,
                "bot_runtime": proc_info.bot_runtime if proc_info else None,
                "supervisord": proc_info.supervisord_running if proc_info else False,
                "mcp_status": mcp_status,
            },
        )
    )

    # 6. Artifact hashes vs golden release templates
    art_status, exp_hashes, act_info = _inspect_artifact_hashes(agent.name)
    checks.append(
        DriftItem(
            drift_type="artifact_hash",
            status=art_status,
            expected=exp_hashes,
            actual=act_info["hashes"],
            detail={"mismatched_artifacts": act_info["mismatched"]},
        )
    )

    drift_count = sum(1 for c in checks if c.status != "clean")
    return AgentDriftReport(
        agent_id=agent.id,
        agent_name=agent.name,
        instance_num=agent.instance_num,
        clean=drift_count == 0,
        drift_count=drift_count,
        checks=checks,
        checked_at=datetime.now(timezone.utc),
    )


async def _get_colliding_fingerprints(session: AsyncSession) -> set[str]:
    fp_res = await session.execute(select(CredentialFingerprint))
    fps = fp_res.scalars().all()
    counts: dict[tuple[str, str], int] = {}
    for fp in fps:
        key = (fp.domain, fp.fingerprint)
        counts[key] = counts.get(key, 0) + 1
    return {fp for (_, fp), count in counts.items() if count > 1}


async def check_fleet_drift(session: AsyncSession) -> FleetDriftReport:
    """Run read-only drift check across all agents in the fleet.
    Guarantees zero DB or container writes.
    """
    res = await session.execute(select(Agent).order_by(Agent.instance_num))
    agents = res.scalars().all()
    agent_map = {a.id: a.name for a in agents}

    fp_res = await session.execute(select(CredentialFingerprint))
    fps = fp_res.scalars().all()
    by_domain_fp: dict[tuple[str, str], list[str]] = {}
    for fp in fps:
        by_domain_fp.setdefault((fp.domain, fp.fingerprint), []).append(
            agent_map.get(fp.agent_id, str(fp.agent_id))
        )

    collisions = [
        {"domain": dom, "fingerprint": fp, "agents": sorted(names)}
        for (dom, fp), names in by_domain_fp.items()
        if len(names) > 1
    ]
    colliding_fps = {c["fingerprint"] for c in collisions}

    reports = await asyncio.gather(
        *[check_agent_drift(session, a, colliding_fingerprints=colliding_fps) for a in agents]
    )

    # Also detect live deployed fingerprint collisions across agents
    live_fps: dict[str, list[str]] = {}
    for rep in reports:
        for chk in rep.checks:
            if chk.drift_type == "credential" and isinstance(chk.actual, str) and chk.actual:
                live_fps.setdefault(chk.actual, []).append(rep.agent_name)
    for fp, names in live_fps.items():
        if len(names) > 1 and fp not in colliding_fps:
            collisions.append({"domain": "a0_api_key (live)", "fingerprint": fp, "agents": sorted(names)})
            colliding_fps.add(fp)
            for rep in reports:
                if rep.agent_name in names:
                    for chk in rep.checks:
                        if chk.drift_type == "credential":
                            chk.status = "drift"
                            if chk.detail is not None:
                                chk.detail["collision"] = True
                    rep.drift_count = sum(1 for c in rep.checks if c.status != "clean")
                    rep.clean = rep.drift_count == 0

    clean_count = sum(1 for r in reports if r.clean)
    return FleetDriftReport(
        total_agents=len(reports),
        clean_agents=clean_count,
        drifted_agents=len(reports) - clean_count,
        has_fingerprint_collisions=len(collisions) > 0,
        collisions=collisions,
        agents=list(reports),
        checked_at=datetime.now(timezone.utc),
    )


async def compute_agent_plan(session: AsyncSession, agent: Agent) -> ReconcilePlanResponse:
    """Compute a redacted, ordered remediation plan to resolve any detected drift for an agent.
    Strictly read-only: performs zero DB or container writes.
    """
    report = await check_agent_drift(session, agent)
    actions: list[PlannedAction] = []
    step = 1

    by_type = {c.drift_type: c for c in report.checks}

    # Artifact hash drift or secret delivery drift -> install golden artifacts & derive .a0-api-key
    art_chk = by_type.get("artifact_hash")
    sec_chk = by_type.get("secret_delivery")
    cred_chk = by_type.get("credential")

    needs_bot_restart = False

    if art_chk and art_chk.status == "drift":
        mismatched = (art_chk.detail or {}).get("mismatched_artifacts", [])
        actions.append(
            PlannedAction(
                step=step,
                action_type="sync_artifacts",
                description=f"Install golden template artifacts ({', '.join(mismatched)}) onto {agent.name}",
                target=agent.name,
                detail={"artifacts": mismatched},
            )
        )
        step += 1
        needs_bot_restart = True

    if (sec_chk and sec_chk.status == "drift") or (cred_chk and cred_chk.status == "drift"):
        sec_detail = (sec_chk.detail or {}) if sec_chk else {}
        if sec_detail.get("env_has_a0_api_key"):
            actions.append(
                PlannedAction(
                    step=step,
                    action_type="remove_env_a0_api_key",
                    description=f"Backup bot .env and remove legacy A0_API_KEY line from {agent.name} bot .env",
                    target=f"/opt/agent-zero/{agent.name}/usr/workdir/matrix-bot/.env",
                )
            )
            step += 1
        actions.append(
            PlannedAction(
                step=step,
                action_type="derive_canonical_secret",
                description=f"Run derive-a0-token.sh to write canonical .a0-api-key (mode 0600) and sync registry fingerprint",
                target=f"{agent.name}:/a0/usr/workdir/matrix-bot/.a0-api-key",
                detail={
                    "expected_fingerprint": (cred_chk.detail or {}).get("canonical_fingerprint") if cred_chk else None
                },
            )
        )
        step += 1
        needs_bot_restart = True

    mem_chk = by_type.get("membership")
    if mem_chk and mem_chk.status == "drift":
        missing = (mem_chk.detail or {}).get("missing_rooms", [])
        for rid in missing:
            actions.append(
                PlannedAction(
                    step=step,
                    action_type="repair_room_membership",
                    description=f"Invite {agent.matrix_user_id} via @admin:v-site.net and join room {rid}",
                    target=rid,
                    detail={"room_id": rid, "user_id": agent.matrix_user_id},
                )
            )
            step += 1

    id_chk = by_type.get("identity")
    if id_chk and id_chk.status == "drift":
        actions.append(
            PlannedAction(
                step=step,
                action_type="flag_terminal_identity_mismatch",
                description=(
                    f"Stop run_bot and require operator token recovery: /whoami ({id_chk.actual}) "
                    f"!= registry ({id_chk.expected})"
                ),
                target=agent.name,
                detail={"expected": id_chk.expected, "actual": id_chk.actual},
            )
        )
        step += 1
        needs_bot_restart = False

    proc_chk = by_type.get("process")
    if proc_chk and proc_chk.status == "drift":
        p_detail = proc_chk.detail or {}
        if p_detail.get("mcp_status") != "pass":
            actions.append(
                PlannedAction(
                    step=step,
                    action_type="restart_service",
                    description=f"Restart run_mcp via supervisorctl on {agent.name}",
                    target=f"{agent.name}:run_mcp",
                )
            )
            step += 1
        if p_detail.get("bot_count") != 1:
            needs_bot_restart = True

    if needs_bot_restart:
        actions.append(
            PlannedAction(
                step=step,
                action_type="restart_service",
                description=f"Restart run_bot via supervisorctl on {agent.name} and verify post-apply preflight",
                target=f"{agent.name}:run_bot",
            )
        )

    return ReconcilePlanResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        clean=report.clean,
        drift_report=report,
        actions=actions,
        computed_at=datetime.now(timezone.utc),
    )


def _create_pre_apply_snapshot(agent_name: str) -> str:
    """Capture a pre-apply snapshot of instance artifacts and .env (without aggregating fleet secrets)."""
    import shutil

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    instance_dir = INSTANCE_BASE / agent_name
    snap_dir = instance_dir / "usr" / "workdir" / ".reconcile-snapshots" / ts
    snap_dir.mkdir(parents=True, exist_ok=True)

    bot_env = instance_dir / "usr" / "workdir" / "matrix-bot" / ".env"
    if bot_env.is_file():
        shutil.copy2(bot_env, snap_dir / "bot.env")
        shutil.copy2(bot_env, instance_dir / "usr" / "workdir" / "matrix-bot" / ".env.sync-backup")

    for label, (_, rel_dst) in TRACKED_ARTIFACTS.items():
        src = instance_dir / rel_dst
        if src.is_file():
            shutil.copy2(src, snap_dir / label)

    return str(snap_dir)


async def apply_agent_reconciliation(
    session: AsyncSession,
    agent: Agent,
    operator: str = "cli:reconcile_apply",
) -> ReconcileApplyResponse:
    """Execute planned reconciliation actions for a SINGLE agent.
    - If clean: true no-op (zero audit_log mutations, zero file/process mutations)
    - If drifted: captures pre-apply snapshot, executes actions sequentially,
      logs each mutation to audit_log, records ReconcileRun, and re-runs check.
    """
    import shutil

    plan = await compute_agent_plan(session, agent)
    pre_check = plan.drift_report

    if plan.clean or not plan.actions:
        return ReconcileApplyResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            noop=True,
            success=True,
            snapshot_dir=None,
            actions_executed=[],
            pre_check=pre_check,
            post_check=pre_check,
            applied_at=datetime.now(timezone.utc),
        )

    snapshot_dir = _create_pre_apply_snapshot(agent.name)
    instance_dir = INSTANCE_BASE / agent.name
    executed: list[AppliedActionResult] = []

    for act in plan.actions:
        step_status = "applied"
        step_detail: dict = {}

        if act.action_type == "sync_artifacts":
            artifacts = (act.detail or {}).get("artifacts", list(TRACKED_ARTIFACTS.keys()))
            # Stop run_bot before overwriting binary if matrix-bot-rust is being synced
            if "matrix-bot-rust" in artifacts:
                await supervisor_action(agent.name, "stop", "run_bot")
            synced = []
            for label in artifacts:
                if label not in TRACKED_ARTIFACTS:
                    continue
                tpl_path, rel_dst = TRACKED_ARTIFACTS[label]
                dst_path = instance_dir / rel_dst
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                tmp_dst = dst_path.with_suffix(dst_path.suffix + ".tmp")
                shutil.copy2(tpl_path, tmp_dst)
                tmp_dst.chmod(0o755)
                tmp_dst.replace(dst_path)
                synced.append(label)
            step_detail = {"synced_artifacts": synced, "snapshot_dir": snapshot_dir}

        elif act.action_type == "remove_env_a0_api_key":
            bot_env = instance_dir / "usr" / "workdir" / "matrix-bot" / ".env"
            if bot_env.is_file():
                lines = bot_env.read_text().splitlines(keepends=True)
                filtered = [ln for ln in lines if not ln.startswith("A0_API_KEY=")]
                tmp_env = bot_env.with_suffix(".env.tmp")
                tmp_env.write_text("".join(filtered))
                tmp_env.replace(bot_env)
                step_detail = {"removed": "A0_API_KEY", "backup": str(bot_env) + ".sync-backup"}
            else:
                step_status = "skipped"
                step_detail = {"reason": "bot_env_not_found"}

        elif act.action_type == "derive_canonical_secret":
            rc, out = await _run([
                "docker", "exec", agent.name,
                "/a0/usr/workdir/derive-a0-token.sh",
                "--output", "/a0/usr/workdir/matrix-bot/.a0-api-key",
            ], timeout=25.0)
            if rc == 0 and out.strip():
                fp = out.strip().splitlines()[-1].strip()
                # Ensure registry fingerprint matches
                reg_rec = next((c for c in agent.credential_fingerprints if c.domain == "a0_api_key"), None)
                now = datetime.now(timezone.utc)
                if reg_rec:
                    reg_rec.fingerprint = fp
                    reg_rec.recorded_at = now
                else:
                    session.add(CredentialFingerprint(
                        agent_id=agent.id,
                        domain="a0_api_key",
                        fingerprint=fp,
                        recorded_at=now,
                    ))
                step_detail = {"fingerprint": fp, "secret_file": "/a0/usr/workdir/matrix-bot/.a0-api-key"}
            else:
                step_status = "failed"
                step_detail = {"error": out or "derive_a0_token_failed"}

        elif act.action_type == "repair_room_membership":
            room_id = (act.detail or {}).get("room_id", act.target)
            ok, rep_info = await repair_room_membership(
                agent.name, agent.matrix_user_id, agent.homeserver_url, room_id
            )
            step_status = "applied" if ok else "failed"
            step_detail = rep_info

        elif act.action_type == "restart_service":
            prog = act.target.split(":", 1)[-1] if ":" in act.target else "run_bot"
            ok, sup_out = await supervisor_action(agent.name, "restart", prog)
            # If restarting run_bot, derive-a0-token.sh runs first (~5s) before exec matrix-bot-rust;
            # poll up to 10s so post_check sees the running matrix-bot-rust process.
            if prog == "run_bot":
                for _ in range(10):
                    await asyncio.sleep(1)
                    pinfo = await get_process_info(agent.name)
                    if pinfo and pinfo.bot_count == 1:
                        break
            else:
                await asyncio.sleep(2)
            step_status = "applied" if ok else "failed"
            step_detail = {"program": prog, "output": sup_out}

        elif act.action_type == "flag_terminal_identity_mismatch":
            ok, sup_out = await supervisor_action(agent.name, "stop", "run_bot")
            step_status = "failed"
            step_detail = {"bot_stopped": ok, "output": sup_out, **(act.detail or {})}

        res_item = AppliedActionResult(
            step=act.step,
            action_type=act.action_type,
            target=act.target,
            status=step_status,
            detail=step_detail,
        )
        executed.append(res_item)

        session.add(
            AuditLog(
                agent_id=agent.id,
                action=f"reconcile_apply:{act.action_type}",
                detail={"step": act.step, "target": act.target, "status": step_status, **step_detail},
                operator=operator,
            )
        )

        if step_status == "failed":
            break

    await session.commit()
    await session.refresh(agent)

    post_check = await check_agent_drift(session, agent)
    overall_success = post_check.clean and all(e.status != "failed" for e in executed)

    run_record = ReconcileRun(
        agent_id=agent.id,
        mode="apply",
        result={
            "noop": False,
            "success": overall_success,
            "snapshot_dir": snapshot_dir,
            "actions_executed": [e.model_dump(mode="json") for e in executed],
            "pre_drift_count": pre_check.drift_count,
            "post_drift_count": post_check.drift_count,
        },
        operator=operator,
    )
    session.add(run_record)
    await session.commit()

    return ReconcileApplyResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        noop=False,
        success=overall_success,
        snapshot_dir=snapshot_dir,
        actions_executed=executed,
        pre_check=pre_check,
        post_check=post_check,
        applied_at=datetime.now(timezone.utc),
    )
