"""Fleet deployment & release management service (Phase 6).

Absorbs:
- sync-fleet.sh (release bundle creation, checksum verification, artifact installation)
- update-fleet.sh v2.2 (Docker image version management + fleet deploy status)
- deploy-supervisord-fleet.sh (supervisord wrapper & process management)
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
import shutil
import tarfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.models.deploy import Deployment, Release
from amctl.schemas.deploy import (
    AgentDeployStatusItem,
    DeployResultResponse,
    FleetDeployStatusResponse,
    ReleaseResponse,
    VersionUpdateResponse,
)
from amctl.services.agent_zero import check_mcp_health
from amctl.services.docker import _run, get_container_status, get_process_info, supervisor_action
from amctl.services.health_engine import run_agent_health_checks
from amctl.services.reconciler import TRACKED_ARTIFACTS, _file_sha256_prefix, check_agent_drift

logger = logging.getLogger(__name__)

RELEASES_DIR = Path("/opt/agent-zero/releases")
INSTANCE_BASE = Path("/opt/agent-zero")


def _full_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


async def create_or_register_release(
    session: AsyncSession,
    version: str,
    bundle_path: str | None = None,
    operator: str = "cli:release",
) -> ReleaseResponse:
    """Build an immutable release bundle tarball from current golden templates (or register
    an existing bundle tarball), compute SHA-256 checksums for the bundle and each artifact,
    and register it in the `releases` table.
    """
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)

    existing_res = await session.execute(select(Release).where(Release.version == version))
    existing = existing_res.scalar_one_or_none()

    if bundle_path and Path(bundle_path).is_file():
        tar_path = Path(bundle_path)
        artifact_hashes: dict[str, str] = {}
        with tarfile.open(tar_path, "r:gz") as tf:
            for member in tf.getmembers():
                if member.isfile() and member.name not in ("MANIFEST.json", "SHA256SUMS"):
                    fobj = tf.extractfile(member)
                    if fobj:
                        data = fobj.read()
                        artifact_hashes[Path(member.name).name] = hashlib.sha256(data).hexdigest()[:12]
    else:
        import gzip
        import io

        tar_path = RELEASES_DIR / f"am-release-{version}.tar.gz"
        artifact_hashes = {}
        sha_lines: list[str] = []
        payload_items: list[tuple[str, bytes, int]] = []

        for label, (tpl_path, _) in sorted(TRACKED_ARTIFACTS.items()):
            if not tpl_path.is_file():
                raise ValueError(f"Golden template artifact missing: {tpl_path}")
            raw = tpl_path.read_bytes()
            full_h = hashlib.sha256(raw).hexdigest()
            artifact_hashes[label] = full_h[:12]
            sha_lines.append(f"{full_h}  {label}")
            payload_items.append((label, raw, 0o755))

        manifest_bytes = (
            json.dumps(
                {"version": version, "artifact_hashes": dict(sorted(artifact_hashes.items()))},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode()
        sha_bytes = ("\n".join(sha_lines) + "\n").encode()
        payload_items.append(("MANIFEST.json", manifest_bytes, 0o644))
        payload_items.append(("SHA256SUMS", sha_bytes, 0o644))

        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
            for name, data, mode in sorted(payload_items, key=lambda x: x[0]):
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                info.mtime = 0
                info.mode = mode
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                tf.addfile(info, io.BytesIO(data))

        with tar_path.open("wb") as raw_f:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_f, mtime=0) as gz_f:
                gz_f.write(tar_buf.getvalue())

    bundle_sha256 = _full_sha256(tar_path)

    if existing:
        existing.bundle_path = str(tar_path)
        existing.checksum_sha256 = bundle_sha256
        existing.artifact_hashes = artifact_hashes
        rel = existing
    else:
        rel = Release(
            version=version,
            bundle_path=str(tar_path),
            checksum_sha256=bundle_sha256,
            artifact_hashes=artifact_hashes,
        )
        session.add(rel)

    session.add(
        AuditLog(
            agent_id=None,
            action="release_register",
            detail={
                "version": version,
                "bundle_path": str(tar_path),
                "checksum_sha256": bundle_sha256[:16],
                "artifact_hashes": artifact_hashes,
            },
            operator=operator,
        )
    )
    await session.commit()
    await session.refresh(rel)
    return ReleaseResponse.model_validate(rel)


async def deploy_release_to_agent(
    session: AsyncSession,
    agent: Agent,
    version: str,
    operator: str = "cli:deploy",
) -> DeployResultResponse:
    """Deploy a registered release bundle to a single agent:
    1. Verify release bundle SHA-256 and artifact hashes
    2. Record pre-deploy instance-local state (Matrix token fp, room_contexts.json, .a0-api-key fp)
    3. Stop bot -> install artifacts atomically -> derive canonical .a0-api-key -> start bot
    4. Verify instance-local state preserved, run health checks & drift check, update agent.release_version
    """
    rel_res = await session.execute(select(Release).where(Release.version == version))
    rel = rel_res.scalar_one_or_none()
    if not rel:
        raise ValueError(f"Release '{version}' not found in registry")

    bundle_file = Path(rel.bundle_path) if rel.bundle_path else None
    if not bundle_file or not bundle_file.is_file():
        raise ValueError(f"Release bundle file missing: {rel.bundle_path}")

    actual_bundle_sha = _full_sha256(bundle_file)
    if actual_bundle_sha != rel.checksum_sha256:
        raise ValueError(f"Release bundle checksum mismatch for {version}")

    instance_dir = INSTANCE_BASE / agent.name
    bot_dir = instance_dir / "usr" / "workdir" / "matrix-bot"

    # Capture instance-local state fingerprints before deploy (Gate 5)
    pre_bot_env = bot_dir / ".env"
    pre_ctx_file = bot_dir / "room_contexts.json"
    pre_matrix_tok_fp = _file_sha256_prefix(pre_bot_env)
    pre_ctx_hash = _file_sha256_prefix(pre_ctx_file)
    _, pre_sync = await _run([
        "docker", "exec", agent.name,
        "bash", "-c",
        "TOK=$(grep '^MATRIX_ACCESS_TOKEN=' /a0/usr/workdir/matrix-bot/.env | cut -d= -f2); "
        f"curl -s -H \"Authorization: Bearer $TOK\" http://172.23.89.{agent.instance_num}:8008/_matrix/client/v3/sync?timeout=0 "
        "| python3 -c 'import sys,json; print(json.load(sys.stdin).get(\"next_batch\",\"\"))' 2>/dev/null || true",
    ])

    dep = Deployment(
        agent_id=agent.id,
        release_id=rel.id,
        status="deploying",
        detail={"version": version, "operator": operator},
    )
    session.add(dep)
    await session.commit()
    await session.refresh(dep)

    extract_dir = RELEASES_DIR / f".extract-{agent.name}-{version}"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(bundle_file, "r:gz") as tf:
            tf.extractall(extract_dir)

        # Verify extracted artifact hashes against release manifest
        for label, exp_prefix in rel.artifact_hashes.items():
            ext_file = extract_dir / label
            act_prefix = _file_sha256_prefix(ext_file)
            if act_prefix != exp_prefix:
                raise ValueError(f"Artifact hash mismatch in bundle for {label}: {act_prefix} != {exp_prefix}")

        # Stop bot before replacing binary
        await supervisor_action(agent.name, "stop", "run_bot")

        # Install each artifact atomically (never touching .env or room_contexts.json)
        installed = []
        for label, (_, rel_dst) in TRACKED_ARTIFACTS.items():
            src_file = extract_dir / label
            if not src_file.is_file():
                continue
            dst_file = instance_dir / rel_dst
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_dst = dst_file.with_suffix(dst_file.suffix + ".deploy.tmp")
            shutil.copy2(src_file, tmp_dst)
            tmp_dst.chmod(0o755)
            tmp_dst.replace(dst_file)
            installed.append(label)

        # Ensure canonical secret file is freshly derived
        await _run([
            "docker", "exec", agent.name,
            "/a0/usr/workdir/derive-a0-token.sh",
            "--output", "/a0/usr/workdir/matrix-bot/.a0-api-key",
        ], timeout=25.0)

        # Start bot and wait for process to come up
        await supervisor_action(agent.name, "start", "run_bot")
        for _ in range(10):
            await asyncio.sleep(1)
            pinfo = await get_process_info(agent.name)
            if pinfo and pinfo.bot_count == 1:
                break

    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)

    # Verify instance-local state preserved (Gate 5)
    post_matrix_tok_fp = _file_sha256_prefix(pre_bot_env)
    post_ctx_hash = _file_sha256_prefix(pre_ctx_file)
    preserved_state = {
        "bot_env_preserved": pre_matrix_tok_fp == post_matrix_tok_fp,
        "room_contexts_preserved": pre_ctx_hash == post_ctx_hash,
        "pre_sync_batch": pre_sync.strip(),
    }

    # Run health checks and drift check
    health_results = await run_agent_health_checks(
        session, agent, include_federation=False, operator=operator
    )
    health_passed = all(v["status"] == "pass" for v in health_results.values())
    drift_report = await check_agent_drift(session, agent)

    overall_ok = (
        health_passed
        and drift_report.clean
        and preserved_state["bot_env_preserved"]
        and preserved_state["room_contexts_preserved"]
    )

    dep.status = "success" if overall_ok else "failed"
    dep.deployed_at = datetime.now(timezone.utc)
    dep.detail = {
        "version": version,
        "installed_artifacts": installed,
        "preserved_state": preserved_state,
        "health_passed": health_passed,
        "drift_clean": drift_report.clean,
    }

    if overall_ok:
        agent.release_version = version

    session.add(
        AuditLog(
            agent_id=agent.id,
            action="deploy_release",
            detail={
                "deployment_id": dep.id,
                "version": version,
                "status": dep.status,
                "preserved_state": preserved_state,
            },
            operator=operator,
        )
    )
    await session.commit()
    await session.refresh(dep)

    return DeployResultResponse(
        deployment_id=dep.id,
        agent_id=agent.id,
        agent_name=agent.name,
        release_version=version,
        status=dep.status,
        preserved_state=preserved_state,
        health_passed=health_passed,
        drift_clean=drift_report.clean,
        detail=dep.detail,
        deployed_at=dep.deployed_at,
    )


async def _get_running_a0_version(agent_name: str) -> str:
    """Query Agent Zero's /api/health endpoint inside the container or inspect image tag."""
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c",
        "curl -s --max-time 3 http://127.0.0.1:80/api/health 2>/dev/null "
        "| python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('gitinfo',{}).get('short_tag',''))\" 2>/dev/null || true",
    ])
    if rc == 0 and out.strip():
        return out.strip()
    rc2, img_out = await _run([
        "docker", "inspect", "--format", "{{.Config.Image}}", agent_name,
    ])
    if rc2 == 0 and ":" in img_out:
        return img_out.split(":", 1)[1].strip()
    return "unknown"


