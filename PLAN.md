# Plan: AI Support Triage Agent

Source spec (real, live Upwork post used as the grounding requirement, not
a client relationship): "Add AI Triage and Reply Assistance to a Customer
Support Inbox," https://www.upwork.com/jobs/~022095518206375349773
(already hired by the original poster, so this build is fully independent,
built to the pattern, not for that client).

## Goal
Build a coded agent that classifies incoming support conversations by
urgency and intent, drafts a knowledge-grounded reply for human approval,
and auto-escalates anything sensitive, as a portfolio piece that proves
real software engineering, not a workflow-canvas build.

## Who uses it
A small manufacturer's support team (2-5 agents) sharing one inbox. For
this build: a dedicated Gmail account set up only for this demo, and a
monday.com board playing the role of the team's shared queue. No real
customer, client, or personal data anywhere, every message is synthetic.

## Done means (checks I can run)
- [x] Classification: a labeled test set of synthetic support messages is
      classified by urgency/intent with the accuracy stated honestly (no
      invented number). No formal percentage was computed across a
      labeled set, stated plainly as a real gap rather than inventing
      one: what IS verified is every real run's classification spot-
      checked against the obviously-correct category (every defect
      complaint across 20 real messages correctly triggered escalation,
      every routine message correctly drafted).
- [x] Draft replies: retrieval pulls from a mock knowledge base and the
      draft is grounded in it (can point to which article backed each
      draft). Confirmed on every real run via the "KB articles used"
      column on each monday.com item.
- [x] Escalation: messages matching defined sensitive/urgent criteria are
      flagged and routed to human review, never auto-sent. 5 real
      escalations across all runs (4 on 2026-10-08, 1 on 2026-10-12),
      zero AI drafts generated for any of them, architecturally
      guaranteed (decide_escalation short-circuits before drafting).
- [x] Human approval gate: no reply leaves the system without an explicit
      approval step. Every draft sits in Gmail's Drafts folder until a
      human opens and sends it; verified live 2026-10-12 (sent a real
      draft, watched the closed loop detect it).
- [x] Audit log: every classification, draft, and approval/rejection is
      logged with a reason. Confirmed on every real run via the
      monday.com board's status/intent/urgency/confidence/reasoning
      columns.
- [x] A mutation/deliberate-breakage check proves the test suite actually
      catches failures (same pattern used on an earlier MCP build).
      Done 2026-10-08: 5/5 deliberate breaks caught, see TESTS.md.

## In scope (version 1)
- Inbox/helpdesk integration (mocked inbox, realistic shape)
- Message classification: urgency + intent
- Knowledge-grounded draft responses (RAG against a small mock knowledge
  base)
- Routing and escalation rules
- Human-in-the-loop approval before anything is treated as "sent"
- Audit log of every decision

## Out of scope
- Live connection to a real paid client's inbox or CRM
- Auto-send without human approval (the original spec explicitly wants a
  human kept in the loop, not removed)
- Multi-language support
- Multi-tenant / per-client customization (this is a single-team demo)

## Limits
Deadline: none fixed, quality over speed. Budget: portfolio project, not
billed. Stack: Python (matches the career-pivot goal toward backend/AI
developer work). Must not change: no GHL, no real client data, always a
human approval step before anything goes out.

## Data it touches
| Data | Sensitive? | Where it lives |
|---|---|---|
| Synthetic support messages | No (fabricated, written for this project, sent by the setup script) | Dedicated Gmail account, under the Triage-Demo label only |
| Mock knowledge base articles | No | Local files, written for this project |
| Classification, drafts, escalation decisions | No | monday.com board (audit/approval queue), visible to a non-technical viewer |
| API credentials (Claude key, Gmail OAuth client, monday.com personal token) | Yes (secrets, not personal data) | Local `.env`, never committed, never logged |

