# Testing a backend ticket

Load this when the request names or links a specific backend ticket (a Jira ID or
URL, e.g. "test MWA-510", "QA the backend for TICKET-123") rather than a bare "run
the API tests" request. It layers on top of the generic procedure in SKILL.md —
everything not covered here (adapter mechanics, the report template, the
Confluence-publish mechanics) is unchanged.

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
2. Read the ticket's acceptance criteria/description in full. This is what the
   generated scenarios in Step 3 must actually target — not a generic guess at what
   the endpoint "probably" does.
3. Find the linked PR (dev panel / remote issue links) and diff it for the actual
   shipped behavior.
   - **No PR linked** → look for a merged feature branch following this repo's
     ticket-key branch convention (e.g. `feature-<TICKET-KEY>`) against the
     product's default integration branch (e.g. `demo`, `stage` or `main`), and diff
     that instead. If the local checkout is behind the remote branch containing the
     merge, don't just test against a stale local checkout — resolve the real merged
     state (e.g. via `git fetch` and diffing against the remote branch, or a
     throwaway worktree) rather than silently testing old code.
4. Before going on, settle the environment with the user as Step 4 describes, using
   where the PR or branch was merged as the hint.
5. If the ticket's description and the actual shipped code disagree on scope (a
   field, a validation rule, a whole case the ticket describes but the code doesn't
   implement), that's a finding for the report's Notes and a candidate for Step 5's
   bug-report draft — not something to quietly test around.

## Step 2: Resolve the latest collection

The committed-to-git collection is not necessarily the latest one. Prior sessions
may have built out collection cases and pushed them straight to the product's
Confluence tracker page as a zip attachment without committing to git — this has
happened before and left richer, more current coverage sitting only on Confluence
while the repo checkout lagged behind.

1. If the product's config has an `api.confluence` block, download the attached
   collection zip as [confluence-publish.md](./confluence-publish.md), "Downloading
   the current collection", describes. It is extracted into
   `<run folder>/confluence-collection/`, and the version it came from is recorded
   in `<run folder>/confluence-base.json`. The download runs through `discover`, so
   it won't show up as a tool of its own: don't take its absence from the tool
   list as "no download tool".
2. Diff `<run folder>/confluence-collection/<collectionPath>` against the local
   repo checkout's collection directory, and tell the user about any divergence
   (what's newer where) rather than picking one silently.
3. From here on, `<run folder>/confluence-collection/` is the collection, used as
   the repo root: Step 3 adds cases there, Step 4 runs the suite from there, and
   the export (SKILL.md step 3) zips it. The repo checkout is only for comparing;
   don't add the generated cases to it unless the user asks.
4. If the download isn't possible (no Atlassian server for that site in this
   session, or the page or file is missing), say so explicitly and fall back to
   the local repo checkout as the base — call this out as a real limitation of
   the current session's tool access, not a design choice, so the user
   knows the run may be working from a stale collection.
5. Also check for **uncommitted local changes** to the collection (`git status` in
   the repo) before assuming the committed state is current — uncommitted
   restructuring or additions from a prior session are common here and must not be
   discarded or ignored. Show them with the divergence in item 2, and copy them
   into `confluence-collection/` only if the user says to.

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
names it. The environment should be the shared one the ticket, the Confluence
tracker and other stakeholders can verify against; a `local`-only result isn't
shareable evidence for a ticket.

Run the collection from the folder Step 2 settled on
(`<run folder>/confluence-collection/` when the download worked), so the result
is for the same collection that gets exported and published.

## Step 5: Comment and bug-report drafts — always ask, never auto-post

After the report is written:

1. Prepare the Jira-comment-ready block (per `report-template.md`). Ask the user
   explicitly: post it to the ticket now, or keep it as copy-pasteable text? Do not
   post without that answer, even if the run passed cleanly.
2. For each bug, scope mismatch, or discrepancy found (including a collection gap
   discovered along the way, e.g. "this endpoint's success path can't currently be
   reached"), draft a bug report (Title / Steps to reproduce / Expected / Actual).
   Ask the user explicitly: file it on the ticket, or keep it as a copy-pasteable
   draft? Do not file without that answer.

## Step 6: Always offer to publish the collection and environment back to Confluence

Whenever `api.confluence` is configured for the product, finish by preparing a
re-upload of:

- The collection from `<run folder>/confluence-collection/`, including any cases
  generated in Step 3.
- The refreshed environment file (if the product uses one, e.g. a `-populated`
  variant with live-captured values), per `confluence-publish.md`.
- The `lastUpdate` panel with the current commit/branch.

Then follow `confluence-publish.md`, step 4: check whether the page's version is
still the one recorded in `confluence-base.json`, show the user what goes where,
and publish only after their yes. If someone uploaded a newer version during the
run, say so and offer to take it as the base and run again.

Reaching this step is mandatory in ticket mode whenever the config exists —
independent of whether the tests passed, and not something to skip because the run
"already has enough evidence." If the session has no Atlassian server for that site
(see `confluence-publish.md`, "Which server to use"), say so plainly here too rather
than silently completing a partial publish.
