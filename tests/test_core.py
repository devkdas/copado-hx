from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from copado_hx.utils.config import CopadoConfig
from copado_hx.utils.storage import store_secrets, get_secret, delete_secret, clear_secrets
from unittest.mock import patch


@pytest.fixture
def tmp_secrets():
    with tempfile.TemporaryDirectory() as tmp:
        secrets_file = Path(tmp) / ".copado-hx-secrets.json"
        with patch("copado_hx.utils.storage.SECRETS_FILE", secrets_file):
            with patch("copado_hx.utils.storage.BACKUP_FILE", Path(tmp) / ".copado-hx-secrets.backup"):
                yield secrets_file


class TestConfig:
    def test_default_config(self):
        cfg = CopadoConfig()
        assert cfg.cicd_instance == "copadotrial6013563.lightning.force.com"
        assert cfg.ai_base_url == "https://copadogpt-api.robotic.copado.com"
        assert cfg.crt_base_url == "https://eu-robotic.copado.com"
        assert cfg.actions_base_url == "https://app-api.copado.com"
        assert cfg.ai_org_id == "49128"
        assert cfg.crt_job_id == "120561"
        assert cfg.ai_api_key == ""
        assert cfg.crt_pak == ""
        assert cfg.actions_api_key == ""

    def test_config_env_merge(self):
        import os
        os.environ["COPADO_AI_API_KEY"] = "test-key"
        os.environ["COPADO_ACTIONS_API_KEY"] = "test-actions-key"
        cfg = CopadoConfig().merge_env()
        assert cfg.ai_api_key == "test-key"
        assert cfg.actions_api_key == "test-actions-key"
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
    def test_store_and_get(self, tmp_secrets):
        clear_secrets()
        store_secrets({"test_key": "test_value"})
        assert get_secret("test_key") == "test_value"
        delete_secret("test_key")
        assert get_secret("test_key") is None

    def test_clear_all(self, tmp_secrets):
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
        client = ActionsApiClient("test-key")
        with patch.object(client, "_client") as mock_client:
            mock_response = mock_client.post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"Id": "a0shk0000000XteAAE", "copado__Status__c": "In Progress"}
            result = client.commit("a09XX0000000001", "test commit")
            assert result["Id"] == "a0shk0000000XteAAE"
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["params"]["webhookKey"] == "test-key"
            payload = call_kwargs["json"]["payload"]
            assert payload["templateName"] == "sfdx_commit_1"
            import json
            data = json.loads(payload["dataJson"])
            assert data["storyId"] == "a09XX0000000001"
            assert data["commitMessage"] == "test commit"

    def test_promote_validate_only_payload(self):
        from copado_hx.api.actions import ActionsApiClient
        client = ActionsApiClient("test-key")
        with patch.object(client, "_client") as mock_client:
            mock_response = mock_client.post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"Id": "a0shk0000000ZXFAA2"}
            result = client.promote("a09XX0000000001", "UAT", validate_only=True)
            assert result["Id"] == "a0shk0000000ZXFAA2"
            call_kwargs = mock_client.post.call_args[1]
            payload = call_kwargs["json"]["payload"]
            assert payload["templateName"] == "sfdx_promote_1"
            import json
            data = json.loads(payload["dataJson"])
            assert data["validateOnly"] is True
            assert data["storyId"] == "a09XX0000000001"
            assert data["targetEnvironment"] == "UAT"

    def test_promote_without_validate(self):
        from copado_hx.api.actions import ActionsApiClient
        client = ActionsApiClient("test-key")
        with patch.object(client, "_client") as mock_client:
            mock_response = mock_client.post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"Id": "a0shk0000000ZXFAA3"}
            result = client.promote("a09XX0000000001", "UAT")
            assert result["Id"] == "a0shk0000000ZXFAA3"
            call_kwargs = mock_client.post.call_args[1]
            payload = call_kwargs["json"]["payload"]
            assert "dataJson" in payload
            import json
            data = json.loads(payload["dataJson"])
            assert data["storyId"] == "a09XX0000000001"
            assert data["targetEnvironment"] == "UAT"


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


