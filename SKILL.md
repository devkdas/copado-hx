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
- Never infer or fabricate workflow IDs, environment names, user story IDs, or test job IDs. Always retrieve them from `copado-hx story list`, `copado-hx workflow list`, `copado-hx env list`, or `copado-hx test list`.
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
**Output:** Table or JSON array of user stories with ID, Name, Status, Title.
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
**Syntax:** `copado-hx commit [--us <id>] [--story <id>] [--message <msg>] [--json]`
**Output:** JSON with `{ workflow_run_id, status }`
**Example:** `copado-hx commit --message "feat: add lead scoring"`
**Do not use if:** No user story context is set. Run `copado-hx story set` first.
**Behind the scenes:** Triggers via the Actions API (RunJobTemplate sfdx_commit_1).

## `copado-hx promote`
**Purpose:** Triggers a CI/CD workflow that promotes a user story to the next environment.
**Syntax:** `copado-hx promote [--us <id>] [--story <id>] [--env <name>] [--validate] [--watch] [--self-heal] [--json]`
**Parameters:**
- `--validate` : Run a validation-only promotion (no actual deploy)
- `--watch` : Poll job status until completion
- `--self-heal` : Auto-diagnose failures via Operate agent
**Guardrail:** PROD/PRODUCTION environments require human approval. The command generates a one-time code. Run `copado-hx approve <CODE>` to complete the gate.
**Example:** `copado-hx promote --env UAT-SFP --validate`
**Example:** `copado-hx promote --env PROD` (generates approval code)
**Behind the scenes:** Triggers via the Actions API (RunJobTemplate sfdx_promote_1).

## `copado-hx deploy`
**Purpose:** Triggers a workflow that deploys a user story to a target environment.
**Syntax:** `copado-hx deploy [--us <id>] [--story <id>] [--env <name>] [--force] [--watch] [--self-heal] [--json]`
**Guardrail:** PROD environments generate a one-time approval code. Use `copado-hx approve <CODE>` to authorize, or `--force` to skip the gate.
**Parameters:**
- `--self-heal` : Auto-diagnose deployment failures via Operate agent
**Example:** `copado-hx deploy --env PROD` (generates approval code)
**Example:** `copado-hx deploy --env PROD --self-heal` (auto-diagnose on failure)

## `copado-hx validate`
**Purpose:** Run a validation-only deployment.
**Syntax:** `copado-hx validate [--us <id>] [--story <id>] [--env <name>] [--json]`

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

## `copado-hx env list`
**Purpose:** List available pipeline environments (alias: `copado-hx environments` — deprecated, use `copado-hx env list` instead).
**Syntax:** `copado-hx env list [--json]`

## `copado-hx test list`
**Purpose:** List available CRT test suites and jobs.
**Syntax:** `copado-hx test list [--json]`
**Output:** Table or JSON array with Job ID, Name, Type.

## `copado-hx test run`
**Purpose:** Trigger a CRT test suite or job.
**Syntax:** `copado-hx test run [--suite <id>] [--job <id>] [--self-heal] [--json]`
**Parameters:**
- `--self-heal` : Auto-diagnose execution failures via Operate agent
**Poll for results:** Use `copado-hx test status --execution <id>` until status is `Succeeded` or `Failed`. Then call `copado-hx test results`.

## `copado-hx test status`
**Purpose:** Poll execution status of a CRT test run.
**Syntax:** `copado-hx test status --execution <id> [--watch] [--self-heal] [--json]`
**Parameters:**
- `--self-heal` : Auto-diagnose failures when status is Failed/Error
**Example:** `copado-hx test status --execution 12345 --watch`

## `copado-hx test results`
**Purpose:** Retrieve CRT test results (JUnit-compatible output).
**Syntax:** `copado-hx test results --execution <id> [--format json|pdf|junit] [--json]`
**Example:** `copado-hx test results --execution 12345 --format json`

## `copado-hx ai ask`

**Syntax:** `copado-hx ai ask --agent <id> "<prompt>" [--us <story_id>] [--json] [--stream]`

**Streaming:** Add `--stream` to see the AI response token-by-token in real time (SSE). When omitted, the full response is returned at once.
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
**Purpose:** Start the MCP server for agent discovery, or list tools from the terminal.
**Syntax:** `copado-hx mcp [--transport stdio]` (server mode), `copado-hx mcp --list-tools` (terminal browse mode)
**When to use:** Use `--list-tools` to browse all 28 tools from a terminal. Use bare `copado-hx mcp` when an MCP-compatible agent (Cursor, Claude Desktop) connects via stdio.
**Key MCP tools for agents:**
- `auth_status_mcp` — Agent readiness report: checks all auth + story context, returns warnings if anything missing. Call FIRST before any workflow.
- `deliver_story` — Composite end-to-end delivery: commit → promote → deploy → (optional tests) in one tool call. For PROD, requires `approval_code` param.
- `promote` — Gated: PROD/PRODUCTION environments return a one-time `approval_code`. Present this code to the developer, then call again with `approval_code='<code>'` after they confirm via `copado-hx approve <code>`.
- `deploy_to_prod` — Gated: requires `approval_code` obtained from a prior promote call or `copado-hx interactive`. Never proceed without showing the code to the developer.
- `approve_action` — Consumes a one-time approval code. Call AFTER the developer confirms the code verbally.
- `check_pending_approvals` — Check if any action awaits human approval before proceeding.
- `self_heal` — Manually diagnose a pipeline failure. Use when promote/deploy/test-run returns an error you can't interpret.

