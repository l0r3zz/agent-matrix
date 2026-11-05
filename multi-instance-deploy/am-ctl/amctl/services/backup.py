"""Database & Infrastructure Backup and Restore Verification Service (Phase 5).

Protects:
1. open_brain database (pg_dump -Fc -Z 9)
2. fleet_ops database (pg_dump -Fc -Z 9)
3. PostgreSQL cluster globals (pg_dumpall --globals-only)
4. Critical infrastructure configs & TLS/signing keys (tar.gz, mode 0600)

Performs GFS retention pruning (30d daily, 12w weekly, 14d pre_deploy),
off-host rsync to tarnover (/home/l0r3zz/Dropbox/GEN-AI/AGENT-MATRIX/backups/),
and non-destructive scratch-DB restore verification inside open-brain-db.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os
from pathlib import Path
import shutil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.audit import AuditLog
from amctl.models.backup import BackupRun
from amctl.models.health import Alert
from amctl.schemas.backup import (
    BackupArtifactResponse,
    BackupSuiteRunResponse,
    BackupVerifyResponse,
)
from amctl.services.docker import _run

logger = logging.getLogger(__name__)

BACKUP_ROOT = Path("/opt/agent-zero/backups")
OFFSITE_HOST = "l0r3zz@172.23.0.103"
OFFSITE_PATH = "/home/l0r3zz/Dropbox/GEN-AI/AGENT-MATRIX/backups"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


async def _dump_database_custom(db_name: str, dest_path: Path) -> tuple[bool, str]:
    """Run pg_dump -Fc -Z 9 inside open-brain-db and write to dest_path on host."""
    container_tmp = f"/tmp/{db_name}.dump"
    rc, out = await _run([
        "docker", "exec", "open-brain-db",
        "pg_dump", "-U", "openbrain", "-Fc", "-Z", "9", "-f", container_tmp, db_name,
    ], timeout=120.0)
    if rc != 0:
        return False, out or f"pg_dump failed for {db_name}"

    rc2, out2 = await _run([
        "docker", "cp", f"open-brain-db:{container_tmp}", str(dest_path),
    ], timeout=60.0)
    await _run(["docker", "exec", "open-brain-db", "rm", "-f", container_tmp])
    if rc2 != 0 or not dest_path.is_file() or dest_path.stat().st_size == 0:
        return False, out2 or f"docker cp failed for {db_name}"

    dest_path.chmod(0o600)
    return True, "ok"


async def _dump_globals(dest_path: Path) -> tuple[bool, str]:
    """Run pg_dumpall --globals-only inside open-brain-db."""
    rc, out = await _run([
        "docker", "exec", "open-brain-db",
        "pg_dumpall", "-U", "openbrain", "--globals-only",
    ], timeout=30.0)
    if rc != 0 or not out:
        return False, out or "pg_dumpall --globals-only failed"

    dest_path.write_text(out + "\n")
    dest_path.chmod(0o600)
    return True, "ok"


async def _bundle_infra_configs(dest_path: Path) -> tuple[bool, str]:
    """Create a 0600 tarball of OpenBrain, am-ctl, and per-agent configs/TLS certs (excluding pgdata/node_modules/.venv)."""
    paths_to_include = [
        "open-brain/docker-compose.yml",
        "open-brain/.env",
        "open-brain/init-db",
        "open-brain/pg-conf",
        "multi-instance-deploy/am-ctl/pyproject.toml",
        "multi-instance-deploy/am-ctl/am-ctl.service",
    ]
    for i in range(1, 6):
        paths_to_include.extend([
            f"agent0-{i}/docker-compose.yml",
            f"agent0-{i}/.env",
            f"agent0-{i}/mhs/Caddyfile",
            f"agent0-{i}/mhs/server.crt",
            f"agent0-{i}/mhs/server.key",
            f"agent0-{i}/usr/settings.json",
            f"agent0-{i}/usr/workdir/matrix-bot/.env",
            f"agent0-{i}/usr/workdir/matrix-bot/room_contexts.json",
            f"agent0-{i}/usr/workdir/matrix-mcp-server/.env",
        ])

    existing = [p for p in paths_to_include if (Path("/opt/agent-zero") / p).exists()]
    cmd = ["tar", "-czf", str(dest_path), "-C", "/opt/agent-zero", *existing]
    rc, out = await _run(cmd, timeout=60.0)
    if rc != 0 or not dest_path.is_file() or dest_path.stat().st_size == 0:
        return False, out or "tar infra_configs failed"

    dest_path.chmod(0o600)
    return True, f"bundled {len(existing)} paths"


def prune_old_backups() -> list[str]:
    """Enforce GFS retention policy:
    - daily/: 30 days
    - weekly/: 12 weeks (84 days)
    - pre_deploy/: 14 days
    - manual/: 30 days
    Returns list of pruned directory paths.
    """
    now = datetime.now(timezone.utc)
    thresholds = {
        "daily": timedelta(days=30),
        "weekly": timedelta(days=84),
        "pre_deploy": timedelta(days=14),
        "manual": timedelta(days=30),
    }
    pruned: list[str] = []

    for tier, max_age in thresholds.items():
        tier_dir = BACKUP_ROOT / tier
        if not tier_dir.is_dir():
            continue
        cutoff_ts = (now - max_age).timestamp()
        for child in sorted(tier_dir.iterdir()):
            if not child.is_dir():
                continue
            # Check directory name YYYY-MM-DD* or mtime
            dir_mtime = child.stat().st_mtime
            try:
                date_part = child.name[:10]
                dt = datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                dir_ts = dt.timestamp()
            except ValueError:
                dir_ts = dir_mtime

            if dir_ts < cutoff_ts:
                shutil.rmtree(child, ignore_errors=True)
                pruned.append(str(child))

    return pruned


async def sync_to_offsite(local_dir: Path, tier: str) -> tuple[bool, str]:
    """Rsync the backup directory to tarnover's Dropbox backup folder."""
    remote_dir = f"{OFFSITE_PATH}/{tier}/{local_dir.name}"
    rc_mkdir, out_mkdir = await _run([
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
        OFFSITE_HOST, f"mkdir -p '{remote_dir}' && chmod 700 '{OFFSITE_PATH}'",
    ], timeout=15.0)
    if rc_mkdir != 0:
        return False, f"ssh mkdir failed: {out_mkdir}"

    rc, out = await _run([
        "rsync", "-az", "--delete",
        "-e", "ssh -o BatchMode=yes -o StrictHostKeyChecking=no",
        f"{local_dir}/",
        f"{OFFSITE_HOST}:{remote_dir}/",
    ], timeout=120.0)
    return rc == 0, out if rc != 0 else f"{OFFSITE_HOST}:{remote_dir}"


