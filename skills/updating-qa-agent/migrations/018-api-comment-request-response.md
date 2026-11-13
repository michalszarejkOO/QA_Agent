# 018: API ticket comments with the endpoint, request and response

## What changed

`writing-jira-comments` now has two defaults: for an API ticket "QA result"
(`references/api-comment-default-template.md`), which always shows the
endpoint, request and response of the happy path, and for a UI ticket
"Checked with status" (`references/ui-comment-default-template.md`, the old
`default-template.md`). A product with its own comment format decides once
whether its API ticket comments include the endpoint, request and response
too, with a line in the project skill's "## Jira QA comment" section.

## Is it needed

Needed for each product whose config in `~/.claude/environments/` (or
`$CLAUDE_CONFIG_DIR/environments/`) has an `api` block and `projectSkill`, and
whose `<projectSkill>/SKILL.md` has a "## Jira QA comment" section that is not
just "Default template." and has no line starting with "API tickets:". One
product's configs for several environments count as one. Not needed when the
section is missing (migration 013 asks about the format first).

## Fresh install

`skip`: configure-project asks the same question for every new API product
with its own comment format (product-config.md step 7, "Jira QA comment
format").

## Steps

1. **Explain (runs by itself).** Say in short: the default comment for an API
   ticket now always shows the endpoint, the request and the response of the
   happy path; a product with its own format chooses whether its comments do
   too. Show the product's current "## Jira QA comment" section.
2. **Ask once per product (asks; default: Tak, zawsze).** "Czy komentarz do
   taska API ma zawierać endpoint, request i response?" (in the user's
   language):
   - **Tak, zawsze** (recommended): every API ticket comment includes them,
     where the format places them or at the end, with tokens, passwords and
     personal data redacted;
   - **Nie**: the comment holds only what the format says (e.g. a comment
     written for the client).
3. **Write (runs by itself).** Add one line to the section: "API tickets:
   always include endpoint, request and response (happy path)." or "API
   tickets: no endpoint, request or response." Show it. Commit in the project
   skill's repo only if `SKILL.md` had no other uncommitted changes; otherwise
   leave the commit to the user and say so.

## Verify

- Every product that needed it has a line starting with "API tickets:" in the
  "## Jira QA comment" section of its project skill.
