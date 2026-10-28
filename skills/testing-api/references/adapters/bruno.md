# Bruno adapter

Load this when the resolved product config has `api.client: "bruno"`. Covers the
mechanics specific to Bruno's "OpenCollection" YAML format (not the older `.bru`
format) — export, CLI invocation, and where per-case caveats live. Everything else
(resolving the product, writing the report, publishing to Confluence) is the parent
skill's shared procedure.

## Typical layout

```
<collectionPath>/
  opencollection.yml           # collection root
  environments/
    <env>.yml                  # baseUrl per environment (e.g. local, demo, staging)
  <folder>/
    <sub-folder>/   01-...yml … NN-...yml   + folder.yml
```

Each request `.yml` has `info` (name/type/seq), `http` (method/url/headers/body),
`runtime.assertions` (a `res.status eq <code>` check the CLI verifies automatically),
and usually a `docs:` block explaining the case, its expected result, and any
precondition. **Read `docs:` before reporting a case's result** — the assertion only
proves the status code; the docs block is where a precondition (order, environment
config, timing) is recorded.

## Export

```
./scripts/export-collection.sh <repo_root> [dest_zip_path] [collection_subpath]
```

Zips the collection for import into the Bruno desktop app. Always pass a
`dest_zip_path` inside the run folder (see the parent skill's step 3); the
script's own fallback, `~/Desktop/<repo-folder-name>-bruno-collection.zip`, is
only for calling it by hand.
`collection_subpath` defaults to `bruno`.

## Run

The Bruno CLI treats the folder it is started from as the collection: it reads
the collection file (`opencollection.yml` / `bruno.json`), `environments/<env>.yml`
and the collection's `.env` from there. Started from the repo root, it finds none
of them and fails on the environment, or runs without its variables. So always run
it from the collection folder, in the same command, wherever the session is:

```
cd "<collection dir>" && npx --yes @usebruno/cli run [<scope>] --env <env> -r --output "<run folder>/bruno-run.json"
```

- `<collection dir>` is `<run root>/<collectionPath>`, absolute. `<run root>` is
  the folder the run uses as repo root: the worktree in generic mode,
  `<run folder>/confluence-collection/` in ticket mode, or the repo itself when
  the user asks to run the local checkout. Check that `opencollection.yml` (or
  `bruno.json`) is there before running.
- `<scope>` is relative to the collection folder, not the repo: leave it out for
  the full collection, or give the subfolder (`auth/verify-otp`) for a scoped run.
- Pass `--output` as an absolute path into the run folder. A relative one would land
  inside the collection, and in ticket mode end up in the exported zip.
- `-r` (recursive) is required to actually walk sub-folders.

Capture the per-request assertion results and the summary table.

## Finding known stateful / order-dependent cases

Before reporting on any case that touches auth, one-time codes, tokens, or anything
else that mutates server-side state:

1. Check that product's `environments/*.json` → `api.knownCaveats` for a list of
   named cases with real caveats (e.g. "case X only passes with env var Y set",
   "case Z depends on case W having run first for the same identifier"). If
   `api.knownCaveatsFile` is also set, load that file too (found as SKILL.md step 0
   says: `<workDir>/config/` first) — it's the fuller version for products whose
   caveat list is too long/structured to keep as flat JSON strings without drifting
   out of sync. Where the two disagree, the file is the more current one.
2. If nothing is recorded there but a case's name or `docs:` block implies
   order-dependence (reuse, expiry, single-use, "depends on"), read the neighboring
   request files in the same folder to confirm before reporting a bare PASS/FAIL —
   don't let a pass that happened for the wrong reason (e.g. an "expiry" case passing
   because a prior case already consumed the resource, not because time actually
   elapsed) read as a bigger guarantee than it is.
3. If you discover a new caveat this way that isn't yet recorded in the product's
   config, mention it in the report's Notes and suggest adding it to
   `api.knownCaveats` (or `api.knownCaveatsFile` if the product uses one) for next
   time — don't silently edit that file yourself unless asked.

## Content/placeholder data

Some collections test endpoints that serve editorial or legal content
(terms-and-conditions, code-of-conduct, etc.) whose source content may still be
placeholder text at the time of testing. That doesn't affect API test validity (the
tests check contract/behavior, not copy), but it's worth one line in Notes if the
report might be read as confirming final copy — check the product's config or the
source files for such a note before asserting the copy is final.
