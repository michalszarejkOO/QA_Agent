---
name: testing-api
description: Runs a repo's API test collection — Bruno, Postman, or Insomnia — against a live environment via that tool's CLI, exports the collection to a zip the user can download and import into the matching desktop app, optionally refreshes a lastUpdate timestamp on a Confluence tracker page and attaches that zip, and produces a Jira-comment-ready pass/fail report. Use when asked to test the API, run the API test suite, verify endpoints are working, export/re-export an API collection, or produce a test summary/report for a Jira ticket, for any product with a Bruno, Postman, or Insomnia collection — not tied to one repo or one tool.
when_to_use: "Trigger on: 'przetestuj API', 'uruchom testy API/bruno/postman/insomnia', 'sprawdź czy endpointy działają', 'wygeneruj raport testów do jiry', 'wyeksportuj kolekcję', 'run the API tests', 'test this endpoint', 'export the collection', or any request to verify API behavior using a committed collection. Product-agnostic: resolve which repo/collection/tool via the environments config (see step 0) or ask if it can't be resolved."
---

# Testing an API collection

Drives a repo's committed API test collection end to end: package it for the
matching desktop app, run it headlessly via that tool's CLI, and turn the result
into a report the user can paste into Jira as test evidence. Product-agnostic and
tool-agnostic — which repo, which client (Bruno/Postman/Insomnia), which Confluence
page (if any), and which stateful-case caveats apply all come from that product's
config, never hardcoded here. The mechanical differences between clients (how a
collection is packaged, the exact CLI invocation, where per-case caveats/annotations
live) are isolated in one adapter file per tool; everything else — resolving the
product, checking caveats, writing the report, publishing to Confluence — is shared
and identical regardless of which tool a given repo happens to use.

## Applicability and exclusions

- Scoped to whatever repo's collection is in play. It does not write new request
  files or product code — if a request needs new test cases, that's a separate
  task.
- The collection is the source of truth. Never recreate it from scratch; only add to
  it if the user explicitly asks for new test cases.
- Requires network access to the target environment and whatever runtime the
  resolved adapter needs (`npx`/Node for Bruno and Postman; Node for Insomnia's
  `inso`). If either is unavailable, say so — do not fabricate a result.
- The Confluence-publish step (step 7) only runs for a product whose environment
  config actually declares an `api.confluence` block. No config, no publish step —
  just export, run, and report.

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Resolve the target repo, client, and collection path before doing anything else (step 0) — never assume the current directory has the collection, and never guess the client from habit when the config says otherwise. |
| MUST | Default to the environment named in that product's config (`api.defaultEnvironment`, commonly `demo`) unless the user names another one. A `local`-type environment requires the app running locally — check reachability first and say clearly if it's down, rather than letting the run fail with a confusing connection error. |
| MUST | Run the resolved adapter's CLI scoped to the folder implied by the request — the whole collection by default, or a specific subfolder when the user names an endpoint or area. |
| MUST | Before writing the report, check the resolved adapter's per-case caveat convention for any test case that looks order- or state-dependent, including any product-specific caveats listed in that product's config (`api.knownCaveats`), and surface real caveats in the report's Notes — a clean pass/fail count that hides a non-representative test is misleading evidence. |
| MUST | Use the report template in [report-template.md](./references/report-template.md) verbatim in structure — same headers, same table shape — so reports stay consistent across runs, products, and tools. Fill it from the actual CLI output, never from memory of a previous run. |
| MUST | If (and only if) the product's config declares an `api.confluence` block, end the run by refreshing the `lastUpdate` timestamp on that Confluence page and attaching the freshly exported zip, per [confluence-publish.md](./references/confluence-publish.md) — this is independent of test results, not conditional on them passing. |
| NEVER | Put collection content (request bodies, raw exports, file dumps) inline in a Confluence page body. It stays a `lastUpdate` marker; the zip is attached as a file, not pasted as text. |
| NEVER | Commit, push, or otherwise persist results/exports into git without being asked. The zip export is a local artifact, not a repo change. |
| NEVER | Claim a PASS the CLI did not report. If any request fails, show the failing assertion(s) and response detail, and reflect the real status in the report. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [adapters/bruno.md](./references/adapters/bruno.md) | `api.client` is `"bruno"` | Collection layout, `docs:` block convention, export/run commands |
| [adapters/postman.md](./references/adapters/postman.md) | `api.client` is `"postman"` | Collection/environment JSON shape, per-request description convention, Newman export/run commands |
| [adapters/insomnia.md](./references/adapters/insomnia.md) | `api.client` is `"insomnia"` | Export shape, `inso` CLI invocation — flag as less battle-tested, confirm syntax against `inso --help` before relying on it |
| [report-template.md](./references/report-template.md) | Generating the final report, every run | The exact Jira-comment template (header fields, results table, coverage bullets, Notes) |
| [confluence-publish.md](./references/confluence-publish.md) | Updating the tracker page, every run where the product config declares one | Reading cloudId/space/folder/title/attachment name from config, the generate-body script, find-or-create/update procedure, attaching the exported zip |

