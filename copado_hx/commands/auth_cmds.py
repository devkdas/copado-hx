import os
from typing import Optional

import typer
from rich.prompt import Prompt

from copado_hx._app import (
    auth_app, get_config, get_secret,
    _mask_token, _sf_url_rewrite,
)
from copado_hx.utils.storage import (
    store_secrets, delete_secret, clear_secrets, get_all_secrets,
)
from copado_hx.utils.output import (
    print_error, print_json, print_panel, print_success, print_warning,
)


@auth_app.command("login")
def auth_login(
    token: Optional[str] = typer.Option(None, "--token", help="AI API key for CI environments"),
    crt_pak: Optional[str] = typer.Option(None, "--crt-pak", help="CRT Platform Access Key"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Authenticate with all Copado services"""
    cfg = get_config()

    if token:
        store_secrets({"ai_api_key": token})
        if json_output:
            print_json({"status": "ok", "service": "ai"})
        else:
            print_success("AI API key stored securely")
        return

    if crt_pak:
        store_secrets({"crt_pak": crt_pak})
        if json_output:
            print_json({"status": "ok", "service": "crt"})
        else:
            print_success("CRT PAK stored securely")
        return

    ai_configured = bool(get_secret("ai_api_key") or cfg.ai_api_key)
    crt_configured = bool(get_secret("crt_pak") or cfg.crt_pak)
    actions_configured = bool(get_secret("actions_api_key") or cfg.actions_api_key)

    try:
        import copado_hx._app
        from copado_hx.auth.salesforce import get_sf_token
        result = get_sf_token()
        store_secrets({
            "sf_access_token": result["access_token"],
            "sf_instance_url": result["instance_url"],
        })
        print_success("Salesforce token refreshed from active session")
        copado_hx._app._sf_client = None
    except Exception:
        sf_url = Prompt.ask("Salesforce login URL", default="https://login.salesforce.com")
        sf_url = _sf_url_rewrite(sf_url)

        client_id = cfg.sf_client_id or get_secret("sf_client_id") or \
                    os.environ.get("COPADO_SF_CLIENT_ID", "") or \
                    Prompt.ask("Connected App Client ID", default="")
        client_secret = cfg.sf_client_secret or get_secret("sf_client_secret") or \
                        os.environ.get("COPADO_SF_CLIENT_SECRET", "") or \
                        Prompt.ask("Connected App Client Secret", password=True, default="")

        if client_id and client_secret:
            store_secrets({"sf_client_id": client_id, "sf_client_secret": client_secret})

        print_panel("Salesforce Authentication",
                     "A browser will open for Salesforce login.\n"
                     "Log in and approve the Connected App.")
        try:
            from copado_hx.auth.salesforce import login_web
            result = login_web()
            store_secrets({
                "sf_access_token": result["access_token"],
                "sf_instance_url": result["instance_url"],
            })
            print_success("Salesforce authenticated successfully")
        except Exception:
            if client_id and client_secret:
                if not json_output:
                    print_warning("Salesforce CLI not available, trying browser paste-URL flow")
                try:
                    from copado_hx.auth.salesforce import login_browser_paste
                    result = login_browser_paste(client_id, client_secret, instance_url=sf_url)
                    store_secrets({
                        "sf_access_token": result["access_token"],
                        "sf_instance_url": result["instance_url"],
                    })
                    print_success("Salesforce authenticated via browser paste")
                except Exception as e2:
                    if not json_output:
                        print_warning("Browser paste failed, trying password grant for headless CI...")
                    sf_user = cfg.sf_username or get_secret("sf_username") or \
                              os.environ.get("COPADO_SF_USERNAME", "")
                    sf_pass = os.environ.get("COPADO_SF_PASSWORD", "")
                    if client_id and client_secret and sf_user and sf_pass:
                        try:
                            from copado_hx.auth.salesforce import login_password_grant
                            result = login_password_grant(
                                client_id, client_secret, sf_user, sf_pass,
                                instance_url=sf_url,
                            )
                            store_secrets({
                                "sf_access_token": result["access_token"],
                                "sf_instance_url": result["instance_url"],
                                "sf_username": sf_user,
                                "sf_password": sf_pass,
                            })
                            print_success("Salesforce authenticated via password grant")
                        except Exception as e3:
                            print_error(f"Password grant failed: {e3}")
                            raise typer.Exit(1)
                    else:
                        print_error(f"Salesforce auth failed: {e2}")
                        print_warning("For headless CI, set COPADO_SF_USERNAME and COPADO_SF_PASSWORD env vars.")
                        raise typer.Exit(1)
            else:
                print_error("Salesforce auth failed. Install Salesforce CLI or set "
                            "COPADO_SF_CLIENT_ID and COPADO_SF_CLIENT_SECRET env vars for browser paste flow.")
                raise typer.Exit(1)

    pipeline_id = cfg.default_pipeline_id or Prompt.ask("Default pipeline ID (optional)", default="")
    if pipeline_id:
        cfg.set_and_save(default_pipeline_id=pipeline_id)

    if not ai_configured:
        ai_key = Prompt.ask("AI API key (from Copado AI Platform profile)", password=True, default="")
        if ai_key:
            store_secrets({"ai_api_key": ai_key})
            print_success("AI API key stored")
        else:
            print_warning("AI key not provided — AI agent commands will not work")

    if not crt_configured:
        crt_key = Prompt.ask("CRT PAK (from Copado Robotic Testing)", default="", password=True)
        if crt_key:
            store_secrets({"crt_pak": crt_key})

    if not actions_configured:
        actions_key = Prompt.ask("Actions API key (from Copado Account Summary > API Key)", default="", password=True)
        if actions_key:
            store_secrets({"actions_api_key": actions_key})

    if json_output:
        print_json({
            "salesforce_authenticated": True,
            "ai_configured": bool(get_secret("ai_api_key") or cfg.ai_api_key),
            "crt_configured": bool(get_secret("crt_pak") or cfg.crt_pak),
            "actions_configured": bool(get_secret("actions_api_key") or cfg.actions_api_key),
            "instance": cfg.cicd_instance,
        })
    else:
        print_success("All services configured!")


@auth_app.command("status")
def auth_status(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show current authenticated org and user"""
    secrets = get_all_secrets()
    sf_token = secrets.get("sf_access_token", "")
    has_sf = bool(sf_token)
    has_ai = bool(secrets.get("ai_api_key") or get_config().ai_api_key)
    has_crt = bool(secrets.get("crt_pak") or get_config().crt_pak)
    has_actions = bool(secrets.get("actions_api_key") or get_config().actions_api_key)

    if json_output:
        print_json({
            "salesforce_authenticated": has_sf,
            "ai_configured": has_ai,
            "crt_configured": has_crt,
            "actions_configured": has_actions,
            "instance": get_config().cicd_instance,
        })
        return

    sf_label = f"Authenticated ({_mask_token(sf_token)})" if has_sf else "Not authenticated"
    print_panel("Authentication Status", f"""
[bold]Salesforce (Stories):[/bold] {sf_label}
[bold]AI Platform:[/bold]         {'Configured' if has_ai else 'Not configured'}
[bold]CRT (Testing):[/bold]       {'Configured' if has_crt else 'Not configured'}
[bold]Actions API (CI/CD):[/bold] {'Configured' if has_actions else 'Not configured'}
[dim]Instance: {get_config().cicd_instance}[/dim]
    """)


@auth_app.command("logout")
def auth_logout(
    type: str = typer.Option("salesforce", "--type", "-t",
                              help="What to clear: salesforce, ai, crt, actions, all"),
) -> None:
    """Logout and clear stored credentials"""
    t = type.lower()
    if t in ("all",):
        clear_secrets()
        print_success("All credentials cleared")
    elif t in ("salesforce", "sf"):
        delete_secret("sf_access_token")
        delete_secret("sf_instance_url")
        print_success("Salesforce session cleared")
    elif t == "ai":
        delete_secret("ai_api_key")
        print_success("AI API key cleared")
    elif t == "crt":
        delete_secret("crt_pak")
        print_success("CRT PAK cleared")
    elif t == "actions":
        delete_secret("actions_api_key")
        print_success("Actions API key cleared")
    else:
        print_error(f"Unknown type: {type}. Use: salesforce, ai, crt, actions, all")
