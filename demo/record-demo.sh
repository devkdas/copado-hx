#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

echo "=== copado-hx Demo Recording ==="
echo "Starting in 3 seconds..."
sleep 3

pause() {
  local msg="$1"
  echo ""
  echo "# $msg"
  sleep 2
}

type_cmd() {
  local cmd="$1"
  echo ""
  echo "$ $cmd"
  sleep 1
  eval "$cmd"
  sleep 2
}

# Source venv
source venv/bin/activate

# === STEP 1: Help ===
pause "Step 1: copado-hx --help"
type_cmd "copado-hx --help"

# === STEP 2: Auth Status ===
pause "Step 2: Authentication Status"
type_cmd "copado-hx auth status"

# === STEP 3: Story List ===
pause "Step 3: List User Stories"
type_cmd "copado-hx story list"

# === STEP 4: Story Show ===
pause "Step 4: Show User Story Details"
type_cmd "copado-hx story show US-0000024"

# === STEP 5: Workflow List ===
pause "Step 5: List Available CI/CD Workflows"
type_cmd "copado-hx workflow list"

# === STEP 6: Set Context + Commit ===
pause "Step 6: Set Working Context and Commit"
type_cmd "copado-hx story set a1vhk0000000P01AAE"
type_cmd 'copado-hx commit -m "feat: add lead scoring"'

# === STEP 7: Promote ===
pause "Step 7: Promote to UAT"
type_cmd "copado-hx promote --env UAT"

# === STEP 8: CRT Test List ===
pause "Step 8: List CRT Test Jobs"
type_cmd "copado-hx test list"

# === STEP 9: CRT Test Run ===
pause "Step 9: Trigger CRT Test Execution"
type_cmd "copado-hx test run --job 120561"

# === STEP 10: Environments ===
pause "Step 10: List Pipeline Environments"
type_cmd "copado-hx environments"

# === STEP 11: Environments --json ===
pause "Step 11: Machine-Readable Output (--json flag)"
type_cmd "copado-hx environments --json"

# === STEP 12: Deploy (with approval gate demo) ===
pause "Step 12: Deploy to Production (with approval gate)"
echo ""
echo "$ copado-hx deploy --env PROD"
sleep 1
echo "[red]You are about to deploy to PRODUCTION. Continue? [y/N]:[/red] n"
sleep 1
echo "Deployment cancelled"
echo ""

# === STEP 13: AI Agent ===
pause "Step 13: Ask Build Agent for Implementation Guidance"
type_cmd 'copado-hx ai ask --agent build "What Apex metadata should I create for a lead scoring feature?"'

# === STEP 14: JSON Output ===
pause "Step 14: Status --json"
type_cmd "copado-hx status --json"

# === STEP 15: MCP Server ===
pause "Step 15: MCP Server"
echo ""
echo "$ copado-hx mcp"
sleep 1
echo "copado-hx MCP server starting (stdio transport)..."
echo "17 tools auto-discovered by any MCP-compatible agent"
echo ""

# === DONE ===
echo ""
echo "=== Demo Complete ==="
echo "All 3 Copado API surfaces demonstrated:"
echo "  - CI/CD via Actions API + Job Templates"
echo "  - Robotic Testing (CRT)"
echo "  - AI Context Hub (5 Specialist Agents)"
echo ""
echo "No browser tab opened at any point."
echo "Every operation from the terminal."
