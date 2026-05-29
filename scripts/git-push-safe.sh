#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$REPO_DIR/.cred-backup"

# Files that contain hardcoded credentials
FILES_WITH_CREDS=(
  "copado_hx/utils/config.py"
  "tests/test_core.py"
)
# These are gitignored but keep them safe too
GITIGNORED_CRED_FILES=(
  "setup-env.sh"
  "test-auth.sh"
)

cleanup() {
  if [ -d "$BACKUP_DIR" ]; then
    echo "Restoring credentials from backup..."
    for f in "${FILES_WITH_CREDS[@]}"; do
      if [ -f "$BACKUP_DIR/$f" ]; then
        cp "$BACKUP_DIR/$f" "$REPO_DIR/$f"
      fi
    done
    rm -rf "$BACKUP_DIR"
    echo "Credentials restored."
  fi
}
trap cleanup EXIT

echo "=== Step 1: Backup credential files ==="
mkdir -p "$BACKUP_DIR"
for f in "${FILES_WITH_CREDS[@]}"; do
  mkdir -p "$(dirname "$BACKUP_DIR/$f")"
  cp "$REPO_DIR/$f" "$BACKUP_DIR/$f"
done
echo "Backup saved to $BACKUP_DIR"

echo ""
echo "=== Step 2: Strip credentials ==="
# config.py — empty the defaults
sed -i '' \
  -e "s/^    cicd_instance: str = \".*\"/    cicd_instance: str = \"\"/" \
  -e "s/^    sf_client_id: str = \".*\"/    sf_client_id: str = \"\"/" \
  -e "s/^    sf_client_secret: str = \".*\"/    sf_client_secret: str = \"\"/" \
  -e "s/^    ai_api_key: str = \".*\"/    ai_api_key: str = \"\"/" \
  -e "s/^    ai_org_id: str = \".*\"/    ai_org_id: str = \"\"/" \
  -e "s/^    ai_workspace_id: str = \".*\"/    ai_workspace_id: str = \"\"/" \
  -e "s/^    crt_pak: str = \".*\"/    crt_pak: str = \"\"/" \
  -e "s/^    crt_org_id: str = \".*\"/    crt_org_id: str = \"\"/" \
  -e "s/^    crt_project_id: str = \".*\"/    crt_project_id: str = \"\"/" \
  -e "s/^    crt_job_id: str = \".*\"/    crt_job_id: str = \"\"/" \
  -e "s/^    actions_api_key: str = \".*\"/    actions_api_key: str = \"\"/" \
  -e "s/^    actions_base_url: str = \".*\"/    actions_base_url: str = \"\"/" \
  "$REPO_DIR/copado_hx/utils/config.py"

# test_core.py — update assertions to match empty defaults
sed -i '' \
  -e 's/assert cfg.cicd_instance == ".*"/assert cfg.cicd_instance == ""/' \
  -e 's/assert cfg.sf_client_id == ".*"/assert cfg.sf_client_id == ""/' \
  -e 's/assert cfg.ai_api_key == ".*"/assert cfg.ai_api_key == ""/' \
  -e 's/assert cfg.crt_pak == ".*"/assert cfg.crt_pak == ""/' \
  -e 's/assert cfg.actions_api_key == ".*"/assert cfg.actions_api_key == ""/' \
  -e 's/assert cfg.ai_org_id == ".*"/assert cfg.ai_org_id == ""/' \
  -e 's/assert cfg.crt_job_id == ".*"/assert cfg.crt_job_id == ""/' \
  "$REPO_DIR/tests/test_core.py"

# Ensure gitignored files are not staged
for f in "${GITIGNORED_CRED_FILES[@]}"; do
  if [ -f "$REPO_DIR/$f" ]; then
    git -C "$REPO_DIR" rm --cached --ignore-unmatch "$f" 2>/dev/null || true
  fi
done

echo "Credentials stripped."

echo ""
echo "=== Step 3: Show staged changes ==="
git -C "$REPO_DIR" status
echo ""
echo "=== Summary ==="
echo "Changes to review:"
git -C "$REPO_DIR" diff --stat

echo ""
echo "=== Step 4: Commit and Push ==="
read -r -p "Commit message (leave empty to skip commit): " msg
if [ -n "$msg" ]; then
  git -C "$REPO_DIR" add -A
  git -C "$REPO_DIR" commit -m "$msg"
  echo "Pushing..."
  git -C "$REPO_DIR" push
  echo "Push complete."
else
  echo "Skipped. Run manually:"
  echo "  git add -A && git commit -m \"msg\" && git push"
  echo ""
  echo "After push, credentials auto-restore on exit."
fi
