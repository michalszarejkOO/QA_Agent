---
name: testing-api
description: Runs a repo's API test collection — Bruno, Postman, or Insomnia — against a live environment via that tool's CLI, builds one package (collection plus environments) for the desktop app, writes it where the product is configured (1Password, a local folder, both, or Confluence) after the user's yes or per their preferences, and produces a Jira-comment-ready pass/fail report. When the request is driven by a specific backend Jira ticket, switches to ticket mode, which reads the ticket and its PR/branch for context, tests on the configured or named environment, generates full scenario coverage for any endpoint the collection doesn't already cover, treats the published collection as the latest version, and closes with a Jira comment and any bug reports, posted, asked about or left as drafts per the user's preferences. Use when asked to test the API, run the API test suite, verify endpoints are working, export/re-export an API collection, or QA/test a backend Jira ticket. Product, repo and tool come from ~/.claude/environments.
when_to_use: "Trigger on: 'przetestuj API', 'uruchom testy API/bruno/postman/insomnia', 'sprawdź czy endpointy działają', 'wygeneruj raport testów do jiry', 'wyeksportuj kolekcję', 'run the API tests', 'test this endpoint', 'export the collection', 'opublikuj kolekcję', 'publish the collection', 'test/QA this backend ticket', a Jira ticket URL/ID for a [BE] or backend-only ticket, or any request to verify API behavior using a committed collection. Not for a retest of a fixed ticket (retesting-tickets)."
---

# Testing an API collection

Drives a repo's committed API test collection end to end: package it for the
matching desktop app, run it headlessly via that tool's CLI, and turn the result
into a report the user can paste into Jira as test evidence. Product-agnostic and
tool-agnostic — which repo, which client (Bruno/Postman/Insomnia), where the
collection is published (if anywhere), and which stateful-case caveats apply all
come from that product's config, never hardcoded here. The mechanical differences between clients (how a
collection is packaged, the exact CLI invocation, where per-case caveats/annotations
live) are isolated in one adapter file per tool; everything else — resolving the
product, checking caveats, writing the report, publishing — is shared
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
- The publish step (step 8) writes the package (collection with its
  environments) to the product's `api.publish.target` (`1password`, `local`,
  `1password+local` or `confluence`; see
  [publishing.md](./references/publishing.md), "The four targets"). No target,
  no publish step: the package stays in the run folder as the file to import. In
  ticket mode, whenever a target exists, always reach this step — never silently
  skip it there. The local folder is written without asking; 1Password and
  Confluence follow the `publishCollection` preference (ask by default).

## Where a run happens

A run reads and prints a lot (the CLI's results, response bodies, the PR diff,
collection files), and all of it stays in the context of the conversation that
read it, sent again with every later turn. So the run itself happens in a
subagent. The main conversation keeps the decisions and everything that goes
to other people: the questions about the Jira comment, bugs and publishing.

What happens after a run follows the user's preferences
(`~/.claude/environments/qa-agent-preferences.json`; read them with
`python3 -I <QA_Agent>/skills/configure-project/scripts/preferences.py get <action> --product <product>`,
see [preferences.md](../configure-project/references/preferences.md)): per
action `auto` (done without asking), `ask` (the default) or `never` (left as a
draft, no question).