## Design in one paragraph
A FastAPI entry layer polls the dedicated Gmail account on an interval for
new messages under the Triage-Demo label and passes each one, unchanged,
to the service layer. The service layer classifies urgency/intent and a
confidence score via the Claude API, checks the two escalation triggers
(sensitive intent, or confidence below threshold), and if neither fires,
retrieves the most relevant mock knowledge-base article and asks Claude to
draft a grounded reply. Two gateways sit below the service layer: a Gmail
gateway (read label, create a real draft, apply the Needs-Human label when
escalating) and a monday.com gateway (create or update the item mirroring
that message's state). A second, lighter poll cycle checks previously
tracked Gmail drafts, and when one has been sent or removed, updates its
monday.com item to "Sent," closing the loop without needing a webhook. A
shared config module loads all three API credentials at start and fails
fast with a clear message if any are missing.

## Risks (how could this fail?)
| Risk | What we do about it |
|---|---|
| Gmail polling delay means the demo isn't real-time | Document as a known limit in RUNBOOK.md, not claimed as instant in the case study |
| Claude misclassifies an ambiguous message | Confidence threshold routes anything uncertain to escalation instead of guessing; report the real accuracy from the test set, not an invented number |
| monday.com Free plan's 200 calls/day cap | Demo-scale usage stays far under it; documented as a real constraint if this were ever scaled to a live client |
| Gmail OAuth token expires | Refresh-token handling built in; re-auth steps written in RUNBOOK.md |
| A human edits a draft heavily before sending | Closed-loop detection only checks whether the draft ID still exists, not its content, so edits don't break tracking |
| Synthetic test messages accidentally resemble something identifiable | Reviewed before the setup script sends them; clearly fictional company and product names only |
| A message gets reprocessed on the next poll (already classified) | Corrected 2026-10-05: handled entirely by Gmail's own Processed label (slice 1's `list_new_message_ids` already excludes it), not a monday.com-side check |
| monday.com Pro trial expires mid-build or before the case study ships | Time-boxed: finish the monday.com-dependent slices and record the Loom + screenshots before the trial locks, do not depend on a live link afterward (see DECISIONS.md #4c) |

## Slices
| # | Title | Done when | Blocked by | Status |
|---|---|---|---|---|
| 1 | Gmail gateway | Can list test messages under the Triage-Demo label and track which are already processed | None | done, real connectivity confirmed 2026-10-05: OAuth consent completed, script output "Connected. Found 0 unprocessed message(s) under 'Triage-Demo'." (expected, no test messages yet) |
| 2 | Classification service | Classifies urgency/intent with a confidence score, tested against a labeled synthetic set, accuracy reported honestly | None (corrected 2026-10-04: does not need the Gmail gateway, only a message) | partly done: validation/clamping rules built and unit-tested (9 tests, fake gateway), real-accuracy-on-labeled-set check still needs a real ANTHROPIC_API_KEY, not run yet |
| 3 | Escalation rule | Both triggers (sensitive intent, low confidence) route correctly; unit tests cover both plus the pass-through case | 2 | done, 5 unit tests passing including the threshold boundary (2026-10-04) |
| 4 | KB + RAG retrieval | Given a message, retrieval returns the right mock KB article(s) | None | done, 4 unit tests passing, 15-article KB written (2026-10-04) |
| 5 | Draft generation | A real Gmail draft is created, grounded in the retrieved KB content | 1, 4 | done: draft-text generation (slice 4) and gateway.create_draft() (slice 1) both built and unit-tested; not yet wired into one end-to-end flow, that's slice 9's integration test (2026-10-05) |
| 6 | monday.com gateway | Items created/updated correctly reflecting each message's state | None | done, real connectivity confirmed: created real item 13204530514 on the board and updated its status, via `scripts/check_monday_connection.py` (2026-10-05) |
| 7 | Closed-loop sent-detection | Manually sending a test draft updates its monday.com item within one poll cycle | 1, 6 | done, fully verified real end-to-end 2026-10-08: manually sent 2 of the 14 real drafts from Gmail, re-ran `check_sent_drafts`, both correctly flipped to "Sent" on the live monday.com board, the other 12 correctly stayed "still pending". Found and fixed a second real bug along the way (LOG.md): sending a draft from inside Gmail's draft view doesn't make `drafts.get()` 404, it keeps succeeding and returns the now-sent message, so `draft_exists` now also checks the message's labels (`DRAFT` gone, `SENT` present) instead of relying on a 404 alone |
| 8 | Setup script | Running it populates the Gmail account with ~15-20 synthetic test messages from empty | 1 | done, run for real 2026-10-05: inserted 18 synthetic manufacturer messages (`scripts/seed_test_messages.py`), covering all 5 intents plus ambiguous/safety cases; re-verified via check_gmail_connection.py, "Found 18 unprocessed message(s)" |
| 9 | Full test suite | Unit + integration + deliberate-breakage checks all pass, numbers written down exactly | 1-8 | real run against all 18 seeded messages complete 2026-10-08 on Groq (openai/gpt-oss-120b) after Gemini's free tier proved too small (DECISIONS.md #7): confirmed via the real monday.com board, 4 escalated to human review + 14 drafted and grounded in KB articles = all 18, 0 unprocessed messages remain in Gmail. While verifying this, found and fixed a real bug in `list_items_with_status` (LOG.md 2026-10-08): monday's own status filter needs the column's internal numeric index, not the label text, so it was silently always returning empty, which is also why slice 7's "Checked 0 pending draft(s)" result had falsely looked like a pass. Unit suite: 94 tests passing. Deliberate-breakage checks still not run |
| 10 | Runbook + case study draft | RUNBOOK.md complete, Loom recorded, case study drafted with honest stand-ins/limits | 9 | done 2026-10-12: RUNBOOK.md and CASE-STUDY.md complete, walkthrough video recorded against two genuinely new test messages and confirmed successful from the real GitHub Actions logs (see TESTS.md). All 10 slices done |

## Stand-ins and honest limits
- The Gmail account and monday.com board are real, live integrations, not
  mocks, but the manufacturer and support team behind them are invented.
  Case study language says "a real API integration, built independently
  and inspired by a real documented need," never "built for a client."
- The knowledge base is a stand-in for a real support KB, 10-15 articles
  written for this project, not pulled from a real business.
- Polling, not a live webhook, is the honest limit on "instant." Stated
  plainly in RUNBOOK.md and the case study.
- Depends on a person behaving well in one place: a human must actually
  review and send (or not send) each draft. The system never auto-sends.

## Addendum (2026-10-08): Slack alerting
While preparing the case study, a real gap surfaced: the system had no
push notification at all, a human had to proactively check the
monday.com board or Gmail Drafts folder to notice anything, including
an escalated defect complaint. Added an optional Slack incoming
webhook (DECISIONS.md #8): one immediate alert per escalation, one
summary alert per run for routine drafts. Built test-first (10 new
tests: 3 for the gateway, 5 for the pipeline wiring, 2 for config),
105 total unit tests passing. Best-effort by design, a Slack outage
never blocks or undoes an escalation, draft, or monday.com write.

## Addendum (2026-10-08): pipeline-failure visibility
A follow-up question exposed a second gap: a whole-run failure (the
LLM provider down, which happened twice in testing) produced only
console output nobody but someone actively watching would see, and the
structured JSON logger already built (`app/logging_setup.py`) was only
wired into the unused FastAPI health-check stub, never into the script
that actually runs. Closed both (DECISIONS.md #9): a third Slack alert
type summarizing every failed message at the end of a run, and
`run_pipeline.py` now writes durable, timestamped log lines to
`pipeline.log`. 2 more tests, 107 total unit tests passing.

## Addendum (2026-10-08): deployment off the local machine
The user wanted this to run live somewhere, not only when she runs a
script on her laptop, so it genuinely demonstrates what a client
deployment would look like. Pushed to a private GitHub repo
(`github.com/Omonje/ai-support-triage-agent`) with two workflows
(DECISIONS.md #10): a scheduled run (every 30 min + manual dispatch)
that executes the real pipeline against the live accounts using
GitHub's encrypted repo secrets, and a test workflow that runs the
full suite on every push, closing the "CI not set up yet" line in
TESTS.md. Verified for real: a manual trigger authenticated to Gmail,
Groq, and monday.com entirely from GitHub's own cloud runners, no
connection to the local machine. One real constraint surfaced and
documented, not hidden: `gmail.modify` is a Restricted OAuth scope, so
the cached token needs re-consent roughly every 7 days while the app
stays in Testing publishing status (the only realistic option short of
an annual paid security audit); a startup failure now alerts via
Slack instead of silently going quiet.

## Addendum (2026-10-08): knowledge base moved to Supabase
Same motivation as the GitHub Actions move: a knowledge base that only
existed as a local JSON file undercut the "built like it's for a
client" story. Added `SupabaseKBRepo` (DECISIONS.md #11), same thin-
REST-gateway pattern as every other gateway, test-first (7 new tests),
migrated all 15 articles for real via a one-time script, verified by
reading them back from the live database. `SUPABASE_URL` and
`SUPABASE_SERVICE_KEY` are now required config. 116 total unit tests
passing. Confirmed with a real GitHub Actions run: clean startup,
0 failures, entirely in the cloud.

## Gate log
- Gate 1 approved: 2026-10-02
- Gate 2 approved:
- Gate 3 passed:
