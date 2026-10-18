"""Release and deployment schemas (Phase 6)."""

from datetime import datetime

from pydantic import BaseModel


class ReleaseCreateRequest(BaseModel):
    version: str
    bundle_path: str | None = None


class ReleaseResponse(BaseModel):
    id: int
    version: str
    bundle_path: str | None = None
    checksum_sha256: str
    artifact_hashes: dict[str, str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DeployRequest(BaseModel):
    version: str
    operator: str = "cli:deploy"


class DeployResultResponse(BaseModel):
    deployment_id: int
    agent_id: int
    agent_name: str
    release_version: str
    status: str
    preserved_state: dict
    health_passed: bool
    drift_clean: bool
    detail: dict | None = None
    deployed_at: datetime


class VersionUpdateRequest(BaseModel):
    image_version: str
    skip_restart: bool = False
    force: bool = False
    operator: str = "cli:deploy_version"


class VersionUpdateResponse(BaseModel):
    agent_name: str
    previous_version: str
    target_version: str
    compose_updated: bool
    container_recreated: bool
    health_passed: bool
    status: str
    detail: dict | None = None


class AgentDeployStatusItem(BaseModel):
    agent_name: str
    instance_num: int
    container_state: str
    running_a0_version: str
    compose_a0_version: str
    version_drift: bool
    release_version: str | None = None
    bot_count: int
    mcp_status: str
    supervisord: bool
    reconcile_clean: bool
    last_deployment_at: datetime | None = None
    last_deployment_status: str | None = None


class FleetDeployStatusResponse(BaseModel):
    total_agents: int
    up_agents: int
    clean_agents: int
    latest_release: str | None = None
    agents: list[AgentDeployStatusItem]
