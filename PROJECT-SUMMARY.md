# AI Support Triage Agent — Plain-English Project Summary

Written 2026-10-06 so this build can be explained to someone else without
needing to read the code. See `PLAN.md`, `DECISIONS.md`, `TESTS.md`, and
`LOG.md` for the full technical record this summary is drawn from.

## What it is, in one breath

A coded software agent (Python, not an n8n workflow) that reads incoming
manufacturer support emails on its own, figures out what each one is
about and how urgent it is, drafts a suggested reply grounded in real
company policy documents, and routes anything risky straight to a human
instead of guessing. Every message's status is tracked on a visible
board a non-technical manager could read without touching any code.

## Why this one, and why it's grounded in something real

This is build #1 on a reprioritized list of 12 portfolio pieces, picked
first for two reasons: AI agent integration is Upwork's fastest-growing
job category, and it's real code, proof the builder is more than someone
who drags boxes around in a no-code tool.

It isn't invented from nothing. It's grounded in a real, live Upwork job
posting that asked for almost exactly this: classify support messages,
draft replies, escalate sensitive ones. The system was never built *for*
that client, their real inbox or data was never touched, but their real,
detailed request became the spec, so the result solves an actual
documented business problem instead of a made-up scenario.

## How it works, start to finish

1. **Scoped by one label.** A dedicated Gmail label ("Triage-Demo") marks
   which emails the agent is allowed to touch. Nothing else in the
   account is ever read or changed.
2. **Classify.** Each new message is read by an AI model and sorted into
   one of five categories (order status, defect complaint, quote
   request, shipping delay, other), with an urgency level and a
   confidence score for how sure the system is.
3. **Decide: human or draft.** Two things force a message straight to a
   human, no auto-draft at all: the AI wasn't confident enough, or the
   message is a product defect complaint (which could be a safety or
   liability issue, never left to an AI's judgment alone).
4. **Ground the reply in real policy.** For everything else, the system
   searches a small knowledge base of company policy articles for the
   most relevant one, then asks the AI to write a reply using *only*
   that policy content, explicitly told never to invent a price, date,
   or promise that isn't actually in the policy doc.
5. **Draft, never send.** That reply becomes a real Gmail draft sitting
   in the Drafts folder. The system never sends anything itself, a
   person has to read it and hit send themselves.
6. **Visible audit trail.** Every message, whatever happened to it, shows
   up as a row on a monday.com board: what it was, how it was
   classified, how confident the AI was, which policy doc it used, and
   its current status. No developer tools needed to see it.
7. **Closes its own loop.** Once a human actually sends the drafted
   reply from Gmail, a second check notices the draft is gone and
   automatically flips that row to "Sent" on the board, nobody has to
   update records by hand.

## What makes this more than "a demo that works once"

- **Built test-first.** Every piece of logic was written as a failing
  test first, then the smallest code to make it pass. 83 automated
  tests currently, all passing in about 2.5 seconds.
- **Real connections, isolated.** Every external service (Gmail, the AI
  model, monday.com) sits behind its own small adapter, so the core
  business logic can be tested instantly with stand-ins, while a
  separate, smaller set of tests confirm the real connections actually
  work against the live accounts.
- **Every hard-to-reverse decision is written down**, with the reasoning
  and what was given up, not just left implicit in the code.
- **Failures are logged honestly**, what broke, why, how it got fixed,
  not smoothed over or hidden.
- **Explicit about its own limits.** The system is clear about what's a
  stand-in (the fictional manufacturer, the synthetic test emails) and
  what's real (the actual Gmail and monday.com integrations), so the
  eventual case study never overclaims.

## Real obstacles hit, and how they were handled

These are worth mentioning, they show the build surviving contact with
real-world conditions, not a clean lab demo:

1. A stuck background software install silently made the test suite take
   92 minutes instead of 2 seconds. Found the actual cause (a hung
   download retrying forever), killed it, confirmed nothing else broke.
2. Google's own test-mode restrictions initially blocked login to the
   Gmail account until it was explicitly added as an approved tester.
3. monday.com's "free" plan turned out to be a disguised paid trial,
   twice, on two different accounts. Decision: accept the time-boxed
   trial, and capture video and screenshots of the working system before
   it expires, rather than depend on a link that will eventually break.
4. The paid AI provider (Claude) got blocked by a billing wall mid-build
   with no budget to pay for it. Rather than stall, the AI layer was
   re-architected to be swappable between providers, the live demo
   switched to Google's free Gemini model, with zero changes to any
   business logic, only the AI "adapter" swapped. That swappability is
   itself a selling point: the system isn't locked to one AI vendor.
5. Even the free tier had real, undocumented-until-hit limits, a newer
   AI model allowed only 20 free requests a day for new accounts, an
   older, more generous model wasn't available to new accounts at all.
   Solved by pinning to a confirmed-working model and simply waiting out
   the daily reset rather than guessing further.
6. Discovered that one failed message anywhere in a batch was taking
   down the entire run. Fixed so a single bad message gets skipped (and
   automatically retried on the next run) instead of losing everything.

## Where things stand (2026-10-06)

Every individual piece is built, tested, and confirmed working against
the real live accounts (Gmail and monday.com both verified). What's left
is the full real run against all 18 test messages, currently waiting on
the free AI tier's daily quota to reset. After that: the real run itself,
a recorded walkthrough video, screenshots of the monday.com board, and
the final written case study.
