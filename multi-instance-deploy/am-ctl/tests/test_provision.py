"""Render and plug-sequence tests for a new agent0-N."""

import json
import stat
from pathlib import Path

from click.testing import CliRunner

from amctl.provision import (
    CmdResult,
    ProvisionError,
    Timeouts,
    address_for,
    extract_bootstrap_token,
    fleet_agent_row,
    health_is_plugged,
    main,
    parse_env,
    provision_agent,
    supervisord_is_ready,
)
from amctl_cli.cli import main as cli_main

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
FAST = Timeouts(homeserver=1, derive=1, supervisord=1, health=1, interval=0)


def test_address_for_canary_six():
    address = address_for(6)
    assert address.name == "agent0-6"
    assert address.matrix_user_id == "@agent0-6:agent0-6-mhs.cybertribe.com"
    assert address.agent_ip == "172.23.88.6"
    assert address.homeserver_ip == "172.23.89.6"
    assert address.web_port == 50006
    assert address.ssh_port == 50027
    assert address.mac_suffix == "06"


def test_address_rejects_values_outside_the_octet_pool():
    for number in (0, 251, -1):
        try:
            address_for(number)
        except ProvisionError:
            continue
        raise AssertionError(number)


def test_extract_bootstrap_token_ignores_ansi():
    logs = "\x1b[32mregistration token Abcd1234\x1b[0m"
    assert extract_bootstrap_token(logs) == "Abcd1234"


def test_fleet_agent_row_matches_the_registry_shape():
    assert fleet_agent_row(address_for(6)) == (
        6,
        "agent0-6",
        "@agent0-6:agent0-6-mhs.cybertribe.com",
        "https://172.23.89.6:8448",
        "agent0-6-mhs.cybertribe.com",
        "http://localhost:80",
        "rust",
        "active",
    )


def test_supervisord_is_ready_accepts_a_stopped_program():
    assert supervisord_is_ready(CmdResult(0, "run_mcp RUNNING\n", ""))
    assert supervisord_is_ready(CmdResult(3, "run_bot STOPPED\nrun_mcp BACKOFF\n", ""))
    assert not supervisord_is_ready(CmdResult(1, "", "container is restarting"))
    assert not supervisord_is_ready(CmdResult(4, "", "refused connection"))


def test_health_requires_the_gateway_tag_and_bot():
    assert health_is_plugged(
        {"version": "0.4.0", "e2ee": True, "botEnabled": True, "crossSigned": True},
        "0.4.0",
    )
    assert not health_is_plugged(
        {"version": "0.3.1", "e2ee": True, "botEnabled": True, "crossSigned": True},
        "0.4.0",
    )


def test_render_writes_a_plugged_tree(tmp_path: Path):
    instance = provision_agent(
        6,
        base_dir=tmp_path,
        template_dir=TEMPLATE_DIR,
        render_only=True,
        environ={"API_KEY_OPENROUTER": "sk-test", "AMCTL_API_KEY": "amctl-test"},
    )
    compose = (instance / "docker-compose.yml").read_text()
    assert "172.23.88.6" in compose
    assert "172.23.89.6" in compose
    assert "50006:80" in compose
    assert "50027:22" in compose
    assert "02:42:AC:17:58:06" in compose
    assert "A0_API_KEY" not in compose

    env = parse_env((instance / ".env").read_text())
    assert env["MATRIX_USER_ID"] == "@agent0-6:agent0-6-mhs.cybertribe.com"
    assert env["A0_SET_agent_profile"] == "agent0"
    assert env["API_KEY_OPENROUTER"] == "sk-test"
    assert "A0_API_KEY" not in env
    assert (instance / ".env").stat().st_mode & 0o777 == 0o600

    mcp = parse_env((instance / "usr/workdir/matrix-mcp-server/.env").read_text())
    assert mcp["BOT_ENABLED"] == "true"
    assert mcp["E2EE_ENABLED"] == "true"
    assert mcp["CRYPTO_STORE_PATH"] == "/a0/usr/workdir/matrix-mcp-server/crypto-store"
    assert mcp["MATRIX_ACCESS_TOKEN"] == "PENDING_REGISTRATION"
    assert mcp["AMCTL_API_KEY"] == "amctl-test"
    assert "MODEL_ACCEPTS_IMAGES" not in mcp
    password_file = instance / "usr/workdir/matrix-mcp-server/.matrix-password"
    assert password_file.read_text().strip() == env["MATRIX_PASSWORD"]
    assert password_file.stat().st_mode & 0o777 == 0o600

    settings = json.loads((instance / "usr/settings.json").read_text())
    servers = json.loads(settings["mcp_servers"])
    assert servers["mcpServers"]["matrix"] == {
        "type": "streamable-http",
        "url": "http://localhost:3000/mcp",
    }
    assert "open-brain" in servers["mcpServers"]
    assert "matrix_access_token" not in settings["mcp_servers"]

    assert (instance / "usr/workdir/startup-services.sh").is_file()
    assert (instance / "usr/workdir/matrix-bot/matrix-bot-rust").is_file()
    assert not (instance / "usr/workdir/split-bot-device.sh").exists()
    assert not (instance / "usr/workdir/matrix-mcp-server/package.json").exists()
    wrapper = instance / "usr/workdir/matrix-mcp-server/run-mcp-wrapper.sh"
    assert wrapper.stat().st_mode & stat.S_IXUSR


