#!/usr/bin/env bash
set -euo pipefail

# run-dev-linux.sh - Development startup script for Linux
# Usage: ./scripts/run-dev-linux.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting Interview Analyzer (Dev Mode) on Linux..."

# Activate virtualenv if present
if [ -f ".venv/bin/activate" ]; then
  echo "Activating virtual environment .venv..."
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Ensure logs directory
mkdir -p .dev_logs

# Cleanup function to kill background servers
cleanup() {
  echo "Stopping dev services..."
  if [ -f .backend_dev_pid ]; then
    kill "$(cat .backend_dev_pid)" >/dev/null 2>&1 || true
    rm -f .backend_dev_pid
  fi
  if [ -n "${VITE_PID:-}" ]; then
    kill "$VITE_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Start backend in background
echo "Starting backend (backend/main.py)..."
python3 -u backend/main.py > .dev_logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend_dev_pid

# Start frontend Vite dev server in background
echo "Starting frontend (Vite dev server)..."
cd electron
# install deps if node_modules missing (non-fatal)
if [ ! -d "node_modules" ]; then
  echo "Installing Node dependencies (this may take a while)..."
  npm install || true
fi
npm run dev > ../.dev_logs/vite.log 2>&1 &
VITE_PID=$!

# Give servers a moment to boot
sleep 1

# Start Electron (foreground)
echo "Starting Electron..."
# In dev mode, Electron will load the Vite dev server
npx electron .

# When Electron exits, cleanup will run via trap
