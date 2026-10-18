"""am-ctl CLI -- thin client for the am-ctl API."""

import sys

import click
import httpx

from amctl_cli.client import AmCtlClient
from amctl_cli.output import (
    console,
    print_agent_drift_report,
    print_agent_health_detail,
    print_agent_model_detail,
    print_agent_status,
    print_agents_table,
    print_alerts_table,
    print_backup_run_result,
    print_backup_verify_result,
    print_backups_table,
    print_credential_collisions,
    print_credential_verify,
    print_deploy_result,
    print_deploy_status,
    print_fleet_drift_report,
    print_fleet_health_matrix,
    print_fleet_models_table,
    print_fleet_summary,
    print_json,
    print_models_diagnose,
    print_reconcile_apply,
    print_reconcile_plan,
    print_releases_table,
)


def get_client(ctx: click.Context) -> AmCtlClient:
    return ctx.obj["client"]


@click.group()
@click.option("--server", default="http://localhost:8077", envvar="AMCTL_SERVER", help="am-ctl server URL")
@click.option("--api-key", default="amctl-dev-key-2026", envvar="AMCTL_API_KEY", help="API key")
@click.option("--output", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.pass_context
def main(ctx, server, api_key, output_format):
    """am-ctl -- Agent Matrix fleet management."""
    ctx.ensure_object(dict)
    ctx.obj["client"] = AmCtlClient(base_url=server, api_key=api_key)
    ctx.obj["output_format"] = output_format


@main.command("status")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def fleet_status(ctx, cmd_output):
    """Fleet-wide summary."""
    client = get_client(ctx)
    try:
        data = client.get_fleet_status()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    fmt = cmd_output or ctx.obj["output_format"]
    if fmt == "json":
        print_json(data)
    else:
        print_fleet_summary(data)


@main.group("agents")
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def agents_group(ctx, grp_output):
    """Agent registry commands."""
    if grp_output:
        ctx.obj["output_format"] = grp_output


@agents_group.command("list")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def agents_list(ctx, cmd_output):
    """List all agents."""
    client = get_client(ctx)
    try:
        data = client.list_agents()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    fmt = cmd_output or ctx.obj["output_format"]
    if fmt == "json":
        print_json(data)
    else:
        print_agents_table(data)


@agents_group.command("show")
@click.argument("name")
@click.option("--live/--no-live", default=True, help="Include live status from Docker/Matrix")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def agents_show(ctx, name, live, cmd_output):
    """Show detailed agent info."""
    client = get_client(ctx)
    try:
        if live:
            data = client.get_agent_status(name)
        else:
            data = {"agent": client.get_agent(name)}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent '{name}' not found[/red]")
        else:
            console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    fmt = cmd_output or ctx.obj["output_format"]
    if fmt == "json":
        print_json(data)
    else:
        print_agent_status(data)


@main.command("health")
@click.argument("agent_name", required=False)
@click.option("--check", "run_check", is_flag=True, help="Trigger an immediate live health check")
@click.option("--history", "show_history", is_flag=True, help="Show health check history for an agent")
@click.option("--server-only", is_flag=True, help="Only check am-ctl server reachability")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def health_cmd(ctx, agent_name, run_check, show_history, server_only, cmd_output):
    """Fleet or per-agent health matrix (Phase 2)."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]

    try:
        if server_only:
            data = client.health()
            if fmt == "json":
                print_json(data)
            else:
                console.print(f"[green]Server OK[/green]  version={data.get('version')}")
            return

        if agent_name:
            if show_history:
                data = client.get_agent_health_history(agent_name)
                print_json(data)
                return
            if run_check:
                data = client.trigger_agent_health_check(agent_name)
            else:
                data = client.get_agent_health(agent_name)
            if fmt == "json":
                print_json(data)
            else:
                print_agent_health_detail(data)
        else:
            if run_check:
                data = client.trigger_fleet_health_check()
            else:
                data = client.get_fleet_health()
            if fmt == "json":
                print_json(data)
            else:
                print_fleet_health_matrix(data)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
        else:
            console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)


@main.group("alerts")
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def alerts_group(ctx, grp_output):
    """Alert management commands."""
    if grp_output:
        ctx.obj["output_format"] = grp_output


@alerts_group.command("list")
@click.option("--status", default="open", type=click.Choice(["open", "acked", "resolved", "all"]))
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def alerts_list(ctx, status, cmd_output):
    """List alerts."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.list_alerts(status=status)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_alerts_table(data)


@alerts_group.command("ack")
@click.argument("alert_id", type=int)
@click.option("--operator", default="cli:operator", help="Operator identifier")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def alerts_ack(ctx, alert_id, operator, cmd_output):
    """Acknowledge an alert."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.ack_alert(alert_id, operator=operator)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        console.print(f"[green]Alert {alert_id} acknowledged by {operator}[/green]")


@main.group("credentials")
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def credentials_group(ctx, grp_output):
    """Credential authority & verification commands (Phase 3)."""
    if grp_output:
        ctx.obj["output_format"] = grp_output


@credentials_group.command("verify")
@click.argument("agent_name")
@click.option("--sync/--no-sync", default=True, help="Sync registry fingerprint if canonical & deployed match")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def credentials_verify(ctx, agent_name, sync, cmd_output):
    """Verify agent's deployed credential matches Agent Zero canonical token."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.verify_agent_credentials(agent_name, sync_registry=sync)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_credential_verify(data)
    if not data.get("valid"):
        sys.exit(1)


@credentials_group.command("check-collisions")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def credentials_check_collisions(ctx, cmd_output):
    """Check for cross-fleet credential fingerprint collisions."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.check_credential_collisions()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_credential_collisions(data)
    if data.get("has_collisions"):
        sys.exit(1)


@main.group("reconcile")
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def reconcile_group(ctx, grp_output):
    """Fleet reconciliation commands (Phase 4)."""
    if grp_output:
        ctx.obj["output_format"] = grp_output


@reconcile_group.command("check")
@click.argument("agent_name", required=False)
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def reconcile_check_cmd(ctx, agent_name, cmd_output):
    """Read-only drift check across the fleet or for a single agent."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.reconcile_check(agent_name=agent_name)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
        else:
            console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    elif agent_name:
        print_agent_drift_report(data)
    else:
        print_fleet_drift_report(data)


@reconcile_group.command("plan")
@click.argument("agent_name")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def reconcile_plan_cmd(ctx, agent_name, cmd_output):
    """Compute read-only remediation plan for a single agent."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.reconcile_plan(agent_name=agent_name)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
        else:
            console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_reconcile_plan(data)


@reconcile_group.command("apply")
@click.argument("agent_name")
@click.option("--yes", "-y", is_flag=True, help="Confirm applying reconciliation changes")
@click.option("--operator", default="cli:reconcile_apply", help="Operator identifier for audit log")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def reconcile_apply_cmd(ctx, agent_name, yes, operator, cmd_output):
    """Apply planned reconciliation actions for a single agent."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        if not yes:
            plan = client.reconcile_plan(agent_name=agent_name)
            if plan.get("clean"):
                if fmt == "json":
                    print_json({"agent_name": agent_name, "noop": True, "success": True})
                else:
                    console.print(f"[green]{agent_name} is already CLEAN -- nothing to apply.[/green]")
                return
            print_reconcile_plan(plan)
            if not click.confirm(f"Apply {len(plan.get('actions', []))} planned action(s) to {agent_name}?"):
                console.print("[yellow]Aborted.[/yellow]")
                sys.exit(1)

        data = client.reconcile_apply(agent_name=agent_name, operator=operator)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
        else:
            console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_reconcile_apply(data)

    if not data.get("success"):
        sys.exit(1)


@reconcile_group.command("history")
@click.argument("agent_name", required=False)
@click.option("--limit", default=20, type=int, help="Max entries to return")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def reconcile_history_cmd(ctx, agent_name, limit, cmd_output):
    """Show past reconciliation runs."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.reconcile_history(agent_name=agent_name, limit=limit)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)
    print_json(data)


@main.group("backup")
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def backup_group(ctx, grp_output):
    """Database & infrastructure backup commands (Phase 5)."""
    if grp_output:
        ctx.obj["output_format"] = grp_output


@backup_group.command("run")
@click.option("--type", "backup_type", default="manual", type=click.Choice(["daily_full", "pre_deploy", "manual"]))
@click.option("--operator", default="cli:backup", help="Operator identifier")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def backup_run_cmd(ctx, backup_type, operator, cmd_output):
    """Trigger immediate backup of open_brain, fleet_ops, globals, and infra_configs."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.backup_run(backup_type=backup_type, operator=operator)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_backup_run_result(data)


@backup_group.command("list")
@click.option("--target", default=None, help="Filter by target (open_brain, fleet_ops, globals, infra_configs)")
@click.option("--limit", default=40, type=int, help="Max entries to show")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def backup_list_cmd(ctx, target, limit, cmd_output):
    """List recorded backups with checksums and off-site sync status."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.backup_list(target=target, limit=limit)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_backups_table(data)


@backup_group.command("verify")
@click.argument("backup_id", required=False, type=int)
@click.option("--operator", default="cli:backup_verify", help="Operator identifier")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def backup_verify_cmd(ctx, backup_id, operator, cmd_output):
    """Verify backup integrity via non-destructive scratch-DB restore."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.backup_verify(backup_id=backup_id, operator=operator)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e.response.text}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_backup_verify_result(data)

    if not data.get("verified"):
        sys.exit(1)


@main.group("deploy", invoke_without_command=True)
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def deploy_group(ctx, grp_output):
    """Fleet deployment & release management commands (Phase 6)."""
    if grp_output:
        ctx.obj["output_format"] = grp_output


@deploy_group.group("release")
def deploy_release_group():
    """Manage release bundles."""


@deploy_release_group.command("upload")
@click.argument("tarball", required=False)
@click.option("--version", "rel_version", default="v1.0.0", help="Release version tag")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def deploy_release_upload(ctx, tarball, rel_version, cmd_output):
    """Build or upload a release bundle and register its SHA-256 checksums."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.register_release(version=rel_version, bundle_path=tarball)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e.response.text}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_releases_table([data])


@deploy_release_group.command("list")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def deploy_release_list(ctx, cmd_output):
    """List registered release bundles."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.list_releases()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_releases_table(data)


@deploy_group.command("status")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def deploy_status_cmd(ctx, cmd_output):
    """Fleet deployment overview (replaces update-fleet.sh --status)."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.deploy_status()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_deploy_status(data)


@deploy_group.command("version")
@click.option("--version", "image_version", required=True, help="Target Agent Zero image tag (e.g. v2.14)")
@click.option("--instances", default="2", help="Comma-separated instance numbers (e.g. 2,3)")
@click.option("--skip-restart", is_flag=True, help="Update docker-compose.yml only without recreating container")
@click.option("--force", is_flag=True, help="Force recreate even if already at target version")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def deploy_version_cmd(ctx, image_version, instances, skip_restart, force, cmd_output):
    """Update Agent Zero Docker image version for specified instance(s)."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    inst_list = [f"agent0-{x.strip()}" if not x.strip().startswith("agent0-") else x.strip() for x in instances.split(",") if x.strip()]
    results = []
    for aname in inst_list:
        try:
            res = client.deploy_version(
                agent_name=aname,
                image_version=image_version,
                skip_restart=skip_restart,
                force=force,
            )
            results.append(res)
            if fmt != "json":
                console.print(
                    f"[cyan]{aname}[/cyan]: {res['previous_version']} -> {res['target_version']} "
                    f"(status=[green]{res['status']}[/green], health={'PASS' if res['health_passed'] else 'WARN'})"
                )
        except httpx.HTTPStatusError as e:
            console.print(f"[red]{aname}: {e.response.text}[/red]")
            sys.exit(1)
    if fmt == "json":
        print_json(results)


@deploy_group.command("agent")
@click.argument("agent_name")
@click.option("--release", "rel_version", required=True, help="Release version to deploy (e.g. v1.0.0)")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def deploy_agent_cmd(ctx, agent_name, rel_version, cmd_output):
    """Deploy a registered release bundle to a single agent."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.deploy_release(agent_name=agent_name, version=rel_version)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e.response.text}[/red]")
        sys.exit(1)
    except httpx.ConnectError:
        console.print("[red]Cannot connect to am-ctl server[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_deploy_result(data)


# Also register agent0-1..agent0-5 as direct subcommands under `am-ctl deploy` so
# `am-ctl deploy agent0-3 --release v1.0` works directly as specified in the gate doc.
for _idx in range(1, 6):
    _aname = f"agent0-{_idx}"

    def _make_deploy_agent_subcmd(fixed_name: str):
        @deploy_group.command(fixed_name, hidden=True)
        @click.option("--release", "rel_version", required=True, help="Release version to deploy")
        @click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None)
        @click.pass_context
        def _sub(ctx, rel_version, cmd_output):
            ctx.invoke(deploy_agent_cmd, agent_name=fixed_name, rel_version=rel_version, cmd_output=cmd_output)

    _make_deploy_agent_subcmd(_aname)


@main.group("models", invoke_without_command=True)
@click.option("--output", "grp_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def models_group(ctx, grp_output):
    """LLM model configuration commands (Phase 7 -- replaces fleet-models.sh)."""
    if grp_output:
        ctx.obj["output_format"] = grp_output
    if ctx.invoked_subcommand is None:
        client = get_client(ctx)
        fmt = grp_output or ctx.obj["output_format"]
        try:
            data = client.list_fleet_models()
        except httpx.ConnectError:
            console.print("[red]Cannot connect to am-ctl server[/red]")
            sys.exit(1)
        if fmt == "json":
            print_json(data)
        else:
            print_fleet_models_table(data)


@models_group.command("list")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def models_list_cmd(ctx, cmd_output):
    """Show fleet-wide model matrix."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    data = client.list_fleet_models()
    if fmt == "json":
        print_json(data)
    else:
        print_fleet_models_table(data)


@models_group.command("show")
@click.argument("agent_name")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def models_show_cmd(ctx, agent_name, cmd_output):
    """Show per-agent model detail."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.get_agent_models(agent_name)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e.response.text}[/red]")
        sys.exit(1)
    if fmt == "json":
        print_json(data)
    else:
        print_agent_model_detail(data)


for _idx in range(1, 6):
    _aname = f"agent0-{_idx}"

    def _make_models_agent_subcmd(fixed_name: str):
        @models_group.command(fixed_name, hidden=True)
        @click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None)
        @click.pass_context
        def _sub(ctx, cmd_output):
            ctx.invoke(models_show_cmd, agent_name=fixed_name, cmd_output=cmd_output)

    _make_models_agent_subcmd(_aname)


@models_group.command("set")
@click.argument("agent_name")
@click.option("--chat-model", default=None, help="Chat model (provider/model-name)")
@click.option("--utility-model", default=None, help="Utility model (provider/model-name)")
@click.option("--embedding-model", default=None, help="Embedding model (provider/model-name)")
@click.option("--preset", default=None, help="Active preset name (e.g. Default, Efficiency, Power)")
@click.option("--operator", default="cli:models", help="Operator identifier")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def models_set_cmd(ctx, agent_name, chat_model, utility_model, embedding_model, preset, operator, cmd_output):
    """Set model configuration or active preset for an agent."""
    if not any([chat_model, utility_model, embedding_model, preset]):
        console.print("[red]Specify at least one of --chat-model, --utility-model, --embedding-model, or --preset[/red]")
        sys.exit(1)
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    try:
        data = client.set_agent_models(
            agent_name=agent_name,
            chat_model=chat_model,
            utility_model=utility_model,
            embedding_model=embedding_model,
            preset=preset,
            operator=operator,
        )
    except httpx.HTTPStatusError as e:
        console.print(f"[red]{e.response.text}[/red]")
        sys.exit(1)

    if fmt == "json":
        print_json(data)
    else:
        print_agent_model_detail(data)


@models_group.command("diagnose")
@click.option("--output", "cmd_output", type=click.Choice(["table", "json"]), default=None, help="Output format")
@click.pass_context
def models_diagnose_cmd(ctx, cmd_output):
    """Check model config & API key availability across the fleet."""
    client = get_client(ctx)
    fmt = cmd_output or ctx.obj["output_format"]
    data = client.diagnose_models()
    if fmt == "json":
        print_json(data)
    else:
        print_models_diagnose(data)


if __name__ == "__main__":
    main()
