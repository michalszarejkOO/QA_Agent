# QA_Agent

Overview of the agent and skills that drive Claude Code in a QA role. This repo is
the **source of truth** — it holds real files, not symlinks. `./setup.sh` links them
into `~/.claude/skills/` and `~/.claude/agents/` so they're visible to Claude Code
from any project on this machine; editing in the repo or through the symlink is
physically the same file.

## Setup on a new machine / after cloning

```
git clone <this-remote> && cd QA_Agent
./setup.sh
```

This links `agents/qa-tester.md` and every folder under `skills/` into `~/.claude/`
(or `$CLAUDE_CONFIG_DIR`, if set). If something else already lives at those paths,
`setup.sh` backs it up to `.bak` before swapping in the symlink — safe to re-run.

Then create `~/.claude/environments/` (global, gitignored, never committed to any
repo) and add your own `<product>-<env>.json` files with the access details for your
own staging environments — shape and fields documented in
[`environments.example/`](./environments.example/). `environments/` in this repo is
just a convenience symlink to that location so it can be inspected from the project.

**Fastest path:** instead of doing the above by hand, ask Claude to run the
`configure-project` skill (`skills/configure-project/`) — it walks you through which
Atlassian connectors are authorized, which products/repos you're testing, and
generates the `environments/*.json` files for you.

## Contents

- `environments/` (symlink to `~/.claude/environments/`, in `.gitignore` — never
  commit) — per-product/per-environment config with access details (Basic Auth, test
  login) for pinned staging environments, one JSON file per product/env — e.g.
  `acme-staging.json` for tickets with prefix `ACME-*`. Global location = the same
  config visible to `qa-tester`/`testing-api` regardless of which project/repo you
  happen to be working in — a new app arrives, you add another
  `<product>-<env>.json` file with a `ticketPrefixes` field, and both find it
  automatically by ticket prefix or repo, instead of waiting for details to be
  pasted in mid-session. See [`environments.example/`](./environments.example/) for
  the exact JSON shape (separate examples for a product with a UI and a product with
  an API collection). `environments.example/validate_environments.py` checks the
  shape of these files (required fields, valid `api.client`, a product with neither
  `api` nor `surfaces`) and one cross-file consistency check: whether a product's
  `jira.connector` actually exists in `atlassian-connectors.json` and whether the two
  files agree on the site. It does not check whether a given connector is actually
  authorized live right now — that drifts independently of the files and needs a
  separate `getAccessibleAtlassianResources` check.

- `skills/configure-project/` — interactive setup wizard for a new clone: asks which
  Atlassian MCP connectors are authorized and for which sites, then asks about each
  product (ticket prefixes, repo path, web/mobile UI and/or API collection,
  credentials, Confluence tracker) and writes the resulting
  `environments/*.json` files. Never edits any other skill or agent file — config
  only.
- `agents/qa-tester.md` — the subagent that performs QA on a live application based
  on a Jira ticket, a PR diff, and (optionally) a Figma design — execution against
  the live app (Playwright for web, `agent-device` for iOS/Android) is delegated
  entirely to the `testing-apps` skill. It never edits code, and never publishes
  anything to Jira without the user's explicit approval. Additionally, when a
  ticket/diff plausibly touches accessibility (forms, custom controls, contrast,
  focus order, ARIA, screen-reader-dependent flows), it explicitly invokes the
  `auditing-accessibility` skill (outside this repo) and folds confirmed violations
  into the "Bugs and deviations found" section, tagged with the WCAG criterion.
  Deliberately left unbound in the frontmatter — like
  `preparing-refinement-questions` — so it isn't loaded on every agent run
  regardless of whether the ticket has anything to do with accessibility.
- `skills/writing-test-cases/` — writes static test cases (Title / Preconditions /
  Steps to reproduce / Expected result) from a ticket/diff, independent of
  execution. Bound to `qa-tester` (its "Derive scenarios" step).
- `skills/reporting-bugs/` — drafts a bug report (Title / Steps to reproduce /
  Expected / Actual). Bound to `qa-tester` (its "Bug report draft" step). Never
  publishes on its own — draft only. Calls `find-duplicates` itself before
  drafting, which is why that skill is bound to `qa-tester` alongside it.
- `skills/find-duplicates/` — checks in Jira whether a similar bug/task already
  exists before a new one is filed; only searches and reports, never files/links
  anything itself. An automatic first step of `reporting-bugs`, hence bound to
  `qa-tester` as its transitive dependency, not invoked by `qa-tester` directly.
