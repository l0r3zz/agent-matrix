"""FastAPI application for am-ctl server."""

import asyncio
from contextlib import asynccontextmanager
import logging

import uvicorn
from fastapi import FastAPI

from amctl import __version__
from amctl.config import settings
from amctl.routers.agents import router as agents_router
from amctl.routers.backups import router as backups_router
from amctl.routers.credentials import router as credentials_router
from amctl.routers.deploy import router as deploy_router
from amctl.routers.health import router as health_router
from amctl.routers.models import router as models_router
from amctl.routers.reconcile import router as reconcile_router
from amctl.services.health_engine import background_health_loop

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    if settings.enable_background_monitor:
        task = asyncio.create_task(background_health_loop())
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="am-ctl",
    description="Agent Matrix fleet management control plane",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(agents_router)
app.include_router(health_router)
app.include_router(credentials_router)
app.include_router(reconcile_router)
app.include_router(backups_router)
app.include_router(deploy_router)
app.include_router(models_router)


@app.get("/api/v1/health")
async def health():
    """Server health check (no auth required)."""
    return {"status": "ok", "version": __version__}


def run():
    """Entry point for am-ctl-server command."""
    uvicorn.run(
        "amctl.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    run()
