#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

stop_pid_file () {
  local file="$1"
  if [[ -f "$file" ]]; then
    local pid
    pid=$(cat "$file" || true)
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "[stop_all] Stopping PID $pid from $file…"
      kill "$pid" || true
      # give it a moment, then force if needed
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$file"
  fi
}

stop_pid_file ".pids/filesystem.pid"
stop_pid_file ".pids/fetch.pid"

echo "[stop_all] Done."
