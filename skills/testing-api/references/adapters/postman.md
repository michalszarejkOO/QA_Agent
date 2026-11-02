# Postman adapter

Load this when the resolved product config has `api.client: "postman"`. Covers the
mechanics specific to Postman's collection JSON format run via the Newman CLI —
export, invocation, and where per-case caveats live. Everything else (resolving the
product, writing the report, publishing to Confluence) is the parent skill's shared
procedure.

## Typical layout

```
<collectionPath>/
  <name>.postman_collection.json     # the collection: folders/requests, pm.test() assertions
  <tests>.postman_collection.json    # optional tests collection (api.testsCollection)
  environments/
    <env>.postman_environment.json   # baseUrl and other variables per environment
```

With `api.testsCollection` the cases live in the tests collection and the main
one keeps one request per endpoint (see
[config-fields.md](../config-fields.md), "The tests collection"). Both use the
same `environments/`.

A collection's `item[]` array nests folders and requests recursively. Each request
item has a `request` (method/url/header/body) and, usually, an `event[]` entry with
`listen: "test"` whose `script.exec` contains one or more `pm.test("<name>", () =>
...)` assertions — that's Postman's equivalent of Bruno's `runtime.assertions`.

**Per-case caveats live in the request's `description` field** (a plain string, or
an object with a `content` key) — Postman's equivalent of Bruno's `docs:` block.
**Read it before reporting a case's result** the same way: the `pm.test` assertions
only prove what they explicitly check; the description is where a precondition
(order, environment config, timing) is recorded, when the collection author wrote
one.

## Export

Postman collections are already plain JSON, so "export" just means zipping them
for re-import into the desktop app, the collection and its environments
separately:

```
./scripts/export-collection.sh <repo_root> <dest_zip_path> <collectionPath> postman [collection|environments]
```

Point `collectionPath` at the directory containing both the `*.postman_collection.json`
file and the `environments/` folder. The default part, `collection`, leaves out
`environments/`, `.env` files and a `.git` folder;
`environments` zips `environments/` on its own, since environment files can hold
live tokens (see [publishing.md](../publishing.md)). Publishing to 1Password skips
the zips: the collection file and each environment file go up as they are, so
people can import them straight into Postman (see
[onepassword-publish.md](../onepassword-publish.md), "What goes into each item").

## Syncing with the Postman app before publishing

People work in the Postman app; the repo files only change when someone exports
them. Importing a file copies it into Postman and nothing links the two after
that. So before publishing (publishing.md step 1), bring the repo up to date with
the app, or the zip carries a stale collection and environments.

**What Postman lets out.** Only a variable's **Shared Value** leaves the app,
through an export or the API. A value kept only in the **Value** column, or in the
**Postman Vault** (Postman moves a value there when someone types it into a
`secret`-type field), stays in that person's app. So variables the whole team
needs, keys included, are plain (`default`-type) variables with their value in
Shared Value; secret type and the Vault are for one person's own values.

**How.** The `postman-sync` agent does the steps below (publishing.md step 1
starts it). It is the only place the Postman MCP server connects, with the
user's Postman API key from 1Password (`~/.claude/environments/postman.json`,
read by `scripts/postman-mcp-headers.sh` when the agent starts), so its 41 tools
never load into the main conversation. Without it (no key set up, 1Password
locked, the agent reports "Postman not connected"), say so with the agent's fix,
ask the user whether they changed anything in the app since the last commit, and
go on with the files.

1. **Find the cloud copies.** Everything here is on the account of whoever is
   signed in to the MCP: teammates may each have their own Postman account and
   their own copy, which is fine, since they share through the publish target,
   not through Postman. `getCollections` needs a workspace: list the user's
   workspaces (`getWorkspaces`); use the one the project skill names only if it
   is in that list (workspace ids differ per account), otherwise pick the one
   named after the product, or ask. Then match
   names exactly, never ids: an import gives the collection a new id, so the
   file's `_postman_id` rarely matches the cloud one. The environment file's
   `name` (e.g. `EMTHETAL_STG`) against `getEnvironments`, the collection file's
   `info.name` against `getCollections`. Two matches (a `... Copy`, an old fork):
   ask which one. Name the workspace and ids you used in the summary. If the
   project skill names no workspace, propose adding this one, marked with whose
   account it is on.
