# testing-api: the run (steps 1-7)

Read by the subagent that runs the suite (SKILL.md, "Where a run happens"),
right after SKILL.md, and by the main conversation when it exports or runs
without a subagent. Step 0 (setup and config) and step 8 (publishing) stay in
SKILL.md; its rules apply here too. In ticket mode,
[ticket-driven-testing.md](./ticket-driven-testing.md) sets the order and
says which of these steps it runs.

## Rules for the run

| Severity | Rule |
| --- | --- |
| MUST | In generic mode, test the staging-like branch's environment (step 2, [target-branch.md](../../testing-apps/references/target-branch.md)) unless the user names another one. Fall back to `api.defaultEnvironment` only when no branch can be resolved. A `local`-type environment requires the app running locally — check reachability first and say clearly if it's down, rather than letting the run fail with a confusing connection error. |
| MUST | Run the resolved adapter's CLI scoped to the folder implied by the request — the whole collection by default, or a specific subfolder when the user names an endpoint or area. With `api.testsCollection`, the collection a run executes is the tests collection; the main one only when the user asks ([config-fields.md](./config-fields.md), "The tests collection"). |
| MUST | Before writing the report, check the resolved adapter's per-case caveat convention for any test case that looks order- or state-dependent, including any product-specific caveats listed in that product's config (`api.knownCaveats`), and surface real caveats in the report's Notes — a clean pass/fail count that hides a non-representative test is misleading evidence. |
| MUST | In generic (non-ticket) mode, when an executed folder/endpoint has only happy-path cases — no validation/boundary, auth, or business-logic cases — flag that gap in the report's Notes. This is an observation only: never generate cases to fill it in generic mode, that stays scoped to ticket mode's step T2. A clean "N/N PASS" next to thin coverage is misleading on its own. |
| MUST | Use the report template in [report-template.md](./report-template.md) verbatim in structure — same headers, same table shape — so reports stay consistent across runs, products, and tools. Fill it from the actual CLI output, never from memory of a previous run. |
| NEVER | Claim a PASS the CLI did not report. If any request fails, show the failing assertion(s) and response detail, and reflect the real status in the report. |

## Keeping the user informed

Before each notable step, write one short line saying what you're about to do:
resolving the config, fetching the ticket or PR, downloading the published
collection, generating new cases, exporting, running the suite, publishing. Say which environment and folder a run targets before starting it.
In a subagent nothing reaches the user before you return, so keep the same
lines as a run log and return it with the summary.

End every run with a point-list summary, after the report and drafts:

- **Done:** each thing completed (cases generated, suite run with pass/fail
  counts, export paths, what was published where, with its new version).
- **Not done / skipped:** each step that wasn't done, with its reason (no
  publish target, environment unreachable, user chose not to post or
  publish, and so on). If nothing was skipped, write "Nothing skipped."
  In ticket mode, also say that cases generated this run are only in
  `<run folder>/published-collection/` (and wherever it was published), not in
  the repo checkout.
- **Proposed additions to the project skill:** each new product-specific finding
  (a stateful case, an environment quirk, a misleading status code), worded as
  the line to add to `<projectSkill>/SKILL.md`, or "None". Add them only after
  the user approves, and never to this skill or Claude's memory.

## References for the run

| Reference | Load when | Covers |
| --- | --- | --- |
| [adapters/bruno.md](./adapters/bruno.md) | `api.client` is `"bruno"` | Collection layout, `docs:` block convention, export/run commands |
| [adapters/postman.md](./adapters/postman.md) | `api.client` is `"postman"` | Collection/environment JSON shape, per-request description convention, Newman export/run commands, syncing the repo files with the Postman app before publishing (the `postman-sync` agent), which variable values leave the app |
| [adapters/insomnia.md](./adapters/insomnia.md) | `api.client` is `"insomnia"` | Export shape, `inso` CLI invocation — flag as less battle-tested, confirm syntax against `inso --help` before relying on it |
| [report-template.md](./report-template.md) | Generating the final report, every run | The exact Jira-comment template (header fields, results table, coverage bullets, Notes) |
| [target-branch.md](../../testing-apps/references/target-branch.md) | Generic mode, when the request names no environment | Picking the staging-like branch (user, config `targetBranch`, detection from merged MRs), mapping it to a collection environment, using recent MRs as context |

