"""Provision a plugged agent0-N.

The retired bash create-instance.sh only rendered files and pointed at the
TypeScript MCP server. A plugged v0.94 agent is the Continuwuity triplet plus
matrix-mcp-server-r2 as the only Matrix client. run_bot stays on disk and
stays stopped.

Run on the Docker host:

    python -m amctl.provision 6
    am-ctl create 6
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_TAG = "0.4.0"
DEFAULT_IMAGE = "ghcr.io/l0r3zz/matrix-mcp-server-r2"
PROFILES = ("agent0", "hacker", "researcher", "developer")
PENDING_TOKEN = "PENDING_REGISTRATION"
CONTAINER_SCRIPTS = (
    "startup-services.sh",
    "watchdog.sh",
    "preflight-check.sh",
    "derive-a0-token.sh",
    "check-token-sync.py",
    "switch-matrix-bot.sh",
    "switch-mcp-server.sh",
    "smoke-test-matrix-bot.sh",
    "sync-mcp-token-into-settings.py",
)
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_BOOTSTRAP = re.compile(r"registration token ([A-Za-z0-9]+)")
_HEALTH_PY = (
    "import urllib.request\n"
    "print(urllib.request.urlopen('http://127.0.0.1:3000/health', timeout=5).read().decode())\n"
)


class ProvisionError(Exception):
    """A provisioning step failed. The message must not contain a secret."""


@dataclass(frozen=True)
class InstanceAddress:
    instance_num: int
    name: str
    localpart: str
    matrix_user_id: str
    homeserver_name: str
    homeserver_fqdn: str
    agent_ip: str
    homeserver_ip: str
    web_port: int
    ssh_port: int
    mac_suffix: str
    display_name: str

    @property
    def homeserver_url(self) -> str:
        return f"http://{self.homeserver_name}:8008"


@dataclass(frozen=True)
class CmdResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Timeouts:
    homeserver: float = 90
    derive: float = 60
    supervisord: float = 90
    health: float = 120
    interval: float = 2


def address_for(instance_num: int) -> InstanceAddress:
    """Map instance N onto the fleet's fixed IP, port, and Matrix names."""
    if not isinstance(instance_num, int) or isinstance(instance_num, bool):
        raise ProvisionError("instance number must be an integer")
    if not 1 <= instance_num <= 250:
        raise ProvisionError("instance number must be 1 through 250")
    name = f"agent0-{instance_num}"
    homeserver_name = f"{name}-mhs"
    fqdn = f"{homeserver_name}.cybertribe.com"
    return InstanceAddress(
        instance_num=instance_num,
        name=name,
        localpart=name,
        matrix_user_id=f"@{name}:{fqdn}",
        homeserver_name=homeserver_name,
        homeserver_fqdn=fqdn,
        agent_ip=f"172.23.88.{instance_num}",
        homeserver_ip=f"172.23.89.{instance_num}",
        web_port=50000 + instance_num,
        ssh_port=50021 + instance_num,
        mac_suffix=f"{instance_num:02X}",
        display_name=f"Agent0-{instance_num}",
    )


def fleet_agent_row(address: InstanceAddress) -> tuple:
    """Row for fleet_ops.agents. am-ctl status reads this table, not Docker."""
    return (
        address.instance_num,
        address.name,
        address.matrix_user_id,
        f"https://{address.homeserver_ip}:8448",
        address.homeserver_fqdn,
        "http://localhost:80",
        "rust",
        "active",
    )


def register_in_fleet(address: InstanceAddress) -> None:
    """Insert the instance into the fleet registry. A second insert is a no-op."""
    try:
        asyncio.run(_insert_fleet_agent(fleet_agent_row(address)))
    except Exception as exc:
        raise ProvisionError(f"could not add {address.name} to the fleet registry") from exc
    print(f"Registered {address.name} in the fleet registry.")


