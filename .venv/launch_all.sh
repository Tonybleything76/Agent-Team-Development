#!/usr/bin/env bash
set -euo pipefail

# --- Paths ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/out}"
mkdir -p "$ARTIFACT_DIR"

# --- Python venv ---
if [[ -d "$PROJECT_ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.venv/bin/activate"
else
  echo "ERROR: .venv not found. Create it with: python3 -m venv .venv"
  exit 1
fi

# --- Env file ---
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "$PROJECT_ROOT/.env"; set +a
else
  echo "WARN: .env not found; proceeding without API keys (agents may fail)."
fi

# --- MCP registry file location (used by the SDK) ---
export MCP_SERVERS_FILE="${MCP_SERVERS_FILE:-$PROJECT_ROOT/mcp/registry.yaml}"

# --- Start MCP servers (filesystem + fetch) ---
echo "[launcher] Starting MCP servers..."
npx -y @modelcontextprotocol/server-filesystem "$PROJECT_ROOT" \
  > "$ARTIFACT_DIR/mcp-filesystem.log" 2>&1 & FS_PID=$!

npx -y @modelcontextprotocol/server-fetch \
  > "$ARTIFACT_DIR/mcp-fetch.log" 2>&1 & FETCH_PID=$!

# Ensure we stop servers if user Ctrl+C
cleanup() {
  echo "[launcher] Shutting down..."
  [[ -n "${FS_PID:-}" ]] && kill "$FS_PID" 2>/dev/null || true
  [[ -n "${FETCH_PID:-}" ]] && kill "$FETCH_PID" 2>/dev/null || true
}
trap cleanup EXIT

# --- Small wait to let servers get ready ---
sleep 1

# --- Launch agents that are installed locally ---
run_agent () {
  local module="$1"
  local name="$2"
  if python -c "import $module" >/dev/null 2>&1; then
    echo "[launcher] Starting $name..."
    # run each agent in the background; logs go to out/
    python -m "$module".main > "$ARTIFACT_DIR/${name}.log" 2>&1 & echo $!
  else
    echo "[launcher] Skipping $name (module '$module' not installed)."
  fi
}

SALES_PID=$(run_agent "sales_agent" "sales_agent" || true)
MARKETING_PID=$(run_agent "marketing_agent" "marketing_agent" || true)
CONTENT_PID=$(run_agent "content_agent" "content_agent" || true)
GOV_PID=$(run_agent "governance_agent" "governance_agent" || true)

echo "[launcher] All start attempts complete. Logs are in: $ARTIFACT_DIR"
echo "[launcher] Press Ctrl+C to stop everything."

# Keep the script running so background agents/servers stay alive
while true; do sleep 60; done
