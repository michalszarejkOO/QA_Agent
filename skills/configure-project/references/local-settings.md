# Letting Claude write to product folders from anywhere

Optional, only if the user asks for it in SKILL.md step 5 (offer it every time:
without it, a session opened outside a product's folder asks for permission each
time it saves run output there).

QA_Agent's skills work from any folder Claude Code is opened in, and every run
writes into the product's `workDir`. So the folder access goes into the **user**
settings, `~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR/settings.json`), not
into one folder's `.claude/settings.local.json`: a project-level entry would only
apply when Claude is opened in that one folder.

## What to add

For each product configured in this run, add its `workDir` and every repo path
outside it (a `surfaces.*.repo`, `api.repo`, or any `repos.*` entry) to
`permissions.additionalDirectories`. A repo inside `workDir` is already covered by
it. Write paths with `~` as the user typed them:

```json
{
  "permissions": {
    "additionalDirectories": [
      "~/Projects/<product-workdir>",
      "~/Projects/<repo-outside-workdir>"
    ]
  }
}
```

If a product configured a Confluence tracker page, don't suggest allowlisting the
upload. With Atlassian's MCP server it goes through `executeWrite`, which covers
every write operation on that site, so an allow rule for it would let any Jira or
Confluence write through without a prompt. The upload itself is a `curl` command
run with Bash, which the user approves per run.

## Procedure

1. Read `~/.claude/settings.json` (it holds the user's other settings: model,
   theme, plugins, permissions). Parse it as JSON.
2. Merge the new `additionalDirectories` entries into the existing array (dedupe,
   don't replace the whole array; skip a path already covered by an entry that is
   its parent). Leave every other key exactly as it was.
3. Show the before/after of `permissions` and confirm before writing: this file
   controls what Claude can do without prompting, everywhere, so an unreviewed
   overwrite is a real risk, not just a formatting concern.
4. If the file doesn't exist yet, write a new one with just `permissions` —
   don't invent unrelated entries.
