from __future__ import annotations

from typing import Optional

from copado_hx.api import BaseApiClient


class SalesforceRestClient(BaseApiClient):
    def __init__(self, instance_url: str, access_token: str):
        base = instance_url.rstrip("/")
        super().__init__(base, timeout=60)
        self._access_token = access_token
        self._api_version = "v61.0"

    def _headers(self) -> dict[str, str]:
        h = super()._headers()
        h["Authorization"] = f"Bearer {self._access_token}"
        return h

    def query(self, soql: str) -> list[dict]:
        import urllib.parse
        result = self.get(f"/services/data/{self._api_version}/query?q={urllib.parse.quote(soql)}")
        return result.get("records", [])

    def get_user_stories(self, pipeline: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        conditions = []
        if pipeline:
            conditions.append(f"copado__Pipeline__r.Name = '{pipeline}'")
        if status:
            conditions.append(f"copado__Status__c = '{status}'")
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        return self.query(
            f"SELECT Id, Name, copado__Status__c, copado__User_Story_Title__c "
            f"FROM copado__User_Story__c{where} "
            f"ORDER BY LastModifiedDate DESC"
        )

    def get_user_story(self, story_id: str) -> Optional[dict]:
        # Support both 18-char Id and Name (e.g., US-0000024)
        field = "Name" if story_id.startswith("US-") else "Id"
        records = self.query(
            f"SELECT Id, Name, copado__Status__c, copado__User_Story_Title__c "
            f"FROM copado__User_Story__c WHERE {field} = '{story_id}'"
        )
        return records[0] if records else None

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

    def get_pipelines(self) -> list[dict]:
        return self.query("SELECT Id, Name, copado__Status__c FROM copado__Pipeline__c ORDER BY Name")
