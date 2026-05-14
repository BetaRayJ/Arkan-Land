#!/usr/bin/env bash
set -e

echo "=== Arkan Finance Platform ==="

# Install / upgrade Python deps
echo "[1/2] Installing backend dependencies..."
pip install -q --upgrade -r backend/requirements.txt

# Start FastAPI
echo "[2/2] Starting server on http://localhost:8080"
echo "      Press Ctrl+C to stop."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
