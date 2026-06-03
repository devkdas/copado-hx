import time

import typer
from rich.console import Console
from rich.prompt import IntPrompt
from rich.panel import Panel

from copado_hx._app import app, get_config, get_sf_client
from copado_hx.utils.output import (
    print_error, print_panel, print_success, print_table, print_warning,
)
from copado_hx.utils.session_state import (
    has_pending_approval, load_state, record_action,
)
from copado_hx.utils.storage import get_secret

console = Console()


# ── Recommendation engine ──

def _recommend() -> list[dict[str, str]]:
    state = load_state()
    cfg = get_config()

    has_sf = get_secret("sf_access_token") is not None
    has_ai = get_secret("ai_api_key") is not None or bool(get_config().ai_api_key)
    story = cfg.current_story_id
    last_action = state.get("last_action", "")
    last_env = state.get("last_env", "")
    test_failed = state.get("last_test_result") == "Failed"

    suggestions: list[dict[str, str]] = []

    if has_pending_approval():
        p = state.get("pending_approval", {})
        suggestions.append({"cmd": f"copado-hx approve {p.get('code', '')}", "why": f"Complete pending approval for {p.get('action')} to {p.get('env')}"})
        suggestions.append({"cmd": "copado-hx list-pending", "why": "View pending approval details"})
        return suggestions[:4]

    if not has_sf:
        suggestions.append({"cmd": "copado-hx auth login", "why": "Authenticate with Salesforce"})
        suggestions.append({"cmd": "copado-hx auth status", "why": "Check authentication state"})
        return suggestions[:4]

    if last_action in ("story_set", "story_pick"):
        if story:
            suggestions.append({"cmd": f"copado-hx story show --id {story}", "why": "View story details"})
            suggestions.append({"cmd": f'copado-hx commit --us {story} -m "message"', "why": "Commit changes"})
            if has_ai:
                suggestions.append({"cmd": "copado-hx ai ask --agent build \"Suggest metadata\"", "why": "AI build guidance"})
            suggestions.append({"cmd": f"copado-hx promote --us {story} --env INT-SFP", "why": "Promote to integration"})
        return suggestions[:4]

    if last_action == "commit":
        if story:
            suggestions.append({"cmd": f"copado-hx promote --us {story} --env INT-SFP", "why": "Promote to next environment"})
            suggestions.append({"cmd": f"copado-hx promote --us {story} --env INT-SFP --validate", "why": "Validate before promoting"})
        suggestions.append({"cmd": "copado-hx story list", "why": "Check other stories"})
        if has_ai:
            suggestions.append({"cmd": "copado-hx ai ask --agent build \"Review my commit\"", "why": "AI code review"})
        return suggestions[:4]

    if last_action == "promote":
        suggestions.append({"cmd": "copado-hx status --job <JOB_ID> --watch", "why": "Watch promotion progress"})
        if last_env:
            suggestions.append({"cmd": f"copado-hx deploy --env {last_env} --force", "why": "Force deploy to unlocked env"})
        suggestions.append({"cmd": "copado-hx approve <CODE>", "why": "Complete gated deployment approval"})
        if has_ai:
            suggestions.append({"cmd": "copado-hx ai ask --agent release \"Generate release notes\"", "why": "AI release notes"})
        return suggestions[:4]

    if last_action == "deploy":
        if has_ai:
            suggestions.append({"cmd": "copado-hx ai ask --agent release \"Generate release notes\"", "why": "AI release notes"})
            suggestions.append({"cmd": "copado-hx ai ask --agent operate \"Change management plan\"", "why": "AI change management"})
        suggestions.append({"cmd": "copado-hx story list", "why": "Pick next story"})
        return suggestions[:4]

    if last_action == "test_run":
        suggestions.append({"cmd": "copado-hx test status --execution <ID> --watch", "why": "Watch test execution"})
        if has_ai:
            suggestions.append({"cmd": "copado-hx ai ask --agent test \"Analyze coverage\"", "why": "AI test analysis"})
        return suggestions[:4]

    if last_action == "test_results":
        if test_failed:
            if has_ai:
                suggestions.append({"cmd": "copado-hx ai triage --execution <ID>", "why": "AI failure triage"})
        else:
            if last_env:
                suggestions.append({"cmd": f"copado-hx deploy --env {last_env}", "why": "Tests passed \u2014 deploy"})
            if has_ai:
                suggestions.append({"cmd": "copado-hx ai ask --agent release \"Generate release notes\"", "why": "AI release notes"})
        suggestions.append({"cmd": "copado-hx story list", "why": "Check other stories"})
        return suggestions[:4]

    suggestions.append({"cmd": "copado-hx story list", "why": "Browse user stories"})
    if story:
        suggestions.append({"cmd": f"copado-hx story show --id {story}", "why": "View current story"})
    suggestions.append({"cmd": "copado-hx auth status", "why": "Check all service connections"})
    return suggestions[:4]


