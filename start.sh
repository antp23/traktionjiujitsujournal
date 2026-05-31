#!/bin/bash
# BJJ Tracker — start backend + frontend

echo "🥋 Starting BJJ Tracker..."

# Backend
cd "$(dirname "$0")/backend"
source venv/bin/activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
echo "✓ Backend running on http://localhost:8000 (pid $BACKEND_PID)"

# Frontend
cd "$(dirname "$0")/frontend"
if command -v npm >/dev/null 2>&1; then
  npm run dev -- --host 127.0.0.1 &
else
  NODE_BIN="${NODE_BIN:-node}"
  if ! command -v "$NODE_BIN" >/dev/null 2>&1 && [ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" ]; then
    NODE_BIN="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
  fi
  "$NODE_BIN" ./node_modules/vite/bin/vite.js --host 127.0.0.1 &
fi
FRONTEND_PID=$!
echo "✓ Frontend starting on http://localhost:5173 (pid $FRONTEND_PID)"

echo ""
echo "Dashboard: http://localhost:5173"
echo "API docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" INT
wait
