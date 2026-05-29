# Identity

You have access to `copado-hx`, a CLI that gives you full control over the Copado DevOps platform for Salesforce. Through this skill you can manage user stories, trigger CI/CD pipeline actions (commit, promote, validate, deploy), execute Copado Robotic Testing (CRT) test suites, and converse with Copado's 5 specialist AI agents (Plan, Build, Test, Release, Operate) — all without opening a browser.

`copado-hx` connects to three Copado API surfaces:
- **Copado CI/CD** — Commits, promotions, deployments via the Actions API (RunJobTemplate); workflow listing/running via the AI Platform API
- **Copado Robotic Testing (CRT)** — Test execution, status polling, results retrieval via robotic testing API
- **Copado AI Context Hub** — Conversations with 5 specialist agent personas (Plan, Build, Test, Release, Operate)

# Prerequisites

- `copado-hx ai ask --agent <name> <question>` is the primary interaction method — use it before starting any task to gather context.
- `copado-hx auth status` must return an authenticated session before any other command.
- If not authenticated, instruct the user to run `copado-hx auth login` and pause.
- A working user story context must be set with `copado-hx story set` before commit, promote, or deploy operations.
- Never infer or fabricate workflow IDs, environment names, or user story IDs. Always retrieve them from `copado-hx story list` or `copado-hx status`.
- API credentials must never be committed to source code or logged to output.
- CI/CD commit/promote/deploy use the Actions API (`webhookKey` from Account Summary). Workflow list/run use the AI Platform API (AI API key). No separate Salesforce session required.

# Commands Reference

## `copado-hx auth login`
**Purpose:** Authenticate with all Copado services.
**When to use:** Before any other operation.
**Syntax:** `copado-hx auth login [--token <ai-api-key>] [--crt-pak <pak>]`
**Output:** Interactive flow: 1) browser opens for Salesforce OAuth, 2) prompt for AI API key, 3) prompt for CRT PAK.
**Example:** `copado-hx auth login`
**Single-service:** `copado-hx auth login --token <ai-key>` or `copado-hx auth login --crt-pak <pak>`

## `copado-hx auth status`
**Purpose:** Check current authentication status across all services.
**Syntax:** `copado-hx auth status [--json]`
**Output:** Shows Salesforce (CI/CD), AI Platform, and CRT authentication status.
**Example:** `copado-hx auth status`

## `copado-hx auth logout`
**Purpose:** Clear stored credentials and end session.
**Syntax:** `copado-hx auth logout [--all]`
**Example:** `copado-hx auth logout --all`

## `copado-hx story list`
**Purpose:** List user stories from Copado CI/CD.
**Syntax:** `copado-hx story list [--pipeline <id>] [--status <status>] [--json]`
**Output:** Table or JSON array of user stories with ID, Name, Status, Subject.
**Example:** `copado-hx story list --status "In Progress"`

## `copado-hx story show`
**Purpose:** Show detailed information about a specific user story.
**Syntax:** `copado-hx story show [<story_id>] [--json]`
**Output:** Story details including ID, status, subject, description, pipeline.

## `copado-hx story set`
**Purpose:** Set a user story as the current working context (like `git checkout`).
**Syntax:** `copado-hx story set <story_id>`
**Output:** Confirmation with story name.
**Do not use if:** Story ID is not known. Run `copado-hx story list` first.

## `copado-hx story create`
**Purpose:** Create a new user story.
**Syntax:** `copado-hx story create --title "<title>" [--pipeline <id>] [--json]`

## `copado-hx commit`
**Purpose:** Triggers a CI/CD workflow that commits metadata changes from the current user story to Git.
**When to use:** After the developer has made local code/config changes and wants to push them to the feature branch.
**Syntax:** `copado-hx commit [--message <msg>] [--us <id>] [--json]`
**Output:** JSON with `{ workflow_run_id, status }`
**Example:** `copado-hx commit --message "feat: add lead scoring"`
**Do not use if:** No user story context is set. Run `copado-hx story set` first.
**Behind the scenes:** Triggers via the Actions API (RunJobTemplate sfdx_commit_1).

