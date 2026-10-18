"""Output formatting for the CLI."""

import json

from rich.console import Console
from rich.table import Table

console = Console()

CHECK_COLUMNS = [
    "matrix_auth",
    "identity",
    "membership",
    "a0_auth",
    "mcp",
    "process",
    "federation",
    "sync_cursor",
]


def _fmt_status(status: str) -> str:
    if status == "pass":
        return "[green]PASS[/green]"
    if status == "warn":
        return "[yellow]WARN[/yellow]"
    if status == "fail":
        return "[red]FAIL[/red]"
    return f"[dim]{status.upper()}[/dim]"


def print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


def print_agents_table(agents: list[dict]):
    """Print agents as a rich table."""
    table = Table(title="Agent Registry")
    table.add_column("Name", style="cyan")
    table.add_column("Instance", justify="right")
    table.add_column("Matrix ID", style="green")
    table.add_column("Runtime")
    table.add_column("Status")
    table.add_column("Release")

    for a in agents:
        status_style = "green" if a["status"] == "active" else "yellow"
        table.add_row(
            a["name"],
            str(a["instance_num"]),
            a["matrix_user_id"],
            a["bot_runtime"],
            f"[{status_style}]{a['status']}[/{status_style}]",
            a.get("release_version") or "-",
        )

    console.print(table)


def print_agent_status(data: dict):
    """Print detailed agent status."""
    agent = data["agent"]
    containers = data.get("containers", [])
    processes = data.get("processes")
    identity = data.get("identity")

    console.print(f"\n[bold cyan]{agent['name']}[/bold cyan]  (instance {agent['instance_num']})")
    console.print(f"  Matrix ID:  {agent['matrix_user_id']}")
    console.print(f"  Homeserver: {agent['homeserver_fqdn']}")
    console.print(f"  Runtime:    {agent['bot_runtime']}")
    console.print(f"  Status:     {agent['status']}")
    console.print(f"  Release:    {agent.get('release_version') or '-'}")

    # Containers
    console.print("\n  [bold]Containers:[/bold]")
    for c in containers:
        icon = "[green]UP[/green]" if c["running"] else "[red]DOWN[/red]"
        uptime = f"  ({c['uptime']})" if c.get("uptime") else ""
        console.print(f"    {c['name']:30s} {icon}{uptime}")

    # Processes
    if processes:
        console.print("\n  [bold]Processes:[/bold]")
        bot_icon = "[green]OK[/green]" if processes["bot_count"] == 1 else f"[red]{processes['bot_count']}[/red]"
        console.print(f"    Bot:         {bot_icon}  (runtime: {processes.get('bot_runtime') or 'none'})")
        mcp_icon = "[green]OK[/green]" if processes["mcp_running"] else "[red]DOWN[/red]"
        console.print(f"    MCP:         {mcp_icon}")
        wd_icon = "[green]OK[/green]" if processes["watchdog_running"] else "[yellow]OFF[/yellow]"
        console.print(f"    Watchdog:    {wd_icon}")
        sup_icon = "[green]OK[/green]" if processes["supervisord_running"] else "[red]DOWN[/red]"
        console.print(f"    Supervisord: {sup_icon}")

    # Identity
    if identity:
        console.print("\n  [bold]Matrix Identity:[/bold]")
        if identity.get("user_id"):
            match = identity["user_id"] == agent["matrix_user_id"]
            match_icon = "[green]MATCH[/green]" if match else "[red]MISMATCH[/red]"
            console.print(f"    /whoami:  {identity['user_id']}  {match_icon}")
        elif identity.get("error"):
            console.print(f"    /whoami:  [red]ERROR: {identity['error']}[/red]")

    # Credentials
    creds = agent.get("credential_fingerprints", [])
    if creds:
        console.print("\n  [bold]Credential Fingerprints:[/bold]")
        for c in creds:
            console.print(f"    {c['domain']:15s}  {c['fingerprint']}")

    # Required rooms
    rooms = agent.get("required_rooms", [])
    if rooms:
        console.print("\n  [bold]Required Rooms:[/bold]")
        for r in rooms:
            console.print(f"    {r.get('room_name') or 'unnamed':20s}  {r['room_id']}")

    console.print()