def test_render_refuses_an_existing_directory(tmp_path: Path):
    provision_agent(6, base_dir=tmp_path, template_dir=TEMPLATE_DIR, render_only=True, environ={})
    try:
        provision_agent(6, base_dir=tmp_path, template_dir=TEMPLATE_DIR, render_only=True, environ={})
    except ProvisionError as exc:
        assert "already exists" in str(exc)
        return
    raise AssertionError("existing instance was overwritten")


def test_force_keeps_password_and_homeserver_data(tmp_path: Path):
    instance = provision_agent(6, base_dir=tmp_path, template_dir=TEMPLATE_DIR, render_only=True, environ={})
    password = parse_env((instance / ".env").read_text())["MATRIX_PASSWORD"]
    marker = instance / "mhs/continuwuity-data/keep-me"
    marker.write_text("identity")
    provision_agent(
        6,
        base_dir=tmp_path,
        template_dir=TEMPLATE_DIR,
        render_only=True,
        force=True,
        environ={},
    )
    again = parse_env((instance / ".env").read_text())
    assert again["MATRIX_PASSWORD"] == password
    assert again["MATRIX_USERNAME"] == "agent0-6"
    assert marker.read_text() == "identity"
    assert (instance / ".env").read_text().count("MATRIX_USERNAME=") == 1


class FakeHost:
    def __init__(self, mcp_env: Path):
        self.mcp_env = mcp_env
        self.calls: list[list[str]] = []

    def run(self, args, cwd=None, check=True, env=None):
        self.calls.append(args)
        joined = " ".join(args)
        if args[:3] == ["bash", "-lc", "command -v step"]:
            return CmdResult(1, "", "missing")
        if args[:2] == ["docker", "logs"]:
            return CmdResult(0, "\x1b[32mregistration token Abcd1234\x1b[0m\n", "")
        if "derive-a0-token.sh" in joined:
            return CmdResult(0, "abc123def456\n", "")
        if "deploy-mms-r2-to-agent.sh" in joined:
            text = self.mcp_env.read_text()
            assert "syt_test_token" in text
            assert "PENDING_REGISTRATION" not in text
            assert env["MMS_R2_TAG"] == "0.4.0"
            return CmdResult(0, "", "")
        if "--version" in args:
            return CmdResult(0, "matrix-mcp-server-r2 0.4.0\n", "")
        if "urlopen" in joined:
            body = json.dumps(
                {"version": "0.4.0", "e2ee": True, "botEnabled": True, "crossSigned": True}
            )
            return CmdResult(0, body + "\n", "")
        if args[-2:] == ["status", "run_bot"]:
            return CmdResult(0, "run_bot                         STOPPED\n", "")
        if args[-1:] == ["status"] and "supervisorctl" in args:
            return CmdResult(3, "run_bot STOPPED\nrun_mcp BACKOFF\n", "")
        if "matrix-bot-rust" in joined:
            return CmdResult(0, "0\n", "")
        return CmdResult(0, "", "")

    def request(self, method, url, body=None, headers=None):
        if url.endswith("/versions"):
            return 200, {"versions": ["v1.11"]}
        if url.endswith("/login"):
            return 403, {"errcode": "M_FORBIDDEN"}
        if url.endswith("/register") and body and "auth" not in body:
            return 401, {"session": "sess1"}
        if url.endswith("/register"):
            return 200, {"access_token": "syt_test_token", "device_id": "DEVICE1"}
        if url.endswith("/whoami"):
            return 200, {"device_id": "DEVICE1"}
        raise AssertionError(url)


