# Discovering and configuring Atlassian connectors

Produces `~/.claude/environments/atlassian-connectors.json` (or
`$CLAUDE_CONFIG_DIR/environments/atlassian-connectors.json`), the standing map every
skill checks before guessing which Atlassian MCP connector reaches which Jira/
Confluence site — see `agents/qa-tester.md`'s "Jira ticket" input and
`skills/testing-api/references/ticket-driven-testing.md` step T0. There is
deliberately no example template for this file elsewhere in the repo; this is where
it gets created.

## Shape

```json
{
  "connectors": {
    "<connector-name>": { "site": "<your-site>.atlassian.net" }
  }
}
```

`<connector-name>` is whatever short, memorable name you want to refer to this
connector by inside product configs' `jira.connector` field — it does not have to
match the MCP tool prefix, but making it recognizable (e.g. `internal`, `client-x`)
helps more than a generic `atlassian1`.

## Procedure

1. **List which Atlassian MCP tools/connectors are available this session.** Look for
   tool names matching `mcp__*atlassian*` or `mcp__*Atlassian*` (there may be more
   than one — different plugins, or the same site connected two ways). Tell the user
   what you found and ask them to confirm which of these they actually want
   registered (some sessions have duplicates or stale ones not worth keeping).

2. **For each connector the user confirms, resolve its site live.** Call that
   connector's own `getAccessibleAtlassianResources` tool — never ask the user to
   type the site/cloudId from memory, and never reuse a site you saw earlier in the
   conversation for a *different* connector. If a connector is authorized for more
   than one site, ask the user which one this product config should use (or
   register it under two different connector names if they genuinely need both).

3. **Ask the user to name each connector** (the `<connector-name>` key) — offer the
   resolved site's short name as a default suggestion, but let them override it.

4. **Show the assembled JSON** for confirmation before writing.

5. **Write the file.** If `atlassian-connectors.json` already exists, show the diff
   against the existing content and merge rather than overwrite — a second run
   (e.g. adding a second Jira site later) must not drop connectors already
   registered.

6. **Note the file's one blind spot** to the user: this only records site mappings,
   not live authorization — if a connector is later revoked or a new one added, the
   skills that read this file will still trust whatever's on disk until someone
   updates it (or a skill's own live `getAccessibleAtlassianResources` check catches
   the drift and reports it as a blocker).

If the user says no Atlassian integration is needed at all, skip this whole
reference and tell [product-config.md](./product-config.md) to omit `jira` and
`api.confluence` from every product.
