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

Zips the collection for import into the Bruno desktop app. Without a
`dest_zip_path` it defaults to `~/Desktop/<repo-folder-name>-bruno-collection.zip`.
`collection_subpath` defaults to `bruno`.

## Run

```
npx --yes @usebruno/cli run <scope-path> --env <env> -r
```

`<scope-path>` is `<collectionPath>` for the full collection or
`<collectionPath>/<subfolder>` for a scoped run, resolved relative to the repo root.
`-r` (recursive) is required to actually walk sub-folders. Capture the per-request
assertion results and the summary table.

## Finding known stateful / order-dependent cases

Before reporting on any case that touches auth, one-time codes, tokens, or anything
else that mutates server-side state:

1. Check that product's `environments/*.json` → `api.knownCaveats` for a list of
   named cases with real caveats (e.g. "case X only passes with env var Y set",
   "case Z depends on case W having run first for the same identifier"). If
   `api.knownCaveatsFile` is also set, load that file too (resolved relative to the
   same `environments/` directory) — it's the fuller version for products whose
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
