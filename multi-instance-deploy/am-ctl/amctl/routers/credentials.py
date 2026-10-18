"""Credential authority & collision detection endpoints (Phase 3)."""

from datetime import datetime, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.db import get_session
from amctl.middleware.auth import require_api_key
from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.models.credential import CredentialFingerprint, TrustedSender
from amctl.schemas.credential import (
    AgentCredentialsResponse,
    CollisionCheckResponse,
    CollisionItem,
    CredentialRecord,
    CredentialVerifyResponse,
    TrustedSenderItem,
)
from amctl.services.agent_zero import (
    _read_bot_a0_key,
    check_a0_auth,
    derive_canonical_a0_fingerprint,
)

router = APIRouter(prefix="/api/v1", tags=["credentials"])


@router.get("/agents/{name}/credentials", response_model=AgentCredentialsResponse)
async def get_agent_credentials(
    name: str,
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Return recorded credential fingerprints for an agent (never plaintext secrets)."""
    res = await session.execute(select(Agent).where(Agent.name == name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    creds = [CredentialRecord.model_validate(c) for c in agent.credential_fingerprints]
    return AgentCredentialsResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        credentials=creds,
    )


@router.post("/agents/{name}/credentials/verify", response_model=CredentialVerifyResponse)
async def verify_agent_credentials(
    name: str,
    sync_registry: bool = Query(default=True, description="Update DB fingerprint if canonical & deployed match"),
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Validate that the agent's deployed credential matches Agent Zero's canonical
    create_auth_token() and passes an authenticated API probe.
    """
    res = await session.execute(select(Agent).where(Agent.name == name))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    reg_fp = None
    reg_record = None
    for c in agent.credential_fingerprints:
        if c.domain == "a0_api_key":
            reg_fp = c.fingerprint
            reg_record = c
            break

    canonical_fp, derive_err = await derive_canonical_a0_fingerprint(agent.name)
    deployed_key, key_source = await _read_bot_a0_key(agent.name)
    deployed_fp = hashlib.sha256(deployed_key.encode()).hexdigest()[:12] if deployed_key else None

    probe_status, probe_detail = await check_a0_auth(agent.name, expected_fingerprint=canonical_fp)

    valid = (
        canonical_fp is not None
        and deployed_fp is not None
        and canonical_fp == deployed_fp
        and probe_status == "pass"
    )

    if valid and sync_registry and reg_fp != canonical_fp:
        now = datetime.now(timezone.utc)
        if reg_record:
            old_fp = reg_record.fingerprint
            reg_record.fingerprint = canonical_fp
            reg_record.recorded_at = now
        else:
            old_fp = None
            reg_record = CredentialFingerprint(
                agent_id=agent.id,
                domain="a0_api_key",
                fingerprint=canonical_fp,
                recorded_at=now,
            )
            session.add(reg_record)
        session.add(AuditLog(
            agent_id=agent.id,
            action="credential_fingerprint_sync",
            detail={"domain": "a0_api_key", "old": old_fp, "new": canonical_fp, "source": key_source},
            operator="api:credentials_verify",
        ))
        await session.commit()
        reg_fp = canonical_fp
    elif valid and reg_fp != canonical_fp:
        valid = False

    return CredentialVerifyResponse(
        agent_name=agent.name,
        valid=valid,
        canonical_fingerprint=canonical_fp,
        deployed_fingerprint=deployed_fp,
        registry_fingerprint=reg_fp,
        secret_file_source=key_source,
        a0_probe_status=probe_status,
        detail=probe_detail if not derive_err else {**(probe_detail or {}), "derive_error": derive_err},
    )


@router.get("/credentials/collisions", response_model=CollisionCheckResponse)
async def check_credential_collisions(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Detect any cross-fleet credential fingerprint collisions across sovereign agents."""
    res = await session.execute(select(Agent).order_by(Agent.instance_num))
    agents = res.scalars().all()
    agent_map = {a.id: a.name for a in agents}

    fp_res = await session.execute(select(CredentialFingerprint))
    fps = fp_res.scalars().all()

    by_domain_fp: dict[tuple[str, str], list[str]] = {}
    for fp in fps:
        aname = agent_map.get(fp.agent_id, f"agent_id:{fp.agent_id}")
        key = (fp.domain, fp.fingerprint)
        by_domain_fp.setdefault(key, []).append(aname)

    collisions = [
        CollisionItem(domain=domain, fingerprint=fingerprint, agents=sorted(agent_names))
        for (domain, fingerprint), agent_names in by_domain_fp.items()
        if len(agent_names) > 1
    ]

    return CollisionCheckResponse(
        has_collisions=len(collisions) > 0,
        collisions=collisions,
    )


@router.get("/trusted-senders", response_model=list[TrustedSenderItem])
async def list_trusted_senders(
    session: AsyncSession = Depends(get_session),
    _key: str = Depends(require_api_key),
):
    """Return trusted Matrix user IDs for bot invite auto-join (Phase 8)."""
    res = await session.execute(select(TrustedSender).order_by(TrustedSender.id))
    return res.scalars().all()