2. **Environments: pull and merge.** `getEnvironment` for each, then rewrite the
   environment file in the collection folder from the brief (the repo's, or the
   run folder's copy for a product without `repo`) from it:
   - variables, order, values and types come from Postman;
   - a variable that is empty in Postman but has a value in the file keeps the
     file's value (it's in someone's Value column or Vault), and the summary says
     so, with the fix: put it in Shared Value as a `default`-type variable;
   - a `secret`-type variable comes back from the API with no value at all,
     even when one is set: treat it as empty in Postman, as above;
   - drop the stray `"secret": true` field the API returns next to a `type`; a
     file with it imports without that value;
   - keep the file's own header fields (`id`, `name`, `_postman_*`).
   Show what changed by name only (added, removed, value set or cleared, type),
   never values, and list per environment which variables have a value.
3. **Collection: check, don't rewrite.** A collection is too large to pass through
   the conversation safely, and the Postman CLI (`postman collection get`) prints
   only the v3 format. Compare the cloud collection's `updatedAt` with when the
   files were last changed, for each collection file (the main ones and the
   tests collection), matched by `info.name`: the last commit of the file
   (`git log -1 --format=%cI -- <file>`), or, for a product without `repo`, the
   published version's `updatedAt` in `<run folder>/published-base.json`.
   Newer in Postman: ask the user to export it over the collection file (Export,
   Collection v2.1, same path and name), then compare the request names with the
   previous version and show what changed. Not newer: say the files are current,
   and if they changed after `updatedAt`, that the app is behind them: the user
   should import the collection again (Replace is fine for a collection).
4. **Both sides changed.** If the files changed since the cloud copy's
   `updatedAt` (repo commits or uncommitted changes, or, without `repo`, cases
   this run added) and Postman changed too, show both and ask which to keep;
   never overwrite either silently.
5. **Commit only when the user says so** (SKILL.md, NEVER rule on git), in the
   collection's own repo, with the change summary as the message. Without
   `repo` there is nothing to commit: the publish carries the change.

**The other way round.** Someone who takes the collection from 1Password or
Confluence and imports the environment with **Replace** loses their local
values (Value column) for it. Suggest importing it as a new environment, or, on
their yes, updating their cloud environment through the `postman-sync` agent
(`putEnvironment`, Shared Values only; the brief says so explicitly).

## Run

```
npx --yes newman run "<collection dir>/<name>.postman_collection.json" \
  -e "<collection dir>/environments/<env>.postman_environment.json" \
  --reporters cli,json --reporter-json-export "<run folder>/newman-run.json"
```

`<name>` is the tests collection when the config has `testsCollection`;
otherwise the main collection (one run per file when there are several).

Newman resolves relative paths against the shell's current folder, so pass every
path absolute: `<collection dir>` is `<run root>/<collectionPath>`, where `<run
root>` is the worktree in generic mode, `<run folder>/published-collection/` in
ticket mode, or the repo itself when the user asks to run the local checkout.

Add `--folder "<folder name>"` to scope the run to one folder (Newman's equivalent
of Bruno's `-r <scope-path>`; unlike Bruno, Newman takes a folder *name* as it
appears in the collection, not a filesystem path). Read the CLI summary table for
the pass/fail counts, and parse `<run folder>/newman-run.json` (`run.stats`,
`run.executions[].assertions[]`) when you need the exact failing assertion text
rather than re-deriving it from the CLI's abbreviated output.

## Finding known stateful / order-dependent cases

Same procedure as Bruno's, adjusted for where the annotation lives:

1. Check that product's `environments/*.json` → `api.knownCaveats` for named cases
   with real caveats.
2. If nothing is recorded there but a request's name or `description` implies
   order-dependence (reuse, expiry, single-use, "depends on"), read the neighboring
   requests in the same folder to confirm before reporting a bare PASS/FAIL.
3. If you discover a new caveat this way, mention it in the report's Notes and
   suggest adding it to `api.knownCaveats` — don't silently edit that JSON file
   yourself unless asked.
