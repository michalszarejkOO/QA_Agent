---
name: find-duplicates
description: Searches Jira for existing bugs or tasks that may already cover a newly observed defect or work item, before it gets filed as new — returns ranked candidate matches with reasoning, or confirms none found. Use when asked to check for duplicate tickets, search the backlog for something similar, or as the automatic first step before drafting a new bug report. Never files, links, or comments on anything itself.
when_to_use: "Trigger on: 'check for duplicates', 'has this been reported before', 'search the backlog for X', 'is there already a ticket for this', manually browsing the backlog for overlap with a described issue, and automatically as the first step of reporting-bugs before a new bug report is drafted."
---

# Find duplicates

Check whether a defect or task someone is about to file already exists in Jira,
before it gets filed as new. This searches and judges; it never files, links,
comments, or transitions a ticket — the decision to file anyway, link as duplicate,
or skip rests with the human or the calling skill.

## Sources

- The observed defect or task: whatever description is available (title, steps,
  error text, affected component). No description at all → ask for one rather than
  searching on nothing.
- Jira, via the Atlassian MCP tools.

## Procedure

1. **Resolve the connector.** Confirm which Jira connector currently reaches the
   target site with `getAccessibleAtlassianResources` before trusting any cached
   connector-to-site mapping (e.g. a `reference_atlassian_connectors`-style memory
   note) — this mapping has been observed to drift between sessions.
2. **Build a compact fingerprint**, not the raw text: the concrete wrong behavior,
   the affected component/area, and any distinctive error message or identifier.
   Dumping the full description into a text search buries the match under noise.
3. **Run several JQL searches**, not one exact-phrase guess — vary the terms (e.g.
   the component name alone, the error string alone, a key noun phrase) and scope to
   the relevant project. Default to excluding closed/won't-fix issues unless asked to
   include them; widen to closed issues if the open search returns nothing.
4. **Judge each candidate against the new item**, not just its keyword overlap —
   read the candidate's summary/description and compare the actual behavior
   described, not only whether words match. Classify each as:
   - **Likely duplicate** — same underlying behavior, same area, same trigger.
   - **Possibly related** — same area or symptom but not clearly the same root cause.
   - Anything else found by the search but not meeting either bar → drop it, don't
     list it just because it matched a keyword.
5. **Report plainly.** If nothing clears either bar, say so — don't force a
   "possibly related" pick to seem thorough.

## Output

Report as markdown tables, grouped by classification — never a flat list of
paragraphs, which is hard to scan once there are more than a couple of candidates:

- One table per classification (`Likely duplicate`, `Possibly related`), each
  followed by a one-line recommended action where useful (e.g. "link as duplicate
  and close the older one").
- Table columns: the ticket keys as linked references (`[KEY](url)`), then a short
  "what overlaps" column carrying the one-line reasoning tied to the specific
  overlapping behavior — not "keywords matched."
- When the scan spans multiple areas/issue types (e.g. Bugs vs Stories vs Tasks),
  split each classification's table by area instead of one giant mixed table.
- Close with a short "checked and cleared" section — plain bullets are fine here,
  no table needed — naming what was ruled out and why, so it reads as thorough
  rather than incomplete.
- If none found, state that clearly instead of an empty table.

Never call a Jira write tool (create, comment, link, transition) — this skill only
searches and reports.

## Offering to save the report

After delivering the report as a standalone request (not the automatic pre-check
before `reporting-bugs` — skip this offer there, it's just an internal gate), ask
the user whether they'd like it saved somewhere, e.g. via AskUserQuestion:

- **Published to Confluence** — if chosen, ask for the target page/space link
  before publishing.
- **Saved as a PDF**.
- Or neither — the in-chat report is enough.

Only act once the user picks; don't publish or export unprompted.

## Using this before filing a bug

When invoked ahead of `reporting-bugs`: run this first against the defect just
identified, before Title/Steps/Expected/Actual are drafted. A likely duplicate found
→ surface it plainly instead of silently drafting a new report; only draft the report
too if the caller confirms it's wanted anyway (e.g. a distinct repro or new
information). No duplicate found, or only "possibly related" → proceed to draft as
normal, noting the related ticket(s) if any were found.
