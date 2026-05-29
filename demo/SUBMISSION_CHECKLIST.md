# Submission Checklist — CopadoCON Bangalore 2026 Hackathon

## Track B: Agentic Orchestrator

### Deadline: 3 June 2026, 11:59 PM IST
### Submit to: hackathon@copado.com

---

## Deliverables

- [x] **GitHub Repository** — https://github.com/devkdas/copado-hx
  - [x] MIT License
  - [x] Source code only (no credentials)
  - [x] All code written during hackathon

- [x] **README.md** — Setup, architecture diagram, API usage, install instructions
  - [x] Verified on GitHub

- [x] **SKILL.md** — At repo root
  - [x] All 7 sections: Identity, Prerequisites, Commands Reference, Workflow Playbooks, Guardrails, Output Parsing Guide, Agent Persona Routing

- [ ] **Demo Video (max 5 min)** — Recorded walkthrough
  - [ ] Recorded with voiceover following demo/VIDEO_SCRIPT.md
  - [ ] Under 5 minutes
  - [ ] No Copado UI tab opened during demo
  - [ ] Shows all 3 API surfaces: CI/CD (Actions API), CRT, AI
   - [ ] Asciinema terminal recording done: demo/demo-recording.cast (46s at 1x)
  - [ ] GIF conversion done: demo/demo.gif

- [x] **Slide Deck (max 8 slides)**
  - [x] Markdown: demo/DECK.md
  - [x] PowerPoint: demo/copado-hx-deck.pptx
  - [x] Problem slide
  - [x] Architecture slide (Actions API updated)
  - [x] Auth slide
  - [x] CI/CD slide (Actions API, not AI Platform workflows)
  - [x] AI Agents slide
  - [x] CRT Testing slide
  - [x] MCP Server slide
  - [x] Demo/Results slide

- [x] **Brief Written Description** — README.md covers this

---

## Rules Compliance

- [x] Rule 1: All code written during hackathon
- [x] Rule 2: Open-source libraries used (httpx, Typer, Rich, FastMCP)
- [x] Rule 3: Hackathon credentials for Copado API calls
- [x] Rule 4: No credentials committed (git-push-safe.sh handles stripping)
- [x] Rule 5: Team size (min 2 members) — Kartheek Dasari + Ravalika Bommera
- [x] Rule 6: Copado UI for setup only (sf org login web is Salesforce OAuth)
- [x] Rule 7: Only 5 specialist agents (no Orchestrate Agent)
- [x] MCP Server bonus implemented
- [x] All 3 API surfaces integrated (Actions API for CI/CD, CRT for testing, Context Hub for AI)

---

## Pre-Submission Verification

- [x] Tests pass: pytest tests/ (17 passed)
- [x] pyflakes clean: no warnings
- [x] auth status shows all 4 services green
- [x] story list returns results (1 story)
- [x] workflow list shows 7 workflows
- [x] commit works via Actions API (returns Job Execution ID)
- [x] promote works via Actions API (returns Job Execution ID)
- [x] ai ask --agent works (Build agent responded with Apex code)
- [x] test list shows CRT jobs (1 job: CLI-Target-Job)
- [x] environments shows pipeline environments (7 envs)
- [x] deploy PROD gate shows confirmation prompt
- [x] config --show masks secrets (keys show `***`)
- [x] GitHub repo has no hardcoded credentials (verified via API)
- [x] Single signed commit (verified by GitHub)
- [x] git-push-safe.sh updated to strip all sensitive fields (incl. actions_api_key)
- [x] PPTX deck generated (8 slides, dark theme)
- [x] Asciinema re-recorded with real API responses (not the 500-era fake)
- [x] MCP server starts successfully (17 tools advertised)

---

## Demo Jam (13 June 2026) — Additional Prep

- [ ] Demo video recorded with voiceover
- [ ] Laptop charged, terminal dark theme, large font
- [ ] `source venv/bin/activate` pre-run
- [ ] `~/.copado-hx-secrets.json` in place with fresh SF access token
- [ ] Internet connection confirmed (SF REST + Actions API + CRT + AI)
- [ ] Backup creds: config.py, test_core.py, ~/.copado-hx-secrets.json
- [ ] Fallback: asciinema play demo/demo-recording.cast if live demo fails
- [ ] PPTX deck on laptop + backup USB / cloud
- [ ] All commands verified working in pre-demo walkthrough

---

## Submission Email Template

```
To: hackathon@copado.com
Subject: Hackathon Submission -- Track B -- copado-hx

Team Name: copado-hx
Track: B (Agentic Orchestrator)
GitHub Repository: https://github.com/devkdas/copado-hx
Demo Video: [Link to video or attachment]
Slide Deck: Included in repo at demo/DECK.md and demo/copado-hx-deck.pptx

Team Lead: Ravalika Bommera
Team Members: Kartheek Dasari (devkdas), Ravalika Bommera

Brief Description:
copado-hx is a unified CLI that wraps Copado CI/CD (via Copado Actions API),
Robotic Testing (CRT), and AI Context Hub (5 specialist agents) into a single
terminal tool. Extended with SKILL.md for autonomous AI agent operation and
an MCP Server for native agent discovery.
```

---

## After Submission

- [ ] Semi-finalists announced: 8 June 2026
- [ ] Live demo prep (if shortlisted): 13 June 2026 at CopadoCon Bangalore
