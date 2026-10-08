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
| Closed-loop, real connectivity | Full path, real accounts | integration | fully passed 2026-10-08: 2 of the 14 real drafts were manually sent from Gmail, `check_sent_drafts` correctly flipped both to "Sent" on the live monday.com board and correctly left the other 12 "still pending". Two real bugs were found and fixed getting here (both in LOG.md): monday's status filter needing an index not label text, and `draft_exists` wrongly trusting a 404 that Gmail never actually returns after a draft is sent from its own draft view |
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

Run 2026-10-08. Each break was applied by monkeypatching the broken
behavior into the test's own namespace in memory and calling the real
existing test functions directly, rather than editing the real source
files (the auto-permission system correctly refused direct edits that
weaken escalation/scope-filter logic, even temporarily; monkeypatching
proves the same thing without ever writing broken logic into a real
file on disk). Script kept outside the repo, in the session scratchpad.

| Break | Caught by | Caught? |
|---|---|---|
| Force escalation trigger to never fire | `test_sensitive_intent_escalates_even_with_high_confidence`, `test_low_confidence_escalates_even_with_non_sensitive_intent` | yes, both |
| Force confidence score to always read 100% | `test_low_confidence_escalates_even_with_non_sensitive_intent`, `test_confidence_just_below_threshold_escalates` | yes, both |
| Skip the duplicate-message check | `test_list_new_message_ids_queries_label_and_excludes_processed` | yes |
| Remove the Gmail label scope filter | `test_list_new_message_ids_queries_label_and_excludes_processed` | yes |
| Corrupt the KB retrieval so it returns an unrelated article | `test_returns_most_relevant_article_for_a_defect_message`, `test_returns_most_relevant_article_for_a_shipping_message` | yes, both |

Full suite re-run clean afterward (94 passed), confirming the breaks were fully reverted (in-memory only, no source file was ever changed).

## Results (exact numbers, with the date)
- Date: 2026-10-08
- Unit tests: 95 passing (full suite, `pytest -q`), runs in ~2s
- Integration tests: Gmail connectivity, monday.com connectivity, closed-loop sent-detection (14 pending drafts found and correctly checked), and the full pipeline real run (18/18 messages processed: 14 drafted, 4 escalated, 0 failures) all passed against live accounts
- Deliberate breaks caught: 5/5 (see table above)
- Load test (shape of results and its limits): not applicable at demo scale, note in RUNBOOK.md instead

## CI
Has the CI file actually run? not set up yet.

## Test walkthrough video
Path:
