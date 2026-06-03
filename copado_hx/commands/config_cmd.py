import json
from pathlib import Path

import typer
from rich import print as rprint
from rich.prompt import Confirm

from copado_hx._app import app, get_config
from copado_hx.utils.output import print_success, print_warning


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    init: bool = typer.Option(False, "--init", help="Initialize .copado-hx.json in current directory"),
) -> None:
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
        data = cfg.model_dump(exclude_none=True)
        for key in ("ai_api_key", "crt_pak", "actions_api_key"):
            if data.get(key):
                data[key] = "***"
        rprint(json.dumps(data, indent=2))
        return

    print_warning("Use --show to view config or --init to create .copado-hx.json")
