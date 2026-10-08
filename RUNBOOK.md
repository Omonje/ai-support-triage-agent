# Runbook

## Where it actually runs
This isn't just a script on a laptop. It's deployed to GitHub Actions
at [github.com/Omonje/ai-support-triage-agent](https://github.com/Omonje/ai-support-triage-agent)
(private repo): `.github/workflows/run_pipeline.yml` runs the real
pipeline against the live Gmail, monday.com, and Groq accounts every
30 minutes, plus on manual trigger, using GitHub's encrypted repo
secrets, no `.env` file or local machine involved. A second workflow,
`tests.yml`, runs the full test suite on every push. Everything below
in "How to run it" is how to run it **locally**, for development or a
one-off manual check, separate from the deployed, scheduled copy.

## Weekly maintenance: Gmail re-consent
`gmail.modify` is a Restricted OAuth scope. While this app stays in
Testing publishing status (the realistic choice for a portfolio build,
production use needs an annual paid third-party security audit), the
cached refresh token Google issues expires roughly every 7 days. When
it does, the scheduled GitHub Actions run will fail at the Gmail-auth
step and (if `SLACK_WEBHOOK_URL` is set) post a Slack alert saying
startup failed. To fix it:
1. Locally: delete `gmail_token.json`, run
   `python -m scripts.check_gmail_connection` to go through the
   interactive consent flow again (opens a browser), which writes a
   fresh `gmail_token.json`.
2. `gh secret set GMAIL_TOKEN_JSON --repo Omonje/ai-support-triage-agent < gmail_token.json`
   to push the new token to GitHub.
3. Re-run the workflow (`gh workflow run run_pipeline.yml --repo Omonje/ai-support-triage-agent`)
   to confirm it's working again.

## How to run it (locally)
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

Steps 5 and 6 above describe running it by hand locally. The deployed
copy already runs steps 5 and 6 on its own schedule (every 30 minutes,
see "Where it actually runs"), closer to the cadence
`INBOX_POLL_INTERVAL_SECONDS` / `SENT_CHECK_POLL_INTERVAL_SECONDS` in
`.env.example` originally described as the intent, though not exactly
that interval (GitHub Actions' minimum practical granularity and free-
tier usage limits make 30 minutes the sensible cadence here, not 2 and
5 minutes).

## Release steps
1. `pytest -q` — full suite must pass (107 tests as of 2026-10-08).
   The same suite also runs automatically in CI on every push.
2. Run the two connectivity checks (step 3 above) against the real
   accounts, locally, if testing a change before pushing.
3. Push to `main`. The test workflow runs automatically; the pipeline
   workflow picks up the new code on its next scheduled run, or
   trigger it immediately with
   `gh workflow run run_pipeline.yml --repo Omonje/ai-support-triage-agent`.
4. Check the run's output (`gh run view --repo Omonje/ai-support-triage-agent --log`,
   or the Actions tab in the browser) for any `[FAILED]` lines before
   considering the release complete.

## The way back
`git revert` the commit on `main` and push. The next scheduled run (or
a manual `gh workflow run`) picks up the reverted code automatically,
nothing to redeploy by hand. No external state needs undoing either
way: the pipeline only ever creates Gmail drafts (never sends) and
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
| The scheduled run itself not firing | No run has completed in longer than ~30 minutes | GitHub itself emails repo admins when a scheduled workflow run fails, and the Actions tab shows run history directly; no separate uptime check is built on top of that |
| Gmail token expiring (Restricted-scope 7-day limit) | The scheduled run's Gmail-auth step fails | Now alerts via Slack immediately (the startup-failure alert added alongside this), instead of the workflow silently going quiet; see "Weekly maintenance" above for the fix |
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
