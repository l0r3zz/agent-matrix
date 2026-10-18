"""Application settings loaded from environment or .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://amctl:amctl-fleet-2026@172.23.90.1:5432/fleet_ops"
    api_key: str = "amctl-dev-key-2026"
    host: str = "0.0.0.0"
    port: int = 8077
    log_level: str = "info"

    # Docker socket (g2s host)
    docker_host: str = "unix:///var/run/docker.sock"

    # Phase 2: Continuous health monitoring interval (seconds)
    health_check_interval_secs: int = 300
    federation_check_interval_secs: int = 1800  # every 30 min (or on explicit check)
    enable_background_monitor: bool = True

    model_config = {"env_prefix": "AMCTL_", "env_file": ".env"}


settings = Settings()
