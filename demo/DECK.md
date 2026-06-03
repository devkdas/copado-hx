# copado-hx: Headless Salesforce DevOps
## CopadoCON Bangalore 2026 — Track B: Agentic Orchestrator
#### Team: Headless Nomads

---

## Slide 1: The Problem

### Salesforce DevOps Today
- **Context switching**: Browser tabs for CI/CD, AI, testing, Git
- **No agent automation**: Every pipeline step = human clicking through UIs
- **Fragmented APIs**: CI/CD in Salesforce org, CRT in robotic testing, AI in separate platform
- **Result**: Slow releases, human error, cognitive overload

### One CLI. One Agent. Zero Tabs.

---

## Slide 2: copado-hx Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    copado-hx CLI                         │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌───────────┐   │
│  │Auth  │  │Story │  │CI/CD │  │CRT   │  │AI Agents  │   │
│  │      │  │Mgmt  │  │Action│  │Tests │  │P/B/T/R/O  │   │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └─────┬─────┘   │
│     │         │         │         │            │         │
└─────┼─────────┼─────────┼─────────┼────────────┼─────────┘
      │         │         │         │            │
  ┌───┴──┐  ┌───┴──┐ ┌────┴────┐ ┌──┴───┐ ┌──────┴──────┐
  │  sf  │  │Sales │ │Copado   │ │CRT EU│ │Copado AI    │
  │login │  │force │ │Actions  │ │REST  │ │Context Hub  │
  │OAuth │  │REST  │ │API      │ │API   │ │5 Specialist │
  │      │  │API   │ │RunJob   │ │      │ │Agents       │
  └──────┘  └──────┘ │Template │ └──────┘ └─────────────┘
                     └─────────┘
```

**4 API surfaces, 1 unified CLI — Actions API (CI/CD), SF REST, CRT, AI Context Hub.**

---

## Slide 3: Auth & Setup

### One Command to Rule Them All
```bash
copado-hx auth login
```

### What happens:
1. Browser opens → Salesforce OAuth (`sf org login web`)
2. AI API Key prompt → Copado AI Platform access
3. CRT PAK prompt → Copado Robotic Testing access

### No passwords stored on disk
- Access tokens in `~/.copado-hx-secrets.json` (chmod 600)
- Salesforce credentials never leave the OAuth flow
- Env vars for CI: `COPADO_AI_API_KEY`, `COPADO_CRT_PAK`, `COPADO_ACTIONS_API_KEY`

### Auth Status
```bash
copado-hx auth status --json
# → { salesforce: ok, ai: ok, crt: ok, actions: ok }
```

---

## Slide 4: CI/CD Pipeline (Copado Actions API)

### 3 Job Templates
| Template | Purpose |
|---|---|
| **sfdx_commit_1** | SFDX Commit — trigger build |
| **sfdx_deploy_1** | SFDX Deploy — deploy to environment |
| **sfdx_promote_1** | SFDX Promote — promote across environments |

### CLI Commands
```bash
copado-hx workflow list                    # List AI Platform workflows
copado-hx commit -m "feat: x"      --story <id>  # Actions API commit
copado-hx promote --env UAT-SFP --validate --story <id>  # Actions API promote
copado-hx deploy --env PROD         --story <id>  # Human approval gate
copado-hx status --job <id> --watch               # Live job monitoring
```

### Auth: Actions API `webhookKey` from Copado Account Summary

---

## Slide 5: AI Specialist Agents (Context Hub)

### 5 Purpose-Built Agents
```
┌────────────────┐
│  Orchestrator  │ ← You are here (agent or human)
│     Agent      │
└───────┬────────┘
        │ delegates to
        ▼
┌──────┬──────┬──────┬──────┬────────┐
│ Plan │ Build│ Test │Release│Operate│
│Agent │Agent │Agent │Agent  │Agent  │
│      │      │      │       │       │
│Story │Code  │QWord │Deploy │Change │
│Refine│Gen   │Script│Coord. │Mgmt.  │
│Conf. │Review│Cover │Release│Train. │
│Detect│Apex  │age   │Notes  │Docs   │
└──────┴──────┴──────┴───────┴───────┘
```

```bash
copado-hx ai ask --agent build "Write Apex for lead scoring"
copado-hx ai ask --agent release "Generate release notes"
copado-hx ai chat --agent plan   # Interactive REPL
```

---

## Slide 6: Robotic Testing (CRT — Agentia Testing)

### Full Test Lifecycle from Terminal
```bash
# Discover
copado-hx test list

# Execute
copado-hx test run --job 120561
# → Returns Execution ID: 5249902

# Monitor
copado-hx test status --execution <id> --watch
# → Live polling terminal dashboard

# Results
copado-hx test results --execution <id> --format json
copado-hx test results --execution <id> --format pdf
# → Downloadable PDF test report
```

### Technical Details
- **Endpoint:** `eu-robotic.copado.com`
- **Auth:** `X-Authorization` with PAK
- **Format:** JUnit-compatible JSON output
- **Build trigger → poll → results** pattern

---

## Slide 7: MCP Server (Bonus)

### Expose All 28 tools as MCP Tools
```bash
copado-hx mcp --list-tools
# → Table of all 28 tools: story_list, commit, promote, deploy_to_prod, deliver_story, ...
```

### Available Tools (28 tools — sample shown)
| Tool | Description |
|---|---|
| `story_list` | Query user stories |
| `commit` | Trigger CI/CD commit via Actions API |
| `promote` | Promote to environment via Actions API |
| `deploy_to_prod` | Production deploy with gate |
| `ai_ask_agent` | Query any specialist agent |
| `run_test / test_status / test_results` | Full CRT lifecycle |
| `workflow_list / workflow_run` | Custom workflow trigger |
| `list_environments / list_pipelines` | Org exploration |
| `story_show`, `story_set_context`, `check_pipeline_status`, `auth_status`, `list_test_jobs`, `list_environments`, `list_pipelines` | +7 more |

**Any MCP-compatible agent** (Claude Desktop, Cursor, VS Code) can discover and invoke all 28 tools natively.

---

## Slide 8: Demo & Results

### Live Demo Flow (5 min)
```
 1. copado-hx --help                    → Full command reference
 2. copado-hx auth status               → All 4 services green
 3. copado-hx story list                → Find user story
 4. copado-hx story show                → Inspect story
 5. copado-hx workflow list             → 7 available workflows
 6. copado-hx story set                 → Set working context
 7. copado-hx commit -m "feat: x"       → Actions API Job Execution
 8. copado-hx promote --env UAT-SFP --validate → Actions API validation
 9. copado-hx test list                 → CRT jobs
10. copado-hx test run --job 120561     → CRT build triggered
 11. copado-hx env list                  → 7 pipeline environments
12. copado-hx deploy --env PROD         → Human approval gate demo
 13. copado-hx ai ask --agent build      → AI generates Apex code
 14. copado-hx ai ask --agent test       → Multi-agent handoff (Build→Test)
 15. copado-hx status --json             → Machine-readable output
   16. copado-hx mcp --list-tools           → MCP server with 28 tools listed
```

### Deliverables
| Item | Status |
|---|---|
| **copado-hx CLI** | Yes — 20 commands, 46 unit tests |
| **SKILL.md** | Yes — Complete agent instruction file |
| **MCP Server** | Yes — 28 tools |
| **Agentforce Action** | Yes — 5 `@InvocableMethod` Apex actions in `agentforce/` |
| **All APIs verified** | Yes — AI, CRT, Actions API (CI/CD), SF REST |
| **Secure auth** | Yes — OAuth web flow, no passwords on disk |

### Links
- **Source:** `github.com/devkdas/copado-hx`
- **License:** MIT

**Built for CopadoCON Bangalore 2026 — No Browser. No Context Switching. Just Your Terminal and AI.**
