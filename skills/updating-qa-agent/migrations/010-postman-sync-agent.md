# 010: Postman sync through its own agent, with an API key from 1Password

## What changed

Before publishing a Postman collection, `testing-api` syncs the repo files with
the user's Postman app. That used to go through the `postman` plugin, which
loads its whole Postman MCP server into every session, about 120k tokens of tool
descriptions. Now a `postman-sync` agent does it: the Postman MCP server
(`mcp.postman.com/minimal`, 41 tools) connects only inside that agent, so the
main conversation never loads its tools. The agent signs in with the user's
Postman API key, read from 1Password each time it connects
(`skills/testing-api/scripts/postman-mcp-headers.sh`), because an agent can't
open the browser sign-in. `~/.claude/environments/postman.json` says where the
key is. The agent's report always lists the variables without a Shared Value and
reminds the user that only Shared Value reaches 1Password.

## Is it needed

Needed when either is true:

- a product config in `~/.claude/environments/` has `"api": {"client": "postman"}`
  and `~/.claude/environments/postman.json` is missing or has no `apiKeyRef`
  starting with `op://`;
- `~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR/settings.json`) has an
  enabled plugin named `postman@...` under `enabledPlugins`.

Otherwise not needed. `check_setup.py --full` reports both.

## Fresh install

`ask`: the user chooses where their Postman API key is kept. On a machine with
no Postman product, "Is it needed" says no and nothing is asked.

## Steps

1. **Explain (runs by itself).** Say in short: publishing a Postman collection
   first checks what the team has in the Postman app. That now runs in its own
   agent, so the Postman tools (about 120k tokens with the old plugin) never load
   into the conversation. The agent signs in with a Postman API key that stays
   in 1Password.
2. **The key (asks).** Requires the 1Password CLI (`op`; migration 006 or
   `setup.sh` installs it). Ask: "Where is your Postman API key?"
   - **I have it in 1Password** → ask for the vault and item name. Don't list
     their items unasked. If they don't remember, offer to look for items with
     "postman" in the title (`op item list --format json`, titles and vaults
     only).
   - I don't have one yet → tell them: in Postman, Settings > API keys >
     Generate API key, then save it in 1Password, in a new item in their own
     vault (a password or API credential item, or a note with the key in it).
     They never paste it into the chat. Wait until they say it's saved, then ask
     for the vault and item.
   - Later → leave the migration pending. Publishing then asks about app changes
     instead of checking.
3. **Find the field (runs by itself).** Read the item's field labels only
   (`op item get "<item>" --vault "<vault>" --format json`, print `label` of each
   field, never a value). Pick the one holding the key: `credential`, then
   `password`, then `notesPlain`. Several candidates: ask which. Build
   `op://<vault>/<item>/<field>`.
4. **Check the key (runs by itself).** With the key in a shell variable, never
   printed, send one MCP `initialize` request to
   `https://mcp.postman.com/minimal` with `Authorization: Bearer <key>` and show
   only the HTTP status. `200`: go on. `401`: the key is wrong or revoked; go back
   to step 2. If the field holds no `PMAK-...` token, say so and go back to step 2.
5. **Write (runs by itself).** Write `~/.claude/environments/postman.json` as
   `{"apiKeyRef": "op://<vault>/<item>/<field>"}` (a real file, not a link, like
   the other shared files) and show it. It holds a reference, not the key.
6. **The old plugin (asks).** If a `postman@...` plugin is enabled in the user
   settings, ask: "The postman plugin loads about 120k tokens of Postman tools into
   every session and QA_Agent no longer uses it. Turn it off?"
   - **Yes, turn it off** → `claude plugin disable <name>`;
   - keep it (they use it outside QA_Agent).
7. **Say when it applies.** `setup.sh` links the `postman-sync` agent; new
   Claude Code sessions see it, so restart Claude Code. Remind them of the team
   rule from `testing-api`'s `adapters/postman.md`: every value the team needs,
   keys included, goes into Shared Value as a `default`-type variable.

## Verify

- `~/.claude/agents/postman-sync.md` links to the repo's `agents/postman-sync.md`.
- `validate_environments.py` prints `postman.json: ok`.
- `check_setup.py --full` prints `OK Postman API key reference set` and no
  Postman plugin warning (unless the user kept the plugin).
