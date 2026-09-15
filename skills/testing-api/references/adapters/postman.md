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
  environments/
    <env>.postman_environment.json   # baseUrl and other variables per environment
```

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

Postman collections are already plain JSON, so "export" just means bundling the
collection and its environment file(s) into one zip for re-import into the desktop
app:

```
./scripts/export-collection.sh <repo_root> [dest_zip_path] <collectionPath> postman
```

Point `collectionPath` at the directory containing both the `*.postman_collection.json`
file and the `environments/` folder, so both come along in the zip.

## Run

```
npx --yes newman run <collectionPath>/<name>.postman_collection.json \
  -e <collectionPath>/environments/<env>.postman_environment.json \
  --reporters cli,json --reporter-json-export /tmp/newman-run.json
```

Add `--folder "<folder name>"` to scope the run to one folder (Newman's equivalent
of Bruno's `-r <scope-path>`; unlike Bruno, Newman takes a folder *name* as it
appears in the collection, not a filesystem path). Read the CLI summary table for
the pass/fail counts, and parse `/tmp/newman-run.json` (`run.stats`,
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
