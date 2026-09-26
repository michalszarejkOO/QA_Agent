---
name: testing-api
description: Runs a repo's API test collection — Bruno, Postman, or Insomnia — against a live environment via that tool's CLI, exports the collection to a zip the user can download and import into the matching desktop app, optionally refreshes a lastUpdate timestamp on a Confluence tracker page and attaches that zip, and produces a Jira-comment-ready pass/fail report. When the request is driven by a specific backend Jira ticket, switches to ticket mode: reads the ticket and its PR/branch for context, always tests against `demo`, generates full scenario coverage (not just happy path) for any endpoint the collection doesn't already cover, treats the Confluence-attached collection as the latest version, and closes by preparing (never auto-posting) a Jira comment and any bug reports for the user's approval. Use when asked to test the API, run the API test suite, verify endpoints are working, export/re-export an API collection, QA/test a backend Jira ticket, or produce a test summary/report for a Jira ticket, for any product with a Bruno, Postman, or Insomnia collection — not tied to one repo or one tool.
when_to_use: "Trigger on: 'przetestuj API', 'uruchom testy API/bruno/postman/insomnia', 'sprawdź czy endpointy działają', 'wygeneruj raport testów do jiry', 'wyeksportuj kolekcję', 'run the API tests', 'test this endpoint', 'export the collection', 'test/QA this backend ticket', a Jira ticket URL/ID for a [BE] or backend-only ticket, or any request to verify API behavior using a committed collection. Product-agnostic: resolve which repo/collection/tool via the environments config (see step 0) or ask if it can't be resolved."
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
  it if the user explicitly asks for new test cases. **Exception: ticket mode**
  (see [ticket-driven-testing.md](./references/ticket-driven-testing.md)) — when the
  request names a specific backend ticket, the ask to test that ticket *is* the ask
  for new test cases covering it, so generate what's missing before running.
- Requires network access to the target environment and whatever runtime the
  resolved adapter needs (`npx`/Node for Bruno and Postman; Node for Insomnia's
  `inso`). If either is unavailable, say so — do not fabricate a result.
- The Confluence-publish step (step 7) only runs for a product whose environment
  config actually declares an `api.confluence` block. No config, no publish step —
  just export, run, and report. In ticket mode this step is mandatory whenever that
  block exists (see rule table) — never silently skip it there.

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

### Additional rules — ticket mode only

Load [ticket-driven-testing.md](./references/ticket-driven-testing.md) whenever the
request names or links a specific backend ticket, and follow these on top of the
rules above:

