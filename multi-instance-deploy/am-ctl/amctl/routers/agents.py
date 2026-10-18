"""Agent registry API endpoints."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.schemas.agent import (
    AgentLiveStatus,
    AgentResponse,
    AgentUpdate,
    FleetSummary,
)
from amctl.services.docker import get_container_status, get_process_info
from amctl.services.matrix import get_whoami

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agents"])


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """List all agents in the registry."""
    result = await session.execute(
        select(Agent).order_by(Agent.instance_num)
    )
    return result.scalars().all()


@router.get("/agents/{name}", response_model=AgentResponse)
async def get_agent(
    name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Get a single agent by name."""
    result = await session.execute(
        select(Agent).where(Agent.name == name)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return agent


@router.put("/agents/{name}", response_model=AgentResponse)
async def update_agent(
    name: str,
    update: AgentUpdate,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Update mutable fields on an agent."""
    result = await session.execute(
        select(Agent).where(Agent.name == name)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    update_data = update.model_dump(exclude_unset=True)
    changes = {}
    for field, value in update_data.items():
        old_val = getattr(agent, field)
        if old_val != value:
            changes[field] = {"old": old_val, "new": value}
        setattr(agent, field, value)

    audit = AuditLog(
        agent_id=agent.id,
        action="agent_update",
        detail={"updated_fields": update_data, "changes": changes},
        operator="api:key",
    )
    session.add(audit)

    await session.commit()
    await session.refresh(agent)
    return agent


@router.get("/agents/{name}/status", response_model=AgentLiveStatus)
async def get_agent_status(
    name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Get live status for an agent: registry + Docker + Matrix."""
    result = await session.execute(
        select(Agent).where(Agent.name == name)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    containers, processes, identity = await asyncio.gather(
        get_container_status(agent.name),
        get_process_info(agent.name),
        get_whoami(agent.name, agent.homeserver_url),
    )

    return AgentLiveStatus(
        agent=agent,
        containers=containers,
        processes=processes,
        identity=identity,
    )


@router.get("/status", response_model=FleetSummary)
async def get_fleet_status(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Fleet-wide summary with container status."""
    result = await session.execute(
        select(Agent).order_by(Agent.instance_num)
    )
    agents = result.scalars().all()

    container_checks = await asyncio.gather(
        *[get_container_status(a.name) for a in agents]
    )

    running = sum(
        1 for containers in container_checks
        if any(c.running and c.name.startswith("agent0-") and "-" not in c.name.split("agent0-")[1] for c in containers)
    )

    return FleetSummary(
        total_agents=len(agents),
        active=sum(1 for a in agents if a.status == "active"),
        containers_running=running,
        containers_down=len(agents) - running,
        agents=agents,
    )