def _get_compose_a0_version(agent_name: str) -> str:
    compose_path = INSTANCE_BASE / agent_name / "docker-compose.yml"
    if not compose_path.is_file():
        return "unknown"
    for line in compose_path.read_text().splitlines():
        m = re.search(r"image:\s*agent0ai/agent-zero:(\S+)", line)
        if m:
            return m.group(1).strip()
    return "unknown"


def _get_compose_service_name(compose_path: Path) -> str:
    lines = compose_path.read_text().splitlines()
    in_services = False
    for line in lines:
        if line.startswith("services:"):
            in_services = True
            continue
        if in_services and re.match(r"^  [a-zA-Z0-9_-]+:", line):
            return line.strip().rstrip(":")
    return "agent-zero"


async def update_agent_image_version(
    session: AsyncSession,
    agent: Agent,
    image_version: str,
    skip_restart: bool = False,
    force: bool = False,
    operator: str = "cli:deploy_version",
) -> VersionUpdateResponse:
    """Update Agent Zero Docker image version in docker-compose.yml and optionally
    recreate the container (absorbs update-fleet.sh v2.2).
    """
    compose_path = INSTANCE_BASE / agent.name / "docker-compose.yml"
    if not compose_path.is_file():
        raise ValueError(f"Missing {compose_path}")

    prev_ver = await _get_running_a0_version(agent.name)
    compose_ver = _get_compose_a0_version(agent.name)

    if prev_ver == image_version and compose_ver == image_version and not force and not skip_restart:
        return VersionUpdateResponse(
            agent_name=agent.name,
            previous_version=prev_ver,
            target_version=image_version,
            compose_updated=False,
            container_recreated=False,
            health_passed=True,
            status="already_current",
            detail={"message": f"{agent.name} is already at {image_version}"},
        )

    # Backup compose file and update tag
    shutil.copy2(compose_path, compose_path.with_suffix(".yml.bak"))
    content = compose_path.read_text()
    new_content = re.sub(
        r"(image:\s*agent0ai/agent-zero:)\S+",
        rf"\g<1>{image_version}",
        content,
    )
    compose_path.write_text(new_content)
    compose_updated = True
    container_recreated = False

    if not skip_restart:
        svc_name = _get_compose_service_name(compose_path)
        rc, out = await _run([
            "bash", "-c",
            f"cd /opt/agent-zero/{agent.name} && set -a && [ -f .env ] && source .env && set +a && "
            f"docker compose up -d --no-deps --force-recreate {svc_name}",
        ], timeout=120.0)
        container_recreated = rc == 0
        # Wait for container services & Agent Zero UI to stabilize
        for _ in range(25):
            await asyncio.sleep(2)
            pinfo = await get_process_info(agent.name)
            cur_v = await _get_running_a0_version(agent.name)
            if pinfo and pinfo.bot_count == 1 and cur_v == image_version:
                break

    health_results = await run_agent_health_checks(
        session, agent, include_federation=False, operator=operator
    )
    health_passed = all(v["status"] == "pass" for v in health_results.values())

    session.add(
        AuditLog(
            agent_id=agent.id,
            action="deploy_image_version",
            detail={
                "previous_version": prev_ver,
                "target_version": image_version,
                "skip_restart": skip_restart,
                "container_recreated": container_recreated,
                "health_passed": health_passed,
            },
            operator=operator,
        )
    )
    await session.commit()

    return VersionUpdateResponse(
        agent_name=agent.name,
        previous_version=prev_ver,
        target_version=image_version,
        compose_updated=compose_updated,
        container_recreated=container_recreated,
        health_passed=health_passed,
        status="success" if health_passed else "degraded",
    )


