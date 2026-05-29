from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional


SECRETS_FILE = Path.home() / ".copado-hx-secrets.json"


def store_secrets(secrets: Dict[str, str]) -> None:
    existing = {}
    if SECRETS_FILE.exists():
        try:
            existing = json.loads(SECRETS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    existing.update(secrets)
    SECRETS_FILE.write_text(json.dumps(existing, indent=2))
    SECRETS_FILE.chmod(0o600)


def get_secret(key: str) -> Optional[str]:
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text())
            return data.get(key)
        except (json.JSONDecodeError, OSError):
            return None
    return os.environ.get(f"COPADO_{key.upper()}")


def delete_secret(key: str) -> None:
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text())
            data.pop(key, None)
            SECRETS_FILE.write_text(json.dumps(data, indent=2))
            SECRETS_FILE.chmod(0o600)
        except (json.JSONDecodeError, OSError):
            pass


def get_all_secrets() -> Dict[str, str]:
    if SECRETS_FILE.exists():
        try:
            return json.loads(SECRETS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def clear_secrets() -> None:
    if SECRETS_FILE.exists():
        SECRETS_FILE.unlink()
