from __future__ import annotations

from typing import Dict, Optional

from copado_hx.api import BaseApiClient


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
        super().__init__(base, timeout=120)
        self._api_key = api_key
        self._org_id = org_id
        self._workspace_id = workspace_id

    def _headers(self) -> Dict[str, str]:
        h = super()._headers()
        h["X-Authorization"] = self._api_key
        return h

    def list_dialogues(self) -> list[dict]:
        return self.get(f"/organizations/{self._org_id}/dialogues") or []

    def create_dialogue(self, agent_id: str) -> dict:
        return self.post(
            f"/organizations/{self._org_id}/dialogues",
            json={"workspaceId": self._workspace_id, "assistantId": agent_id},
        )

    def send_message(self, dialogue_id: str, message: str) -> dict:
        return self.post(
            f"/organizations/{self._org_id}/dialogues/{dialogue_id}/messages",
            json={"message": message},
        )

    def _validate_agent(self, agent_id: str) -> None:
        if agent_id not in self.AGENTS:
            raise ValueError(f"Unknown agent: {agent_id}. Valid: {', '.join(self.AGENTS.keys())}")

    def ask_agent(self, agent_id: str, prompt: str) -> dict:
        self._validate_agent(agent_id)
        resp = self.post(
            f"/organizations/{self._org_id}/workspaces/{self._workspace_id}/expert/{agent_id}/v1/chat/completions",
            json={"model": agent_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
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

    def chat_agent(self, agent_id: str, prompt: str, history: Optional[list[dict]] = None) -> dict:
        self._validate_agent(agent_id)
        messages = (history or []) + [{"role": "user", "content": prompt}]
        resp = self.post(
            f"/organizations/{self._org_id}/workspaces/{self._workspace_id}/expert/{agent_id}/v1/chat/completions",
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

    def get_dialogue(self, dialogue_id: str) -> dict:
        return self.get(f"/organizations/{self._org_id}/dialogues/{dialogue_id}")