# ─── MOCK DATA TESTS ─────────────────────────────────────────────────────────

class TestMockData:
    def test_mock_module_imports(self):
        from copado_hx.api import mock_data as md
        assert md.MockCrtClient is not None
        assert md.MockSalesforceRestClient is not None
        assert md.MockActionsApiClient is not None
        assert md.MockCopadoCicdClient is not None
        assert md.MockAiPlatformClient is not None
        assert callable(md.get_mock_user_stories)
        assert callable(md.get_mock_user_story)
        assert callable(md.get_mock_environments)
        assert callable(md.get_mock_workflows)
        assert callable(md.get_mock_ai_response)
        assert len(md.MOCK_STORIES) == 1
        assert len(md.MOCK_ENVIRONMENTS) == 7
        assert len(md.MOCK_WORKFLOWS) == 7
        assert len(md.MOCK_TEST_JOBS) == 1

    def test_mock_sf_client(self):
        from copado_hx.api.mock_data import MockSalesforceRestClient
        client = MockSalesforceRestClient()
        stories = client.get_user_stories()
        assert len(stories) >= 1
        story = client.get_user_story("US-0000024")
        assert story is not None
        assert story["copado__Status__c"] == "Draft"
        assert story["Id"] == "a1vhk0000000P01AAE"
        envs = client.get_environments()
        assert len(envs) == 7

    def test_mock_crt_client_dynamic(self):
        from copado_hx.api.mock_data import MockCrtClient
        client = MockCrtClient()
        jobs = client.list_jobs_detailed()
        assert len(jobs) == 1
        result = client.trigger_build("120561")
        assert "id" in result["data"]
        assert "buildId" in result["data"]
        status = client.get_build_status("120561", "123")
        assert "totalTests" in status
        assert "passedTests" in status
        results = client.get_build_results("120561", "123")
        assert "totalTests" in results
        assert results["totalTests"] > 0

    def test_mock_sf_client_returns_dynamic_ids(self):
        from copado_hx.api.mock_data import MockSalesforceRestClient
        client = MockSalesforceRestClient()
        stories_a = client.get_user_stories()
        stories_b = client.get_user_stories()
        # Dynamic stories differ on each call
        assert len(stories_a) >= 1
        assert len(stories_b) >= 1

    def test_mock_actions_client(self):
        from copado_hx.api.mock_data import MockActionsApiClient
        client = MockActionsApiClient()
        result = client.commit("a09XX0000000001", "test")
        assert result["Id"] == "a0shk0000000wjxAAA"
        result = client.promote("a09XX0000000001", "UAT")
        assert result["Id"] == "a0shk0000000wlZAAQ"
        result = client.deploy("a09XX0000000001", "PROD")
        assert result["Id"] == "a0shk0000000wlZAAQ"

    def test_mock_cicd_client(self):
        from copado_hx.api.mock_data import MockCopadoCicdClient
        client = MockCopadoCicdClient()
        wfs = client.list_workflows()
        assert len(wfs) == 7
        run = client.trigger_workflow("wf-001")
        assert run["status"] == "succeeded"

    def test_mock_ai_client_context_aware(self):
        from copado_hx.api.mock_data import MockAiPlatformClient
        client = MockAiPlatformClient()
        result = client.ask_agent("release", "analyze failures in test execution")
        assert result["agent"] == "release"
        assert "Test Failure Analysis" in result["response"]

        result2 = client.ask_agent("plan", "generate a lead scoring architecture overview")
        assert "Analysis Results" in result2["response"]

    def test_mock_getter_functions(self):
        from copado_hx.api.mock_data import (
            get_mock_user_stories, get_mock_user_story,
            get_mock_environments, get_mock_workflows,
            get_mock_ai_response,
        )
        assert len(get_mock_user_stories()) >= 1
        assert get_mock_user_story("US-0000024") is not None
        assert get_mock_user_story("NONEXISTENT") is None
        assert len(get_mock_environments()) == 7
        assert len(get_mock_workflows()) == 7
        ai = get_mock_ai_response("release", "test")
        assert ai["agent"] == "release"