## `copado-hx promote`
**Purpose:** Triggers a CI/CD workflow that promotes a user story to the next environment.
**Flags:**
- `--validate` : Run a validation-only promotion (no actual deploy)
- `--env <name>` : Target environment (e.g., UAT, SIT, PROD)
**Output:** JSON with `{ workflow_run_id, status }`
**Poll for completion:** Use `copado-hx status --job <run_id> --watch`
**Example:** `copado-hx promote --env UAT --validate`
**Behind the scenes:** Triggers via the Actions API (RunJobTemplate sfdx_promote_1).

## `copado-hx deploy`
**Purpose:** Triggers a workflow that deploys a user story to a target environment (requires approval gate confirmation for PROD).
**Syntax:** `copado-hx deploy [--us <id>] [--env <name>] [--force] [--json]`
**Output:** Confirmation or error containing `{ workflow_run_id }`.
**Guardrail:** `copado-hx deploy` to PROD requires explicit human confirmation via interactive prompt.

## `copado-hx validate`
**Purpose:** Run a validation-only deployment.
**Syntax:** `copado-hx validate [--us <id>] [--env <name>] [--json]`

## `copado-hx workflow list`
**Purpose:** List available CI/CD workflows on the Copado AI Platform.
**Syntax:** `copado-hx workflow list [--json]`

## `copado-hx workflow run`
**Purpose:** Trigger a specific workflow by ID with parameters.
**Syntax:** `copado-hx workflow run <workflow_id> [--param key=value...] [--json]`
**Example:** `copado-hx workflow run 8e19fcd1 --param release_id_or_name=REL-1001`
**Note:** Runs are monitored via `copado-hx status --run <run_id>`.

## `copado-hx status`
**Purpose:** Show pipeline/validation job status, workflow run status, or list environments.
**Syntax:** `copado-hx status [--job <id>] [--run <id>] [--watch] [--json]`
**Example:** `copado-hx status --run abc123 --watch`

## `copado-hx environments`
**Purpose:** List available pipeline environments.
**Syntax:** `copado-hx environments [--json]`

## `copado-hx test list`
**Purpose:** List available CRT test suites and jobs.
**Syntax:** `copado-hx test list [--json]`
**Output:** Table or JSON array with Job ID, Name, Type.

## `copado-hx test run`
**Purpose:** Triggers a CRT test suite or job execution.
**Syntax:** `copado-hx test run [--suite <id>] [--job <id>] [--json]`
**Output:** JSON with `{ executionId, status, projectId, jobId }`
**Poll for results:** Use `copado-hx test status --execution <id>` until status is `Succeeded` or `Failed`. Then call `copado-hx test results`.
**Note:** `--suite` is a convenience alias for a CRT jobId.

## `copado-hx test status`
**Purpose:** Poll execution status of a CRT test run.
**Syntax:** `copado-hx test status --execution <id> [--watch] [--json]`
**Example:** `copado-hx test status --execution 12345 --watch`

## `copado-hx test results`
**Purpose:** Retrieve CRT test results (JUnit-compatible output).
**Syntax:** `copado-hx test results --execution <id> [--format json|pdf|junit] [--json]`
**Example:** `copado-hx test results --execution 12345 --format json`

## `copado-hx ai ask`
**Purpose:** Sends a prompt to one of the 5 Copado AI specialist agents.
**Agents:** plan | build | test | release | operate
**Syntax:** `copado-hx ai ask --agent <id> "<prompt>" [--us <story_id>] [--json]`
**Output:** Streaming text response from the agent.
**When to use each agent:**
- `plan`: User story refinement, conflict detection, sprint planning
- `build`: Code generation, metadata analysis, coverage improvement
- `test`: QWord test script generation, automation advice
- `release`: Deployment coordination, job error analysis, release notes
- `operate`: Post-release docs, change management, troubleshooting guides