## `copado-hx config`
**Purpose:** Manage copado-hx configuration.
**Syntax:** `copado-hx config [--show] [--init]`
**Example:** `copado-hx config --init`

## `copado-hx guide`
**Purpose:** Display current context (story, auth, last action) with state-aware next-step recommendations.
**When to use:** Before starting work or after any CI/CD action to see what to do next.
**Syntax:** `copado-hx guide`
**Output:** Context panel (story, auth, last action) + suggested next commands.
**Example:** `copado-hx guide`

## `copado-hx interactive`
**Purpose:** Menu-driven guided workflow — shows context + numbered action list, executes selected command, loops.
**When to use:** When you want step-by-step guidance through the CI/CD pipeline.
**Syntax:** `copado-hx interactive [--all]`
**Example:** `copado-hx interactive`

## `copado-hx pick`
**Purpose:** Interactive story picker — fetches stories, shows numbered table, sets context on selection.
**When to use:** Instead of `copado-hx story list` + `copado-hx story set` when you prefer a picker UI.
**Syntax:** `copado-hx pick`
**Example:** `copado-hx pick`

## `copado-hx ship`
**Purpose:** One-shot end-to-end pipeline: commit \u2192 promote \u2192 test \u2192 deploy.
**When to use:** When the developer says "ship this story end-to-end".
**Syntax:** `copado-hx ship --us <story-id> [--to <env>] [--skip-tests]`
**Flags:**
- `--us, --story <id>` (required): User story ID
- `--to, -e <env>` (default: UAT-SFP): Target environment
- `--skip-tests`: Skip CRT test execution step
**Example:** `copado-hx ship --us US-0000024 --to UAT-SFP`

## `copado-hx approve`
**Purpose:** Complete a gated deployment approval using a one-time code.
**When to use:** After `copado-hx promote --env PROD` or `copado-hx deploy --env PROD` generates an approval code. Show the code to the developer, then run `copado-hx approve <CODE>`.
**Syntax:** `copado-hx approve <code>`
**Example:** `copado-hx approve AP-7FD45A35`

## `copado-hx list-pending`
**Purpose:** Show any pending actions awaiting human approval.
**When to use:** Before a deployment workflow to check if an earlier step requires approval.
**Syntax:** `copado-hx list-pending`
**Example:** `copado-hx list-pending` → "Pending: promote to PROD --us US-0000024"

## Agentforce Action (`agentforce/`)
**Purpose:** Expose copado-hx commands as Agentforce Agent Actions.
**Syntax:** `sf project deploy start -d agentforce/ -o <org>`
**Details:** 5 `@InvocableMethod` Apex actions — commit, promote, deploy, getStories, getJobStatus. Deployable to any Agentforce-enabled org. See `agentforce/README.md`.

# Workflow Playbooks

## Playbook: Full Story Delivery (Commit → UAT → Test → PROD)

Use this when the developer says: "ship my user story", "promote to prod", "deploy US-1234 end to end", or similar.

**Steps:**
1. Verify auth: `copado-hx auth status`
2. Set context: `copado-hx story set --id <us-id>`
3. Ask Build Agent for commit guidance: `copado-hx ai ask --agent build "What metadata should I commit for <us-id>?"`
4. Commit: `copado-hx commit --message "<generated message>"`
5. Promote + validate to UAT-SFP: `copado-hx promote --env UAT-SFP --validate`
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
10. Promote to UAT-SFP: `copado-hx promote --env UAT-SFP`
11. Run tests: `copado-hx test run --suite <id>`
12. Ask Release Agent: `copado-hx ai ask --agent release "Is story <id> ready for PROD? Check deployment status and blockers."`
13. **STOP. Ask the human:** deploy approval.
14. `copado-hx deploy --env PROD`
15. Generate release notes: `copado-hx ai ask --agent release "Generate release notes for story <id>"`
16. Ask Operate Agent: `copado-hx ai ask --agent operate "Create training and change management docs for this release"`

## Playbook: Multi-Agent Handoff (Build → Test with Context Passed via --json)