async def execute_backup_suite(
    session: AsyncSession,
    backup_type: str = "manual",
    operator: str = "cli:backup",
) -> BackupSuiteRunResponse:
    """Execute full backup suite (open_brain, fleet_ops, globals, infra_configs),
    write SHA256SUMS, sync off-site to tarnover, and prune expired backups.
    """
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    day_stamp = now.strftime("%Y-%m-%d")

    if backup_type == "daily_full":
        tier = "daily"
        run_dir = BACKUP_ROOT / tier / day_stamp
    elif backup_type == "pre_deploy":
        tier = "pre_deploy"
        run_dir = BACKUP_ROOT / tier / stamp
    else:
        tier = "manual"
        run_dir = BACKUP_ROOT / tier / stamp

    run_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(BACKUP_ROOT, 0o700)

    targets = [
        ("open_brain", run_dir / f"open_brain-{stamp}.dump"),
        ("fleet_ops", run_dir / f"fleet_ops-{stamp}.dump"),
        ("globals", run_dir / f"globals-{stamp}.sql"),
        ("infra_configs", run_dir / f"infra_configs-{stamp}.tar.gz"),
    ]

    records: list[BackupRun] = []
    sha_lines: list[str] = []

    for target_name, path in targets:
        if target_name in ("open_brain", "fleet_ops"):
            ok, msg = await _dump_database_custom(target_name, path)
        elif target_name == "globals":
            ok, msg = await _dump_globals(path)
        else:
            ok, msg = await _bundle_infra_configs(path)

        if ok and path.is_file():
            size = path.stat().st_size
            checksum = _sha256_file(path)
            sha_lines.append(f"{checksum}  {path.name}")
            status = "success"
        else:
            size = 0
            checksum = ""
            status = "failed"

        rec = BackupRun(
            backup_type=backup_type,
            target=target_name,
            file_path=str(path),
            size_bytes=size,
            checksum_sha256=checksum,
            offsite_synced=False,
            status=status,
            detail={"message": msg},
            created_at=now,
        )
        session.add(rec)
        records.append(rec)

    # Write SHA256SUMS manifest
    if sha_lines:
        sha_file = run_dir / "SHA256SUMS"
        sha_file.write_text("\n".join(sha_lines) + "\n")
        sha_file.chmod(0o600)

    # Sunday weekly snapshot copy for GFS rotation
    if backup_type == "daily_full" and now.weekday() == 6:
        weekly_dir = BACKUP_ROOT / "weekly" / day_stamp
        if weekly_dir.exists():
            shutil.rmtree(weekly_dir)
        shutil.copytree(run_dir, weekly_dir)

    # Sync to off-host tarnover
    offsite_ok, offsite_info = await sync_to_offsite(run_dir, tier)
    for rec in records:
        if rec.status == "success":
            rec.offsite_synced = offsite_ok
            rec.detail = {**(rec.detail or {}), "offsite": offsite_info}

    pruned_dirs = prune_old_backups()

    session.add(
        AuditLog(
            agent_id=None,
            action=f"backup_run:{backup_type}",
            detail={
                "backup_dir": str(run_dir),
                "offsite_synced": offsite_ok,
                "offsite_target": offsite_info,
                "pruned_dirs": pruned_dirs,
                "targets": {r.target: r.status for r in records},
            },
            operator=operator,
        )
    )

    await session.commit()
    for r in records:
        await session.refresh(r)

    # Resolve any open backup_freshness alert if all 4 succeeded
    if all(r.status == "success" for r in records):
        await _resolve_backup_alerts(session)

    return BackupSuiteRunResponse(
        backup_type=backup_type,
        backup_dir=str(run_dir),
        offsite_target=f"{OFFSITE_HOST}:{OFFSITE_PATH}/{tier}/{run_dir.name}",
        offsite_synced=offsite_ok,
        pruned_dirs=pruned_dirs,
        artifacts=[BackupArtifactResponse.model_validate(r) for r in records],
        completed_at=datetime.now(timezone.utc),
    )


