# Demo Video Script (5 minutes)

## Setup
**Screen:** Full-screen terminal (dark theme, large font)
**Tools:** iTerm2 + copado-hx CLI + screen recorder (OBS/QuickTime)
**Playback:** `asciinema play demo/demo-recording.cast --speed 2` (~23s)

---

## 0:00 — Title Card (15s)

**Visual:** `copado-hx` ASCII art logo + Track B badge
**Audio:** "Copado Headless Developer Experience — Track B Agentic Orchestrator. Kartheek Dasari and Ravalika Bommera."

---

## 0:15 — The Problem (30s)

**Visual:** Browser tabs montage (Salesforce Lightning, CRT, AI Context Hub)
**Audio:** "Salesforce DevOps today means context-switching across three browser tabs — CI/CD in Lightning, testing in CRT, AI in the Context Hub. copado-hx unifies all three into one CLI. One terminal. Zero browser tabs."

---

## 0:45 — Auth + Help + Stories (30s)

**Visual:** Start asciinema playback. Steps 1–4: `--help`, `auth status`, `story list`, `story show`.
**Audio:** "One command shows all services authenticated — AI Platform, CRT Testing, Actions API for CI/CD. List user stories, inspect details, all from the terminal."

---

## 1:15 — CI/CD Pipeline (45s)

**Visual:** Steps 5–7: `workflow list`, `story set`, `commit`, `promote`.
**Audio:** "Seven built-in workflows available. Set the working story context, commit metadata changes — triggers a Copado Actions API job execution. Promote across environments. All real API calls, no fake output."

---

## 2:00 — CRT Testing + Environments (45s)

**Visual:** Steps 8–11: `test list`, `test run`, `environments`, `environments --json`.
**Audio:** "List CRT test jobs, trigger a build execution. List all pipeline environments — seven environments from Copado to UAT. Every command supports --json for machine-readable output."

---

## 2:45 — Production Deploy Gate + AI Agent (45s)

**Visual:** Steps 12–13: `deploy --env PROD` (cancelled), `ai ask --agent build`.
**Audio:** "Production deployment has a human approval gate — the CLI stops and asks for confirmation. Then ask the Build Agent for implementation guidance. It scans the org and returns comprehensive Apex architecture with code samples."

---

## 3:30 — JSON Output + Status + MCP Server (45s)

**Visual:** Steps 14–15: `status --json`, `mcp`.
**Audio:** "Every command returns JSON for scripting and CI integration. The MCP Server exposes all 17 commands as discoverable tools — any MCP-compatible agent like Claude Code or Cursor can drive copado-hx natively."

---

## 4:15 — SKILL.md + Closing (45s)

**Visual:** Show SKILL.md header (29 sections, 5 playbooks, 9 guardrails) + copado-hx --help
**Audio:** "The SKILL.md gives any AI coding assistant full playbooks for all 3 API surfaces. copado-hx — no browser, no context switching, just your terminal and your AI. Built for CopadoCON Bangalore 2026."

---

## Technical Notes

### Recording Tips
- Use OBS / QuickTime Player for screen + audio recording
- Play asciinema at 2x speed: `asciinema play demo/demo-recording.cast --speed 2`
- Record voiceover separately, sync in post-production
- Keep terminal full-screen, dark theme, monospace font (Fira Code / JetBrains Mono)

### File Locations
- Terminal recording: `demo/demo-recording.cast`
- Video output: `demo/copado-hx-demo.mp4`
- Slide deck: `demo/copado-hx-deck.pptx`

### Actual Recording Contents (15 steps, 46s at 1x)
| Step | Command | Real API |
|---|---|---|---|
| 1 | `copado-hx --help` | — |
| 2 | `copado-hx auth status` | 4/4 green |
| 3 | `copado-hx story list` | SF REST: 1 story |
| 4 | `copado-hx story show US-0000024` | SF REST: story details |
| 5 | `copado-hx workflow list` | AI Platform: 7 workflows |
| 6 | `copado-hx story set + commit -m "feat: lead scoring"` | Actions API: JE returned |
| 7 | `copado-hx promote --env UAT` | Actions API: JE returned |
| 8 | `copado-hx test list` | CRT: 1 job |
| 9 | `copado-hx test run --job 120561` | CRT: build triggered (ID: 5249902) |
| 10 | `copado-hx environments` | SF REST: 7 envs |
| 11 | `copado-hx environments --json` | SF REST: JSON output |
| 12 | `copado-hx deploy --env PROD` | Gate: cancelled at prompt |
| 13 | `copado-hx ai ask --agent build "Lead scoring?"` | AI Context Hub: Apex code |
| 14 | `copado-hx status --json` | SF REST: JSON |
| 15 | `copado-hx mcp` | MCP: 17 tools |

