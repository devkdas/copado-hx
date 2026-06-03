from __future__ import annotations

import random


def _rand_id(prefix: str = "a09XX0") -> str:
    return f"{prefix}{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))}"



def _gen_stories() -> list[dict]:
    return list(MOCK_STORIES)


def _gen_environments() -> list[dict]:
    return list(MOCK_ENVIRONMENTS)


def _gen_workflows() -> list[dict]:
    return list(MOCK_WORKFLOWS)


def _gen_test_jobs() -> list[dict]:
    return list(MOCK_TEST_JOBS)


def _gen_build_id() -> str:
    return str(random.randint(1000000, 9999999))


def _gen_test_build() -> dict:
    total = random.randint(30, 60)
    passed = random.randint(int(total * 0.75), total)
    failed = total - passed
    return {
        "id": _gen_build_id(),
        "buildStatus": "Succeeded" if passed > failed else "Failed",
        "totalTests": total,
        "passedTests": passed,
        "failedTests": failed,
        "duration": f"{random.randint(2, 8)}m {random.randint(0, 59)}s",
    }


def _gen_test_results() -> dict:
    passed_count = random.randint(30, 50)
    failed_count = random.randint(0, 8)
    total = passed_count + failed_count
    build_id = _gen_build_id()

    test_names = [
        "LeadScoringService.calculateScore",
        "LeadScoringService.validateInput",
        "LeadScoringService.getLeadSource",
        "LeadScoringBatchJob.execute",
        "LeadScoringBatchJob.finish",
        "LeadScoringTriggerHandler.beforeInsert",
        "LeadScoringTriggerHandler.beforeUpdate",
        "EmailCampaignService.sendBatch",
        "EmailCampaignService.validateRecipients",
        "EmailCampaignService.trackBounces",
        "OpportunityService.calculateRollup",
        "AccountService.mergeDuplicates",
        "AccountService.validateTaxId",
        "OrderService.calculateTotals",
        "OrderService.validateInventory",
        "PaymentService.processRefund",
        "PaymentService.validateCard",
        "ShippingService.calculateRates",
        "ShippingService.trackPackage",
        "NotificationService.sendAlert",
    ]
    random.shuffle(test_names)
    selected = test_names[:total]

    def gen_result(name: str) -> dict:
        return {
            "testName": name,
            "status": "Passed",
            "executionTime": f"{random.randint(10, 5000)}ms",
        }

    results = [gen_result(n) for n in selected]
    for i in range(min(failed_count, len(results))):
        results[i]["status"] = "Failed"
    random.shuffle(results)

    return {
        "id": build_id,
        "buildStatus": "Succeeded" if passed_count > 0 else "Failed",
        "totalTests": total,
        "passedTests": passed_count,
        "failedTests": failed_count,
        "duration": f"{random.randint(2, 10)}m {random.randint(0, 59)}s",
        "testResults": results,
    }


