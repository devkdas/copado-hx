from __future__ import annotations

import json
import sys

from copado_hx.utils.config import CopadoConfig
from copado_hx.utils.storage import get_secret


def _get_sf_client():
    from copado_hx.api.sf_rest import SalesforceRestClient
    token = get_secret("sf_access_token") or ""
    instance = get_secret("sf_instance_url") or ""
    if token and instance:
        return SalesforceRestClient(instance, token)
    return None


def _get_actions_client():
    from copado_hx.api.actions import ActionsApiClient
    cfg = CopadoConfig.load().merge_env()
    api_key = cfg.actions_api_key or get_secret("actions_api_key") or ""
    if api_key:
        return ActionsApiClient(api_key, cfg.actions_base_url)
    return None


def _get_cicd_client():
    from copado_hx.api.cicd import CopadoCicdClient
    cfg = CopadoConfig.load().merge_env()
    api_key = cfg.ai_api_key or get_secret("ai_api_key") or ""
    if api_key:
        return CopadoCicdClient(api_key, cfg.ai_base_url, cfg.ai_org_id, cfg.ai_workspace_id)
    return None


def _get_crt_client():
    from copado_hx.api.crt import CrtClient
    cfg = CopadoConfig.load().merge_env()
    pak = cfg.crt_pak or get_secret("crt_pak") or ""
    if pak:
        return CrtClient(cfg.crt_base_url, pak, cfg.crt_org_id, cfg.crt_project_id)
    return None


def _get_ai_client():
    from copado_hx.api.ai import AiPlatformClient
    cfg = CopadoConfig.load().merge_env()
    api_key = cfg.ai_api_key or get_secret("ai_api_key") or ""
    if api_key:
        return AiPlatformClient(api_key, cfg.ai_base_url, cfg.ai_org_id, cfg.ai_workspace_id)
    return None


