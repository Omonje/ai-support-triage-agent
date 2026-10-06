# Log

Add a line every time something goes wrong. This feeds the hand-over document.

| Date | What happened | Cause | Fix |
|---|---|---|---|
| 2026-10-04 | Full test suite took 5561s (92 min) to run 23 tests that normally take under a second | An earlier `pip install sentence-transformers` (abandoned when we switched to scikit-learn for retrieval) was stuck in an infinite DNS-failure retry loop downloading torch in the background, starving CPU/network and slowing everything else sharing the machine | Stopped the stuck background task, confirmed sentence-transformers was never actually installed (`pip show` found nothing), re-ran the suite: 3.5s for 23 tests, back to normal |
| 2026-10-05 | First real run of `scripts/run_pipeline.py` against the 18 seeded messages failed on the first Claude API call | Anthropic account has no credits/billing set up: "Your credit balance is too low to access the Anthropic API" (400, invalid_request_error) | Fixed 2026-10-06 by making the LLM provider swappable (DECISIONS.md #6) and switching to Gemini's free tier instead of waiting on payment |
| 2026-10-06 | First real run with Gemini failed with `503 UNAVAILABLE: This model is currently experiencing high demand` | Transient Gemini capacity issue, not a code or auth problem (the API key itself worked) | Exposed a real gap: retry-on-transient-failure was never actually built despite being in the design. Added `app/gateways/retry.py` (exponential backoff, 3 attempts) and wired it into both LLM gateways. While doing this, found the new failure-path tests were sleeping for real (no injected fake sleep), making the suite 15s instead of ~2s; fixed by making `sleep` an injectable constructor param on both gateways and passing a no-op in tests |

## Retro (at the end)
- What surprised us?
- What did the plan miss?
- Which step of the workflow skills should change?
