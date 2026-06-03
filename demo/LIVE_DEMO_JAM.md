# Live Demo Jam — CopadoCON Bangalore 2026

## Track B: Agentic Orchestrator — copado-hx

**Date:** 13 June 2026
**Duration:** 5 minutes max (target: 4:30)
**Team:** Headless Nomads — Ravalika Bommera (lead), Kartheek Dasari

---

## Pre-Demo Setup (Do Before Stage Time)

```bash
# 1. Refresh Salesforce token
sf org login web -a copado-hx -r https://copadotrial6013563.my.salesforce.com

# 2. Persist to secrets file
source .venv/bin/activate && copado-hx auth login

# 3. Verify all 4 APIs green
copado-hx auth status

# 4. Verify key commands work
copado-hx story list
copado-hx test list
copado-hx env list
copado-hx workflow list

# 5. Quick commit+promote test
copado-hx story set a1vhk0000000P01AAE
copado-hx commit -m "test: pre-demo verify"
copado-hx promote --env UAT-SFP --validate

# 6. Backup: open asciinema recording ready
#    asciinema play demo/demo-recording.cast --speed 2
```

### Physical Checklist
- [ ] Laptop fully charged + charger nearby
- [ ] Terminal: dark theme, large font (20pt+), full screen
- [ ] No notifications (Do Not Disturb ON)
- [ ] Presenter mode / external display tested
- [ ] `source .venv/bin/activate` pre-run in terminal
- [ ] `~/.copado-hx-secrets.json` confirmed present
- [ ] Internet connection confirmed
- [ ] PPTX deck open on second screen / backup
- [ ] Water on stage

---

## Demo Script (5 min, ~20s per command)

### Pre-roll (30s) — Stage Presence

**Say:** *"Hello everyone, we're team Headless Nomads. Today we'll show you how to do full Salesforce DevOps — CI/CD, testing, AI agents — all from the terminal. Zero browser tabs, zero context switching."*

*Hit Enter to clear screen, then type first command slowly and deliberately.*

---

### 1. copado-hx --help (20s)

```bash
copado-hx --help
```

**Say:** *"copado-hx is a unified CLI with 20 commands. Auth, stories, commit, promote, deploy, test, AI, config, MCP server, guided workflows — every Copado surface from one tool."*

**Pointer:** Wave cursor over the command groups, especially commit/promote/deploy (Actions API), test (CRT), ai (Context Hub).

---

### 2. copado-hx auth status (15s)

```bash
copado-hx auth status
```

**Say:** *"All 4 services authenticated — Salesforce for data, Actions API for CI/CD, CRT for robotic testing, AI Context Hub for agents. One login, all connected."*

---

### 3. copado-hx story list (15s)

```bash
copado-hx story list
```

**Say:** *"Our user story — 'My first Source Format User Story'. We'll work from this throughout."*

---

### 4. copado-hx story show US-0000024 (15s)

```bash
copado-hx story show US-0000024
```

**Say:** *"Draft status. Let's commit, promote, and test it — all from here."*

---

### 5. copado-hx workflow list (15s)

```bash
copado-hx workflow list
```

**Say:** *"7 available workflows. These are the AI Platform workflows. But for CI/CD we use the Actions API — faster, no workflow nodes needed."*

---

### 6. Set context + commit (25s)

```bash
copado-hx story set a1vhk0000000P01AAE
copado-hx commit -m "feat: lead scoring"
```

**Say:** *"Set context, then commit. Behind the scenes this calls the Actions API — RunJobTemplate with the sfdx_commit_1 template. Returns a real Job Execution ID."*

**Key point:** Emphasize *"Actions API, not AI Platform workflows. This is the newer, faster CI/CD path."*

---

### 7. copado-hx promote --env UAT-SFP --validate (20s)

```bash
copado-hx promote --env UAT-SFP --validate
```

**Say:** *"Validation-only promote to UAT-SFP through the Actions API. The --validate flag triggers a dry run — no actual deployment, just checks. Real Job Execution ID returned. Full CI/CD pipeline from the terminal."*

---

### 8. copado-hx test list (15s)

```bash
copado-hx test list
```

**Say:** *"CRT — Copado Robotic Testing. One test job configured: CLI-Target-Job."*

---

### 9. copado-hx test run --job 120561 (20s)

```bash
copado-hx test run --job 120561
```

**Say:** *"Trigger a test execution. Returns a real Execution ID — real CRT API call to the EU region. Run test status to check results."*

---

### 10. copado-hx env list (15s)

