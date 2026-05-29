# copado-hx — Copado Headless Developer CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)

**copado-hx** is a unified, open-source CLI that wraps the full Copado API surface — CI/CD via Copado Actions API (RunJobTemplate), Robotic Testing (CRT), and AI Context Hub — into a single, ergonomic developer tool.

No browser tab required. Built for **CopadoCON Bangalore 2026 Hackathon — Track B (Agentic Orchestrator)**

---

## Features

- **Authenticate** with Salesforce via `sf org login web` OAuth flow, or use API tokens for AI/CRT
- **Manage user stories** — list, show, set context, create via Salesforce REST API
- **CI/CD pipeline ops** — commit, promote, deploy via Actions API (RunJobTemplate), 7 workflows listed via AI Platform API
- **Robotic testing** — list job suites, trigger builds, poll status, retrieve results (JSON/PDF)
- **AI specialist agents** — invoke Plan, Build, Test, Release, Operate agents from the terminal
- **Agent-ready SKILL.md** — MCP-compatible agent instruction file for any AI coding assistant
- **MCP Server** — expose all 17 commands as discoverable tools via the Model Context Protocol
- **Output flexibility** — human-readable by default, `--json` for machine parsing
- **Secure credential storage** — encrypted local file with `chmod 600`, no plaintext tokens

---

## Installation

### Prerequisites

- Python 3.11+
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
copado-hx promote --env UAT --validate
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

## Command Reference

### Authentication

| Command | Description |
|---|---|
| `copado-hx auth login` | Interactive OAuth login |
| `copado-hx auth login --token <token>` | Token-based auth for CI |
| `copado-hx auth status` | Show auth status across all services |
| `copado-hx auth logout` | Clear stored credentials |

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
| `copado-hx promote --env UAT --validate` | Promote with validation |
| `copado-hx deploy --env PROD` | Deploy (requires approval) |
| `copado-hx status --job <id> --watch` | Watch job execution |

### Test Execution (CRT)

| Command | Description |
|---|---|
| `copado-hx test list` | List test suites/jobs |
| `copado-hx test run --job <id>` | Trigger test execution |
| `copado-hx test status --execution <id> --watch` | Poll for completion |
| `copado-hx test results --execution <id> --format json` | Get results |
| `copado-hx test results --execution <id> --format pdf` | Download PDF report |

### AI Specialist Agents

| Command | Description |
|---|---|
| `copado-hx ai ask --agent plan "Refine story US-1234"` | Plan Agent |
| `copado-hx ai ask --agent build "Generate Apex for lead scoring"` | Build Agent |
| `copado-hx ai ask --agent test "Generate QWord test script"` | Test Agent |
| `copado-hx ai ask --agent release "Analyze deployment status"` | Release Agent |
| `copado-hx ai ask --agent operate "Create change management plan"` | Operate Agent |
| `copado-hx ai chat --agent build` | Interactive REPL |

### MCP Server

```bash
copado-hx mcp
```

Starts an MCP server exposing all copado-hx tools for any MCP-compatible agent (Cursor, Claude Desktop, etc.).

### All commands support `--json` flag for machine-readable output.

---

## Configuration

copado-hx reads configuration from:
1. Environment variables
2. `.copado-hx.json` in the current directory
3. `~/.copado-hx.json` in your home directory

### Environment Variables

| Variable | Description |
|---|---|
| `COPADO_SF_CLIENT_ID` | Salesforce connected app client ID |
| `COPADO_SF_CLIENT_SECRET` | Salesforce connected app client secret |
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
  "default_env": "UAT",
  "output_format": "human"
}
```

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
| `GET /services/data/{v}/query (User_Story__c)` | `copado-hx story list` |
| `POST /services/data/{v}/sobjects/User_Story__c` | `copado-hx story create` |

### Copado Robotic Testing (CRT) Open API

| Endpoint | copado-hx command |
|---|---|
| `POST /pace/v4/projects/{id}/jobs/{id}/builds` | `copado-hx test run` |
| `GET /pace/v4/projects/{id}/jobs/{id}/builds/{id}` | `copado-hx test status` |
| `GET /pace/v4/projects/{id}/jobs/{id}/builds/{id}/results` | `copado-hx test results` |
| `GET /pace/v4/projects/{id}/jobs` | `copado-hx test list` |

### Copado AI Context Hub (Dialogue API)

| Endpoint | copado-hx command |
|---|---|
| `POST /dialogues` | `copado-hx ai ask` (via `start_dialogue`) |
| `POST /dialogues/{id}/messages` | `copado-hx ai ask` (via `send_message`) |
| `GET /dialogues/{id}` | `copado-hx ai chat` (internal) |
| `GET /organizations/{id}/workspaces` | `copado-hx ai ask` (workspace resolution) |

---

## Security

- **No credentials hardcoded** in source code — all secrets loaded from environment variables or config file at runtime.
- **Salesforce auth** uses OAuth web flow via `sf org login web` — no passwords stored on disk.
- **Secrets stored encrypted** in `~/.copado-hx-secrets.json` with `chmod 600` permissions.
- **Environment variables** are the preferred method for CI/CD environments.
- **Credentials never logged** to output or error messages.
- **Production deployments** require explicit human confirmation.
- **Input validation** prevents injection attacks.

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
│  ┌────┴────┐   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐  ┌───┴────┐  │
│  │  Auth   │   │   SF    │   │  Action │   │   CRT   │  │   AI   │  │
│  │ Clients │   │  REST   │   │   API   │   │   EU    │  │Context │  │
│  └─────────┘   └─────────┘   │RunJobTmpl│  │   API   │  │  Hub   │  │
│                              └─────────┘   └─────────┘  └────────┘  │
│                                                                     │
│  MCP Server (stdio): 17 tools auto-discovered by any MCP agent      │
│  SKILL.md: Agent instruction file with 5 playbooks, 9 guardrails    │
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

- **copado-hx CLI** (Track A foundation): 13 command groups covering auth, stories, CI/CD (Actions API), workflow management, CRT testing, AI agents, config, and MCP server
- **SKILL.md** (required): Complete agent instruction file with all 7 required sections — Identity, Prerequisites, Commands Reference, Workflow Playbooks (5 playbooks), Guardrails (9 rules), Output Parsing Guide, and Agent Persona Routing
- **MCP Server** (Bonus): 17 tools exposed via FastMCP, auto-discoverable by any MCP-compatible agent (Cursor, Claude Desktop, VS Code)
- **3 Copado API surfaces integrated**: CI/CD via Actions API (RunJobTemplate) for commit/promote/deploy, SF REST API for story management and job status, Robotic Testing (CRT), AI Context Hub with all 5 specialist agents (Plan, Build, Test, Release, Operate)
- **Secure auth**: OAuth web flow via `sf org login web`, no passwords stored on disk, secrets encrypted in `~/.copado-hx-secrets.json`

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Built for CopadoCON Bangalore 2026

**Copado Headless Hackathon** — *"The Future of Salesforce DevOps Has No Browser Tab"*

No browser. No context switching. Just your terminal and your AI agent.
