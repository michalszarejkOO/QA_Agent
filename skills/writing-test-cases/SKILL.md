---
name: writing-test-cases
description: Writes manual test cases from a Jira ticket's acceptance criteria, a PR diff, or a described feature. Defaults to a plain four-field table (Title, Preconditions, Steps to reproduce, Expected result) for review or hand-off — this is not execution, it does not open a browser. When explicitly asked to publish/create a Confluence page for a Jira ticket, switches to a Figma-grounded Confluence mode instead: a trackable, executable granular Smoke/Regression suite plus a condensed regression layer on the same page. Use when asked to write test cases, draft a test plan, prepare test scenarios, turn a Jira ticket into a Confluence QA page, or condense/merge an existing granular suite into fewer realistic regression cases.
when_to_use: "Plain-table trigger: 'write test cases for X', 'prepare a test plan', 'draft test scenarios', turning acceptance criteria into documented test cases, listing what should be tested before or independent of actually running the tests. Confluence-mode trigger: 'create a Confluence page with test cases for MWA-123', 'publish test cases for this ticket to Confluence', 'QA this story on Confluence', or a request to condense/merge/combine an existing granular test-case page into realistic regression journeys."
---

# Writing test cases

Produce test cases from a ticket, a PR diff, or a described feature — the document a
QA engineer writes *before* or *independent of* actually running anything. This is not
execution: it does not open a browser, does not produce a pass/fail verdict, and does
not touch code. Executing derived scenarios live against a running app is the
`qa-tester` subagent's job, not this skill's. Writing automated Playwright test code is
`writing-playwright-e2e-tests` / `e2e-engineer`, not this skill.

This skill has two modes that produce genuinely different artifacts — pick one
deliberately, don't blend them:

- **Plain table** (default) — a lightweight, four-field review document. No Jira/Figma
  fetching is required (though it's used when already provided), nothing gets
  published anywhere, and the output is just a Markdown table returned inline. This is
  what a bare "write test cases for X" means, and what `qa-tester` itself calls
  internally to turn gathered context into scenarios before touching Playwright.
- **Confluence page** — only when the request explicitly asks to create, publish, or
  update a Confluence page (or to condense an existing one into a regression layer).
  This mode fetches the Jira ticket and the linked Figma design itself, plans coverage
  deliberately, writes a full tagged Smoke/Regression suite, condenses it into a
  second realistic-journey layer, and creates the trackable page — see **Confluence
  mode** below.

Don't infer Confluence mode from the mere presence of a Jira ticket — plenty of
"write test cases for MWA-123" requests just want the table back in the response.

## Sources

Same sources of truth as manual QA execution, used the same way:

- **Jira ticket** — acceptance criteria and description are the primary source of
  what "correct" means. Fetch with the Atlassian MCP tools, or use what's already
  pasted into the request.
- **PR diff**, if referenced — read it for edge cases the ticket doesn't spell out:
  new validation, new error states, changed conditionals. A diff that doesn't touch
  what the ticket describes is a mismatch worth flagging, not something to test
  around silently.
- **Figma design**, if linked — adds states/variants (empty, error, loading) worth
  their own test case even when the ticket doesn't mention them. In Confluence mode
  this is required, not optional — see Step B.

Missing all three (no ticket, no diff, no feature description) → ask what to write
test cases for rather than inventing scope.

---

## Mode 1: Plain table

### Format

Exactly four fields per test case — no priority, no coverage matrix, no cross-linking
between test cases. Output as a Markdown table with these columns, one row per test
case:

| Title | Preconditions | Steps to reproduce | Expected result |
| --- | --- | --- | --- |

- **Title**: `TC-XX: <short, specific description of what this test case walks>` —
  numbered sequentially (`TC-01`, `TC-02`, ...) in the order the ticket/diff presents
  them.
- **Preconditions**: the starting state required before step 1 — app/account state,
  data that must exist, language/locale, feature flags. If there are none, write
  "None."
- **Steps to reproduce**: a numbered list of concrete actions, one per line, ordered
  and specific enough that someone unfamiliar with the ticket could execute them
  (tap X, enter Y, select Z) — not vague verbs like "test the feature."
- **Expected result**: a numbered list matching the steps 1:1 — what should be
  observably true after each step, not just at the end. Every step that changes
  visible state gets its own expected-result line.

### Procedure

1. Pull acceptance criteria (or the feature description) and the PR diff if given.
2. Turn each acceptance criterion into one test case. Add test cases for edge cases
   the diff or design surfaces (new validation, error states, empty/loading states)
   even if the ticket doesn't spell them out — but don't invent scope neither the
   ticket nor the diff supports.
3. For each test case, write concrete steps and a matching expected result per step —
   not a single expected result covering the whole flow, unless the flow is a single
   action.
4. Number test cases sequentially and keep step/expected-result numbering aligned
   within each row.
5. Return the table. If a source (ticket, diff, or design) was unavailable, say so
   explicitly rather than silently working from less context.

### Output

A single Markdown table, ready to paste into Jira, Confluence, or a test-management
tool — nothing else added (no priority column, no "covers" column, no test-case
cross-references) unless the request explicitly asks for those too.

---

## Mode 2: Confluence page

Only when the request explicitly asks to create, publish, or update a Confluence page
(or to condense an existing one into a regression layer) — see "Don't infer Confluence
mode..." above. Load
[references/confluence-mode.md](./references/confluence-mode.md) and follow it
exactly: it owns fetching the ticket and design, planning coverage, writing the
granular suite, condensing it into a regression layer, and creating the page.