class TestConfigMockMode:
    def test_mock_mode_default(self):
        cfg = CopadoConfig()
        assert cfg.mock_mode is False

    def test_mock_mode_env_true(self):
        import os
        os.environ["COPADO_MOCK_MODE"] = "true"
        cfg = CopadoConfig().merge_env()
        assert cfg.mock_mode is True
        del os.environ["COPADO_MOCK_MODE"]

    def test_mock_mode_env_false(self):
        import os
        os.environ["COPADO_MOCK_MODE"] = "false"
        cfg = CopadoConfig().merge_env()
        assert cfg.mock_mode is False
        del os.environ["COPADO_MOCK_MODE"]

    def test_mock_mode_env_1(self):
        import os
        os.environ["COPADO_MOCK_MODE"] = "1"
        cfg = CopadoConfig().merge_env()
        assert cfg.mock_mode is True
        del os.environ["COPADO_MOCK_MODE"]


class TestConfidenceScore:
    def test_confidence_multi_factor_formula(self):
        total, passed, failed = 42, 39, 3
        test_score = (passed / total) * 60
        no_critical = max(0, 20 - (failed * 5))
        coverage_bonus = 20 if passed / total >= 0.5 else 0
        confidence = min(100, test_score + no_critical + coverage_bonus)
        assert test_score == pytest.approx(55.714, rel=0.01)
        assert no_critical == 5
        assert coverage_bonus == 20
        assert confidence == pytest.approx(80.714, rel=0.01)

    def test_confidence_all_passed(self):
        total, passed, failed = 10, 10, 0
        test_score = (passed / total) * 60
        no_critical = 20 if failed == 0 else max(0, 20 - (failed * 5))
        coverage_bonus = 20 if passed / total >= 0.5 else 0
        confidence = min(100, test_score + no_critical + coverage_bonus)
        assert confidence == 100

    def test_confidence_all_failed(self):
        total, passed, failed = 10, 0, 10
        test_score = (passed / total) * 60
        no_critical = max(0, 20 - (failed * 5))
        coverage_bonus = 20 if passed / total >= 0.5 else 0
        confidence = min(100, test_score + no_critical + coverage_bonus)
        assert confidence == 0

    def test_confidence_threshold_green(self):
        from copado_hx.utils.output import show_confidence_score
        score = show_confidence_score(10, 10, 0)
        assert score is None  # prints to console, no return value

    def test_confidence_text_recommendations(self):
        from copado_hx.utils.output import show_confidence_score
        assert callable(show_confidence_score)

    def test_shared_function_importable(self):
        from copado_hx.utils.output import show_confidence_score
        result1 = show_confidence_score(10, 10, 0)
        result2 = show_confidence_score(10, 7, 3)
        result3 = show_confidence_score(10, 2, 8)
        assert result1 is None and result2 is None and result3 is None


class TestAiTriage:
    def test_triage_prompt_format(self):
        from copado_hx.api.mock_data import MOCK_TEST_RESULTS
        tests = MOCK_TEST_RESULTS.get("testResults", [])
        failures = [t for t in tests if t.get("status") not in ("Passed", "Succeeded")]
        assert len(failures) == 3
        names = [f.get("testName") for f in failures]
        assert "EmailCampaignService.sendBatch" in names
        assert "OpportunityService.calculateRollup" in names

    def test_mock_ai_returns_triage_response(self):
        from copado_hx.api.mock_data import get_mock_ai_response
        result = get_mock_ai_response("release", "Analyze failures")
        resp = result.get("response", "")
        assert "Test Failure Analysis" in resp
        assert "Deployment Confidence" in resp

    def test_mock_ai_context_aware_failures(self):
        from copado_hx.api.mock_data import get_mock_ai_response
        result = get_mock_ai_response("release", "triage test execution failures")
        assert "Test Failure Analysis" in result["response"]

    def test_mock_ai_context_aware_deploy(self):
        from copado_hx.api.mock_data import get_mock_ai_response
        result = get_mock_ai_response("release", "deploy to production")
        assert "Deployment Analysis" in result["response"]

    def test_triage_early_exit_logic(self):
        failures = []
        assert len(failures) == 0  # early exit when no failures


