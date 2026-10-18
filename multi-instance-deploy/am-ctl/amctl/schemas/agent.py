"""Agent schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel


class RoomInfo(BaseModel):
    room_id: str
    room_name: str | None = None

    model_config = {"from_attributes": True}


class CredentialInfo(BaseModel):
    domain: str
    fingerprint: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class AgentBase(BaseModel):
    instance_num: int
    name: str
    matrix_user_id: str
    homeserver_url: str
    homeserver_fqdn: str
    agent_zero_endpoint: str = "http://localhost:80"
    bot_runtime: str = "rust"
    status: str = "active"
    release_version: str | None = None


class AgentResponse(AgentBase):
    """Agent record from the registry."""
    id: int
    created_at: datetime
    updated_at: datetime
    required_rooms: list[RoomInfo] = []
    credential_fingerprints: list[CredentialInfo] = []

    model_config = {"from_attributes": True}


class AgentUpdate(BaseModel):
    """Fields that can be updated on an agent."""
    status: str | None = None
    bot_runtime: str | None = None
    release_version: str | None = None
    agent_zero_endpoint: str | None = None


class ContainerStatus(BaseModel):
    """Live container status from Docker."""
    name: str
    running: bool
    uptime: str | None = None


class ProcessInfo(BaseModel):
    """Process info from inside the agent container."""
    bot_count: int
    bot_runtime: str | None = None
    mcp_running: bool
    watchdog_running: bool
    supervisord_running: bool


class MatrixIdentity(BaseModel):
    """Live identity from /whoami."""
    user_id: str | None = None
    device_id: str | None = None
    error: str | None = None


class AgentLiveStatus(BaseModel):
    """Live status combining registry + Docker + Matrix data."""
    agent: AgentResponse
    containers: list[ContainerStatus]
    processes: ProcessInfo | None = None
    identity: MatrixIdentity | None = None


class FleetSummary(BaseModel):
    """Fleet-wide summary."""
    total_agents: int
    active: int
    containers_running: int
    containers_down: int
    agents: list[AgentResponse]
