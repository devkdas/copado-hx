from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.prompt import Prompt, Confirm

from copado_hx.api.actions import ActionsApiClient
from copado_hx.api.ai import AiPlatformClient
from copado_hx.api.cicd import CopadoCicdClient
from copado_hx.api.crt import CrtClient
from copado_hx.api.sf_rest import SalesforceRestClient
from copado_hx.auth.salesforce import login_web
from copado_hx.utils.config import CopadoConfig
from copado_hx.utils.output import (
    output_result,
    print_error,
    print_json,
    print_markdown,
    print_panel,
    print_success,
    print_table,
    print_warning,
)
from copado_hx.utils.storage import (
    store_secrets,
    get_secret,
    delete_secret,
    get_all_secrets,
    clear_secrets,
)

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
    if _sf_client is None:
        token = get_secret("sf_access_token")
        instance = get_secret("sf_instance_url")
        if not token or not instance:
            print_error("Salesforce not authenticated. Run: copado-hx auth login")
            raise typer.Exit(1)
        _sf_client = SalesforceRestClient(instance, token)
    return _sf_client


def get_cicd_client() -> CopadoCicdClient:
    global _cicd_client
    if _cicd_client is None:
        cfg = get_config()
        api_key = cfg.ai_api_key or get_secret("ai_api_key") or ""
        org_id = cfg.ai_org_id or get_secret("ai_org_id") or ""
        ws_id = cfg.ai_workspace_id or get_secret("ai_workspace_id") or ""
        if not api_key:
            print_error("AI API key not configured. Set COPADO_AI_API_KEY env var or run: copado-hx auth login")
            raise typer.Exit(1)
        if not org_id or not ws_id:
            print_error("Org/Workspace IDs not configured.")
            raise typer.Exit(1)
        _cicd_client = CopadoCicdClient(api_key, cfg.ai_base_url, org_id, ws_id)
    return _cicd_client


def get_actions_client() -> ActionsApiClient:
    global _actions_client
    if _actions_client is None:
        cfg = get_config()
        api_key = cfg.actions_api_key or get_secret("actions_api_key") or ""
        if not api_key:
            print_error("Actions API key not configured. Set COPADO_ACTIONS_API_KEY env var.")
            raise typer.Exit(1)
        _actions_client = ActionsApiClient(api_key, cfg.actions_base_url)
    return _actions_client


def get_crt_client() -> CrtClient:
    global _crt_client
    if _crt_client is None:
        cfg = get_config()
        pak = cfg.crt_pak or get_secret("crt_pak") or ""
        if not pak:
            print_error("CRT PAK not configured. Set COPADO_CRT_PAK env var or run: copado-hx auth login")
            raise typer.Exit(1)
        _crt_client = CrtClient(cfg.crt_base_url, pak, cfg.crt_org_id, cfg.crt_project_id)
    return _crt_client


def get_ai_client() -> AiPlatformClient:
    global _ai_client
    if _ai_client is None:
        cfg = get_config()
        api_key = cfg.ai_api_key or get_secret("ai_api_key") or ""
        if not api_key:
            print_error("AI API key not configured. Set COPADO_AI_API_KEY env var.")
            raise typer.Exit(1)
        _ai_client = AiPlatformClient(api_key, cfg.ai_base_url, cfg.ai_org_id, cfg.ai_workspace_id)
    return _ai_client


# ─── AUTH COMMANDS ────────────────────────────────────────────────────────────

