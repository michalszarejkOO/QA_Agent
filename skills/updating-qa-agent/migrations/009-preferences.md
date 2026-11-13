# 009: preferences for what runs by itself

## What changed

A new machine file, `~/.claude/environments/qa-agent-preferences.json` (shape:
`environments.example/qa-agent-preferences.example.json`, docs:
`skills/configure-project/references/preferences.md`), sets per action whether
QA_Agent asks (`ask`, the default), just does it (`auto`) or never does it
(`never`): confirming the ticket environment, publishing the API collection,
posting the Jira comment, filing bugs, attaching evidence, adding lines to the
project skill. Every question now offers "Yes, always" / "No, never ask", which
save the answer. Every test run ends with the summary, scenario table, Jira
comment draft and bug drafts in the chat, not in report files
(`results.saveReportFiles` keeps a copy). `claudePermissions` lists tool groups
Claude Code may use without its own prompt. 1Password calls go through
`skills/testing-api/scripts/op.sh`, which uses a service-account token from the
Keychain when the user stored one, so there's no Touch ID prompt.

## Is it needed

Needed if `~/.claude/environments/qa-agent-preferences.json` (or under
`$CLAUDE_CONFIG_DIR`) doesn't exist.

## Steps

1. **Preferences (asks).** Ask as `configure-project` step 5b does
   (ask-and-remember is the default; "as much as possible" and "drafts only" are
   the other options), then the permission groups question, and write the file
   with `preferences.py set` (and the `claudePermissions` list by hand).
2. **Permissions (asks; default: yes when a group was picked).** Run
   `preferences.py permissions` to show the missing allow rules, and
   `preferences.py permissions --apply` after the user's yes. If Claude Code
   blocks it, give them the command to run themselves (`! python3 -I ...`).
3. **1Password without Touch ID (asks; default: skip).** If a product publishes
   to 1Password, say that each run currently asks for Touch ID several times, and
   that a service account stops that; the steps are the user's own
   (`testing-api` `references/onepassword-publish.md`, "No prompts at all").

## Verify

- `python3 environments.example/validate_environments.py` passes and prints
  `qa-agent-preferences.json: ok`.
- `preferences.py show` lists the user's choices, and `preferences.py
  permissions` prints "ok" when groups were picked.
