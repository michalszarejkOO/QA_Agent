# 003: only Atlassian's own MCP server for Jira and Confluence

## What changed

Skills now call Jira and Confluence only through Atlassian's own MCP server: the
claude.ai Atlassian connector, or `https://mcp.atlassian.com/v2/mcp` added to
Claude Code. Publishing an API collection to Confluence (`testing-api`,
`confluence-publish.md`) used to require the community `mcp-atlassian` server; it
now uploads through Atlassian's server and writes the page in that server's HTML.
`mcp-atlassian` and other Atlassian servers (company plugins) are no longer used:
their uploads and page format differ and fail. A machine whose Jira or Confluence
site is reachable only through one of them needs Atlassian's server added for that
site.

## Is it needed

Read `~/.claude/environments/atlassian-connectors.json` (or
`$CLAUDE_CONFIG_DIR/environments/atlassian-connectors.json`). If it doesn't exist,
not needed. Otherwise, for each site in it, look for an MCP server in this session
that has both `getAccessibleAtlassianResources` and `discover` and whose
`getAccessibleAtlassianResources` returns that site. Needed if any site has no such
server. Also needed if a project skill (`projectSkill` in a product config) or a doc
a config points at (`api.knownCaveatsFile`, `api.confluence.envRefreshProcedure`)
names tools of another Atlassian server: `confluence_…` or `jira_…` tool names, or
`mcp-atlassian`.

## Steps

1. **List the sites (runs by itself).** For each site, say which server reaches it,
   or that only another server (name it, e.g. `mcp-atlassian`) or none does.
2. **Add Atlassian's server for each missing site (asks; default: yes).** Give the
   user the command from `skills/configure-project/references/connectors.md`
   ("Two or more Atlassian sites"):
   `claude mcp add --transport http --scope user atlassian-<site-short-name> https://mcp.atlassian.com/v2/mcp`.
   Run it once they agree, then have them restart Claude Code, open `/mcp` → that
   server → Authenticate, and pick that site on Atlassian's consent screen (it may
   preselect another site).
3. **Old server (asks; default: leave it).** If `mcp-atlassian` or another
   Atlassian server is still registered, say QA_Agent no longer uses it. Removing
   it is the user's call (`claude mcp remove <name>`); other tools of theirs may
   still use it.
4. **Allow rules (asks; default: remove).** If `~/.claude/settings.json` allows
   `confluence_upload_attachment` / `confluence_upload_attachments` tools that
   `configure-project` used to suggest, offer to remove those entries. Show the
   before/after of `permissions` and leave every other setting as it is.
5. **Old tool names in project docs (asks; default: update).** For each project
   skill or config doc from "Is it needed" that names another server's tools, show
   the lines and the replacement from the "Atlassian tool names" table in
   `skills/configure-project/references/connectors.md` (for example
   `confluence_upload_attachment` → `createConfluenceAttachment` through `discover`).
   Change the file only after the user agrees; it's theirs, and may hold steps that
   have no direct equivalent: name those and leave them to the user.

The new server shows up only after a restart, so if step 2 added one, finish this
migration in the new session: mark it applied there, after Verify passes.

## Verify

- `checking-qa-agent` reports OK for every site in `atlassian-connectors.json`.
- No project skill or config doc names `mcp-atlassian` or its `confluence_…` /
  `jira_…` tools, except lines the user chose to keep.
