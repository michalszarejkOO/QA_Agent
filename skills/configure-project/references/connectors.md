# Discovering and configuring Atlassian connectors

Produces `~/.claude/environments/atlassian-connectors.json` (or
`$CLAUDE_CONFIG_DIR/environments/atlassian-connectors.json`), the standing map every
skill checks before guessing which Atlassian MCP connector reaches which Jira/
Confluence site — see `agents/qa-tester.md`'s "Jira ticket" input and
`skills/testing-api/references/ticket-driven-testing.md` step T0. There is
deliberately no example template for this file elsewhere in the repo; this is where
it gets created.

It also holds the [Atlassian tool names](#atlassian-tool-names) that every skill
uses to call Jira and Confluence.

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

## Two or more Atlassian sites

Each Atlassian MCP server's OAuth grant covers one site, and claude.ai lets a user
add only one Atlassian connector. So when the products span more than one site
(e.g. two clients), every extra site needs a local Claude Code MCP server:

```
claude mcp add --transport http --scope user atlassian-<site-short-name> https://mcp.atlassian.com/v2/mcp
```

then `/mcp` → that server → Authenticate, and pick the right site on Atlassian's
consent screen: it may preselect another site the account belongs to. A new
server only shows up in a new Claude Code session. Always confirm afterwards with
that server's own `getAccessibleAtlassianResources` (step 2 below). If the user
has no connector at all yet, the same local setup works for the first site too.

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

## Atlassian tool names

Every skill and the `qa-tester` agent that talks to Jira or Confluence uses the
names below, so a renamed tool is fixed here once. They are the operation names
of Atlassian's own MCP server (`https://mcp.atlassian.com/v2/mcp`, also behind the
claude.ai Atlassian connector). The full tool name adds the server's prefix, which
is whatever the user named it (`mcp__atlassian-<site>__getJiraIssue`,
`mcp__claude_ai_Atlassian__getJiraIssue`, ...); pick the server for the site from
`atlassian-connectors.json`.

Two kinds of operation:

- **Direct**: a tool of its own; call it as is (load its schema with ToolSearch
  first if it's deferred).
- **Through discover**: no tool of its own. Call that server's `discover` with
  the goal in words, then run the operation with the execute tool `discover`
  names (`executeRead` for reads, `executeWrite` for writes), passing `cloudId`
  at the top level and the operation's arguments in `inputs`. Never guess an
  operation name; if one below is missing, `discover` the goal again.

| To do this | Operation | How |
| --- | --- | --- |
| Find which site a server reaches (cloudId) | `getAccessibleAtlassianResources` | direct |
| Read one Jira issue (`view: "evidence"` adds its issue links) | `getJiraIssue` | direct |
| Search Jira with JQL | `searchJiraIssuesUsingJql` | direct |
| List an issue's web links (Figma, Confluence, other URLs) | `listJiraIssueRemoteIssueLinks` | through discover, `executeRead` |
| List a project's issue types | `listJiraProjectIssueTypesMetadata` | through discover, `executeRead` |
| Get an issue type's fields (required ones, allowed values, `customfield_*` ids) | `getJiraIssueTypeMetaWithFields` | through discover, `executeRead` |
| Create a Jira issue | `createJiraIssue` | direct |
| Add or edit a Jira comment | `addOrEditJiraIssueComment` | direct |
| Edit a Jira issue / move it to another status | `editJiraIssue` / `transitionJiraIssue` | direct |
| Search Confluence (CQL) | `searchConfluence` | direct |
| Read a Confluence page | `getConfluenceContent` | direct |
| Create / update a Confluence page | `createConfluenceContent` / `updateConfluenceContent` | direct |
| Get the body format rules before writing a page or comment body | `getContentFormatGuide`, with `toolName` set to `createConfluencePage` or `updateConfluencePage` for pages, `addOrEditJiraIssueComment` for a Jira comment in HTML | through discover, `executeRead` |

A different Atlassian MCP server (for example the community `mcp-atlassian`, with
names like `jira_get_issue`) works too: match each row by what it does, not by
name, and tell the user which tool you used for it.
