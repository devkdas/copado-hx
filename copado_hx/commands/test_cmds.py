import time
from typing import Any, Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from copado_hx._app import test_app, get_config, get_crt_client, _handle_api_error, get_ai_client
from copado_hx.utils.output import (
    print_error, print_json, print_panel, print_success, print_table,
    print_warning, output_result, show_confidence_score,
)
from copado_hx.utils.session_state import record_action


def _self_diagnose_test(context: str, error: str) -> dict[str, Any]:
    from copado_hx.api.mock_data import MockAiPlatformClient
    prompt = (
        f"A CRT test operation failed.\n"
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


def _display_test_results(data: dict) -> None:
    total = int(data.get("totalTests", data.get("total", 0)))
    passed = int(data.get("passedTests", data.get("passed", 0)))
    failed = int(data.get("failedTests", data.get("failed", 0)))
    show_confidence_score(total, passed, failed)
    output_result(data, title="Test Results")


@test_app.command("list")
def test_list(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List available test suites and jobs"""
    client = get_crt_client()
    try:
        jobs = client.list_jobs_detailed()
    except Exception as e:
        _handle_api_error(e)
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
    self_heal: bool = typer.Option(False, "--self-heal", help="Auto-diagnose failures via Operate agent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Trigger a CRT test suite or job execution"""
    job_id = job or suite or get_config().crt_job_id
    if not job_id:
        job_id = Prompt.ask("CRT job ID", default="")
        if not job_id:
            print_error("Job ID required")
            raise typer.Exit(1)

    client = get_crt_client()
    try:
        result = client.trigger_build(job_id)
    except Exception as e:
        if self_heal:
            diag = _self_diagnose_test("CRT test execution", str(e))
            if json_output:
                print_json({"error": str(e), "self_healing": diag})
            else:
                print_error(f"Test execution failed: {e}")
                print_panel("Self-Healing Diagnosis", diag.get("diagnosis", ""))
        else:
            _handle_api_error(e)
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        data = result.get("data", result)
        build_id = data.get("id", data.get("buildId", ""))
        record_action("test_run", execution_id=build_id, job_id=job_id)
        print_success("Test execution triggered")
        print_success(f"Execution ID: {build_id}")
        print_success("Run 'copado-hx test status --execution <id>' to check status")


@test_app.command("status")
def test_status(
    execution_id: str = typer.Option(..., "--execution", "-e", help="Execution ID"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Poll until completion"),
    self_heal: bool = typer.Option(False, "--self-heal", help="Auto-diagnose failures via Operate agent"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Poll execution status of a CRT test run"""
    job_id = get_config().crt_job_id
    client = get_crt_client()

    if watch:
        console = Console()
        errors = 0
        with console.status("Waiting for test completion...") as s:
            for _ in range(60):
                try:
                    result = client.get_build_status(job_id, execution_id)
                    errors = 0
                except Exception:
                    errors += 1
                    if errors >= 3:
                        print_error("Test status polling failed after 3 consecutive errors.")
                        raise typer.Exit(1)
                    time.sleep(10)
                    continue
                status_val = result.get("status", result.get("buildStatus", ""))
                if json_output:
                    print_json({"execution_id": execution_id, "status": status_val})
                else:
                    s.update(f"Status: {status_val}")
                if status_val in ("Succeeded", "Completed", "Passed", "Failed", "Error", "Cancelled"):
                    if status_val in ("Failed", "Error") and self_heal:
                        diag = _self_diagnose_test(f"CRT test {execution_id}", f"Status: {status_val}")
                        if json_output:
                            print_json({"execution_id": execution_id, "status": status_val, "self_healing": diag})
                        else:
                            print_panel("Self-Healing Diagnosis", diag.get("diagnosis", ""))
                    break
                time.sleep(10)
    else:
        try:
            result = client.get_build_status(job_id, execution_id)
        except Exception as e:
            _handle_api_error(e)
            raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        status_val = result.get("status", result.get("buildStatus", "Unknown"))
        style = "green" if status_val in ("Succeeded", "Completed", "Passed") else "red"
        print_panel(f"Test Execution: {execution_id}", f"[bold]Status:[/bold] [{style}]{status_val}[/{style}]")


@test_app.command("results")
def test_results(
    execution: str = typer.Argument(..., help="Execution ID to retrieve results for"),
    job: Optional[str] = typer.Option(None, "--job", "-j", help="CRT job ID"),
    fmt: str = typer.Option("json", "--format", "-f", help="Output format (json|pdf)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Retrieve test results (JUnit-compatible output)"""
    job_id = get_config().crt_job_id
    client = get_crt_client()

    try:
        if fmt == "pdf":
            result = client.get_build_results_formatted(job_id, execution, fmt="pdf")
            if isinstance(result, bytes):
                pdf_path = Path(f"test-results-{execution}.pdf")
                pdf_path.write_bytes(result)
                print_success(f"PDF saved to {pdf_path}")
                return
        else:
            result = client.get_build_results(job_id, execution)
    except Exception as e:
        _handle_api_error(e)
        raise typer.Exit(1)

    if json_output or fmt == "json":
        print_json(result)
    else:
        if fmt != "pdf":
            total = int(result.get("totalTests", result.get("total", 0)))
            passed = int(result.get("passedTests", result.get("passed", 0)))
            failed = int(result.get("failedTests", result.get("failed", 0)))
            result_status = "Passed" if failed == 0 else "Failed"
            record_action("test_results", last_test_result=result_status)
            show_confidence_score(total, passed, failed)
        output_result(result, title=f"Test Results for {execution}")
