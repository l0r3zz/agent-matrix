"""Docker client for agent container inspection and process control.

Uses docker CLI via subprocess since the server runs on the Docker host (g2s).
This avoids pulling in the full Docker SDK as a dependency.
"""

import asyncio
import json
import logging

from amctl.schemas.agent import ContainerStatus, ProcessInfo

logger = logging.getLogger(__name__)


async def _run(cmd: list[str], timeout: float = 15.0) -> tuple[int, str]:
    """Run a command and return (exit_code, stdout)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 1, ""
    return proc.returncode or 0, stdout.decode().strip()


async def get_container_status(agent_name: str) -> list[ContainerStatus]:
    """Get running status of all containers for an agent instance."""
    container_names = [
        agent_name,
        f"{agent_name}-continuwuity",
        f"{agent_name}-mhs",
    ]
    results = []
    for cname in container_names:
        rc, out = await _run([
            "docker", "inspect", "--format",
            '{"running": {{.State.Running}}, "status": "{{.State.Status}}", "started": "{{.State.StartedAt}}"}',
            cname,
        ])
        if rc == 0:
            try:
                data = json.loads(out)
                results.append(ContainerStatus(
                    name=cname,
                    running=data["running"],
                    uptime=data.get("status", "unknown"),
                ))
            except (json.JSONDecodeError, KeyError):
                results.append(ContainerStatus(name=cname, running=False))
        else:
            results.append(ContainerStatus(name=cname, running=False))
    return results


async def get_process_info(agent_name: str) -> ProcessInfo | None:
    """Get process info from inside an agent container."""
    rc, out = await _run(["docker", "ps", "--format", "{{.Names}}", "--filter", f"name=^{agent_name}$"])
    if rc != 0 or agent_name not in out:
        return None

    # Bot process count (useexact binary name or bracketed regex so bash -c doesn't match itself)
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c", "pgrep -fc '[m]atrix-bot-rust' 2>/dev/null || true",
    ])
    bot_count = int(out) if out.isdigit() else 0

    # MCP server
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c", "pgrep -fc '[m]atrix-mcp-server-r2|[n]ode.*http-server' 2>/dev/null || true",
    ])
    mcp_running = out.isdigit() and int(out) > 0

    # Watchdog (either standalone watchdog or supervisord managing services)
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c", "pgrep -fc '[w]atchdog' 2>/dev/null || true",
    ])
    watchdog_running = out.isdigit() and int(out) > 0

    # Supervisord (PID 1 check)
    rc, out = await _run([
        "docker", "exec", agent_name,
        "bash", "-c", "cat /proc/1/cmdline 2>/dev/null | tr '\\0' ' '",
    ])
    supervisord_running = "supervisord" in out if rc == 0 else False

    return ProcessInfo(
        bot_count=bot_count,
        bot_runtime="rust" if bot_count > 0 else None,
        mcp_running=mcp_running,
        watchdog_running=watchdog_running or supervisord_running,
        supervisord_running=supervisord_running,
    )


async def supervisor_action(agent_name: str, action: str, program: str) -> tuple[bool, str]:
    """Run supervisorctl <action> <program> inside an agent container."""
    rc, out = await _run([
        "docker", "exec", agent_name,
        "supervisorctl", action, program,
    ])
    return rc == 0, out
