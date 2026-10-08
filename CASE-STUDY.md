# AI Support Triage Agent

Independent build, grounded in a real, live Upwork job post asking for
almost this exact system (already filled by its original poster, so
this is an independent build to the same real requirement, not client
work). Code, not a workflow canvas.

## The problem

A small manufacturer's support team sharing one inbox runs into the
same pattern as teams this size everywhere: every message gets read
and triaged by hand, no matter how routine. A question about tracking
and a report of a cracked, unsafe part land in the same queue and get
the same first response speed, whoever happens to open the inbox next.
That's a real risk two ways. Routine messages pile up and slow down
replies to customers who are just waiting on a tracking number. And a
safety-relevant complaint, like a defective part, can sit next to
twenty routine ones with nothing marking it as different until someone
actually reads it.

## What was built

A coded agent (Python, not a drag-and-drop workflow) that reads new
messages from a shared support inbox on its own, works out what each
one is actually about and how urgent it is, and makes one of two calls.
If the message is routine, it looks up the company's own policy
documents, writes a reply using only what those documents actually say,
and leaves it as a draft for a person to read and send, it never sends
anything on its own. If the message mentions a product defect, or the
system just isn't confident enough in its read, it skips drafting
entirely and routes it straight to a person instead, and posts an
immediate Slack alert so that doesn't sit unnoticed in a queue. Either
way, the decision and the reasoning behind it show up as a
plain-language row on a shared board anyone on the team can check
without touching any code, not buried in logs.

The system plugs into real Gmail and real monday.com accounts (not
local mocks), and it's built to swap the AI model behind it without
touching any of that decision logic, so it isn't locked to one AI
vendor. It's also deployed, not just runnable: it executes on its own
schedule from GitHub Actions against the live accounts, with its own
automated test suite running on every change, not a script someone
has to remember to run from a laptop.

## What happened when it actually ran

Built test-first: 107 automated tests, every piece of business logic
proven before being wired to a real account. Then run for real against
18 synthetic support messages covering order status, shipping delays,
quote requests, and defect complaints, through real Gmail and real
monday.com, no mocks.

The result: all 4 messages describing a product defect were correctly
pulled out and routed straight to a person, with zero AI-written
replies ever generated for them. The other 14 got a policy-grounded
draft reply sitting in Gmail, ready for a one-click review and send.
Two of those were sent manually during testing, and the system
correctly updated their status on the board within one check, closing
the loop without anyone touching it by hand.

Several real problems came up while proving this against live
accounts, not a lab setup: a free AI tier's daily request limit that
looked fine on paper but wasn't enough for a full run (fixed by making
the AI provider swappable, a second real adapter added without
touching any business logic), a quirk in how monday.com's own
filtering worked against its documented behavior, and Gmail not
actually marking a draft as gone the moment it's sent, the way the
first version assumed. Each was found, fixed, and covered by a new
test so it can't silently come back. A later review question, "how
does the team know when something needs their attention," also turned
up a real gap: nothing had been pushing a notification at all, closed
the same way, test-first, with a Slack alert for escalations, drafts,
and run failures alike, plus a durable log file for anyone checking
after the fact. Moving it off a laptop and onto a real schedule turned
up one more: Google classifies the Gmail permission this system needs
(read, label, and draft) as a Restricted scope, which caps how long an
unverified app's access lasts before it needs a quick manual renewal,
a real constraint of working with Gmail's API that's documented
plainly rather than glossed over, with an alert now in place so it's
never a silent failure. Nothing about this build was a clean,
first-try demo, and that's worth saying plainly rather than hiding.

What this isn't: a live deployment handling real customer data. The
manufacturer, its support team, and every message are invented for this
project, built to the shape of a real documented need rather than for
an actual client. Replies are drafted, read, and sent entirely by a
human, the agent never sends on its own.
