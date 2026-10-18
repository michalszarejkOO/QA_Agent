---
type: llm
weight: 1
---

PASS only if all of the following hold:
- The response classifies MWA-9001 as backend, and states the concrete
  signal(s) it rested that decision on (the "[BE]"/"API" labels, the
  backend-shaped changed paths, and/or the api-only config block) — not a
  black-box verdict.
- It hands off to the `testing-api` skill and stops there, per
  routing-qa-tickets' own procedure — it does not also try to derive Jira/PR
  context, write test scenarios, or drive a browser itself (that's
  testing-api's and qa-tester's job, not routing-qa-tickets').
- It does not ask the user whether this is backend or frontend — the signals
  given are unambiguous and a clarifying question here would be an
  unnecessary round-trip.

FAIL if it guesses without citing a signal, asks an unnecessary clarifying
question, or attempts frontend-shaped testing (e.g. mentions a browser,
Playwright, or a web/mobile target).

This rubric only grades the classification and dispatch decision, not whether
the run actually completed. The prompt deliberately withholds the ticket's
full acceptance criteria and the PR's full diff (only a name-only file list is
given) — correctly noticing that gap, naming exactly what's missing, and
stopping there without fabricating a test run or a result is a PASS, not a
FAIL, as long as the classification and dispatch above were still done
correctly first.