async def _insert_fleet_agent(row: tuple) -> None:
    import asyncpg

    from amctl.config import settings

    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(
            """
            INSERT INTO agents (
                instance_num, name, matrix_user_id, homeserver_url, homeserver_fqdn,
                agent_zero_endpoint, bot_runtime, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (instance_num) DO NOTHING
            """,
            *row,
        )
    finally:
        await conn.close()


def default_template_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "templates"


def default_amctl_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def extract_bootstrap_token(logs: str) -> str | None:
    """Return Continuwuity's one-time registration token, if the log has one."""
    match = _BOOTSTRAP.search(_ANSI.sub("", logs))
    return match.group(1) if match else None


def health_is_plugged(body: dict, tag: str) -> bool:
    """True when /health shows this gateway tag, E2EE, the bot, and cross-signing."""
    return (
        body.get("version") == tag
        and body.get("e2ee") is True
        and body.get("botEnabled") is True
        and body.get("crossSigned") is True
    )


def supervisord_is_ready(result: CmdResult) -> bool:
    """True when supervisorctl reached the daemon.

    Exit 0 means every program is running. Exit 3 means the daemon answered
    and at least one program is stopped, exiting, or in backoff. run_bot stays
    stopped, and run_mcp stays in backoff until the gateway binary is installed.
    """
    return result.returncode in (0, 3)


def _status_tail(result: CmdResult) -> str:
    text = (result.stdout or result.stderr).strip()
    lines = [line.strip() for line in text.splitlines()[-4:] if line.strip()]
    tail = " | ".join(lines) if lines else "no status output"
    if len(tail) > 240:
        tail = tail[:240]
    return tail


def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value
    return values


def set_env_key(path: Path, key: str, value: str) -> None:
    """Replace or append one env line. Callers must not log value."""
    lines = path.read_text().splitlines() if path.exists() else []
    prefix = f"{key}="
    replaced = False
    updated: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            updated.append(prefix + value)
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(prefix + value)
    _write_secret(path, "\n".join(updated) + "\n")


def _write_secret(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
    os.chmod(path, 0o600)


def _substitute(text: str, mapping: dict[str, str]) -> str:
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def plugged_settings(template_text: str) -> str:
    """Point Agent Zero at the local gateway. The gateway reads its own .env."""
    data = json.loads(template_text)
    raw = data.get("mcp_servers") or "{}"
    servers = json.loads(raw) if isinstance(raw, str) else raw
    block = servers.setdefault("mcpServers", {})
    block["matrix"] = {
        "type": "streamable-http",
        "url": "http://localhost:3000/mcp",
    }
    data["mcp_servers"] = json.dumps(servers)
    return json.dumps(data, indent=4) + "\n"


def _ignore_build_debris(_directory: str, names: list[str]) -> set[str]:
    skipped = {"__pycache__", "target", ".git"}
    return {name for name in names if name in skipped or name.endswith(".pyc")}


def _amctl_api_key(environ: dict[str, str], amctl_dir: Path) -> str | None:
    key = environ.get("AMCTL_API_KEY", "").strip()
    if key:
        return key
    env_file = amctl_dir / ".env"
    if not env_file.is_file():
        return None
    found = parse_env(env_file.read_text()).get("AMCTL_API_KEY", "").strip()
    return found or None


def _self_signed_cert(crt: Path, key: Path, common_name: str) -> None:
    crt.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "ed25519",
            "-keyout",
            str(key),
            "-out",
            str(crt),
            "-days",
            "365",
            "-nodes",
            "-subj",
            f"/CN={common_name}",
        ],
        check=True,
        capture_output=True,
    )
    os.chmod(key, 0o600)


