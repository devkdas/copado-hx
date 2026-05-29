from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict


class CopadoConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cicd_instance: str = ""
    sf_client_id: str = ""
    sf_client_secret: str = ""
    ai_base_url: str = "https://copadogpt-api.robotic.copado.com"
    ai_api_key: str = ""
    ai_org_id: str = ""
    ai_workspace_id: str = ""
    crt_base_url: str = "https://eu-robotic.copado.com"
    crt_pak: str = ""
    crt_org_id: str = ""
    crt_project_id: str = ""
    crt_job_id: str = ""
    actions_api_key: str = ""
    actions_base_url: str = ""
    default_pipeline_id: str = ""
    default_env: str = "UAT"
    output_format: str = "human"

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "CopadoConfig":
        if path is None:
            path = Path.cwd() / ".copado-hx.json"
            if not path.exists():
                path = Path.home() / ".copado-hx.json"
        if path.exists():
            raw = yaml.safe_load(path.read_text())
            if isinstance(raw, dict):
                return cls(**raw)
        return cls()

    def save(self, path: Optional[Path] = None) -> None:
        if path is None:
            path = Path.cwd() / ".copado-hx.json"
        path.write_text(yaml.dump(self.model_dump(exclude_none=True), default_flow_style=False))

    def merge_env(self) -> "CopadoConfig":
        import os
        env_map = {
            "COPADO_CICD_INSTANCE": "cicd_instance",
            "COPADO_AI_API_KEY": "ai_api_key",
            "COPADO_AI_BASE_URL": "ai_base_url",
            "COPADO_AI_ORG_ID": "ai_org_id",
            "COPADO_AI_WORKSPACE_ID": "ai_workspace_id",
            "COPADO_CRT_PAK": "crt_pak",
            "COPADO_CRT_BASE_URL": "crt_base_url",
            "COPADO_CRT_ORG_ID": "crt_org_id",
            "COPADO_CRT_PROJECT_ID": "crt_project_id",
            "COPADO_CRT_JOB_ID": "crt_job_id",
            "COPADO_ACTIONS_API_KEY": "actions_api_key",
            "COPADO_ACTIONS_BASE_URL": "actions_base_url",
            "COPADO_PIPELINE_ID": "default_pipeline_id",
            "COPADO_DEFAULT_ENV": "default_env",
        }
        for env_var, field_name in env_map.items():
            val = os.environ.get(env_var)
            if val:
                setattr(self, field_name, val)
        return self
