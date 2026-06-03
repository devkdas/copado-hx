from typing import Optional

import typer

from copado_hx._app import wf_app, get_cicd_client
from copado_hx.utils.output import (
    print_json, print_success, print_table, print_warning,
)


@wf_app.command("list")
def workflow_list(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List available CI/CD workflows on the Copado AI Platform"""
    client = get_cicd_client()
    try:
        workflows = client.list_workflows()
    except Exception:
        from copado_hx.api.mock_data import MockCopadoCicdClient
        print_warning("Copado API unavailable — showing demo data")
        workflows = MockCopadoCicdClient().list_workflows()

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
) -> None:
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
    except Exception:
        from copado_hx.api.mock_data import MockCopadoCicdClient
        print_warning("Copado API unavailable — showing demo response")
        result = MockCopadoCicdClient().trigger_workflow(workflow_id, parameters or None)

    if json_output:
        print_json(result)
    else:
        run_id = result.get("id", result.get("run_id", "N/A"))
        print_success(f"Workflow run triggered: {run_id}")
