"""Health and alert schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel


class CheckStateResponse(BaseModel):
    check_type: str
    status: str
    detail: dict | None = None
    since: datetime
    last_check: datetime
    fail_count: int = 0

    model_config = {"from_attributes": True}


class AgentHealthSummary(BaseModel):
    agent_id: int
    agent_name: str
    instance_num: int
    overall_status: str  # 'pass' | 'warn' | 'fail' | 'unknown'
    checks: dict[str, CheckStateResponse]


class FleetHealthResponse(BaseModel):
    total_agents: int
    healthy_agents: int
    degraded_agents: int
    failing_agents: int
    open_alerts: int
    last_monitor_run: datetime | None = None
    agents: list[AgentHealthSummary]


class HealthHistoryEntry(BaseModel):
    id: int
    agent_id: int
    check_type: str
    status: str
    detail: dict | None = None
    checked_at: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: int
    agent_id: int
    agent_name: str | None = None
    check_type: str
    classification: str
    status: str
    message: str
    detail: dict | None = None
    created_at: datetime
    acked_at: datetime | None = None
    acked_by: datetime | str | None = None
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertAckRequest(BaseModel):
    operator: str = "cli:operator"


class CheckReportItem(BaseModel):
    check_type: str
    status: str  # 'pass' | 'warn' | 'fail'
    detail: dict | None = None


class HealthReportRequest(BaseModel):
    reporter: str = "watchdog:v3"
    checks: list[CheckReportItem]