def render_instance(
    address: InstanceAddress,
    base_dir: Path,
    template_dir: Path,
    *,
    profile: str,
    force: bool = False,
    environ: dict[str, str] | None = None,
    amctl_dir: Path | None = None,
) -> Path:
    """Write the instance directory. Refuse to replace an existing one unless force."""
    if profile not in PROFILES:
        raise ProvisionError(f"unknown profile {profile}")
    environ = environ if environ is not None else dict(os.environ)
    amctl_dir = amctl_dir or default_amctl_dir()
    instance_dir = base_dir / address.name
    if instance_dir.exists() and not force:
        raise ProvisionError(
            f"{instance_dir} already exists. Pass --force to rewrite generated files, "
            "or --plug-only to install the gateway into it."
        )

    workdir = instance_dir / "usr" / "workdir"
    mhs_dir = instance_dir / "mhs"
    data_dir = mhs_dir / "continuwuity-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)

    mapping = {
        "__INSTANCE_NUM__": str(address.instance_num),
        "__MAC_SUFFIX__": address.mac_suffix,
        "__WEB_PORT__": str(address.web_port),
        "__SSH_PORT__": str(address.ssh_port),
        "{{INSTANCE}}": address.name,
        "{{TZ}}": environ.get("TZ", "America/Los_Angeles"),
        "{{PROFILE}}": profile,
        "{{MHS_IP}}": address.homeserver_ip,
        "{{MHS}}": address.homeserver_name,
    }
    compose = _substitute((template_dir / "docker-compose.yml.template").read_text(), mapping)
    (instance_dir / "docker-compose.yml").write_text(compose)
    caddy = _substitute((template_dir / "Caddyfile.template").read_text(), mapping)
    (mhs_dir / "Caddyfile").write_text(caddy)

    crt = mhs_dir / "server.crt"
    key = mhs_dir / "server.key"
    if not crt.exists() or not key.exists():
        _self_signed_cert(crt, key, address.homeserver_fqdn)

    _write_instance_env(instance_dir / ".env", address, template_dir, mapping, profile, environ)
    _write_mcp_tree(workdir, template_dir, address, environ, amctl_dir)
    _write_bot_tree(workdir, template_dir, address)
    _copy_container_scripts(workdir, template_dir / "scripts")
    for prompt in template_dir.glob("*.promptinclude.md"):
        shutil.copyfile(prompt, workdir / prompt.name)

    settings_template = template_dir / "settings.json.template"
    settings_path = instance_dir / "usr" / "settings.json"
    if settings_template.is_file():
        settings_path.write_text(plugged_settings(settings_template.read_text()))
    return instance_dir


def _write_instance_env(
    path: Path,
    address: InstanceAddress,
    template_dir: Path,
    mapping: dict[str, str],
    profile: str,
    environ: dict[str, str],
) -> None:
    existing = parse_env(path.read_text()) if path.exists() else {}
    template = (template_dir / "env.template").read_text()
    text = _substitute(template, mapping)
    if "A0_SET_agent_profile=" not in text:
        text += f"\nA0_SET_agent_profile={profile}\n"
    password = existing.get("MATRIX_PASSWORD") or secrets.token_urlsafe(24)
    extra = [
        "",
        "# Matrix account. The access token is filled in after registration.",
        f"MATRIX_USERNAME={address.localpart}",
        f"MATRIX_PASSWORD={password}",
        f"MATRIX_HOMESERVER_URL={address.homeserver_url}",
        f"MATRIX_USER_ID={address.matrix_user_id}",
    ]
    if "MATRIX_ACCESS_TOKEN" in existing and not existing["MATRIX_ACCESS_TOKEN"].startswith("PENDING_"):
        extra.append(f"MATRIX_ACCESS_TOKEN={existing['MATRIX_ACCESS_TOKEN']}")
    for key, value in environ.items():
        if key.startswith("API_KEY_") and value:
            extra.append(f"{key}={value}")
    text = text.rstrip() + "\n" + "\n".join(extra) + "\n"
    if "A0_API_KEY=" in text:
        raise ProvisionError("refusing to write A0_API_KEY into the instance env")
    _write_secret(path, text)


