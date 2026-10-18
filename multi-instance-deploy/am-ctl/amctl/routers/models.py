"""Model configuration API endpoints (Phase 7)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.agent import Agent
from amctl.schemas.model_config import (
    AgentModelConfigResponse,
    FleetModelsDiagnoseResponse,
    FleetModelsResponse,
    ModelSetRequest,
)
from amctl.services.model_manager import (
    diagnose_fleet_models,
    get_agent_model_config,
    get_fleet_models,
    set_agent_model_config,
)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("", response_model=FleetModelsResponse)
async def list_fleet_models(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Fleet-wide model matrix (absorbs fleet-models.sh)."""
    return await get_fleet_models(session)


@router.post("/diagnose", response_model=FleetModelsDiagnoseResponse)
async def diagnose_models(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Run model availability and config sync diagnostics across the fleet."""
    return await diagnose_fleet_models(session)


@router.get("/{agent_name}", response_model=AgentModelConfigResponse)
async def get_models_for_agent(
    agent_name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Get active preset and model slots for a single agent."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return await get_agent_model_config(session, agent)


@router.put("/{agent_name}", response_model=AgentModelConfigResponse)
async def set_models_for_agent(
    agent_name: str,
    req: ModelSetRequest,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Update active preset and/or chat, utility, embedding model slots for an agent."""
    res = await session.execute(select(Agent).where(Agent.name == agent_name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    try:
        return await set_agent_model_config(
            session,
            agent,
            chat_model=req.chat_model,
            utility_model=req.utility_model,
            embedding_model=req.embedding_model,
            preset=req.preset,
            operator=req.operator,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
