from typing import Optional

import typer
from rich import print as rprint
from rich.prompt import Prompt

from copado_hx._app import ai_app, get_config, get_ai_client, get_crt_client
from copado_hx.api.ai import AiPlatformClient
from copado_hx.utils.output import (
    print_error, print_json, print_markdown, print_panel, print_success,
    print_warning, show_confidence_score,
)


@ai_app.command("ask")
def ai_ask(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent: plan, build, test, release, operate"),
    prompt: str = typer.Argument(..., help="Prompt for the AI agent"),
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story context"),
    stream: bool = typer.Option(False, "--stream", help="Stream AI response token by token (SSE)"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Send a prompt to one of the 5 Copado AI specialist agents"""
    agents = AiPlatformClient.AGENTS
    if agent not in agents:
        print_error(f"Unknown agent: {agent}. Valid: {', '.join(agents.keys())}")
        raise typer.Exit(1)

    full_prompt = prompt
    if story_id:
        full_prompt = f"[Story: {story_id}] {prompt}"

    client = get_ai_client()
    if stream:
        import sys
        try:
            gen = client.ask_agent_stream(agent, full_prompt)
        except Exception:
            from copado_hx.api.mock_data import MockAiPlatformClient
            gen = MockAiPlatformClient().ask_agent_stream(agent, full_prompt)
        for token in gen:
            sys.stdout.write(token)
            sys.stdout.flush()
        sys.stdout.write("\n")
        return

    try:
        result = client.ask_agent(agent, full_prompt)
    except Exception:
        from copado_hx.api.mock_data import MockAiPlatformClient
        print_warning("Copado AI API unavailable — returning demo response")
        result = MockAiPlatformClient().ask_agent(agent, full_prompt)

    if json_output:
        print_json(result)
    else:
        agent_info = agents[agent]
        print_panel(f"[Agent] {agent_info['description']}", result.get("response", str(result)))


@ai_app.command("triage")
def ai_triage(
    execution_id: str = typer.Option(..., "--execution", "-e", help="Test execution ID"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Analyze test failures via the Release AI agent (shortcut: test results + release agent)"""
    job_id = get_config().crt_job_id
    client = get_crt_client()
    try:
        result = client.get_build_results(job_id, execution_id)
    except Exception:
        from copado_hx.api.mock_data import MockCrtClient
        print_warning("CRT API unavailable — using demo test results")
        result = MockCrtClient().get_build_results(job_id, execution_id)

    total = int(result.get("totalTests", result.get("total", 0)))
    passed = int(result.get("passedTests", result.get("passed", 0)))
    failed = int(result.get("failedTests", result.get("failed", 0)))
    tests = result.get("testResults", result.get("tests", result.get("results", [])))
    failures = [t for t in tests if t.get("status", t.get("result", "")) not in ("Passed", "Succeeded")]

    if not failures:
        if json_output:
            print_json({"execution_id": execution_id, "status": "passed", "message": "All tests passed."})
        else:
            print_success(f"Execution {execution_id}: All {total} tests passed — no analysis needed")
            show_confidence_score(total, passed, failed)
        return

    prompt_parts = [
        f"Analyze test execution {execution_id}: {passed}/{total} passed, {failed} failed.",
        "Failed tests:",
    ]
    for f in failures:
        name = f.get("testName", f.get("name", "unknown"))
        dur = f.get("executionTime", f.get("duration", ""))
        prompt_parts.append(f"  - {name} ({dur})")
    prompt_parts.append("Diagnose root causes, severity, and recommend fixes.")

    prompt = "\n".join(prompt_parts)

    ai_client = get_ai_client()
    try:
        analysis = ai_client.ask_agent("release", prompt)
    except Exception:
        from copado_hx.api.mock_data import MockAiPlatformClient
        print_warning("AI API unavailable — using demo analysis")
        analysis = MockAiPlatformClient().ask_agent("release", prompt)

    if json_output:
        print_json({"execution_id": execution_id, "analysis": analysis})
    else:
        print_success(f"AI Triage for Execution {execution_id}")
        print_panel("Failed Tests",
                    "\n".join(f"[red]● {f.get('testName', f.get('name', 'unknown'))}[/red]"
                              for f in failures), "red")
        rprint()
        print_markdown(analysis.get("response", str(analysis)))
        show_confidence_score(total, passed, failed)


@ai_app.command("chat")
def ai_chat(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent: plan, build, test, release, operate"),
    story_id: Optional[str] = typer.Option(None, "--us", "--story", help="User story context"),
) -> None:
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
        except Exception:
            from copado_hx.api.mock_data import MockAiPlatformClient
            print_warning("AI API unavailable — using demo mode")
            result = MockAiPlatformClient().chat_agent(agent, user_input, history)

        response = result.get("response", str(result))
        if isinstance(response, str):
            print_markdown(response)
        else:
            print_json(response)

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print()
