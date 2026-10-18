---
type: llm
weight: 1
---

PASS only if all of the following hold:
- The response classifies ACME-201 as frontend/web, citing the concrete
  signal(s) (the "Web"/"UI" labels, the `.tsx`/`.scss` changed paths, and/or
  the surfaces-only config).
- It resolves the target to `https://app.acme.staging.example.com/` (the
  single surface's `appUrl`) itself, without asking the user to supply a URL.
- It dispatches to the `qa-tester` agent with that ticket and target, and
  stops there — it does not itself try to write test scenarios or drive a
  browser (that's qa-tester's own job).
- It does not ask the user whether this is backend or frontend, or web or
  mobile — the signals given are unambiguous.

FAIL if it guesses without citing a signal, asks an unnecessary clarifying
question, mentions Bruno/API-collection testing, or asks the user to supply
the app URL when the config already resolves it unambiguously.

This rubric only grades the classification and dispatch decision, not whether
qa-tester's own execution actually completed. The prompt deliberately
withholds the ticket's full acceptance criteria and the PR's full diff (only
a name-only file list is given) — correctly noticing that gap, naming exactly
what's missing, and stopping there without fabricating scenarios or results
is a PASS, not a FAIL, as long as the classification and dispatch above were
still done correctly first.
