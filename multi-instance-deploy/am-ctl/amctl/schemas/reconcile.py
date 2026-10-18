"""Reconciliation engine schemas (Phase 4)."""

from datetime import datetime

from pydantic import BaseModel


class DriftItem(BaseModel):
    drift_type: str  # 'identity' | 'membership' | 'credential' | 'secret_delivery' | 'process' | 'artifact_hash'
    status: str      # 'clean' | 'drift'
    expected: str | dict | list | None = None
    actual: str | dict | list | None = None
    detail: dict | None = None


class PlannedAction(BaseModel):
    step: int
    action_type: str
    description: str
    target: str
    detail: dict | None = None


class AgentDriftReport(BaseModel):
    agent_id: int
    agent_name: str
    instance_num: int
    clean: bool
    drift_count: int
    checks: list[DriftItem]
    checked_at: datetime


class FleetDriftReport(BaseModel):
    total_agents: int
    clean_agents: int
    drifted_agents: int
    has_fingerprint_collisions: bool
    collisions: list[dict] = []
    agents: list[AgentDriftReport]
    checked_at: datetime


class ReconcilePlanResponse(BaseModel):
    agent_id: int
    agent_name: str
    clean: bool
    drift_report: AgentDriftReport
    actions: list[PlannedAction]
    computed_at: datetime


class AppliedActionResult(BaseModel):
    step: int
    action_type: str
    target: str
    status: str  # 'applied' | 'failed' | 'skipped'
    detail: dict | None = None


class ReconcileApplyResponse(BaseModel):
    agent_id: int
    agent_name: str
    noop: bool
    success: bool
    snapshot_dir: str | None = None
    actions_executed: list[AppliedActionResult]
    pre_check: AgentDriftReport
    post_check: AgentDriftReport
    applied_at: datetime


class ReconcileHistoryEntry(BaseModel):
    id: int
    agent_id: int | None = None
    agent_name: str | None = None
    mode: str
    result: dict
    operator: str
    created_at: datetime

    model_config = {"from_attributes": True}
