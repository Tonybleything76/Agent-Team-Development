#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
cd "$(dirname "$0")"

# --- 0) Sanity: venv check ---------------------------------------------------
if [[ ! -f ".venv/bin/activate" ]]; then
  echo "ERROR: .venv not found. Create/activate it first:"
  echo "  python3 -m venv .venv && source .venv/bin/activate"
  echo "  pip install -e ./adeptly_mcp_sdk && pip install -e ./agents/sales_agent"
  exit 1
fi

# --- 1) Activate venv ---------------------------------------------------------
source .venv/bin/activate

# --- 2) Load .env (optional) --------------------------------------------------
# Keeps API keys/secrets out of your code; .env should be in .gitignore
if [[ -f ".env" ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs || true)
fi

mkdir -p logs .pids

# --- 3) Start MCP servers in background --------------------------------------
# Filesystem server (Node)
# Runs against the current directory: "."
echo "[start_all] Launching MCP filesystem server…"
npx -y @modelcontextprotocol/server-filesystem . > logs/filesystem.log 2>&1 &
FS_PID=$!
echo $FS_PID > .pids/filesystem.pid
echo "[start_all] filesystem PID: $FS_PID (logs/filesystem.log)"

# Fetch server (Python; installed in this venv)
echo "[start_all] Launching MCP fetch server…"
python -m mcp_server_fetch > logs/fetch.log 2>&1 &
FETCH_PID=$!
echo $FETCH_PID > .pids/fetch.pid
echo "[start_all] fetch PID: $FETCH_PID (logs/fetch.log)"

# --- 4) Run your agent in the foreground -------------------------------------
# Foreground means Ctrl+C will stop the agent; servers remain running.
echo "[start_all] Starting Sales Agent…"
python -m sales_agent.main 2>&1 | tee -a logs/agent.log

# --- 5) Optional: clean up servers when agent exits ---------------------------
# If you want servers to stop when the agent stops, uncomment the lines below:
# if kill -0 "$FS_PID" 2>/dev/null; then kill "$FS_PID" || true; fi
# if kill -0 "$FETCH_PID" 2>/dev/null; then kill "$FETCH_PID" || true; fi
# rm -f .pids/filesystem.pid .pids/fetch.pid
