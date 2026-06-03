from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx


class CopadoError(Exception):
    def __init__(self, message: str, status_code: int = 0, raw_response: Optional[str] = None):
        self.status_code = status_code
        self.raw_response = raw_response
        super().__init__(message)


class AuthError(CopadoError):
    pass


class NotFoundError(CopadoError):
    pass


class RateLimitError(CopadoError):
    pass


class BaseApiClient:
    def __init__(self, base_url: str, timeout: int = 60, connect_timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=connect_timeout),
            verify=True,
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._headers()
        extra_headers = kwargs.pop("headers", {})
        headers.update(extra_headers)

        try:
            resp = self._client.request(method, url, headers=headers, **kwargs)
        except httpx.TimeoutException:
            raise CopadoError(f"Request timed out after {self.timeout}s", 0)
        except httpx.ConnectError as e:
            raise CopadoError(f"Connection failed: {e}", 0)

        if resp.status_code >= 400:
            self._handle_error(resp)

        if resp.status_code == 204:
            return {"status": "success"}

        try:
            return resp.json()
        except (json.JSONDecodeError, ValueError):
            return {"raw": resp.text, "status_code": resp.status_code}

    def _diagnose_401(self, resp: httpx.Response, body: str, detail: str) -> str:
        msg = str(body).lower() + str(detail).lower()
        if "invalid_session_id" in msg or "session expired" in msg:
            return (
                "Salesforce session expired or invalid.\n"
                "  → Re-run: copado-hx auth login\n"
                "  → Or configure OAuth password flow with sf_client_id / sf_client_secret"
            )
        if "unauthorized" in msg or "invalid" in msg:
            return (
                "Invalid credentials.\n"
                "  → Check your API key or access token\n"
                "  → Run: copado-hx auth status"
            )
        return (
            "Authentication failed.\n"
            "  → Run: copado-hx auth login to re-authenticate"
        )

    def _diagnose_403(self, resp: httpx.Response, body: str, detail: str) -> str:
        msg = str(body).lower() + str(detail).lower()
        if "webhook" in msg or "copado-webhook-key" in msg or "actions" in msg:
            return (
                "Copado Actions API Key appears invalid or missing.\n"
                "  → Generate a new key: App Launcher > Copado Actions API > API Keys\n"
                "  → Update it with: copado-hx auth login --type actions"
            )
        return (
            "Access denied — possible causes:\n"
            "  1. API key is wrong → regenerate in App Launcher\n"
            "  2. Pipeline is not source-format → check pipeline settings\n"
            "  3. User lacks Copado_User permission set"
        )

    def _handle_error(self, resp: httpx.Response) -> None:
        status = resp.status_code
        body = ""
        try:
            body = resp.text[:500]
            detail = resp.json().get("message", resp.json().get("error", body))
        except (json.JSONDecodeError, ValueError, AttributeError):
            detail = body or resp.reason_phrase or "Unknown error"

        if status == 401:
            hints = self._diagnose_401(resp, body, detail)
            raise AuthError(f"Authentication failed ({status}): {detail}\n\n{hints}", status, body)
        elif status == 403:
            hints = self._diagnose_403(resp, body, detail)
            raise AuthError(f"Access denied ({status}): {detail}\n\n{hints}", status, body)
        elif status == 404:
            raise NotFoundError(
                f"Resource not found ({status}): {detail}\n\n"
                "  → Check the ID is correct (18-char Salesforce ID or valid name)\n"
                "  → Run discovery commands: copado-hx story list, copado-hx environments",
                status, body,
            )
        elif status == 429:
            raise RateLimitError(
                f"Rate limit exceeded ({status}): {detail}\n\n"
                "  → Wait a few seconds and retry\n"
                "  → Reduce request frequency",
                status, body,
            )
        elif status == 500:
            raise CopadoError(
                f"Server error (500): {detail}\n\n"
                "  → Copado server error — retry after a few seconds\n"
                "  → If persistent, your API key may be expired — re-run: copado-hx auth login\n"
                "  → Or check Salesforce status at trust.salesforce.com",
                status, body,
            )
        else:
            raise CopadoError(f"API error ({status}): {detail}", status, body)

    def get(self, path: str, **kwargs) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Any:
        return self._request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs) -> Any:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Any:
        return self._request("DELETE", path, **kwargs)

    def close(self):
        self._client.close()