## `copado-hx ai chat`
**Purpose:** Opens an interactive REPL with a Copado AI agent.
**Syntax:** `copado-hx ai chat --agent <id> [--us <story_id>]`
**Example:** `copado-hx ai chat --agent build`
**Example:** `copado-hx ai chat --agent release --us US-1234`

## `copado-hx mcp`
**Purpose:** Start the MCP server for agent discovery.
**Syntax:** `copado-hx mcp [--transport stdio]`
**When to use:** When an MCP-compatible agent needs to discover copado-hx tools natively.

## `copado-hx config`
**Purpose:** Manage copado-hx configuration.
**Syntax:** `copado-hx config [--show] [--init]`
**Example:** `copado-hx config --init`

# Workflow Playbooks

## Playbook: Full Story Delivery (Commit → UAT → Test → PROD)

Use this when the developer says: "ship my user story", "promote to prod", "deploy US-1234 end to end", or similar.

**Steps:**
1. Verify auth: `copado-hx auth status`
2. Set context: `copado-hx story set --id <us-id>`
3. Ask Build Agent for commit guidance: `copado-hx ai ask --agent build "What metadata should I commit for <us-id>?"`
4. Commit: `copado-hx commit --message "<generated message>"`
5. Promote + validate to UAT: `copado-hx promote --env UAT --validate`
6. Poll until complete: `copado-hx status --job <jobExecutionId> --watch`
7. Run CRT smoke tests: `copado-hx test run --suite <smoke-suite-id>` (Note: --suite is a convenience alias for a CRT jobId — retrieve it from `copado-hx test list`)
8. Poll test results: `copado-hx test status --execution <id> --watch`
9. **STOP. Ask the human:** "Tests passed. Shall I proceed to deploy to PROD?"
10. Only on explicit human approval: `copado-hx deploy --env PROD`
11. Generate release notes: `copado-hx ai ask --agent release "Generate release notes for <us-id>"`

## Playbook: Investigate a Failed Deployment

Use this when the developer says: "why did my deployment fail?", "fix my pipeline error".

**Steps:**
1. `copado-hx status` → retrieve the failed job execution ID
2. `copado-hx ai ask --agent release "Analyze the job execution error for <jobExecutionId>"`
3. Present the root cause and suggested fix to the developer.
4. If a code fix is needed: `copado-hx ai ask --agent build "Fix the issue: <error summary>"`

## Playbook: Generate and Run a Test

Use this when the developer says: "write a test for my class", "test this feature".

**Steps:**
1. `copado-hx ai ask --agent test "Generate a CRT QWord test script for <class/feature>"`
2. Present the generated script to the developer for review.
3. **STOP. Ask the human:** "Shall I trigger this test suite?"
4. On approval: `copado-hx test run --suite <id>` (Note: --suite is a convenience alias for a CRT jobId — retrieve it from `copado-hx test list`)
5. `copado-hx test results --execution <id>`

## Playbook: Discover and Set Working Context

Use this when the developer says: "what am I working on?", "show my stories", "set up my context".

**Steps:**
1. `copado-hx story list --status "In Progress"` → show active stories
2. Present the list to the developer and ask which story to work on.
3. On selection: `copado-hx story set --id <selected-id>`
4. Confirm: `copado-hx story show`

## Playbook: Full AI-Assisted Sprint Cycle

Use this when the developer starts a new sprint task.

**Steps:**
1. "What's the next story I should work on?" → `copado-hx story list --status "To Do"`
2. Set context: `copado-hx story set --id <id>`
3. Ask Plan Agent to refine: `copado-hx ai ask --agent plan "Refine user story <id> and check for metadata conflicts"`
4. Present the refined story to the developer.
5. Ask Build Agent for implementation guidance: `copado-hx ai ask --agent build "How should I implement story <id>? What Apex classes needed?"`
6. Wait for developer to implement the code changes.
7. Ask Build Agent to review: `copado-hx ai ask --agent build "Review these changes for story <id>: <diff summary>"`
8. Commit: `copado-hx commit --message "feat: implement <feature>"`
9. Ask Test Agent: `copado-hx ai ask --agent test "Generate tests for the changes in story <id>"`
10. Promote to UAT: `copado-hx promote --env UAT`
11. Run tests: `copado-hx test run --suite <id>`
12. Ask Release Agent: `copado-hx ai ask --agent release "Is story <id> ready for PROD? Check deployment status and blockers."`
13. **STOP. Ask the human:** deploy approval.
14. `copado-hx deploy --env PROD`
15. Generate release notes: `copado-hx ai ask --agent release "Generate release notes for story <id>"`
16. Ask Operate Agent: `copado-hx ai ask --agent operate "Create training and change management docs for this release"`

