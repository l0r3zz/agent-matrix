"""Open, extend, finish, interrupt, and expire operational runs."""

import asyncio
import os
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.oplog import ACTIONS, OperationalRun, OperationalStage
from amctl.oplog import export

TAIL_LIMIT = 8 * 1024
RETENTION_DAYS = 30

_BEARER = re.compile(r"Bearer\s+\S+", re.IGNORECASE)
_SECRET_VALUE = re.compile(r"\b(?:syt_|sk-or-)[A-Za-z0-9._\-]+")
_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Za-z0-9_]*(?:password|token|api_key|secret)[A-Za-z0-9_]*)\s*=\s*\S+"
)


def redact(text: str | None) -> str:
    """Replace bearer tokens, syt_ and sk-or- values, and secret assignments."""
    if not text:
        return ""
    cleaned = _BEARER.sub("Bearer [redacted]", text)
    cleaned = _SECRET_VALUE.sub("[redacted]", cleaned)
    cleaned = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[redacted]", cleaned)
    return cleaned


def terminal_line(text: str) -> str:
    """Print one redacted line. The stored text and the printed text match."""
    cleaned = redact(text)
    print(cleaned)
    return cleaned


def bound_stream(text: str | None) -> tuple[str, bool]:
    cleaned = redact(text)
    encoded = cleaned.encode("utf-8")
    if len(encoded) <= TAIL_LIMIT:
        return cleaned, False
    cut = encoded[:TAIL_LIMIT]
    while cut and (cut[-1] & 0xC0) == 0x80:
        cut = cut[:-1]
    return cut.decode("utf-8"), True


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enabled() -> bool:
    return os.environ.get("AMCTL_OPLOG") != "off"


def pid_alive(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


async def start_run(
    session: AsyncSession,
    *,
    action: str,
    target: str | None,
    actor: str,
    writer_pid: int | None = None,
) -> OperationalRun:
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action}")
    if not actor:
        raise ValueError("actor is required")
    row = OperationalRun(
        run_id=str(uuid.uuid4()),
        action=action,
        target=target,
        actor=actor,
        writer_pid=os.getpid() if writer_pid is None else writer_pid,
        outcome=None,
        started_at=_utcnow(),
        ended_at=None,
    )
    session.add(row)
    await session.commit()
    return row


async def write_stage(
    session: AsyncSession,
    run_id: str,
    stage: str,
    phase: str,
    severity: str,
    body: str,
    *,
    cause: str | None = None,
    exit_status: int | None = None,
    stdout: str = "",
    stderr: str = "",
    instance_present: bool | None = None,
    observed_at: datetime | None = None,
) -> OperationalStage:
    if phase not in {"start", "finish"}:
        raise ValueError(f"unknown phase {phase}")
    if severity not in {"INFO", "WARN", "ERROR"}:
        raise ValueError(f"unknown severity {severity}")
    stdout_tail, stdout_cut = bound_stream(stdout)
    stderr_tail, stderr_cut = bound_stream(stderr)
    cleaned_cause = redact(cause) if cause else None
    if phase == "finish" and severity == "ERROR" and not (cleaned_cause and cleaned_cause.strip()):
        cleaned_cause = "no result"
    if phase == "finish" and severity != "ERROR":
        cleaned_cause = None if not cleaned_cause else cleaned_cause
        if severity == "INFO":
            cleaned_cause = None
    row = OperationalStage(
        run_id=run_id,
        stage=stage,
        phase=phase,
        severity=severity,
        body=redact(body) or f"{stage} {phase}.",
        observed_at=observed_at or _utcnow(),
        exit_status=exit_status,
        stdout_tail=stdout_tail or None,
        stderr_tail=stderr_tail or None,
        truncated=stdout_cut or stderr_cut,
        cause=cleaned_cause,
        instance_present=instance_present,
    )
    run = await session.get(OperationalRun, run_id)
    session.add(row)
    await session.flush()
    if run is not None:
        export.write_stage(row, run)
    await session.commit()
    return row


async def finish_run(
    session: AsyncSession,
    run_id: str,
    outcome: str,
    *,
    instance_present: bool | None = None,
) -> OperationalRun | None:
    if outcome not in {"succeeded", "failed", "interrupted"}:
        raise ValueError(f"unknown outcome {outcome}")
    run = await session.get(OperationalRun, run_id)
    if run is None:
        return None
    when = _utcnow()
    run.outcome = outcome
    run.ended_at = when
    await session.flush()
    export.write_terminal(run, when, instance_present)
    await session.commit()
    return run


