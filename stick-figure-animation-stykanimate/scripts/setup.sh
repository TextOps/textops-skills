#!/usr/bin/env bash
# Clone StykAnimate, install what headless rendering and .styk export need, and start the local service.
# Usage: setup.sh [app_dir] [port]   — prints the app dir on success. Safe to re-run.
set -euo pipefail
APP="${1:-${STYK_APP:-$HOME/StykAnimate-App}}"
PORT="${2:-${STYK_PORT:-47831}}"

if [ ! -d "$APP/.git" ]; then
  git clone --depth 1 https://github.com/filippocalippo/StykAnimate-App "$APP" >&2
fi
if [ ! -d "$APP/node_modules" ]; then
  # Electron's binary is not needed: rendering runs in headless Chromium.
  (cd "$APP" && ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm ci --ignore-scripts >&2)
fi
python3 -m pip install -q -r "$APP/backend/requirements-fast.txt" >&2 || echo "optional fast codec deps not installed" >&2

if ! curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null; then
  # Redirect the whole subshell and exec node, so nothing holds a caller's $(...) pipe open.
  (cd "$APP" && STYK_PYTHON="${STYK_PYTHON:-python3}" exec setsid node scripts/serve.mjs --port "$PORT") \
    < /dev/null > "$APP/../stykanimate-serve.log" 2>&1 &
  for _ in $(seq 1 30); do curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null && break; sleep 1; done
fi
curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null || { echo "service did not start; see $APP/../stykanimate-serve.log" >&2; exit 1; }
echo "$APP"