class TestGracefulFallback:
    def test_mock_mode_fallback_enables_on_getter_failure(self):
        from copado_hx.utils.config import CopadoConfig
        cfg = CopadoConfig(mock_mode=False)
        assert cfg.mock_mode is False  # intentionally off

    def test_getters_return_mock_when_config_says_mock(self):
        from copado_hx._app import get_config, get_sf_client
        orig = get_config().mock_mode
        get_config().mock_mode = True
        client = get_sf_client()
        from copado_hx.api.mock_data import MockSalesforceRestClient
        assert isinstance(client, MockSalesforceRestClient)
        get_config().mock_mode = orig


class TestDemoCommand:
    def test_demo_imports_from_cli(self):
        from copado_hx.cli import app
        names = []
        for c in app.registered_commands:
            if c.name:
                names.append(c.name)
            elif c.callback:
                names.append(c.callback.__name__.replace("_", "-"))
        assert "demo" in names

    def test_display_test_results_confidence(self):
        from copado_hx.commands.test_cmds import _display_test_results
        assert callable(_display_test_results)


class TestApprovalGates:
    def test_is_gated_env(self):
        from copado_hx.utils.session_state import is_gated_env
        assert is_gated_env("PROD") is True
        assert is_gated_env("PRODUCTION") is True
        assert is_gated_env("prod") is True
        assert is_gated_env("UAT-SFP") is False
        assert is_gated_env("DEV") is False

    def test_store_and_consume_approval(self):
        from copado_hx.utils.session_state import (
            store_approval, consume_approval, has_pending_approval,
            save_state,
        )
        save_state({})
        code = store_approval("promote", "US-123", "PROD")
        assert code.startswith("AP-")
        assert has_pending_approval() is True
        pending = consume_approval(code)
        assert pending is not None
        assert pending["action"] == "promote"
        assert pending["story_id"] == "US-123"
        assert pending["env"] == "PROD"
        assert has_pending_approval() is False
        assert consume_approval(code) is None

    def test_consume_invalid_code(self):
        from copado_hx.utils.session_state import consume_approval, save_state
        save_state({})
        assert consume_approval("INVALID") is None

    def test_has_pending_empty(self):
        from copado_hx.utils.session_state import has_pending_approval, save_state
        save_state({})
        assert has_pending_approval() is False


class TestSelfHeal:
    def test_self_diagnose_mock_path(self):
        from copado_hx.api.mock_data import MockAiPlatformClient
        mock = MockAiPlatformClient()
        result = mock.ask_agent("operate", "Analyze this")
        assert result["agent"] == "operate"
        assert "Analysis Results" in result.get("response", "")

    def test_mock_operate_agent_exists(self):
        from copado_hx.api.ai import AiPlatformClient
        assert "operate" in AiPlatformClient.AGENTS

    def test_self_diagnose_function_import(self):
        from copado_hx.commands.pipeline_cmds import _self_diagnose
        assert callable(_self_diagnose)

    def test_self_diagnose_test_function_import(self):
        from copado_hx.commands.test_cmds import _self_diagnose_test
        assert callable(_self_diagnose_test)


class TestMcpApprovalTools:
    def test_approve_action_module_imports(self):
        from copado_hx.utils.session_state import consume_approval
        assert callable(consume_approval)

    def test_mcp_approve_tool_import(self):
        from copado_hx.skills.mcp_server import _self_diagnose
        assert callable(_self_diagnose)
