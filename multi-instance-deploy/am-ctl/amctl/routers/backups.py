"""Backup & restore verification API endpoints (Phase 5)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.backup import BackupRun
from amctl.schemas.backup import (
    BackupArtifactResponse,
    BackupSuiteRunResponse,
    BackupVerifyResponse,
)
from amctl.services.backup import (
    check_backup_freshness,
    execute_backup_suite,
    verify_latest_backups,
)

router = APIRouter(prefix="/api/v1/backups", tags=["backups"])


@router.post("/run", response_model=BackupSuiteRunResponse)
async def run_backup(
    backup_type: str = Query(default="manual", description="daily_full | pre_deploy | manual"),
    operator: str = Query(default="api:backup"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Trigger an immediate backup of open_brain, fleet_ops, globals, and infra_configs."""
    return await execute_backup_suite(session, backup_type=backup_type, operator=operator)


@router.get("", response_model=list[BackupArtifactResponse])
async def list_backups(
    target: str | None = Query(default=None),
    limit: int = Query(default=40, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """List recent backup runs."""
    stmt = select(BackupRun).order_by(BackupRun.created_at.desc()).limit(limit)
    if target:
        stmt = stmt.where(BackupRun.target == target)
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("/verify", response_model=BackupVerifyResponse)
async def verify_latest_backup_suite(
    operator: str = Query(default="api:backup_verify"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Run non-destructive scratch-DB restore verification on the latest open_brain and fleet_ops dumps."""
    try:
        return await verify_latest_backups(session, backup_id=None, operator=operator)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{backup_id}/verify", response_model=BackupVerifyResponse)
async def verify_specific_backup(
    backup_id: int,
    operator: str = Query(default="api:backup_verify"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Run non-destructive scratch-DB restore verification targeting a specific backup_id."""
    try:
        return await verify_latest_backups(session, backup_id=backup_id, operator=operator)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-freshness")
async def trigger_backup_freshness_check(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Evaluate backup freshness and open/resolve backup_freshness alerts accordingly."""
    status, details = await check_backup_freshness(session)
    return {"status": status, "details": details}