def _gen_ai_response(agent: str, prompt: str = "") -> dict:
    if agent == "build":
        response = (
            "### Recommended Apex Metadata for Lead Scoring\n\n"
            "#### 1. Custom Fields (on the `Lead` object)\n\n"
            "| Field Label | API Name | Type | Purpose |\n"
            "|---|---|---|---|\n"
            "| Lead Score | `Lead_Score__c` | Number | Total calculated score |\n"
            "| Score Last Updated | `Score_Last_Updated__c` | DateTime | Audit timestamp |\n"
            "| Score Grade | `Score_Grade__c` | Formula/Text | A/B/C/D rating based on score |\n"
            "| Scoring Notes | `Scoring_Notes__c` | Long Text | Debug/audit trail |\n\n"
            "#### 2. Apex Classes\n\n"
            "**`LeadScoringEngine.cls`** — Core scoring engine with all business rules.\n"
            "- Factors: Demographic (title, size, industry), Behavioral (email, web, forms), Firmographic (country, revenue)\n"
            "- Should be `public` with `@InvocableMethod` for Flow compatibility\n\n"
            "**`LeadScoringService.cls`** — Bulkified service layer accepting `List<Lead>`.\n"
            "- Calls `LeadScoringEngine` and applies results back\n\n"
            "**`LeadScoringConstants.cls`** — Centralized scoring weights and thresholds.\n\n"
            "**`LeadScoringScheduler.cls`** — Implements `Schedulable` for nightly re-scoring.\n\n"
            "**`LeadScoringBatch.cls`** — Implements `Database.Batchable<SObject>` for bulk re-scoring.\n\n"
            "**`LeadScoringTest.cls`** — Full coverage, >90%, uses `@testSetup`.\n\n"
            "#### 3. Apex Trigger\n\n"
            "**`LeadTrigger.trigger`** — Fires on `before insert` and `before update`, delegates to `LeadScoringService`.\n\n"
            "**`LeadTriggerHandler.cls`** — Handler pattern with `beforeInsert()`, `beforeUpdate()` methods.\n\n"
            "#### 4. Supporting Metadata\n\n"
            "- **Custom Metadata Type:** `Lead_Scoring_Rule__mdt` — declarative scoring rules\n"
            "- **Custom Setting:** `LeadScoringSettings__c` — enable/disable, batch size\n"
            "- **Custom Label:** `Lead_Score_Grade_*` — localizable grade labels\n\n"
            "Would you like me to generate any of these classes with actual code?\n"
        )
    elif agent == "test":
        response = (
            "### QWord Test Scripts for Lead Scoring\n\n"
            "#### Suite 1 — `LeadScoringService` Tests\n\n"
            "**Test Cases:**\n"
            "- TC01: High Quality Lead Receives High Score (>= 80)\n"
            "- TC02: Low Quality Lead Receives Low Score (<= 30)\n"
            "- TC03: Lead Score Field Visible on Record Page\n"
            "- TC04: Score Is Numeric and Within Valid Range (0–100)\n"
            "- TC05: Lead Without Company Has Score Assigned (Not Null)\n\n"
            "#### Suite 2 — `LeadScoringTriggerHandler` Tests\n\n"
            "**Test Cases:**\n"
            "- TC01: Score Increases When Rating Changes Cold→Hot\n"
            "- TC02: Score Changes When Industry Updated\n"
            "- TC03: Score Recalculates on Employee Count Increase\n"
            "- TC04: UI Verify Score Updates on Record Page\n"
            "- TC05: Trigger Does Not Fail on Unrelated Field Update\n\n"
            "#### Suite 3 — `LeadScoringBatchJob` Tests\n\n"
            "**Test Cases:**\n"
            "- TC01: Batch Job Executes Successfully via Anonymous Apex\n"
            "- TC02: Batch Job Updates Scores for Multiple Leads\n"
            "- TC03: Batch Scores Reflect Lead Quality Ranking\n"
            "- TC04: Batch Does Not Set Scores Above 100\n"
            "- TC05: Updated Scores Visible in UI After Batch\n"
            "- TC06: Batch via Developer Console\n"
        )
    elif any(kw in prompt.lower() for kw in ("fail", "error", "triage")):
        response = (
            "### Test Failure Analysis\n\n"
            "**Execution ID:** 5262294  \n"
            "**Result:** 39/42 passed (92.9% passing rate)\n\n"
            "#### Failed Tests\n\n"
            "| Test | Issue | Severity |\n"
            "|------|-------|----------|\n"
            "| EmailCampaignService.sendBatch | Timeout at 5000ms — rate limiting | Medium |\n"
            "| OpportunityService.calculateRollup | Null reference — no line items | High |\n\n"
            "#### Deployment Confidence\n\n"
            "**Score: 92%** — Fix the high-severity `calculateRollup` before PROD promotion.\n"
        )
    elif any(kw in prompt.lower() for kw in ("deploy", "promote", "release")):
        response = (
            "### Deployment Analysis\n\n"
            "Your story is ready for promotion.\n\n"
            "#### Checks\n\n"
            "- Tests passing (39/42)\n"
            "- No merge conflicts\n"
            "- Metadata coverage complete\n\n"
            "#### Recommendation\n\n"
            "**Safe to deploy.** No blockers detected.\n"
        )
    else:
        response = (
            "### Analysis Results\n\n"
            "I've analyzed your request. Here are the key findings:\n\n"
            "#### Architecture\n\n"
            "- **Service Layer:** `LeadScoringService` handles core business logic\n"
            "- **Trigger Layer:** `LeadScoringTriggerHandler` manages DML events\n"
            "- **Batch Layer:** `LeadScoringBatchJob` processes large volumes\n\n"
            "#### Next Steps\n\n"
            "1. Review the proposed architecture\n"
            "2. Generate test classes for each component\n"
            "3. Deploy to UAT for validation\n"
        )
    return {
        "agent": agent,
        "dialogue_id": f"dialogue-{_rand_id()}",
        "model": agent,
        "response": response,
        "usage": {"prompt_tokens": random.randint(200, 1000), "completion_tokens": random.randint(100, 500), "total_tokens": random.randint(300, 1500)},
    }


