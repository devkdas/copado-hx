import time
from typing import Any, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt

from copado_hx._app import (
    app, get_config, get_sf_client, get_actions_client,
    get_cicd_client, _resolve_story_id, _handle_api_error,
    _poll_job, _validate_environment,
)
from copado_hx.commands.guide_cmds import _recommend
from copado_hx.utils.output import (
    print_error, print_json, print_panel, print_success, print_table, print_warning,
)
from copado_hx.utils.session_state import (
    record_action, consume_approval, has_pending_approval, is_gated_env, store_approval,
)


def _self_diagnose(context: str, error: str) -> dict[str, Any]:
    from copado_hx.api.mock_data import MockAiPlatformClient
    from copado_hx._app import get_ai_client
    prompt = (
        f"A pipeline operation failed.\n"
        f"Context: {context}\n"
        f"Error: {error}\n\n"
        "Diagnose the root cause, severity, and recommend specific remediation steps."
    )
    ai = get_ai_client()
    if not ai:
        result = MockAiPlatformClient().ask_agent("operate", prompt)
    else:
        try:
            result = ai.ask_agent("operate", prompt)
        except Exception:
            result = MockAiPlatformClient().ask_agent("operate", prompt)
    return {"diagnosis": result.get("response", ""), "agent": "operate", "context": context}


def _show_suggestions() -> None:
    try:
        suggestions = _recommend()
        if suggestions:
            lines = [f"  [bold]{s['cmd']}[/bold]  —  {s['why']}" for s in suggestions[:3]]
            print_panel("Suggested Next Steps", "\n".join(lines))
    except Exception:
        pass


@app.command()
def approve(
    code: str = typer.Argument(..., help="Approval code to validate"),
) -> None:
    """Approve a pending action using a one-time approval code"""
    pending = consume_approval(code)
    if not pending:
        print_error(f"Invalid or expired approval code '{code}'.")
        raise typer.Exit(1)
    print_success(f"Approval for {pending.get('action')} to {pending.get('env')} recorded.")
    print_success(f"Now run: copado-hx {pending.get('action')} --us {pending.get('story_id')} --env {pending.get('env')}")


@app.command()
def list_pending():
    """Show any pending actions awaiting human approval"""
    if not has_pending_approval():
        print_success("No pending approvals.")
        return
    from copado_hx.utils.session_state import load_state
    state = load_state()
    p = state.get("pending_approval", {})
    print_panel("Pending Approval", f"Action: {p.get('action')}\nStory: {p.get('story_id')}\nEnv: {p.get('env')}\nCode: {p.get('code')}")