def _print_context() -> None:
    cfg = get_config()
    state = load_state()

    has_sf = get_secret("sf_access_token") is not None
    story = cfg.current_story_id or "[yellow]not selected[/yellow]"
    last_action = state.get("last_action", "")
    last_env = state.get("last_env", "")

    lines = [f"[bold]Story:[/bold]       {story}"]
    if last_action:
        lines.append(f"[bold]Last action:[/bold] {last_action.replace('_', ' ')}")
    if last_env:
        lines.append(f"[bold]Environment:[/bold] {last_env}")
    if has_sf:
        lines.append("[bold]Auth:[/bold]        [green]authenticated[/green]")
    else:
        lines.append("[bold]Auth:[/bold]        [red]not authenticated[/red]")

    console.print()
    print_panel("Current Context", "\n".join(lines), "cyan")
    console.print()


def _print_actions(actions: list[dict[str, str]]) -> None:
    lines = []
    for a in actions:
        lines.append(f"  [bold cyan]\u2192[/bold cyan] [bold]{a['cmd']}[/bold]")
        lines.append(f"    [dim]{a['why']}[/dim]")
    console.print(Panel(
        "\n".join(lines),
        title="[bold]Suggested Next Steps[/bold]",
        border_style="blue",
        expand=False,
    ))


# ── guide ──

@app.command()
def guide():
    """Context summary + available actions (non-interactive)."""
    _print_context()
    suggestions = _recommend()
    if suggestions:
        _print_actions(suggestions)
    else:
        console.print("[yellow]No actions available. Run [bold]copado-hx auth login[/bold] to get started.[/yellow]")


# ── interactive ──

@app.command()
def interactive(
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all available actions table"),
):
    """Interactive guided workflow \u2014 select \u2192 execute \u2192 loop."""
    from copado_hx.commands.pipeline_cmds import commit, promote, deploy
    from copado_hx.commands.test_cmds import test_run
    from copado_hx.commands.story_cmds import story_list, story_show, story_set
    from copado_hx.commands.ai_cmds import ai_ask

    suggestions = _recommend()

    if show_all:
        _print_context()
        _print_actions(suggestions)
        return

    console.print("[bold cyan]Interactive Mode[/bold cyan] \u2014 select an action or 0 to exit")
    console.print()

    while True:
        _print_context()

        if not suggestions:
            console.print("[yellow]No actions available. Run [bold]copado-hx auth login[/bold] first.[/yellow]")
            console.print()
            break

        labels = []
        for i, a in enumerate(suggestions, 1):
            labels.append(f"  [bold]{i}.[/bold] {a['cmd']}  [dim]\u2014 {a['why']}[/dim]")
        console.print(Panel(
            "\n".join(labels),
            title="[bold]Actions[/bold]",
            border_style="blue",
            expand=False,
        ))
        console.print()

        try:
            choice = IntPrompt.ask(
                f"[bold]Select (0 to exit, 1\u2013{len(suggestions)})[/bold]",
                default=0,
            )
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Exiting interactive mode.[/yellow]")
            break

        if choice == 0:
            console.print("[yellow]Exiting interactive mode.[/yellow]")
            break
        if choice < 0 or choice > len(suggestions):
            console.print(f"[red]Invalid choice. Pick 1\u2013{len(suggestions)}.[/red]")
            continue

        selected = suggestions[choice - 1]
        cmd = selected["cmd"]
        console.print(f"[dim]$ {cmd}[/dim]")
        console.print()

        parts = cmd.replace("copado-hx ", "").split()
        try:
            if parts[0] == "story":
                if parts[1] == "list":
                    story_list()
                elif parts[1] == "show":
                    sid = parts[3] if len(parts) > 3 else None
                    story_show(sid)
                elif parts[1] == "set":
                    sid = parts[3] if len(parts) > 3 else parts[2] if len(parts) > 2 else None
                    story_set(sid)
            elif parts[0] == "commit":
                sid = parts[2] if len(parts) > 2 else None
                msg = parts[4] if len(parts) > 4 else ""
                commit(message=msg, story_id=sid)
            elif parts[0] == "promote":
                sid = parts[2] if len(parts) > 2 else None
                env = parts[4] if len(parts) > 4 else "UAT-SFP"
                promote(story_id=sid, environment=env)
            elif parts[0] == "deploy":
                env = parts[2] if len(parts) > 2 else "PROD"
                deploy(environment=env, force=True)
            elif parts[0] == "status":
                from copado_hx.commands.pipeline_cmds import status as pipeline_status
                pipeline_status()
            elif parts[0] == "test":
                if parts[1] == "run":
                    test_run()
            elif parts[0] == "ai":
                if parts[1] == "ask":
                    agent = parts[4] if len(parts) > 4 else "build"
                    prompt = " ".join(parts[5:]) if len(parts) > 5 else "Help"
                    ai_ask(agent=agent, prompt=prompt)
            elif parts[0] == "auth":
                if parts[1] == "status":
                    from copado_hx.commands.auth_cmds import auth_status
                    auth_status()
                elif parts[1] == "login":
                    from copado_hx.commands.auth_cmds import auth_login
                    auth_login()
        except typer.Exit:
            pass
        except Exception as e:
            print_error(f"Command failed: {e}")

        suggestions = _recommend()
        console.print()


