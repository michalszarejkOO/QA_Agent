# Scaffolding .claude/settings.local.json

Optional, only if the user asks for it in SKILL.md step 4. `.claude/settings.local.json`
is per-machine and gitignored (see the repo's `.gitignore`) — there is no committed
example for it, unlike `environments.example/`, because its contents (an individual's
permission allowlist, `additionalDirectories`) are inherently local and vary by what
tools that person actually uses.

## What to add

For each product repo path configured in this run (a `surfaces.*.repo`, `api.repo`,
or any `repos.*` entry), add it to `additionalDirectories` so this working directory
can read/write there without a permission prompt every time:

```json
{
  "permissions": {
    "additionalDirectories": [
      "~/Projects/<repo-1>",
      "~/Projects/<repo-2>"
    ]
  }
}
```

If a product configured a Confluence tracker page, mention (don't auto-add without
asking — these are write-capable tools) that the user will likely also want to
allowlist the Confluence attachment tools they actually use, e.g.:

```json
{
  "permissions": {
    "allow": [
      "mcp__<their-confluence-connector>__confluence_upload_attachment",
      "mcp__<their-confluence-connector>__confluence_upload_attachments"
    ]
  }
}
```

Only suggest the connector name actually resolved in
[connectors.md](./connectors.md) — never guess a tool prefix.

## Procedure

1. Read the existing `.claude/settings.local.json` if one exists (most repos will
   have one after first use). Parse it as JSON.
2. Merge the new `additionalDirectories` entries into the existing array (dedupe,
   don't replace the whole array) and, only if the user confirms they want it, the
   suggested `allow` entries the same way.
3. Show the merged result and confirm before writing — this file controls what
   Claude can do without prompting, so an unreviewed overwrite is a real risk, not
   just a formatting concern.
4. If no such file exists yet, write a new one with just these two keys — don't
   invent unrelated permission entries.
