import typer

from copado_hx._app import app, env_app, get_sf_client, _handle_api_error
from copado_hx.utils.output import (
    print_json, print_table, print_warning,
)


@env_app.command("list")
def env_list(json_output: bool = typer.Option(False, "--json")) -> None:
    """List pipeline environments"""
    client = get_sf_client()
    try:
        envs = client.get_environments()
    except Exception as e:
        _handle_api_error(e)
        raise typer.Exit(1)

    if json_output:
        print_json(envs)
    else:
        if not envs:
            print_warning("No environments found")
            return
        rows = [[e.get("Id", ""), e.get("Name", ""), e.get("copado__Type__c", "")] for e in envs]
        print_table("Pipeline Environments", ["ID", "Name", "Type"], rows)


@app.command("environments")
def environments(json_output: bool = typer.Option(False, "--json")) -> None:
    """List pipeline environments (alias for 'env list')"""
    print_warning("'environments' is deprecated — use 'copado-hx env list' instead")
    env_list(json_output=json_output)
