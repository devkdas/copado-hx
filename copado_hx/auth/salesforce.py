from __future__ import annotations

import subprocess
import json


from copado_hx.api import AuthError


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
    result = subprocess.run(
        ["sf", "org", "auth", "show-access-token", "-o", org_alias, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise AuthError(f"Could not get access token: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    token = data.get("result", {}).get("accessToken", "")
    if not token:
        raise AuthError("Empty access token in response")
    return {
        "access_token": token,
        "instance_url": "https://copadotrial6013563.my.salesforce.com",
    }
