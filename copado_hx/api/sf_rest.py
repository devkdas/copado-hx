from __future__ import annotations

import urllib.parse
from typing import Any, Optional

from copado_hx.api import BaseApiClient, AuthError, CopadoError


class SalesforceRestClient(BaseApiClient):
    def __init__(self, instance_url: str, access_token: str):
        base = instance_url.rstrip("/")
        super().__init__(base, timeout=60)
        self._access_token = access_token
        self._api_version = "v61.0"
        self._auto_refresh = True

    def _headers(self) -> dict[str, str]:
        h = super()._headers()
        h["Authorization"] = f"Bearer {self._access_token}"
        return h

    def _try_refresh_token(self) -> bool:
        import os
        from copado_hx.api import AuthError as CopadoAuthError
        from copado_hx.auth.salesforce import login_password_grant
        from copado_hx.utils.storage import get_secret, store_secrets

        client_id = get_secret("sf_client_id") or ""
        client_secret = get_secret("sf_client_secret") or ""
        username = get_secret("sf_username") or ""
        password = get_secret("sf_password") or os.environ.get("COPADO_SF_PASSWORD", "")
        if not all([client_id, client_secret, username, password]):
            return False

        instance_url = get_secret("sf_instance_url") or self.base_url
        try:
            result = login_password_grant(
                client_id, client_secret, username, password, instance_url=instance_url,
            )
            self._access_token = result["access_token"]
            store_secrets({"sf_access_token": result["access_token"]})
            return True
        except CopadoAuthError:
            return False

    def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            return super()._request(method, path, **kwargs)
        except AuthError:
            if not self._auto_refresh or not self._try_refresh_token():
                raise
            try:
                return super()._request(method, path, **kwargs)
            except AuthError:
                self._auto_refresh = False
                raise

    def query(self, soql: str) -> list[dict]:
        result = self.get(f"/services/data/{self._api_version}/query?q={urllib.parse.quote(soql)}")
        return result.get("records", [])

    def query_one(self, soql: str) -> dict | None:
        records = self.query(soql)
        return records[0] if records else None

    _STORY_FIELDS = (
        "Id, Name, copado__Status__c, copado__User_Story_Title__c, "
        "copado__Environment__c, copado__Environment__r.Name, "
        "copado__Developer__c, copado__Project__c, "
        "LastModifiedDate, CreatedDate"
    )

    def _normalize_story(self, record: dict) -> dict:
        env_rel = record.get("copado__Environment__r") or {}
        env_name = env_rel.get("Name", "") if isinstance(env_rel, dict) else ""
        return {
            "Id": record.get("Id", ""),
            "Name": record.get("Name", ""),
            "copado__Status__c": record.get("copado__Status__c", "Unknown"),
            "copado__User_Story_Title__c": record.get("copado__User_Story_Title__c", ""),
            "Environment": env_name or record.get("copado__Environment__c", ""),
            "Developer": record.get("copado__Developer__c", ""),
            "Project": record.get("copado__Project__c", ""),
            "LastModifiedDate": record.get("LastModifiedDate", ""),
        }

    def get_user_stories(self, pipeline: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        conditions = []
        if pipeline:
            conditions.append(f"copado__Pipeline__c = '{pipeline}'")
        if status:
            conditions.append(f"copado__Status__c = '{status}'")
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        raw = self.query(
            f"SELECT {self._STORY_FIELDS} FROM copado__User_Story__c{where} "
            f"ORDER BY LastModifiedDate DESC"
        )
        return [self._normalize_story(r) for r in raw]

    def get_user_story(self, story_id: str) -> Optional[dict]:
        field = "Name" if story_id.startswith("US-") else "Id"
        records = self.query(
            f"SELECT {self._STORY_FIELDS} FROM copado__User_Story__c WHERE {field} = '{story_id}'"
        )
        return self._normalize_story(records[0]) if records else None

    def create_user_story(self, name: str, pipeline_id: str) -> dict:
        return self.post(
            f"/services/data/{self._api_version}/sobjects/copado__User_Story__c",
            json={
                "Name": name,
                "copado__Pipeline__c": pipeline_id,
            },
        )

    def get_environments(self) -> list[dict]:
        return self.query(
            "SELECT Id, Name, copado__Type__c FROM copado__Environment__c ORDER BY Name"
        )

    def resolve_environment(self, env_name: str) -> Optional[dict]:
        records = self.query(
            f"SELECT Id, Name, copado__Type__c "
            f"FROM copado__Environment__c WHERE Name = '{env_name}' LIMIT 1"
        )
        return records[0] if records else None

    def get_pipelines(self) -> list[dict]:
        try:
            return self.query("SELECT Id, Name, copado__Status__c FROM copado__Pipeline__c ORDER BY Name")
        except CopadoError:
            return []

    def troubleshoot_pipeline(self, pipeline_id: str) -> Optional[str]:
        try:
            record = self.query_one(
                f"SELECT Id, Name, copado__Platform__c "
                f"FROM copado__Pipeline__c WHERE Id = '{pipeline_id}' LIMIT 1"
            )
            if not record:
                return (
                    f"Pipeline '{pipeline_id}' not found via SOQL.\n"
                    "  → Verify the 18-char Salesforce ID is correct\n"
                    "  → Run: copado-hx status  to list available pipelines"
                )
            platform = record.get("copado__Platform__c", "")
            if platform and "source" not in platform.lower():
                return (
                    f"Pipeline '{record.get('Name', '')}' platform is '{platform}'.\n"
                    "  Actions API requires a source-format pipeline.\n"
                    "  → In Copado Setup, set Pipeline Platform = 'Salesforce' with 'Source Format' enabled."
                )
            return None
        except CopadoError:
            return "Pipeline object not available in this org."
