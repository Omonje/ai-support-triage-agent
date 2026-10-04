# Tests

## Test plan
| What is tested | Where (seam) | How | Status |
|---|---|---|---|
| Classification logic (urgency/intent, confidence scoring) | Service layer, Claude API faked | unit | written, 9 tests passing (2026-10-04) |
| Escalation rule (two triggers: sensitive intent, low confidence) | Service layer | unit | written, 5 tests passing including threshold boundary (2026-10-04) |
| Retrieval (does it return the right KB article for a given message) | Service layer, real small fixed article set, no faking needed (deterministic local computation) | unit | written, 4 tests passing (2026-10-04) |
| Draft generation is grounded in retrieved KB content | Service layer, Claude API faked | unit | written, 5 tests passing, incl. refusing to draft with zero KB articles (2026-10-04) |
| Gmail gateway (read label, create draft, apply label) | Repository layer, real Gmail test account | integration | not started |
| monday.com gateway (create/update item, status transitions) | Repository layer, real monday.com Free account | integration | not started |
| Closed-loop detection (sent draft updates monday.com item) | Full path | integration | not started |
| Whole request path, message in to monday.com item out | Entry to repository, real test account, synthetic messages | integration | not started |
| Refused paths: malformed message, empty body, non-English (if out of scope), duplicate message ID reprocessed | Service + entry | unit | not started |
| Failure paths: Claude API down or slow, Gmail API rate-limited, monday.com API down | Service + repository, faked failures | unit | not started |

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
- Date:
- Unit tests:
- Integration tests:
- Deliberate breaks caught:
- Load test (shape of results and its limits): not applicable at demo scale, note in RUNBOOK.md instead

## CI
Has the CI file actually run? not set up yet.

## Test walkthrough video
Path:
