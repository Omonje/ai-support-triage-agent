# Tests

## Test plan
| What is tested | Where (seam) | How | Status |
|---|---|---|---|
| Classification logic (urgency/intent, confidence scoring) | Service layer, Claude API faked | unit | written, 9 tests passing (2026-10-04) |
| Escalation rule (two triggers: sensitive intent, low confidence) | Service layer | unit | written, 5 tests passing including threshold boundary (2026-10-04) |
| Retrieval (does it return the right KB article for a given message) | Service layer, real small fixed article set, no faking needed (deterministic local computation) | unit | written, 4 tests passing (2026-10-04) |
| Draft generation is grounded in retrieved KB content | Service layer, Claude API faked | unit | written, 5 tests passing, incl. refusing to draft with zero KB articles (2026-10-04) |
| Gmail gateway (read label, create draft, apply label) | Repository layer, fake Gmail service | unit | written, 13 tests passing (2026-10-05) |
| Gmail gateway, real connectivity | Repository layer, real Gmail account | integration | passed 2026-10-05: OAuth consent completed (after adding the demo Gmail account as a test user), script output exactly: "Connected. Found 0 unprocessed message(s) under 'Triage-Demo'." (expected, no test messages sent yet) |
| monday.com gateway (create/update item, status transitions) | Repository layer, fake HTTP post | unit | written, 6 tests passing (2026-10-05) |
| monday.com gateway, real connectivity | Repository layer, real monday.com account | integration | passed 2026-10-05: created real item 13204530514 on board 18433915127, updated its status to "Sent", both confirmed by the script's own output |
| Closed-loop detection (sent draft updates monday.com item) | Service layer, both gateways faked | unit | written, 4 tests passing (2026-10-06) |
| monday.com list_items_with_status | Repository layer, fake HTTP post | unit | written, 3 tests passing (2026-10-06) |
| Gmail draft_exists (404 vs other errors) | Repository layer, fake Gmail service + real HttpError | unit | written, 4 tests passing (2026-10-06) |
| Closed-loop, real connectivity | Full path, real accounts | integration | passed 2026-10-08 against the live board with real pending drafts: "Checked 14 pending draft(s)", every one correctly reported "still pending". (The 2026-10-06 "Checked 0 pending draft(s)" result had looked like a pass but was actually a bug, see below and LOG.md: the status filter always returned empty.) Manually sending one test draft and re-checking it flips to "Sent" is the one remaining manual step |
| Whole request path, message in to monday.com item out | Entry to repository, real test account, synthetic messages | integration | passed 2026-10-08: all 18 seeded messages processed, confirmed via the real monday.com board (14 "Draft Ready for Approval" + 4 "Escalated - Needs Human") and 0 unprocessed messages left in Gmail |
| monday.com list_items_with_status filters correctly by status when the board has items in more than one status | Repository layer, fake HTTP post | unit | written, 2026-10-08, regression test for the bug below |
| Refused paths: malformed message, empty body, non-English (if out of scope), duplicate message ID reprocessed | Service + entry | unit | not started |
| Failure paths: Claude API down or slow, Gmail API rate-limited, monday.com API down | Service + repository, faked failures | unit | not started |
| Pipeline (message in -> classify/escalate/draft -> monday item -> marked processed) | Service layer, all three gateways faked | unit | written, 7 tests passing (2026-10-05/06), includes one-message-fails-rest-continue and failed-message-not-marked-processed |
| Retry-with-backoff on a transient LLM API failure | `app/gateways/retry.py` | unit | written, 4 tests passing, confirmed real: caught an actual Gemini 503 in production use 2026-10-06 that prompted building this | |
| Groq gateway (classify/draft against the shared interface) | Repository layer, fake Groq client | unit | written, 9 tests passing (2026-10-08), mirrors test_gemini_gateway.py |
| Whole pipeline, real run against all 18 seeded messages, real Gemini + Gmail + monday.com | Full path | integration | Gemini attempted twice (2026-10-06, 2026-10-08), blocked both times by the free tier's 20/day cap (see LOG.md and DECISIONS.md #7); completed 2026-10-08 after switching to Groq (openai/gpt-oss-120b), all 18 messages processed with 0 failures |

## Deliberate-breakage check
Break the code on purpose in these ways. Every break must make a test fail.
| Break | Caught by | Caught? |
|---|---|---|
| Force escalation trigger to never fire | Escalation rule unit test | not run yet |
| Force confidence score to always read 100% | Low-confidence escalation test | not run yet |
| Skip the duplicate-message check | Reprocessing test | not run yet |
| Remove the Gmail label scope filter | Scope/label test | not run yet |
| Corrupt the KB retrieval so it returns an unrelated article | Grounding test | not run yet |

## Results (exact numbers, with the date)
- Date: 2026-10-08
- Unit tests: 94 passing (full suite, `pytest -q`), runs in ~2.3s
- Integration tests: Gmail connectivity, monday.com connectivity, closed-loop sent-detection (14 pending drafts found and correctly checked), and the full pipeline real run (18/18 messages processed: 14 drafted, 4 escalated, 0 failures) all passed against live accounts
- Deliberate breaks caught: not run yet
- Load test (shape of results and its limits): not applicable at demo scale, note in RUNBOOK.md instead

## CI
Has the CI file actually run? not set up yet.

## Test walkthrough video
Path:
