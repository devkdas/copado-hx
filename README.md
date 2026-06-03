# copado-hx — Copado Headless Developer CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![CI](https://github.com/devkdas/copado-hx/workflows/CI/badge.svg)](https://github.com/devkdas/copado-hx/actions)

<p align="center">
  <img src="demo/demo.gif" alt="copado-hx demo" width="790">
</p>

**copado-hx** is a unified, open-source CLI that wraps the full Copado API surface — CI/CD via Copado Actions API (RunJobTemplate), Salesforce REST API, Robotic Testing (CRT), and AI Context Hub — into a single, ergonomic developer tool.

No browser tab required. Built for **CopadoCON Bangalore 2026 Hackathon — Track B (Agentic Orchestrator)**

---

## Table of Contents

- [The Problem](#the-problem)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Live Demo Workflow](#live-demo-workflow)
- [Command Reference](#command-reference)
- [Tech Stack](#tech-stack)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [API Coverage](#api-coverage)
- [Security](#security)
- [Architecture](#architecture)
- [Track B Compliance](#track-b-compliance)

---

## Features

- **Authenticate** with Salesforce via `sf org login web` OAuth flow, or use API tokens for AI/CRT
- **Manage user stories** — list, show, set context, create via Salesforce REST API
- **CI/CD pipeline ops** — commit, promote, deploy via Actions API (RunJobTemplate), 7 workflows listed via AI Platform API
- **Robotic testing** — list job suites, trigger builds, poll status, retrieve results (JSON/PDF)
- **AI specialist agents** — invoke Plan, Build, Test, Release, Operate agents from the terminal (with `--stream` for real-time SSE token streaming)
- **Agent-ready SKILL.md** — MCP-compatible agent instruction file for any AI coding assistant
- **MCP Server** — expose all 28 tools as discoverable via the Model Context Protocol:
  ```
  ╭────┬─────────────────────────┬───────────────────────────────────────────────╮
  │ #  │ Tool                    │ Description                                   │
  ├────┼─────────────────────────┼───────────────────────────────────────────────┤
  │ 1  │ version_mcp             │ Return version information for copado-hx      │
  │ 2  │ config_get_mcp          │ Get a configuration value by key              │
  │ 3  │ auth_status             │ Check authentication status                   │
  │ 4  │ auth_status_mcp         │ Agent readiness report + story context        │
  │ 5  │ auth_logout_mcp         │ Clear stored credentials                      │
  │ 6  │ story_list              │ List user stories                             │
  │ 7  │ story_show              │ Get details about a user story                │
  │ 8  │ story_set_context       │ Set working story context                     │
  │ 9  │ story_create_mcp        │ Create a user story                           │
  │ 10 │ commit                  │ Commit metadata changes                       │
  │ 11 │ promote                 │ Promote with PROD gate + self-heal            │
  │ 12 │ deploy_to_prod          │ Deploy to PROD with gate + self-heal          │
  │ 13 │ deliver_story           │ End-to-end: commit → promote → deploy → test  │
  │ 14 │ approve_action          │ Complete one-time approval code for gated     │
  │ 15 │ check_pending_approvals │ Check pending actions awaiting human approval │
  │ 16 │ self_heal               │ Diagnose pipeline failure via Operate agent   │
  │ 17 │ workflow_list           │ List CI/CD workflows                          │
  │ 18 │ workflow_run            │ Trigger a CI/CD workflow                      │
  │ 19 │ list_test_jobs          │ List CRT test job suites                      │
  │ 20 │ run_test                │ Trigger CRT test (with self-heal)             │
  │ 21 │ test_status             │ Check CRT test status                         │
  │ 22 │ test_results            │ Retrieve CRT test results                     │
  │ 23 │ ai_ask_agent            │ Ask 5 AI specialist agents                    │
  │ 24 │ ai_triage               │ Auto-analyze test failures via AI             │
  │ 25 │ deployment_confidence   │ Deployment confidence score from test results │
  │ 26 │ list_environments       │ List pipeline environments                    │
  │ 27 │ list_pipelines          │ List available pipelines                      │
  │ 28 │ check_pipeline_status   │ Check workflow run status                     │
  ╰────┴─────────────────────────┴───────────────────────────────────────────────╯
  ```
- **Human-in-loop approval gates** — one-time approval codes for PROD deployments, `copado-hx approve <code>`
- **Self-healing pipeline** — auto-diagnose failures via Operate AI agent, `--self-heal` flag on promote/deploy/test-run
- **Output flexibility** — human-readable by default, `--json` for machine parsing
- **Secure credential storage** — permission-restricted local file (`chmod 600`), no plaintext tokens in source

---

## The Problem

Salesforce DevOps teams juggle multiple tools: a browser for Copado CI/CD, a terminal for Salesforce CLI, a test runner for CRT, and AI agents scattered across tabs. Context switching kills velocity. **copado-hx** eliminates every browser tab by wrapping all 4 Copado API surfaces into a single terminal CLI — backed by an MCP server for AI agent discovery and a SKILL.md for autonomous orchestration.

---

## Installation

### Prerequisites

- Python 3.10+
- Salesforce org with Copado CI/CD installed
- Copado AI API Key and CRT PAK (from Copado administration)

### Install from source

```bash
git clone https://github.com/devkdas/copado-hx.git
cd copado-hx
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Quick Start

### 1. Authenticate

```bash
copado-hx auth login
```

This opens a browser for Salesforce OAuth (via `sf org login web`), then prompts for AI API Key and CRT PAK. All credentials are stored securely in `~/.copado-hx-secrets.json`.

### 2. Set up configuration

```bash
# Create .copado-hx.json in your project root
copado-hx config --init

# Or set via environment variables
export COPADO_AI_API_KEY="your-ai-api-key"
export COPADO_CRT_PAK="your-crt-pak"
export COPADO_ACTIONS_API_KEY="your-actions-api-key"
```

### 3. View your user stories

```bash
copado-hx story list
```

### 4. Set working context

```bash
copado-hx story set --id US-1234
```

### 5. Ask an AI agent for guidance

```bash
copado-hx ai ask --agent build "What metadata should I commit for US-1234?"
```

### 6. Commit changes

```bash
copado-hx commit --message "feat: add lead scoring"
```

### 7. Promote and test

```bash
copado-hx promote --env UAT-SFP --validate
copado-hx test run --job 120561
copado-hx test status --execution <id> --watch
copado-hx test results --execution <id> --format json
```

### 8. Deploy to production

```bash
copado-hx deploy --env PROD
# Interactive confirmation required for production deployments
```

### 9. Generate release notes

```bash
copado-hx ai ask --agent release "Generate release notes for US-1234"
```

---

## Live Demo Workflow

This 12-step demo walks through the full lifecycle — auth to deploy — using live Copado APIs:

```
 1. copado-hx --help                    # Full command reference
 2. copado-hx auth status               # 4/4 services green
 3. copado-hx story list                # Find user story
 4. copado-hx story show US-0000024     # Inspect story details
 5. copado-hx workflow list             # 7 available workflows
 6. copado-hx story set US-0000024      # Set working context
 7. copado-hx commit -m "feat: lead scoring"  # Actions API commit
 8. copado-hx promote --env UAT-SFP --validate # Validation deployment
 9. copado-hx test list                 # Available CRT jobs
10. copado-hx test run --job 120561     # Trigger CRT build
11. copado-hx env list                  # 7 pipeline environments
12. copado-hx deploy --env PROD         # Production safety gate
```

Every command hits real Copado APIs. If credentials are missing or APIs are unreachable, copado-hx automatically falls back to realistic mock data — so the demo never breaks.

---

## Command Reference

### Authentication

| Command | Description |
|---|---|
| `copado-hx auth login` | Interactive OAuth wizard (SF URL, client ID/secret, pipeline ID) |
| `copado-hx auth login --token <token>` | Token-based auth for CI |
| `copado-hx auth login --crt-pak <pak>` | CRT PAK for CI |
| `copado-hx auth status` | Show auth status with masked tokens |
| `copado-hx auth logout` | Clear Salesforce session |
| `copado-hx auth logout --type all` | Clear all stored credentials |
| `copado-hx auth logout --type ai` | Clear only AI API key |

### User Stories

| Command | Description |
|---|---|
| `copado-hx story list` | List user stories |
| `copado-hx story list --pipeline <id> --status "In Progress"` | Filtered list |
| `copado-hx story set --id US-1234` | Set working context (like git checkout) |
| `copado-hx story show` | Show current story details |
| `copado-hx story create --title "Add feature" --pipeline <id>` | Create new story |

### CI/CD Operations

| Command | Description |
|---|---|
| `copado-hx commit --message "feat: ..."` | Commit changes |
| `copado-hx commit --message "feat: ..." --self-heal` | Commit + auto-diagnose on failure |
| `copado-hx validate` | Validation-only deployment |
| `copado-hx promote --env UAT-SFP --validate` | Promote with validation |
| `copado-hx promote --env UAT-SFP --watch` | Promote + live poll until done |
| `copado-hx promote --env PROD` | Gated — generates approval code first |
| `copado-hx approve <CODE>` | Complete a gated deployment approval |
| `copado-hx list-pending` | Show pending approval requests |
| `copado-hx deploy --env PROD --force` | Deploy (skip gate with --force) |
| `copado-hx deploy --env PROD --watch` | Deploy + live poll |
| `copado-hx deploy --self-heal` | Deploy + auto-diagnose on failure |
| `copado-hx status --job <id> --watch` | Watch job execution |

### Test Execution (CRT)

| Command | Description |
|---|---|
| `copado-hx test list` | List test suites/jobs |
| `copado-hx test run --job <id>` | Trigger test execution |
| `copado-hx test run --job <id> --self-heal` | Trigger + auto-diagnose on failure |
| `copado-hx test status --execution <id> --watch` | Poll for completion |
| `copado-hx test status --execution <id> --watch --self-heal` | Poll + auto-diagnose on failure |
| `copado-hx test results --execution <id> --format json` | Get results |
| `copado-hx test results --execution <id> --format pdf` | Download PDF report |

### AI Specialist Agents

| Command | Description |
|---|---|
| `copado-hx ai ask --agent plan "Refine story US-1234"` | Plan Agent | Add `--stream` for token-by-token |
| `copado-hx ai ask --agent build "Generate Apex for lead scoring"` | Build Agent | Add `--stream` for token-by-token |
| `copado-hx ai ask --agent test "Generate QWord test script"` | Test Agent | Add `--stream` for token-by-token |
| `copado-hx ai ask --agent release "Analyze deployment status"` | Release Agent | Add `--stream` for token-by-token |
| `copado-hx ai ask --agent operate "Create change management plan"` | Operate Agent | Add `--stream` for token-by-token |
| `copado-hx ai chat --agent build` | Interactive REPL |

### MCP Server

```bash
# List all available tools (terminal mode):
copado-hx mcp --list-tools

# Start the MCP server for Cursor/Claude Desktop (piped stdin):
copado-hx mcp
```

The bare `copado-hx mcp` starts a server over stdio for MCP-compatible agents. Use `--list-tools` to browse all 28 tools from a terminal.

### MCP Client Integration

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

**Cursor** — In Cursor settings → Features → MCP Servers → Add new MCP server:
```json
{
  "name": "copado-hx",
  "type": "command",
  "command": "copado-hx",
  "args": ["mcp"]
}
```

### All commands support `--json` flag for machine-readable output.

---

## Configuration

copado-hx reads configuration from:
1. `.env` file (optional, requires `pip install copado-hx[dotenv]`)
2. Environment variables
3. `.copado-hx.json` in the current directory
4. `~/.copado-hx.json` in your home directory

### Environment Variables

| Variable | Description |
|---|---|
| `COPADO_AI_API_KEY` | Copado AI API key |
| `COPADO_AI_BASE_URL` | AI API base URL |
| `COPADO_AI_ORG_ID` | AI organization ID |
| `COPADO_AI_WORKSPACE_ID` | AI workspace ID |
| `COPADO_CRT_PAK` | CRT Personal Access Key |
| `COPADO_CRT_BASE_URL` | CRT API base URL |
| `COPADO_CRT_ORG_ID` | CRT organization ID |
| `COPADO_CRT_PROJECT_ID` | CRT project ID |
| `COPADO_CRT_JOB_ID` | Default CRT job ID |
| `COPADO_CICD_INSTANCE` | Salesforce instance URL |
| `COPADO_ACTIONS_API_KEY` | Copado Actions API webhookKey |
| `COPADO_ACTIONS_BASE_URL` | Actions API base URL (default: https://app-api.copado.com) |
| `COPADO_PIPELINE_ID` | Default pipeline ID |
| `COPADO_DEFAULT_ENV` | Default target environment |
| `COPADO_SF_CLIENT_ID` | Salesforce Connected App client ID |
| `COPADO_SF_CLIENT_SECRET` | Salesforce Connected App client secret |
| `COPADO_SF_REDIRECT_URI` | OAuth redirect URI (default: sfdx://success) |
| `COPADO_SF_USERNAME` | Salesforce username (for password grant in CI) |
| `COPADO_SF_PASSWORD` | Salesforce password (for password grant in CI) |

### Config File

```json
{
  "cicd_instance": "your-instance.lightning.force.com",
  "ai_base_url": "https://copadogpt-api.robotic.copado.com",
  "ai_api_key": "your-ai-key",
  "ai_org_id": "49128",
  "ai_workspace_id": "your-workspace-id",
  "crt_base_url": "https://eu-robotic.copado.com",
  "crt_pak": "your-crt-pak",
  "crt_org_id": "43844",
  "crt_project_id": "76303",
  "crt_job_id": "120561",
  "actions_api_key": "your-actions-api-key",
  "actions_base_url": "https://app-api.copado.com",
  "default_env": "UAT-SFP",
  "output_format": "human"
}
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `Error: No user story context set` | Story not selected | `copado-hx story set --id <id>` or `copado-hx pick` |
| `Error: URL_NOT_RESET` when listing stories | Expired Salesforce session | Re-run `copado-hx auth login` |
| `Error: 500` with "expired" hint | Expired or invalid AI API key | Regenerate key in Copado admin, run `copado-hx auth login --token <key>` |
| Commands return mock data unexpectedly | `COPADO_MOCK_MODE=true` set or credentials missing | Check env vars, run `copado-hx auth status` |
| `copado-hx mcp` not found | MCP dependencies not installed | `pip install mcp` |
| `ImportError: no module named copado_hx` | Package not installed | `pip install -e .` from repo root |
| CRT test returns no jobs | CRT PAK expired or wrong project ID | Check PAK in Copado admin, verify `crt_project_id` in config |
| `copado-hx deploy --env PROD` cancelled | Safety gate requires confirmation | Re-run with `--force` flag or confirm interactively |

---

## API Coverage

### Copado CI/CD — via Actions API (RunJobTemplate) + AI Platform Workflows

| Endpoint | copado-hx command |
|---|---|
| `POST /json/v1/webhook/mcwebhook/RunJobTemplate (sfdx_commit_1)` | `copado-hx commit` |
| `POST /json/v1/webhook/mcwebhook/RunJobTemplate (sfdx_promote_1)` | `copado-hx promote` |
| `POST /json/v1/webhook/mcwebhook/RunJobTemplate (sfdx_deploy_1)` | `copado-hx deploy` |
| `GET /organizations/{id}/workflows` | `copado-hx workflow list` |
| `POST /organizations/{id}/workflows/runs` | `copado-hx workflow run` |
| `GET /services/data/{v}/query (copado__JobExecution__c)` | `copado-hx status --job` |
| `GET /services/data/{v}/query (copado__User_Story__c)` | `copado-hx story list` |
| `POST /services/data/{v}/sobjects/copado__User_Story__c` | `copado-hx story create` |

### Copado Robotic Testing (CRT) Open API

| Endpoint | copado-hx command |
|---|---|
| `POST /pace/v4/projects/{id}/jobs/{id}/builds` | `copado-hx test run` |
| `GET /pace/v4/projects/{id}/jobs/{id}/builds/{id}` | `copado-hx test status` |
| `GET /pace/v4/projects/{id}/jobs/{id}/builds/{id}/results` | `copado-hx test results` |
| `GET /pace/v4/projects/{id}/jobs` | `copado-hx test list` |

### Copado AI Context Hub (Chat Completions API)

| Endpoint | copado-hx command |
|---|---|
| `POST /organizations/{id}/workspaces/{ws}/expert/{agent}/v1/chat/completions` | `copado-hx ai ask` |
| `POST /organizations/{id}/workspaces/{ws}/expert/{agent}/v1/chat/completions` | `copado-hx ai chat` |

---

## Security

- **No credentials hardcoded** in source code — all secrets loaded from environment variables or config file at runtime.
- **Salesforce auth** uses OAuth web flow via `sf org login web` — no passwords stored on disk.
- **Secrets stored with restricted permissions** in `~/.copado-hx-secrets.json` (`chmod 600`).
- **Environment variables** are the preferred method for CI/CD environments.
- **Credentials never logged** to output or error messages.
- **Production deployments** require explicit human confirmation.
- **SOQL queries** use f-string interpolation against trusted org IDs — input is validated via Salesforce ID format checks.

---

## Development

```bash
# Setup
git clone https://github.com/devkdas/copado-hx.git
cd copado-hx
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Install MCP dependencies (optional)
pip install mcp

# Run tests
pytest tests/
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| CLI Framework | Typer |
| HTTP Client | httpx |
| Terminal UI | Rich |
| Config Model | Pydantic |
| MCP Server | FastMCP (mcp) |
| Secret Storage | File (chmod 600) / keyring |
| Test Framework | pytest + pyflakes |
| CI/CD | GitHub Actions (3.11, 3.12, 3.13) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER / AI AGENT                              │
│  (Terminal, Cursor, Claude Desktop, VS Code, MCP-compatible agent)  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                    copado-hx commands
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                         copado-hx CLI                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐   │
│  │  Auth    │  │  Story   │  │  CI/CD   │  │   CRT    │  │  AI  │   │
│  │  login   │  │  list    │  │  commit  │  │  test    │  │ ask  │   │
│  │  status  │  │  set     │  │  promote │  │  run     │  │ chat │   │
│  │  logout  │  │  show    │  │  deploy  │  │  status  │  │      │   │
│  │          │  │  create  │  │  validate│  │  results │  │      │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬───┘   │
│       │             │             │             │           │       │
│  ┌────┴────┐   ┌────┴────┐   ┌────┴─────┐  ┌────┴────┐  ┌───┴────┐  │
│  │  Auth   │   │   SF    │   │  Action  │  │   CRT   │  │   AI   │  │
│  │ Clients │   │  REST   │   │   API    │  │   EU    │  │Context │  │
│  └─────────┘   └─────────┘   │RunJobTmpl│  │   API   │  │  Hub   │  │
│                              └──────────┘  └─────────┘  └────────┘  │
│                                                                     │
│  MCP Server (stdio): 28 tools auto-discovered by any MCP agent      │
│  SKILL.md: Agent instruction file with 6 playbooks, 9 guardrails    │
└─────────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼──────────────┬──────────────┐
              ▼             ▼              ▼              ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ Salesforce │ │  Copado    │ │  Copado    │ │  Copado    │
     │   OAuth    │ │ REST API   │ │ AI Platform│ │ CRT (EU)   │
     │ Web Flow   │ │ v61.0      │ │ Workflows  │ │ PACE API   │
     └────────────┘ └────────────┘ └────────────┘ └────────────┘
```

---

## Track B Compliance

This project implements **Track B — The Agentic Orchestrator** from the Copado Headless Hackathon:

- **copado-hx CLI** (Track A foundation): 20 commands covering auth, stories, CI/CD (Actions API), workflow management, CRT testing, AI agents, config, guided workflows, and MCP server
- **SKILL.md** (required): Complete agent instruction file with all 7 required sections — Identity, Prerequisites, Commands Reference, Workflow Playbooks (6 playbooks), Guardrails (9 rules), Output Parsing Guide, and Agent Persona Routing
- **MCP Server** (Bonus): 28 tools exposed via FastMCP, auto-discoverable by any MCP-compatible agent (Cursor, Claude Desktop, VS Code)
- **Agentforce Action** (Bonus): Apex `@InvocableMethod` class exposing 5 Copado actions as Agentforce Agent Actions — `agentforce/` directory
- **4 Copado API surfaces integrated**: CI/CD via Actions API (RunJobTemplate) for commit/promote/deploy, SF REST API for story management and job status, Robotic Testing (CRT), AI Context Hub with all 5 specialist agents (Plan, Build, Test, Release, Operate)
- **Secure auth**: OAuth web flow via `sf org login web`, no passwords stored on disk, secrets stored with restricted permissions in `~/.copado-hx-secrets.json`

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Built for CopadoCON Bangalore 2026

**Copado Headless Hackathon** — *"The Future of Salesforce DevOps Has No Browser Tab"*

No browser. No context switching. Just your terminal and your AI agent.
