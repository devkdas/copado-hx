from __future__ import annotations

from typing import Any, Optional

from copado_hx.api import BaseApiClient


class CopadoCicdClient(BaseApiClient):
    def __init__(self, api_key: str, base_url: str, org_id: str, workspace_id: str):
        base = base_url.rstrip("/")
        super().__init__(base, timeout=120)
        self._api_key = api_key
        self._org_id = org_id
        self._workspace_id = workspace_id

    def _headers(self) -> dict[str, str]:
        h = super()._headers()
        h["X-Authorization"] = self._api_key
        return h

    def list_workflows(self) -> list[dict]:
        return self.get(f"/organizations/{self._org_id}/workflows") or []

    def get_workflow(self, workflow_id: str) -> dict:
        return self.get(f"/organizations/{self._org_id}/workflows/{workflow_id}")

    def trigger_workflow(
        self,
        workflow_id: str,
        parameters: Optional[dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> dict:
        ws_id = workspace_id or self._workspace_id
        body: dict[str, Any] = {"workflow_id": workflow_id, "workspace_id": ws_id}
        if parameters:
            body["parameters"] = parameters
        return self.post(f"/organizations/{self._org_id}/workflows/runs", json=body)

    def list_runs(self) -> list[dict]:
        return self.get(f"/organizations/{self._org_id}/workflows/runs") or []

    def get_run(self, run_id: str) -> dict:
        return self.get(f"/organizations/{self._org_id}/workflows/runs/{run_id}")

    def list_skills(self) -> list[dict]:
        return self.get(f"/organizations/{self._org_id}/skills/my") or []

    def promote_skill(self, skill_id: str) -> dict:
        return self.post(f"/organizations/{self._org_id}/skills/{skill_id}/promote")

    def demote_skill(self, skill_id: str) -> dict:
        return self.post(f"/organizations/{self._org_id}/skills/{skill_id}/demote")

    def commit(self, story_id: str, message: str) -> dict:
        workflow_id = "16615d17-a810-4e46-aff3-af0a2fa4d649"
        parameters = {
            "user_story_title": story_id,
            "auto_commit": True,
        }
        if message:
            parameters["commit_message"] = message
        return self.trigger_workflow(workflow_id, parameters)

    def promote(self, story_id: str, environment: str, validate_only: bool = False) -> dict:
        workflow_id = "d4e5f6a7-b8c9-4d0e-a1f2-3b4c5d6e7f80"
        parameters = {
            "problem": story_id,
            "target_environment": environment,
        }
        return self.trigger_workflow(workflow_id, parameters)

    def deploy(self, story_id: str, environment: str) -> dict:
        workflow_id = "16615d17-a810-4e46-aff3-af0a2fa4d649"
        parameters = {
            "user_story_title": story_id,
            "target_environment": environment,
        }
        return self.trigger_workflow(workflow_id, parameters)

    def get_job_execution_status(self, run_id: str) -> dict:
        return self.get_run(run_id)