# Guardrails — What Agents Must Never Do

**Never deploy to a PROD or production environment without explicit human confirmation.** Always pause and ask: "I'm about to deploy to PROD. Please confirm."

**Never fabricate or guess IDs** (user story IDs, pipeline IDs, environment names, suite IDs). Always retrieve them from the CLI first using `copado-hx story list`, `copado-hx environments`, or `copado-hx test list`.

**Never run `copado-hx deploy` immediately after `copado-hx promote`** without checking test results and receiving human approval.

**Never store or log API tokens** in any output, file, or message.

**Never chain more than 3 destructive actions** (commit, promote, deploy) without a human checkpoint between each stage.

**Always surface test failures to the human** before proceeding to the next pipeline stage. Do not auto-retry failed tests.

**Never assume API credentials or configuration.** If `copado-hx auth status` shows any service as unauthenticated, stop and inform the human.

**Never infer pipeline or environment relationships.** Use `copado-hx environments` and `copado-hx status` to discover them.

**The Release Agent's commit, promote, and deploy capabilities are only available for Source Format Pipelines.** For Metadata Pipelines, surface a clear error.

**Always use `--json` flag when parsing output programmatically.** Never try to parse human-readable output.

# Output Parsing Guide

All `copado-hx` commands support `--json` for structured output. Always use `--json` when parsing output programmatically.

| Field | Meaning | Agent Action |
|---|---|---|
| `status: "Completed Successfully"` | Action succeeded | Proceed to next step |
| `status: "Completed with Errors"` | Partial failure | Stop, surface errors to human |
| `status: "In Progress"` | Still running | Poll again in 10 seconds |
| `status: "Failed"` | Hard failure | Stop, invoke Release Agent for analysis |
| `testResult: "Succeeded"` | All tests passed | Safe to proceed |
| `testResult: "Failed"` | Tests failed | Stop, surface failures, do not deploy |
| `salesforce_authenticated: true` | CI/CD API ready | Can execute CI/CD operations |
| `crt_configured: true` | CRT API ready | Can execute test operations |
| `ai_configured: true` | AI API ready | Can invoke specialist agents |
| `error` key present | Command failed | Surface error message to human |

## Exit Codes
- `0` = Success
- `1` = General error
- `2` = Authentication error

# Agent Persona Routing

When the developer's request maps to a DevOps lifecycle stage, route to the appropriate Copado AI agent using `copado-hx ai ask --agent <id>`:

| Developer Says | Route to Agent |
|---|---|
| "Write a user story", "plan this feature", "check for conflicts", "refine story", "sprint planning" | `plan` |
| "Write the code", "generate Apex", "review my class", "fix this bug", "analyze metadata", "improve coverage" | `build` |
| "Write a test", "generate test script", "improve coverage", "review test approach", "QWord script" | `test` |
| "Deploy this", "promote to UAT", "why did it fail?", "release notes", "deployment status", "check blocking issues" | `release` |
| "Write docs", "create training material", "change management plan", "troubleshooting guide", "post-release tasks" | `operate` |
| "Ship my story", "end to end", "full delivery" | Follow **Full Story Delivery** playbook |

# MCP Server

`copado-hx` includes an optional MCP server that exposes all commands as discoverable tools for any MCP-compatible agent (Cursor, Claude Desktop, etc.).

Start with: `copado-hx mcp`

The MCP server provides all the same tools and capabilities described in this SKILL.md, natively discovered through the Model Context Protocol.