- `skills/testing-apps/` — executes scenarios against a live app: one skill, one
  adapter choice based on the shape of the target (URL → web/Playwright, bundle
  id/device name → mobile/`agent-device`), instead of two separate places carrying
  the same logic. The web adapter (`references/adapters/web.md`) carries what used
  to be written inline in `qa-tester.md`: a fresh session on every run,
  network-before-clicking, screenshot-then-judge discipline. The mobile adapter
  (`references/adapters/mobile.md`, formerly a standalone `testing-mobile-apps`
  skill) carries the `agent-device` mechanics: converting screenshot pixels to
  points for `press`, verifying a "dead button" both by ref and by coordinates (to
  catch real accessibility hit-frame mismatches instead of reporting a false
  alarm), the gotcha where the daemon holds onto stale environment variables, and a
  separate reference file for one-time signing setup on a physical iPhone. Rules
  shared by both platforms (the real-account/real-payment boundary, "don't judge
  without examining the screenshot") live once, in the main `SKILL.md`, not
  duplicated per adapter. Deliberately scoped to web + mobile (iOS/Android) —
  `agent-device` also supports macOS/TV, but this skill doesn't reach into that.
  Bound to `qa-tester` (its "Execute" step), and the mobile adapter is also
  callable directly for dogfooding without a full ticket/PR context.
- `skills/preparing-refinement-questions/` — generates refinement-session questions
  from a Jira ticket. **Standalone skill, deliberately unbound** from any agent
  (it applies before a feature is delivered, so `qa-tester` would never use it —
  binding it would only raise the context cost of every test run).
- `skills/testing-api/` — runs a repo's API test collection (Bruno, Postman, or
  Insomnia) via that tool's CLI against a live environment, exports it to a zip,
  optionally refreshes a Confluence tracker page (attaching the zip), and produces a
  pass/fail report ready to paste into a Jira comment. **Standalone, deliberately
  unbound** from `qa-tester` — this is collection-level API testing, not manual QA
  against a live app. Product- and tool-agnostic: which repo/collection/client and
  (if applicable) which Confluence page comes from
  `environments/<product>-<env>.json` → the `api` key (`client`: `bruno` |
  `postman` | `insomnia`, plus repo, collectionPath, defaultEnvironment,
  knownCaveats, optionally confluence). Tool-specific mechanics (how to package the
  collection, the exact CLI invocation, where per-case annotations/caveats live)
  live in one adapter file per client (`references/adapters/{bruno,
  postman,insomnia}.md`); everything else (report template, Confluence publishing,
  stateful-case detection) is shared and not duplicated. This skill generalizes a
  pattern first proven on a single project's local `.claude/skills/` collection
  runner, before Postman and Insomnia were added as further adapters once it became
  clear different projects use different API clients and separate skills would have
  duplicated the same reporting logic.

- `skills/routing-qa-tickets/` — a standalone skill invoked right at the start when
  a request only carries a bare Jira ticket and/or PR link, without saying whether
  the change is backend or frontend. Checks the config under
  `~/.claude/environments/` first (the config shape alone — only `api` or only
  `surfaces` — sometimes settles it immediately); if not, it looks at cheap signals
  (ticket labels/component, the PR's changed-file list, not the full diff) and
  classifies backend/frontend, and for frontend, web/mobile as well. Backend →
  hands off unchanged to `testing-api`. Frontend → resolves a concrete target (web:
  `surfaces.*.appUrl` from config; mobile: asks for a device/bundle id, since the
  current config shape doesn't carry one) and hands off to `qa-tester`. Conflicting
  signals (touched paths look like both backend and frontend) or none at all → it
  doesn't guess, it asks the user. Doesn't duplicate anyone else's context — it only
  classifies and hands off.

## Origin notes

Several pieces of this repo grew out of real QA sessions rather than being designed
upfront — worth knowing the shape of that history even with identifying details
generalized:

`agents/qa-tester.md` picked up several of its rules (checking which Atlassian site
a connector is actually authorized for before assuming, handling a private repo on
an unreachable code-hosting API, an unusual login flow, a hard stop in front of a
real payment gateway) from a session that hit each of those as real blockers on a
live ticket — the fixes went into the agent, and the reusable parts became their own
skills.

The `testing-apps` mobile adapter grew out of an exploratory session on a physical
iOS device — initially as a standalone `testing-mobile-apps` skill. One-time signing
setup (device and macOS Developer Mode, a locally-keyed certificate in Xcode,
registering the device's UDID with a developer account) took up most of that
session and was moved into its own reference file so later runs wouldn't
re-discover it by trial and error. Two lessons from that session are worth knowing
regardless of project: the `agent-device` daemon holds onto the environment
variables from when it started (a later `export` doesn't reach it — it has to be
killed and restarted), and `press <x> <y>` takes iOS points, not screenshot pixels —
mixing up the units once produced a false "dead button" report for a control that
actually worked once tapped in the right place (and still surfaced a real bug: its
accessibility hit-frame was offset from its visible position — a serious issue in an
app used by people with disabilities). `testing-mobile-apps` then lived separately
from the web execution logic, which was still written inline in `qa-tester.md` — an
asymmetry with no real reason behind it, so both were moved together into
`skills/testing-apps/` as two adapters of one skill, the same pattern `testing-api`
later followed for Bruno/Postman/Insomnia.

## How it fits together

`qa-tester`'s frontmatter carries:

```yaml
skills:
  - writing-test-cases
  - reporting-bugs
  - find-duplicates
  - testing-apps
```

These four skills load in full on every run of the agent (not via descriptive
routing) and are used inside its own procedure — `testing-apps` in the "Execute"
step, itself picking the web/mobile adapter by the shape of the target;
`find-duplicates` isn't invoked by `qa-tester` directly — it's bound because a
subagent only receives the full content of the skills listed in its frontmatter at
startup, rather than loading them on demand the way a normal session does, so
`find-duplicates` has to be listed here separately even though in practice
`reporting-bugs` calls it, not `qa-tester` directly.
`preparing-refinement-questions` is invoked directly, independent of `qa-tester` —
e.g. "prepare refinement questions for ACME-1234".

## Eval suite

`.claude-plugin/plugin.json` and `evals/` exist solely so `claude plugin eval .` can
run — a minimal regression set for the two spots in this repo most prone to a silent
wrong answer: backend/frontend/mobile classification in `routing-qa-tickets`
(including two cases where the skill must ask rather than guess), and the "never
publish without approval" gate in `testing-api` ticket mode. The manifest doesn't
change how this repo is distributed — `setup.sh`'s symlinks still are — it's only
needed so a session launched by `claude plugin eval` can see this repo's skills by
name at all. See [`evals/README.md`](./evals/README.md) for scope, how to run it,
and a known, not-yet-polished edge case.
