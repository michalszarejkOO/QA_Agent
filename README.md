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

It also creates `~/.claude/environments/` (global, never committed to any repo), the
index of products, plus `environments/` in this repo as a convenience link to it, and
removes product links there whose project folder is gone.

Then add your products: ask Claude to run the `configure-project` skill
(`skills/configure-project/`). It walks you through which Atlassian connectors are
authorized (Atlassian's own MCP server only: the claude.ai Atlassian connector or
`https://mcp.atlassian.com/v2/mcp`, see
[`connectors.md`](./skills/configure-project/references/connectors.md)) and which
products/repos you're testing, and for each product writes
`<workDir>/config/<product>-<env>.json` in the project's own working directory and
symlinks it into `~/.claude/environments/`. Shape and fields are documented in
[`environments.example/`](./environments.example/).

## Updating an existing install

```
git pull
./setup.sh
```

Or open Claude in this folder and say "set up QA_Agent" / "zrób setup": `CLAUDE.md`
tells it to run `setup.sh` and then whichever of `configure-project` (no products
yet) or `updating-qa-agent` (pending migrations) applies.

The first `setup.sh` also enables the repo's git hooks (`core.hooksPath=.githooks`):
from then on every `git pull` and branch switch re-runs `setup.sh` and prints
whether the setup needs an update. Git never enables hooks by itself, so that
first run is always manual. `qa-tester`, `testing-apps` and `testing-api` also
check the setup at the start of a run and warn when it's out of date.

To see whether everything a run needs is in place (links, hooks, configs, MCP
servers, tools, Jira access), say "check QA_Agent" / "sprawdź setup": the
`checking-qa-agent` skill prints a FAIL/WARN/OK report with a fix command for each
problem and changes nothing. `setup.sh` prints the same report minus the live Jira
check, and `configure-project` / `updating-qa-agent` end with it.

`setup.sh` does everything that needs no decision and lists any pending
**migrations**: changes that existing installs can't pick up from `git pull` alone
(a new required config field, files that move, an MCP server registered
differently). Apply them by telling Claude "update QA_Agent" / "aktualizuj skille":
the `updating-qa-agent` skill runs them in order, asks only what it can't work
out (e.g. a project's working directory), and records what's done, so every
machine ends up with the same setup however many updates it skipped.

## Making changes to QA_Agent

If your change needs something done on machines that already use QA_Agent, add
a migration in the same commit: `skills/updating-qa-agent/migrations/NNN-<slug>.md`
with the sections "What changed", "Is it needed", "Steps" and "Verify" (details in
[`skills/updating-qa-agent/SKILL.md`](./skills/updating-qa-agent/SKILL.md)), then run
`python3 -I skills/updating-qa-agent/scripts/migrations.py lint`. A change that
only edits skill text needs no migration. Removing or renaming a skill folder:
add its old name to `RETIRED_SKILLS` in `setup.sh`. Keep skills and the agent
product-agnostic (see "Generic skills here, project knowledge in the project").

## Contents

- `environments/` (symlink to `~/.claude/environments/`, in `.gitignore` — never
  commit) — per-product/per-environment config with access details (Basic Auth, test
  login) for pinned staging environments, one JSON file per product/env — e.g.
  `acme-staging.json` for tickets with prefix `ACME-*`. Global location = the same
  config visible to `qa-tester`/`testing-api` regardless of which project/repo you
  happen to be working in — a new app arrives, you add another
  `<product>-<env>.json` file with a `ticketPrefixes` field, and both find it
  automatically by ticket prefix or repo, instead of waiting for details to be
  pasted in mid-session. Each product file also names a required working
  directory (`workDir`): the one folder where everything a run produces for that
  product lands (evidence, API run output, worktrees, reports), so dropping a
  project means deleting one folder. See [`environments.example/`](./environments.example/) for
  the exact JSON shape (separate examples for a product with a UI and a product with
  an API collection). `environments.example/validate_environments.py` checks the
  shape of these files (required fields, valid `api.client`, a product with neither
  `api` nor `surfaces`, a `workDir` that doesn't exist) and one cross-file consistency check: whether a product's
  `jira.connector` actually exists in `atlassian-connectors.json` and whether the two
  files agree on the site. It does not check whether a given connector is actually
  authorized live right now — that drifts independently of the files and needs a
  separate `getAccessibleAtlassianResources` check.

- `skills/configure-project/` — interactive setup wizard for a new clone: asks which
  Atlassian MCP connectors are authorized and for which sites, then asks about each
  product (ticket prefixes, working directory, repo path, web/mobile UI and/or API collection,
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
  optionally refreshes a Confluence tracker page (attaching the zip, after you approve
  what goes there), and produces a
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

- `skills/creating-jira-tickets/` — turns a drafted bug or task into a real Jira
  issue: reconciles it with the project's required fields, asks for what's
  missing, and creates it only after explicit confirmation.
- `skills/create-quality-metrics/` — client-facing QA quality dashboard (HTML or
  Confluence) with a release-readiness verdict, from real Jira/test/CI numbers only.
  The HTML goes to the product's `<workDir>/reports/`.
- `skills/updating-qa-agent/` — brings an existing install up to date after a
  pull: runs `setup.sh`, then applies pending migrations from its `migrations/`
  folder in order (state in `~/.claude/environments/qa-agent-migrations.json`).
  Anyone changing QA_Agent in a way existing installs must act on adds a migration
  here (see "Making changes to QA_Agent").
- `skills/checking-qa-agent/` — read-only health check ("doctor"): links, hooks,
  migrations, configs, MCP servers, tools, and live Jira access, each problem with
  its fix command. Its script part (`updating-qa-agent/scripts/check_setup.py`) also
  runs quickly at the start of every test run and after every pull.
- `CLAUDE.md` and `.githooks/` — route "set up / update QA_Agent" requests to the
  right skill, and re-run `setup.sh` after every pull or branch switch.

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

## Generic skills here, project knowledge in the project

This repo's skills and agent stay product-agnostic: nothing in `skills/` or
`agents/` names a real product. Everything specific to one product lives in two
places outside the repo, both found through the product's
`environments/<product>-<env>.json`:

- **Config** (URLs, logins, repos, collection, Jira connector): the JSON file
  itself, kept in `<workDir>/config/` and symlinked into `~/.claude/environments/`.
- **Knowledge** (gotchas, test-data rules, workflows, links, lessons from runs):
  the product's own skill, `projectSkill`, a folder inside the product's
  `workDir`, symlinked into `~/.claude/skills/<product>`.

A normal session loads the project skill by its description. A subagent only
gets the skills in its frontmatter, so `qa-tester` (and `testing-apps` /
`testing-api` wherever they run) read `projectSkill/SKILL.md` explicitly once
they've matched the product. When a run turns up something new about the product,
it's proposed as an addition to that skill, applied only after the user approves,
and never added to this repo or to Claude's memory. Dropping a project means
deleting its `workDir`, and the config, output and knowledge all go with it.

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
