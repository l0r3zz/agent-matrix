"""Credential authority and identity schemas (Phase 3)."""

from datetime import datetime

from pydantic import BaseModel


class CredentialRecord(BaseModel):
    domain: str
    fingerprint: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class AgentCredentialsResponse(BaseModel):
    agent_id: int
    agent_name: str
    credentials: list[CredentialRecord]


class CredentialVerifyResponse(BaseModel):
    agent_name: str
    valid: bool
    canonical_fingerprint: str | None = None
    deployed_fingerprint: str | None = None
    registry_fingerprint: str | None = None
    secret_file_source: str
    a0_probe_status: str
    detail: dict | None = None


class CollisionItem(BaseModel):
    domain: str
    fingerprint: str
    agents: list[str]


class CollisionCheckResponse(BaseModel):
    has_collisions: bool
    collisions: list[CollisionItem]


class TrustedSenderItem(BaseModel):
    id: int
    matrix_user_id: str
    trust_level: str

    model_config = {"from_attributes": True}

