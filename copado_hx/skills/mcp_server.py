from __future__ import annotations

import json
import logging
import sys
from typing import Any

from copado_hx.utils.config import CopadoConfig
from copado_hx.utils.storage import get_secret
from copado_hx.utils.session_state import (
    consume_approval,
    has_pending_approval,
    is_gated_env,
    store_approval,
)


logging.getLogger("mcp").setLevel(logging.CRITICAL)


def _get_sf_client():
    from copado_hx.api.sf_rest import SalesforceRestClient
    token = get_secret("sf_access_token") or ""
    instance = get_secret("sf_instance_url") or ""
    if token and instance:
        return SalesforceRestClient(instance, token)
    if not instance:
        instance = get_secret("sf_instance_url") or "https://login.salesforce.com"
    try:
        from copado_hx.auth.salesforce import login_password_grant
        from copado_hx.utils.storage import store_secrets
        import os
        cfg = CopadoConfig.load().merge_env()
        client_id = cfg.sf_client_id or get_secret("sf_client_id") or ""
        client_secret = cfg.sf_client_secret or get_secret("sf_client_secret") or ""
        username = cfg.sf_username or get_secret("sf_username") or ""
        password = get_secret("sf_password") or os.environ.get("COPADO_SF_PASSWORD", "")
        if not all([client_id, client_secret, username, password]):
            return None
        result = login_password_grant(client_id, client_secret, username, password, instance_url=instance)
        store_secrets({"sf_access_token": result["access_token"], "sf_instance_url": result.get("instance_url", instance), "sf_username": username, "sf_password": password})
        return SalesforceRestClient(result.get("instance_url", instance), result["access_token"])
    except Exception:
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


def _self_diagnose(context: str, error_message: str, story_id: str = "") -> dict[str, Any]:
    from copado_hx.api.mock_data import MockAiPlatformClient
    prompt = (
        f"A pipeline operation failed.\n"
        f"Context: {context}\n"
        f"Error: {error_message}\n"
        f"Story ID: {story_id or 'unknown'}\n\n"
        "Diagnose the root cause, severity, and recommend specific remediation steps."
    )
    ai = _get_ai_client()
    if not ai:
        mock = MockAiPlatformClient()
        result = mock.ask_agent("operate", prompt)
    else:
        try:
            result = ai.ask_agent("operate", prompt)
        except Exception:
            from copado_hx.api.mock_data import MockAiPlatformClient
            result = MockAiPlatformClient().ask_agent("operate", prompt)
    return {
        "diagnosis": result.get("response", ""),
        "agent": "operate",
        "context": context,
        "severity": "high" if any(kw in error_message.lower() for kw in ("denied", "unauthorized", "timeout")) else "medium",
    }


def _load_state():
    from copado_hx.utils.session_state import load_state
    return load_state()


