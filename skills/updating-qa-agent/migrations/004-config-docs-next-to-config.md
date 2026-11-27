# 004: docs a product config points at live next to it

## What changed

A product config can point at extra docs: `api.knownCaveatsFile` (known quirks of
its API tests) and `api.confluence.envRefreshProcedure` (how to refresh live
values before publishing the collection). They used to sit in
`~/.claude/environments/`. Since 001 the config itself lives in
`<workDir>/config/`, and 001 moved only the `.json` files, so these docs stayed
behind. They now belong next to the config, in `<workDir>/config/`, so everything
about a product is in its working directory. `testing-api` looks there first and
still finds a doc left in `~/.claude/environments/`, so nothing stops working
before this migration runs.

## Is it needed

Run `check_setup.py --full` (see `checking-qa-agent`). Needed if it reports a
WARN "file ... is still in ~/.claude/environments" or a FAIL "points at ..., which
is neither in ... nor in ...". Configs that are still real files in
`~/.claude/environments/` (001 not applied yet) are covered by 001; apply 001
first, then check again.

## Steps

1. **List (runs by itself).** For each product config with such a doc, show the
   field, the filename, where it is now and where it goes: the folder of the real
   config file (`readlink` the link in `~/.claude/environments/`).
2. **Copy (asks; default: yes).** Copy each doc into that folder under the same
   name. If a file with that name is already there and differs, show the diff and
   ask which one to keep; never overwrite without asking. Docs can hold logins or
   other secrets: copy them, never print their contents in the chat. If the
   working directory is a git repo, check that `config/` is in its `.gitignore`
   (001 added it) before going on.
3. **Remove the old copies (asks; default: yes, after step 4 passes).** Delete a
   doc from `~/.claude/environments/` only once the check in Verify is clean, and
   only if no other product config still points at it there (two products can
   share one doc: then copy it to both config folders first).
4. **Missing docs (asks).** For a FAIL (the doc is in neither place), ask the user
   where it is: put it next to the config, or remove the field from the config if
   the doc is gone for good (show the diff).

## Verify

- `check_setup.py --full` reports no "is still in" WARN and no "points at ..."
  FAIL.
- `~/.claude/environments/` holds only symlinks plus `atlassian-connectors.json`,
  `evidence.json` and `qa-agent-migrations.json`.
