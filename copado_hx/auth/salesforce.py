from __future__ import annotations

import json
import subprocess
import urllib.parse

import httpx

from copado_hx.api import AuthError


SF_AUTH_BASE = "https://login.salesforce.com"
REDIRECT_URI = "sfdx://success"


def login_web(org_alias: str = "copado-hx") -> dict:
    result = subprocess.run(
        ["sf", "org", "login", "web", "--alias", org_alias,
         "--instance-url", "https://copadotrial6013563.my.salesforce.com",
         "--no-prompt"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        stdout_lines = result.stdout.strip().split("\n")
        if stdout_lines and "Successfully authorized" in stdout_lines[-1]:
            pass
        else:
            stderr = result.stderr.strip()
            if "already been aliased" in stderr:
                pass
            else:
                raise AuthError(f"Web auth failed: {stderr or result.stdout[:500]}")

    return get_sf_token(org_alias)


def get_sf_token(org_alias: str = "copado-hx") -> dict:
    token_result = subprocess.run(
        ["sf", "org", "auth", "show-access-token", "-o", org_alias, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    if token_result.returncode != 0:
        raise AuthError(f"Could not get access token: {token_result.stderr.strip()}")
    token_data = json.loads(token_result.stdout)
    token = token_data.get("result", {}).get("accessToken", "")
    if not token:
        raise AuthError("Empty access token in response")

    org_result = subprocess.run(
        ["sf", "org", "display", "-o", org_alias, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    org_info = {}
    if org_result.returncode == 0:
        org_data = json.loads(org_result.stdout)
        org_info = org_data.get("result", {})
    instance_url = org_info.get("instanceUrl") or org_info.get("instance_url") or SF_AUTH_BASE

    return {
        "access_token": token,
        "instance_url": instance_url,
    }


def login_browser_paste(
    client_id: str,
    client_secret: str,
    instance_url: str = SF_AUTH_BASE,
    redirect_uri: str = REDIRECT_URI,
) -> dict:
    """Browser paste-URL OAuth 2.0 — no Salesforce CLI required.

    1. Prints authorization URL for user to open in browser
    2. User logs in and approves the Connected App
    3. User pastes the redirect URL back into the terminal
    4. CLI extracts the auth code and exchanges it for an access token
    """
    import webbrowser
    from rich.prompt import Prompt
    from rich import print as rprint
    from rich.panel import Panel

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    })
    auth_url = f"{instance_url.rstrip('/')}/services/oauth2/authorize?{params}"

    rprint(Panel(
        "[bold]Step 1:[/bold] Open this URL in your browser:\n\n"
        f"[cyan]{auth_url}[/cyan]\n\n"
        "[bold]Step 2:[/bold] Log in and approve the Connected App\n"
        "[bold]Step 3:[/bold] Copy the URL you are redirected to (starts with "
        f"[cyan]{redirect_uri}[/cyan])\n"
        "[bold]Step 4:[/bold] Paste it below",
        title="Salesforce OAuth — Browser Paste",
        border_style="cyan",
    ))

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    callback_url = Prompt.ask("Paste the redirect URL here")

    parsed = urllib.parse.urlparse(callback_url)
    query = urllib.parse.parse_qs(parsed.query)
    code = query.get("code", [None])[0]
    if not code:
        code = urllib.parse.parse_qs(parsed.fragment).get("code", [None])[0]
    if not code:
        raise AuthError("Could not extract authorization code from URL. "
                        "Make sure you paste the full redirect URL.")

    token_data = _exchange_code(instance_url, client_id, client_secret, code, redirect_uri)
    return {
        "access_token": token_data["access_token"],
        "instance_url": token_data.get("instance_url", instance_url),
    }


def login_password_grant(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
    instance_url: str = SF_AUTH_BASE,
) -> dict:
    """OAuth 2.0 Resource Owner Password Credentials Grant.

    For headless/CI environments where browser-based flows are unavailable.
    Requires username+password (appended with security token if needed).
    """
    token_url = f"{instance_url.rstrip('/')}/services/oauth2/token"
    body = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = httpx.post(token_url, data=body, headers=headers, timeout=30)
    except Exception as e:
        raise AuthError(f"Password grant failed (connection): {e}")

    if resp.status_code >= 400:
        detail = resp.text[:500]
        raise AuthError(f"Password grant failed ({resp.status_code}): {detail}")

    data = resp.json()
    return {
        "access_token": data["access_token"],
        "instance_url": data.get("instance_url", instance_url),
    }


def _exchange_code(
    instance_url: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict:
    token_url = f"{instance_url.rstrip('/')}/services/oauth2/token"
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = httpx.post(token_url, data=body, headers=headers, timeout=30)
    except Exception as e:
        raise AuthError(f"Token exchange failed: {e}")

    if resp.status_code >= 400:
        detail = resp.text[:500]
        raise AuthError(f"Token exchange failed ({resp.status_code}): {detail}")

    return resp.json()
