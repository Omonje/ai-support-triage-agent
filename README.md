# AI Support Triage Agent

A coded agent that classifies incoming support emails by urgency/intent,
drafts a knowledge-grounded reply for human approval, and escalates
anything sensitive instead of guessing. Built as an independent portfolio
piece, grounded in a real, live Upwork job spec (not built for that
client, see `DECISIONS.md`).

**Status:** complete. All 10 slices are done. See `PLAN.md` for scope and
design, `TESTS.md` for the test results (116 unit tests passing, 18 of 18
seeded messages processed in a real run), and `CASE-STUDY.md` for the
write-up. The LLM layer is swappable between Claude, Gemini and Groq
(`LLM_PROVIDER` in `.env`); the live run used Groq, see `DECISIONS.md` #6
and #7.

## What this is, honestly

- Real Gmail integration (one dedicated account, one label), real
  monday.com integration. Not mocks.
- The manufacturer and support team behind it are invented. See
  `PLAN.md`'s "Stand-ins and honest limits" section.
- Nothing is ever auto-sent. Every reply is a Gmail draft a human reviews.

## Install

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
copy .env.example .env
```

Then fill in `.env`:
- `LLM_PROVIDER` (`claude`, `gemini` or `groq`) and the matching key:
  `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` or `GROQ_API_KEY`
- `GMAIL_OAUTH_CLIENT_PATH` / Gmail OAuth: see `RUNBOOK.md` for the
  Google Cloud Console walkthrough
- `MONDAY_API_TOKEN` / `MONDAY_BOARD_ID`: from your monday.com account's
  personal API token page and the target board's id

## Run

```
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Health check: `GET /health`

## Test

```
.venv\Scripts\python.exe -m pytest -q
```

## Project layout

```
app/
  main.py          entry layer: FastAPI app, health check, startup config check
  config.py        loads and validates all settings, fails fast on bad config
  errors.py         two kinds of error: expected (TriageError) and bugs
  logging_setup.py  structured logging, never logs secrets or message content
  service/          classification, escalation rule, RAG retrieval, draft generation
  gateways/         Gmail gateway, monday.com gateway, Claude gateway
tests/
scripts/            the setup script that seeds synthetic test messages
```
