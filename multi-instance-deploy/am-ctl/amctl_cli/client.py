"""HTTP client for the am-ctl API."""

import httpx


class AmCtlClient:
    """Thin wrapper around the am-ctl API."""

    def __init__(self, base_url: str = "http://localhost:8077", api_key: str = "amctl-dev-key-2026"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=60.0,
        )

    def health(self) -> dict:
        resp = self._client.get("/api/v1/health")
        resp.raise_for_status()
        return resp.json()

    def list_agents(self) -> list[dict]:
        resp = self._client.get("/api/v1/agents")
        resp.raise_for_status()
        return resp.json()

    def get_agent(self, name: str) -> dict:
        resp = self._client.get(f"/api/v1/agents/{name}")
        resp.raise_for_status()
        return resp.json()

    def get_agent_status(self, name: str) -> dict:
        resp = self._client.get(f"/api/v1/agents/{name}/status")
        resp.raise_for_status()
        return resp.json()

    def get_fleet_status(self) -> dict:
        resp = self._client.get("/api/v1/status")
        resp.raise_for_status()
        return resp.json()

    def update_agent(self, name: str, **kwargs) -> dict:
        resp = self._client.put(f"/api/v1/agents/{name}", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    # Phase 2: Health & Alerts
    def get_fleet_health(self) -> dict:
        resp = self._client.get("/api/v1/health/fleet")
        resp.raise_for_status()
        return resp.json()

    def trigger_fleet_health_check(self) -> dict:
        resp = self._client.post("/api/v1/health/fleet/check")
        resp.raise_for_status()
        return resp.json()

    def get_agent_health(self, name: str) -> dict:
        resp = self._client.get(f"/api/v1/health/{name}")
        resp.raise_for_status()
        return resp.json()

    def trigger_agent_health_check(self, name: str) -> dict:
        resp = self._client.post(f"/api/v1/health/{name}/check")
        resp.raise_for_status()
        return resp.json()

    def get_agent_health_history(self, name: str, check_type: str | None = None, limit: int = 50) -> list[dict]:
        params = {"limit": limit}
        if check_type:
            params["check_type"] = check_type
        resp = self._client.get(f"/api/v1/health/{name}/history", params=params)
        resp.raise_for_status()
        return resp.json()

    def list_alerts(self, status: str = "open") -> list[dict]:
        resp = self._client.get("/api/v1/alerts", params={"status": status})
        resp.raise_for_status()
        return resp.json()

    def ack_alert(self, alert_id: int, operator: str = "cli:operator") -> dict:
        resp = self._client.post(f"/api/v1/alerts/{alert_id}/ack", json={"operator": operator})
        resp.raise_for_status()
        return resp.json()

    # Phase 3: Credentials & Identity
    def get_agent_credentials(self, name: str) -> dict:
        resp = self._client.get(f"/api/v1/agents/{name}/credentials")
        resp.raise_for_status()
        return resp.json()

    def verify_agent_credentials(self, name: str, sync_registry: bool = True) -> dict:
        resp = self._client.post(
            f"/api/v1/agents/{name}/credentials/verify",
            params={"sync_registry": sync_registry},
        )
        resp.raise_for_status()
        return resp.json()

    def check_credential_collisions(self) -> dict:
        resp = self._client.get("/api/v1/credentials/collisions")
        resp.raise_for_status()
        return resp.json()

    # Phase 4: Reconciler (check / plan / history)
    def reconcile_check(self, agent_name: str | None = None) -> dict:
        params = {"agent_name": agent_name} if agent_name else {}
        resp = self._client.post("/api/v1/reconcile/check", params=params)
        resp.raise_for_status()
        return resp.json()

    def reconcile_plan(self, agent_name: str) -> dict:
        resp = self._client.post(f"/api/v1/reconcile/plan/{agent_name}")
        resp.raise_for_status()
        return resp.json()

    def reconcile_apply(self, agent_name: str, operator: str = "cli:reconcile_apply") -> dict:
        resp = self._client.post(
            f"/api/v1/reconcile/apply/{agent_name}",
            params={"operator": operator},
        )
        resp.raise_for_status()
        return resp.json()

    def reconcile_history(self, agent_name: str | None = None, limit: int = 50) -> list[dict]:
        params: dict = {"limit": limit}
        if agent_name:
            params["agent_name"] = agent_name
        resp = self._client.get("/api/v1/reconcile/history", params=params)
        resp.raise_for_status()
        return resp.json()

    # Phase 5: Database & Infrastructure Backups
    def backup_run(self, backup_type: str = "manual", operator: str = "cli:backup") -> dict:
        resp = self._client.post(
            "/api/v1/backups/run",
            params={"backup_type": backup_type, "operator": operator},
        )
        resp.raise_for_status()
        return resp.json()

    def backup_list(self, target: str | None = None, limit: int = 40) -> list[dict]:
        params: dict = {"limit": limit}
        if target:
            params["target"] = target
        resp = self._client.get("/api/v1/backups", params=params)
        resp.raise_for_status()
        return resp.json()

    def backup_verify(self, backup_id: int | None = None, operator: str = "cli:backup_verify") -> dict:
        if backup_id is not None:
            resp = self._client.post(
                f"/api/v1/backups/{backup_id}/verify",
                params={"operator": operator},
            )
        else:
            resp = self._client.post(
                "/api/v1/backups/verify",
                params={"operator": operator},
            )
        resp.raise_for_status()
        return resp.json()

    # Phase 6: Releases & Deployment
    def register_release(self, version: str, bundle_path: str | None = None) -> dict:
        resp = self._client.post(
            "/api/v1/releases",
            json={"version": version, "bundle_path": bundle_path},
        )
        resp.raise_for_status()
        return resp.json()

    def list_releases(self) -> list[dict]:
        resp = self._client.get("/api/v1/releases")
        resp.raise_for_status()
        return resp.json()

    def deploy_release(self, agent_name: str, version: str, operator: str = "cli:deploy") -> dict:
        resp = self._client.post(
            f"/api/v1/deploy/{agent_name}",
            json={"version": version, "operator": operator},
        )
        resp.raise_for_status()
        return resp.json()

    def deploy_status(self) -> dict:
        resp = self._client.get("/api/v1/deploy/status")
        resp.raise_for_status()
        return resp.json()

    def deploy_version(
        self,
        agent_name: str,
        image_version: str,
        skip_restart: bool = False,
        force: bool = False,
        operator: str = "cli:deploy_version",
    ) -> dict:
        resp = self._client.post(
            f"/api/v1/deploy/{agent_name}/version",
            json={
                "image_version": image_version,
                "skip_restart": skip_restart,
                "force": force,
                "operator": operator,
            },
        )
        resp.raise_for_status()
        return resp.json()

    # Phase 7: Model Management
    def list_fleet_models(self) -> dict:
        resp = self._client.get("/api/v1/models")
        resp.raise_for_status()
        return resp.json()

    def get_agent_models(self, agent_name: str) -> dict:
        resp = self._client.get(f"/api/v1/models/{agent_name}")
        resp.raise_for_status()
        return resp.json()

    def set_agent_models(
        self,
        agent_name: str,
        chat_model: str | None = None,
        utility_model: str | None = None,
        embedding_model: str | None = None,
        preset: str | None = None,
        operator: str = "cli:models",
    ) -> dict:
        resp = self._client.put(
            f"/api/v1/models/{agent_name}",
            json={
                "chat_model": chat_model,
                "utility_model": utility_model,
                "embedding_model": embedding_model,
                "preset": preset,
                "operator": operator,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def diagnose_models(self) -> dict:
        resp = self._client.post("/api/v1/models/diagnose")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self._client.close()
