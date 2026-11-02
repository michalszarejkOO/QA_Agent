# Testing a backend ticket

Load this when the request names or links a specific backend ticket (a Jira ID or
URL, e.g. "test MWA-510", "QA the backend for TICKET-123") rather than a bare "run
the API tests" request. It layers on top of the generic procedure in SKILL.md —
everything not covered here (adapter mechanics, the report template, the
publishing mechanics) is unchanged.

## Rules

These apply on top of SKILL.md's "Non-negotiable rules":

| Severity | Rule |
| --- | --- |
| MUST | Test only on an environment the user named or confirmed for this run. If the message names one, use it. Otherwise, before running anything, ask: with `api.ticketEnvironment` set, propose it and ask to confirm (the change may be deployed somewhere else); without it, ask which environment to use. Offer the collection's environment names and, if known, where the ticket's PR was merged. Never assume `demo`, never fall back to `api.defaultEnvironment` silently, never pick a `local`-type one unless the user names it. See Step 4 below. |
| MUST | Before doing anything else, read the ticket's acceptance criteria and its linked PR's diff (or the merged feature branch found by the repo's ticket-key naming convention, if no PR is linked) so the scenarios generated actually target what changed. |
| MUST | Treat the published collection (1Password or Confluence, per `api.publish.collection`) as the latest version, not whatever's in the local repo checkout — diff the two and flag any divergence to the user rather than silently picking one. Download it into `<run folder>/published-collection/` and work only from there: new cases, the run and the export all use that folder. |
| MUST | Generate full scenario coverage for the ticket's endpoint(s) before executing anything, if the resolved collection doesn't already have it: happy path(s), validation/boundary cases, auth cases (missing/invalid/wrong-role token), and business-logic edge cases — not just the happy path. Follow the resolved adapter's existing naming/`docs:`/assertion conventions. |
| MUST | After the report, always prepare a Jira-comment-ready block and explicitly ask the user whether to post it to the ticket now or just keep it as copy-pasteable text — never post it automatically. |
| MUST | If any bug, scope mismatch, or discrepancy is found, draft a bug report (Title / Steps to reproduce / Expected / Actual) for each and explicitly ask the user whether to file it on the ticket or just keep it as a copy-pasteable draft — never file it automatically. |
| MUST | Always finish by offering to publish the (possibly extended) collection and the refreshed environments to their targets, whenever the product has one — never skipped in ticket mode, not conditional on results. The upload itself still waits for the version check and the user's yes (rules above). |

## Order

Follow this instead of (really: layered onto) SKILL.md's generic procedure.
Full detail for each numbered step is in the Steps below; this is the
ordering.

T0. **Gather ticket context first.** Fetch the ticket (verify the right Jira
    connector reaches its site with `getAccessibleAtlassianResources` before
    trusting any cached mapping — it drifts) and read its acceptance criteria and
    comments (Step 1 below). Find
    its linked PR and diff it; if none is linked, find the merged feature branch by
    this repo's ticket-key branch convention and diff that instead.

T1. **Resolve the product/client/config** as SKILL.md step 0, then resolve the *latest*
    collection specifically: download the published one (wherever
    `api.publish.collection` points) into `<run folder>/published-collection/` and
    diff it against the local repo checkout (download as
    [publishing.md](./publishing.md), "Downloading the published
    collection", describes). That folder is the
    collection for everything below: new cases go there, the suite runs from it and
    the export zips it. Tell the user about any divergence rather than silently
    picking one. If
    the download isn't possible this session, say so plainly and fall
    back to the local repo checkout, flagging that as a limitation, not a silent
    substitution.

T2. **Check coverage for the ticket's endpoint(s)** against that resolved
    collection. If it's missing entirely, or only has a thin/assertion-less
    placeholder, generate a full set of cases before running anything — happy
    path(s), validation/boundary cases, auth cases, and business-logic edge cases —
    following the resolved adapter's existing naming/`docs:`/assertion conventions.

T3. **Run SKILL.md steps 1 and 3–6** (load adapter, export, check
    reachability, run the suite, investigate failures) — but the environment is
    the one the user named or confirmed for this run (Step 4 below), never a `local`-type one unless the user names it.

T4. **Write the report** (SKILL.md step 7), then **prepare the Jira comment** and
    **ask the user** whether to post it to the ticket now or keep it as
    copy-pasteable text.

T5. **If any bug, scope mismatch, or discrepancy surfaced**, draft a bug report per
    case (Title / Steps to reproduce / Expected / Actual) and ask the user whether
    to file it on the ticket or keep it as a copy-pasteable draft.

T6. **Always finish by offering to publish** (SKILL.md step 8) whenever the product
    has a publish target — the (possibly extended) collection from
    `<run folder>/published-collection/` and the refreshed environments. Never skip
    offering it in ticket mode, whatever the results; publish only after the user's
    yes, given after the version check in
    [publishing.md](./publishing.md), step 4.

## In a subagent: where the run stops to ask

Ticket mode runs in a subagent (SKILL.md, "Where a run happens"), which can't
ask the user. Stop and return the questions, then continue when the main
conversation passes the answers back:

1. **After Steps 1 and 2** (ticket, PR, published collection downloaded and
   compared), stop once with everything that needs the user:
   - the environment (Step 4), unless the brief names one: propose
     `api.ticketEnvironment` if set, list the collection's environment names,
     and say where the PR or branch was merged;
   - uncommitted local collection changes (Step 2, item 5): copy them into
     `published-collection/` or not;
   - any divergence between the published and the local collection (Step 2,
     item 2), as information.
   Nothing to ask (environment in the brief, no local changes)? Don't stop.
2. **After the report and drafts** (T4–T5), return them without asking: the
   main conversation asks about the comment, each bug and publishing (T6).
3. **Anything else the steps say to ask** (an unreachable environment, two
   items with the same name): stop and return the question with its options.

## Why this mode exists

The generic procedure treats the collection as fixed and never invents scenarios.
That's right for "just run the suite." It's wrong for "test this ticket" — a ticket
implies a specific endpoint/change that the collection may not cover yet, and the
user asking to test it *is* the ask for whatever cases that requires. This mode
exists to close that gap without weakening the generic rule for every other request.

## Step 1: Ticket and PR/branch context

1. Fetch the ticket. Resolve which Jira connector currently reaches its site with
   `getAccessibleAtlassianResources` before trusting any cached
   connector-to-site mapping (e.g. a `reference_atlassian_connectors`-style memory
   note, or a product config's `jira.connector` field) — this mapping has been
   observed to drift between sessions without the user reconfiguring anything.
2. Read the ticket's acceptance criteria/description in full, and every comment
   (they often clarify or change the criteria), as
   [connectors.md, "Reading a ticket you're going to test"](../../configure-project/references/connectors.md#reading-a-ticket-youre-going-to-test)
   says: `view: "evidence"`, never `fields` on `getJiraIssue`. This is what the
   generated scenarios in Step 3 must actually target — not a generic guess at what
   the endpoint "probably" does.
3. Find the linked PR (dev panel / remote issue links) and diff it for the actual
   shipped behavior.
   - **No PR linked** → look for a merged feature branch following this repo's
     ticket-key branch convention (e.g. `feature-<TICKET-KEY>`) against the
     product's default integration branch (e.g. `demo`, `stage` or `main`), and diff
     that instead. If the local checkout is behind the remote branch containing the
     merge, don't just test against a stale local checkout — resolve the real merged
     state rather than silently testing old code.
   - **Read code without moving the user's checkout.** `git fetch`, then read the
     remote branch in place: `git show origin/<branch>:<path>`, `git diff`,
     `git log`, `git grep <pattern> origin/<branch>`. When you need the files on
     disk, add a throwaway worktree under `<workDir>/worktrees/`. Never
     `checkout`, `switch`, `reset` or `pull` in the user's clone: it may hold
     their work, and a detached HEAD left behind confuses the next person.
4. Before going on, settle the environment with the user as Step 4 describes, using
   where the PR or branch was merged as the hint.
5. If the ticket's description and the actual shipped code disagree on scope (a
   field, a validation rule, a whole case the ticket describes but the code doesn't
   implement), that's a finding for the report's Notes and a candidate for Step 5's
   bug-report draft — not something to quietly test around.

## Step 2: Resolve the latest collection

The committed-to-git collection is not necessarily the latest one. Prior sessions
may have built out collection cases and published them (to 1Password or the
product's Confluence tracker page) without committing to git — this has happened
before and left richer, more current coverage sitting only in the published copy
while the repo checkout lagged behind.

1. If the product's config names a target for the collection (`api.publish`, or an
   `api.confluence` block in an older config), download it as
   [publishing.md](./publishing.md), "Downloading the published collection",
   describes. It is extracted into `<run folder>/published-collection/`, and the
   version it came from is recorded in `<run folder>/published-base.json`. On
   Confluence the download runs through `discover`, so it won't show up as a tool
   of its own: don't take its absence from the tool list as "no download tool".
2. Diff `<run folder>/published-collection/<collectionPath>` against the local
   repo checkout's collection directory, and tell the user about any divergence
   (what's newer where) rather than picking one silently.
3. From here on, `<run folder>/published-collection/` is the collection, used as
   the repo root: Step 3 adds cases there, Step 4 runs the suite from there, and
   the export (SKILL.md step 3) zips it. The repo checkout is only for comparing;
   don't add the generated cases to it unless the user asks.
4. If the download isn't possible (no Atlassian server for that site in this
   session, `op` not installed or not signed in, or the page, file or item is
   missing), say so explicitly and fall back to
   the local repo checkout as the base — call this out as a real limitation of
   the current session's tool access, not a design choice, so the user
   knows the run may be working from a stale collection.
5. Also check for **uncommitted local changes** to the collection (`git status` in
   the repo) before assuming the committed state is current — uncommitted
   restructuring or additions from a prior session are common here and must not be
   discarded or ignored. Show them with the divergence in item 2, and copy them
   into `published-collection/` only if the user says to.

## Step 3: Generate full scenario coverage

Check whether the resolved collection (Step 2) already has adequate cases for the
ticket's endpoint(s). "Adequate" means real assertions exist (not just a request
with no `runtime.assertions`/equivalent) and more than a single happy-path case.

If coverage is missing or thin, generate a full set before running anything,
following the resolved adapter's existing naming/`docs:`/assertion conventions (see
`adapters/bruno.md` etc., and any repo-local convention doc such as
`test-case-conventions.md` if one exists) — do not invent a different structure.
Cover, at minimum:

- **Happy path(s)** — including any input variants the ticket's acceptance criteria
  call out (e.g. multiple valid enum combinations), not just one.
- **Validation/boundary cases** — empty/missing required fields, invalid enum
  values, malformed types, boundary lengths.
- **Auth cases** — missing token, invalid/expired token, wrong-role token if the
  endpoint is role-gated.
- **Business-logic edge cases** — anything the ticket or the code implies about
  state (already-done actions, conflicting prior state, idempotency, single-use
  tokens/codes) — read the diff from Step 1 for what the implementation actually
  guards against, don't guess.

If the endpoint depends on a stateful chain (an OTP flow, a token exchange) to
reach a real success case, build that chain using the collection's existing
patterns (e.g. `before-request`/`after-response` scripts capturing runtime
variables) rather than a one-off manual value — see how prior cases in the same
collection solved the same problem before inventing a new mechanism.

## Step 4: Run on an environment the user named or confirmed

A ticket's change can be deployed to a different environment than usual (a hotfix
on `uat`, a feature still only on `development`), so ticket mode never runs on an
environment the user hasn't named or confirmed for this run:

1. **The user's message names one** ("test IMS-123 on uat") → use it.
2. **The config has `api.ticketEnvironment`** → propose it and ask the user to
   confirm before running anything: "Test on `<env>`? The change may be deployed
   elsewhere."
3. **No `api.ticketEnvironment`** → ask which environment to test on. Don't
   fall back to `api.defaultEnvironment` silently; it's for plain runs, and one
   product's config files can each have a different one.

When asking, list the collection's environment names, and say where the ticket's
PR or feature branch was merged if Step 1 found it (map the branch to an
environment per [target-branch.md](../../testing-apps/references/target-branch.md)).
Ask right after Step 1, so the rest of the run doesn't stop for it. Never assume an
environment called `demo` exists, and never use a `local`-type one unless the user
names it. The environment should be the shared one the ticket, the published
collection and other stakeholders can verify against; a `local`-only result isn't
shareable evidence for a ticket.

Run the collection from the folder Step 2 settled on
(`<run folder>/published-collection/` when the download worked), so the result
is for the same collection that gets exported and published.

## Step 5: Comment and bug-report drafts — always ask, never auto-post

After the report is written:

1. Prepare the Jira-comment-ready block per `report-template.md`, "Ticket comment
   (ticket mode)": a short business summary, what was tested, the request and
   response for each changed endpoint, and any issues. Ask the user
   explicitly: post it to the ticket now, or keep it as copy-pasteable text? Do not
   post without that answer, even if the run passed cleanly.