def print_fleet_summary(data: dict):
    """Print fleet-wide summary."""
    console.print(f"\n[bold]Fleet Summary[/bold]")
    console.print(f"  Total agents:       {data['total_agents']}")
    console.print(f"  Active:             {data['active']}")
    console.print(f"  Containers running: {data['containers_running']}")
    console.print(f"  Containers down:    {data['containers_down']}")
    console.print()

    if data.get("agents"):
        print_agents_table(data["agents"])


def print_fleet_health_matrix(data: dict):
    """Print fleet-wide health matrix table."""
    console.print(f"\n[bold]Fleet Health Matrix[/bold]")
    console.print(
        f"  Total: {data['total_agents']}  |  "
        f"[green]Healthy: {data['healthy_agents']}[/green]  |  "
        f"[yellow]Degraded: {data['degraded_agents']}[/yellow]  |  "
        f"[red]Failing: {data['failing_agents']}[/red]  |  "
        f"Open Alerts: {data['open_alerts']}"
    )
    if data.get("last_monitor_run"):
        console.print(f"  Last Check: {data['last_monitor_run']}")
    console.print()

    table = Table(title="Agent Health Checks")
    table.add_column("Agent", style="cyan")
    table.add_column("Overall", justify="center")
    for col in CHECK_COLUMNS:
        table.add_column(col, justify="center")

    for agent in data.get("agents", []):
        checks = agent.get("checks", {})
        row = [
            agent["agent_name"],
            _fmt_status(agent["overall_status"]),
        ]
        for col in CHECK_COLUMNS:
            chk = checks.get(col)
            row.append(_fmt_status(chk["status"]) if chk else "[dim]-[/dim]")
        table.add_row(*row)

    console.print(table)


