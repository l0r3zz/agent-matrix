"""Release & fleet deployment API endpoints (Phase 6)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.agent import Agent
from amctl.models.deploy import Release
from amctl.schemas.deploy import (
    DeployRequest,
    DeployResultResponse,
    FleetDeployStatusResponse,
    ReleaseCreateRequest,
    ReleaseResponse,
    VersionUpdateRequest,
    VersionUpdateResponse,
)
from amctl.services.deployer import (
    create_or_register_release,
    deploy_release_to_agent,
    get_fleet_deploy_status,
    update_agent_image_version,
)

router = APIRouter(prefix="/api/v1", tags=["deploy"])


@router.post("/releases", response_model=ReleaseResponse)
async def register_release(
    req: ReleaseCreateRequest,
    operator: str = Query(default="api:release"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Build or register a release bundle with SHA-256 artifact checksums."""
    try:
        return await create_or_register_release(
            session, version=req.version, bundle_path=req.bundle_path, operator=operator
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/releases", response_model=list[ReleaseResponse])
async def list_releases(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """List registered releases."""
    res = await session.execute(select(Release).order_by(Release.created_at.desc()))
    return res.scalars().all()


@router.get("/deploy/status", response_model=FleetDeployStatusResponse)
async def deploy_status(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Fleet-wide deployment and version overview (absorbs update-fleet.sh --status)."""
    return await get_fleet_deploy_status(session)


@router.post("/deploy/{agent_name}", response_model=DeployResultResponse)
async def deploy_to_agent(
    agent_name: str,
    req: DeployRequest,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Deploy a registered release bundle to a single agent."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    try:
        return await deploy_release_to_agent(
            session, agent, version=req.version, operator=req.operator
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deploy/{agent_name}/version", response_model=VersionUpdateResponse)
async def update_agent_version(
    agent_name: str,
    req: VersionUpdateRequest,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Update Agent Zero Docker image version for a single agent."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    try:
        return await update_agent_image_version(
            session,
            agent,
            image_version=req.image_version,
            skip_restart=req.skip_restart,
            force=req.force,
            operator=req.operator,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
