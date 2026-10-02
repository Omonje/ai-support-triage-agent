# Glossary

One line per term, in the words the project uses. No implementation details. Add a term the moment it is settled.

| Term | Meaning | Do not call it |
|---|---|---|
| Triage-Demo label | The single Gmail label the agent reads and acts on. Nothing outside this label is ever touched. | "the inbox" (too broad, implies whole-account access) |
| Needs-Human label | Gmail label applied to a message when it is escalated, no draft is created for these. | "flagged" (too vague) |
| Escalation | A message routed straight to a human, no draft generated, because it tripped a trigger. | "rejected" (it is not rejected, just not auto-drafted) |
| Escalation trigger | One of two conditions that force escalation: a sensitive-intent classification, or classification confidence below the set threshold. | "error" (this is expected behavior, not a failure) |
| Draft-for-approval | A real Gmail draft the agent creates in the Drafts folder. A human reviews and sends it manually, the agent never sends anything itself. | "auto-reply" (nothing is sent automatically) |
| Audit/approval queue | The monday.com board that mirrors every message's state (classified, draft ready, escalated, sent) as an item a non-technical viewer can read. | "the log" (it is visible by design, not a developer-only log) |
| Closed-loop detection | The polling check that notices a tracked Gmail draft has been sent or removed, and updates its monday.com item to reflect that. | "webhook" (this is polling, not a push notification) |
| Setup script | The script that sends ~15-20 synthetic test emails into the dedicated Gmail account, used to populate or reset the demo. | "seed data" in any client-facing material (fine internally) |
