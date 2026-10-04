# Decisions

Record a decision only when it is hard to reverse, a later reader would ask "why?", and there was a real trade-off.

## Decision log
| # | Decision | Chosen | Instead of | Why | What we give up |
|---|---|---|---|---|---|
| 1 | Inbox integration | Real Gmail API, scoped to a dedicated label | A local SQLite mock inbox | A real API integration is a stronger, more demoable production-readiness signal than a mock, matches the "production-ready, realistic" bar for this round of portfolio builds | Added setup cost (Google Cloud OAuth client), and the demo depends on a real external API instead of a fully controlled local stand-in |
| 2 | Niche framing | Manufacturers | Generic / another already-covered niche | Zero existing portfolio coverage for this niche; gives classification categories real texture (order status, defect complaint, quote request, urgent delay) | None significant |
| 3 | LLM provider | Claude API | OpenAI or another provider | Consistent with an earlier build, reuses existing API familiarity | None significant |
| 4 | Audit log + approval queue tool | monday.com, new account (Free plan) | Airtable (rejected, overused across her other portfolio pieces), Notion (database model doesn't naturally fit a live status-driven queue) | Needed a client-visible tool, not a local file. monday.com's task/status model maps directly onto "classified -> draft ready for approval -> sent/escalated," which Airtable and Notion would have to bend to fit | None at this scale; would need a paid plan only if this became a real high-volume deployment |
| 4b | Correction (2026-10-xx) | — | — | The "confirmed Free plan" check on 2026-10-02 read an account that was actually mid-trial of a paid plan, not genuinely Free; the trial has since expired and hit a paywall. New account being created to get a real Free plan. Logged so this isn't mistaken for a stable fact later | — |
| 4c | monday.com has no real Free tier reachable through signup | Build on the Pro CRM trial, time-boxed, record a video and screenshots before it expires | Switching to ClickUp (genuine permanent free tier) | The new account (demo-account@example.com) auto-enrolled into the same Pro/CRM trial pattern as the first account, there is no plain Free path through monday's signup. Finishing on the trial is faster than a third account-creation cycle | The live board will stop being viewable/demoable once the trial ends and locks; the case study has to rely on the recorded video and screenshots captured during the trial window, not a live link |
| 5 | KB retrieval method | TF-IDF + cosine similarity (scikit-learn) | Learned embeddings (sentence-transformers / an embeddings API) | A 15-article fixed policy KB is exactly the case where keyword/term overlap is already a strong, explainable signal; embeddings would add a heavy dependency (torch) and, in practice, an unreliable download in this environment for no real gain at this scale | Won't catch pure paraphrase with zero shared vocabulary; acceptable for a demo-scale KB, would revisit if the KB grew large or became more free-form |

## Decisions I should be able to defend
For each: the question someone will ask, and my answer in my own words.

| Question | My answer |
|---|---|
| Why a real Gmail integration instead of mocking it like the other builds? | Gmail's API is free, well-documented, and scoping to a single label keeps it safe. A real integration is more credible proof than a mock, and "draft for approval" maps directly onto a real Gmail draft rather than an invented internal UI. |
| Whose Gmail account is this running against? | A dedicated account/label set up only for this demo, never my real inbox or any real client's, and every message in it is synthetic, written for this project. |
