# 013: Jira QA comment format per product

## What changed

The QA comment drafted for a Jira ticket after testing now comes from one
skill, `writing-jira-comments`, used by `qa-tester`, `testing-api` ticket mode
and `testing-apps` retests. It uses the product's own format when the project
skill has a "Jira QA comment" section, otherwise a default template (a
"Checked with status" heading with one status, a list of what was checked, or
only the problems when it failed, no tables). Before, `qa-tester` put its
scenario table into the comment and `testing-api` used its report, so the two
looked different and neither followed a product's own format unless the
project skill happened to say so in its own words.

## Is it needed

Needed when a product config in `~/.claude/environments/` (or
`$CLAUDE_CONFIG_DIR/environments/`) has `projectSkill` and that
`<projectSkill>/SKILL.md` has no heading named "Jira QA comment". Otherwise not
needed. Once applied it isn't asked again, also for products the user chose to
leave as they are.

## Fresh install

`skip`: configure-project asks the same question for every new product with a
project skill (product-config.md step 7).

## Steps

1. **Look for an existing format (runs by itself).** For each product that
   needs it (one product's configs for several environments count as one),
   search its project skill folder for a rule about Jira comments (e.g. "Jira
   comment", "QA comment", "Checked with status", a `jira.md` reference). Note
   the file and lines.
2. **Explain and ask once per product (asks).** Say in short: comments after
   testing now come from `writing-jira-comments`, in the product's format when
   the project skill names one, otherwise the default template; show the
   template's short form. Ask per product "Which format should QA comments for
   this product use?":
   - **Use the format already in the project skill** (recommended, and offered
     only when step 1 found one): the section points to that file or lines;
   - **Default template** (recommended when nothing was found): the section
     says "Default template.";
   - **Default with changes**: ask what to change and write those changes;
   - **Our own format**: ask for an example comment or a file and describe it;
   - leave the product as it is.
3. **Write the section (runs by itself).** Add "## Jira QA comment" to
   `<projectSkill>/SKILL.md` with the chosen content and show it. Commit in the
   project skill's repo only if `SKILL.md` had no other uncommitted changes;
   otherwise leave the commit to the user and say so.
4. **Show the result.** Per product: the format chosen and the section
   written, or "left as it is".

## Verify

- Every product the user didn't leave as it is has a "## Jira QA comment"
  heading in its project skill's `SKILL.md`.
