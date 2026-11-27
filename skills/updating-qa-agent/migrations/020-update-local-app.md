# 020: update the collection in Postman or Bruno after a publish

## What changed

After `testing-api` publishes a Postman or Bruno collection, it can now bring
the user's own app up to date, so nobody imports the new version by hand. A new
preference, `updateLocalApp` in `~/.claude/environments/qa-agent-preferences.json`,
decides it: `never` (shown as **manual**, the default and the old behaviour)
leaves the import to the user; `auto` replaces the collection and environments
in the user's Postman workspace through the Postman API
(`skills/testing-api/scripts/postman-push.py`, run by the `postman-sync` agent
in push mode), or, for Bruno, keeps the local folder Bruno has open current.
Names stay the same, so Postman never gets a second copy. Docs: testing-api
`references/publishing.md` step 8.

## Is it needed

Needed if some product config has `api.client` `postman` or `bruno`, and
`~/.claude/environments/qa-agent-preferences.json` (or under
`$CLAUDE_CONFIG_DIR`) has no `updateLocalApp` in `actions`. A machine with no
such product doesn't need it.

## Fresh install

`skip`: configure-project step 5b already asks the same question
(`updateLocalApp`) for every product with a Postman or Bruno collection.

## Steps

1. **Explain (runs by itself).** Say in two lines: after a publish the agent
   can now update the collection in your Postman or Bruno itself, with the same
   names, so you don't import it; until now you imported it by hand.
2. **Ask (tappable options; default in bold).** "Jak aktualizować kolekcję w
   Postmanie / Bruno po publikacji?" (in the user's language), with the two
   options and descriptions from configure-project `references/preferences.md`,
   "Choosing in the setup wizard":
   - **manual**: after a publish you import the collection yourself (Postman:
     Import with Replace; Bruno: open the collection folder); nothing in your
     app changes without you.
   - **auto**: the agent replaces the collection and environments in your
     Postman workspace through the Postman API (Bruno reloads them from the
     local folder), same names, no import; it stops and asks when something
     changed in your app after the check.
3. **Save (runs by itself).** `python3 -I
   ~/.claude/skills/configure-project/scripts/preferences.py set updateLocalApp
   <never|auto>` (`manual` is `never`). With `auto`: for a Bruno product whose
   `api.publish.target` is `1password`, say that auto needs a local copy and
   offer to switch the target to `1password+local` with an
   `apiCollectionsFolder` (configure-project `references/product-config.md`);
   for a Postman product without `~/.claude/environments/postman.json`, say
   that auto needs the Postman API key (migration 010 sets it up). Show
   `preferences.py show`.

## Verify

- `python3 environments.example/validate_environments.py` passes and prints
  `qa-agent-preferences.json: ok`.
- `preferences.py get updateLocalApp` prints `auto` or `never`.
