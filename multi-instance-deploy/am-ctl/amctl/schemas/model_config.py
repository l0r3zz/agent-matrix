"""Model configuration schemas (Phase 7)."""

from datetime import datetime

from pydantic import BaseModel


class AgentModelConfigResponse(BaseModel):
    agent_id: int
    agent_name: str
    instance_num: int
    profile: str
    selected_preset: str
    chat_model: str
    utility_model: str
    embedding_model: str
    ctx_length: int = 0
    vision: bool = False
    available_presets: list[str] = []
    updated_at: datetime | None = None


class FleetModelsResponse(BaseModel):
    total_agents: int
    online_agents: int
    agents: list[AgentModelConfigResponse]


class ModelSetRequest(BaseModel):
    chat_model: str | None = None
    utility_model: str | None = None
    embedding_model: str | None = None
    preset: str | None = None
    operator: str = "cli:models"


class ModelDiagnoseItem(BaseModel):
    agent_name: str
    preset: str
    config_json_valid: bool
    presets_yaml_valid: bool
    db_synced: bool
    api_keys_present: dict[str, bool]
    status: str  # 'pass' | 'warn' | 'fail'
    issues: list[str] = []


class FleetModelsDiagnoseResponse(BaseModel):
    overall_status: str
    agents: list[ModelDiagnoseItem]
