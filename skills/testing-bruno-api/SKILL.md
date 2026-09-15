---
name: testing-bruno-api
description: Runs a repo's Bruno API test collection against a live environment via the Bruno CLI, exports the collection to a zip the user can download and import into the Bruno app, optionally refreshes a lastUpdate timestamp on a Confluence tracker page and attaches that zip, and produces a Jira-comment-ready pass/fail report. Use when asked to test the API, run the Bruno/API test suite, verify endpoints are working, export/re-export a Bruno collection, or produce a test summary/report for a Jira ticket, for any product with a Bruno collection — not tied to one repo.
when_to_use: "Trigger on: 'przetestuj API', 'uruchom testy bruno', 'sprawdź czy endpointy działają', 'wygeneruj raport testów do jiry', 'wyeksportuj kolekcję bruno', 'run the bruno tests', 'test this endpoint', 'export the bruno collection', or any request to verify API behavior using a Bruno collection. Product-agnostic: resolve which repo/collection via the environments config (see step 0) or ask if it can't be resolved."
---

# Testing an API with Bruno

Drives a repo's Bruno "OpenCollection" YAML collection end to end: package it for the
Bruno desktop app, run it headlessly with the Bruno CLI, and turn the result into a
report the user can paste into Jira as test evidence. Product-agnostic — which repo,
which Confluence page (if any), and which stateful-case caveats apply all come from
that product's config, never hardcoded here.

## Applicability and exclusions

- Scoped to whatever repo's Bruno collection is in play. It does not write new
  request files or product code — if a request needs new test cases, that's a
  separate task.
- The collection is the source of truth. Never recreate it from scratch; only add to
  it if the user explicitly asks for new test cases.
- Requires network access to the target environment and `npx` (Node). If either is
  unavailable, say so — do not fabricate a result.
- The Confluence-publish step (step 7) only runs for a product whose environment
  config actually declares a `bruno.confluence` block. No config, no publish step —
  just export, run, and report.

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Resolve the target repo and collection path before doing anything else (step 0) — never assume the current directory has the collection. |
| MUST | Default to the environment named in that product's config (`bruno.defaultEnvironment`, commonly `demo`) unless the user names another one. A `local`-type environment requires the app running locally — check reachability first and say clearly if it's down, rather than letting the run fail with a confusing connection error. |
| MUST | Run the CLI with `-r` (recursive) scoped to the folder implied by the request — the whole collection by default, or a specific subfolder when the user names an endpoint or area. |
| MUST | Before writing the report, check the `docs:` block of any test case that looks order- or state-dependent (see [test-case-conventions.md](./references/test-case-conventions.md)), including any product-specific caveats listed in that product's config, and surface real caveats in the report's Notes — a clean pass/fail count that hides a non-representative test is misleading evidence. |
| MUST | Use the report template in [report-template.md](./references/report-template.md) verbatim in structure — same headers, same table shape — so reports stay consistent across runs and products. Fill it from the actual CLI output, never from memory of a previous run. |
| MUST | If (and only if) the product's config declares a `bruno.confluence` block, end the run by refreshing the `lastUpdate` timestamp on that Confluence page and attaching the freshly exported zip, per [confluence-publish.md](./references/confluence-publish.md) — this is independent of test results, not conditional on them passing. |
| NEVER | Put collection content (request bodies, YAML, file dumps) inline in a Confluence page body. It stays a `lastUpdate` marker; the zip is attached as a file, not pasted as text. |
| NEVER | Commit, push, or otherwise persist results/exports into git without being asked. The zip export is a local artifact, not a repo change. |
| NEVER | Claim a PASS the CLI did not report. If any request fails, show the failing assertion(s) and response detail, and reflect the real status in the report. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [report-template.md](./references/report-template.md) | Generating the final report, every run | The exact Jira-comment template (header fields, results table, coverage bullets, Notes) |
| [test-case-conventions.md](./references/test-case-conventions.md) | Interpreting results, or when any stateful/order-dependent case is in scope | How to read a Bruno collection's layout and `docs:` blocks, and where to find product-specific known caveats |
| [confluence-publish.md](./references/confluence-publish.md) | Updating the tracker page, every run where the product config declares one | Reading cloudId/space/folder/title/attachment name from config, the generate-body script, find-or-create/update procedure, attaching the exported zip |