1. **Main conversation: the brief.** Run the setup check (step 0, first
   sentence) and resolve the product config (step 0). Decide the mode: ticket
   mode when the request names or links a specific backend ticket. Collect
   what the user already said: environment, folder or endpoint, anything to
   watch. In ticket mode the environment is the one the user named, else
   `api.ticketEnvironment` when `confirmTicketEnvironment` is `auto`; otherwise
   don't ask yet: the subagent stops after reading the ticket with the question
   and where the PR was merged (ticket-driven-testing.md, "In a subagent: where
   the run stops to ask"). Read the preferences for `postJiraComment`,
   `fileBugs`, `attachEvidence` and `publishCollection` and put them in the
   brief. Say in one line what the run will do (product, mode,
   environment or "asks after reading the ticket", model), and, when the run
   downloads from 1Password (`api.publish.target` with `1password`, in ticket
   mode or without `repo`), that 1Password will ask for approval during it.
2. **Start a subagent** (`general-purpose`, model `sonnet`, in both modes).
   If the user asks for Opus for this run ("puść na Opusie", "run it on
   Opus"), start it with model `opus` instead; that applies to this run only.
   Give it the brief and this instruction: "Load the testing-api skill, read
   its references/run.md, and follow both as the run inside a subagent. You
   can't ask the user: wherever
   the skill says to ask, stop and report the question with its options and
   the default. Do the actions the brief marks `auto` yourself (post the
   comment, file the bugs, attach the evidence, publish when the check in
   publishing.md is clean), except at a safety stop (publishing.md, step 4:
   a secret flagged or a newer published version; a bug that may be a
   duplicate; data the project skill says not to touch): then don't do it and
   report it as a question. Leave the `ask` and `never` ones as drafts."
3. **When it stops with a question**, ask the user and continue the same
   subagent with the answer, rather than starting a new one.
4. **When it returns**, show its report, the Jira comment draft and any bug
   drafts in full, and what it already did (`auto`: links to the comment and
   bugs, where it published). Then, in this order: ask about each `ask` action
   ("Tak" / "Nie" / "Tak, zawsze" / "Nie, nigdy"; save "always"/"never" with
   `preferences.py set`) and any safety stop the subagent reported, and act on
   the answers; show the `never` ones as drafts without asking. If the product
   has a publish target the subagent didn't handle, do step 8 here, from the
   files it left in the run folder. Relay its summary (run.md, "Keeping the user
   informed"). **Last**, ask about the proposed project-skill lines
   (`updateProjectSkill`, `ask` by default).

**If you are that subagent:** the brief and the setup check are done. Read
[run.md](./references/run.md) now if you haven't. Start at step 0 with the
brief (skip its setup check), ask nothing, do the `auto` actions from the
brief (step 8 too when `publishCollection` is `auto`, or the target is `local`),
and stop after step 7 (generic) or after the drafts (ticket mode, T4–T5 without
the questions). Return, in this order: the report, the Jira comment draft, bug
drafts, what you did by yourself (links, where you published), the safety
stops, what's ready to publish (the package in the run folder and the version
it's based on, `published-base.json`), proposed project-skill lines, the
summary (run.md, "Keeping the user informed") and the run log.

Stays in the main conversation, with no subagent: an export only ("wyeksportuj
kolekcję"), publishing an export that already exists, or a run whose results
are already in the conversation (only the report and the questions are left).
An export or a run here reads [run.md](./references/run.md) for its steps.

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Resolve the target repo, client, and collection path before doing anything else (step 0) — never assume the current directory has the collection, and never guess the client from habit when the config says otherwise. |
| MUST | If (and only if) the product's config names a publish target, end the run by writing the freshly built package there, per [publishing.md](./references/publishing.md) — independent of test results, not conditional on them passing. The local folder is written without a question; 1Password and Confluence follow `publishCollection`. |
| NEVER | Upload anything (to 1Password or Confluence: create an item or page, upload a file, update a body) without the user's yes to the summary in [publishing.md](./references/publishing.md), step 4 (what goes where, from which folder, and which version it replaces), or `publishCollection: auto` with a clean check. Before that, always read the published version and compare it with this run's base; a newer or different version is a safety stop, never overwritten silently, `auto` or not. No answer, or anything but a clear yes, means don't publish. |
| NEVER | Put environments, `.env` files or anything with live tokens on Confluence: only the collection without environments goes there, and the package (collection + environments) goes to 1Password or the local folder; `.env` files stay out of every zip. Never upload a file to Confluence that `scan_secrets.py` flags without the user's yes after seeing its list. Never print a secret's value. |
| NEVER | Put collection content (request bodies, raw exports, file dumps) inline in a Confluence page body. It stays a `lastUpdate` marker; the zip is attached as a file, not pasted as text. |
| NEVER | Commit, push, or otherwise persist results/exports into git without being asked. The zip export is a local artifact, not a repo change. |

The rules for the run itself (environment, scope, caveats, report, no claimed
PASS) are in [run.md](./references/run.md), "Rules for the run".

### Ticket mode

A retest of a fixed bug or a ticket sent back to QA is the `retesting-tickets`
skill, not ticket mode: it runs only the requests involved, using this skill's
adapter and collection steps.

When the request names or links a specific backend ticket, load
[ticket-driven-testing.md](./references/ticket-driven-testing.md) and follow it:
its rule table applies on top of the rules above, and its order replaces the
generic procedure. Two of its rules, because nothing may slip past them:

| Severity | Rule |
| --- | --- |
| MUST | Test on the environment the user named for this run; otherwise on `api.ticketEnvironment`, without asking when `confirmTicketEnvironment` is `auto`, after the user confirms it when `ask`. Never assume `demo`, never fall back to `api.defaultEnvironment` silently. |
| MUST | Post the Jira comment and file bugs only as `postJiraComment` and `fileBugs` say: `auto` (done, except at a safety stop), `ask` (the default: draft, then ask about each) or `never` (draft only). The drafts are always shown in full. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [run.md](./references/run.md) | Inside the subagent, right after this file; in the main conversation for an export or a run without a subagent | Steps 1-7 (adapter, request, export, environment check, run, failures, report), the rules for the run, the run log and closing summary, and the references the run loads (adapters, report template, target branch) |
| [config-fields.md](./references/config-fields.md) | Step 0, when the config has `testsCollection`, `knownCaveatsFile`, `publish.extraEnvironmentFiles` or `publish.envRefreshProcedure`, the collection folder holds several collection files, or a field isn't clear | The full `api` block, the optional fields, where their files live |
| [publishing.md](./references/publishing.md) | Step 8 whenever the config names a publish target; downloading the published collection (ticket mode, or no `repo`) | The four targets (`api.publish.target`), the package, staging in `.publish/`, `apiCollectionsFolder`, the secret scan, comparing with the published version, the summary and question before any upload, `published-collection/` and `published-base.json` |
| [onepassword-publish.md](./references/onepassword-publish.md) | `api.publish.target` is `1password` or `1password+local` | Vault and item name from config, `op` sign-in (the user's, one approval per stage, or `op.sh` with a service account), one Secure Note item per product holding the package zip, notes and tags, reading the version, uploading, downloading |
| [confluence-publish.md](./references/confluence-publish.md) | `api.publish.target` is `confluence` | Reading cloudId/space/folder/title/attachment name from config, reading attachment versions, the generate-body script, find-or-create/update procedure, attaching the files, downloading the attached collection |
| [ticket-driven-testing.md](./references/ticket-driven-testing.md) | The request names or links a specific backend ticket | Ticket mode's rules and order (T0–T6), where the run stops to ask, gathering ticket/PR context, resolving the published collection as the latest one, generating full scenario coverage, and the comment/bug-report step per the preferences |

## Procedure

0. **Check the setup, then resolve the product, client, and config.** First run
   `python3 -I "$(dirname "$(dirname "$(readlink ~/.claude/agents/qa-tester.md)")")/skills/updating-qa-agent/scripts/check_setup.py"`. If it prints a warning, show it to the user and offer to update first
   (`./setup.sh`, then the `updating-qa-agent` skill); if they'd rather run now,
   continue with the fallbacks. Then resolve the product. Figure out which repo/collection is
   in scope from the user's request (a repo name, a ticket prefix, or an explicit
   path). Look for a matching file under `~/.claude/environments/*.json` (or
   `$CLAUDE_CONFIG_DIR/environments/` if that's set — the same global, per-product
   config `qa-tester` uses) with an `api` block. A run needs `client` and `defaultEnvironment`, plus
   either `repo` (with `collectionPath`) or a publish target for the collection; `ticketEnvironment`, `knownCaveats`, `publish` and
   `confluence` are used where the steps below name them. The full shape, the
   optional `testsCollection` (a separate collection for test cases),
   `knownCaveatsFile`, `publish.extraEnvironmentFiles` and `publish.envRefreshProcedure`, and where to find those files are in
   [config-fields.md](./references/config-fields.md): read it when the config
   has one of the optional fields, or a field isn't clear.
   `client` is one of `"bruno"`, `"postman"`, `"insomnia"` and selects which adapter
   the rest of this procedure loads — everything below is identical in shape across
   clients, only the exact commands and file conventions differ, and those live in
   the adapter, never in this file.
   - **Found** → use `repo` as the repo root, `client` to pick the adapter, and
     `collectionPath` (`.` when absent) for every step below. **No `repo`**: the
     published copy is the source of the collection (config-fields.md, "No
     `repo`"), so every run, generic ones too, downloads it into the run folder
     first and uses `<run folder>/published-collection/` as the repo root;
     `publish.apiCollectionsFolder`, when set, holds the last published
     package and is the fallback when the download isn't possible. `publish` is optional; without a target
     step 8 is skipped. Create this run's **run folder**,
     `<workDir>/api-runs/<ticket key, or YYYY-MM-DD-<env>>/` (top-level
     `workDir` from the same file; add `-2`, `-3`, ... if it exists). Every file
     this run writes goes there: the CLI's result file, the staging folder
     `.publish/` (the package; publishing.md, "Staging"), the report, and any
     helper script you write (a case generator, a one-off
     check). Nothing goes to `/tmp`, `~/Desktop` or the session's scratchpad
     directory, even where general instructions suggest it for temporary files. If the file has
     `projectSkill`, read `<projectSkill>/SKILL.md` now (unless this session
     already loaded it) and follow its rules for this product's collection and
     test data.
   - **Not found, but the current directory has a recognizable collection** (a
     `bruno/`-style folder, a `*.postman_collection.json`, or an Insomnia export) →
     infer the client from whichever of those is present, use the cwd as repo root,
     use the environment the user names (or list the collection's environments and
     ask), and skip the publish step (nothing to publish to
     without config). The run folder is `./api-runs/<YYYY-MM-DD-<env>>/`; say in
     the report that no working directory is configured.
   - **Not found and cwd has no collection** → ask the user which repo/collection/tool
     to run against rather than guessing.

Steps 1-7 (load the adapter, parse the request, export, check the
environment, run, investigate failures, write the report) are in
[run.md](./references/run.md).

8. **If the product's config names a publish target** (in the main
   conversation, or in the subagent when `publishCollection` is `auto` or the
   target is `local`), write the package there, following
   [publishing.md](./references/publishing.md) exactly (identifiers come from
   config, not from this file). The local folder is written without asking. For
   1Password and Confluence it scans what goes to Confluence for secrets,
   compares the package with what is published now, and then follows
   `publishCollection`: asks (`ask`), publishes when the check is clean
   (`auto`), or uploads nothing (`never`). A generic run exports `origin/<branch>`
   without uncommitted changes, so the published collection may be newer than this
   one: that check is what keeps it from being overwritten. Offer this regardless
   of whether the tests passed. Give the user the link, the vault and item, or the
   local path when done. If there's no target, skip this step silently — don't ask the user to set
   one up unless they bring it up.

## Procedure — ticket mode

The order (T0–T6) and every step's detail are in
[ticket-driven-testing.md](./references/ticket-driven-testing.md).