async def interrupt_orphans(session: AsyncSession) -> int:
    """Mark an open run interrupted when its writer process is gone."""
    result = await session.execute(select(OperationalRun).where(OperationalRun.outcome.is_(None)))
    count = 0
    for run in result.scalars().all():
        if pid_alive(run.writer_pid):
            continue
        open_stage = await session.execute(
            select(OperationalStage)
            .where(OperationalStage.run_id == run.run_id)
            .order_by(OperationalStage.id.desc())
        )
        latest = open_stage.scalars().first()
        stage_name = latest.stage if latest is not None and latest.phase == "start" else "interrupted"
        await write_stage(
            session,
            run.run_id,
            stage_name,
            "finish",
            "ERROR",
            "The stage did not finish.",
            cause="The writer process is not alive.",
        )
        await finish_run(session, run.run_id, "interrupted")
        count += 1
    return count


async def purge_expired(session: AsyncSession, *, now: datetime | None = None, days: int = RETENTION_DAYS) -> int:
    """Delete run rows older than `days` from ended_at and stage rows older than observed_at."""
    moment = now or _utcnow()
    cutoff = moment - timedelta(days=days)
    old_runs = await session.execute(
        select(OperationalRun.run_id).where(
            OperationalRun.ended_at.is_not(None),
            OperationalRun.ended_at < cutoff,
        )
    )
    run_ids = list(old_runs.scalars().all())
    old_stages = await session.execute(
        select(OperationalStage.id).where(OperationalStage.observed_at < cutoff)
    )
    stage_ids = list(old_stages.scalars().all())
    if stage_ids:
        await session.execute(delete(OperationalStage).where(OperationalStage.id.in_(stage_ids)))
    if run_ids:
        await session.execute(delete(OperationalStage).where(OperationalStage.run_id.in_(run_ids)))
        await session.execute(delete(OperationalRun).where(OperationalRun.run_id.in_(run_ids)))
    await session.commit()
    _drop_lines(cutoff, set(run_ids))
    return len(run_ids) + len(stage_ids)


def _drop_lines(cutoff: datetime, deleted_run_ids: set[str]) -> None:
    path = export.log_path()
    if not path.is_file():
        return
    kept: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            import json

            payload = json.loads(raw)
            record = payload["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
            when = datetime.fromtimestamp(int(record["timeUnixNano"]) / 1_000_000_000, tz=timezone.utc)
            attributes = {
                item["key"]: next(iter(item["value"].values()))
                for item in record.get("attributes", [])
            }
            run_id = attributes.get("run.id")
        except (KeyError, ValueError, IndexError):
            kept.append(raw)
            continue
        if run_id in deleted_run_ids or when < cutoff:
            continue
        kept.append(raw)
    text = ("\n".join(kept) + "\n") if kept else ""
    path.write_text(text, encoding="utf-8")


def start_run_sync(*, action: str, target: str | None, actor: str, writer_pid: int | None = None) -> str | None:
    if not _enabled():
        return None
    from amctl.db import async_session

    async def _open():
        async with async_session() as session:
            row = await start_run(
                session,
                action=action,
                target=target,
                actor=actor,
                writer_pid=writer_pid,
            )
            return row.run_id

    return asyncio.run(_open())


def stage_sync(
    *,
    run_id: str | None,
    stage: str,
    phase: str,
    severity: str = "INFO",
    body: str = "",
    cause: str | None = None,
    exit_status: int | None = None,
    stdout: str = "",
    stderr: str = "",
    instance_present: bool | None = None,
) -> None:
    if not _enabled() or not run_id or run_id == "oplog-off":
        return
    from amctl.db import async_session

    async def _write():
        async with async_session() as session:
            await write_stage(
                session,
                run_id,
                stage,
                phase,
                severity,
                body,
                cause=cause,
                exit_status=exit_status,
                stdout=stdout,
                stderr=stderr,
                instance_present=instance_present,
            )

    asyncio.run(_write())


def finish_sync(
    *,
    run_id: str | None,
    outcome: str,
    instance_present: bool | None = None,
) -> None:
    if not _enabled() or not run_id or run_id == "oplog-off":
        return
    from amctl.db import async_session

    async def _finish():
        async with async_session() as session:
            await finish_run(session, run_id, outcome, instance_present=instance_present)

    asyncio.run(_finish())