@auth_app.command("login")
def auth_login(
    token: Optional[str] = typer.Option(None, "--token", help="AI API key for CI environments"),
    crt_pak: Optional[str] = typer.Option(None, "--crt-pak", help="CRT Platform Access Key"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Authenticate with all Copado services"""
    cfg = get_config()

    if token:
        store_secrets({"ai_api_key": token})
        if json_output:
            print_json({"status": "ok", "service": "ai"})
        else:
            print_success("AI API key stored securely")
        return

    if crt_pak:
        store_secrets({"crt_pak": crt_pak})
        if json_output:
            print_json({"status": "ok", "service": "crt"})
        else:
            print_success("CRT PAK stored securely")
        return

    sf_configured = bool(get_secret("sf_access_token"))
    ai_configured = bool(get_secret("ai_api_key") or cfg.ai_api_key)
    crt_configured = bool(get_secret("crt_pak") or cfg.crt_pak)
    actions_configured = bool(get_secret("actions_api_key") or cfg.actions_api_key)

    if not sf_configured:
        print_panel("Step 1/3: Salesforce Authentication",
                     "A browser will open for Salesforce login.\n"
                     "Log in and approve the Connected App 'Copado_CLI'.")
        try:
            result = login_web()
            store_secrets({
                "sf_access_token": result["access_token"],
                "sf_instance_url": result["instance_url"],
            })
            print_success("Salesforce authenticated successfully")
            global _sf_client
            _sf_client = None
        except Exception as e:
            print_error(f"Salesforce auth failed: {e}")
            raise typer.Exit(1)

    if not ai_configured:
        ai_key = Prompt.ask("AI API key (from Copado AI Platform profile)", password=True, default="")
        if ai_key:
            store_secrets({"ai_api_key": ai_key})
            print_success("AI API key stored")
        else:
            print_warning("AI key not provided — AI agent commands will not work")

    if not crt_configured:
        crt_key = Prompt.ask("CRT PAK (from Copado Robotic Testing)", default="", password=True)
        if crt_key:
            store_secrets({"crt_pak": crt_key})

    if not actions_configured:
        actions_key = Prompt.ask("Actions API key (from Copado Account Summary > API Key)", default="", password=True)
        if actions_key:
            store_secrets({"actions_api_key": actions_key})

    if json_output:
        print_json({
            "salesforce_authenticated": True,
            "ai_configured": bool(get_secret("ai_api_key") or cfg.ai_api_key),
            "crt_configured": bool(get_secret("crt_pak") or cfg.crt_pak),
        })
    else:
        print_success("All services configured!")


@auth_app.command("status")
def auth_status(json_output: bool = typer.Option(False, "--json")):
    """Show current authenticated org and user"""
    secrets = get_all_secrets()
    has_sf = bool(secrets.get("sf_access_token"))
    has_ai = bool(secrets.get("ai_api_key") or get_config().ai_api_key)
    has_crt = bool(secrets.get("crt_pak") or get_config().crt_pak)
    has_actions = bool(secrets.get("actions_api_key") or get_config().actions_api_key)

    if json_output:
        print_json({
            "salesforce_authenticated": has_sf,
            "ai_configured": has_ai,
            "crt_configured": has_crt,
            "actions_configured": has_actions,
            "instance": get_config().cicd_instance,
        })
        return

    print_panel("Authentication Status", f"""
[bold]Salesforce (Stories):[/bold] {'Authenticated' if has_sf else 'Not authenticated'}
[bold]AI Platform:[/bold]         {'Configured' if has_ai else 'Not configured'}
[bold]CRT (Testing):[/bold]       {'Configured' if has_crt else 'Not configured'}
[bold]Actions API (CI/CD):[/bold] {'Configured' if has_actions else 'Not configured'}
[dim]Instance: {get_config().cicd_instance}[/dim]
    """)
    return


@auth_app.command("logout")
def auth_logout(
    all: bool = typer.Option(False, "--all", help="Clear all stored credentials"),
):
    """Logout and clear stored credentials"""
    if all:
        clear_secrets()
        print_success("All credentials cleared")
    else:
        delete_secret("sf_access_token")
        delete_secret("sf_instance_url")
        print_success("Salesforce session cleared")


# ─── STORY COMMANDS ───────────────────────────────────────────────────────────

@story_app.command("list")
def story_list(
    pipeline: Optional[str] = typer.Option(None, "--pipeline", "-p", help="Filter by pipeline name"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (e.g. 'In Progress')"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List user stories"""
    client = get_sf_client()
    try:
        stories = client.get_user_stories(pipeline=pipeline, status=status)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(stories)
        return

    if not stories:
        print_warning("No user stories found")
        return

    rows = []
    for s in stories:
        rows.append([
            s.get("Id", ""),
            s.get("Name", ""),
            s.get("copado__Status__c", ""),
            s.get("copado__User_Story_Title__c", ""),
        ])
    print_table("User Stories", ["ID", "Name", "Status", "Title"], rows)


@story_app.command("show")
def story_show(
    story_id: Optional[str] = typer.Argument(None, help="User story ID (uses context if not provided)"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Show current user story details"""
    if not story_id:
        story_id = get_secret("current_story_id")
        if not story_id:
            story_id = Prompt.ask("User Story ID")
    client = get_sf_client()
    try:
        story = client.get_user_story(story_id)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not story:
        print_error(f"User story {story_id} not found")
        raise typer.Exit(1)

    if json_output:
        print_json(story)
        return

    print_panel(f"User Story: {story.get('Name', '')}", f"""
[bold]ID:[/bold]          {story.get('Id', '')}
[bold]Status:[/bold]      {story.get('copado__Status__c', '')}
[bold]Title:[/bold]       {story.get('copado__User_Story_Title__c', '')}
    """)


@story_app.command("set")
def story_set(
    story_id: str = typer.Argument(..., help="User story ID to set as working context"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Set working context (like git checkout)"""
    client = get_sf_client()
    try:
        story = client.get_user_story(story_id)
    except Exception as e:
        msg = str(e)
        if "invalid ID" in msg.lower():
            print_error(f"Invalid story ID: {story_id}. Use a valid 18-char ID or US-xxxxx name. Run 'copado-hx story list'.")
        else:
            print_error(msg)
        raise typer.Exit(1)

    if not story:
        print_error(f"User story {story_id} not found. Run 'copado-hx story list' to see available stories.")
        raise typer.Exit(1)

    store_secrets({"current_story_id": story_id, "current_story_name": story.get("Name", "")})
    if json_output:
        print_json({"status": "ok", "story_id": story_id, "name": story.get("Name", "")})
        return
    print_success(f"Working context set to: {story.get('Name', story_id)}")


@story_app.command("create")
def story_create(
    title: str = typer.Option(..., "--title", "-t", help="User story title"),
    pipeline: Optional[str] = typer.Option(None, "--pipeline", "-p", help="Pipeline ID"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Create a new user story"""
    client = get_sf_client()
    pipeline_id = pipeline or get_config().default_pipeline_id
    if not pipeline_id:
        pipeline_id = Prompt.ask("Pipeline ID")
    try:
        result = client.create_user_story(title, pipeline_id)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        story_id = result.get("id", result.get("Id", ""))
        print_success(f"User story created: {story_id}")
        store_secrets({"current_story_id": story_id, "current_story_name": title})


# ─── COMMIT ──────────────────────────────────────────────────────────────────

@app.command()
def commit(
    message: str = typer.Option("", "--message", "-m", help="Commit message"),
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Commit metadata changes from the current user story context"""
    sid = story_id or get_secret("current_story_id")
    if not sid:
        print_error("No user story context set. Use 'copado-hx story set <id>' or --us flag.")
        raise typer.Exit(1)

    if not message:
        story_name = get_secret("current_story_name") or sid
        message = Prompt.ask("Commit message", default=f"feat: update {story_name}")

    client = get_actions_client()
    try:
        result = client.commit(sid, message)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        job_id = result.get("Id", result.get("id", ""))
        print_success(f"Commit triggered: JE={job_id}")
        print_success(f"Message: {message}")


# ─── PROMOTE ─────────────────────────────────────────────────────────────────

@app.command()
def promote(
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    environment: str = typer.Option("UAT", "--env", "-e", help="Target environment"),
    validate: bool = typer.Option(False, "--validate", help="Validation-only deployment"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Promote a user story to the next environment"""
    sid = story_id or get_secret("current_story_id")
    if not sid:
        print_error("No user story context set.")
        raise typer.Exit(1)

    client = get_actions_client()
    try:
        result = client.promote(sid, environment, validate_only=validate)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        action = "Validation" if validate else "Promotion"
        print_success(f"{action} to {environment} triggered")
        job_id = result.get("Id", result.get("id", ""))
        if job_id:
            print_success(f"Job execution: {job_id}")


# ─── DEPLOY ──────────────────────────────────────────────────────────────────

@app.command()
def deploy(
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    environment: str = typer.Option("PROD", "--env", "-e", help="Target environment"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Execute a deployment to production (requires approval gate confirmation)"""
    if environment.upper() == "PROD" and not force:
        confirmed = Confirm.ask(
            "[red]You are about to deploy to PRODUCTION. Continue?[/red]",
            default=False,
        )
        if not confirmed:
            print_warning("Deployment cancelled")
            raise typer.Exit(0)

    sid = story_id or get_secret("current_story_id")
    if not sid:
        print_error("No user story context set.")
        raise typer.Exit(1)

    client = get_actions_client()
    try:
        result = client.deploy(sid, environment)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        job_id = result.get("Id", result.get("id", ""))
        print_success(f"Deployment to {environment} triggered: JE={job_id}")


# ─── VALIDATE ────────────────────────────────────────────────────────────────

@app.command()
def validate(
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    environment: str = typer.Option("UAT", "--env", "-e", help="Target environment"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Run a validation-only deployment"""
    sid = story_id or get_secret("current_story_id")
    if not sid:
        print_error("No user story context set.")
        raise typer.Exit(1)

    client = get_actions_client()
    try:
        result = client.promote(sid, environment, validate_only=True)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        print_success(f"Validation deployment to {environment} triggered")
        job_id = result.get("Id", result.get("id", ""))
        if job_id:
            print_success(f"Job execution: {job_id}")


# ─── STATUS ──────────────────────────────────────────────────────────────────

@app.command()
def status(
    job: Optional[str] = typer.Option(None, "--job", "-j", help="Job execution ID to monitor"),
    run: Optional[str] = typer.Option(None, "--run", "-r", help="Workflow run ID to monitor"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Live-polling terminal dashboard"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Show pipeline status: workflow runs, promotions, deployments, quality gates"""
    client = get_cicd_client()

    if job:
        sf = get_sf_client()
        try:
            records = sf.query(
                f"SELECT Id, Name, copado__Status__c, LastModifiedDate "
                f"FROM copado__JobExecution__c WHERE Id = '{job}'"
            )
            result = records[0] if records else {}
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)

        if json_output:
            print_json(result)
        else:
            status_val = result.get("copado__Status__c", "Unknown")
            print_panel(f"Job Execution: {job}", f"[bold]Status:[/bold] {status_val}")

        if watch:
            with typer.progressbar(length=100, label="Waiting for completion...") as pb:
                for i in range(30):
                    time.sleep(10)
                    try:
                        records = sf.query(
                            f"SELECT Id, Name, copado__Status__c "
                            f"FROM copado__JobExecution__c WHERE Id = '{job}'"
                        )
                        result = records[0] if records else {}
                    except Exception:
                        break
                    s = result.get("copado__Status__c", "")
                    if s in ("Completed", "Failed", "Error"):
                        break
                    pb.update(10)
            style = "green" if s == "Completed" else "red"
            print_panel(f"Job Execution: {job}", f"[bold]Final Status:[/bold] [{style}]{s}[/{style}]")
        return

    if run:
        try:
            result = client.get_run(run)
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)

        if json_output:
            print_json(result)
        else:
            status_val = result.get("status", "Unknown")
            print_panel(f"Workflow Run: {run}", f"[bold]Status:[/bold] {status_val}")

        if watch:
            with typer.progressbar(length=100, label="Waiting for completion...") as pb:
                for i in range(30):
                    time.sleep(10)
                    try:
                        result = client.get_run(run)
                    except Exception:
                        break
                    s = result.get("status", "")
                    if s in ("completed", "failed", "succeeded"):
                        break
                    pb.update(10)
            print_success(f"Final status: {s}")
        return

    sf = get_sf_client()
    try:
        envs = sf.get_environments()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json({"environments": envs})
    else:
        rows = [[e.get("Id", ""), e.get("Name", ""), e.get("copado__Type__c", "")] for e in envs]
        print_table("Pipeline Environments", ["ID", "Name", "Type"], rows)


# ─── WORKFLOW COMMANDS ─────────────────────────────────────────────────────────

@wf_app.command("list")
def workflow_list(
    json_output: bool = typer.Option(False, "--json"),
):
    """List available CI/CD workflows on the Copado AI Platform"""
    client = get_cicd_client()
    try:
        workflows = client.list_workflows()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(workflows)
    else:
        rows = [[w.get("id", "")[:12], w.get("title", ""), str(len(w.get("nodes", [])))] for w in workflows]
        print_table("Available Workflows", ["ID", "Title", "Nodes"], rows)


@wf_app.command("run")
def workflow_run(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    param: Optional[list[str]] = typer.Option(None, "--param", "-p", help="Parameters as key=value pairs"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Trigger a CI/CD workflow by ID with optional parameters"""
    parameters = {}
    if param:
        for p in param:
            if "=" in p:
                k, v = p.split("=", 1)
                parameters[k] = v
            else:
                print_warning(f"Ignoring param without '=': {p}")

    client = get_cicd_client()
    try:
        result = client.trigger_workflow(workflow_id, parameters or None)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        run_id = result.get("id", result.get("run_id", "N/A"))
        print_success(f"Workflow run triggered: {run_id}")


# ─── TEST COMMANDS ───────────────────────────────────────────────────────────

@test_app.command("list")
def test_list(
    json_output: bool = typer.Option(False, "--json"),
):
    """List available test suites and jobs"""
    client = get_crt_client()
    try:
        jobs = client.list_jobs_detailed()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(jobs)
        return

    if not jobs:
        print_warning("No test jobs found")
        return

    rows = []
    for j in jobs:
        jid = j.get("id", j.get("jobId", ""))
        jname = j.get("name", j.get("jobName", ""))
        jtype = j.get("type", j.get("jobType", ""))
        rows.append([str(jid), str(jname), str(jtype)])
    print_table("Available Test Jobs", ["Job ID", "Name", "Type"], rows)


@test_app.command("run")
def test_run(
    suite: Optional[str] = typer.Option(None, "--suite", help="Test suite ID (resolves to jobId)"),
    job: Optional[str] = typer.Option(None, "--job", "-j", help="CRT job ID"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Trigger a CRT test suite or job execution"""
    job_id = job or suite or get_config().crt_job_id
    if not job_id:
        job_id = Prompt.ask("CRT job ID")
        if not job_id:
            print_error("Job ID required")
            raise typer.Exit(1)

    client = get_crt_client()
    try:
        result = client.trigger_build(job_id)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        data = result.get("data", result)
        build_id = data.get("id", data.get("buildId", ""))
        print_success("Test execution triggered")
        print_success(f"Execution ID: {build_id}")
        print_success("Run 'copado-hx test status --execution <id>' to check status")


@test_app.command("status")
def test_status(
    execution_id: str = typer.Option(..., "--execution", "-e", help="Execution ID"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Poll until completion"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Poll execution status of a CRT test run"""
    job_id = get_config().crt_job_id
    client = get_crt_client()

    if watch:
        with typer.progressbar(length=100, label="Waiting for test completion...") as pb:
            for i in range(60):
                try:
                    result = client.get_build_status(job_id, execution_id)
                except Exception:
                    time.sleep(10)
                    pb.update(2)
                    continue
                status_val = result.get("status", result.get("buildStatus", ""))
                if json_output:
                    pass
                else:
                    pb.label = f"Status: {status_val}"
                if status_val in ("Succeeded", "Completed", "Passed", "Failed", "Error", "Cancelled"):
                    break
                time.sleep(10)
                pb.update(2)
    else:
        try:
            result = client.get_build_status(job_id, execution_id)
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        status_val = result.get("status", result.get("buildStatus", "Unknown"))
        style = "green" if status_val in ("Succeeded", "Completed", "Passed") else "red"
        print_panel(f"Test Execution: {execution_id}", f"[bold]Status:[/bold] [{style}]{status_val}[/{style}]")


@test_app.command("results")
def test_results(
    execution_id: str = typer.Option(..., "--execution", "-e", help="Execution ID"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, pdf, junit"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Retrieve test results (JUnit-compatible output)"""
    job_id = get_config().crt_job_id
    client = get_crt_client()

    try:
        if format == "pdf":
            result = client.get_build_results_formatted(job_id, execution_id, fmt="pdf")
            if isinstance(result, bytes):
                pdf_path = Path(f"test-results-{execution_id}.pdf")
                pdf_path.write_bytes(result)
                print_success(f"PDF saved to {pdf_path}")
                return
        else:
            result = client.get_build_results(job_id, execution_id)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output or format == "json":
        print_json(result)
    else:
        output_result(result, title=f"Test Results for {execution_id}")


# ─── AI COMMANDS ─────────────────────────────────────────────────────────────

@ai_app.command("ask")
def ai_ask(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent: plan, build, test, release, operate"),
    prompt: str = typer.Argument(..., help="Prompt for the AI agent"),
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story context"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Send a prompt to one of the 5 Copado AI specialist agents"""
    agents = AiPlatformClient.AGENTS
    if agent not in agents:
        print_error(f"Unknown agent: {agent}. Valid: {', '.join(agents.keys())}")
        raise typer.Exit(1)

    full_prompt = prompt
    if story_id:
        full_prompt = f"[Story: {story_id}] {prompt}"

    client = get_ai_client()
    try:
        result = client.ask_agent(agent, full_prompt)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        agent_info = agents[agent]
        print_panel(f"[Agent] {agent_info['description']}", result.get("response", str(result)))


@ai_app.command("chat")
def ai_chat(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent: plan, build, test, release, operate"),
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story context"),
):
    """Interactive REPL with an AI agent"""
    agents = AiPlatformClient.AGENTS
    if agent not in agents:
        print_error(f"Unknown agent: {agent}. Valid: {', '.join(agents.keys())}")
        raise typer.Exit(1)

    client = get_ai_client()
    agent_info = agents[agent]

    rprint(f"[bold cyan][Agent] {agent_info['description']}[/bold cyan]")
    rprint("[dim]Type 'exit' or 'quit' to end the conversation[/dim]")
    if story_id:
        rprint(f"[dim]Context: Story {story_id}[/dim]")
    rprint()

    history: list[dict] = []
    while True:
        try:
            user_input = Prompt.ask(f"[bold green]You ({agent})[/bold green]")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
            break

        if not user_input.strip():
            continue

        if story_id:
            user_input = f"[Story: {story_id}] {user_input}"

        try:
            with typer.progressbar(length=1, label="Thinking...") as pb:
                result = client.chat_agent(agent, user_input, history)
                pb.update(1)

            response = result.get("response", str(result))
            if isinstance(response, str):
                print_markdown(response)
            else:
                print_json(response)

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            print()
        except Exception as e:
            print_error(str(e))
            break


# ─── ENVIRONMENTS ────────────────────────────────────────────────────────────

@app.command()
def environments(
    json_output: bool = typer.Option(False, "--json"),
):
    """List pipeline environments"""
    client = get_sf_client()
    try:
        envs = client.get_environments()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    if json_output:
        print_json(envs)
    else:
        if not envs:
            print_warning("No environments found")
            return
        rows = [[e.get("Id", ""), e.get("Name", ""), e.get("copado__Type__c", "")] for e in envs]
        print_table("Pipeline Environments", ["ID", "Name", "Type"], rows)


# ─── MCP SERVER ──────────────────────────────────────────────────────────────

@app.command()
def mcp(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio (default)"),
):
    """Start the MCP server for agent discovery"""
    try:
        from copado_hx.skills.mcp_server import run_mcp_server
        run_mcp_server(transport=transport)
    except ImportError as e:
        print_error(f"MCP dependencies not installed: {e}")
        print_warning("Install with: pip install mcp")
        raise typer.Exit(1)


# ─── CONFIG ──────────────────────────────────────────────────────────────────

@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    init: bool = typer.Option(False, "--init", help="Initialize .copado-hx.json in current directory"),
):
    """Manage copado-hx configuration"""
    cfg = get_config()

    if init:
        cfg_path = Path.cwd() / ".copado-hx.json"
        if cfg_path.exists():
            confirmed = Confirm.ask(f"{cfg_path} already exists. Overwrite?", default=False)
            if not confirmed:
                return
        cfg.save(cfg_path)
        print_success(f"Configuration saved to {cfg_path}")
        return

    if show:
        import json
        data = cfg.model_dump(exclude_none=True)
        for key in ("sf_client_secret", "ai_api_key", "crt_pak"):
            if data.get(key):
                data[key] = "***"
        rprint(json.dumps(data, indent=2))
        return

    print_warning("Use --show to view config or --init to create .copado-hx.json")


def main():
    app()


if __name__ == "__main__":
    app()
