#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
APP_MODE=demo .venv/bin/uvicorn human_api.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload &
API_PID=$!
cd frontend
npm run dev -- --host 127.0.0.1 &
WEB_PID=$!
cleanup() {
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
wait "$API_PID" "$WEB_PID"