def test_bring_up_installs_the_gateway_and_leaves_the_bot_stopped(tmp_path: Path):
    instance = provision_agent(6, base_dir=tmp_path, template_dir=TEMPLATE_DIR, render_only=True, environ={})
    host = FakeHost(instance / "usr/workdir/matrix-mcp-server/.env")
    provision_agent(
        6,
        base_dir=tmp_path,
        template_dir=TEMPLATE_DIR,
        plug_only=True,
        host=host,
        timeouts=FAST,
        sleep=lambda _seconds: None,
        environ={},
    )
    flat = [" ".join(call) for call in host.calls]
    assert any(call[:3] == ["docker", "compose", "up"] for call in host.calls)
    assert all("down" not in call for call in flat)
    assert any("deploy-mms-r2-to-agent.sh" in call and call.endswith(" 6") for call in flat)
    assert all("split-bot-device" not in call for call in flat)
    assert all("rust-restart" not in call for call in flat)
    mcp = parse_env((instance / "usr/workdir/matrix-mcp-server/.env").read_text())
    assert mcp["MATRIX_ACCESS_TOKEN"] == "syt_test_token"
    assert mcp["BOT_ENABLED"] == "true"


def test_bring_up_reports_the_supervisorctl_exit_when_the_daemon_is_down(tmp_path: Path):
    instance = provision_agent(6, base_dir=tmp_path, template_dir=TEMPLATE_DIR, render_only=True, environ={})

    class Unreachable(FakeHost):
        def run(self, args, cwd=None, check=True, env=None):
            if args[-1:] == ["status"] and "supervisorctl" in args and args[-2:] != ["status", "run_bot"]:
                self.calls.append(args)
                return CmdResult(4, "", "refused connection")
            return super().run(args, cwd=cwd, check=check, env=env)

    host = Unreachable(instance / "usr/workdir/matrix-mcp-server/.env")
    try:
        provision_agent(
            6,
            base_dir=tmp_path,
            template_dir=TEMPLATE_DIR,
            plug_only=True,
            host=host,
            timeouts=FAST,
            sleep=lambda _seconds: None,
            environ={},
        )
    except ProvisionError as exc:
        assert "supervisorctl exit 4" in str(exc)
        assert "refused connection" in str(exc)
        return
    raise AssertionError("unreachable supervisord was treated as ready")


def test_module_cli_render_only(tmp_path: Path):
    code = main(["6", "--render-only", "--base-dir", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "agent0-6" / "docker-compose.yml").is_file()


def test_am_ctl_create_render_only(tmp_path: Path):
    result = CliRunner().invoke(
        cli_main,
        ["create", "6", "--render-only", "--base-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "agent0-6" / "usr/workdir/matrix-mcp-server/.env").is_file()


def test_am_ctl_create_registers_the_fleet_row(monkeypatch, tmp_path: Path):
    from amctl.provision import register_in_fleet

    seen = {}

    def fake_provision(instance_num, **kwargs):
        seen["instance_num"] = instance_num
        seen.update(kwargs)
        return tmp_path

    monkeypatch.setattr("amctl.provision.provision_agent", fake_provision)
    result = CliRunner().invoke(cli_main, ["create", "6", "--base-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert seen["instance_num"] == 6
    assert seen["register"] is register_in_fleet
    assert seen["render_only"] is False


def test_am_ctl_create_render_only_skips_the_fleet_row(monkeypatch, tmp_path: Path):
    seen = {}

    def fake_provision(instance_num, **kwargs):
        seen.update(kwargs)
        return tmp_path

    monkeypatch.setattr("amctl.provision.provision_agent", fake_provision)
    result = CliRunner().invoke(
        cli_main,
        ["create", "6", "--render-only", "--base-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert seen["register"] is None
