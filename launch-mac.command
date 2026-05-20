#!/bin/bash
# Arkan Finance — macOS double-click launcher
# Place this file anywhere (e.g. Desktop), chmod +x it once, then double-click.

set -e

# Resolve the project directory (same folder as this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/backend"
PORT=8080
URL="http://localhost:$PORT"

echo "========================================"
echo "  Arkan Finance — Market Intelligence   "
echo "========================================"

# ── 1. Python check ──────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3.11 python3.12 python3.10 python3 python; do
  if command -v "$candidate" &>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  osascript -e 'display alert "Python not found" message "Install Python 3.10+ from https://python.org then re-run."'
  exit 1
fi
echo "✓ Using $PYTHON ($($PYTHON --version 2>&1))"

# ── 2. Virtual env (created once, reused) ────────────────────────────────────
VENV="$BACKEND/.venv"
if [ ! -d "$VENV" ]; then
  echo "→ Creating virtual environment (first run only)…"
  "$PYTHON" -m venv "$VENV"
fi
source "$VENV/bin/activate"

# ── 3. Install / upgrade deps ────────────────────────────────────────────────
echo "→ Checking dependencies…"
pip install -q --upgrade pip
pip install -q -r "$BACKEND/requirements.txt"
echo "✓ Dependencies ready"

# ── 4. Kill any previous instance on $PORT ───────────────────────────────────
lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null || true

# ── 5. Start FastAPI server in the background ────────────────────────────────
echo "→ Starting server on $URL"
cd "$BACKEND"
nohup python -m uvicorn main:app --host 127.0.0.1 --port $PORT \
  > "$BACKEND/arkan.log" 2>&1 &
SERVER_PID=$!
echo "  Server PID: $SERVER_PID"

# ── 6. Wait for server to be ready ───────────────────────────────────────────
echo -n "→ Waiting for server"
for i in $(seq 1 30); do
  if curl -s "$URL/api/health" >/dev/null 2>&1; then
    echo " ready!"
    break
  fi
  echo -n "."
  sleep 1
done

# ── 7. Open in default browser ───────────────────────────────────────────────
echo "→ Opening $URL in browser"
open "$URL"

echo ""
echo "✓ Arkan Finance is running at $URL"
echo "  Logs: $BACKEND/arkan.log"
echo "  Press Ctrl+C here to stop the server."
echo ""

# Keep terminal open; trap Ctrl+C to cleanly stop server
trap "echo ''; echo 'Stopping server…'; kill $SERVER_PID 2>/dev/null; exit 0" INT TERM
wait $SERVER_PID
