"""Backup and restore verification schemas (Phase 5)."""

from datetime import datetime

from pydantic import BaseModel


class BackupArtifactResponse(BaseModel):
    id: int
    backup_type: str
    target: str
    file_path: str
    size_bytes: int
    checksum_sha256: str
    offsite_synced: bool
    status: str
    detail: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BackupSuiteRunResponse(BaseModel):
    backup_type: str
    backup_dir: str
    offsite_target: str
    offsite_synced: bool
    pruned_dirs: list[str] = []
    artifacts: list[BackupArtifactResponse]
    completed_at: datetime


class BackupVerifyResponse(BaseModel):
    verified: bool
    open_brain_dump_id: int | None = None
    fleet_ops_dump_id: int | None = None
    open_brain_live_thoughts: int
    open_brain_restored_thoughts: int
    fleet_ops_live_agents: int
    fleet_ops_restored_agents: int
    pgvector_index_present: bool
    scratch_db_cleaned: bool
    detail: dict | None = None
    verified_at: datetime
