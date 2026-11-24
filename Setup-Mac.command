#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v brew >/dev/null 2>&1; then
    if node_prefix=$(brew --prefix node@22 2>/dev/null); then
        export PATH="$node_prefix/bin:$PATH"
    fi
    if python_prefix=$(brew --prefix python@3.12 2>/dev/null); then
        export PATH="$python_prefix/bin:$PATH"
    fi
fi

if ! command -v python3.12 >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    printf '%s\n' 'Install Python 3.12 and Node.js 22 first. See README-MAC.md.'
    exit 1
fi
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (!(major === 22 && minor >= 12 || major >= 24)) { console.error("Use Node.js 22.12+ or 24+. See README-MAC.md."); process.exit(1); }'

if [[ -d .venv && ! -x .venv/bin/python ]]; then
    printf '%s\n' 'An incompatible .venv exists. Move it aside and run setup again.'
    exit 1
fi
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci)

if [[ ! -f backend/.env ]]; then
    cp backend/.env.example backend/.env
fi
if command -v brew >/dev/null 2>&1 && brew list --versions mongodb-community@8.0 >/dev/null 2>&1; then
    brew services start mongodb-community@8.0 || printf '%s\n' 'Start MongoDB manually before using the app.'
fi

printf '\n%s\n' 'Setup complete. Put your own GROQ_API_KEY in backend/.env, then run Start-Mac.command.'