2. For each bug, scope mismatch, or discrepancy found (including a collection gap
   discovered along the way, e.g. "this endpoint's success path can't currently be
   reached"), draft a bug report (Title / Steps to reproduce / Expected / Actual).
   Ask the user explicitly: file it on the ticket, or keep it as a copy-pasteable
   draft? Do not file without that answer. Files that go with a comment or a
   bug go up as `~/.claude/skills/creating-jira-tickets/references/jira-attachments.md`
   says, from where the run saved them.

## Step 6: Always offer to publish the collection and environments

Whenever the product has a publish target, finish by preparing an upload of:

- The collection from `<run folder>/published-collection/`, including any cases
  generated in Step 3.
- The environments, including a refreshed live-populated file if the product uses
  one (`envRefreshProcedure`).
- On Confluence, the `lastUpdate` panel with the current commit/branch.

Then follow [publishing.md](./publishing.md): scan what goes to Confluence, check
whether the published version is still the one recorded in `published-base.json`,
show the user what goes where, and publish only after their yes. If someone
published a newer version during the run, say so and offer to take it as the base
and run again.

Reaching this step is mandatory in ticket mode whenever a target exists —
independent of whether the tests passed, and not something to skip because the run
"already has enough evidence." If the target can't be reached this session (no
Atlassian server for the site, see `confluence-publish.md`, "Which server to use";
or `op` not signed in), say so plainly here too rather than silently completing a
partial publish.
