---
name: creating-jira-tickets
description: Reconciles a drafted bug report or task against the target Jira project's actual required-field schema for that issue type (priority, version, environment, components, labels, and any project-specific custom fields) — asks the user for whichever required fields the draft doesn't already cover, then creates the ticket after explicit confirmation. Use when asked to file, create, or submit a Jira bug/task, or as the step after a draft (e.g. from reporting-bugs) is ready and the user wants it actually filed.
when_to_use: "Trigger on: 'file this bug', 'create a Jira ticket for X', 'submit this as a task', 'go ahead and file it', turning an already-drafted bug report or task description into an actual Jira issue. Do NOT trigger just to draft a report (that's reporting-bugs) or to search for duplicates (that's find-duplicates) — this only runs once there's content ready to become a real ticket and the user wants it created."
---

# Creating Jira tickets

Take a drafted bug report or task and actually file it — but only after the target
project's real field requirements are met, not a guessed or remembered set. Jira's
required fields vary per project and issue type (a "Priority" field with different
allowed values per project, a "Bug" type needing Environment where "Task" doesn't,
custom fields specific to one board), so this skill always reads the live schema
rather than assuming a fixed template covers it.

## Sources

- The drafted content: whatever the user/calling skill already produced (title,
  description, steps, expected/actual, or a task description). No draft at all → ask
  what should be filed rather than inventing content.
- Jira's own field metadata for the target project + issue type, via the Atlassian
  MCP tools — this is the authority on what's required, not this skill's memory of a
  past project's fields.

## Procedure

1. **Resolve the connector.** Confirm which Jira connector reaches the target site
   with `getAccessibleAtlassianResources` before trusting any cached
   connector-to-site mapping (e.g. a `reference_atlassian_connectors`-style memory
   note) — this has been observed to drift between sessions.
2. **Identify project and issue type.** If either isn't already stated or obvious
   from context (e.g. filing into the same project as a linked ticket), ask — never
   guess a project key.
3. **Fetch the real schema** for that project + issue type with
   `getJiraIssueTypeMetaWithFields` (or `getJiraProjectIssueTypesMetadata` to first
   confirm the issue type exists). This is the authoritative required-field list and,
   for enumerated fields, their allowed values — read it fresh each time rather than
   reusing a remembered field set from a different project.
4. **Map the draft onto known fields** — title → summary, steps/expected/actual (or
   the task description) → description — and mark which required fields from step 3
   still have no value. Commonly Priority, Affects/Fix Version, Environment,
   Components, Labels, but only what the fetched schema actually marks required for
   *this* project/type — don't assume a fixed list across projects.
5. **Ask for missing required fields one at a time**, not all at once and not
   pre-filled with a guess.
   - **Enumerated fields** (priority, environment, custom pick-lists, and any field
     whose schema returns a fixed `allowedValues` list) — use `AskUserQuestion` with
     the schema's own values as the options, not free text. If the schema returns
     more choices than the widget's 4-option limit, show the most relevant/common
     ones (e.g. open versions over archived ones) and rely on the tool's built-in
     "Other" to catch the rest — never invent an option the schema didn't return.
   - **Free-text fields** (summary detail, arbitrary labels, anything without a
     fixed value set) — ask directly in conversation; a forced-choice widget doesn't
     fit open-ended input.
6. **Show the full assembled field set for confirmation** before creating anything —
   every field value that will be sent, not just the ones that changed. Creating a
   Jira ticket is visible to the whole team and hard to undo cleanly, so this
   confirmation is required every run, not just the first time this skill is used.
7. **On explicit confirmation, create the ticket** with `createJiraIssue` using
   exactly the confirmed fields. If the user changes anything at this step, re-show
   the updated set before creating — don't file on an unconfirmed edit.
8. **Report the result** — the created ticket's key and link. If creation fails
   (e.g. a field Jira rejects), report the actual error rather than retrying with
   guessed field changes.

## Boundaries

- Never call `createJiraIssue` (or any other Jira write) without the explicit
  confirmation in step 6/7 having just happened in this run.
- Never invent a value for an enumerated field that isn't in the schema's allowed
  list, and never invent a custom field's meaning — if a custom field's purpose isn't
  obvious from its name, ask rather than guess.
- This skill doesn't draft report content (`reporting-bugs`) and doesn't check for
  duplicates (`find-duplicates`) — if either hasn't happened yet and seems relevant,
  say so before filing rather than silently skipping them.
