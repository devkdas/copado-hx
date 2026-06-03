from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CopadoConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cicd_instance: str = "copadotrial6013563.lightning.force.com"
    ai_base_url: str = "https://copadogpt-api.robotic.copado.com"
    ai_api_key: str = ""
    ai_org_id: str = "49128"
    ai_workspace_id: str = "b00a8dda-c336-472c-9a64-e6bf3bc415c1"
    crt_base_url: str = "https://eu-robotic.copado.com"
    crt_pak: str = ""
    crt_org_id: str = "43844"
    crt_project_id: str = "76303"
    crt_job_id: str = "120561"
    actions_api_key: str = ""
    actions_base_url: str = "https://app-api.copado.com"
    sf_client_id: str = ""
    sf_client_secret: str = ""
    sf_redirect_uri: str = "sfdx://success"
    sf_username: str = ""
    default_pipeline_id: str = ""
    default_env: str = "UAT-SFP"
    output_format: str = "human"
    current_story_id: str = ""
    current_story_name: str = ""
    mock_mode: bool = False

    @classmethod
    def _default_path(cls) -> Path:
        path = Path.cwd() / ".copado-hx.json"
        if not path.exists():
            path = Path.home() / ".copado-hx.json"
        return path

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "CopadoConfig":
        if path is None:
            path = cls._default_path()
        if path.exists():
            raw = None
            text = path.read_text()
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                try:
                    import yaml
                    raw = yaml.safe_load(text)
                except ImportError:
                    pass
            if isinstance(raw, dict):
                return cls(**raw)
        return cls()

    def save(self, path: Optional[Path] = None) -> None:
        if path is None:
            path = self._default_path()
        data = self.model_dump(exclude_none=True)
        path.write_text(json.dumps(data, indent=2))

    def set_and_save(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.save()

    def merge_env(self) -> "CopadoConfig":
        import os

        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

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
            "COPADO_MOCK_MODE": "mock_mode",
            "COPADO_SF_CLIENT_ID": "sf_client_id",
            "COPADO_SF_CLIENT_SECRET": "sf_client_secret",
            "COPADO_SF_REDIRECT_URI": "sf_redirect_uri",
            "COPADO_SF_USERNAME": "sf_username",
        }
        bool_fields = {"mock_mode"}
        for env_var, field_name in env_map.items():
            val = os.environ.get(env_var)
            if val:
                if field_name in bool_fields:
                    setattr(self, field_name, val.lower() in ("true", "1", "yes"))
                else:
                    setattr(self, field_name, val)
        return self
