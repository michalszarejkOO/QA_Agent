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
     product's default integration branch (commonly `demo` or `main`), and diff
     that instead. If the local checkout is behind the remote branch containing the
     merge, don't just test against a stale local checkout — resolve the real merged
     state (e.g. via `git fetch` and diffing against the remote branch, or a
     throwaway worktree) rather than silently testing old code.
4. If the ticket's description and the actual shipped code disagree on scope (a
   field, a validation rule, a whole case the ticket describes but the code doesn't
   implement), that's a finding for the report's Notes and a candidate for Step 5's
   bug-report draft — not something to quietly test around.

## Step 2: Resolve the latest collection

The committed-to-git collection is not necessarily the latest one. Prior sessions
may have built out collection cases and pushed them straight to the product's
Confluence tracker page as a zip attachment without committing to git — this has
happened before and left richer, more current coverage sitting only on Confluence
while the repo checkout lagged behind.

1. If the product's config has an `api.confluence` block, look for an
   attachment-capable Confluence tool in this session (an upload/download tool, not
   just page CRUD — page-only tools can't read attachment bytes). If one exists,
   download the attached collection zip and extract it.
2. Diff the extracted collection against the local repo checkout's collection
   directory. If they differ, treat the Confluence version as the base for Steps 3–4
   below, and tell the user about the divergence (what's newer where) rather than
   picking one silently.
3. If no attachment-capable tool is available this session, say so explicitly and
   fall back to the local repo checkout as the base — call this out as a real
   limitation of the current session's tool access, not a design choice, so the user
   knows the run may be working from a stale collection.
4. Also check for **uncommitted local changes** to the collection (`git status` in
   the repo) before assuming the committed state is current — uncommitted
   restructuring or additions from a prior session are common here and must not be
   discarded or ignored.

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

## Step 4: Run against `demo`, always

Ticket mode always tests against the `demo` environment, never `local` and never
whatever `api.defaultEnvironment` happens to say, unless the user's own message for
this run explicitly names a different environment. This is because `demo` is the
environment the ticket, the Confluence tracker, and other stakeholders can all
verify against — a `local`-only result isn't shareable evidence for a ticket.

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

## Step 6: Always publish the collection and environment back to Confluence

Whenever `api.confluence` is configured for the product, finish by re-uploading:

- The collection, including any cases generated in Step 3.
- The refreshed environment file (if the product uses one, e.g. a `-populated`
  variant with live-captured values), per `confluence-publish.md`.
- The `lastUpdate` panel with the current commit/branch.

This is mandatory in ticket mode whenever the config exists — independent of
whether the tests passed, and not something to skip because the run "already has
enough evidence." If no attachment-capable tool is available this session (see Step
2), say so plainly here too rather than silently completing a partial publish.