async def verify_latest_backups(
    session: AsyncSession,
    backup_id: int | None = None,
    operator: str = "cli:backup_verify",
) -> BackupVerifyResponse:
    """Non-destructively verify the latest open_brain and fleet_ops dumps by restoring
    each into an ephemeral scratch database inside open-brain-db, comparing row counts
    and pgvector index presence against the live databases, then dropping the scratch DBs.
    """
    if backup_id is not None:
        target_res = await session.execute(select(BackupRun).where(BackupRun.id == backup_id))
        target_rec = target_res.scalar_one_or_none()
        if target_rec and target_rec.target == "open_brain":
            ob_rec = target_rec
        else:
            ob_rec = None
    else:
        ob_rec = None

    if ob_rec is None:
        ob_res = await session.execute(
            select(BackupRun)
            .where(BackupRun.target == "open_brain", BackupRun.status.in_(["success", "verified"]))
            .order_by(BackupRun.created_at.desc())
            .limit(1)
        )
        ob_rec = ob_res.scalar_one_or_none()

    fo_res = await session.execute(
        select(BackupRun)
        .where(BackupRun.target == "fleet_ops", BackupRun.status.in_(["success", "verified"]))
        .order_by(BackupRun.created_at.desc())
        .limit(1)
    )
    fo_rec = fo_res.scalar_one_or_none()

    if not ob_rec or not fo_rec:
        raise ValueError("Missing open_brain or fleet_ops backup records to verify")

    ob_path = Path(ob_rec.file_path)
    fo_path = Path(fo_rec.file_path)
    if not ob_path.is_file() or not fo_path.is_file():
        raise ValueError("Backup dump files not found on disk")

    # Verify SHA-256 checksums before restoring
    if _sha256_file(ob_path) != ob_rec.checksum_sha256:
        raise ValueError(f"SHA-256 mismatch on {ob_path}")
    if _sha256_file(fo_path) != fo_rec.checksum_sha256:
        raise ValueError(f"SHA-256 mismatch on {fo_path}")

    scratch_ob = "verify_open_brain_tmp"
    scratch_fo = "verify_fleet_ops_tmp"

    try:
        # Copy dumps into container /tmp
        await _run(["docker", "cp", str(ob_path), "open-brain-db:/tmp/verify_ob.dump"])
        await _run(["docker", "cp", str(fo_path), "open-brain-db:/tmp/verify_fo.dump"])

        # Create clean scratch DBs
        for sdb in (scratch_ob, scratch_fo):
            await _run([
                "docker", "exec", "open-brain-db",
                "psql", "-U", "openbrain", "-d", "postgres",
                "-c", f"DROP DATABASE IF EXISTS {sdb};",
            ])
            await _run([
                "docker", "exec", "open-brain-db",
                "psql", "-U", "openbrain", "-d", "postgres",
                "-c", f"CREATE DATABASE {sdb};",
            ])

        # Restore into scratch DBs
        rc_ob, out_ob = await _run([
            "docker", "exec", "open-brain-db",
            "pg_restore", "-U", "openbrain", "--no-owner", "--no-privileges",
            "-d", scratch_ob, "/tmp/verify_ob.dump",
        ], timeout=120.0)
        rc_fo, out_fo = await _run([
            "docker", "exec", "open-brain-db",
            "pg_restore", "-U", "openbrain", "--no-owner", "--no-privileges",
            "-d", scratch_fo, "/tmp/verify_fo.dump",
        ], timeout=120.0)

        # Compare open_brain thoughts count + pgvector index
        _, live_ob_cnt = await _run([
            "docker", "exec", "open-brain-db",
            "psql", "-U", "openbrain", "-d", "open_brain", "-t", "-A",
            "-c", "SELECT count(*) FROM thoughts;",
        ])
        _, rest_ob_cnt = await _run([
            "docker", "exec", "open-brain-db",
            "psql", "-U", "openbrain", "-d", scratch_ob, "-t", "-A",
            "-c", "SELECT count(*) FROM thoughts;",
        ])
        _, vec_idx_cnt = await _run([
            "docker", "exec", "open-brain-db",
            "psql", "-U", "openbrain", "-d", scratch_ob, "-t", "-A",
            "-c", "SELECT count(*) FROM pg_indexes WHERE tablename = 'thoughts' AND indexdef ILIKE '%hnsw%';",
        ])

        # Compare fleet_ops agents count
        _, live_fo_cnt = await _run([
            "docker", "exec", "open-brain-db",
            "psql", "-U", "openbrain", "-d", "fleet_ops", "-t", "-A",
            "-c", "SELECT count(*) FROM agents;",
        ])
        _, rest_fo_cnt = await _run([
            "docker", "exec", "open-brain-db",
            "psql", "-U", "openbrain", "-d", scratch_fo, "-t", "-A",
            "-c", "SELECT count(*) FROM agents;",
        ])

        live_thoughts = int(live_ob_cnt.strip()) if live_ob_cnt.strip().isdigit() else -1
        rest_thoughts = int(rest_ob_cnt.strip()) if rest_ob_cnt.strip().isdigit() else -2
        live_agents = int(live_fo_cnt.strip()) if live_fo_cnt.strip().isdigit() else -1
        rest_agents = int(rest_fo_cnt.strip()) if rest_fo_cnt.strip().isdigit() else -2
        pgvec_ok = vec_idx_cnt.strip().isdigit() and int(vec_idx_cnt.strip()) >= 1

        verified = (
            rc_ob == 0
            and rc_fo == 0
            and live_thoughts >= 0
            and live_thoughts == rest_thoughts
            and live_agents > 0
            and live_agents == rest_agents
            and pgvec_ok
        )
    finally:
        # Always drop scratch DBs and temporary container files
        for sdb in (scratch_ob, scratch_fo):
            await _run([
                "docker", "exec", "open-brain-db",
                "psql", "-U", "openbrain", "-d", "postgres",
                "-c", f"DROP DATABASE IF EXISTS {sdb};",
            ])
        await _run(["docker", "exec", "open-brain-db", "rm", "-f", "/tmp/verify_ob.dump", "/tmp/verify_fo.dump"])

    # Confirm scratch DBs are gone
    _, rem_cnt = await _run([
        "docker", "exec", "open-brain-db",
        "psql", "-U", "openbrain", "-d", "postgres", "-t", "-A",
        "-c", f"SELECT count(*) FROM pg_database WHERE datname IN ('{scratch_ob}', '{scratch_fo}');",
    ])
    scratch_cleaned = rem_cnt.strip() == "0"

    now = datetime.now(timezone.utc)
    if verified:
        ob_rec.status = "verified"
        fo_rec.status = "verified"
        ob_rec.detail = {**(ob_rec.detail or {}), "verified_at": now.isoformat(), "thoughts_count": rest_thoughts}
        fo_rec.detail = {**(fo_rec.detail or {}), "verified_at": now.isoformat(), "agents_count": rest_agents}

    session.add(
        AuditLog(
            agent_id=None,
            action="backup_verify",
            detail={
                "verified": verified,
                "open_brain_dump_id": ob_rec.id,
                "fleet_ops_dump_id": fo_rec.id,
                "thoughts_count": rest_thoughts,
                "agents_count": rest_agents,
                "pgvector_index_present": pgvec_ok,
                "scratch_db_cleaned": scratch_cleaned,
            },
            operator=operator,
        )
    )
    await session.commit()

    return BackupVerifyResponse(
        verified=verified,
        open_brain_dump_id=ob_rec.id,
        fleet_ops_dump_id=fo_rec.id,
        open_brain_live_thoughts=live_thoughts,
        open_brain_restored_thoughts=rest_thoughts,
        fleet_ops_live_agents=live_agents,
        fleet_ops_restored_agents=rest_agents,
        pgvector_index_present=pgvec_ok,
        scratch_db_cleaned=scratch_cleaned,
        detail={"open_brain_file": ob_rec.file_path, "fleet_ops_file": fo_rec.file_path},
        verified_at=now,
    )


