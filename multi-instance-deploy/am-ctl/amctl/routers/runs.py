"""Read operational runs. Writers are the provisioner, decommission, and control-plane services."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.oplog import OperationalRun

router = APIRouter(prefix="/api/v1", tags=["runs"])


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _run_summary(run: OperationalRun) -> dict:
    return {
        "run_id": run.run_id,
        "action": run.action,
        "target": run.target,
        "actor": run.actor,
        "outcome": run.outcome,
        "started_at": _iso(run.started_at),
        "ended_at": _iso(run.ended_at),
    }


def _stages(run: OperationalRun) -> list[dict]:
    starts: dict[str, datetime] = {}
    rows = []
    for stage in run.stages:
        item = {
            "stage": stage.stage,
            "phase": stage.phase,
            "severity": stage.severity,
            "body": stage.body,
            "observed_at": _iso(stage.observed_at),
            "cause": stage.cause,
            "exit_status": stage.exit_status,
            "truncated": stage.truncated,
            "stdout_tail": stage.stdout_tail,
            "stderr_tail": stage.stderr_tail,
            "instance_present": stage.instance_present,
        }
        if stage.phase == "start":
            starts[stage.stage] = _aware(stage.observed_at)
            item["duration_seconds"] = None
        else:
            started = starts.get(stage.stage)
            if started is None:
                item["duration_seconds"] = None
            else:
                item["duration_seconds"] = (_aware(stage.observed_at) - started).total_seconds()
        rows.append(item)
    return rows


@router.get("/runs")
async def list_runs(
    target: str | None = None,
    action: str | None = None,
    limit: int = Query(default=20),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Newest runs. The list does not include stage tails."""
    bounded = min(max(limit, 1), 100)
    stmt = select(OperationalRun).order_by(OperationalRun.started_at.desc()).limit(bounded)
    if target is not None:
        stmt = stmt.where(OperationalRun.target == target)
    if action is not None:
        stmt = stmt.where(OperationalRun.action == action)
    result = await session.execute(stmt)
    return [_run_summary(run) for run in result.scalars().all()]


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """One run and its stages in write order."""
    result = await session.execute(
        select(OperationalRun)
        .where(OperationalRun.run_id == run_id)
        .options(selectinload(OperationalRun.stages))
    )
    run = result.scalar_one_or_none()
    if run is None:
        return JSONResponse(
            status_code=404,
            content={"outcome": "not_found", "run_id": run_id, "stages": []},
        )
    body = _run_summary(run)
    body["stages"] = _stages(run)
    return body
