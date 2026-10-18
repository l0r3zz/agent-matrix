"""Continuous health monitoring engine, failure classification, and auto-repair."""

import asyncio
from datetime import datetime, timezone
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.config import settings
from amctl.db import async_session
from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.models.health import Alert, AlertRule, HealthCheck, HealthState
from amctl.services.agent_zero import check_a0_auth, check_mcp_health
from amctl.services.backup import check_backup_freshness
from amctl.services.docker import get_container_status, get_process_info, supervisor_action
from amctl.services.matrix import (
    check_and_refresh_federation_keys,
    check_sync_cursor,
    get_joined_rooms,
    get_whoami,
    repair_room_membership,
)

logger = logging.getLogger(__name__)

ALL_CHECK_TYPES = (
    "matrix_auth",
    "identity",
    "membership",
    "a0_auth",
    "mcp",
    "process",
    "federation",
    "sync_cursor",
)

last_monitor_run: datetime | None = None


async def _load_alert_rules(session: AsyncSession) -> dict[str, AlertRule]:
    result = await session.execute(select(AlertRule))
    return {r.check_type: r for r in result.scalars().all()}


async def _record_check_and_act(
    session: AsyncSession,
    agent: Agent,
    check_type: str,
    status: str,
    detail: dict,
    rules: dict[str, AlertRule],
    operator: str = "monitor:health",
) -> None:
    """Persist time-series HealthCheck, upsert materialized HealthState,
    and execute failure classification / auto-repair / alerting rules.
    """
    now = datetime.now(timezone.utc)

    # 1. Append to health_checks time-series
    hc = HealthCheck(
        agent_id=agent.id,
        check_type=check_type,
        status=status,
        detail=detail,
        checked_at=now,
    )
    session.add(hc)

    # 2. Upsert health_state
    state_res = await session.execute(
        select(HealthState).where(
            HealthState.agent_id == agent.id,
            HealthState.check_type == check_type,
        )
    )
    state = state_res.scalar_one_or_none()

    if state is None:
        fail_count = 1 if status == "fail" else 0
        state = HealthState(
            agent_id=agent.id,
            check_type=check_type,
            status=status,
            detail=detail,
            since=now,
            last_check=now,
            fail_count=fail_count,
        )
        session.add(state)
    else:
        if state.status != status:
            state.since = now
        state.status = status
        state.detail = detail
        state.last_check = now
        if status == "fail":
            state.fail_count = (state.fail_count or 0) + 1
        else:
            state.fail_count = 0

    rule = rules.get(check_type)
    classification = rule.classification if rule else (
        "terminal_config" if check_type in ("matrix_auth", "identity", "a0_auth", "membership") else "restartable"
    )
    action = rule.action if rule else "log_only"

    # 3. Resolve open alerts if check now passes
    if status == "pass":
        open_alerts_res = await session.execute(
            select(Alert).where(
                Alert.agent_id == agent.id,
                Alert.check_type == check_type,
                Alert.status.in_(["open", "acked"]),
            )
        )
        for alert in open_alerts_res.scalars().all():
            alert.status = "resolved"
            alert.resolved_at = now
        return

    if status != "fail":
        return

    # 4. Handle failure according to classification (TERMINAL_CONFIG vs RESTARTABLE)
    detail["classification"] = classification.upper()

    if action == "stop_and_alert":
        # Terminal configuration failure -> stop bot so it does not spin in restart/401 loops, and open alert
        ok, sup_out = await supervisor_action(agent.name, "stop", "run_bot")
        detail["bot_stopped"] = ok
        detail["supervisor_output"] = sup_out
        session.add(AuditLog(
            agent_id=agent.id,
            action="terminal_config_stop_bot",
            detail={"check_type": check_type, "classification": "TERMINAL_CONFIG", "reason": detail},
            operator=operator,
        ))
        await _ensure_open_alert(
            session,
            agent_id=agent.id,
            check_type=check_type,
            classification="TERMINAL_CONFIG",
            message=f"Terminal configuration failure on {agent.name} ({check_type}): bot stopped",
            detail=detail,
        )

    elif action == "restart":
        max_retries = rule.max_retries if rule else 3
        if state.fail_count <= max_retries:
            target_prog = "run_mcp" if check_type == "mcp" else "run_bot"
            ok, sup_out = await supervisor_action(agent.name, "restart", target_prog)
            detail["restarted_program"] = target_prog
            detail["restart_ok"] = ok
            session.add(AuditLog(
                agent_id=agent.id,
                action=f"auto_restart_{target_prog}",
                detail={"check_type": check_type, "fail_count": state.fail_count, "output": sup_out},
                operator=operator,
            ))
        else:
            await _ensure_open_alert(
                session,
                agent_id=agent.id,
                check_type=check_type,
                classification="RESTARTABLE",
                message=f"Restart retries exhausted ({state.fail_count}/{max_retries}) on {agent.name} ({check_type})",
                detail=detail,
            )