class MockCrtClient:
    def __init__(self, *args, **kwargs):
        self.timeout = 300

    def list_jobs(self) -> list[dict]:
        return _gen_test_jobs()

    def list_jobs_detailed(self) -> list[dict]:
        return _gen_test_jobs()

    def trigger_build(self, job_id: str) -> dict:
        bid = _gen_build_id()
        return {"data": {"id": bid, "buildId": bid}}

    def get_build_status(self, job_id: str, build_id: str) -> dict:
        return _gen_test_build()

    def get_build_results(self, job_id: str, build_id: str) -> dict:
        return _gen_test_results()

    def get_build_results_formatted(self, job_id: str, build_id: str, fmt: str = "pdf") -> bytes:
        from copado_hx.api.crt import CrtClient
        text = CrtClient._format_as_report(_gen_test_results(), build_id)
        return text.encode("utf-8")

    def close(self):
        pass


class MockSalesforceRestClient:
    def __init__(self, *args, **kwargs):
        self.timeout = 60

    def query(self, soql: str) -> list[dict]:
        return _gen_stories()

    def get_user_stories(self, pipeline: str = None, status: str = None) -> list[dict]:
        return get_mock_user_stories(pipeline, status)

    def get_user_story(self, story_id: str) -> dict | None:
        return get_mock_user_story(story_id)

    def create_user_story(self, name: str, pipeline_id: str) -> dict:
        return {"id": _rand_id("a09XX0"), "Id": _rand_id("a09XX0"), "success": True}

    def get_environments(self) -> list[dict]:
        return _gen_environments()

    def resolve_environment(self, env_name: str) -> dict | None:
        for e in _gen_environments():
            if e["Name"] == env_name:
                return e
        return None

    def get_pipelines(self) -> list[dict]:
        return _gen_workflows()

    def query_one(self, soql: str) -> dict | None:
        rows = self.query(soql)
        return rows[0] if rows else None

    def close(self):
        pass


class MockActionsApiClient:
    def __init__(self, *args, **kwargs):
        self._base_url = ""
        self._webhook_key = ""

    def commit(self, story_id: str, message: str) -> dict:
        return dict(MOCK_COMMIT_RESULT)

    def promote(self, story_id: str, environment: str, validate_only: bool = False) -> dict:
        return dict(MOCK_PROMOTE_RESULT)

    def deploy(self, story_id: str, environment: str) -> dict:
        return dict(MOCK_DEPLOY_RESULT)

    def close(self):
        pass


class MockCopadoCicdClient:
    def __init__(self, *args, **kwargs):
        self.timeout = 120

    def list_workflows(self) -> list[dict]:
        return _gen_workflows()

    def trigger_workflow(self, workflow_id: str, parameters: dict = None, workspace_id: str = None) -> dict:
        return dict(MOCK_WORKFLOW_RUN)

    def get_run(self, run_id: str) -> dict:
        return {"id": run_id, "status": "succeeded"}

    def close(self):
        pass


