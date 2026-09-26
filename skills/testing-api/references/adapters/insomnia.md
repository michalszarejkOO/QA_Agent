# Insomnia adapter

Load this when the resolved product config has `api.client: "insomnia"`.

> **Unverified against a real collection.** Unlike the Bruno and Postman adapters,
> this one hasn't been exercised against a live Insomnia project yet, and
> Insomnia's testing model is structurally different from Bruno/Postman's
> per-request assertions — see below. Confirm the exact command shape against
> `inso --help` (and `inso run test --help`) before relying on anything in this
> file, and update it with what you actually find rather than trusting this text
> blindly.

## Why this one is different

Bruno and Postman both attach assertions directly to each request
(`runtime.assertions` / `pm.test()`), so "run the collection" and "run the tests"
are the same action. Insomnia's CLI (`inso`, from Kong) is built around a separate
concept — **Unit Test Suites**: Mocha/Chai-style test files that call
`insomnia.send(requestId)` and assert on the response, stored alongside the
collection rather than inside each request. There may be no per-request assertion
to run at all if a product's Insomnia workspace was never given a Unit Test Suite —
check for one before assuming this adapter can produce a pass/fail report the same
way the other two do.

## Typical layout

```
<collectionPath>/
  insomnia.json    # Insomnia v4 export: requests, environments, and (if present) unit test suites
```

Or, for a Git-sync'd workspace, a directory of per-resource YAML files instead of
one JSON export — check the product's `api.repo` for which shape is in use before
assuming it's the single-file export.

## Export

```
./scripts/export-collection.sh <repo_root> [dest_zip_path] <collectionPath> insomnia
```

## Run

Once a Unit Test Suite is confirmed to exist:

```
npx --yes insomnia-inso run test --env <env-name> --reporter list <path-or-identifier>
```

Treat the exact flags as provisional — confirm with `inso run test --help` in this
environment before trusting the invocation above, and note in the report if the
command shape differs from what's written here so the next run doesn't repeat the
same guess.

## Finding known stateful / order-dependent cases

Same procedure as the other adapters: check `api.knownCaveats` first, then a unit
test file's own comments/descriptions for order-dependence, and surface anything
newly discovered in the report's Notes rather than silently editing the config.
