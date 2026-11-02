---
name: reading-jira-tickets
description: Reads a Jira ticket fully before testing or writing about it — picks the Atlassian connector for the ticket's site, fetches the issue with every comment, web link and the linked issues it relies on, finds the Figma design and the PR or branch with its diff, and says which part couldn't be read. Also how to search Jira with JQL without losing fields. Read-only; never comments, edits or transitions. Used by qa-tester (UI), testing-api ticket mode (API), routing-qa-tickets, testing-apps retests, writing-test-cases, preparing-refinement-questions, find-duplicates and create-quality-metrics, and on request.
when_to_use: "Trigger on: 'przeczytaj ticket IP-123', 'co jest w tickecie', 'read ABC-123 before testing', 'find the PR for this ticket', the context step of qa-tester, testing-api ticket mode, writing-test-cases or preparing-refinement-questions, a JQL search for find-duplicates. Do NOT trigger for writing to Jira (writing-jira-comments, creating-jira-tickets) or for registering connectors (configure-project)."
---

# Reading a Jira ticket

Everything a test run or a document does follows from how well the ticket was
read, so read all of it, but without fields nobody uses. Only reads: never
comment, edit, transition or create anything here.

## Which connector

1. Find the product: the config in `~/.claude/environments/` (or
   `$CLAUDE_CONFIG_DIR/environments/`) whose `ticketPrefixes` matches the
   ticket key. Its `jira` field names the connector.
2. No such config: match the ticket URL's hostname against
   `~/.claude/environments/atlassian-connectors.json`. Never try connectors
   blind; several at once is normal, each authorized for its own site.
3. Before trusting the mapping, check that the connector's
   `getAccessibleAtlassianResources` lists the ticket's site: the grant has been
   seen to drift between sessions. If it doesn't, report precisely which site
   is authorized and which one the ticket lives on, so the connector is
   re-authorized for that site, not given broader permissions.

Tool names and which ones go through `discover`: the `configure-project`
skill's `references/connectors.md`, "Atlassian tool names". Only Atlassian's
own MCP server; never fall back to another one.

## The ticket

Measured on a large ticket (30.10.2026): `view: "compact"` (the default) ~500
tokens, `"evidence"` ~2,700, `"full"` ~6,200, mostly worklogs and metadata.

1. **The issue:** `getJiraIssue` with `view: "evidence"`. It has the full
   description and acceptance criteria, issue type, parent, every linked issue
   (key, summary, status), sprint and custom fields, and the number of comments.
   - **Never pass `fields` to `getJiraIssue`**: the server silently drops fields
     such as summary, issue type and links, so the ticket looks complete when it
     isn't.
   - Don't use `view: "full"`, unless a run needs worklogs, watchers, time
     tracking, or a design custom field `evidence` doesn't map.
2. **The comments, whenever the count is above 0:** `listJiraIssueComments`, all
   pages. Comments often clarify or change the acceptance criteria, or say what
   was agreed to be out of scope; a later comment overrides the description.
3. **Web links** (Figma, Confluence, other URLs): `listJiraIssueRemoteIssueLinks`
   (through `discover`, `executeRead`).
4. **Parent or linked issues**, only when the description or comments rely on
   them (e.g. "as in IP-78"): `getJiraIssue` on each with the default view.

Only a description given, no key: find the ticket with JQL ("Searching Jira").
The full description and acceptance criteria already in the brief: use them
without fetching again.

## The design

A figma.com URL in the brief, the description, a comment or the web links.
Fetching and comparing it is the caller's job (Figma MCP tools). No link
anywhere: say there is none; never guess or search for a design.

## The PR or branch

- **A GitHub PR:** `gh pr view <n> --json title,body,url` and `gh pr diff <n>`.
- **Linked in the ticket:** the development panel or the web links.
- **No PR linked, a Bitbucket or GitLab PR, or an API you can't reach:** read
  [references/finding-the-pr.md](references/finding-the-pr.md) before calling
  it a blocker. It finds the branch with `git` (the ticket key in
  `git ls-remote`) and reads it without moving the user's checkout.
- **Merged already:** note where (which integration branch), so the caller can
  pick the environment that has it. A local checkout behind the remote is not
  the merged state: read `origin/<branch>`.
- **Never move the user's checkout:** read in place (`git show
  origin/<branch>:<path>`, `git diff`, `git grep`); never `checkout`, `switch`,
  `reset` or `pull` in their clone.

## Searching Jira

`searchJiraIssuesUsingJql` returns no descriptions in any case. Pass `fields`
with what the next step uses, e.g. `["summary", "status", "issuetype", "created",
"labels"]` (about a third smaller than the default). `fields` is honored exactly
in search, so leave out nothing the step needs: for metrics, list every field a
metric reads (priority, resolution date, fix versions, components, ...) or
don't pass `fields` at all. To judge a candidate, open it with `getJiraIssue`
(default view) instead of widening the search.

## What to hand back

The acceptance criteria as the comments left them, what the comments changed
or put out of scope, linked issues that matter, the Figma link or "no design",
the PR or branch with its diff (or what was tried), and where it was merged.

If any call fails, say which part wasn't read. Never test or write against a
ticket you only partly read without saying so.
