from typing import Optional

import typer
from rich.prompt import Prompt

from copado_hx._app import (
    story_app, get_config, get_sf_client,
    _resolve_story_id, _handle_api_error,
)
from copado_hx.utils.output import (
    print_error, print_json, print_panel, print_success, print_table, print_warning,
)


@story_app.command("list")
def story_list(
    pipeline: Optional[str] = typer.Option(None, "--pipeline", "-p", help="Filter by pipeline ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (e.g. 'In Progress')"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List user stories"""
    client = get_sf_client()
    try:
        stories = client.get_user_stories(pipeline=pipeline, status=status)
    except Exception as e:
        _handle_api_error(e)
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
) -> None:
    """Show current user story details"""
    sid = _resolve_story_id(story_id)
    if not sid:
        sid = Prompt.ask("User Story ID")
    client = get_sf_client()
    try:
        story = client.get_user_story(sid)
    except Exception as e:
        _handle_api_error(e)
        raise typer.Exit(1)

    if not story:
        print_error(f"User story {sid} not found")
        raise typer.Exit(1)

    if json_output:
        print_json(story)
        return

    lines = f"""
[bold]ID:[/bold]          {story.get('Id', '')}
[bold]Title:[/bold]       {story.get('copado__User_Story_Title__c', '')}
[bold]Status:[/bold]      {story.get('copado__Status__c', '')}
[bold]Environment:[/bold] {story.get('Environment', '—')}
[bold]Developer:[/bold]   {story.get('Developer', '—')}
[bold]Project:[/bold]     {story.get('Project', '—')}
[bold]Modified:[/bold]    {story.get('LastModifiedDate', '—')}
"""
    meta = story.get("metadata_scope", [])
    if meta:
        meta_lines = "\n".join(
            f"  - {m.get('name', '?')} ({m.get('type', '?')})" for m in meta
        )
        lines += f"[bold]Metadata:[/bold]\n{meta_lines}"

    print_panel(f"User Story: {story.get('Name', '')}", lines)


@story_app.command("set")
def story_set(
    story_id: Optional[str] = typer.Argument(None, help="User story ID (or use --id)"),
    story_id_opt: Optional[str] = typer.Option(None, "--id", "-i", help="User story ID (alternative to positional)"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Set working context (like git checkout)"""
    sid = story_id_opt or story_id
    if not sid:
        print_error("Story ID required. Use: copado-hx story set <id> or copado-hx story set --id <id>")
        raise typer.Exit(1)
    try:
        sf = get_sf_client()
        story = sf.get_user_story(sid)
    except Exception as e:
        if "invalid ID" in str(e).lower():
            print_error(f"Story '{sid}' does not exist or you don't have access.")
        else:
            _handle_api_error(e)
        raise typer.Exit(1)

    if not story:
        print_error(f"User story {sid} not found. Run 'copado-hx story list' to see available stories.")
        raise typer.Exit(1)

    get_config().set_and_save(current_story_id=sid, current_story_name=story.get("Name", ""))
    if json_output:
        print_json({"status": "ok", "story_id": sid, "name": story.get("Name", "")})
        return
    print_success(f"Working context set to: {story.get('Name', sid)}")


@story_app.command("create")
def story_create(
    title: str = typer.Option(..., "--title", "-t", help="User story title"),
    pipeline: Optional[str] = typer.Option(None, "--pipeline", "-p", help="Pipeline ID"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Create a new user story"""
    client = get_sf_client()
    pipeline_id = pipeline or get_config().default_pipeline_id
    if not pipeline_id:
        pipeline_id = Prompt.ask("Pipeline ID")
    try:
        result = client.create_user_story(title, pipeline_id)
    except Exception as e:
        _handle_api_error(e)
        diag = client.troubleshoot_pipeline(pipeline_id)
        if diag:
            print_warning(diag)
        raise typer.Exit(1)

    if json_output:
        print_json(result)
    else:
        story_id = result.get("id", result.get("Id", ""))
        print_success(f"User story created: {story_id}")
        get_config().set_and_save(current_story_id=story_id, current_story_name=title)
