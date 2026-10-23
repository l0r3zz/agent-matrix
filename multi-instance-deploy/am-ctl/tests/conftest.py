"""Pytest fixtures for am-ctl unit and integration tests."""

from collections.abc import AsyncGenerator
import os

# Disable background health loop during tests before importing app
os.environ["AMCTL_ENABLE_BACKGROUND_MONITOR"] = "false"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import BigInteger, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from amctl.app import app


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"
from amctl.config import settings
from amctl.db import get_session
from amctl.models import (
    Agent,
    AlertRule,
    Base,
    CredentialFingerprint,
    RequiredRoom,
    TrustedSender,
)

settings.enable_background_monitor = False
API_HEADERS = {"X-API-Key": settings.api_key}


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated in-memory SQLite async session seeded with a baseline fleet."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        # Seed alert rules
        rules = [
            AlertRule(check_type="matrix_auth", classification="terminal_config", action="stop_and_alert", max_retries=0, cooldown_secs=300),
            AlertRule(check_type="identity", classification="terminal_config", action="stop_and_alert", max_retries=0, cooldown_secs=300),
            AlertRule(check_type="a0_auth", classification="terminal_config", action="stop_and_alert", max_retries=0, cooldown_secs=300),
            AlertRule(check_type="membership", classification="repairable", action="auto_repair", max_retries=1, cooldown_secs=300),
            AlertRule(check_type="mcp", classification="restartable", action="restart", max_retries=2, cooldown_secs=60),
            AlertRule(check_type="process", classification="restartable", action="restart", max_retries=2, cooldown_secs=60),
            AlertRule(check_type="sync_cursor", classification="restartable", action="restart", max_retries=2, cooldown_secs=60),
            AlertRule(check_type="federation", classification="transient", action="log_only", max_retries=0, cooldown_secs=300),
        ]
        session.add_all(rules)

        # Seed two agents (agent0-1 and agent0-2)
        for idx in (1, 2):
            ag = Agent(
                instance_num=idx,
                name=f"agent0-{idx}",
                matrix_user_id=f"@agent0-{idx}:agent0-{idx}-mhs.cybertribe.com",
                homeserver_fqdn=f"agent0-{idx}-mhs.cybertribe.com",
                homeserver_url=f"https://172.23.89.{idx}:8448",
                agent_zero_endpoint=f"http://172.23.88.{idx}:80",
                status="active",
                bot_runtime="rust",
                release_version="v1.2.0",
            )
            session.add(ag)
            await session.flush()
            session.add(RequiredRoom(agent_id=ag.id, room_id="!gahcrWFWAUJQPPkuQy:v-site.net", room_name="#general:v-site.net"))
            session.add(CredentialFingerprint(agent_id=ag.id, domain="a0_api_key", fingerprint=f"fp000000000{idx}"))

        session.add(TrustedSender(matrix_user_id="@l0r3zz:v-site.net", trust_level="operator"))
        session.add(TrustedSender(matrix_user_id="@admin:v-site.net", trust_level="admin"))
        await session.commit()

        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient wired to the FastAPI app with overridden DB session."""
    async def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