def print_agent_health_detail(data: dict):
    """Print detailed health check state for one agent."""
    console.print(
        f"\n[bold cyan]{data['agent_name']}[/bold cyan]  "
        f"Overall: {_fmt_status(data['overall_status'])}\n"
    )
    table = Table(title=f"Health Checks -- {data['agent_name']}")
    table.add_column("Check Type", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Fails", justify="right")
    table.add_column("Since")
    table.add_column("Last Check")
    table.add_column("Detail")

    checks = data.get("checks", {})
    for col in CHECK_COLUMNS:
        chk = checks.get(col)
        if not chk:
            table.add_row(col, "[dim]-[/dim]", "-", "-", "-", "-")
            continue
        detail_str = json.dumps(chk.get("detail") or {})
        if len(detail_str) > 70:
            detail_str = detail_str[:67] + "..."
        table.add_row(
            col,
            _fmt_status(chk["status"]),
            str(chk.get("fail_count", 0)),
            str(chk.get("since", ""))[:19],
            str(chk.get("last_check", ""))[:19],
            detail_str,
        )
    console.print(table)


def print_alerts_table(alerts: list[dict]):
    """Print active or historical alerts."""
    if not alerts:
        console.print("[green]No alerts matching filter.[/green]")
        return

    table = Table(title="Alerts")
    table.add_column("ID", justify="right")
    table.add_column("Agent", style="cyan")
    table.add_column("Check")
    table.add_column("Class")
    table.add_column("Status")
    table.add_column("Created")
    table.add_column("Message")

    for a in alerts:
        st_color = "red" if a["status"] == "open" else ("yellow" if a["status"] == "acked" else "green")
        table.add_row(
            str(a["id"]),
            a.get("agent_name") or str(a["agent_id"]),
            a["check_type"],
            a["classification"],
            f"[{st_color}]{a['status']}[/{st_color}]",
            str(a.get("created_at", ""))[:19],
            a["message"],
        )
    console.print(table)


def print_credential_verify(data: dict):
    """Print credential verification result."""
    valid_icon = "[green]VALID[/green]" if data["valid"] else "[red]INVALID[/red]"
    console.print(f"\n[bold cyan]{data['agent_name']}[/bold cyan]  Credential Verification: {valid_icon}")
    console.print(f"  Canonical (create_auth_token):  {data.get('canonical_fingerprint') or '-'}")
    console.print(f"  Deployed (bot runtime):         {data.get('deployed_fingerprint') or '-'}")
    console.print(f"  Registry (fleet_ops DB):        {data.get('registry_fingerprint') or '-'}")
    console.print(f"  Delivery Source:                {data.get('secret_file_source')}")
    console.print(f"  Agent Zero Auth Probe:          {_fmt_status(data.get('a0_probe_status', 'fail'))}")
    console.print()


def print_credential_collisions(data: dict):
    """Print cross-fleet credential fingerprint collision report."""
    if not data.get("has_collisions"):
        console.print("[green]No cross-fleet credential fingerprint collisions detected.[/green]")
        return

    console.print("[bold red]COLLISION DETECTED: Multiple agents share the same credential fingerprint![/bold red]\n")
    table = Table(title="Credential Fingerprint Collisions")
    table.add_column("Domain", style="cyan")
    table.add_column("Fingerprint", style="red")
    table.add_column("Colliding Agents", style="yellow")

    for c in data.get("collisions", []):
        table.add_row(c["domain"], c["fingerprint"], ", ".join(c["agents"]))
    console.print(table)


DRIFT_COLUMNS = [
    "identity",
    "membership",
    "credential",
    "secret_delivery",
    "process",
    "artifact_hash",
]


def _fmt_drift(status: str) -> str:
    if status == "clean":
        return "[green]CLEAN[/green]"
    return "[yellow]DRIFT[/yellow]"


def print_fleet_drift_report(data: dict):
    """Print fleet-wide reconciliation drift check report."""
    console.print("\n[bold]Fleet Reconciliation Drift Report (read-only)[/bold]")
    console.print(
        f"  Total: {data['total_agents']}  |  "
        f"[green]Clean: {data['clean_agents']}[/green]  |  "
        f"[yellow]Drifted: {data['drifted_agents']}[/yellow]  |  "
        f"Collisions: {'[red]YES[/red]' if data.get('has_fingerprint_collisions') else '[green]NONE[/green]'}"
    )
    console.print()

    table = Table(title="Fleet Drift Matrix")
    table.add_column("Agent", style="cyan")
    table.add_column("Overall", justify="center")
    for col in DRIFT_COLUMNS:
        table.add_column(col, justify="center")

    for agent in data.get("agents", []):
        by_type = {c["drift_type"]: c for c in agent.get("checks", [])}
        overall = "[green]CLEAN[/green]" if agent["clean"] else f"[yellow]DRIFT ({agent['drift_count']})[/yellow]"
        row = [agent["agent_name"], overall]
        for col in DRIFT_COLUMNS:
            chk = by_type.get(col)
            row.append(_fmt_drift(chk["status"]) if chk else "[dim]-[/dim]")
        table.add_row(*row)

    console.print(table)


def print_agent_drift_report(data: dict):
    """Print detailed per-agent drift report."""
    overall = "[green]CLEAN[/green]" if data["clean"] else f"[yellow]DRIFT ({data['drift_count']})[/yellow]"
    console.print(f"\n[bold cyan]{data['agent_name']}[/bold cyan]  Reconcile Check: {overall}\n")

    table = Table(title=f"Drift Checks -- {data['agent_name']}")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Expected")
    table.add_column("Actual")

    for chk in data.get("checks", []):
        exp_str = json.dumps(chk["expected"]) if isinstance(chk["expected"], (dict, list)) else str(chk["expected"] or "-")
        act_str = json.dumps(chk["actual"]) if isinstance(chk["actual"], (dict, list)) else str(chk["actual"] or "-")
        if len(exp_str) > 52:
            exp_str = exp_str[:49] + "..."
        if len(act_str) > 52:
            act_str = act_str[:49] + "..."
        table.add_row(
            chk["drift_type"],
            _fmt_drift(chk["status"]),
            exp_str,
            act_str,
        )
    console.print(table)


def print_reconcile_plan(data: dict):
    """Print proposed remediation actions for an agent."""
    print_agent_drift_report(data["drift_report"])
    actions = data.get("actions", [])
    if not actions:
        console.print(f"\n[green]No actions required -- {data['agent_name']} is completely in sync.[/green]\n")
        return

    console.print(f"\n[bold yellow]Proposed Remediation Plan ({len(actions)} steps, read-only preview):[/bold yellow]")
    for act in actions:
        console.print(f"  [bold]{act['step']}. \\[{act['action_type']}][/bold] ({act['target']})")
        console.print(f"     {act['description']}")
    console.print()


def print_reconcile_apply(data: dict):
    """Print reconciliation apply result."""
    if data.get("noop"):
        console.print(f"\n[green]{data['agent_name']} is already CLEAN -- no-op (zero mutations applied).[/green]\n")
        return

    status_icon = "[bold green]SUCCESS (CLEAN)[/bold green]" if data.get("success") else "[bold red]INCOMPLETE / FAILED[/bold red]"
    console.print(f"\n[bold cyan]{data['agent_name']}[/bold cyan]  Reconcile Apply: {status_icon}")
    if data.get("snapshot_dir"):
        console.print(f"  Snapshot: {data['snapshot_dir']}")

    console.print("\n  [bold]Actions Executed:[/bold]")
    for act in data.get("actions_executed", []):
        st_color = "green" if act["status"] == "applied" else ("yellow" if act["status"] == "skipped" else "red")
        console.print(
            f"    {act['step']}. \\[{act['action_type']}] ({act['target']}) -> "
            f"[{st_color}]{act['status'].upper()}[/{st_color}]"
        )

    print_agent_drift_report(data["post_check"])


def print_backup_run_result(data: dict):
    """Print backup suite execution summary."""
    offsite_icon = "[green]SYNCED[/green]" if data.get("offsite_synced") else "[red]FAILED[/red]"
    console.print(f"\n[bold cyan]Backup Suite Complete[/bold cyan]  (type: {data['backup_type']})")
    console.print(f"  Local Dir:      {data['backup_dir']}")
    console.print(f"  Offsite Target: {data['offsite_target']}  ({offsite_icon})")
    if data.get("pruned_dirs"):
        console.print(f"  Pruned Expired: {len(data['pruned_dirs'])} dir(s)")
    console.print()
    print_backups_table(data.get("artifacts", []))


def print_backups_table(backups: list[dict]):
    """Print backup catalog table."""
    if not backups:
        console.print("[yellow]No backups recorded yet.[/yellow]")
        return

    table = Table(title="Backup Catalog")
    table.add_column("ID", justify="right")
    table.add_column("Type")
    table.add_column("Target", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("SHA-256")
    table.add_column("Offsite", justify="center")
    table.add_column("Created")

    for b in backups:
        st = b["status"]
        st_fmt = "[green]VERIFIED[/green]" if st == "verified" else ("[green]SUCCESS[/green]" if st == "success" else "[red]FAILED[/red]")
        off_fmt = "[green]YES[/green]" if b.get("offsite_synced") else "[yellow]NO[/yellow]"
        size_kb = f"{b['size_bytes'] / 1024:.1f} KB"
        table.add_row(
            str(b["id"]),
            b["backup_type"],
            b["target"],
            st_fmt,
            size_kb,
            (b.get("checksum_sha256") or "-")[:12],
            off_fmt,
            str(b.get("created_at", ""))[:19],
        )
    console.print(table)


def print_backup_verify_result(data: dict):
    """Print scratch-DB restore verification result."""
    v_icon = "[bold green]PASSED[/bold green]" if data.get("verified") else "[bold red]FAILED[/bold red]"
    console.print(f"\n[bold cyan]Scratch-DB Restore Verification:[/bold cyan] {v_icon}")
    console.print(
        f"  open_brain (dump #{data.get('open_brain_dump_id')}): "
        f"restored {data['open_brain_restored_thoughts']} / {data['open_brain_live_thoughts']} thoughts "
        f"(HNSW vector index: {'[green]OK[/green]' if data.get('pgvector_index_present') else '[red]MISSING[/red]'})"
    )
    console.print(
        f"  fleet_ops  (dump #{data.get('fleet_ops_dump_id')}): "
        f"restored {data['fleet_ops_restored_agents']} / {data['fleet_ops_live_agents']} agents"
    )
    console.print(
        f"  Scratch DBs Cleaned Up: {'[green]YES[/green]' if data.get('scratch_db_cleaned') else '[red]NO[/red]'}\n"
    )


def print_releases_table(releases: list[dict]):
    """Print registered release bundles."""
    if not releases:
        console.print("[yellow]No releases registered yet.[/yellow]")
        return

    table = Table(title="Release Registry")
    table.add_column("ID", justify="right")
    table.add_column("Version", style="cyan")
    table.add_column("Bundle SHA-256")
    table.add_column("Artifacts")
    table.add_column("Created")

    for r in releases:
        arts = ", ".join(f"{k}:{v[:8]}" for k, v in (r.get("artifact_hashes") or {}).items())
        table.add_row(
            str(r["id"]),
            r["version"],
            (r.get("checksum_sha256") or "")[:16],
            arts,
            str(r.get("created_at", ""))[:19],
        )
    console.print(table)


def print_deploy_result(data: dict):
    """Print single-agent release deployment result."""
    st_icon = "[bold green]SUCCESS[/bold green]" if data.get("status") == "success" else "[bold red]FAILED[/bold red]"
    console.print(f"\n[bold cyan]{data['agent_name']}[/bold cyan]  Deploy Release {data['release_version']}: {st_icon}")
    ps = data.get("preserved_state") or {}
    console.print(f"  Bot .env Preserved:       {'[green]YES[/green]' if ps.get('bot_env_preserved') else '[red]NO[/red]'}")
    console.print(f"  Room Contexts Preserved:  {'[green]YES[/green]' if ps.get('room_contexts_preserved') else '[red]NO[/red]'}")
    console.print(f"  Post-Deploy Health Check: {'[green]PASS[/green]' if data.get('health_passed') else '[red]FAIL[/red]'}")
    console.print(f"  Post-Deploy Drift Check:  {'[green]CLEAN[/green]' if data.get('drift_clean') else '[yellow]DRIFT[/yellow]'}\n")


def print_deploy_status(data: dict):
    """Print fleet deployment overview (absorbs update-fleet.sh --status)."""
    console.print("\n[bold]Fleet Deployment Status[/bold]")
    console.print(
        f"  Total: {data['total_agents']}  |  "
        f"[green]Up: {data['up_agents']}[/green]  |  "
        f"[green]Clean: {data['clean_agents']}[/green]  |  "
        f"Latest Release: {data.get('latest_release') or '-'}\n"
    )

    table = Table(title="Instance Deployment Overview")
    table.add_column("Instance", style="cyan")
    table.add_column("Container", justify="center")
    table.add_column("A0 Version", justify="center")
    table.add_column("Compose Tag", justify="center")
    table.add_column("Release", justify="center")
    table.add_column("Bot", justify="right")
    table.add_column("MCP", justify="center")
    table.add_column("Supervisord", justify="center")
    table.add_column("Reconcile", justify="center")

    for a in data.get("agents", []):
        c_fmt = "[green]up[/green]" if a["container_state"] == "up" else "[red]down[/red]"
        comp_fmt = f"[yellow]{a['compose_a0_version']} ![/yellow]" if a.get("version_drift") else a["compose_a0_version"]
        bot_fmt = f"[green]{a['bot_count']}[/green]" if a["bot_count"] == 1 else f"[yellow]{a['bot_count']}[/yellow]"
        sup_fmt = "[green]OK[/green]" if a.get("supervisord") else "[red]NO[/red]"
        rec_fmt = "[green]CLEAN[/green]" if a.get("reconcile_clean") else "[yellow]DRIFT[/yellow]"
        table.add_row(
            a["agent_name"],
            c_fmt,
            a["running_a0_version"],
            comp_fmt,
            a.get("release_version") or "-",
            bot_fmt,
            a["mcp_status"],
            sup_fmt,
            rec_fmt,
        )
    console.print(table)


def print_fleet_models_table(data: dict):
    """Print fleet-wide LLM model configuration matrix."""
    console.print("\n[bold]Agent-Matrix Fleet -- Model Configuration Matrix[/bold]")
    console.print(f"  Total: {data['total_agents']}  |  [green]Online: {data['online_agents']}[/green]\n")

    table = Table(title="Fleet Model Configurations")
    table.add_column("Agent", style="cyan")
    table.add_column("Profile")
    table.add_column("Preset", style="magenta")
    table.add_column("Chat Model", style="green")
    table.add_column("Utility Model")
    table.add_column("Embedding Model")
    table.add_column("Ctx Len", justify="right")

    for a in data.get("agents", []):
        table.add_row(
            a["agent_name"],
            a["profile"],
            a["selected_preset"],
            a["chat_model"],
            a["utility_model"],
            a["embedding_model"],
            f"{a.get('ctx_length', 0):,}" if a.get("ctx_length") else "-",
        )
    console.print(table)


def print_agent_model_detail(data: dict):
    """Print detailed model config for a single agent."""
    console.print(f"\n[bold cyan]{data['agent_name']}[/bold cyan]  (profile: {data['profile']})")
    console.print(f"  Active Preset:     [magenta]{data['selected_preset']}[/magenta]")
    console.print(f"  Available Presets: {', '.join(data.get('available_presets', []))}")
    console.print(f"  Chat Model:        [green]{data['chat_model']}[/green]")
    console.print(f"  Utility Model:     {data['utility_model']}")
    console.print(f"  Embedding Model:   {data['embedding_model']}")
    console.print(f"  Context Length:    {data.get('ctx_length', 0):,}")
    console.print(f"  Vision Enabled:    {data.get('vision')}\n")


def print_models_diagnose(data: dict):
    """Print model diagnostics table."""
    console.print(f"\n[bold]Fleet Model Diagnostics[/bold]  Overall: {_fmt_status(data['overall_status'])}\n")
    table = Table(title="Model Diagnostics")
    table.add_column("Agent", style="cyan")
    table.add_column("Preset")
    table.add_column("config.json", justify="center")
    table.add_column("presets.yaml", justify="center")
    table.add_column("DB Synced", justify="center")
    table.add_column("API Keys")
    table.add_column("Status", justify="center")

    for a in data.get("agents", []):
        keys_ok = [k for k, v in (a.get("api_keys_present") or {}).items() if v]
        table.add_row(
            a["agent_name"],
            a["preset"],
            "[green]OK[/green]" if a["config_json_valid"] else "[red]ERR[/red]",
            "[green]OK[/green]" if a["presets_yaml_valid"] else "[red]ERR[/red]",
            "[green]OK[/green]" if a["db_synced"] else "[yellow]SYNC[/yellow]",
            ", ".join(keys_ok) or "none",
            _fmt_status(a["status"]),
        )
    console.print(table)
