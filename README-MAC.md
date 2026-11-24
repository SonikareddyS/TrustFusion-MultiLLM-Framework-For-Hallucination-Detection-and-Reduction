# Run TrustFusion On A Mac

This ZIP is a snapshot of the current working source, including uncommitted
changes. It is not a trained-model export. Windows virtual environments, installed
dependencies, private `.env` files, Git history, build output, and database files
are excluded. Create your own account after starting the application.

## 1. Install Prerequisites

Install Homebrew from https://brew.sh/ if needed. Then open Terminal and run:

```bash
brew install python@3.12 node@22
brew tap mongodb/brew
brew install mongodb-community@8.0
brew services start mongodb-community@8.0
```

Python 3.12 and Node.js 22.12 or newer within version 22 are recommended.
Dependencies must be installed natively for your Mac; do not copy a Windows
virtual environment. Installation needs internet access and several GB of free
disk space for the Python environment and local verification models.

## 2. Run Setup

Extract the ZIP into a writable folder. Open Terminal, type `cd `, drag the
extracted `TrustFusion` folder into Terminal, and press Return. Then run:

```bash
bash Setup-Mac.command
```

Setup installs Python and frontend dependencies and creates `backend/.env`
without overwriting an existing file. Open that file in a text editor and replace
the `GROQ_API_KEY` placeholder with your own Groq API key from https://console.groq.com/keys.
Do not share this file or send credentials in chat.

MongoDB defaults to `mongodb://localhost:27017`. A different local or remote
MongoDB deployment can be configured through `MONGO_URI` in `backend/.env`.
The OpenRouter key is optional; the unpaid Mistral option is disabled by default.

## 3. Start The App

From the same Terminal folder:

```bash
bash Start-Mac.command
```

The script starts both servers and opens http://127.0.0.1:5173/ in your browser.
Register your own user account. Keep Terminal open; Control-C stops both servers.
Double-clicking the `.command` files in Finder may also work, but the explicit
`bash` commands avoid execute-permission and Finder launch issues.

The app uses ports 8000 and 5173. Stop other processes using those ports first.
Backend health: http://127.0.0.1:8000/health. This checks server availability,
not MongoDB or provider-account readiness.

## Manual Startup

For troubleshooting, use two Terminal windows in the project folder:

```bash
# Terminal 1
.venv/bin/python -B -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

```bash
# Terminal 2
export PATH="$(brew --prefix node@22)/bin:$PATH"
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## Verification And Limits

Default providers are GPT OSS 120B, Qwen 3.8 27B, and GPT OSS 20B on Groq.
Their availability and limits depend on your account. The app retrieves live
sources before model generation, then verifies claims. This is RAG, not
fine-tuning or retraining hosted models.

The first query may download embedding/NLI weights and can exceed the 75-second
API deadline. Retry after initialization. Semantic consensus does not prove
factual agreement; current labels and the 49% safety cap have known limitations.
Source freshness and model verification do not guarantee truth.

Focused regression checks, from the project folder:

```bash
.venv/bin/python -B tests/test_trust_accuracy.py EvidenceAccuracyTests.test_2_false_date_is_red_and_excluded TrustFormulaTests PipelineAPITests
```

This initializes real verification models before the deadline-bound API tests.
See `tests/README.md` for additional tests and historical Windows setup notes.
The source was developed on Windows. Mac shell syntax and package compatibility
can be checked separately, but full execution on an actual Mac has not been
verified. If installation fails, share the error text, not your API key.

This is a local development application, not a production deployment. Replace
the development JWT signing constant in `backend/core/auth/auth_handler.py` and
review authentication and CORS before exposing the service publicly.