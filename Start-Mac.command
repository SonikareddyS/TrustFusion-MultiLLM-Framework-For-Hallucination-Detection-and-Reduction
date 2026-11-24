#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v brew >/dev/null 2>&1; then
    if node_prefix=$(brew --prefix node@22 2>/dev/null); then
        export PATH="$node_prefix/bin:$PATH"
    fi
fi
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules || ! -f backend/.env ]]; then
    printf '%s\n' 'Run Setup-Mac.command first, then configure backend/.env.'
    exit 1
fi
.venv/bin/python -c 'from dotenv import dotenv_values; import sys; key = dotenv_values("backend/.env").get("GROQ_API_KEY", ""); sys.exit(0 if key and not key.startswith("replace_") else "Set your own GROQ_API_KEY in backend/.env first.")'

for port in 8000 5173; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        printf 'Port %s is already in use. Stop that process before starting TrustFusion.\n' "$port"
        exit 1
    fi
done

backend_pid=""
frontend_pid=""
cleanup() {
    if [[ -n "$frontend_pid" ]]; then kill "$frontend_pid" 2>/dev/null || true; fi
    if [[ -n "$backend_pid" ]]; then kill "$backend_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

.venv/bin/python -B -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 &
backend_pid=$!
node frontend/node_modules/vite/bin/vite.js --help >/dev/null
(
    cd frontend
    exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort --open
) &
frontend_pid=$!
printf '\n%s\n' 'TrustFusion: http://127.0.0.1:5173/' 'Keep this Terminal open. Press Control-C to stop both servers.'
wait "$backend_pid"