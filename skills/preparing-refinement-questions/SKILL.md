---
name: preparing-refinement-questions
description: Generates the list of clarifying questions to raise in a refinement/grooming session from a Jira ticket's summary and description — surfaces ambiguity, missing acceptance criteria, uncovered edge cases, and unstated dependencies as direct questions. Use when asked to prepare refinement questions, get a ticket ready for grooming, or find what needs clarifying before a ticket is estimated or started.
when_to_use: "Trigger on: 'prepare refinement questions for X', 'what should we ask about this ticket', 'get this ready for grooming', reviewing a ticket before estimation or sprint planning to find what's unclear or missing."
---

# Preparing refinement questions

Produce the list of questions a QA/dev would raise about a ticket *before* work
starts — not a verdict on whether the ticket is "ready," and not a rewritten version
of the ticket. This reads one ticket and asks what needs answering; it does not
grade a whole backlog (that's `reviewing-backlog-quality`, which works from an
already-extracted epic/story list during business analysis, not a single ticket
picked up for dev/QA refinement).

## Sources

- The Jira ticket: summary, description, existing acceptance criteria, comments,
  linked issues. Fetch with the Atlassian MCP tools, or use what's already pasted in.
- A linked Figma design, if referenced — states/variants it shows that the ticket
  text doesn't mention are exactly the kind of gap this skill surfaces.

No ticket content available at all → ask for it rather than inventing questions
about nothing.

## What counts as a question worth asking

- **Ambiguous language** — "handle correctly," "as appropriate," "should work" with
  no stated rule. Turn it into "what should happen when...?"
- **Missing or incomplete acceptance criteria** — behavior implied by the summary but
  never stated as a testable rule.
- **Uncovered edge cases** — empty/error/loading states, permissions or roles,
  concurrent edits, localization, offline or slow network, boundary values — ask
  about the ones the ticket's own scope would plausibly touch, not every case in the
  abstract.
- **Unstated scope boundaries** — what's explicitly out of scope, if the ticket
  doesn't say.
- **Dependencies** — other tickets, teams, services, or feature flags the ticket
  assumes without naming.
- **Missing non-functional angles** — accessibility, analytics/tracking, security,
  performance — only where the feature's nature makes them plausible, not as a
  boilerplate checklist.

Don't ask about something the ticket already answers clearly, and don't propose new
scope ("you should also build X") — this surfaces what's missing or unclear in what's
already described, phrased as a question, not a design suggestion.

## Procedure

1. Read the ticket's summary, description, and existing acceptance criteria (and the
   Figma design, if linked).
2. List every gap using the categories above, one pass per category rather than one
   ticket-wide skim — it's easy to miss a category by reading straight through.
3. Turn each gap into a direct, answerable question — not a comment or observation.
   "What should the comment field show if the answer changes but the comment doesn't
   get resubmitted?" not "the comment-saving logic seems unclear."
4. Group the output under short category headers only where it aids scanning; skip
   a category with no questions rather than forcing one in.
5. Return the list. If the ticket is unusually complete and few or no questions
   arise, say that plainly rather than inventing filler questions to seem thorough.

## Output

A Markdown list of questions grouped under short headers (e.g. `### Acceptance
criteria`, `### Edge cases`, `### Dependencies`), ready to paste into the ticket or a
refinement session doc. No verdict, no priority ranking, no rewritten ticket text.