@app.command()
def commit(
    message: str = typer.Option("", "--message", "-m", help="Commit message"),
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    self_heal: bool = typer.Option(False, "--self-heal", help="Auto-diagnose failures via Operate agent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Commit metadata changes from the current user story context"""
    sid = _resolve_story_id(story_id)
    if not sid:
        print_error("No user story context set. Use 'copado-hx story set <id>' or --us flag.")
        raise typer.Exit(1)

    if not message:
        story_name = get_config().current_story_name or sid
        message = Prompt.ask("Commit message", default=f"feat: update {story_name}")

    client = get_actions_client()
    try:
        result = client.commit(sid, message)
    except Exception as e:
        if self_heal:
            diag = _self_diagnose("commit", str(e))
            if json_output:
                print_json({"error": str(e), "self_healing": diag})
            else:
                print_error(f"Commit failed: {e}")
                print_panel("Self-Healing Diagnosis", diag.get("diagnosis", ""))
                _show_suggestions()
        else:
            _handle_api_error(e)
        raise typer.Exit(1)

    job_id = result.get("Id", result.get("id", ""))
    record_action("commit", story_id=sid, execution_id=job_id)

    if json_output:
        print_json(result)
    else:
        print_success(f"Commit triggered: JE={job_id}")
        print_success(f"Message: {message}")


@app.command()
def promote(
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    environment: str = typer.Option("UAT-SFP", "--env", "-e", help="Target environment"),
    validate: bool = typer.Option(False, "--validate", help="Validation-only deployment"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Poll until job completes"),
    self_heal: bool = typer.Option(False, "--self-heal", help="Auto-diagnose failures via Operate agent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Promote a user story to the next environment"""
    sid = _resolve_story_id(story_id)
    if not sid:
        print_error("No user story context set.")
        raise typer.Exit(1)

    client = get_actions_client()
    try:
        _validate_environment(environment)
        if is_gated_env(environment):
            code = store_approval("promote", sid, environment)
            print_warning(f"Promote to {environment.upper()} requires human approval.")
            print_warning(f"Approval code: [bold]{code}[/bold] — show this to the developer.")
            print_success(f"Run: copado-hx approve {code}")
            if json_output:
                print_json({"status": "approval_required", "approval_code": code, "environment": environment})
            return
        result = client.promote(sid, environment, validate_only=validate)
    except Exception as e:
        if self_heal:
            diag = _self_diagnose(f"promote to {environment}", str(e))
            if json_output:
                print_json({"error": str(e), "self_healing": diag})
            else:
                print_error(f"Promote failed: {e}")
                print_panel("Self-Healing Diagnosis", diag.get("diagnosis", ""))
                _show_suggestions()
        else:
            _handle_api_error(e)
        raise typer.Exit(1)

    job_id = result.get("Id", result.get("id", ""))

    record_action("promote", story_id=sid, execution_id=job_id, env=environment)

    if watch and job_id:
        final = _poll_job(job_id, get_sf_client())
        if json_output:
            print_json({"job_id": job_id, "final_status": final})
        else:
            style = "green" if final == "Completed" else "red"
            print_panel(f"Promotion to {environment}", f"[bold]Final Status:[/bold] [{style}]{final}[/{style}]")
        return

    if json_output:
        print_json(result)
    else:
        action = "Validation" if validate else "Promotion"
        print_success(f"{action} to {environment} triggered")
        if job_id:
            print_success(f"Job execution: {job_id}")


@app.command()
def deploy(
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    environment: str = typer.Option("PROD", "--env", "-e", help="Target environment"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Poll until job completes"),
    self_heal: bool = typer.Option(False, "--self-heal", help="Auto-diagnose failures via Operate agent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Execute a deployment to production (requires approval gate confirmation)"""
    if is_gated_env(environment) and not force:
        code = store_approval("deploy", story_id or "", environment)
        print_warning(f"Deploy to {environment.upper()} requires human approval.")
        print_warning(f"Approval code: [bold]{code}[/bold] — show this to the developer.")
        print_success(f"Run: copado-hx approve {code}")
        if json_output:
            print_json({"status": "approval_required", "approval_code": code, "environment": environment})
        return

    sid = _resolve_story_id(story_id)
    if not sid:
        print_error("No user story context set.")
        raise typer.Exit(1)

    client = get_actions_client()
    try:
        _validate_environment(environment)
        result = client.deploy(sid, environment)
    except Exception as e:
        if self_heal:
            diag = _self_diagnose(f"deploy to {environment}", str(e))
            if json_output:
                print_json({"error": str(e), "self_healing": diag})
            else:
                print_error(f"Deploy failed: {e}")
                print_panel("Self-Healing Diagnosis", diag.get("diagnosis", ""))
                _show_suggestions()
        else:
            _handle_api_error(e)
        raise typer.Exit(1)

    job_id = result.get("Id", result.get("id", ""))
    record_action("deploy", story_id=sid, env=environment)

    if watch and job_id:
        final = _poll_job(job_id, get_sf_client())
        if json_output:
            print_json({"job_id": job_id, "final_status": final})
        else:
            style = "green" if final == "Completed" else "red"
            print_panel(f"Deployment to {environment}", f"[bold]Final Status:[/bold] [{style}]{final}[/{style}]")
        return

    if json_output:
        print_json(result)
    else:
        print_success(f"Deployment to {environment} triggered: JE={job_id}")


@app.command()
def validate(
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story ID"),
    environment: str = typer.Option("UAT-SFP", "--env", "-e", help="Target environment"),
    self_heal: bool = typer.Option(False, "--self-heal", help="Auto-diagnose failures via Operate agent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run a validation-only deployment"""
    sid = _resolve_story_id(story_id)
    if not sid:
        print_error("No user story context set.")
        raise typer.Exit(1)

    client = get_actions_client()
    try:
        result = client.promote(sid, environment, validate_only=True)
    except Exception as e:
        if self_heal:
            diag = _self_diagnose(f"validation to {environment}", str(e))
            if json_output:
                print_json({"error": str(e), "self_healing": diag})
            else:
                print_error(f"Validation failed: {e}")
                print_panel("Self-Healing Diagnosis", diag.get("diagnosis", ""))
                _show_suggestions()
        else:
            _handle_api_error(e)
        raise typer.Exit(1)

    job_id = result.get("Id", result.get("id", ""))
    record_action("validate", story_id=sid, execution_id=job_id, env=environment)

    if json_output:
        print_json(result)
    else:
        print_success(f"Validation deployment to {environment} triggered")
        if job_id:
            print_success(f"Job execution: {job_id}")


@app.command()
def status(
    job: Optional[str] = typer.Option(None, "--job", "-j", help="Job execution ID to monitor"),
    run: Optional[str] = typer.Option(None, "--run", "-r", help="Workflow run ID to monitor"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Live-polling terminal dashboard"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
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
            _handle_api_error(e)
            raise typer.Exit(1)

        if json_output:
            print_json(result)
        else:
            status_val = result.get("copado__Status__c", "Unknown")
            print_panel(f"Job Execution: {job}", f"[bold]Status:[/bold] {status_val}")

        if watch:
            console = Console()
            s = ""
            with console.status("Waiting for completion...") as st:
                for _ in range(60):
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
                    st.update(f"Status: {s}")
                    if s in ("Completed", "Failed", "Error"):
                        break
            style = "green" if s == "Completed" else "red"
            print_panel(f"Job Execution: {job}", f"[bold]Final Status:[/bold] [{style}]{s}[/{style}]")
        return

    if run:
        try:
            result = client.get_run(run)
        except Exception as e:
            _handle_api_error(e)
            raise typer.Exit(1)

        if json_output:
            print_json(result)
        else:
            status_val = result.get("status", "Unknown")
            print_panel(f"Workflow Run: {run}", f"[bold]Status:[/bold] {status_val}")

        if watch:
            console = Console()
            s = ""
            with console.status("Waiting for completion...") as st:
                for _ in range(60):
                    time.sleep(10)
                    try:
                        result = client.get_run(run)
                    except Exception:
                        break
                    s = result.get("status", "")
                    st.update(f"Status: {s}")
                    if s in ("completed", "failed", "succeeded"):
                        break
            print_success(f"Final status: {s}")
        return

    sf = get_sf_client()

    if watch:
        console = Console()
        with console.status("Polling pipeline status...") as s:
            for _ in range(30):
                try:
                    records = sf.query(
                        "SELECT Id, Name, copado__Status__c, LastModifiedDate "
                        "FROM copado__JobExecution__c "
                        "ORDER BY LastModifiedDate DESC LIMIT 10"
                    )
                    console.clear()
                    rows = [[r.get("Id", "")[:12], r.get("Name", "")[:30],
                             r.get("copado__Status__c", ""),
                             r.get("LastModifiedDate", "")[:19]] for r in records]
                    print_table("Recent Job Executions", ["ID", "Name", "Status", "Last Modified"], rows)
                    s.update("Refreshing...")
                except Exception:
                    break
                time.sleep(10)
        return

    try:
        envs = sf.get_environments()
    except Exception as e:
        _handle_api_error(e)
        raise typer.Exit(1)

    if json_output:
        print_json({"environments": envs})
    else:
        rows = [[e.get("Id", ""), e.get("Name", ""), e.get("copado__Type__c", "")] for e in envs]
        print_table("Pipeline Environments", ["ID", "Name", "Type"], rows)
