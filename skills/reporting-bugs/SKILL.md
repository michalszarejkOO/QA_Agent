---
name: reporting-bugs
description: Drafts a bug report — Title, Steps to reproduce, Expected, Actual — from an observed defect, whether found during manual or automated testing, surfaced in code review, or just described directly. Never files or posts it; produces the draft for a human to review and publish. Use when asked to report, write up, or draft a bug/defect.
when_to_use: "Trigger on: 'report this bug', 'write up this defect', 'draft a bug report', turning an observed failure (in a browser session, a log, a description) into a ready-to-file bug ticket."
---

# Reporting bugs

Turn an observed defect into a bug report someone can file as-is. This drafts the
report; it does not investigate the defect for you (pull evidence from wherever the
delegating task already gathered it — screenshots, network requests, console errors,
logs, a plain description) and it never files, posts, or comments the result anywhere.

## Format

Exactly four fields, one bug per block — no extra fields (no priority, no root cause,
no suggested fix) unless the request explicitly asks for those too:

```
Title:
Steps to reproduce:
Expected:
Actual:
```

- **Title**: specific enough to distinguish this bug from others in the same area.
  Name the concrete wrong behavior, not the general area — "Editing only the comment
  without changing the answer is silently discarded on Next," not "Bug in
  questionnaire form."
- **Steps to reproduce**: a numbered list, starting from a defined precondition,
  precise enough that someone unfamiliar with the investigation could follow it
  and hit the same result.
- **Expected**: what should happen, stated plainly — usually derivable from the
  ticket, the code's evident intent, or ordinary product behavior.
- **Actual**: what actually happens, with concrete evidence inline where you have
  it — an error message, a response body, "no request fires," a value that reverts
  after reload — never a vague "it doesn't work."

Multiple bugs in one request → one block per bug, same four fields each, in the
order found.

## Procedure

1. Identify what's actually wrong and what evidence supports it. If the defect was
   only described, not observed directly, say so in Actual rather than presenting
   secondhand claims as verified fact.
2. Invoke the `find-duplicates` skill against this defect before drafting. A likely
   duplicate found → surface it plainly instead of silently drafting a new report;
   only draft anyway if there's a distinct repro or new information worth adding, or
   the caller confirms it's wanted regardless. Nothing found, or only "possibly
   related" → continue to step 3, noting any related ticket(s) alongside the draft.
3. Write Title last if it helps — it's easiest to name precisely once Steps/Expected/
   Actual are settled.
4. Don't speculate about root cause or fix unless it was independently verified (e.g.
   read in the actual source, not guessed) — this format has no field for it. If you
   have a verified root cause and it's valuable context, one line is enough; don't
   turn the report into a code review.
5. Return the draft. Never call a Jira/issue-tracker write tool yourself — filing is
   the human's decision, not this skill's.
