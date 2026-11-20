---
name: writing-jira-comments
description: Drafts the QA comment for a Jira ticket after testing, in the product's own format when its project skill has a "Jira QA comment" section, otherwise in a default template - for an API ticket "QA result" with the endpoint, request and response of the happy path, for a UI ticket "Checked with status" with a list of what was checked, or only the problems when it failed. Posting follows the user's postJiraComment preference (auto, ask or never). Used by qa-tester, testing-api and retesting-tickets, and on request.
when_to_use: "Trigger on: 'napisz komentarz do jiry', 'draft the QA comment for IP-123', 'przygotuj komentarz z testów', the comment step of qa-tester or testing-api ticket mode. Do NOT trigger for bug reports (reporting-bugs) or for posting a ready comment."
---

# Writing the Jira QA comment

Turns the results of a test run into the comment that goes on the tested Jira
ticket. It only drafts. Whoever posts it follows the `postJiraComment`
preference ([preferences.md](../configure-project/references/preferences.md),
"After a test run"): `auto` posts it (a subagent too), `ask` (the default)
shows the draft and asks in the main conversation, `never` leaves the draft.

## Which format

1. Find the product: the config in `~/.claude/environments/` whose
   `ticketPrefixes` matches the ticket key. If it has `projectSkill`, open
   `<projectSkill>/SKILL.md` and look for the section **"Jira QA comment"**.
2. **The section describes a format, or points to a file that does:** use
   that format. Where it is silent on something, the rules below apply.
3. **No section, no project skill, or the section says "Default template":**
   for a ticket tested through the API, use
   [references/api-comment-default-template.md](references/api-comment-default-template.md);
   for a ticket tested in the app (web or mobile), use
   [references/ui-comment-default-template.md](references/ui-comment-default-template.md).
   A ticket tested both ways gets the UI template with the API template's
   "Endpoint, request and response" part added.
4. **API ticket, project format:** when the section says API comments always
   include the endpoint, request and response (the setup wizard's question),
   add them as the API template's "Endpoint, request and response" part shows,
   where the format places them or at the end. Otherwise follow the format.

Say in one line which one you used ("Format: Emtethal project skill",
"Format: default API template" or "Format: default UI template").

## Rules for every comment

- **Only what this run checked**, from its real results: never a case that
  didn't run, never a PASS the run didn't show. A case that couldn't run goes
  into the comment as not checked, with the reason.
- **One status for the whole ticket**, in the heading. No PASS or FAIL next to
  each line.
- **FAILED lists only the problems**, each with the key response or
  behaviour and a link to its bug when one was filed; what worked stays in the
  run's report, so the comment shows at once what has to be fixed. Leave out
  problems the developers already know about, unless the project skill says
  otherwise.
- **Links, not bare keys**: Jira tickets, PRs, commits, Figma nodes, Confluence
  pages. Test data ids (users, records) stay plain text.
- **Short.** A simple ticket gets the heading and one line per checked
  behaviour. Per-case detail only for tickets with real scenarios.
- **No tables** (they break in Jira comments) and no panels, unless the project
  format asks for them.
- **English**, unless the project format says otherwise.
- **Never a secret** (token, password, API key) in the comment or its code
  blocks.

## Showing and posting

- In the chat, show the draft as plain text: no blockquote (`>`) or other line
  prefix, because the terminal draws a bar on each line and it gets copied
  with the text.
- Posting (per `postJiraComment`): `addOrEditJiraIssueComment` with
  `contentFormat: "html"` and the body built as the template's "HTML" section
  shows (a project format is posted as HTML too). Before editing an existing
  comment, fetch it with `listJiraIssueComments` and `responseContentFormat:
  "html"` and keep everything in it, so the user's edits and images stay.
- Screenshots go into the comment body, where they belong (a `<figure>`), not
  only as attachments; videos are attached. Both go up as
  `~/.claude/skills/creating-jira-tickets/references/jira-attachments.md`
  says: Atlassian's own server (`uploadAttachmentToJiraIssue`), straight from
  the run folder. Never through `mcp-atlassian`, never via a copy in another
  folder.
