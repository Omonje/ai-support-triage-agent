# Log

Add a line every time something goes wrong. This feeds the hand-over document.

| Date | What happened | Cause | Fix |
|---|---|---|---|
| 2026-10-04 | Full test suite took 5561s (92 min) to run 23 tests that normally take under a second | An earlier `pip install sentence-transformers` (abandoned when we switched to scikit-learn for retrieval) was stuck in an infinite DNS-failure retry loop downloading torch in the background, starving CPU/network and slowing everything else sharing the machine | Stopped the stuck background task, confirmed sentence-transformers was never actually installed (`pip show` found nothing), re-ran the suite: 3.5s for 23 tests, back to normal |
| 2026-10-05 | First real run of `scripts/run_pipeline.py` against the 18 seeded messages failed on the first Claude API call | Anthropic account has no credits/billing set up: "Your credit balance is too low to access the Anthropic API" (400, invalid_request_error) | Not yet fixed, needs Blessing to add a payment method/credits at console.anthropic.com -> Plans & Billing. Error handling worked as designed: clean GatewayError, no crash, no partial/corrupt state (confirmed zero monday.com items or Gmail drafts were created before the failure) |

## Retro (at the end)
- What surprised us?
- What did the plan miss?
- Which step of the workflow skills should change?
