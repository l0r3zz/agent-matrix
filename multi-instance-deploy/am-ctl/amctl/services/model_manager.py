"""Model management service (Phase 7).

Absorbs fleet-models.sh and upgrades it for Agent Zero v2.14's preset-based
architecture (/a0/usr/plugins/_model_config/config.json + presets.yaml),
persists state in the `model_configs` DB table, and logs all mutations to `audit_log`.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amctl.models.agent import Agent
from amctl.models.audit import AuditLog
from amctl.models.model_config import ModelConfig
from amctl.schemas.model_config import (
    AgentModelConfigResponse,
    FleetModelsDiagnoseResponse,
    FleetModelsResponse,
    ModelDiagnoseItem,
)
from amctl.services.docker import _run

logger = logging.getLogger(__name__)

INSTANCE_BASE = Path("/opt/agent-zero")

READ_MODELS_PY = """
import json, yaml
cfg = json.load(open('/a0/usr/plugins/_model_config/config.json'))
sel = cfg.get('model_preset', 'Default')
presets = yaml.safe_load(open('/a0/usr/plugins/_model_config/presets.yaml')) or []
names = [p.get('name') for p in presets if isinstance(p, dict) and p.get('name')]
default_p = next((p for p in presets if p.get('name') == 'Default'), {})
active_p = next((p for p in presets if p.get('name') == sel), default_p)

def fmt(slot):
    s = active_p.get(slot) or default_p.get(slot) or {}
    prov = s.get('provider', '')
    nm = s.get('name', '')
    return f'{prov}/{nm}' if prov and nm else 'unknown'