| Severity | Rule |
| --- | --- |
| MUST | Always test against the `demo` environment — never `local`, and never a different `api.defaultEnvironment` — unless the user's message explicitly names another environment for this run. |
| MUST | Before doing anything else, read the ticket's acceptance criteria and its linked PR's diff (or the merged feature branch found by the repo's ticket-key naming convention, if no PR is linked) so the scenarios generated actually target what changed. |
| MUST | Treat the collection currently attached to the product's Confluence tracker page as the latest version, not whatever's in the local repo checkout — diff the two and flag any divergence to the user rather than silently picking one. |
| MUST | Generate full scenario coverage for the ticket's endpoint(s) before executing anything, if the resolved collection doesn't already have it: happy path(s), validation/boundary cases, auth cases (missing/invalid/wrong-role token), and business-logic edge cases — not just the happy path. Follow the resolved adapter's existing naming/`docs:`/assertion conventions. |
| MUST | After the report, always prepare a Jira-comment-ready block and explicitly ask the user whether to post it to the ticket now or just keep it as copy-pasteable text — never post it automatically. |
| MUST | If any bug, scope mismatch, or discrepancy is found, draft a bug report (Title / Steps to reproduce / Expected / Actual) for each and explicitly ask the user whether to file it on the ticket or just keep it as a copy-pasteable draft — never file it automatically. |
| MUST | Always finish by re-uploading the (possibly extended) collection and refreshed environment file to the product's Confluence tracker page and refreshing `lastUpdate`, whenever `api.confluence` is configured — mandatory in ticket mode, not conditional on results or on remembering to ask. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [adapters/bruno.md](./references/adapters/bruno.md) | `api.client` is `"bruno"` | Collection layout, `docs:` block convention, export/run commands |
| [adapters/postman.md](./references/adapters/postman.md) | `api.client` is `"postman"` | Collection/environment JSON shape, per-request description convention, Newman export/run commands |
| [adapters/insomnia.md](./references/adapters/insomnia.md) | `api.client` is `"insomnia"` | Export shape, `inso` CLI invocation — flag as less battle-tested, confirm syntax against `inso --help` before relying on it |
| [report-template.md](./references/report-template.md) | Generating the final report, every run | The exact Jira-comment template (header fields, results table, coverage bullets, Notes) |
| [confluence-publish.md](./references/confluence-publish.md) | Updating the tracker page, every run where the product config declares one | Reading cloudId/space/folder/title/attachment name from config, the generate-body script, find-or-create/update procedure, attaching the exported zip |
| [ticket-driven-testing.md](./references/ticket-driven-testing.md) | The request names or links a specific backend ticket | Gathering ticket/PR context, resolving the Confluence attachment as the latest collection, generating full scenario coverage, and the ask-before-posting comment/bug-report step |

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
     "knownCaveatsFile": "<filename, resolved relative to this same environments/ dir, of a fuller markdown doc — use this instead of/alongside knownCaveats when the caveat list is long enough that keeping it as JSON strings risks drifting out of sync with a richer doc>",
     "confluence": {
       "cloudId": "<site>",
       "spaceKey": "<space>",
       "parentId": "<folder page id>",
       "pageTitle": "<fixed page title>",
       "attachmentName": "<fixed zip filename>",
       "secondaryAttachments": [
         { "name": "<fixed filename>", "sourcePath": "<path relative to repo root>" }
       ],
       "envRefreshProcedure": "<optional filename, resolved relative to this same environments/ dir, of a doc describing how to mint live values into a secondaryAttachments file before export>"
     }
   }
   ```
   `knownCaveatsFile`, `secondaryAttachments`, and `envRefreshProcedure` are all
   optional — most products need none of them. See
   [confluence-publish.md](./references/confluence-publish.md) for how the last two
   are used, and [adapters/bruno.md](./references/adapters/bruno.md) for
   `knownCaveatsFile`.
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
   a file they can re-import into the matching desktop app. If the product's config
   has `api.confluence.attachmentName`, pass it as the export's destination filename
   (e.g. `~/Desktop/<attachmentName>`) so repeat exports land under the same
   predictable name instead of whatever the adapter's own default happens to be —
   otherwise use the adapter's default. Report the output path.

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

## Procedure — ticket mode

Follow this instead of (really: layered onto) the generic procedure whenever the
request names or links a specific backend ticket (e.g. "test MWA-510", a Jira URL
for a `[BE]`/backend-only ticket). Full detail for each numbered step lives in
[ticket-driven-testing.md](./references/ticket-driven-testing.md); this is the
ordering.

T0. **Gather ticket context first.** Fetch the ticket (verify the right Jira
    connector reaches its site with `getAccessibleAtlassianResources` before
    trusting any cached mapping — it drifts) and read its acceptance criteria. Find
    its linked PR and diff it; if none is linked, find the merged feature branch by
    this repo's ticket-key branch convention and diff that instead.

T1. **Resolve the product/client/config** as step 0 above, then resolve the *latest*
    collection specifically: fetch whatever is currently attached to the product's
    Confluence tracker page (if `api.confluence` is configured) and diff it against
    the local repo checkout. Use the Confluence version as the base for everything
    below; tell the user about any divergence rather than silently picking one. If
    no attachment-reading tool is available this session, say so plainly and fall
    back to the local repo checkout, flagging that as a limitation, not a silent
    substitution.

T2. **Check coverage for the ticket's endpoint(s)** against that resolved
    collection. If it's missing entirely, or only has a thin/assertion-less
    placeholder, generate a full set of cases before running anything — happy
    path(s), validation/boundary cases, auth cases, and business-logic edge cases —
    following the resolved adapter's existing naming/`docs:`/assertion conventions.

T3. **Run steps 1 and 3–6 of the generic procedure** (load adapter, export, check
    `demo` reachability, run the suite, investigate failures) — but environment is
    always `demo` in ticket mode, never the request's or config's default if that
    would mean `local`.

T4. **Write the report** (generic step 7), then **prepare the Jira comment** and
    **ask the user** whether to post it to the ticket now or keep it as
    copy-pasteable text.

T5. **If any bug, scope mismatch, or discrepancy surfaced**, draft a bug report per
    case (Title / Steps to reproduce / Expected / Actual) and ask the user whether
    to file it on the ticket or keep it as a copy-pasteable draft.

T6. **Always finish by publishing to Confluence** (generic step 8) whenever
    `api.confluence` is configured — re-upload the (possibly extended) collection
    and the refreshed environment file, not just the timestamp. This step is
    mandatory in ticket mode, not conditional on results.
