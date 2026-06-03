from __future__ import annotations

import json
from typing import Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box as rich_box

_console = Console()


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    table = Table(title=title, box=rich_box.ROUNDED)
    for col in columns:
        table.add_column(col, style="cyan" if col == "ID" else "white")
    for row in rows:
        table.add_row(*[str(c) for c in row])
    _console.print(table)


def print_panel(title: str, content: str, style: str = "green") -> None:
    _console.print(Panel(content, title=title, border_style=style))


def print_error(message: str, detail: Optional[str] = None) -> None:
    msg = f"[red]Error:[/red] {message}"
    if detail:
        msg += f"\n[dim]{detail}[/dim]"
    _console.print(msg)


def print_success(message: str) -> None:
    _console.print(f"[green]OK[/green] {message}")


def print_warning(message: str) -> None:
    _console.print(f"[yellow]WARN[/yellow] {message}")


def print_markdown(text: str) -> None:
    _console.print(Markdown(text))


def spinner(message: str = "Working...") -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=_console,
    )


def show_confidence_score(total: int, passed: int, failed: int) -> None:
    """Multi-factor confidence score with recommendation text.

    Formula: (passed/total * 60) + failure_penalty + coverage_bonus (placeholder).
    """
    if total <= 0:
        return

    test_score = (passed / total) * 60
    no_critical = 20 if failed == 0 else max(0, 20 - (failed * 5))
    coverage_bonus = 20 if passed / total >= 0.5 else 0
    confidence = min(100, test_score + no_critical + coverage_bonus)

    if confidence >= 85:
        style = "green"
        recommendation = "SAFE TO DEPLOY"
        risk = "Low"
    elif confidence >= 60:
        style = "yellow"
        recommendation = "DEPLOY WITH CAUTION"
        risk = "Medium"
    else:
        style = "red"
        recommendation = "DO NOT DEPLOY"
        risk = "High"

    bar_len = 30
    filled = int(bar_len * confidence / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    _console.print(Panel(
        f"[{style}]{bar}[/{style}]\n"
        f"[bold]Score:[/bold]     {confidence:.1f}%\n"
        f"[bold]Risk:[/bold]      [{style}]{risk}[/{style}]\n"
        f"[bold]Verdict:[/bold]   [{style}]{recommendation}[/{style}]\n"
        f"[dim]Tests: {passed}/{total} passed, {failed} failed[/dim]",
        title="Deployment Confidence",
        border_style=style,
    ))


def output_result(data: Any, json_flag: bool = False, **table_kwargs) -> None:
    if json_flag:
        print_json(data)
    else:
        if isinstance(data, dict):
            if "items" in data and isinstance(data["items"], list):
                items = data["items"]
                if items:
                    cols = list(items[0].keys()) if items else []
                    rows = [[str(item.get(c, "")) for c in cols] for item in items]
                    title = table_kwargs.get("title", "Results")
                    print_table(title, cols, rows)
            else:
                _console.print(Panel(json.dumps(data, indent=2, default=str), title="Result"))
        elif isinstance(data, list):
            if data:
                cols = list(data[0].keys()) if isinstance(data[0], dict) else ["Value"]
                rows = [[str(item.get(c, "")) for c in cols] if isinstance(item, dict) else [str(item)] for item in data]
                print_table(table_kwargs.get("title", "Results"), cols, rows)
        else:
            _console.print(str(data))
