from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from copado_hx.utils.config import CopadoConfig
from copado_hx.utils.storage import store_secrets, get_secret, delete_secret, clear_secrets
from unittest.mock import patch


class TestConfig:
    def test_default_config(self):
        cfg = CopadoConfig()
        assert cfg.cicd_instance == ""
        assert cfg.ai_api_key == ""
        assert cfg.crt_pak == ""
        assert cfg.ai_base_url == "https://copadogpt-api.robotic.copado.com"
        assert cfg.ai_org_id == ""
        assert cfg.crt_base_url == "https://eu-robotic.copado.com"
        assert cfg.crt_job_id == ""
        assert cfg.actions_api_key == ""
        assert cfg.actions_base_url == "https://app-api.copado.com"

    def test_config_env_merge(self):
        import os
        os.environ["COPADO_AI_API_KEY"] = "test-key"
        os.environ["COPADO_ACTIONS_API_KEY"] = "test-actions-key"
        cfg = CopadoConfig().merge_env()
        assert cfg.ai_api_key == ""
        assert cfg.actions_api_key == ""
        assert cfg.actions_base_url == "https://app-api.copado.com"
        del os.environ["COPADO_AI_API_KEY"]
        del os.environ["COPADO_ACTIONS_API_KEY"]

    def test_config_load_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / ".copado-hx.json"
            cfg = CopadoConfig(cicd_instance="test.instance.com", ai_api_key="secret")
            cfg.save(cfg_path)

            loaded = CopadoConfig.load(cfg_path)
            assert loaded.cicd_instance == "test.instance.com"
            assert loaded.ai_api_key == "secret"

    def test_config_no_passwords(self):
        cfg = CopadoConfig()
        assert not hasattr(cfg, "sf_password")
        assert not hasattr(cfg, "sf_security_token")


class TestStorage:
    def test_store_and_get(self):
        clear_secrets()
        store_secrets({"test_key": "test_value"})
        assert get_secret("test_key") == "test_value"
        delete_secret("test_key")
        assert get_secret("test_key") is None

    def test_clear_all(self):
        store_secrets({"a": "1", "b": "2"})
        clear_secrets()
        assert get_secret("a") is None
        assert get_secret("b") is None


class TestApiBase:
    def test_error_parsing(self):
        from copado_hx.api.base import CopadoError, AuthError, NotFoundError, RateLimitError

        assert issubclass(AuthError, CopadoError)
        assert issubclass(NotFoundError, CopadoError)
        assert issubclass(RateLimitError, CopadoError)

        err = CopadoError("test", 500)
        assert err.status_code == 500
        assert str(err) == "test"


class TestApiActions:
    def test_module_imports(self):
        from copado_hx.api.actions import ActionsApiClient
        assert ActionsApiClient is not None
        assert ActionsApiClient.ACTIONS["commit"] == "sfdx_commit_1"
        assert ActionsApiClient.ACTIONS["promote"] == "sfdx_promote_1"
        assert ActionsApiClient.ACTIONS["deploy"] == "sfdx_deploy_1"

    def test_run_job_template_payload(self):
        from copado_hx.api.actions import ActionsApiClient
        from unittest.mock import patch
        client = ActionsApiClient("test-key")
        with patch.object(client, "_client") as mock_client:
            mock_response = mock_client.post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"Id": "a0shk0000000XteAAE", "copado__Status__c": "In Progress"}
            result = client.commit("a09XX0000000001", "test commit")
            assert result["Id"] == "a0shk0000000XteAAE"
            # Verify the correct URL and payload were used
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["params"]["webhookKey"] == "test-key"
            assert call_kwargs["json"]["payload"]["templateName"] == "sfdx_commit_1"


class TestApiCicd:
    def test_module_imports(self):
        from copado_hx.api.cicd import CopadoCicdClient
        # Just verify the class exists and can be instantiated
        assert CopadoCicdClient is not None


class TestApiRest:
    def test_module_imports(self):
        from copado_hx.api.sf_rest import SalesforceRestClient
        assert SalesforceRestClient is not None

    def test_query_params(self):
        from copado_hx.api.sf_rest import SalesforceRestClient
        with patch.object(SalesforceRestClient, "_request") as mock:
            mock.return_value = {"records": [{"Id": "test-id", "Name": "Test Story"}]}
            client = SalesforceRestClient("https://example.com", "test-token")
            stories = client.get_user_stories(pipeline="MyPipe", status="In Progress")
            assert len(stories) == 1
            assert stories[0]["Name"] == "Test Story"
            called_url = mock.call_args[0][1]
            assert "MyPipe" in called_url
            assert "%27MyPipe%27" in called_url
            assert "%27In%20Progress%27" in called_url


class TestApiCrt:
    def test_module_imports(self):
        from copado_hx.api.crt import CrtClient
        assert CrtClient is not None


class TestApiAi:
    def test_agent_list(self):
        from copado_hx.api.ai import AiPlatformClient
        assert len(AiPlatformClient.AGENTS) == 5
        assert "plan" in AiPlatformClient.AGENTS
        assert "build" in AiPlatformClient.AGENTS
        assert "test" in AiPlatformClient.AGENTS
        assert "release" in AiPlatformClient.AGENTS
        assert "operate" in AiPlatformClient.AGENTS

    def test_invalid_agent(self):
        from copado_hx.api.ai import AiPlatformClient

        client = AiPlatformClient("test-key", "https://example.com", "org1", "ws1")
        with pytest.raises(ValueError):
            client.ask_agent("invalid_agent", "hello")


class TestSalesforceAuth:
    def test_module_imports(self):
        from copado_hx.auth.salesforce import login_web, get_sf_token
        assert callable(login_web)
        assert callable(get_sf_token)


def test_cli_import():
    from copado_hx.cli import app
    assert app is not None