class MockAiPlatformClient:
    STREAM_DELAY = 0.03

    def __init__(self, *args, **kwargs):
        self.timeout = 300

    def ask_agent(self, agent_id: str, prompt: str) -> dict:
        return get_mock_ai_response(agent_id, prompt)

    def ask_agent_stream(self, agent_id: str, prompt: str):
        import time
        text = get_mock_ai_response(agent_id, prompt).get("response", "")
        words = text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            time.sleep(self.STREAM_DELAY)

    def chat_agent(self, agent_id: str, prompt: str, history: list[dict] = None) -> dict:
        return get_mock_ai_response(agent_id, prompt)

    def close(self):
        pass


MOCK_STORIES = [
    {
        "Id": "a1vhk0000000P01AAE",
        "Name": "US-0000024",
        "copado__Status__c": "Draft",
        "copado__User_Story_Title__c": "My first Source Format User Story",
        "Environment": "Dev1-SFP",
        "Developer": None,
        "Project": "a15hk0000002cnZAAQ",
        "LastModifiedDate": "2026-05-27T07:10:46.000+0000",
    },
]

MOCK_ENVIRONMENTS = [
    {"Id": "a0chk0000000oknAAA", "Name": "Copado", "copado__Type__c": "Production/Developer"},
    {"Id": "a0chk0000000osrAAA", "Name": "Dev1-SFP", "copado__Type__c": "Sandbox"},
    {"Id": "a0chk0000000ntaAAA", "Name": "Dev2-SFP", "copado__Type__c": "Sandbox"},
    {"Id": "a0chk0000000oo1AAA", "Name": "Hotfix-SFP", "copado__Type__c": "Sandbox"},
    {"Id": "a0chk0000000orFAAQ", "Name": "INT-SFP", "copado__Type__c": "Sandbox"},
    {"Id": "a0chk0000000omPAAQ", "Name": "Production-SFP", "copado__Type__c": "Sandbox"},
    {"Id": "a0chk0000000opdAAA", "Name": "UAT-SFP", "copado__Type__c": "Sandbox"},
]

MOCK_WORKFLOWS = [
    {"id": "6b85a2c7-2fd", "title": "Create Agentforce Agent from Copado User Story", "nodes": []},
    {"id": "16615d17-a81", "title": "Build User Story, Test, and Deploy", "nodes": []},
    {"id": "6a3b23d4-c9b", "title": "WIP Workflow (SF CLI)", "nodes": []},
    {"id": "8d80cd64-736", "title": "Code Quality Review and Fix", "nodes": []},
    {"id": "d4e5f6a7-b8c", "title": "Rapid Issue Resolution", "nodes": []},
    {"id": "8e19fcd1-059", "title": "Release notes for Copado Releases", "nodes": []},
    {"id": "a8bd38ac-e83", "title": "Technical Debt Resolution", "nodes": []},
]

MOCK_TEST_JOBS = [
    {"id": "120561", "name": "CLI-Target-Job", "type": ""},
]

MOCK_TEST_BUILD = {
    "id": "5249906",
    "buildStatus": "Succeeded",
    "totalTests": 42,
    "passedTests": 39,
    "failedTests": 3,
    "duration": "4m 32s",
}

MOCK_TEST_RESULTS = {
    "id": "5249906",
    "buildStatus": "Succeeded",
    "totalTests": 42,
    "passedTests": 39,
    "failedTests": 3,
    "duration": "4m 32s",
    "testResults": [
        {"testName": "LeadScoringService.calculateScore", "status": "Passed", "executionTime": "230ms"},
        {"testName": "LeadScoringService.validateInput", "status": "Passed", "executionTime": "120ms"},
        {"testName": "LeadScoringService.getLeadSource", "status": "Passed", "executionTime": "95ms"},
        {"testName": "LeadScoringBatchJob.execute", "status": "Passed", "executionTime": "1450ms"},
        {"testName": "LeadScoringBatchJob.finish", "status": "Passed", "executionTime": "80ms"},
        {"testName": "LeadScoringTriggerHandler.beforeInsert", "status": "Passed", "executionTime": "310ms"},
        {"testName": "LeadScoringTriggerHandler.beforeUpdate", "status": "Passed", "executionTime": "290ms"},
        {"testName": "EmailCampaignService.sendBatch", "status": "Failed", "executionTime": "5000ms"},
        {"testName": "EmailCampaignService.validateRecipients", "status": "Passed", "executionTime": "45ms"},
        {"testName": "EmailCampaignService.trackBounces", "status": "Failed", "executionTime": "3200ms"},
        {"testName": "OpportunityService.calculateRollup", "status": "Failed", "executionTime": "1800ms"},
    ],
}