# ── pick ──

@app.command()
def pick():
    """Interactive story picker \u2014 choose a story and set context."""
    client = get_sf_client()
    console.print("[cyan]Fetching your stories...[/cyan]")

    try:
        stories = client.get_user_stories()
    except Exception as e:
        print_error(f"Failed to load stories: {e}")
        raise typer.Exit(1)

    if not stories:
        print_warning("No stories found.")
        return

    console.print()
    print_table(
        "Open Stories",
        ["#", "Name", "Title", "Status"],
        [
            [str(i + 1), s.get("Name", ""), s.get("copado__User_Story_Title__c", ""), s.get("copado__Status__c", "")]
            for i, s in enumerate(stories)
        ],
    )
    console.print()

    try:
        choice = IntPrompt.ask(f"[bold]Select a story (1\u2013{len(stories)}, 0 to cancel)[/bold]", default=0)
    except (KeyboardInterrupt, EOFError):
        return

    if choice == 0:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    if choice < 0 or choice > len(stories):
        print_warning(f"Invalid choice. Pick 1\u2013{len(stories)}.")
        return

    selected = stories[choice - 1]
    story_id = selected.get("Name", "")

    get_config().set_and_save(
        current_story_id=story_id,
        current_story_name=selected.get("copado__User_Story_Title__c", ""),
    )
    record_action("story_pick", last_story=story_id)

    console.print()
    print_success(f"Story selected: [bold]{story_id}[/bold]")
    console.print(f"  [bold]Title:[/bold]       {selected.get('copado__User_Story_Title__c', 'N/A')}")
    console.print(f"  [bold]Status:[/bold]      {selected.get('copado__Status__c', 'N/A')}")
    console.print()


# ── ship ──

@app.command()
def ship(
    story_id: str = typer.Option(..., "--us", "--story", help="User story ID"),
    target_env: str = typer.Option("UAT-SFP", "--to", "-e", help="Target environment"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip CRT test execution"),
):
    """Guided end-to-end pipeline: commit \u2192 promote \u2192 test \u2192 deploy."""
    from copado_hx.commands.pipeline_cmds import commit, promote, deploy
    from copado_hx.commands.test_cmds import test_run

    STEP_DELAY = 1.5

    def _step(num: int, title: str, fn, *args, **kwargs):
        console.print()
        console.print(f"[bold yellow]Ship Step {num}[/bold yellow]  [bold]{title}[/bold]")
        time.sleep(STEP_DELAY)
        try:
            fn(*args, **kwargs)
            record_action(f"ship_{title.lower().replace(' ', '_')}", status="success")
        except (typer.Exit, SystemExit):
            print_error(f"Ship step {num} failed: {title}")
            record_action(f"ship_{title.lower().replace(' ', '_')}", status="failed")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Ship step {num} failed: {e}")
            record_action(f"ship_{title.lower().replace(' ', '_')}", status="failed", error=str(e))
            raise typer.Exit(1)

    _step(1, "Commit", commit, story_id=story_id,
          message=f"feat: ship {story_id}")

    _step(2, "Promote", promote, story_id=story_id, environment=target_env)

    if not skip_tests:
        _step(3, "Run Tests", test_run)

    _step(4, "Deploy", deploy, story_id=story_id, environment=target_env, force=True)

    console.print()
    print_success("Pipeline complete! Story delivered end-to-end.")
    record_action("ship_complete", last_story=story_id, last_env=target_env)
