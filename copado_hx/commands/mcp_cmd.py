import typer

from copado_hx._app import app
from copado_hx.utils.output import (
    print_error, print_success, print_table, print_warning,
)


@app.command()
def mcp(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio (default)"),
    list_tools: bool = typer.Option(False, "--list-tools", help="Print available tools and exit (no server start)"),
) -> None:
    """Start the MCP server for agent discovery"""
    if list_tools:
        print_success("copado-hx MCP — Tools Available")
        print_table(
            "Tools (28 total)", ["#", "Tool", "Description"],
            [
                ["1", "version_mcp", "Return version information for copado-hx and Python"],
                ["2", "config_get_mcp", "Get a configuration value by key"],
                ["3", "auth_status", "Check authentication status across all services"],
                ["4", "auth_status_mcp", "Structured agent readiness report + story context check"],
                ["5", "auth_logout_mcp", "Clear stored credentials for all services"],
                ["6", "story_list", "List user stories from the Salesforce org"],
                ["7", "story_show", "Get detailed information about a specific user story"],
                ["8", "story_set_context", "Set a user story as the current working context"],
                ["9", "story_create_mcp", "Create a user story in the Salesforce org"],
                ["10", "commit", "Commit metadata changes via Actions API"],
                ["11", "promote", "Promote a user story with PROD approval gate + self-heal"],
                ["12", "deploy_to_prod", "Deploy to production with approval gate + self-heal"],
                ["13", "deliver_story", "End-to-end delivery: commit \u2192 promote \u2192 deploy \u2192 test"],
                ["14", "approve_action", "Complete a one-time approval code for gated deployment"],
                ["15", "check_pending_approvals", "Check for pending actions awaiting human approval"],
                ["16", "self_heal", "Diagnose pipeline failure via Operate agent"],
                ["17", "workflow_list", "List available CI/CD workflows"],
                ["18", "workflow_run", "Trigger a CI/CD workflow"],
                ["19", "list_test_jobs", "List available CRT test jobs"],
                ["20", "run_test", "Trigger a CRT test execution (with self-heal)"],
                ["21", "test_status", "Check CRT test execution status"],
                ["22", "test_results", "Retrieve CRT test results"],
                ["23", "ai_ask_agent", "Ask one of 5 AI specialist agents"],
                ["24", "ai_triage", "Auto-analyze test failures via Release AI agent"],
                ["25", "deployment_confidence", "Calculate deployment confidence score from test results"],
                ["26", "list_environments", "List pipeline environments"],
                ["27", "list_pipelines", "List available pipelines"],
                ["28", "check_pipeline_status", "Check workflow run status"],
            ],
        )
        print_success("Use 'copado-hx mcp' to start the server for MCP client connection")
        return

    try:
        from copado_hx.skills.mcp_server import run_mcp_server
        run_mcp_server(transport=transport)
    except ImportError as e:
        print_error(f"MCP dependencies not installed: {e}")
        print_warning("Install with: pip install mcp")
        raise typer.Exit(1)