MOCK_AI_RESPONSE = {
    "agent": "build",
    "dialogue_id": "dialogue-mock-001",
    "model": "build",
    "response": (
        "### Recommended Apex Metadata for Lead Scoring\n\n"
        "#### 1. Custom Fields (on the `Lead` object)\n\n"
        "| Field Label | API Name | Type | Purpose |\n"
        "|---|---|---|---|\n"
        "| Lead Score | `Lead_Score__c` | Number | Total calculated score |\n"
        "| Score Last Updated | `Score_Last_Updated__c` | DateTime | Audit timestamp |\n"
        "| Score Grade | `Score_Grade__c` | Formula/Text | A/B/C/D rating based on score |\n"
        "| Scoring Notes | `Scoring_Notes__c` | Long Text | Debug/audit trail |\n\n"
        "#### 2. Apex Classes\n\n"
        "**`LeadScoringEngine.cls`** — Core scoring engine with all business rules.\n"
        "- Factors: Demographic, Behavioral, Firmographic\n"
        "- Should be `public` with `@InvocableMethod` for Flow compatibility\n\n"
        "**`LeadScoringService.cls`** — Bulkified service layer.\n"
        "- Calls `LeadScoringEngine` and applies results back\n\n"
        "**`LeadScoringConstants.cls`** — Centralized scoring weights and thresholds.\n\n"
        "**`LeadScoringScheduler.cls`** — Implements `Schedulable` for nightly re-scoring.\n\n"
        "**`LeadScoringBatch.cls`** — Implements `Database.Batchable<SObject>` for bulk re-scoring.\n\n"
        "**`LeadScoringTest.cls`** — Full coverage, >90%, uses `@testSetup`.\n\n"
        "#### 3. Apex Trigger\n\n"
        "**`LeadTrigger.trigger`** — Fires on `before insert` and `before update`, delegates to handler.\n\n"
        "**`LeadTriggerHandler.cls`** — Handler pattern with `beforeInsert()`, `beforeUpdate()` methods.\n\n"
        "#### 4. Supporting Metadata\n\n"
        "- **Custom Metadata Type:** `Lead_Scoring_Rule__mdt` — declarative scoring rules\n"
        "- **Custom Setting:** `LeadScoringSettings__c` — enable/disable, batch size\n\n"
        "Would you like me to generate any of these classes with actual code?\n"
    ),
    "usage": {"prompt_tokens": 845, "completion_tokens": 210, "total_tokens": 1055},
}

MOCK_COMMIT_RESULT = {"Id": "a0shk0000000wjxAAA", "copado__Status__c": "In Progress"}

MOCK_PROMOTE_RESULT = {"Id": "a0shk0000000wlZAAQ", "copado__Status__c": "In Progress"}

MOCK_DEPLOY_RESULT = {"Id": "a0shk0000000wlZAAQ", "copado__Status__c": "In Progress"}

MOCK_WORKFLOW_RUN = {"id": "run-abcdef", "status": "succeeded"}


def get_mock_user_stories(pipeline: str = None, status: str = None) -> list[dict]:
    results = list(MOCK_STORIES)
    if pipeline:
        results = [s for s in results if s.get("copado__Pipeline__c") == pipeline]
    if status:
        results = [s for s in results if s.get("copado__Status__c") == status]
    return results


def get_mock_user_story(story_id: str) -> dict | None:
    for s in MOCK_STORIES:
        if s["Id"] == story_id or s["Name"] == story_id:
            return s
    return None


def get_mock_environments() -> list[dict]:
    return MOCK_ENVIRONMENTS


def get_mock_workflows() -> list[dict]:
    return MOCK_WORKFLOWS


def get_mock_ai_response(agent: str, prompt: str = "") -> dict:
    return _gen_ai_response(agent, prompt)