async def _ensure_open_alert(
    session: AsyncSession,
    agent_id: int,
    check_type: str,
    classification: str,
    message: str,
    detail: dict,
) -> None:
    existing_res = await session.execute(
        select(Alert).where(
            Alert.agent_id == agent_id,
            Alert.check_type == check_type,
            Alert.status.in_(["open", "acked"]),
        )
    )
    existing = existing_res.scalar_one_or_none()
    if existing:
        existing.detail = detail
        existing.message = message
    else:
        session.add(Alert(
            agent_id=agent_id,
            check_type=check_type,
            classification=classification,
            status="open",
            message=message,
            detail=detail,
        ))


async def run_agent_health_checks(
    session: AsyncSession,
    agent: Agent,
    include_federation: bool = True,
    operator: str = "monitor:health",
) -> dict[str, dict]:
    """Execute all health checks for a single agent and persist results."""
    rules = await _load_alert_rules(session)

    # Expected A0 fingerprint from registry if recorded
    expected_a0_fp = None
    for cred in agent.credential_fingerprints:
        if cred.domain == "a0_api_key":
            expected_a0_fp = cred.fingerprint
            break

    # Gather probes concurrently where safe
    whoami_task = get_whoami(agent.name, agent.homeserver_url)
    rooms_task = get_joined_rooms(agent.name, agent.homeserver_url)
    a0_task = check_a0_auth(agent.name, expected_fingerprint=expected_a0_fp)
    mcp_task = check_mcp_health(agent.name)
    proc_task = get_process_info(agent.name)
    containers_task = get_container_status(agent.name)
    sync_task = check_sync_cursor(agent.name, agent.homeserver_url)

    if include_federation:
        fed_task = check_and_refresh_federation_keys(agent.homeserver_fqdn)
        whoami, rooms_res, a0_res, mcp_res, proc_info, containers, sync_res, fed_res = await asyncio.gather(
            whoami_task, rooms_task, a0_task, mcp_task, proc_task, containers_task, sync_task, fed_task
        )
    else:
        whoami, rooms_res, a0_res, mcp_res, proc_info, containers, sync_res = await asyncio.gather(
            whoami_task, rooms_task, a0_task, mcp_task, proc_task, containers_task, sync_task
        )
        fed_res = None

    results: dict[str, dict] = {}

    # 1. matrix_auth
    if whoami.user_id:
        m_status = "pass"
        m_detail = {"user_id": whoami.user_id, "device_id": whoami.device_id}
    elif whoami.error in ("http_401", "http_403", "no_token"):
        m_status = "fail"
        m_detail = {"error": whoami.error}
    else:
        m_status = "warn"
        m_detail = {"error": whoami.error or "transient_auth_error"}
    await _record_check_and_act(session, agent, "matrix_auth", m_status, m_detail, rules, operator)
    results["matrix_auth"] = {"status": m_status, "detail": m_detail}

    # 2. identity
    if whoami.user_id and whoami.user_id == agent.matrix_user_id:
        id_status = "pass"
        id_detail = {"actual": whoami.user_id, "expected": agent.matrix_user_id}
    elif whoami.user_id and whoami.user_id != agent.matrix_user_id:
        id_status = "fail"
        id_detail = {
            "actual": whoami.user_id,
            "expected": agent.matrix_user_id,
            "error": "identity_mismatch",
        }
    elif whoami.error in ("http_401", "http_403", "no_token"):
        id_status = "fail"
        id_detail = {
            "actual": None,
            "expected": agent.matrix_user_id,
            "error": whoami.error,
        }
    else:
        id_status = "warn"
        id_detail = {
            "actual": None,
            "expected": agent.matrix_user_id,
            "error": whoami.error or "transient_whoami_error",
        }
    await _record_check_and_act(session, agent, "identity", id_status, id_detail, rules, operator)
    results["identity"] = {"status": id_status, "detail": id_detail}

    # 3. membership (with automatic repair if missing required rooms)
    rooms_ok, joined_rooms, rooms_err = rooms_res
    required_room_ids = [r.room_id for r in agent.required_rooms]
    if not rooms_ok:
        mem_status = "fail"
        mem_detail = {"error": rooms_err, "required": required_room_ids}
    else:
        missing = [rid for rid in required_room_ids if rid not in joined_rooms]
        if not missing:
            mem_status = "pass"
            mem_detail = {"joined_required": required_room_ids, "total_joined": len(joined_rooms)}
        else:
            # Attempt auto-repair for each missing room
            repaired = []
            failed_repairs = {}
            for rid in missing:
                rep_ok, rep_info = await repair_room_membership(
                    agent.name, agent.matrix_user_id, agent.homeserver_url, rid
                )
                if rep_ok:
                    repaired.append(rid)
                    session.add(AuditLog(
                        agent_id=agent.id,
                        action="membership_auto_repair",
                        detail={"room_id": rid, "status": "repaired", **rep_info},
                        operator=operator,
                    ))
                else:
                    failed_repairs[rid] = rep_info
                    session.add(AuditLog(
                        agent_id=agent.id,
                        action="membership_auto_repair_failed",
                        detail={"room_id": rid, "status": "failed", **rep_info},
                        operator=operator,
                    ))

            if len(repaired) == len(missing):
                mem_status = "pass"
                mem_detail = {
                    "joined_required": required_room_ids,
                    "auto_repaired": repaired,
                }
            else:
                mem_status = "fail"
                mem_detail = {
                    "missing_rooms": [r for r in missing if r not in repaired],
                    "auto_repaired": repaired,
                    "repair_errors": failed_repairs,
                }
                await _ensure_open_alert(
                    session,
                    agent_id=agent.id,
                    check_type="membership",
                    classification="TERMINAL_CONFIG",
                    message=f"Missing required room membership on {agent.name} and auto-repair failed",
                    detail=mem_detail,
                )

    await _record_check_and_act(session, agent, "membership", mem_status, mem_detail, rules, operator)
    results["membership"] = {"status": mem_status, "detail": mem_detail}

    # 4. a0_auth
    a0_status, a0_detail = a0_res
    await _record_check_and_act(session, agent, "a0_auth", a0_status, a0_detail, rules, operator)
    results["a0_auth"] = {"status": a0_status, "detail": a0_detail}

    # 5. mcp
    mcp_status, mcp_detail = mcp_res
    await _record_check_and_act(session, agent, "mcp", mcp_status, mcp_detail, rules, operator)
    results["mcp"] = {"status": mcp_status, "detail": mcp_detail}

    # 6. process
    all_containers_up = all(c.running for c in containers) and len(containers) == 3
    # If a terminal config fault just stopped the bot intentionally, don't auto-restart it via process check
    terminal_stopped = any(
        results[k]["status"] == "fail" for k in ("matrix_auth", "identity", "a0_auth")
    )
    if proc_info and all_containers_up and proc_info.bot_count == 1 and proc_info.supervisord_running:
        p_status = "pass"
        p_detail = {
            "bot_count": proc_info.bot_count,
            "bot_runtime": proc_info.bot_runtime,
            "supervisord": proc_info.supervisord_running,
            "containers_up": 3,
        }
    elif terminal_stopped and proc_info and proc_info.bot_count == 0:
        p_status = "warn"
        p_detail = {
            "bot_count": 0,
            "reason": "bot_stopped_due_to_terminal_config",
            "supervisord": proc_info.supervisord_running,
        }
    else:
        p_status = "fail"
        p_detail = {
            "bot_count": proc_info.bot_count if proc_info else 0,
            "supervisord": proc_info.supervisord_running if proc_info else False,
            "containers": {c.name: c.running for c in containers},
        }
    await _record_check_and_act(session, agent, "process", p_status, p_detail, rules, operator)
    results["process"] = {"status": p_status, "detail": p_detail}

    # 7. sync_cursor
    sync_ok, sync_detail = sync_res
    sc_status = "pass" if sync_ok else "fail"
    await _record_check_and_act(session, agent, "sync_cursor", sc_status, sync_detail, rules, operator)
    results["sync_cursor"] = {"status": sc_status, "detail": sync_detail}

    # 8. federation
    if fed_res is not None:
        fed_status, fed_detail = fed_res
        await _record_check_and_act(session, agent, "federation", fed_status, fed_detail, rules, operator)
        results["federation"] = {"status": fed_status, "detail": fed_detail}

    await session.commit()
    return results


