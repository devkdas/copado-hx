from __future__ import annotations

from typing import Dict

from copado_hx.api import BaseApiClient


class CrtClient(BaseApiClient):
    def __init__(self, base_url: str, pak: str, org_id: str, project_id: str):
        base = base_url.rstrip("/")
        self._pak = pak
        self._org_id = org_id
        self._project_id = project_id
        super().__init__(base, timeout=120)

    def _headers(self) -> Dict[str, str]:
        h = super()._headers()
        h["X-Authorization"] = self._pak
        return h

    def list_jobs(self) -> list[dict]:
        return self.get(f"/pace/v4/projects/{self._project_id}/jobs") or []

    def list_jobs_detailed(self) -> list[dict]:
        data = self.list_jobs()
        if isinstance(data, dict):
            items = data.get("data", data.get("items", data.get("jobs", [])))
            return items
        return data if isinstance(data, list) else []

    def trigger_build(self, job_id: str) -> dict:
        return self.post(f"/pace/v4/projects/{self._project_id}/jobs/{job_id}/builds", json={})

    def get_build_status(self, job_id: str, build_id: str) -> dict:
        return self.get(f"/pace/v4/projects/{self._project_id}/jobs/{job_id}/builds/{build_id}")

    def get_build_results(self, job_id: str, build_id: str) -> dict:
        return self.get(f"/pace/v4/projects/{self._project_id}/jobs/{job_id}/builds/{build_id}/results")
