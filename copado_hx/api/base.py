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
    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=httpx.Timeout(timeout), verify=True)

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

    def _handle_error(self, resp: httpx.Response) -> None:
        status = resp.status_code
        body = ""
        try:
            body = resp.text[:500]
            detail = resp.json().get("message", resp.json().get("error", body))
        except (json.JSONDecodeError, ValueError, AttributeError):
            detail = body or resp.reason_phrase or "Unknown error"

        if status == 401:
            raise AuthError(f"Authentication failed: {detail}", status, body)
        elif status == 403:
            raise AuthError(f"Access denied: {detail}", status, body)
        elif status == 404:
            raise NotFoundError(f"Resource not found: {detail}", status, body)
        elif status == 429:
            raise RateLimitError(f"Rate limit exceeded: {detail}", status, body)
        elif status == 500:
            raise CopadoError(
                f"Server error (500): {detail}",
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