Use this when the developer wants the Build Agent to generate code and the Test Agent to generate tests for the same feature, passing context between them programmatically.

**Steps:**
1. Set context: `copado-hx story set --id <us-id>`
2. Ask Build Agent with `--json` for structured output:
   `copado-hx ai ask --agent build "What Apex classes do I need for lead scoring in story <us-id>?" --json`
3. Extract the agent's response from the JSON output:
   `copado-hx ai ask --agent build "List only the Apex class names for lead scoring" --json | jq '.response'`
4. Pass that context to the Test Agent in the next prompt:
   `copado-hx ai ask --agent test "Generate CRT QWord test scripts for the classes identified by the Build Agent: LeadScoringService, LeadScoringTriggerHandler, LeadScoringBatchJob"`
5. Test Agent receives the Build Agent's output as context and generates targeted tests.
6. Present the generated test scripts to the developer for review.
7. **STOP. Ask the human:** "Shall I trigger these tests?"
8. On approval: `copado-hx test run --suite <id>`
9. `copado-hx test results --execution <id>`

**How context flows:**
- Build Agent output → extracted via `--json` → injected into Test Agent prompt
- Story ID (`--us`) provides shared scope context
- Developer acts as the approval gate between agent handoffs

# Guardrails — What Agents Must Never Do

## PRODUCTION SAFETY (CRITICAL)

**Never deploy to a PROD or production environment without explicit human confirmation.** Always pause and ask verbatim: "I'm about to deploy to PROD. Please confirm yes/no." Wait for a yes/no answer. Do not proceed without it.

- For `promote` MCP tool with a gated env: the tool returns `approval_required` with a one-time code. Show the code to the developer. Call `approve_action(code='...')` only after the developer confirms.
- For `deploy_to_prod` MCP tool: requires `approval_code` parameter. Never set it without showing the code to the developer first.
- For `deliver_story` MCP tool with `target_environment=PROD`: requires `approval_code` parameter. The tool rejects without it.
- For CLI `copado-hx promote --env PROD` or `copado-hx deploy --env PROD`: generates a one-time approval code (`AP-XXXX`). Show this code to the developer. Then run `copado-hx approve <CODE>` after they confirm.

**Never use `--yes` or `-y` flags for PROD deployments.** These bypass safety prompts and should never be used for production.

**Never chain commit → promote → deploy without a human checkpoint between each stage.** After each action, present the result and ask "Shall I proceed to the next step?"

## DATA INTEGRITY

**Never fabricate or guess IDs** (user story IDs, pipeline IDs, environment names, suite IDs). Always retrieve them from the CLI first using `copado-hx story list`, `copado-hx env list`, or `copado-hx test list`.

**Never run `copado-hx deploy` immediately after `copado-hx promote`** without checking test results and receiving human approval.

**Never assume API credentials or configuration.** If `copado-hx auth status` shows any service as unauthenticated, stop and inform the human.

**Never infer pipeline or environment relationships.** Use `copado-hx env list` and `copado-hx status` to discover them.

## SECURITY

**Never store or log API tokens** in any output, file, or message. Tokens are stored securely in the OS keychain (keyring) and `~/.copado-hx-secrets.json`.

**Never output raw HTTP responses** — always use the structured `--json` output.

## TEST INTEGRITY

**Always surface test failures to the human** before proceeding to the next pipeline stage. Do not auto-retry failed tests.

**Never deploy with failing tests.** If `test results` shows failures, run `ai triage` and present the analysis to the human.

**The commit, promote, and deploy commands are only available for Source Format Pipelines.** For Metadata Pipelines, surface a clear error.

# Output Parsing Guide

All `copado-hx` commands support `--json` for structured output. Always use `--json` when parsing output programmatically. Never try to parse human-readable output.

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
| `status: "partial"` (deliver_story) | Some steps in composite delivery failed | Inspect each step's `status`, surface failures to human |
| `ready: false` (auth_status_mcp) | Not all services are authenticated | Call `auth_status_mcp` to see `warnings[]`, run `copado-hx auth login` |
| `guardrail` key present | Safety gate triggered (e.g. PROD) | Follow the guardrail instruction, ask human for approval |

## Exit Codes
- `0` = Success
- `1` = Error (includes auth errors)

# Agent Persona Routing

When the developer's request maps to a DevOps lifecycle stage, route to the appropriate Copado AI agent using `copado-hx ai ask --agent <id>`:

| Developer Says | Route to Agent |
|---|---|
| "Write a user story", "plan this feature", "check for conflicts", "refine story", "sprint planning" | `plan` |
| "Write the code", "generate Apex", "review my class", "fix this bug", "analyze metadata", "improve coverage" | `build` |
| "Write a test", "generate test script", "improve coverage", "review test approach", "QWord script" | `test` |
| "Deploy this", "promote to UAT-SFP", "why did it fail?", "release notes", "deployment status", "check blocking issues" | `release` |
| "Write docs", "create training material", "change management plan", "troubleshooting guide", "post-release tasks" | `operate` |
| "Ship my story", "end to end", "full delivery", "deliver this" | Call `deliver_story` MCP tool (or follow **Full Story Delivery** playbook) |
| "Is everything ready?", "check readiness", "status check" | `auth_status_mcp` MCP tool — returns auth + story context + warnings |