async def run_fleet_health_cycle(include_federation: bool = True, operator: str = "monitor:health") -> None:
    """Run health checks across all active agents in the fleet."""
    global last_monitor_run
    async with async_session() as session:
        result = await session.execute(
            select(Agent).where(Agent.status == "active").order_by(Agent.instance_num)
        )
        agents = result.scalars().all()
        for agent in agents:
            try:
                await run_agent_health_checks(
                    session,
                    agent,
                    include_federation=include_federation,
                    operator=operator,
                )
            except Exception as e:
                logger.exception("Health check failed for %s: %s", agent.name, e)
        try:
            await check_backup_freshness(session)
        except Exception as e:
            logger.exception("Backup freshness check failed: %s", e)
        last_monitor_run = datetime.now(timezone.utc)


async def background_health_loop() -> None:
    """Background task running periodic health checks for the fleet."""
    logger.info(
        "Starting background health monitor (interval=%ds, federation_interval=%ds)",
        settings.health_check_interval_secs,
        settings.federation_check_interval_secs,
    )
    last_fed_ts = 0.0
    while True:
        try:
            now_ts = asyncio.get_event_loop().time()
            do_fed = (now_ts - last_fed_ts) >= settings.federation_check_interval_secs or last_fed_ts == 0.0
            await run_fleet_health_cycle(include_federation=do_fed, operator="monitor:background")
            if do_fed:
                last_fed_ts = now_ts
        except asyncio.CancelledError:
            logger.info("Background health monitor cancelled")
            break
        except Exception as e:
            logger.exception("Error in background health monitor loop: %s", e)

        await asyncio.sleep(settings.health_check_interval_secs)