```bash
copado-hx env list
```

**Say:** *"7 pipeline environments — Dev1-SFP, Dev2-SFP, INT-SFP, UAT-SFP, Production-SFP. Full enterprise pipeline visible from terminal."*

---

### 11. copado-hx env list --json (15s)

```bash
copado-hx env list --json
```

**Say:** *"Every command supports --json for machine parsing. Pipe to jq, feed into CI/CD scripts, integrate with anything."*

---

### 12. copado-hx deploy --env PROD (15s)

```bash
copado-hx deploy --env PROD
# Type 'n' at the prompt
```

**Say:** *"PROD deploy requires human approval — type 'y' to proceed, 'n' to cancel. We'll cancel here. Safety first."*

**Pointer:** Pause at the prompt, look at judges, say *"Security gate — built in."*

---

### 13. Ask Build Agent about lead scoring (40s)

```bash
copado-hx ai ask --agent build "What Apex metadata should I create for a lead scoring feature?"
```

**Say:** *"AI Context Hub — 5 specialist agents. Build agent responds with architecture: Apex service class, trigger, handler, batch job, test classes. Real AI, real guidance, no copy-paste from docs."*

**Pointer:** Scroll through the response quickly, highlight the architecture diagram section. Don't read it — just show the richness.

---

### 14. Multi-Agent Handoff: Build → Test (30s)

```bash
copado-hx ai ask --agent test "Generate QWord test scripts for: LeadScoringService, LeadScoringTriggerHandler, LeadScoringBatchJob"
```

**Say:** *"Now the multi-agent handoff — I pass the Build Agent's output to the Test Agent so it generates tests for the exact classes identified. Context flows between agents via --json. No copy-paste, no browser."*

**Key point:** Emphasize *"Build Agent identified the classes, Test Agent generates the tests — handoff happens through the CLI's --json pipeline, no manual context switching."*

---

### 15. copado-hx status --json (15s)

```bash
copado-hx status --json
```

**Say:** *"Full pipeline status as JSON. Machine-readable, scriptable, integrable."*

---

### 16. copado-hx mcp --list-tools (15s)

```bash
copado-hx mcp --list-tools
```

**Say:** *"MCP Server — 28 tools auto-discovered by any MCP-compatible agent. Cursor, Claude Desktop, VS Code can all talk to copado-hx natively."*

---

### Outro (30s) — The Close

**Say:** *"That's copado-hx. All 4 Copado API surfaces — Actions API for CI/CD, CRT for testing, Context Hub for AI. SKILL.md for AI agents. MCP Server for agent discovery. All from the terminal. No browser. No context switching."*

*Pause, make eye contact with judges.*

**Say:** *"We're team Headless Nomads. Happy to answer questions. Thank you."*

---

## Winning Tips

| Tip | Why |
|-----|-----|
| **Lead with "why"** | First 10s should answer: why does this matter? (No browser, no context switching) |
| **Emphasize Actions API** | Judges asked for CI/CD — Actions API is the differentiator vs AI Platform workflows |
| **Mention "4 API surfaces"** | Shows breadth: Actions API (CI/CD) + SF REST + CRT (testing) + Context Hub (AI) |
| **Mention "MCP Server bonus"** | Extra credit — 28 tools, auto-discoverable |
| **Agentforce Action built (skip in demo)** | Agentforce `@InvocableMethod` Apex class + metadata in `agentforce/` — omitted from live demo due to time |
| **Pace = slow** | Nerves make you speed up. Deliberately pause between commands. Count to 2 after each output appears. |
| **If API fails** | Switch immediately: *"Let me show you the recording instead"* → `asciinema play demo/demo-recording.cast --speed 2`. No apology, no fumbling. |
| **If you forget a line** | Silence is better than filler. Just do the next command. The output speaks for itself. |
| **Close strong** | End on "No browser. No context switching." — that's your tagline. Judges will remember one line. |
| **Mirror judges' body language** | Lean forward when they lean forward. Smile. Be confident but not arrogant. |
| **Team presence** | One speaks, one handles terminal. Switch roles smoothly. Practice handoff. |

---

## Fallback (if live APIs fail mid-demo)

```bash
# Don't panic. Say:
# "Let me show you the recorded version with the same real API responses."

asciinema play demo/demo-recording.cast --speed 2
# Narrate over it using the same script above
```

## After Demo
- [ ] Stop screen recording
- [ ] Answer questions honestly — "I don't know" is better than "I think..."
- [ ] Thank the judges
- [ ] Collect feedback
