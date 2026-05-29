from __future__ import annotations

import json

import httpx

from copado_hx.api.base import CopadoError


class ActionsApiClient:
    ACTIONS = {
        "commit": "sfdx_commit_1",
        "promote": "sfdx_promote_1",
        "deploy": "sfdx_deploy_1",
    }

    def __init__(self, webhook_key: str, base_url: str = "https://app-api.copado.com"):
        self._webhook_key = webhook_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=httpx.Timeout(120), verify=True)

    def _run_job_template(self, template_name: str) -> dict:
        body = {"payload": {"templateName": template_name, "runAfterInstantiation": True}}
        url = f"{self._base_url}/json/v1/webhook/mcwebhook/RunJobTemplate"
        params = {"webhookKey": self._webhook_key}

        try:
            resp = self._client.post(url, params=params, json=body)
        except httpx.TimeoutException:
            raise CopadoError("Actions API request timed out", 0)
        except httpx.ConnectError as e:
            raise CopadoError(f"Connection to Actions API failed: {e}", 0)

        if resp.status_code >= 400:
            detail = resp.text[:500]
            raise CopadoError(
                f"Actions API error ({resp.status_code}): {detail}",
                resp.status_code,
                detail,
            )

        try:
            return resp.json()
        except (json.JSONDecodeError, ValueError):
            return {"raw": resp.text, "status_code": resp.status_code}

    def commit(self, story_id: str, message: str) -> dict:
        return self._run_job_template(self.ACTIONS["commit"])

    def promote(self, story_id: str, environment: str, validate_only: bool = False) -> dict:
        return self._run_job_template(self.ACTIONS["promote"])

    def deploy(self, story_id: str, environment: str) -> dict:
        return self._run_job_template(self.ACTIONS["deploy"])

    def close(self):
        self._client.close()
