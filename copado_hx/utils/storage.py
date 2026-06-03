from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

_KEYRING_AVAILABLE = False
_KEYRING_SERVICE = "copado-hx"

try:
    import keyring as _kr
    _KEYRING_AVAILABLE = True
except Exception:
    pass


SECRETS_FILE = Path.home() / ".copado-hx-secrets.json"
BACKUP_FILE = Path.home() / ".copado-hx-secrets.backup"


def _keyring_supported() -> bool:
    if not _KEYRING_AVAILABLE:
        return False
    try:
        return _kr.get_keyring() is not None
    except Exception:
        return False


def store_secrets(secrets: Dict[str, str]) -> None:
    for k, v in secrets.items():
        if _keyring_supported():
            try:
                _kr.set_password(_KEYRING_SERVICE, k, v)
            except Exception:
                pass
    existing = {}
    if SECRETS_FILE.exists():
        try:
            existing = json.loads(SECRETS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    existing.update(secrets)
    payload = json.dumps(existing, indent=2)
    SECRETS_FILE.write_text(payload)
    SECRETS_FILE.chmod(0o600)
    BACKUP_FILE.write_text(payload)
    BACKUP_FILE.chmod(0o600)


def get_secret(key: str) -> Optional[str]:
    if _keyring_supported():
        try:
            val = _kr.get_password(_KEYRING_SERVICE, key)
            if val is not None:
                return val
        except Exception:
            pass
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text())
            return data.get(key)
        except (json.JSONDecodeError, OSError):
            return None
    return os.environ.get(f"COPADO_{key.upper()}")


def delete_secret(key: str) -> None:
    if _keyring_supported():
        try:
            _kr.delete_password(_KEYRING_SERVICE, key)
        except Exception:
            pass
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
    if _keyring_supported():
        try:
            for k in list(get_all_secrets().keys()):
                try:
                    _kr.delete_password(_KEYRING_SERVICE, k)
                except Exception:
                    pass
        except Exception:
            pass
    if SECRETS_FILE.exists():
        SECRETS_FILE.unlink()
