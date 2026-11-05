---
name: writing-jira-comments
description: Drafts the QA comment for a Jira ticket after testing, in the product's own format when its project skill has a "Jira QA comment" section, otherwise in the default template (a "Checked with status" heading with one status, a list of what was checked, or only the problems when it failed, no tables). Only drafts; posting happens in the main conversation after the user's yes. Used by qa-tester and testing-api, and on request.
when_to_use: "Trigger on: 'napisz komentarz do jiry', 'draft the QA comment for IP-123', 'przygotuj komentarz z testów', the comment step of qa-tester or testing-api ticket mode. Do NOT trigger for bug reports (reporting-bugs) or for posting a ready comment."
---

# Writing the Jira QA comment

Turns the results of a test run into the comment that goes on the tested Jira
ticket. It only drafts: whoever posts it (the main conversation, never a
subagent) shows the draft and asks the user first.

## Which format

1. Find the product: the config in `~/.claude/environments/` whose
   `ticketPrefixes` matches the ticket key. If it has `projectSkill`, open
   `<projectSkill>/SKILL.md` and look for the section **"Jira QA comment"**.
2. **The section describes a format, or points to a file that does:** use
   that format. Where it is silent on something, the rules below apply.
3. **No section, no project skill, or the section says "Default template":**
   use [references/default-template.md](references/default-template.md).

Say in one line which one you used ("Format: Emtethal project skill" or
"Format: default template").

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
- Posting (main conversation, after the user's yes): `addOrEditJiraIssueComment`
  with the body in ADF, built as the template's "ADF" section shows. Before
  editing an existing comment, fetch its current ADF so the user's own edits
  are kept.
- Screenshots and videos go up as
  `~/.claude/skills/creating-jira-tickets/references/jira-attachments.md`
  says: Atlassian's own server (`uploadAttachmentToJiraIssue`, `inlineFileId`
  for an image in the comment), straight from the run folder. Never through
  `mcp-atlassian`, never via a copy in another folder.