## Steps 1-7

1. **Load the resolved adapter** from the table in "References for the run" and follow it for every
   tool-specific detail in the steps below — this file only describes the shared
   shape of each step.

2. **Parse the rest of the request.** If it names a folder/area under the
   collection (e.g. "content", "auth/verify-otp"), scope both the run and the report
   to that folder. If it names an environment ("local", "demo"), use that.
   Otherwise, in generic mode, resolve the staging-like branch and its environment
   per [target-branch.md](../../testing-apps/references/target-branch.md): config
   `targetBranch`, then detection from merged MRs, then `api.defaultEnvironment`.
   Run the collection as it is on that branch (a fresh worktree at
   `origin/<branch>`, under `<workDir>/worktrees/`), not the local checkout's branch. Carry over uncommitted
   collection changes only if the user says to. Use the recent MRs the script
   lists as the run's context. **No `repo`:** there is no collection branch;
   run the downloaded published collection on the environment the user names,
   otherwise `api.defaultEnvironment`. Ticket mode skips this; it uses the ticket
   environment (SKILL.md, "Ticket mode") and the ticket's own
   branch.

3. **Export the collection**, per the adapter's export instructions, so the user has
   a file they can re-import into the matching desktop app. Always pass a
   destination inside the run folder, under the fixed name
   [publishing.md](./publishing.md) step 1 gives, so repeat exports
   keep the same predictable name. The collection zip never holds environments or
   `.env` files; export the environments as their own zip (part `environments`)
   too. Export from the folder the run uses: the worktree from step 2 in generic
   mode, or `<run folder>/published-collection/` (as the repo root) in ticket
   mode and in any run without `repo`. Report the output paths and which folder they came from.

4. **Check the target environment.** For a local-style environment, verify the
   expected localhost URL is reachable (e.g. a short `curl -o /dev/null -w
   "%{http_code}"` against any known route) before running anything; if it isn't,
   tell the user and ask whether to fall back to the default remote environment
   rather than running a suite that will fail uniformly on connection errors. A
   public remote environment is still worth a quick reachability check, but failure
   there is a real signal, not an environment problem.

5. **Run the suite** with the adapter's CLI invocation, scoped to the full
   collection or the folder from step 2: the tests collection when the config
   has `testsCollection`, otherwise the main collection (with several main
   files, config-fields.md, "Several main collection files"). Capture the per-request/assertion results
   and the summary the CLI prints.

6. **Investigate any failure** before reporting: show which assertion failed, the
   actual status/response, and whether the adapter's per-case caveat convention (or
   the product's `api.knownCaveats`) names a precondition (wrong environment, wrong
   order, expired state) that explains it. Don't just report a number.
   Also check each executed folder/endpoint's case set for thinness — happy-path
   only, no validation/auth/business-logic cases — and flag any gap found in the
   report's Notes (step 7). Flag only; don't generate cases here, that's ticket
   mode's job (ticket-driven-testing.md, Step 3).

7. **Write the report** using [report-template.md](./report-template.md),
   filled with this run's real numbers, current commit (`git rev-parse --short HEAD`,
   run in the repo root) and branch, or the published version when the run used
   the published collection (report-template.md, "Rules for filling it in"),
   the environment used, which client/tool ran the
   suite, and a Notes section that includes any caveats found in step 6 or flagged by
   the adapter/`api.knownCaveats` for cases that ran. Present it in a fenced code
   block so it's a clean paste into Jira, and save the same text as
   `<run folder>/report.md`.