def run_mcp_server(transport: str = "stdio") -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("MCP dependencies not available. Install: pip install mcp", file=sys.stderr)
        sys.exit(1)

    cfg = CopadoConfig.load().merge_env()
    mcp = FastMCP(
        "copado-hx",
        description="Copado Headless DevOps — Full Salesforce DevOps via MCP",
        version="1.0.0",
    )

    @mcp.tool()
    def auth_status() -> str:
        """Check authentication status across all services"""
        sf = _get_sf_client() is not None
        ai = _get_ai_client() is not None
        crt = _get_crt_client() is not None
        actions = _get_actions_client() is not None
        return json.dumps({
            "salesforce_authenticated": sf,
            "ai_configured": ai,
            "crt_configured": crt,
            "actions_configured": actions,
        }, indent=2)

    @mcp.tool()
    def story_list(pipeline: str = "", status: str = "") -> str:
        """List user stories from the Salesforce org"""
        client = _get_sf_client()
        if not client:
            return json.dumps({"error": "Salesforce not authenticated. Run: copado-hx auth login"})
        p = pipeline if pipeline else None
        s = status if status else None
        stories = client.get_user_stories(pipeline=p, status=s)
        return json.dumps(stories, indent=2, default=str)

    @mcp.tool()
    def story_show(story_id: str) -> str:
        """Get detailed information about a specific user story"""
        client = _get_sf_client()
        if not client:
            return json.dumps({"error": "Salesforce not authenticated"})
        story = client.get_user_story(story_id)
        return json.dumps(story, indent=2, default=str) if story else json.dumps({"error": "Not found"})

    @mcp.tool()
    def story_set_context(story_id: str) -> str:
        """Set a user story as the current working context"""
        from copado_hx.utils.storage import store_secrets
        client = _get_sf_client()
        if not client:
            return json.dumps({"error": "Salesforce not authenticated"})
        story = client.get_user_story(story_id)
        if not story:
            return json.dumps({"error": f"Story {story_id} not found"})
        store_secrets({"current_story_id": story_id, "current_story_name": story.get("Name", "")})
        return json.dumps({"status": "ok", "story_id": story_id, "name": story.get("Name", "")})

    @mcp.tool()
    def commit(user_story_id: str = "", message: str = "feat: update") -> str:
        """Commit metadata changes — triggers Actions API RunJobTemplate"""
        client = _get_actions_client()
        if not client:
            return json.dumps({"error": "Actions API key not configured"})
        us_id = user_story_id or get_secret("current_story_id") or ""
        if not us_id:
            return json.dumps({"error": "No user story ID"})
        result = client.commit(us_id, message)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def promote(user_story_id: str = "", environment: str = "UAT") -> str:
        """Promote a user story — triggers Actions API RunJobTemplate"""
        client = _get_actions_client()
        if not client:
            return json.dumps({"error": "Actions API key not configured"})
        us_id = user_story_id or get_secret("current_story_id") or ""
        if not us_id:
            return json.dumps({"error": "No user story ID"})
        result = client.promote(us_id, environment)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def deploy_to_prod(user_story_id: str = "", environment: str = "PROD") -> str:
        """Deploy to production — triggers Actions API RunJobTemplate"""
        client = _get_actions_client()
        if not client:
            return json.dumps({"error": "Actions API key not configured"})
        us_id = user_story_id or get_secret("current_story_id") or ""
        if not us_id:
            return json.dumps({"error": "No user story ID"})
        result = client.deploy(us_id, environment)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def workflow_list() -> str:
        """List available CI/CD workflows on the Copado AI Platform"""
        client = _get_cicd_client()
        if not client:
            return json.dumps({"error": "CI/CD not configured"})
        workflows = client.list_workflows()
        return json.dumps(workflows, indent=2, default=str)

    @mcp.tool()
    def workflow_run(workflow_id: str, parameters: str = "{}") -> str:
        """Trigger a CI/CD workflow with JSON parameters"""
        client = _get_cicd_client()
        if not client:
            return json.dumps({"error": "CI/CD not configured"})
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in parameters"})
        result = client.trigger_workflow(workflow_id, params or None)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def list_test_jobs() -> str:
        """List available CRT test jobs"""
        client = _get_crt_client()
        if not client:
            return json.dumps({"error": "CRT PAK not configured"})
        jobs = client.list_jobs_detailed()
        return json.dumps(jobs, indent=2, default=str)

    @mcp.tool()
    def run_test(job_id: str = "") -> str:
        """Trigger a CRT test job execution"""
        client = _get_crt_client()
        if not client:
            return json.dumps({"error": "CRT PAK not configured"})
        jid = job_id or cfg.crt_job_id
        result = client.trigger_build(jid)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def test_status(execution_id: str, job_id: str = "") -> str:
        """Get execution status of a CRT test run"""
        client = _get_crt_client()
        if not client:
            return json.dumps({"error": "CRT PAK not configured"})
        jid = job_id or cfg.crt_job_id
        result = client.get_build_status(jid, execution_id)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def test_results(execution_id: str, job_id: str = "") -> str:
        """Retrieve CRT test results"""
        client = _get_crt_client()
        if not client:
            return json.dumps({"error": "CRT PAK not configured"})
        jid = job_id or cfg.crt_job_id
        result = client.get_build_results(jid, execution_id)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def ai_ask_agent(agent: str, prompt: str) -> str:
        """Ask one of 5 Copado AI specialist agents: plan, build, test, release, operate"""
        from copado_hx.api.ai import AiPlatformClient
        if agent not in AiPlatformClient.AGENTS:
            return json.dumps({"error": f"Unknown agent: {agent}. Valid: plan, build, test, release, operate"})
        client = _get_ai_client()
        if not client:
            return json.dumps({"error": "AI API key not configured"})
        result = client.ask_agent(agent, prompt)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def list_environments() -> str:
        """List available pipeline environments"""
        client = _get_sf_client()
        if not client:
            return json.dumps({"error": "Salesforce not authenticated"})
        envs = client.get_environments()
        return json.dumps(envs, indent=2, default=str)

    @mcp.tool()
    def list_pipelines() -> str:
        """List available pipelines"""
        client = _get_sf_client()
        if not client:
            return json.dumps({"error": "Salesforce not authenticated"})
        pipelines = client.get_pipelines()
        return json.dumps(pipelines, indent=2, default=str)

    @mcp.tool()
    def check_pipeline_status(run_id: str) -> str:
        """Check the status of a workflow run"""
        client = _get_cicd_client()
        if not client:
            return json.dumps({"error": "CI/CD not configured"})
        result = client.get_run(run_id)
        return json.dumps(result, indent=2, default=str)

    print(f"copado-hx MCP server starting ({transport} transport)...", file=sys.stderr, flush=True)
    mcp.run(transport=transport)


if __name__ == "__main__":
    run_mcp_server()
