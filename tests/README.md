# TrustFusion Accuracy Verification

Run from the repository root in PowerShell using the working local environment:

```powershell
.\.venv\Scripts\python.exe -B tests\test_trust_accuracy.py
$env:TRUSTFUSION_LIVE_TEST = "1"
.\.venv\Scripts\python.exe -B tests\test_trust_accuracy.py
```

The original `venv` points to a Python installation on another machine. The
`.venv` environment was created locally and installed from the backend requirements.
First use downloads all-MiniLM-L6-v2 and cross-encoder/nli-deberta-v3-small.

## Verification Scope

The factual AI, false Apollo date, vague-answer, and missing-evidence cases use
controlled article/model fixtures with REAL embeddings, FAISS, and NLI. They are
repeatable behavior checks, not claims about arbitrary provider accuracy.
The API test patches only model/article fetching and persistence; it exercises
the actual FastAPI route, pipeline, scoring, synthesis, and JSON contract.
The separate live gate fetches Wikipedia and DuckDuckGo-linked website articles
and verifies that relevant sources from both providers survive FAISS filtering.

Latest full run: **9 tests passed, no skips**. Exact output and per-model score
breakdowns are in [trust_accuracy_output.txt](trust_accuracy_output.txt).

| Controlled Case | Consensus | Verification | Similarity | Trust | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| AI definition and three applications | 1.0000 | 1.0000 | 1.0000 | 1.0000 | Green |
| Correct Apollo date, two models | 1.0000 | 1.0000 | 0.9484 | 0.9897 | Green |
| Wrong Apollo date | 1.0000 | 0.0000 | 0.8967 | 0.4900 | Red, factual cap |
| Vague answer | 0.3333 | 0.0000 | 0.2267 | 0.1787 | Red |

## Behavior Contract

- Live retrieval runs on every query, including the legacy `use_rag=false` flag.
- Relevant live evidence is retrieved before model generation. A bounded set of
  source excerpts, URLs, and the current UTC date is supplied to each model.
  The same request-local sources are then used for claim verification.
- This is retrieval-augmented generation, not training or fine-tuning hosted
  models. Fetching a page today does not establish that its contents are current.
  Models are instructed to abstain when evidence is missing, conflicting, or
  insufficiently current, and to ignore instructions embedded in source text.
- No shared local index or cached-document fallback participates in this path.
- Query cosine relevance must be at least 0.45, including claim-guided retrieval.
- Each claim is SUPPORTED, CONTRADICTED, or UNVERIFIED with source evidence.
- Verification is clamped `(supported - 0.5 * contradicted) / total`; no claims means zero.
- Trust is `0.4 * consensus + 0.4 * verification + 0.2 * similarity`.
- Contradictions or verification below 0.35 cap trust at 0.49.
- Green requires trust >= 0.80 and no contradictions; Amber starts at 0.50.
- Overall consensus averages the per-model cluster fractions over enabled models.
- `agreement_component` and `rag_component` remain compatibility aliases.
- `completeness_component` now reports verified claim coverage, not word count or
  a guarantee that every requested subquestion was answered.
- Final synthesis requires source support and support from more than half of all
  enabled models. It abstains rather than copying an unverified raw response.
- NLI and embedding thresholds are conservative heuristics, not a proof of truth.
  Unverified does not mean proven false; inspect the claim evidence and warnings.

## Build And Live Status

Frontend production build and changed-file ESLint pass. Full frontend lint has
an existing `react-hooks/set-state-in-effect` failure in the untouched App.jsx.
Desktop/mobile browser checks cover status colors, markdown tables, line breaks,
source links, and horizontal overflow.

Backend starts and `/health` returns `{"status":"ok"}`. Live AI retrieval found
Wikipedia Artificial intelligence plus IBM, Britannica, and Built In articles.
A separate three-provider live request returned HTTP 200, but llama-3.3-70b and
llama-3.1-8b returned provider HTTP 404. GPT OSS responded; independent majority
synthesis therefore abstained. Provider availability and MongoDB persistence
are not certified by the controlled scoring tests.

## Local Authentication

MongoDB was missing from this machine. A portable MongoDB 8.0.17 installation
now runs on 127.0.0.1:27017, with persistent data under Local AppData/TrustFusion.
It is a terminal process, not an automatically starting Windows service. To
restart it in PowerShell after closing that terminal:

```powershell
& "$env:LOCALAPPDATA\TrustFusion\mongodb\mongodb-win32-x86_64-windows-8.0.17\bin\mongod.exe" --dbpath "$env:LOCALAPPDATA\TrustFusion\mongodb-data" --bind_ip 127.0.0.1 --port 27017 --logpath "$env:LOCALAPPDATA\TrustFusion\mongodb-data\mongod.log" --logappend
```

Authentication uses bcrypt directly over the existing SHA-256 password digest,
preserving stored hash compatibility without the Passlib/bcrypt runtime crash.
Database connection failures return 503 with CORS headers. Login and registration
requests time out after ten seconds and display readable error messages.
Real MongoDB-backed registration/login, incorrect password, and duplicate account
checks passed; their generated test account was deleted immediately afterward.
Focused authentication regressions: `python -B tests/test_trust_accuracy.py AuthenticationTests`.

## Query Latency

The original cold request was recorded at 173.266 seconds; later warm requests
were around 7-8 seconds. A new live five-model Prime Minister query completed in
22.84 seconds, with every provider call below 0.5 seconds; remaining work was
local initialization, retrieval, and claim verification. These are observations,
not guaranteed response times.

- Provider calls have a wall-clock deadline using `settings.llm_timeout` (default 30 seconds).
- Article collection has an 18-second network-phase deadline and retains completed sources.
- The API pipeline returns a readable 504 after a 75-second deadline.
- The browser has an 85-second timeout, an elapsed counter, Cancel, and duplicate-request protection.
- Cached model weights load locally first; repeated NLI pairs are reused only within a query.
- Three Groq models returned 404 and Mistral returned 402 Payment Required in the
  live check. Only GPT OSS answered; majority-supported synthesis must abstain.

Six focused deadline, API, and real-NLI accuracy checks passed after these changes:
`python -B tests/test_trust_accuracy.py EvidenceAccuracyTests.test_1_factual_ai_query EvidenceAccuracyTests.test_2_false_date_is_red_and_excluded QueryLatencyTests PipelineAPITests`.