async def get_fleet_deploy_status(session: AsyncSession) -> FleetDeployStatusResponse:
    """Return fleet-wide deployment overview (absorbs update-fleet.sh --status)."""
    res = await session.execute(select(Agent).order_by(Agent.instance_num))
    agents = res.scalars().all()

    rel_res = await session.execute(select(Release).order_by(Release.created_at.desc()).limit(1))
    latest_rel = rel_res.scalar_one_or_none()

    dep_res = await session.execute(select(Deployment).order_by(Deployment.deployed_at.desc()))
    all_deps = dep_res.scalars().all()
    latest_dep_by_agent: dict[int, Deployment] = {}
    for d in all_deps:
        if d.agent_id not in latest_dep_by_agent:
            latest_dep_by_agent[d.agent_id] = d

    items: list[AgentDeployStatusItem] = []
    up_count = 0
    clean_count = 0

    for a in agents:
        containers, pinfo, run_ver, mcp_res, drift = await asyncio.gather(
            get_container_status(a.name),
            get_process_info(a.name),
            _get_running_a0_version(a.name),
            check_mcp_health(a.name),
            check_agent_drift(session, a),
        )
        comp_ver = _get_compose_a0_version(a.name)
        is_up = any(c.name == a.name and c.running for c in containers)
        if is_up:
            up_count += 1
        if drift.clean:
            clean_count += 1

        mcp_st, mcp_det = mcp_res
        mcp_label = f"r2:{mcp_det.get('version', '0.1.1')}" if mcp_st == "pass" else "down"
        last_dep = latest_dep_by_agent.get(a.id)

        items.append(
            AgentDeployStatusItem(
                agent_name=a.name,
                instance_num=a.instance_num,
                container_state="up" if is_up else "down",
                running_a0_version=run_ver,
                compose_a0_version=comp_ver,
                version_drift=(run_ver != comp_ver and comp_ver != "unknown"),
                release_version=a.release_version,
                bot_count=pinfo.bot_count if pinfo else 0,
                mcp_status=mcp_label,
                supervisord=pinfo.supervisord_running if pinfo else False,
                reconcile_clean=drift.clean,
                last_deployment_at=last_dep.deployed_at if last_dep else None,
                last_deployment_status=last_dep.status if last_dep else None,
            )
        )

    return FleetDeployStatusResponse(
        total_agents=len(items),
        up_agents=up_count,
        clean_agents=clean_count,
        latest_release=latest_rel.version if latest_rel else None,
        agents=items,
    )
