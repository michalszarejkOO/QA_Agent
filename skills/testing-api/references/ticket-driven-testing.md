# Testing a backend ticket

Load this when the request names or links a specific backend ticket (a Jira ID or
URL, e.g. "test MWA-510", "QA the backend for TICKET-123") rather than a bare "run
the API tests" request. It layers on top of the generic procedure in SKILL.md and run.md —
everything not covered here (adapter mechanics, the report template, the
publishing mechanics) is unchanged.

## Rules

These apply on top of the "Non-negotiable rules" in SKILL.md and "Rules for the run" in run.md:

| Severity | Rule |
| --- | --- |
| MUST | Test on the environment the user named for this run, else on `api.ticketEnvironment` per the `confirmTicketEnvironment` preference (`auto`: no question; `ask`: propose it and ask to confirm, the change may be deployed somewhere else); without `ticketEnvironment`, ask which environment to use. Offer the collection's environment names and, if known, where the ticket's PR was merged. Never assume `demo`, never fall back to `api.defaultEnvironment` silently, never pick a `local`-type one unless the user names it. See Step 4 below. |
| MUST | Before doing anything else, read the ticket's acceptance criteria and its linked PR's diff (or the merged feature branch found by the repo's ticket-key naming convention, if no PR is linked) so the scenarios generated actually target what changed. |
| MUST | Treat the published collection (per `api.publish.target`: the 1Password item, the package in `apiCollectionsFolder`, or the Confluence zip) as the latest version, not whatever's in the local repo checkout — diff the two and flag any divergence to the user rather than silently picking one. Download it into `<run folder>/published-collection/` and work only from there: new cases, the run and the export all use that folder. |
| MUST | Generate full scenario coverage for the ticket's endpoint(s) before executing anything, if the resolved collection doesn't already have it: happy path(s), validation/boundary cases, auth cases (missing/invalid/wrong-role token), and business-logic edge cases — not just the happy path. Follow the resolved adapter's existing naming/`docs:`/assertion conventions. |
| MUST | After the report, always prepare the Jira comment and show it in full; post it only per `postJiraComment` (`auto` posts, `ask` asks, `never` leaves the draft). |
| MUST | If any bug, scope mismatch, or discrepancy is found, draft a bug report (Title / Steps to reproduce / Expected / Actual) for each and show it in full; file it only per `fileBugs` (`auto` files unless it may be a duplicate, `ask` asks, `never` leaves the draft). |
| MUST | Always finish with the publish step whenever the product has a target — never skipped in ticket mode, not conditional on results. The run folder is staged right away; the upload waits for the version check and the user's yes, or `publishCollection: auto` with a clean check, and `apiCollectionsFolder` follows publishing.md, "The API collections folder". |

## Order

Follow this instead of (really: layered onto) the generic procedure (SKILL.md and run.md).
Full detail for each numbered step is in the Steps below; this is the
ordering.

T0. **Gather ticket context first** with the `reading-jira-tickets` skill: the
    ticket with its acceptance criteria and comments, and the linked PR or the
    merged feature branch with its diff (Step 1 below).

T1. **Resolve the product/client/config** as SKILL.md step 0, then resolve the *latest*
    collection specifically: download the published one (from where
    `api.publish.target` says) into `<run folder>/published-collection/` and
    diff it against the local repo checkout (download as
    [publishing.md](./publishing.md), "Downloading the published
    collection", describes). That folder is the
    collection for everything below: new cases go there, the suite runs from it and
    the package is built from it. Tell the user about any divergence rather than silently
    picking one. If
    the download isn't possible this session, say so plainly and fall
    back to the local repo checkout, flagging that as a limitation, not a silent
    substitution.

T2. **Check coverage for the ticket's endpoint(s)** against that resolved
    collection (its tests collection, when the config has `testsCollection`). If it's missing entirely, or only has a thin/assertion-less
    placeholder, generate a full set of cases before running anything — happy
    path(s), validation/boundary cases, auth cases, and business-logic edge cases —
    following the resolved adapter's existing naming/`docs:`/assertion conventions.

T3. **Run run.md steps 1 and 3–6** (load adapter, export, check
    reachability, run the suite, investigate failures) — but the environment is
    the one the user named or confirmed for this run (Step 4 below), never a `local`-type one unless the user names it.

T4. **Write the report** (run.md step 7), then **prepare the Jira comment**
    with the `writing-jira-comments` skill (the product's format from its
    project skill, or the default API template), shown in full.

T5. **If any bug, scope mismatch, or discrepancy surfaced**, draft a bug report per
    case (Title / Steps to reproduce / Expected / Actual), shown in full.

    Then post and file per `postJiraComment` and `fileBugs`
    ([preferences.md](../../configure-project/references/preferences.md), "After
    a test run"); in a subagent, only the `auto` ones (SKILL.md, "Where a run
    happens").

T6. **Always finish with the publish step** (SKILL.md step 8) whenever the
    product has a publish target — the package built from
    `<run folder>/published-collection/` with the refreshed environments. Never
    skip it in ticket mode, whatever the results; the upload comes after the
    version check in [publishing.md](./publishing.md), step 4, on the user's
    yes or with `publishCollection: auto`, and `apiCollectionsFolder` is
    written as publishing.md, "The API collections folder", says. Ask T4/T5's and this step's questions together,
    so the user answers once at the end; the project-skill lines come last.

## In a subagent: where the run stops to ask

Ticket mode runs in a subagent (SKILL.md, "Where a run happens"), which can't
ask the user. Stop and return the questions, then continue when the main
conversation passes the answers back:

1. **After Steps 1 and 2** (ticket, PR, published collection downloaded and
   compared), stop once with everything that needs the user:
   - the environment (Step 4), unless the brief names one or
     `confirmTicketEnvironment` is `auto` with `api.ticketEnvironment` set
     (then use it and say so): propose `api.ticketEnvironment` if set, list
     the collection's environment names, and say where the PR or branch was
     merged;
   - uncommitted local collection changes (Step 2, item 5): copy them into
     `published-collection/` or not;
   - any divergence between the published and the local collection (Step 2,
     item 2), as information.
   Nothing to ask (environment in the brief, no local changes)? Don't stop.
2. **After the report and drafts** (T4–T6), do the `auto` actions (post the
   comment, file the bugs, attach evidence, publish) and return the links and
   the remaining drafts without asking: the main conversation asks about the
   actions at `ask`, then the project-skill lines.
3. **Anything else the steps say to ask** (an unreachable environment, two
   items with the same name): stop and return the question with its options.

## Why this mode exists

The generic procedure treats the collection as fixed and never invents scenarios.
That's right for "just run the suite." It's wrong for "test this ticket" — a ticket
implies a specific endpoint/change that the collection may not cover yet, and the
user asking to test it *is* the ask for whatever cases that requires. This mode
exists to close that gap without weakening the generic rule for every other request.

## Step 1: Ticket and PR/branch context

1. **Read the ticket and its PR or branch** with the `reading-jira-tickets`
   skill (`~/.claude/skills/reading-jira-tickets/SKILL.md`; missing → stop and
   say QA_Agent needs an update): connector, the whole ticket with every
   comment, the PR or merged branch and its diff, and where it was merged. The
   acceptance criteria as the comments left them are what the scenarios in
   Step 3 target, not a guess at what the endpoint "probably" does.
2. When you need the code on disk, add a throwaway worktree under
   `<workDir>/worktrees/`; never move the user's checkout.
3. Before going on, settle the environment with the user as Step 4 describes, using
   where the PR or branch was merged as the hint.
4. If the ticket's description and the actual shipped code disagree on scope (a
   field, a validation rule, a whole case the ticket describes but the code doesn't
   implement), that's a finding for the report's Notes and a candidate for Step 5's
   bug-report draft — not something to quietly test around.

## Step 2: Resolve the latest collection

The committed-to-git collection is not necessarily the latest one. Prior sessions
may have built out collection cases and published them (to 1Password, the local
folder or the product's Confluence tracker page) without committing to git — this has happened
before and left richer, more current coverage sitting only in the published copy
while the repo checkout lagged behind.

1. If the product's config names a target (`api.publish.target`), download it as
   [publishing.md](./publishing.md), "Downloading the published collection",
   describes. It is extracted into `<run folder>/published-collection/`, and the
   version it came from is recorded in `<run folder>/published-base.json`. On
   Confluence the download runs through `discover`, so it won't show up as a tool
   of its own: don't take its absence from the tool list as "no download tool".
   With `target: "local"`, the package in `api.publish.apiCollectionsFolder` is the latest
   version and is extracted the same way.
2. Diff `<run folder>/published-collection/<collectionPath>` against the local
   repo checkout's collection directory, and tell the user about any divergence
   (what's newer where) rather than picking one silently. No `repo` in the
   config: skip this and item 5, there is nothing to compare with.
3. From here on, `<run folder>/published-collection/` is the collection, used as
   the repo root: Step 3 adds cases there, Step 4 runs the suite from there, and
   the package (run.md step 3) is built from it. The repo checkout is only for comparing;
   don't add the generated cases to it unless the user asks.
4. If the download isn't possible (no Atlassian server for that site in this
   session, `op` not installed or not signed in, or the page, file or item is
   missing), say so explicitly and fall back to
   the local repo checkout as the base — call this out as a real limitation of
   the current session's tool access, not a design choice, so the user
   knows the run may be working from a stale collection. No `repo` in the
   config: fall back to the package in `api.publish.apiCollectionsFolder` instead, as
   [publishing.md](./publishing.md), "When the download isn't possible",
   describes.
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

**Where the cases go.** With `api.testsCollection`
([config-fields.md](./config-fields.md), "The tests collection"):

- **Tests collection:** every generated case, under the main collection's domain
  folder for the endpoint (create it there if the tests collection doesn't have
  it yet), in a folder for the endpoint itself (`PUT /v1/users/me/phone`). Never a
  folder named after the ticket; each case's description names the ticket.
- **Main collection:** only when it has no request for the endpoint yet, add
  one: in the folder of its domain, named for what it does without a ticket key
  (`PUT Change phone number`), its description naming the ticket, with a working
  happy-path body and no saved examples. No fitting folder: create one named
  after the resource (`Users` for `/v1/users/...`) and say so in the summary.
  Don't move or rename existing requests or folders unless the user asks; flow
  folders stay as they are.

Without `testsCollection`, the cases go into the main collection, following the
project skill's rules for it.

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
2. **The config has `api.ticketEnvironment`** → read the
   `confirmTicketEnvironment` preference
   ([preferences.md](../../configure-project/references/preferences.md)). `auto`:
   use it and say so in one line ("Testing on `<env>` (ticketEnvironment)"),
   unless Step 1 found the PR merged to a branch that maps to another
   environment; then ask. `ask` (the default): propose it and ask the user to
   confirm before running anything: "Test on `<env>`? The change may be deployed
   elsewhere.", with the "always" option that saves `auto`.
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

## Step 5: Comment and bug-report drafts — shown in the chat, posted per preference

After the report is written:

1. Prepare the Jira comment with the `writing-jira-comments` skill (T4): the
   product's format from its project skill, or the default API template
   (`api-comment-default-template.md`, with the endpoint, request and response
   of the happy path for each changed endpoint, never skipped). Show it in the
   chat in full.
2. For each bug, scope mismatch, or discrepancy found (including a collection gap
   discovered along the way, e.g. "this endpoint's success path can't currently be
   reached"), draft a bug report (Title / Steps to reproduce / Expected / Actual)
   and show it in the chat in full.
3. Post and file per the `postJiraComment` and `fileBugs` preferences, as
   [preferences.md](../../configure-project/references/preferences.md), "After a
   test run", describes: `auto` posts/files and gives the link, `ask` (the
   default) asks with "always"/"never" options that are saved, `never` leaves the
   drafts. Nothing is posted or filed on any other basis. Files that go with a
   comment or a bug go up as
   `~/.claude/skills/creating-jira-tickets/references/jira-attachments.md` says,
   from where the run saved them.

## Step 6: Always publish the package

Whenever the product has a publish target, finish by building the package from
`<run folder>/published-collection/`: the collection, including any cases
generated in Step 3, with its environments, including a refreshed live-populated
file if the product uses one (`publish.envRefreshProcedure`), and the tests
collection when the config has `testsCollection`. For Confluence also the
collection zip without environments and the `lastUpdate` panel with the current
commit/branch.

Then follow [publishing.md](./publishing.md): write the local folder (no
question), scan what goes to Confluence, check whether the published version is
still the one recorded in `published-base.json`, show the user what goes where,
and upload per `publishCollection` (after their yes with `ask`). If someone
published a newer version during the run, say so and offer to take it as the base
and run again.

Reaching this step is mandatory in ticket mode whenever a target exists —
independent of whether the tests passed, and not something to skip because the run
"already has enough evidence." If the target can't be reached this session (no
Atlassian server for the site, see `confluence-publish.md`, "Which server to use";
or `op` not signed in), say so plainly here too rather than silently completing a
partial publish.
