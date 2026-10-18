"""Health and alert API endpoints (Phase 2)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.models.health import Alert, AlertRule, HealthCheck, HealthState
from amctl.schemas.health import (
    AgentHealthSummary,
    AlertAckRequest,
    AlertResponse,
    CheckStateResponse,
    FleetHealthResponse,
    HealthHistoryEntry,
    HealthReportRequest,
)
import amctl.services.health_engine as health_engine

router = APIRouter(prefix="/api/v1", tags=["health"])


def _compute_overall_status(checks: dict[str, CheckStateResponse]) -> str:
    if not checks:
        return "unknown"
    statuses = [c.status for c in checks.values()]
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


@router.get("/health/fleet", response_model=FleetHealthResponse)
async def get_fleet_health(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Return materialized fleet health matrix from DB (sub-500ms)."""
    agents_res = await session.execute(select(Agent).order_by(Agent.instance_num))
    agents = agents_res.scalars().all()

    states_res = await session.execute(select(HealthState))
    all_states = states_res.scalars().all()

    alerts_count_res = await session.execute(
        select(func.count(Alert.id)).where(Alert.status == "open")
    )
    open_alerts = alerts_count_res.scalar() or 0

    by_agent: dict[int, dict[str, CheckStateResponse]] = {a.id: {} for a in agents}
    latest_check_ts: datetime | None = health_engine.last_monitor_run

    for st in all_states:
        if st.agent_id in by_agent:
            by_agent[st.agent_id][st.check_type] = CheckStateResponse.model_validate(st)
            if latest_check_ts is None or (st.last_check and st.last_check > latest_check_ts):
                latest_check_ts = st.last_check

    summaries = []
    healthy = 0
    degraded = 0
    failing = 0

    for a in agents:
        checks = by_agent.get(a.id, {})
        overall = _compute_overall_status(checks)
        if overall == "pass":
            healthy += 1
        elif overall == "warn":
            degraded += 1
        elif overall == "fail":
            failing += 1
        summaries.append(
            AgentHealthSummary(
                agent_id=a.id,
                agent_name=a.name,
                instance_num=a.instance_num,
                overall_status=overall,
                checks=checks,
            )
        )

    return FleetHealthResponse(
        total_agents=len(agents),
        healthy_agents=healthy,
        degraded_agents=degraded,
        failing_agents=failing,
        open_alerts=open_alerts,
        last_monitor_run=latest_check_ts,
        agents=summaries,
    )


@router.post("/health/fleet/check", response_model=FleetHealthResponse)
async def trigger_fleet_health_check(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Trigger an immediate health check across all active agents."""
    await health_engine.run_fleet_health_cycle(include_federation=True, operator="api:manual_check")
    return await get_fleet_health(session=session, _key=_key)


@router.get("/health/{agent_name}", response_model=AgentHealthSummary)
async def get_agent_health(
    agent_name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Get materialized health detail for a single agent."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    st_res = await session.execute(
        select(HealthState).where(HealthState.agent_id == agent.id)
    )
    states = st_res.scalars().all()
    checks = {s.check_type: CheckStateResponse.model_validate(s) for s in states}

    return AgentHealthSummary(
        agent_id=agent.id,
        agent_name=agent.name,
        instance_num=agent.instance_num,
        overall_status=_compute_overall_status(checks),
        checks=checks,
    )


@router.post("/health/{agent_name}/check", response_model=AgentHealthSummary)
async def trigger_agent_health_check(
    agent_name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Trigger immediate live health checks for one agent and return updated state."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    await health_engine.run_agent_health_checks(
        session, agent, include_federation=True, operator="api:manual_check"
    )
    return await get_agent_health(agent_name=agent_name, session=session, _key=_key)


@router.post("/health/{agent_name}/report", response_model=AgentHealthSummary)
async def report_agent_health(
    agent_name: str,
    report: HealthReportRequest,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Ingest health check results reported from inside the container
    (preflight-check.sh or watchdog.sh v3.0) and apply alert_rules classification.
    """
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    rules = await health_engine._load_alert_rules(session)
    for item in report.checks:
        detail = dict(item.detail or {})
        detail["reported_by"] = report.reporter
        await health_engine._record_check_and_act(
            session=session,
            agent=agent,
            check_type=item.check_type,
            status=item.status,
            detail=detail,
            rules=rules,
            operator=report.reporter,
        )
    await session.commit()
    return await get_agent_health(agent_name=agent_name, session=session, _key=_key)


@router.get("/health/rules/all")
async def list_alert_rules(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Return configured alert_rules (used by watchdog v3.0 inside containers)."""
    res = await session.execute(select(AlertRule).order_by(AlertRule.id))
    rules = res.scalars().all()
    return [
        {
            "check_type": r.check_type,
            "classification": r.classification,
            "action": r.action,
            "max_retries": r.max_retries,
            "cooldown_secs": r.cooldown_secs,
        }
        for r in rules
    ]


@router.get("/health/{agent_name}/history", response_model=list[HealthHistoryEntry])
async def get_agent_health_history(
    agent_name: str,
    check_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Get time-series health check history for an agent."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    stmt = select(HealthCheck).where(HealthCheck.agent_id == agent.id)
    if check_type:
        stmt = stmt.where(HealthCheck.check_type == check_type)
    stmt = stmt.order_by(HealthCheck.checked_at.desc()).limit(limit)

    hist_res = await session.execute(stmt)
    return hist_res.scalars().all()


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status: str | None = Query(default="open"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """List alerts (defaults to open alerts; pass status=all for all)."""
    agents_res = await session.execute(select(Agent))
    agent_names = {a.id: a.name for a in agents_res.scalars().all()}

    stmt = select(Alert).order_by(Alert.created_at.desc())
    if status and status != "all":
        stmt = stmt.where(Alert.status == status)

    res = await session.execute(stmt)
    alerts = res.scalars().all()
    out = []
    for al in alerts:
        resp = AlertResponse.model_validate(al)
        resp.agent_name = agent_names.get(al.agent_id)
        out.append(resp)
    return out


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    body: AlertAckRequest | None = None,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Acknowledge an active alert."""
    res = await session.execute(select(Alert).where(Alert.id == alert_id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    operator = body.operator if body else "api:key"
    alert.status = "acked"
    alert.acked_at = datetime.now(timezone.utc)
    alert.acked_by = operator

    session.add(AuditLog(
        agent_id=alert.agent_id,
        action="alert_ack",
        detail={"alert_id": alert.id, "check_type": alert.check_type},
        operator=operator,
    ))
    await session.commit()
    await session.refresh(alert)

    agent_res = await session.execute(select(Agent).where(Agent.id == alert.agent_id))
    agent = agent_res.scalar_one_or_none()
    resp = AlertResponse.model_validate(alert)
    resp.agent_name = agent.name if agent else None
    return resp
