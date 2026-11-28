"""Open one operational run around a control-plane function."""

import functools
import os

from sqlalchemy.ext.asyncio import AsyncSession

from amctl.oplog.record import finish_run, start_run, write_stage


def _disabled() -> bool:
    return os.environ.get("AMCTL_OPLOG") == "off"


def _session_from(args, kwargs) -> AsyncSession | None:
    found = kwargs.get("session")
    if isinstance(found, AsyncSession):
        return found
    for arg in args:
        if isinstance(arg, AsyncSession):
            return arg
    return None


def _target_from(args, kwargs, kind: str) -> str | None:
    if kind == "none":
        return None
    if kind == "arg0":
        if args:
            return str(args[0])
        return None
    agent = kwargs.get("agent")
    if agent is not None and hasattr(agent, "name"):
        return agent.name
    for arg in args:
        if hasattr(arg, "name") and hasattr(arg, "instance_num"):
            return arg.name
    return None


def _outcome(result) -> str:
    if getattr(result, "success", True) is False:
        return "failed"
    if getattr(result, "valid", True) is False:
        return "failed"
    return "succeeded"


async def call(session: AsyncSession, *, action: str, target: str | None, actor: str, stage: str, work):
    """Flush a start record, run the work, then finish the run."""
    if _disabled():
        return await work()
    run = await start_run(session, action=action, target=target, actor=actor or "control-plane")
    await write_stage(session, run.run_id, stage, "start", "INFO", f"Starting {stage}.")
    try:
        result = await work()
    except Exception as exc:
        cause = str(exc).strip() or "The stage failed."
        await write_stage(
            session,
            run.run_id,
            stage,
            "finish",
            "ERROR",
            cause,
            cause=cause,
        )
        await finish_run(session, run.run_id, "failed")
        raise
    outcome = _outcome(result)
    if outcome == "failed":
        await write_stage(
            session,
            run.run_id,
            stage,
            "finish",
            "ERROR",
            f"{stage} failed.",
            cause=f"{stage} failed.",
        )
    else:
        await write_stage(session, run.run_id, stage, "finish", "INFO", f"{stage} finished.")
    await finish_run(session, run.run_id, outcome)
    return result


def tracked(*, action: str, stage: str, target: str = "agent"):
    """Record one run each time the wrapped coroutine is called."""

    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            if _disabled():
                return await fn(*args, **kwargs)
            session = _session_from(args, kwargs)
            name = _target_from(args, kwargs, target)
            actor = kwargs.get("operator") or "control-plane"

            async def work():
                return await fn(*args, **kwargs)

            if session is None:
                from amctl.db import async_session

                async with async_session() as opened:
                    return await call(
                        opened,
                        action=action,
                        target=name,
                        actor=actor,
                        stage=stage,
                        work=work,
                    )
            return await call(
                session,
                action=action,
                target=name,
                actor=actor,
                stage=stage,
                work=work,
            )

        wrapper._oplog_action = action
        return wrapper

    return deco