## Procedure

0. **Resolve the product and its Bruno config.** Figure out which repo/collection is
   in scope from the user's request (a repo name, a ticket prefix, or an explicit
   path). Look for a matching file under `~/.claude/environments/*.json` (or
   `$CLAUDE_CONFIG_DIR/environments/` if that's set — the same global, per-product
   config `qa-tester` uses) with a `bruno` block:
   ```json
   "bruno": {
     "repo": "~/Projects/<repo>",
     "collectionPath": "bruno",
     "defaultEnvironment": "demo",
     "knownCaveats": ["<free text about stateful/order-dependent cases, if any>"],
     "confluence": {
       "cloudId": "<site>",
       "spaceKey": "<space>",
       "parentId": "<folder page id>",
       "pageTitle": "<fixed page title>",
       "attachmentName": "<fixed zip filename>"
     }
   }
   ```
   - **Found** → use `repo` as the repo root and `collectionPath` (default `bruno`)
     for every step below. `confluence` is optional; its absence just means step 7 is
     skipped.
   - **Not found, but the current directory has a `bruno/`-style collection** → use
     the cwd as repo root, default environment `demo`, and skip the Confluence step
     (nothing to publish to without config).
   - **Not found and cwd has no collection** → ask the user which repo/collection to
     run against rather than guessing.

1. **Parse the rest of the request.** If it names a folder under the collection
   (e.g. "content", "auth/verify-otp"), scope both the run and the report to that
   folder. If it names an environment ("local", "demo"), use that; otherwise default
   per step 0.

2. **Export the collection.** Run `./scripts/export-collection.sh <repo_root>
   [dest_zip_path] [collection_subpath]` to zip the collection. Without a `dest_zip_path`
   it defaults to `~/Desktop/<repo-folder-name>-bruno-collection.zip`. Report the
   output path so the user can re-import it into the Bruno desktop app.

3. **Check the target environment.** For a local-style environment, verify the
   expected localhost URL is reachable (e.g. a short `curl -o /dev/null -w
   "%{http_code}"` against any known route) before running anything; if it isn't,
   tell the user and ask whether to fall back to the default remote environment
   rather than running a suite that will fail uniformly on connection errors. A
   public remote environment is still worth a quick reachability check, but failure
   there is a real signal, not an environment problem.

4. **Run the suite:**
   ```
   npx --yes @usebruno/cli run <scope-path> --env <env> -r
   ```
   `<scope-path>` is `<collectionPath>` for the full collection or
   `<collectionPath>/<subfolder>` for a scoped run, resolved relative to the repo
   root. Capture the per-request assertion results and the summary table.

5. **Investigate any failure** before reporting: show which assertion failed, the
   actual status/response, and whether the `docs:` block names a precondition (wrong
   environment, wrong order, expired state) that explains it. Don't just report a
   number.

6. **Write the report** using [report-template.md](./references/report-template.md),
   filled with this run's real numbers, current commit (`git rev-parse --short HEAD`,
   run in the repo root) and branch, the environment used, and a Notes section that
   includes any caveats found in step 5 or flagged by
   [test-case-conventions.md](./references/test-case-conventions.md)/the product's
   `bruno.knownCaveats` for cases that ran. Present it in a fenced code block so it's
   a clean paste into Jira.

7. **If the product's config has a `bruno.confluence` block**, refresh that page's
   `lastUpdate` and attach the zip, following
   [confluence-publish.md](./references/confluence-publish.md) exactly (identifiers
   come from config, not from this file). Do this regardless of whether the tests
   passed — it's a timestamp and a file, not a test result. Give the user the page
   link when done. If there's no `confluence` block, skip this step silently — don't
   ask the user to set one up unless they bring it up.
