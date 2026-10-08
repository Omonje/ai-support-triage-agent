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
   - `SLACK_WEBHOOK_URL` (optional). If set, an escalation posts an
     immediate alert, each run posts one summary alert for any drafts
     created, and one summary alert for any messages that failed. If
     left blank, the pipeline runs exactly the same with no alerts.
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
1. `pytest -q` — full suite must pass (107 tests as of 2026-10-08).
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

## Error handling and how the team finds out

**How errors are handled in the code:**
- Every external call (Gmail, the LLM provider, monday.com, Slack) is
  wrapped in a `GatewayError` with a safe, readable message, never a
  raw stack trace or a leaked secret (`app/errors.py`).
- Config is checked once at startup and fails fast with a clear message
  if anything required is missing or invalid, before any message is
  touched (`app/config.py`).
- One message's failure never stops the batch. It's caught per-message
  in `process_new_messages`, recorded, and the rest of the batch keeps
  going.
- A failed message is deliberately not marked "Processed" in Gmail, so
  it's retried automatically on the next run, no one has to intervene
  for a transient blip.
- The LLM calls specifically retry 3 times with exponential backoff
  before giving up (`app/gateways/retry.py`), since that's where real
  transient failures (503s, rate limits) have actually happened in
  testing.

**How the team finds out:**
- If `SLACK_WEBHOOK_URL` is set: an escalation posts an alert
  immediately, and each run ends with up to two summary alerts, one
  for drafts ready and one listing every message that failed (skipped
  entirely if nothing failed). This is a real alert, not a human
  needing to notice anything.
- Every run also writes structured, timestamped JSON log lines to
  `pipeline.log` in the project root (via `app/logging_setup.py`), not
  just console output that's gone once the terminal closes. A warning
  is logged for every failed message and every failed Slack send; an
  info line logs the run's final processed/failed counts.
- This is still a portfolio demo run on demand, not a continuously
  monitored production service: there's no process-uptime monitoring,
  no log rotation on `pipeline.log`, and no alert if the script simply
  never gets run. If this were handed to a real support team, the
  things worth adding on top are:

| Number or check | Alert when | Who is told, and how |
|---|---|---|
| The scheduled run itself not firing | No run has completed in longer than the expected poll interval | Needs an external scheduler/uptime check (e.g. a cron health-check ping), not built here since this demo runs on demand, not on a schedule |
| LLM provider errors (quota/5xx) | Repeated `GATEWAY_ERROR` for the same provider across runs | Already alerted per-run via the Slack failure summary above; a real deployment on a paid LLM tier wouldn't hit the free-tier daily caps this demo hit twice (LOG.md) |
| monday.com item count vs. Gmail processed count | They disagree (a message was processed but never got a monday.com row, or vice versa) | Manual reconciliation for now; `scripts/check_monday_connection.py`'s pattern could be extended into a dedicated audit script |
| `pipeline.log` growth | File size becomes unmanageable | No rotation is built in; a real deployment would use a log aggregator (e.g. CloudWatch, Datadog) instead of a flat file |

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
