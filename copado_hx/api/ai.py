from __future__ import annotations

import json
from typing import Dict, Generator, Optional

import httpx

from copado_hx.api import BaseApiClient
from copado_hx.api.base import CopadoError


class AiPlatformClient(BaseApiClient):
    AGENTS = {
        "plan": {"id": "plan", "description": "Plan Agent — user story refinement, conflicts, sprint planning"},
        "build": {"id": "build", "description": "Build Agent — Apex generation, metadata analysis, troubleshooting"},
        "test": {"id": "test", "description": "Test Agent — CRT test scripts, coverage advice"},
        "release": {"id": "release", "description": "Release Agent — commits, promotions, deployments, release notes"},
        "operate": {"id": "operate", "description": "Operate Agent — post-release docs, change management, training"},
    }

    def __init__(self, api_key: str, base_url: str, org_id: str, workspace_id: str):
        base = base_url.rstrip("/")
        super().__init__(base, timeout=300)
        self._api_key = api_key
        self._org_id = org_id
        self._workspace_id = workspace_id

    def _headers(self) -> Dict[str, str]:
        h = super()._headers()
        h["X-Authorization"] = self._api_key
        return h

    def _validate_agent(self, agent_id: str) -> None:
        if agent_id not in self.AGENTS:
            raise ValueError(f"Unknown agent: {agent_id}. Valid: {', '.join(self.AGENTS.keys())}")

    def _chat_url(self, agent_id: str) -> str:
        return f"/organizations/{self._org_id}/workspaces/{self._workspace_id}/expert/{agent_id}/v1/chat/completions"

    def ask_agent(self, agent_id: str, prompt: str, **kwargs) -> dict:
        self._validate_agent(agent_id)
        resp = self.post(
            self._chat_url(agent_id),
            json={"model": agent_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, **kwargs},
        )
        choice = resp.get("choices", [{}])[0]
        message = choice.get("message", {})
        return {
            "agent": agent_id,
            "dialogue_id": resp.get("id", ""),
            "response": message.get("content", ""),
            "model": resp.get("model", ""),
            "usage": resp.get("usage"),
        }

    def ask_agent_stream(
        self, agent_id: str, prompt: str, **kwargs
    ) -> Generator[str, None, None]:
        self._validate_agent(agent_id)
        url = f"{self.base_url}{self._chat_url(agent_id)}"
        body = {"model": agent_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "stream": True, **kwargs}
        headers = self._headers()

        try:
            with self._client.stream("POST", url, json=body, headers=headers) as resp:
                if resp.status_code >= 400:
                    detail = resp.text[:500]
                    raise CopadoError(f"AI API error ({resp.status_code}): {detail}", resp.status_code)
                for line in resp.iter_lines():
                    line = line.strip() if line else ""
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        return
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError):
                        if data_str.strip():
                            yield data_str
        except httpx.TimeoutException:
            raise CopadoError("AI API request timed out", 0)
        except httpx.ConnectError as e:
            raise CopadoError(f"Connection to AI API failed: {e}", 0)

    def chat_agent(self, agent_id: str, prompt: str, history: Optional[list[dict]] = None) -> dict:
        self._validate_agent(agent_id)
        messages = (history or []) + [{"role": "user", "content": prompt}]
        resp = self.post(
            self._chat_url(agent_id),
            json={"model": agent_id, "messages": messages, "max_tokens": 4096},
        )
        choice = resp.get("choices", [{}])[0]
        message = choice.get("message", {})
        return {
            "agent": agent_id,
            "dialogue_id": resp.get("id", ""),
            "response": message.get("content", ""),
            "model": resp.get("model", ""),
            "usage": resp.get("usage"),
        }


