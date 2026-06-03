from __future__ import annotations

import time
from typing import Optional

import typer
from rich.console import Console

from copado_hx.api.actions import ActionsApiClient
from copado_hx.api.ai import AiPlatformClient
from copado_hx.api.base import CopadoError
from copado_hx.api.cicd import CopadoCicdClient
from copado_hx.api.crt import CrtClient
from copado_hx.api.sf_rest import SalesforceRestClient
from copado_hx.utils.config import CopadoConfig
from copado_hx.utils.output import (
    print_error,
    print_warning,
)
from copado_hx.utils.storage import (
    get_secret,
)

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("copado-hx")
except Exception:
    __version__ = "1.0.0"

app = typer.Typer(
    name="copado-hx",
    help="Copado Headless Developer Experience — Full Salesforce DevOps from the terminal",
    no_args_is_help=True,
)

auth_app = typer.Typer(help="Authentication commands")
app.add_typer(auth_app, name="auth", help="Authentication commands")

story_app = typer.Typer(help="User story management")
app.add_typer(story_app, name="story", help="User story management")

test_app = typer.Typer(help="Test execution (CRT)")
app.add_typer(test_app, name="test", help="Test execution (CRT)")

ai_app = typer.Typer(help="AI agent conversations")
app.add_typer(ai_app, name="ai", help="AI agent conversations")

wf_app = typer.Typer(help="Workflow management (CI/CD)")
app.add_typer(wf_app, name="workflow", help="Workflow management (CI/CD)")

env_app = typer.Typer(help="Environment commands")
app.add_typer(env_app, name="env", help="Environment commands")

_config: Optional[CopadoConfig] = None
_cicd_client: Optional[CopadoCicdClient] = None
_actions_client: Optional[ActionsApiClient] = None
_crt_client: Optional[CrtClient] = None
_ai_client: Optional[AiPlatformClient] = None
_sf_client: Optional[SalesforceRestClient] = None


def get_config() -> CopadoConfig:
    global _config
    if _config is None:
        _config = CopadoConfig.load().merge_env()
    return _config


def get_sf_client() -> SalesforceRestClient:
    global _sf_client
    cfg = get_config()
    if cfg.mock_mode:
        from copado_hx.api.mock_data import MockSalesforceRestClient
        return MockSalesforceRestClient()
    if _sf_client is None:
        token = get_secret("sf_access_token")
        instance = get_secret("sf_instance_url")
        if not token or not instance:
            cfg.mock_mode = True
            print_warning("Salesforce not authenticated, falling back to mock data")
            from copado_hx.api.mock_data import MockSalesforceRestClient
            return MockSalesforceRestClient()
        _sf_client = SalesforceRestClient(instance, token)
    return _sf_client


def get_cicd_client() -> CopadoCicdClient:
    global _cicd_client
    cfg = get_config()
    if cfg.mock_mode:
        from copado_hx.api.mock_data import MockCopadoCicdClient
        return MockCopadoCicdClient()
    if _cicd_client is None:
        api_key = cfg.ai_api_key or get_secret("ai_api_key") or ""
        org_id = cfg.ai_org_id or get_secret("ai_org_id") or ""
        ws_id = cfg.ai_workspace_id or get_secret("ai_workspace_id") or ""
        if not api_key or not org_id or not ws_id:
            cfg.mock_mode = True
            print_warning("CI/CD credentials not configured, falling back to mock data")
            from copado_hx.api.mock_data import MockCopadoCicdClient
            return MockCopadoCicdClient()
        _cicd_client = CopadoCicdClient(api_key, cfg.ai_base_url, org_id, ws_id)
    return _cicd_client


def get_actions_client() -> ActionsApiClient:
    global _actions_client
    cfg = get_config()
    if cfg.mock_mode:
        from copado_hx.api.mock_data import MockActionsApiClient
        return MockActionsApiClient()
    if _actions_client is None:
        api_key = cfg.actions_api_key or get_secret("actions_api_key") or ""
        if not api_key:
            cfg.mock_mode = True
            print_warning("Actions API key not configured, falling back to mock data")
            from copado_hx.api.mock_data import MockActionsApiClient
            return MockActionsApiClient()
        _actions_client = ActionsApiClient(api_key, cfg.actions_base_url)
    return _actions_client


def get_crt_client() -> CrtClient:
    global _crt_client
    cfg = get_config()
    if cfg.mock_mode:
        from copado_hx.api.mock_data import MockCrtClient
        return MockCrtClient()
    if _crt_client is None:
        pak = cfg.crt_pak or get_secret("crt_pak") or ""
        if not pak:
            cfg.mock_mode = True
            print_warning("CRT PAK not configured, falling back to mock data")
            from copado_hx.api.mock_data import MockCrtClient
            return MockCrtClient()
        _crt_client = CrtClient(cfg.crt_base_url, pak, cfg.crt_org_id, cfg.crt_project_id)
    return _crt_client


def get_ai_client() -> AiPlatformClient:
    global _ai_client
    cfg = get_config()
    if cfg.mock_mode:
        from copado_hx.api.mock_data import MockAiPlatformClient
        return MockAiPlatformClient()
    if _ai_client is None:
        api_key = cfg.ai_api_key or get_secret("ai_api_key") or ""
        if not api_key:
            cfg.mock_mode = True
            print_warning("AI API key not configured, falling back to mock data")
            from copado_hx.api.mock_data import MockAiPlatformClient
            return MockAiPlatformClient()
        _ai_client = AiPlatformClient(api_key, cfg.ai_base_url, cfg.ai_org_id, cfg.ai_workspace_id)
    return _ai_client


def _resolve_story_id(story_id: Optional[str] = None) -> Optional[str]:
    if story_id:
        return story_id
    sid = get_config().current_story_id
    if not sid:
        sid = get_secret("current_story_id") or ""
        if sid:
            get_config().set_and_save(current_story_id=sid)
    return sid or None


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "****"
    return f"****{token[-4:]}"


def _handle_api_error(e: Exception) -> None:
    if isinstance(e, CopadoError):
        print_error(str(e))
        return
    msg = str(e)
    if "timed out" in msg.lower() or "timeout" in msg.lower():
        print_error("Request timed out — check your network connection.")
    else:
        print_error(msg)


def _poll_job(job_id: str, sf_client: 'SalesforceRestClient') -> str:
    console = Console()
    final_status = ""
    errors = 0
    with console.status("Waiting for job completion...") as s:
        for _ in range(60):
            time.sleep(10)
            try:
                records = sf_client.query(
                    f"SELECT Id, copado__Status__c FROM copado__JobExecution__c WHERE Id = '{job_id}'"
                )
                result = records[0] if records else {}
                final_status = result.get("copado__Status__c", "")
                s.update(f"Status: {final_status}")
                errors = 0
                if final_status in ("Completed", "Failed", "Error"):
                    break
            except Exception:
                errors += 1
                if errors >= 3:
                    print_error("Job polling failed after 3 consecutive errors.")
                    break
    return final_status


def _validate_environment(env_name: str) -> None:
    sf = get_sf_client()
    try:
        result = sf.resolve_environment(env_name)
    except CopadoError:
        raise CopadoError(f"Could not validate environment '{env_name}'.")
    if not result:
        raise CopadoError(f"Environment '{env_name}' not found via SOQL. Use copado-hx env list to see available environments.")


def _sf_url_rewrite(url: str) -> str:
    url = url.strip().rstrip("/")
    if ".lightning.force.com" in url:
        url = url.replace(".lightning.force.com", ".my.salesforce.com")
    if not url.startswith("https://"):
        url = f"https://{url}"
    return url
