# Runbook

## How to run it
1. `python -m venv .venv` then activate it, `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and fill in:
   - `LLM_PROVIDER` (`claude`, `gemini`, or `groq`) and the matching API key.
     Groq (console.groq.com/keys) is the one actually used for the live
     demo, free tier, no card.
   - Gmail: `GMAIL_OAUTH_CLIENT_PATH` pointing at a Google Cloud OAuth
     client file (Desktop app type), `GMAIL_LABEL=Triage-Demo`.
   - monday.com: `MONDAY_API_TOKEN` (personal token from
     `https://<account>.monday.com/apps/manage/tokens`) and
     `MONDAY_BOARD_ID`.
3. `python -m scripts.check_gmail_connection` and
   `python -m scripts.check_monday_connection` to confirm both real
   connections work before touching the pipeline. First Gmail run opens
   a browser for OAuth consent and caches the token at
   `GMAIL_TOKEN_CACHE_PATH`.
4. `python -m scripts.seed_test_messages` once, to populate the demo
   inbox with synthetic support messages (idempotent to re-run, but
   re-running adds more messages rather than resetting).
5. `python -m scripts.run_pipeline` to process every new message under
   the label: classify, escalate-or-draft, write the monday.com item,
   mark it processed. Safe to re-run; already-processed messages are
   skipped and failed ones retry automatically.
6. `python -m scripts.check_sent_drafts` to close the loop: flips any
   monday.com item to "Sent" once its Gmail draft has actually been
   sent by a human.

In a real deployment, steps 5 and 6 would run on a schedule
(`INBOX_POLL_INTERVAL_SECONDS` / `SENT_CHECK_POLL_INTERVAL_SECONDS` in
`.env` already define the intended cadence), not by hand. For this
portfolio build they're run manually, which is the honest limit stated
in PLAN.md.

## Release steps
1. `pytest -q` — full suite must pass (95 tests as of 2026-10-08).
2. Run the two connectivity checks (step 3 above) against the real
   accounts.
3. Run `scripts.run_pipeline`, read its per-message output for any
   `[FAILED]` lines before considering the run complete.

## The way back
There's no deployed service to roll back, this runs on demand from a
local machine. If a bad change needs undoing: `git revert` the commit,
`pip install -r requirements.txt` again if a dependency changed, re-run
the release steps above. No external state needs manual undoing, since
the pipeline only ever creates Gmail drafts (never sends) and
monday.com items (never deletes), and failed messages are simply
retried on the next run rather than left half-applied.

## Smoke test (right after release, with a test user)
- [ ] `python -m scripts.check_gmail_connection` reports "Connected"
      with the expected unprocessed-message count.
- [ ] `python -m scripts.check_monday_connection` confirms the token
      and board ID still work.
- [ ] `python -m scripts.run_pipeline` against at least one real
      message produces either a drafted or escalated result with 0
      `[FAILED]` lines.
- [ ] `python -m scripts.check_sent_drafts` runs without error against
      whatever drafts currently exist.

## What is watched
This is a portfolio demo run on demand, not a monitored production
service, so there's no alerting pipeline. If this were handed to a real
support team, the things worth watching are:

| Number or check | Alert when | Who is told, and how |
|---|---|---|
| `[FAILED]` count in `run_pipeline` output | Any failures on a run | Whoever operates the script reads the console output directly; a real deployment would pipe this to a log aggregator and alert on a nonzero count |
| LLM provider errors (quota/5xx) | Repeated `GATEWAY_ERROR` for the same provider across runs | Same as above; a real deployment on a paid LLM tier wouldn't hit the free-tier daily caps this demo hit twice (LOG.md) |
| monday.com item count vs. Gmail processed count | They disagree (a message was processed but never got a monday.com row, or vice versa) | Manual reconciliation for now; `scripts/check_monday_connection.py`'s pattern could be extended into a dedicated audit script |

## First 48 hours
Not applicable in the usual sense, this isn't a live deployment with
real traffic. If it were stood up for a real team, the honest version
of this section would track: whether the confidence-escalation
threshold (0.6) needs tuning against real message volume, whether the
KB's 15 articles cover the actual range of questions coming in, and
whether the polling interval feels responsive enough in practice.

## Owner and support
Owner: Blessing Omonjeva (Obaline Systems). This is an independent
portfolio build, not a deployed client system, so there's no live
support line, questions about the build go through Upwork/the
portfolio listing this is attached to.

## Live walkthrough video
Path: <to be added after recording>