def _write_mcp_tree(
    workdir: Path,
    template_dir: Path,
    address: InstanceAddress,
    environ: dict[str, str],
    amctl_dir: Path,
) -> None:
    mcp_dir = workdir / "matrix-mcp-server"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    env_path = mcp_dir / ".env"
    existing = parse_env(env_path.read_text()) if env_path.exists() else {}
    token = existing.get("MATRIX_ACCESS_TOKEN", PENDING_TOKEN)
    password_path = mcp_dir / ".matrix-password"
    if not password_path.exists():
        instance_password = parse_env((workdir.parents[1] / ".env").read_text()).get("MATRIX_PASSWORD", "")
        if not instance_password:
            raise ProvisionError("instance .env has no MATRIX_PASSWORD")
        _write_secret(password_path, instance_password + "\n")

    lines = [
        "PORT=3000",
        f"MATRIX_HOMESERVER_URL={address.homeserver_url}",
        f"MATRIX_USER_ID={address.matrix_user_id}",
        f"MATRIX_ACCESS_TOKEN={token}",
        "E2EE_ENABLED=true",
        "CRYPTO_STORE_PATH=/a0/usr/workdir/matrix-mcp-server/crypto-store",
        "MATRIX_UIAA_PASSWORD_FILE=/a0/usr/workdir/matrix-mcp-server/.matrix-password",
        "BOT_ENABLED=true",
        f"BOT_DISPLAY_NAME={address.display_name}",
        f"AGENT_IDENTITY={address.display_name}",
        "A0_API_URL=http://localhost:80/api/api_message",
        "AMCTL_URL=http://172.23.88.254:8077",
        "BOT_STATE_DIR=/a0/usr/workdir/matrix-bot",
    ]
    api_key = _amctl_api_key(environ, amctl_dir)
    if api_key:
        lines.append(f"AMCTL_API_KEY={api_key}")
    text = "\n".join(lines) + "\n"
    if "MODEL_ACCEPTS_IMAGES=" in text or "A0_API_KEY=" in text:
        raise ProvisionError("refusing to write a disallowed MCP env line")
    _write_secret(env_path, text)

    source = template_dir / "scripts" / "run-mcp-wrapper.sh.template"
    dest = mcp_dir / "run-mcp-wrapper.sh"
    if source.is_file():
        shutil.copyfile(source, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_bot_tree(workdir: Path, template_dir: Path, address: InstanceAddress) -> None:
    """Keep matrix-bot on disk for rollback. Do not start it."""
    source = template_dir / "matrix-bot"
    dest = workdir / "matrix-bot"
    if source.is_dir():
        shutil.copytree(source, dest, dirs_exist_ok=True, ignore=_ignore_build_debris)
    env_path = dest / ".env"
    template = dest / ".env.template"
    if not env_path.exists() and template.is_file():
        text = template.read_text().replace("__INSTANCE_NUM__", str(address.instance_num))
        text = text.replace("__MATRIX_ACCESS_TOKEN__", PENDING_TOKEN)
        _write_secret(env_path, text)
    if template.exists():
        template.unlink()


def _copy_container_scripts(workdir: Path, scripts_dir: Path) -> None:
    for name in CONTAINER_SCRIPTS:
        source = scripts_dir / name
        if not source.is_file():
            continue
        dest = workdir / name
        shutil.copyfile(source, dest)
        if name.endswith(".sh"):
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class LocalHost:
    """Docker and HTTP on the machine that owns the agent containers."""

    def run(
        self,
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> CmdResult:
        proc = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
        )
        if check and proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            tail = detail[-1] if detail else args[0]
            raise ProvisionError(f"command failed ({args[0]}): {tail}")
        return CmdResult(proc.returncode, proc.stdout, proc.stderr)

    def request(
        self,
        method: str,
        url: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict]:
        try:
            response = httpx.request(method, url, json=body, headers=headers, timeout=30.0)
        except httpx.HTTPError:
            return 0, {}
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        return response.status_code, payload


def _wait(predicate, timeout: float, interval: float, sleep, failure: str):
    deadline = time.monotonic() + timeout
    while True:
        if predicate():
            return
        if time.monotonic() >= deadline:
            raise ProvisionError(failure)
        sleep(interval)


def _register(host, address: InstanceAddress, password: str) -> str:
    base = f"http://{address.homeserver_ip}:8008/_matrix/client/v3"
    _status, login = host.request(
        "POST",
        f"{base}/login",
        {
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": address.localpart},
            "password": password,
        },
    )
    token = login.get("access_token")
    if isinstance(token, str) and token:
        return token

    logs = host.run(["docker", "logs", f"{address.name}-continuwuity"])
    bootstrap = extract_bootstrap_token(logs.stdout + logs.stderr)
    if not bootstrap:
        raise ProvisionError("Continuwuity did not log a registration token")

    _status, started = host.request(
        "POST",
        f"{base}/register",
        {"username": address.localpart, "password": password},
    )
    token = started.get("access_token")
    if isinstance(token, str) and token:
        return token
    session = started.get("session")
    if not isinstance(session, str) or not session:
        err = started.get("errcode", "registration failed")
        raise ProvisionError(f"Matrix registration failed ({err})")

    _status, finished = host.request(
        "POST",
        f"{base}/register",
        {
            "username": address.localpart,
            "password": password,
            "auth": {
                "type": "m.login.registration_token",
                "token": bootstrap,
                "session": session,
            },
        },
    )
    token = finished.get("access_token")
    if not isinstance(token, str) or not token:
        err = finished.get("errcode", "registration failed")
        raise ProvisionError(f"Matrix registration failed ({err})")
    return token


def _device_id(host, address: InstanceAddress, token: str) -> str | None:
    status, body = host.request(
        "GET",
        f"http://{address.homeserver_ip}:8008/_matrix/client/v3/account/whoami",
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200:
        return None
    device = body.get("device_id", "")
    if not isinstance(device, str) or not device:
        return None
    if device == "AgentZeroBot":
        raise ProvisionError("refusing to bind the gateway to the AgentZeroBot device")
    return device


def _try_step_ca(host, address: InstanceAddress, instance_dir: Path) -> None:
    which = host.run(["bash", "-lc", "command -v step"], check=False)
    if which.returncode != 0:
        print("step CLI not found. Federation keeps the placeholder certificate.")
        return
    crt = instance_dir / "mhs" / "server.crt"
    key = instance_dir / "mhs" / "server.key"
    issuer = host.run(["openssl", "x509", "-in", str(crt), "-noout", "-issuer"], check=False)
    if "CyberTribe CA" in (issuer.stdout + issuer.stderr):
        print("Step-CA certificate already present.")
        return
    args = [
        "step",
        "ca",
        "certificate",
        address.homeserver_fqdn,
        str(crt),
        str(key),
        "--san",
        address.homeserver_fqdn,
        "--not-after=8760h",
        "--force",
    ]
    passwd = Path("/opt/agent-zero/multi-instance-deploy/scripts/step_ca_provisioner_passwd")
    if passwd.is_file():
        args.extend(["--provisioner-password-file", str(passwd)])
    host.run(args)
    os.chmod(key, 0o600)
    _append_step_root(host, crt)
    # Caddy reads the certificate at start. A reload can keep serving the
    # placeholder, and Synapse then cannot verify the homeserver.
    host.run(["docker", "restart", f"{address.name}-mhs"], check=False)


def _append_step_root(host, crt: Path) -> None:
    """Add the step-ca root so the file matches the chain Synapse already trusts."""
    root_path = crt.with_name("root.crt")
    fetched = host.run(["step", "ca", "root", str(root_path), "--force"], check=False)
    if fetched.returncode != 0 or not root_path.is_file():
        return
    bundle = crt.read_text()
    root = root_path.read_text().strip()
    if root and root not in bundle:
        if bundle and not bundle.endswith("\n"):
            bundle += "\n"
        crt.write_text(bundle + root + "\n")
    root_path.unlink(missing_ok=True)


def bring_up(
    address: InstanceAddress,
    instance_dir: Path,
    template_dir: Path,
    *,
    host=None,
    tag: str = DEFAULT_TAG,
    image: str = DEFAULT_IMAGE,
    timeouts: Timeouts | None = None,
    sleep=time.sleep,
) -> None:
    """Start the triplet, register the Matrix user, and install the gateway."""
    host = host or LocalHost()
    timeouts = timeouts or Timeouts()
    env_path = instance_dir / ".env"
    password = parse_env(env_path.read_text()).get("MATRIX_PASSWORD", "")
    if not password:
        raise ProvisionError("instance .env has no MATRIX_PASSWORD")

    print(f"Starting {address.name}")
    host.run(["docker", "compose", "up", "-d"], cwd=instance_dir)

    versions = f"http://{address.homeserver_ip}:8008/_matrix/client/versions"

    def homeserver_ready() -> bool:
        status, _body = host.request("GET", versions)
        return status == 200

    _wait(
        homeserver_ready,
        timeouts.homeserver,
        timeouts.interval,
        sleep,
        "Continuwuity did not become ready",
    )

    mcp_env = instance_dir / "usr" / "workdir" / "matrix-mcp-server" / ".env"
    existing = parse_env(mcp_env.read_text()).get("MATRIX_ACCESS_TOKEN", "")
    token = ""
    if existing and not existing.startswith("PENDING_"):
        token = existing if _device_id(host, address, existing) else ""
    if not token:
        token = _register(host, address, password)
        if not _device_id(host, address, token):
            raise ProvisionError("MCP token has no device id")
    set_env_key(mcp_env, "MATRIX_ACCESS_TOKEN", token)
    set_env_key(env_path, "MATRIX_ACCESS_TOKEN", token)
    print("Gateway token written.")

    derive = ["/a0/usr/workdir/derive-a0-token.sh"]

    def derived() -> bool:
        result = host.run(["docker", "exec", address.name, *derive], check=False)
        return result.returncode == 0 and bool(result.stdout.strip())

    _wait(derived, timeouts.derive, timeouts.interval, sleep, "could not derive the Agent Zero credential")
    print("Agent Zero credential derived.")

    _try_step_ca(host, address, instance_dir)

    last_status = CmdResult(1, "", "")

    def supervisord_ready() -> bool:
        nonlocal last_status
        last_status = host.run(
            ["docker", "exec", address.name, "supervisorctl", "status"],
            check=False,
        )
        return supervisord_is_ready(last_status)

    try:
        _wait(
            supervisord_ready,
            timeouts.supervisord,
            timeouts.interval,
            sleep,
            "supervisord did not become ready",
        )
    except ProvisionError as exc:
        raise ProvisionError(
            f"{exc} (supervisorctl exit {last_status.returncode}: {_status_tail(last_status)})"
        ) from exc

    deploy = template_dir / "scripts" / "deploy-mms-r2-to-agent.sh"
    if not deploy.is_file():
        raise ProvisionError(f"missing {deploy}")
    deploy_env = os.environ.copy()
    deploy_env["MMS_R2_TAG"] = tag
    deploy_env["GHCR_IMAGE"] = image
    print(f"Installing {image}:{tag}")
    host.run([str(deploy), str(address.instance_num)], cwd=deploy.parent, env=deploy_env)

    version = host.run(
        [
            "docker",
            "exec",
            address.name,
            "/a0/usr/workdir/matrix-mcp-server/matrix-mcp-server-r2",
            "--version",
        ]
    )
    expected = f"matrix-mcp-server-r2 {tag}"
    if expected not in version.stdout:
        raise ProvisionError(f"gateway --version was not {expected}")

    def healthy() -> bool:
        result = host.run(["docker", "exec", address.name, "python3", "-c", _HEALTH_PY], check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return False
        try:
            body = json.loads(result.stdout)
        except json.JSONDecodeError:
            return False
        return isinstance(body, dict) and health_is_plugged(body, tag)

    _wait(
        healthy,
        timeouts.health,
        timeouts.interval,
        sleep,
        f"/health did not report {tag} with e2ee, botEnabled, and crossSigned",
    )

    bot = host.run(["docker", "exec", address.name, "supervisorctl", "status", "run_bot"], check=False)
    parts = bot.stdout.split()
    if len(parts) >= 2 and parts[1] == "RUNNING":
        raise ProvisionError("run_bot is RUNNING")
    rust = host.run(
        ["docker", "exec", address.name, "sh", "-c", "pgrep -fc '[m]atrix-bot-rust' || true"],
        check=False,
    )
    count = rust.stdout.strip() or "0"
    if count != "0":
        raise ProvisionError("matrix-bot-rust is running")

    print(f"{address.name} is plugged.")
    print(f"  run_mcp reports {expected}")
    print(f"  /health version={tag} e2ee=true botEnabled=true crossSigned=true")
    print("  run_bot is stopped")
    print(f"Invite {address.matrix_user_id} to Fleet HQ Clean.")


def provision_agent(
    instance_num: int,
    *,
    profile: str = "agent0",
    base_dir: Path | None = None,
    template_dir: Path | None = None,
    render_only: bool = False,
    plug_only: bool = False,
    force: bool = False,
    tag: str = DEFAULT_TAG,
    host=None,
    environ: dict[str, str] | None = None,
    timeouts: Timeouts | None = None,
    sleep=time.sleep,
    register=None,
) -> Path:
    if render_only and plug_only:
        raise ProvisionError("pass only one of --render-only and --plug-only")
    address = address_for(instance_num)
    base_dir = base_dir or Path("/opt/agent-zero")
    template_dir = template_dir or default_template_dir()
    instance_dir = base_dir / address.name
    print(f"Provisioning {address.name} (profile {profile})")
    print(f"  files: {instance_dir}")
    print(f"  agent IP: {address.agent_ip}")
    print(f"  homeserver IP: {address.homeserver_ip}")
    print(f"  gateway: {DEFAULT_IMAGE}:{tag}")

    if not plug_only:
        render_instance(
            address,
            base_dir,
            template_dir,
            profile=profile,
            force=force,
            environ=environ,
        )
        print(f"Rendered {instance_dir}")
    elif not instance_dir.is_dir():
        raise ProvisionError(f"{instance_dir} does not exist")

    if not render_only:
        bring_up(
            address,
            instance_dir,
            template_dir,
            host=host,
            tag=tag,
            timeouts=timeouts,
            sleep=sleep,
        )
        if register is not None:
            register(address)
    return instance_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision a plugged agent0-N with matrix-mcp-server-r2 0.4.0.",
    )
    parser.add_argument("instance_num", type=int, help="Instance number, for example 6")
    parser.add_argument("-p", "--profile", default="agent0", choices=PROFILES)
    parser.add_argument("--render-only", action="store_true", help="Write files and do not start Docker")
    parser.add_argument(
        "--plug-only",
        action="store_true",
        help="Register and install the gateway into an existing instance directory",
    )
    parser.add_argument("--base-dir", type=Path, default=Path("/opt/agent-zero"))
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite generated files. Keep Continuwuity data, the crypto store, and an existing password.",
    )
    parser.add_argument("--mms-tag", default=DEFAULT_TAG, help="matrix-mcp-server-r2 image tag")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        provision_agent(
            args.instance_num,
            profile=args.profile,
            base_dir=args.base_dir,
            render_only=args.render_only,
            plug_only=args.plug_only,
            force=args.force,
            tag=args.mms_tag,
            register=None if args.render_only else register_in_fleet,
        )
    except ProvisionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