async def check_backup_freshness(session: AsyncSession) -> tuple[str, dict]:
    """Check if both open_brain and fleet_ops have a valid backup within the last 26 hours.
    Opens a platform alert on agent_id=1 (fleet control plane anchor) if stale (>26h) or failed.
    """
    now = datetime.now(timezone.utc)
    status = "pass"
    details: dict = {}

    for target in ("open_brain", "fleet_ops"):
        res = await session.execute(
            select(BackupRun)
            .where(BackupRun.target == target)
            .order_by(BackupRun.created_at.desc())
            .limit(1)
        )
        latest = res.scalar_one_or_none()
        if latest is None:
            status = "fail"
            details[target] = {"error": "no_backup_found"}
            continue

        created_dt = latest.created_at
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        age_hours = (now - created_dt).total_seconds() / 3600.0
        details[target] = {
            "id": latest.id,
            "status": latest.status,
            "age_hours": round(age_hours, 2),
            "offsite_synced": latest.offsite_synced,
        }
        if latest.status == "failed" or age_hours > 48.0:
            status = "fail"
        elif age_hours > 26.0 and status != "fail":
            status = "warn"

    if status in ("warn", "fail"):
        existing_res = await session.execute(
            select(Alert).where(
                Alert.check_type == "backup_freshness",
                Alert.status.in_(["open", "acked"]),
            )
        )
        existing = existing_res.scalar_one_or_none()
        msg = f"Database backup freshness {status.upper()}: open_brain/fleet_ops backup is stale or failed"
        if existing:
            existing.message = msg
            existing.detail = details
        else:
            session.add(
                Alert(
                    agent_id=1,
                    check_type="backup_freshness",
                    classification="TERMINAL_CONFIG" if status == "fail" else "RESTARTABLE",
                    status="open",
                    message=msg,
                    detail=details,
                )
            )
        await session.commit()
    else:
        await _resolve_backup_alerts(session)

    return status, details


async def _resolve_backup_alerts(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    res = await session.execute(
        select(Alert).where(
            Alert.check_type == "backup_freshness",
            Alert.status.in_(["open", "acked"]),
        )
    )
    changed = False
    for al in res.scalars().all():
        al.status = "resolved"
        al.resolved_at = now
        changed = True
    if changed:
        await session.commit()
