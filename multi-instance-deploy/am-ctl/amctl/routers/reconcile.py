"""Reconciliation API endpoints (Phase 4): read-only check, plan, and history."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.agent import Agent
from amctl.models.reconcile import ReconcileRun
from amctl.schemas.reconcile import (
    AgentDriftReport,
    FleetDriftReport,
    ReconcileApplyResponse,
    ReconcileHistoryEntry,
    ReconcilePlanResponse,
)
from amctl.services.reconciler import (
    apply_agent_reconciliation,
    check_agent_drift,
    check_fleet_drift,
    compute_agent_plan,
)

router = APIRouter(prefix="/api/v1/reconcile", tags=["reconcile"])


@router.post("/check", response_model=FleetDriftReport | AgentDriftReport)
async def reconcile_check(
    agent_name: str | None = Query(default=None, description="Optional single agent name to check"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Read-only drift check across the fleet or for a single agent.
    Guarantees zero DB writes and zero container/host writes.
    """
    if agent_name:
        res = await session.execute(select(Agent).where(Agent.name == agent_name))
        agent = res.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        return await check_agent_drift(session, agent)

    return await check_fleet_drift(session)


@router.post("/plan/{agent_name}", response_model=ReconcilePlanResponse)
async def reconcile_plan(
    agent_name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Compute a read-only remediation plan for a single agent.
    Guarantees zero DB writes and zero container/host writes.
    """
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return await compute_agent_plan(session, agent)


@router.post("/apply/{agent_name}", response_model=ReconcileApplyResponse)
async def reconcile_apply(
    agent_name: str,
    operator: str = Query(default="api:reconcile_apply"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Apply planned reconciliation actions for a single agent, log mutations
    to audit_log, and verify post-apply drift state.
    """
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return await apply_agent_reconciliation(session, agent, operator=operator)


@router.get("/history", response_model=list[ReconcileHistoryEntry])
async def reconcile_history(
    agent_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """List past reconciliation runs."""
    agents_res = await session.execute(select(Agent))
    agent_map = {a.id: a.name for a in agents_res.scalars().all()}

    stmt = select(ReconcileRun).order_by(ReconcileRun.created_at.desc()).limit(limit)
    if agent_name:
        target = next((aid for aid, aname in agent_map.items() if aname == agent_name), None)
        if target is None:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        stmt = stmt.where(ReconcileRun.agent_id == target)

    res = await session.execute(stmt)
    runs = res.scalars().all()
    out = []
    for r in runs:
        entry = ReconcileHistoryEntry.model_validate(r)
        entry.agent_name = agent_map.get(r.agent_id) if r.agent_id else "fleet"
        out.append(entry)
    return out