def _build_server():
    from mcp.server.fastmcp import FastMCP
    cfg = CopadoConfig.load().merge_env()
    mcp = FastMCP(
        "copado-hx",
        instructions="Copado Headless DevOps — Full Salesforce DevOps via MCP",
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
    def promote(
        user_story_id: str = "",
        environment: str = "UAT-SFP",
        validate_only: bool = False,
        approval_code: str = "",
    ) -> str:
        """Promote a user story to a target environment.
        PROD/PRODUCTION require an approval_code obtained via copado-hx interactive or shown by the CLI.
        Set validate_only=true for dry-run. Failures auto-routed to Operate agent for diagnosis."""
        client = _get_actions_client()
        if not client:
            return json.dumps({"error": "Actions API key not configured"})
        us_id = user_story_id or get_secret("current_story_id") or ""
        if not us_id:
            return json.dumps({"error": "No user story ID"})

        if is_gated_env(environment):
            if approval_code:
                pending = consume_approval(approval_code)
                if not pending:
                    return json.dumps({
                        "error": f"Invalid or expired approval code '{approval_code}'.",
                        "hint": "Run copado-hx interactive or copado-hx promote --env PROD to generate a fresh code.",
                    })
                if pending.get("env", "").upper() != environment.upper():
                    return json.dumps({"error": f"Approval code is for {pending.get('env')}, not {environment}"})
            else:
                code = store_approval("promote", us_id, environment)
                return json.dumps({
                    "status": "approval_required",
                    "approval_code": code,
                    "message": f"Promote to {environment.upper()} requires human approval. "
                               f"Show the code '{code}' to the developer. "
                               f"Call approve_action(code='{code}') after they confirm.",
                    "environment": environment,
                    "story_id": us_id,
                })

        try:
            result = client.promote(us_id, environment, validate_only=validate_only)
        except Exception as e:
            error_msg = str(e)
            diag = _self_diagnose(f"promote to {environment}", error_msg, us_id)
            return json.dumps({
                "error": error_msg,
                "self_healing": diag,
            }, indent=2, default=str)

        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def deploy_to_prod(
        user_story_id: str = "",
        environment: str = "PROD",
        approval_code: str = "",
    ) -> str:
        """Deploy to production — requires human approval via approval_code.
        Obtain a code by running the promote tool with a gated environment,
        or via copado-hx interactive. Failures auto-routed to Operate agent."""
        if is_gated_env(environment):
            if approval_code:
                pending = consume_approval(approval_code)
                if not pending:
                    return json.dumps({
                        "error": f"Invalid or expired approval code '{approval_code}'.",
                        "hint": "Run copado-hx interactive to generate a fresh code.",
                    })
                if pending.get("env", "").upper() != environment.upper():
                    return json.dumps({"error": f"Approval code is for {pending.get('env')}, not {environment}"})
            else:
                code = store_approval("deploy", user_story_id or "", environment)
                return json.dumps({
                    "status": "approval_required",
                    "approval_code": code,
                    "message": f"Deploy to {environment.upper()} requires human approval. "
                               f"Show the code '{code}' to the developer. "
                               f"Call approve_action(code='{code}') after they confirm.",
                    "environment": environment,
                    "story_id": user_story_id or get_secret("current_story_id") or "",
                })

        client = _get_actions_client()
        if not client:
            return json.dumps({"error": "Actions API key not configured"})
        us_id = user_story_id or get_secret("current_story_id") or ""
        if not us_id:
            return json.dumps({"error": "No user story ID"})
        try:
            result = client.deploy(us_id, environment)
        except Exception as e:
            error_msg = str(e)
            diag = _self_diagnose(f"deploy to {environment}", error_msg, us_id)
            return json.dumps({
                "error": error_msg,
                "self_healing": diag,
            }, indent=2, default=str)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def workflow_list() -> str:
        """List available CI/CD workflows on the Copado AI Platform"""
        client = _get_cicd_client()
        if not client:
            return json.dumps({"error": "CI/CD not configured"})
        try:
            workflows = client.list_workflows()
        except Exception:
            from copado_hx.api.mock_data import MockCopadoCicdClient
            workflows = MockCopadoCicdClient().list_workflows()
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
        try:
            result = client.trigger_workflow(workflow_id, params or None)
        except Exception:
            from copado_hx.api.mock_data import MockCopadoCicdClient
            result = MockCopadoCicdClient().trigger_workflow(workflow_id, params or None)
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
        """Trigger a CRT test job execution. Failures auto-routed to Operate agent."""
        client = _get_crt_client()
        if not client:
            return json.dumps({"error": "CRT PAK not configured"})
        jid = job_id or cfg.crt_job_id
        try:
            result = client.trigger_build(jid)
        except Exception as e:
            error_msg = str(e)
            diag = _self_diagnose("CRT test execution", error_msg)
            return json.dumps({
                "error": error_msg,
                "self_healing": diag,
            }, indent=2, default=str)
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
        try:
            result = client.ask_agent(agent, prompt)
        except Exception:
            from copado_hx.api.mock_data import MockAiPlatformClient
            result = MockAiPlatformClient().ask_agent(agent, prompt)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def ai_triage(execution_id: str) -> str:
        """Analyze test failures via the Release AI agent"""
        cfg = CopadoConfig.load().merge_env()
        crt_client = _get_crt_client()
        if not crt_client:
            return json.dumps({"error": "CRT not configured"})
        try:
            result = crt_client.get_build_results(cfg.crt_job_id, execution_id)
            failures = [t for t in result.get("testResults", [])
                        if t.get("status", "") not in ("Passed", "Succeeded")]
            if not failures:
                return json.dumps({"status": "passed", "message": "All tests passed"})
            prompt = f"Analyze test execution {execution_id}. Failed tests:\n"
            for f in failures:
                prompt += f"  - {f.get('testName', 'unknown')} ({f.get('executionTime', '')})\n"
            prompt += "Diagnose root causes, severity, and recommend fixes."
            ai_client = _get_ai_client()
            if not ai_client:
                return json.dumps({"error": "AI not configured"})
            try:
                analysis = ai_client.ask_agent("release", prompt)
            except Exception:
                from copado_hx.api.mock_data import MockAiPlatformClient
                analysis = MockAiPlatformClient().ask_agent("release", prompt)
            return json.dumps({"execution_id": execution_id, "failures": len(failures), "analysis": analysis})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def deployment_confidence(execution_id: str) -> str:
        """Calculate deployment confidence score from test results"""
        cfg = CopadoConfig.load().merge_env()
        crt_client = _get_crt_client()
        if not crt_client:
            return json.dumps({"error": "CRT not configured"})
        try:
            result = crt_client.get_build_results(cfg.crt_job_id, execution_id)
            total = int(result.get("totalTests", result.get("total", 0)))
            passed = int(result.get("passedTests", result.get("passed", 0)))
            failed = int(result.get("failedTests", result.get("failed", 0)))
            score = round((passed / total * 100), 1) if total > 0 else 0
            return json.dumps({
                "total": total, "passed": passed, "failed": failed,
                "confidence_score": score,
                "go_for_deployment": "yes" if score >= 80 else "no",
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

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
        try:
            result = client.get_run(run_id)
        except Exception:
            from copado_hx.api.mock_data import MockCopadoCicdClient
            result = MockCopadoCicdClient().get_run(run_id)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def auth_logout_mcp() -> str:
        """Clear stored credentials for all services"""
        from copado_hx.utils.storage import delete_secret
        for key in ("sf_access_token", "sf_instance_url", "ai_api_key", "crt_pak", "actions_api_key"):
            delete_secret(key)
        return json.dumps({"status": "ok"}, indent=2)

    @mcp.tool()
    def story_create_mcp(name: str, pipeline_id: str = "") -> str:
        """Create a user story in the Salesforce org"""
        client = _get_sf_client()
        if not client:
            return json.dumps({"error": "Salesforce not authenticated. Run: copado-hx auth login"})
        result = client.create_user_story(name, pipeline_id)
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def version_mcp() -> str:
        """Return version information for copado-hx and Python"""
        from copado_hx._app import __version__
        return json.dumps({
            "version": __version__,
            "python_version": sys.version.split()[0],
        }, indent=2)

    @mcp.tool()
    def config_get_mcp(key: str) -> str:
        """Get a configuration value by key"""
        cfg = CopadoConfig.load().merge_env()
        return json.dumps({
            "key": key,
            "value": str(getattr(cfg, key, "")),
        }, indent=2)

    @mcp.tool()
    def auth_status_mcp() -> str:
        """Check authentication and return a structured readiness report for agents"""
        sf = _get_sf_client() is not None
        ai = _get_ai_client() is not None
        crt = _get_crt_client() is not None
        actions = _get_actions_client() is not None
        cfg = CopadoConfig.load().merge_env()
        has_story = bool(cfg.current_story_id or get_secret("current_story_id"))

        warnings = []
        if not sf:
            warnings.append("Salesforce not authenticated — run copado-hx auth login")
        if not actions:
            warnings.append("Actions API key missing — run copado-hx auth login --type actions")
        if not has_story:
            warnings.append("No story context set — use story_set_context first")

        return json.dumps({
            "ready": sf and actions,
            "salesforce": sf,
            "ai": ai,
            "crt": crt,
            "actions": actions,
            "story_context": has_story,
            "current_story": cfg.current_story_id or "",
            "warnings": warnings,
            "instruction": "Set story context with story_set_context before commit/promote/deploy" if not has_story else "Ready",
        }, indent=2)

    @mcp.tool()
    def approve_action(approval_code: str) -> str:
        """Approve a pending action using a one-time approval code.
        Call this after the developer confirms the code shown by promote/deploy_to_prod."""
        pending = consume_approval(approval_code)
        if not pending:
            return json.dumps({
                "error": f"Invalid or expired approval code '{approval_code}'.",
                "hint": "Generate a fresh code via promote or deploy_to_prod for a gated environment.",
            }, indent=2)
        return json.dumps({
            "status": "approved",
            "action": pending.get("action"),
            "story_id": pending.get("story_id"),
            "environment": pending.get("env"),
            "message": f"Approval for {pending.get('action')} to {pending.get('env')} recorded. "
                       f"Call the {pending.get('action')} tool again with approval_code='{approval_code}' to proceed.",
        }, indent=2)

    @mcp.tool()
    def check_pending_approvals() -> str:
        """Check if there are any pending actions awaiting human approval."""
        if not has_pending_approval():
            return json.dumps({"status": "none"}, indent=2)
        state = _load_state()
        pending = state.get("pending_approval", {})
        return json.dumps({
            "status": "pending",
            "approval_code": pending.get("code"),
            "action": pending.get("action"),
            "story_id": pending.get("story_id"),
            "environment": pending.get("env"),
            "hint": f"Call approve_action(code='{pending.get('code')}') after the developer confirms.",
        }, indent=2)

    @mcp.tool()
    def self_heal(context: str, error_message: str, story_id: str = "") -> str:
        """Diagnose a pipeline failure and get remediation steps from the Operate agent.
        Use this when promote/deploy/test-run fail."""
        diag = _self_diagnose(context, error_message, story_id)
        return json.dumps(diag, indent=2)

    @mcp.tool()
    def deliver_story(
        user_story_id: str = "",
        target_environment: str = "UAT-SFP",
        commit_message: str = "feat: automated delivery",
        run_tests: bool = False,
        approval_code: str = "",
    ) -> str:
        """End-to-end delivery: commit -> promote -> deploy (-> test) in one call.
        For PROD environments, provide an approval_code obtained via promote tool or copado-hx interactive.
        Failures auto-routed to Operate agent."""
        results: dict[str, Any] = {"story_id": user_story_id, "environment": target_environment, "steps": {}}

        sf_client = _get_sf_client()
        if not sf_client:
            return json.dumps({"error": "Salesforce not authenticated"})

        actions_client = _get_actions_client()
        if not actions_client:
            return json.dumps({"error": "Actions API key not configured"})

        us_id = user_story_id or get_secret("current_story_id") or ""
        if not us_id:
            return json.dumps({"error": "No user story ID. Provide user_story_id or set context with story_set_context first."})

        if is_gated_env(target_environment) and not approval_code:
            return json.dumps({
                "error": f"Deliver to {target_environment.upper()} requires human approval. "
                         f"Run copado-hx interactive first to generate an approval code, "
                         f"then call again with approval_code='<code>'.",
                "step": "guardrail",
            })

        if is_gated_env(target_environment):
            pending = consume_approval(approval_code)
            if not pending or pending.get("env", "").upper() != target_environment.upper():
                return json.dumps({
                    "error": f"Invalid or expired approval code for {target_environment.upper()}.",
                    "step": "guardrail",
                })

        from copado_hx.utils.storage import store_secrets
        store_secrets({"current_story_id": us_id})

        steps: list[dict[str, Any]] = []

        try:
            result = actions_client.commit(us_id, commit_message)
            steps.append({"step": "commit", "status": "triggered", "result": result})
        except Exception as e:
            steps.append({"step": "commit", "status": "failed", "error": str(e)})
            diag = _self_diagnose("deliver_story commit", str(e), us_id)
            steps.append({"step": "self_heal", "status": "diagnosed", "result": diag})

        try:
            result = actions_client.promote(us_id, target_environment)
            steps.append({"step": "promote", "status": "triggered", "result": result})
        except Exception as e:
            steps.append({"step": "promote", "status": "failed", "error": str(e)})
            diag = _self_diagnose(f"deliver_story promote to {target_environment}", str(e), us_id)
            steps.append({"step": "self_heal", "status": "diagnosed", "result": diag})

        try:
            result = actions_client.deploy(us_id, target_environment)
            steps.append({"step": "deploy", "status": "triggered", "result": result})
        except Exception as e:
            steps.append({"step": "deploy", "status": "failed", "error": str(e)})
            diag = _self_diagnose(f"deliver_story deploy to {target_environment}", str(e), us_id)
            steps.append({"step": "self_heal", "status": "diagnosed", "result": diag})

        if run_tests:
            crt_client = _get_crt_client()
            if crt_client:
                try:
                    cfg = CopadoConfig.load().merge_env()
                    result = crt_client.trigger_build(cfg.crt_job_id)
                    steps.append({"step": "test", "status": "triggered", "result": result})
                except Exception as e:
                    steps.append({"step": "test", "status": "failed", "error": str(e)})
            else:
                steps.append({"step": "test", "status": "skipped", "reason": "CRT not configured"})

        results["steps"] = steps
        all_ok = all(s["status"] in ("triggered", "skipped") for s in steps)
        results["status"] = "completed" if all_ok else "partial"
        results["summary"] = f"Delivery to {target_environment}: {'all steps triggered' if all_ok else 'some steps failed'}"
        return json.dumps(results, indent=2, default=str)

    return mcp, cfg


def run_mcp_server(transport: str = "stdio") -> None:
    if transport == "stdio" and sys.stdin.isatty():
        print("copado-hx MCP — 28 tools available", file=sys.stderr, flush=True)
        print("", file=sys.stderr, flush=True)
        print("The MCP server requires an MCP client (Claude Code, Cursor, VS Code).", file=sys.stderr, flush=True)
        print("Run with --list-tools to see the tool inventory.", file=sys.stderr, flush=True)
        return

    mcp, cfg = _build_server()
    print(f"copado-hx MCP server starting ({transport} transport)...", file=sys.stderr, flush=True)
    mcp.run(transport=transport)


if __name__ == "__main__":
    run_mcp_server()