# Error Recovery

If any command fails:

1. **Check auth** — Run `copado-hx auth status --json`. Authentication may have expired.
2. **Read the error message** — copado-hx surfaces readable error details, not raw HTTP codes.
3. **401 / session expired** — Run `copado-hx auth login` to re-authenticate. If `sf_username` + `COPADO_SF_PASSWORD` env vars are set, auto-refresh will attempt silently.
4. **403 / access denied** — The API key may be invalid or lack permissions. Regenerate from Copado App Launcher > Connected Apps.
5. **404 / not found** — The resource ID (user story, environment, job) doesn't exist. Run `copado-hx story list`, `copado-hx env list` (or deprecated `copado-hx environments`), or `copado-hx test list` to discover valid IDs.
6. **Deployment/promotion failures** — `copado-hx ai ask --agent release "Analyze this error: <error message>"`
7. **Test failures** — `copado-hx ai triage --execution <id>` for automated root cause analysis.
8. **Timeouts** — Check your network connection. Some operations (AI questions, CRT tests) may take 30-60 seconds.
9. **Token expired / auth lost during agent session** — Run `copado-hx auth status` to diagnose. If expired, use `auth_status_mcp` MCP tool to see which service needs re-authentication. Run `copado-hx auth login` with the appropriate flags (`--type actions`, `--crt-pak`, `--token`).
10. **Never retry a failed deployment automatically** — Always investigate the cause and ask the human before retrying.

## Auto-Recovery Sequence for Agents

When any command fails during an automated workflow:

1. Capture the `status`, `error`, and any `jobExecutionId` from the output.
2. Call `auth_status_mcp` to verify auth hasn't expired (common cause).
3. If auth is fine, check if the error is transient (timeout, rate limit) vs permanent (bad ID, permissions).
 4. For transient errors: retry once after 10 seconds. If it fails again, run `self_heal` MCP tool or `copado-hx deploy --self-heal` for automated diagnosis.
 5. For permanent errors: use `self_heal` MCP tool to get Operate agent diagnosis. Present findings to the developer.
5. For permanent errors: stop immediately. Do not retry. Present the error and suggest a fix.
6. Never proceed to the next pipeline step after any failure without human approval.

# Session State

`copado-hx` tracks session state in `~/.copado-hx-state.json`. This file records the last action, last story ID, last job IDs, and last environment. Agents can use this for context-aware follow-ups after any command.

The state is updated automatically after every command. To read it programmatically:
- `copado-hx status` — shows current context (story, environment)
- `copado-hx auth status --json` — auth state
- The MCP `auth_status_mcp` tool returns a complete readiness report including current story context

# MCP Server

`copado-hx` includes an optional MCP server that exposes all commands as discoverable tools for any MCP-compatible agent (Cursor, Claude Desktop, etc.).

Start with: `copado-hx mcp` (server mode) or `copado-hx mcp --list-tools` to browse all 28 tools from a terminal.

The MCP server provides all the same tools and capabilities described in this SKILL.md, natively discovered through the Model Context Protocol.

### MCP Client Configuration

**Claude Desktop** — Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "copado-hx": {
      "command": "copado-hx",
      "args": ["mcp"]
    }
  }
}
```

**VS Code (Cline / Continue)** — Add to MCP settings:
```json
{
  "command": "copado-hx",
  "args": ["mcp"]
}
```

**Cursor** — Cursor settings → Features → MCP Servers → Add new:
```json
{
  "name": "copado-hx",
  "type": "command",
  "command": "copado-hx",
  "args": ["mcp"]
}
```

## Auth Lifecycle for MCP Agents

Authentication tokens are stored in the OS keychain (`~/.copado-hx-secrets.json`). MCP tools check for valid tokens on each call. If a tool returns an auth error:

1. **Check auth status first** — Call `auth_status_mcp` for a structured readiness report including `warnings[]`.
2. **Re-authenticate** — The MCP server cannot perform interactive browser OAuth. Instruct the human to run:
   - `copado-hx auth login` (full interactive setup)
   - `copado-hx auth login --token <ai-key>` (AI API key only)
   - `copado-hx auth login --crt-pak <pak>` (CRT PAK only)
3. **Verify** — Call `auth_status_mcp` again. When `ready: true`, proceed with workflow.

**Best practice:** Call `auth_status_mcp` at the start of every agent session to verify all prerequisites are met before any pipeline operation.