chat_s = active_p.get('chat') or default_p.get('chat') or {}
print(json.dumps({
    'selected_preset': sel,
    'available_presets': names,
    'chat_model': fmt('chat'),
    'utility_model': fmt('utility'),
    'embedding_model': fmt('embedding'),
    'ctx_length': int(chat_s.get('ctx_length', 0) or 0),
    'vision': bool(chat_s.get('vision', False))
}))
"""


def _get_agent_profile(agent_name: str) -> str:
    env_file = INSTANCE_BASE / agent_name / ".env"
    if not env_file.is_file():
        return "agent0"
    profile = "agent0"
    for line in env_file.read_text().splitlines():
        if line.startswith("A0_SET_agent_profile="):
            val = line.split("=", 1)[1].strip()
            if val and "{{" not in val:
                profile = val.split()[-1]
    return profile


def _check_agent_api_keys(agent_name: str) -> dict[str, bool]:
    """Check API keys configured in host instance .env and container /a0/usr/.env."""
    keys = {"openrouter": False, "openai": False, "anthropic": False, "google": False}
    for env_path in (
        INSTANCE_BASE / agent_name / ".env",
        INSTANCE_BASE / agent_name / "usr" / ".env",
    ):
        if not env_path.is_file():
            continue
        for line in env_path.read_text().splitlines():
            for prov in list(keys.keys()):
                prefix = f"API_KEY_{prov.upper()}="
                if line.startswith(prefix):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and val != "None":
                        keys[prov] = True
    return keys


async def _read_live_agent_models(agent_name: str) -> dict:
    """Read the resolved active preset and model slots (chat, utility, embedding)
    from /a0/usr/plugins/_model_config/config.json and presets.yaml inside the container.
    """
    rc, out = await _run([
        "docker", "exec", agent_name,
        "/opt/venv-a0/bin/python", "-c", READ_MODELS_PY,
    ], timeout=15.0)
    if rc == 0 and out.strip():
        try:
            return json.loads(out.strip().splitlines()[-1])
        except json.JSONDecodeError:
            pass
    return {
        "selected_preset": "unknown",
        "available_presets": [],
        "chat_model": "unknown",
        "utility_model": "unknown",
        "embedding_model": "unknown",
        "ctx_length": 0,
        "vision": False,
    }


async def _sync_agent_models_to_db(session: AsyncSession, agent: Agent, live: dict) -> datetime:
    """Upsert chat, utility, embedding, and preset rows into model_configs table."""
    now = datetime.now(timezone.utc)
    res = await session.execute(select(ModelConfig).where(ModelConfig.agent_id == agent.id))
    existing = {m.config_type: m for m in res.scalars().all()}

    slots = {
        "chat": live["chat_model"],
        "utility": live["utility_model"],
        "embedding": live["embedding_model"],
        "preset": live["selected_preset"],
    }
    for ctype, mname in slots.items():
        if ctype in existing:
            if existing[ctype].model_name != mname:
                existing[ctype].model_name = mname
                existing[ctype].updated_at = now
        else:
            session.add(
                ModelConfig(
                    agent_id=agent.id,
                    config_type=ctype,
                    model_name=mname,
                    updated_at=now,
                )
            )
    await session.commit()
    return now


async def get_agent_model_config(session: AsyncSession, agent: Agent) -> AgentModelConfigResponse:
    """Read live model configuration for a single agent and sync to model_configs table."""
    live = await _read_live_agent_models(agent.name)
    updated_at = await _sync_agent_models_to_db(session, agent, live)
    return AgentModelConfigResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        instance_num=agent.instance_num,
        profile=_get_agent_profile(agent.name),
        selected_preset=live["selected_preset"],
        chat_model=live["chat_model"],
        utility_model=live["utility_model"],
        embedding_model=live["embedding_model"],
        ctx_length=live["ctx_length"],
        vision=live["vision"],
        available_presets=live["available_presets"],
        updated_at=updated_at,
    )


async def get_fleet_models(session: AsyncSession) -> FleetModelsResponse:
    """Return fleet-wide model matrix across all agents."""
    res = await session.execute(select(Agent).order_by(Agent.instance_num))
    agents = res.scalars().all()

    items: list[AgentModelConfigResponse] = []
    online = 0
    for a in agents:
        item = await get_agent_model_config(session, a)
        if item.chat_model != "unknown":
            online += 1
        items.append(item)

    return FleetModelsResponse(
        total_agents=len(items),
        online_agents=online,
        agents=items,
    )


def _validate_provider_model(model_id: str | None, label: str) -> tuple[str, str] | None:
    if not model_id:
        return None
    if "/" not in model_id:
        raise ValueError(f"Invalid {label} '{model_id}': must be in 'provider/model-name' format")
    provider, name = model_id.split("/", 1)
    if not provider or not name:
        raise ValueError(f"Invalid {label} '{model_id}': must be in 'provider/model-name' format")
    return provider, name


def _update_host_env_model(agent_name: str, env_key: str, value: str) -> None:
    env_file = INSTANCE_BASE / agent_name / ".env"
    if not env_file.is_file():
        return
    lines = env_file.read_text().splitlines()
    updated = False
    new_lines = []
    for ln in lines:
        if re.match(rf"^\s*{re.escape(env_key)}=", ln):
            if not updated:
                new_lines.append(f"{env_key}={value}")
                updated = True
            else:
                new_lines.append(f"# {ln}")
        else:
            new_lines.append(ln)
    if not updated:
        new_lines.append(f"{env_key}={value}")
    env_file.write_text("\n".join(new_lines) + "\n")


async def set_agent_model_config(
    session: AsyncSession,
    agent: Agent,
    chat_model: str | None = None,
    utility_model: str | None = None,
    embedding_model: str | None = None,
    preset: str | None = None,
    operator: str = "cli:models",
) -> AgentModelConfigResponse:
    """Update an agent's active preset and/or model slots in presets.yaml + config.json
    and host .env, persist in model_configs, and write to audit_log.
    """
    chat_parsed = _validate_provider_model(chat_model, "chat_model")
    util_parsed = _validate_provider_model(utility_model, "utility_model")
    embed_parsed = _validate_provider_model(embedding_model, "embedding_model")

    before = await _read_live_agent_models(agent.name)

    updates_payload = {
        "preset": preset,
        "chat": chat_parsed,
        "utility": util_parsed,
        "embedding": embed_parsed,
    }

    rc, out = await _run([
        "docker", "exec", agent.name,
        "/opt/venv-a0/bin/python", "-c",
        "import json, sys, yaml\n"
        f"upd = json.loads({json.dumps(json.dumps(updates_payload))})\n"
        "cfg_path = '/a0/usr/plugins/_model_config/config.json'\n"
        "pre_path = '/a0/usr/plugins/_model_config/presets.yaml'\n"
        "cfg = json.load(open(cfg_path))\n"
        "presets = yaml.safe_load(open(pre_path)) or []\n"
        "target_preset = upd.get('preset') or cfg.get('model_preset', 'Default')\n"
        "p_obj = next((p for p in presets if isinstance(p, dict) and p.get('name') == target_preset), None)\n"
        "if p_obj is None:\n"
        "    print(f'ERR:Preset {target_preset} not found')\n"
        "    sys.exit(1)\n"
        "cfg['model_preset'] = target_preset\n"
        "for slot in ('chat', 'utility', 'embedding'):\n"
        "    val = upd.get(slot)\n"
        "    if val:\n"
        "        prov, nm = val[0], val[1]\n"
        "        if slot not in p_obj or not isinstance(p_obj[slot], dict):\n"
        "            p_obj[slot] = {}\n"
        "        p_obj[slot]['provider'] = prov\n"
        "        p_obj[slot]['name'] = nm\n"
        "json.dump(cfg, open(cfg_path, 'w'), indent=2)\n"
        "yaml.safe_dump(presets, open(pre_path, 'w'), sort_keys=False, allow_unicode=True)\n"
        "print('OK')\n",
    ], timeout=15.0)

    if rc != 0 or "OK" not in out:
        raise ValueError(f"Failed to update model config on {agent.name}: {out}")

    if chat_model:
        _update_host_env_model(agent.name, "A0_SET_chat_model", chat_model)
    if utility_model:
        _update_host_env_model(agent.name, "A0_SET_utility_model", utility_model)
    if embedding_model:
        _update_host_env_model(agent.name, "A0_SET_embedding_model", embedding_model)

    after = await _read_live_agent_models(agent.name)
    updated_at = await _sync_agent_models_to_db(session, agent, after)

    changes = {}
    for k in ("selected_preset", "chat_model", "utility_model", "embedding_model"):
        if before.get(k) != after.get(k):
            changes[k] = {"old": before.get(k), "new": after.get(k)}

    session.add(
        AuditLog(
            agent_id=agent.id,
            action="model_config_update",
            detail={
                "changes": changes,
                "requested": {
                    k: v
                    for k, v in {
                        "preset": preset,
                        "chat_model": chat_model,
                        "utility_model": utility_model,
                        "embedding_model": embedding_model,
                    }.items()
                    if v is not None
                },
            },
            operator=operator,
        )
    )
    await session.commit()

    return AgentModelConfigResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        instance_num=agent.instance_num,
        profile=_get_agent_profile(agent.name),
        selected_preset=after["selected_preset"],
        chat_model=after["chat_model"],
        utility_model=after["utility_model"],
        embedding_model=after["embedding_model"],
        ctx_length=after["ctx_length"],
        vision=after["vision"],
        available_presets=after["available_presets"],
        updated_at=updated_at,
    )


async def diagnose_fleet_models(session: AsyncSession) -> FleetModelsDiagnoseResponse:
    """Run model configuration & provider API key diagnostics across all agents."""
    res = await session.execute(select(Agent).order_by(Agent.instance_num))
    agents = res.scalars().all()

    items: list[ModelDiagnoseItem] = []
    overall = "pass"

    for a in agents:
        live = await _read_live_agent_models(a.name)
        db_res = await session.execute(select(ModelConfig).where(ModelConfig.agent_id == a.id))
        db_map = {m.config_type: m.model_name for m in db_res.scalars().all()}

        api_keys = _check_agent_api_keys(a.name)

        issues: list[str] = []
        cfg_ok = live["selected_preset"] != "unknown"
        presets_ok = len(live["available_presets"]) > 0 and live["chat_model"] != "unknown"

        if not cfg_ok:
            issues.append("config.json missing or unreadable")
        if not presets_ok:
            issues.append("presets.yaml missing or active preset unresolved")

        db_synced = (
            db_map.get("chat") == live["chat_model"]
            and db_map.get("utility") == live["utility_model"]
            and db_map.get("embedding") == live["embedding_model"]
        )
        if not db_synced:
            await _sync_agent_models_to_db(session, a, live)
            db_synced = True

        chat_prov = live["chat_model"].split("/", 1)[0] if "/" in live["chat_model"] else ""
        if chat_prov in api_keys and not api_keys[chat_prov]:
            issues.append(f"Missing API key for active chat provider '{chat_prov}'")

        st = "pass" if not issues else ("fail" if not presets_ok else "warn")
        if st == "fail":
            overall = "fail"
        elif st == "warn" and overall == "pass":
            overall = "warn"

        items.append(
            ModelDiagnoseItem(
                agent_name=a.name,
                preset=live["selected_preset"],
                config_json_valid=cfg_ok,
                presets_yaml_valid=presets_ok,
                db_synced=db_synced,
                api_keys_present=api_keys,
                status=st,
                issues=issues,
            )
        )

    return FleetModelsDiagnoseResponse(
        overall_status=overall,
        agents=items,
    )
