from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_STATE_FILE = Path.home() / ".copado-hx-state.json"

GATED_ENVS = {"PROD", "PRODUCTION"}  # environments requiring human approval


def _ensure_file() -> None:
    if not _STATE_FILE.exists():
        _STATE_FILE.write_text("{}")
        _STATE_FILE.chmod(0o600)


def load_state() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    _ensure_file()
    _STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    _STATE_FILE.chmod(0o600)


def record_action(action: str, **extras: Any) -> None:
    state = load_state()
    state["last_action"] = action
    state["last_action_time"] = datetime.now(timezone.utc).isoformat()
    for k, v in extras.items():
        if not k.startswith("last_"):
            state[f"last_{k}"] = v
        else:
            state[k] = v
    save_state(state)


def is_gated_env(env_name: str) -> bool:
    return env_name.upper() in GATED_ENVS


def store_approval(
    action_type: str,
    story_id: str,
    env: str,
    **extras: Any,
) -> str:
    code = "AP-" + secrets.token_hex(4).upper()
    state = load_state()
    state["pending_approval"] = {
        "code": code,
        "action": action_type,
        "story_id": story_id,
        "env": env,
        "created": datetime.now(timezone.utc).isoformat(),
        **extras,
    }
    save_state(state)
    return code


def consume_approval(code: str) -> Optional[dict[str, Any]]:
    state = load_state()
    pending = state.get("pending_approval")
    if not pending or pending.get("code") != code:
        return None
    state.pop("pending_approval", None)
    save_state(state)
    return pending


def has_pending_approval() -> bool:
    return bool(load_state().get("pending_approval"))

