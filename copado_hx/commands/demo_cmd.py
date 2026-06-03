import time

import typer
from rich import print as rprint
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from copado_hx._app import app
from copado_hx.utils.output import (
    print_json, print_panel, print_success, print_table, print_warning,
    show_confidence_score,
)


@app.command()
def demo(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run an interactive guided tour of copado-hx (offline, uses mock data)"""

    print_panel("copado-hx Demo", "[bold]Full Salesforce DevOps from the Terminal[/bold]\n"
                 "An interactive guided tour using realistic mock data.\n"
                 "No actual Salesforce org required.\n[dim]Press Enter after each step to continue...[/dim]")

    def step(num, title, cmd, output_fn) -> None:
        input(f"[bold cyan]Step {num}:[/bold cyan] {title} — [dim]Press Enter...[/dim]")
        rprint(f"\n[bold yellow]> {cmd}[/bold yellow]\n")
        output_fn()

    step(1, "Help & Version", "copado-hx --help",
         lambda: print_table("Commands", ["Group", "Description"], [
             ["auth", "Authentication commands"],
             ["story", "User story management"],
             ["commit", "Commit changes via Actions API"],
             ["promote", "Promote across environments"],
             ["deploy", "Deploy to environment"],
             ["validate", "Validation-only deployment"],
             ["status", "Pipeline status"],
             ["workflow", "Workflow management"],
             ["test", "CRT test execution"],
             ["ai", "AI agent conversations"],
             ["env", "Environment commands"],
             ["mcp", "MCP server"],
             ["config", "Configuration"],
             ["demo", "Interactive guided tour"],
         ]))
    step(2, "Auth Status", "copado-hx auth status",
         lambda: print_panel("Authentication Status", """
[bold]Salesforce (Stories):[/bold] Authenticated (****jhoF)
[bold]AI Platform:[/bold]         Configured
[bold]CRT (Testing):[/bold]       Configured
[bold]Actions API (CI/CD):[/bold] Configured
[dim]Instance: copadotrial6013563.lightning.force.com[/dim]
    """))
    step(3, "List Stories", "copado-hx story list",
         lambda: print_table("User Stories", ["ID", "Name", "Status", "Title"], [
             ["a1vhk0000000P01AAE", "US-0000024", "Draft", "My first Source Format User Story"],
         ]))
    step(4, "Inspect Story", "copado-hx story show US-0000024",
         lambda: print_panel("User Story: US-0000024", """
[bold]ID:[/bold]          a1vhk0000000P01AAE
[bold]Title:[/bold]       My first Source Format User Story
[bold]Status:[/bold]      Draft
[bold]Environment:[/bold] Dev1
[bold]Developer:[/bold]   Kartheek Dasari
[bold]Project:[/bold]     a15hk0000002cnZAAQ
[bold]Modified:[/bold]    2026-05-27T07:10:46.000+0000
    """))
    step(5, "Workflows", "copado-hx workflow list",
         lambda: print_table("Available Workflows", ["ID", "Title", "Nodes"], [
             ["6b85a2c7...", "Create Agentforce Agent", "3"],
             ["16615d17...", "Build, Test, and Deploy", "2"],
             ["6a3b23d4...", "WIP Workflow (SF CLI)", "2"],
             ["d4e5f6a7...", "Rapid Issue Resolution", "2"],
             ["8e19fcd1...", "Release Notes", "1"],
             ["a8bd38ac...", "Technical Debt Resolution", "3"],
         ]))
    step(6, "Set Context", "copado-hx story set US-0000024",
         lambda: print_success("Working context set to: US-0000024"))
    step(7, "Commit", "copado-hx commit -m 'feat: lead scoring'",
         lambda: [print_success("Commit triggered: JE=a0shk0000000WqPAAU"),
                  print_success("Message: feat: lead scoring")])
    step(8, "Promote", "copado-hx promote --env UAT-SFP --validate",
         lambda: [print_success("Promotion to UAT-SFP triggered"),
                  print_success("Job execution: a0shk0000000Yg1AAE")])
    step(9, "Test Jobs", "copado-hx test list",
         lambda: print_table("Available Test Jobs", ["Job ID", "Name", "Type"], [
             ["120561", "CLI-Target-Job", "default"],
         ]))
    step(10, "Run Test", "copado-hx test run --job 120561",
          lambda: [print_success("Test execution triggered"),
                   print_success("Execution ID: 5249902")])
    step(11, "Test Status", "copado-hx test status --execution 5249902 --watch",
          lambda: _demo_test_status())
    step(12, "Test Results + Confidence Score", "copado-hx test results --execution 5249902",
          lambda: _demo_test_results())
    step(13, "Deploy to PROD (gate)", "copado-hx deploy --env PROD",
          lambda: _demo_deploy())
    step(14, "AI Build Agent", 'copado-hx ai ask --agent build "Lead scoring Apex"',
          lambda: _demo_ai_build())
    step(15, "AI Triage", "copado-hx ai triage --execution 5249902",
          lambda: _demo_ai_triage())
    step(16, "MCP Tools", "copado-hx mcp --list-tools",
           lambda: print_table("Tools (28 total)", ["#", "Tool", "Description"], [
               ["1", "auth_status", "Check authentication status"],
               ["9", "deliver_story", "End-to-end delivery in one call"],
               ["14", "promote", "Promote via Actions API"],
               ["22", "ai_ask_agent", "Ask AI specialist agents"],
               ["28", "deployment_confidence", "Confidence score"],
           ]))

    print_panel("Demo Complete", "[bold green]All 16 steps completed![/bold green]\n"
                 "All commands use realistic mock data.\n"
                 "To run with real data: copado-hx auth login first.")


def _demo_test_status() -> None:
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
        task = p.add_task("Waiting for test completion...", total=None)
        for status in ("In Progress", "In Progress", "Succeeded"):
            time.sleep(0.5)
            p.update(task, description=f"Status: {status}")
    print_panel("Test Execution: 5249902", "[bold]Status:[/bold] [green]Succeeded[/green]")


def _demo_test_results() -> None:
    from copado_hx.api import mock_data as md
    print_json(md.MOCK_TEST_RESULTS)
    show_confidence_score(10, 8, 2)


def _demo_deploy() -> None:
    confirmed = Confirm.ask("[red]You are about to deploy to PRODUCTION. Continue?[/red]", default=False)
    if confirmed:
        print_success("Deployment to PROD triggered: JE=a0shk0000000DEPLAA1")
    else:
        print_warning("Deployment cancelled")
        print_success("Human approval gate — safety first!")


def _demo_ai_build() -> None:
    print_panel("[Agent] AI Build Agent — Code Generation & Metadata Analysis", """
**Lead Scoring Architecture:**

1. **LeadScoringService.cls** — scoring logic
2. **LeadTrigger.trigger** — event-driven scoring
3. **LeadTriggerHandler.cls** — trigger pattern
4. **LeadScoringBatch.cls** — bulk processing
5. **LeadScoringServiceTest.cls** — unit tests
6. **LeadScoringBatchTest.cls** — batch tests
7. **LeadScoringTriggerTest.cls** — trigger tests

> 3 test classes providing >75% coverage recommended.
""")


def _demo_ai_triage() -> None:
    print_success("AI Triage for Execution 5249902")
    print_panel("Failed Tests", "[red]● TestAccountCreation (45.2s)[/red]\n[red]● TestOrderProcessing (120.1s)[/red]", "red")
    print_panel("Release Agent Analysis", """
**Root Cause Analysis:**
- **TestAccountCreation** — Timeout waiting for account sync. Possible CRT environment latency.
- **TestOrderProcessing** — Order total mismatch. Check tax calculation rules.

**Severity:** Medium — 2/10 tests failed (80% pass rate).

**Recommendation:** Safe to proceed. The 2 failures appear to be environment-related, not code-related.
""")
