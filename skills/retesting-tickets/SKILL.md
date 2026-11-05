---
name: retesting-tickets
description: Retests Jira tickets sent back to QA (a fixed bug, a task or story reworked after a failed test, a reopened ticket) on an environment — reads each ticket with reading-jira-tickets including its parent, linked and related issues, finds what the fix changed and checks it is deployed there, repeats the original failing steps plus a few checks around the fix through the API (testing-api's adapter, only the requests involved) or the app (testing-apps), and returns Fixed, Not fixed, Fixed with a regression or Can't verify per ticket with evidence. Drafts the Jira comment with writing-jira-comments and suggests the transition; never posts, transitions or files anything. Runs in a subagent, so tickets, responses and screenshots stay out of the main conversation.
when_to_use: "Trigger on: 'retest IP-330', 'zrób retest IP-331 IP-332', 'sprawdź czy IP-330 jest poprawiony', 'zweryfikuj fix', 'retest taska po poprawkach', 'is ABC-123 fixed on stage', a bug or task moved back to Ready for QA. Do NOT trigger for the first test of a new feature ticket (qa-tester, testing-api ticket mode), for running the whole API collection (testing-api), for exploring an app without a ticket (testing-apps) or for drafting a new bug (reporting-bugs)."
---

# Retesting tickets

A retest checks that a ticket sent back to QA now works on an environment and
that the fix broke nothing right next to it. It covers a fixed bug, a task or
story reworked after a failed test, and a reopened ticket. It is not the first
test of a feature: that is `qa-tester` (UI) or `testing-api` ticket mode (API),
which derive full coverage. A retest repeats what failed and checks around it.

## Where a retest happens

Ticket texts, diffs, responses and screenshots stay in the context of the
conversation that read them, so the retest itself runs in a subagent. The main
conversation keeps the decisions and everything that goes to other people.

1. **Main conversation: the brief.** Run the setup check:
   `python3 -I "$(dirname "$(dirname "$(readlink ~/.claude/agents/qa-tester.md)")")/skills/updating-qa-agent/scripts/check_setup.py"`.
   A warning → show it and offer to update first. Resolve the product config in
   `~/.claude/environments/` (or `$CLAUDE_CONFIG_DIR/environments/`) by the
   ticket prefix; several keys from one product go into one run. Collect what
   the user already said: the keys, the environment, the account, anything to
   watch, and for a UI retest whether to record evidence (`mode: ask` in
   `evidence.json`, as `testing-apps` asks it: videos and screenshots, or
   screenshots only). Don't read the tickets here.
   When the collection comes from 1Password, say that 1Password will ask for
   approval during the run. No environment named: don't ask yet,
   the run stops after reading the tickets with the question and where each
   fix was merged. Say in one line what the run will do (keys, product,
   environment or "asks after reading", model).
2. **Start a subagent** (`general-purpose`, model `sonnet`; `opus` for this run
   only when the user asks for it) with the brief and this instruction: "Load
   the retesting-tickets skill and follow 'The run' inside a subagent. You
   can't ask the user: wherever the skill says to ask, stop and report the
   question with its options and the default. Don't post, transition, file or
   publish anything."
3. **When it stops with a question,** ask the user and continue the same
   subagent with the answer.
4. **When it returns,** show the summary and, per ticket, the comment draft
   and the suggested transition; then the bug drafts. Ask about each: post the
   comment (`writing-jira-comments`, "Showing and posting"), move the ticket
   (fetch its available transitions first and name the one you'd use), file
   the bug (`creating-jira-tickets`). Collection changes are published as
   `testing-api` step 8 says, after a yes. Add proposed project-skill lines
   only on a yes.

**If you are that subagent:** the brief and the setup check are done. Start
at "The run", ask nothing, and return in the order of step 8 below.

## Rules

| Severity | Rule |
| --- | --- |
| MUST | Retest only on an environment the user named or confirmed for this run. |
| MUST | Repeat the original failing steps for real. Never call a ticket Fixed from the diff, a comment or a status alone. |
| NEVER | Post a comment, transition a ticket, file a bug or publish a collection. Those happen in the main conversation after the user's yes. |
| NEVER | Retest a fix that isn't deployed on the environment as if it were: that is Can't verify, with where it is merged. |

## The run

1. **Read each ticket** with the `reading-jira-tickets` skill, including its
   "Related issues" section. Find out:
   - **What failed.** A bug: its steps, expected and actual result, the
     environment and data it was found with. A task or story sent back: the
     last QA comment that failed it and the bugs linked to it; those failing
     points are what to retest, not the whole ticket again.
   - **What correct means.** The ticket's acceptance criteria as the comments
     left them; for a bug or a sub-task, the parent or the story it was found
     in, whose acceptance criteria decide the expected result when the bug is
     vague.
   - **What else is involved.** Duplicates and clones (they are fixed or not
     together; name them), blockers still open (Can't verify if they block the
     steps), and other bugs on the same story already fixed, which make good
     checks around the fix.
2. **What the fix changed:** the PR or branch and its diff (`reading-jira-tickets`,
   "The PR or branch"), and where it was merged. No fix found and no comment
   saying what changed: say so and retest anyway when the ticket is back in QA.
3. **Is it on the environment.** Map the branch where the fix was merged to an
   environment as
   [target-branch.md](../testing-apps/references/target-branch.md), "From branch
   to environment", says, and use the project skill's way of checking what is
   deployed when it has one. No environment in the brief: stop here and ask,
   with where each fix was merged as the hint. The fix not deployed on the
   chosen environment: that ticket is Can't verify (not deployed); go on with
   the others.
4. **API or UI, per ticket.** The steps name a request or endpoint → API; they
   are screens and clicks → UI; both → both. Unclear: the signal table in
   `routing-qa-tickets`, "Classification signals". A product with only `api` or
   only `surfaces` settles it alone.
5. **Plan, per ticket.** First the original steps exactly as they failed (same
   kind of data, same role or account type). Then two to four checks around the
   fix: the boundary the fix changed, other paths the diff touches, the parent's
   acceptance criteria that go through the same code. Not a full regression; a
   check that needs much more than that goes into the summary as a suggestion.
6. **Execute.**
   - **API:** load the `testing-api` skill and use its pieces, not its whole
     procedure: the latest collection
     ([ticket-driven-testing.md](../testing-api/references/ticket-driven-testing.md),
     "Step 2: Resolve the latest collection"), the adapter and the environment
     check ([run.md](../testing-api/references/run.md), steps 1 and 4), and
     its "Rules for the run" on caveats and claimed passes. Run only the
     requests involved (the adapter's folder scope, or a single request), and
     look into every failure as run.md step 6 says before calling it Not
     fixed. No case in the collection reproduces the failure: add one to the
     run folder's copy, as a saved example on the existing request unless the
     project skill says otherwise, its description naming the ticket; then
     export as run.md step 3 says, so the main conversation can publish it.
     The run folder is `<workDir>/api-runs/<KEY>-retest/` (several keys: the
     first key plus `-and-more`).
   - **UI:** read [execution.md](../testing-apps/references/execution.md) and
     follow it, with its evidence layout; the original steps get a video
     (screenshots instead when the brief says "evidence: screenshots only"). The
     target URL or device comes from the product config for the chosen
     environment ([target-branch.md](../testing-apps/references/target-branch.md),
     "From branch to environment"; mobile builds from the branch with the fix).
7. **Verdict, per ticket:**
   - **Fixed:** the original steps give the expected result and the checks
     around pass.
   - **Not fixed:** the original steps still fail; the evidence is the request
     and response or the video and screenshot.
   - **Fixed with a regression:** the original steps pass, a check around
     fails. Run `find-duplicates` and draft a new bug with `reporting-bugs`,
     linked to this ticket.
   - **Can't verify:** not deployed, blocked by an open ticket, no test data,
     environment down; say exactly what is needed.
8. **Return,** in this order:
   1. One line per ticket: key, bug or task, API or UI, verdict, the reason in
      a few words.
   2. Per ticket: what was run (original steps and checks around, each with
      its result), evidence paths, the comment draft (`writing-jira-comments`;
      Fixed → PASSED, Not fixed or Fixed with a regression → FAILED, Can't
      verify → BLOCKED) and the suggested move (back to the developer, or on
      to the next status).
   3. Bug drafts for regressions, with possible duplicates.
   4. Collection changes ready to publish: the run folder and the version they
      are based on (`published-base.json`).
   5. Proposed additions to the project skill, or "None".