## Procedure

0. **Resolve the product, client, and config.** Figure out which repo/collection is
   in scope from the user's request (a repo name, a ticket prefix, or an explicit
   path). Look for a matching file under `~/.claude/environments/*.json` (or
   `$CLAUDE_CONFIG_DIR/environments/` if that's set — the same global, per-product
   config `qa-tester` uses) with an `api` block:
   ```json
   "api": {
     "client": "bruno",
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
   `client` is one of `"bruno"`, `"postman"`, `"insomnia"` and selects which adapter
   the rest of this procedure loads — everything below is identical in shape across
   clients, only the exact commands and file conventions differ, and those live in
   the adapter, never in this file.
   - **Found** → use `repo` as the repo root, `client` to pick the adapter, and
     `collectionPath` for every step below. `confluence` is optional; its absence
     just means step 7 is skipped.
   - **Not found, but the current directory has a recognizable collection** (a
     `bruno/`-style folder, a `*.postman_collection.json`, or an Insomnia export) →
     infer the client from whichever of those is present, use the cwd as repo root,
     default environment `demo`, and skip the Confluence step (nothing to publish to
     without config).
   - **Not found and cwd has no collection** → ask the user which repo/collection/tool
     to run against rather than guessing.

1. **Load the resolved adapter** from the table above and follow it for every
   tool-specific detail in the steps below — this file only describes the shared
   shape of each step.

2. **Parse the rest of the request.** If it names a folder/area under the
   collection (e.g. "content", "auth/verify-otp"), scope both the run and the report
   to that folder. If it names an environment ("local", "demo"), use that; otherwise
   default per step 0.

3. **Export the collection**, per the adapter's export instructions, so the user has
   a file they can re-import into the matching desktop app. Report the output path.

4. **Check the target environment.** For a local-style environment, verify the
   expected localhost URL is reachable (e.g. a short `curl -o /dev/null -w
   "%{http_code}"` against any known route) before running anything; if it isn't,
   tell the user and ask whether to fall back to the default remote environment
   rather than running a suite that will fail uniformly on connection errors. A
   public remote environment is still worth a quick reachability check, but failure
   there is a real signal, not an environment problem.

5. **Run the suite** with the adapter's CLI invocation, scoped to the full
   collection or the folder from step 2. Capture the per-request/assertion results
   and the summary the CLI prints.

6. **Investigate any failure** before reporting: show which assertion failed, the
   actual status/response, and whether the adapter's per-case caveat convention (or
   the product's `api.knownCaveats`) names a precondition (wrong environment, wrong
   order, expired state) that explains it. Don't just report a number.

7. **Write the report** using [report-template.md](./references/report-template.md),
   filled with this run's real numbers, current commit (`git rev-parse --short HEAD`,
   run in the repo root) and branch, the environment used, which client/tool ran the
   suite, and a Notes section that includes any caveats found in step 6 or flagged by
   the adapter/`api.knownCaveats` for cases that ran. Present it in a fenced code
   block so it's a clean paste into Jira.

8. **If the product's config has an `api.confluence` block**, refresh that page's
   `lastUpdate` and attach the zip, following
   [confluence-publish.md](./references/confluence-publish.md) exactly (identifiers
   come from config, not from this file). Do this regardless of whether the tests
   passed — it's a timestamp and a file, not a test result. Give the user the page
   link when done. If there's no `confluence` block, skip this step silently — don't
   ask the user to set one up unless they bring it up.
