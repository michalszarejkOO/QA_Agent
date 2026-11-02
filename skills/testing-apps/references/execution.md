# Running a test (both adapters)

Read by whoever drives the app, before the first action: `qa-tester` in its
step 3, a subagent doing a standalone run, or the main conversation for a single
look. Where a standalone run happens and how its branch is chosen is in
[../SKILL.md](../SKILL.md).

## Picking the adapter

| Target looks like | Adapter |
| --- | --- |
| A URL | [Web](./adapters/web.md) — Playwright MCP tools |
| A bundle id, an App Store/TestFlight name, or the request says "iOS app"/"Android app" | [Mobile](./adapters/mobile.md) — `agent-device` CLI |

A macOS, Apple TV, or web-only `agent-device` target is out of scope for the mobile
adapter — `agent-device` supports those too, but this skill's mobile rules
(physical-device signing, points/pixels conversion, the shared daemon and its
signing env) are specific to iOS/Android handhelds and simulators/emulators. Call `agent-device`
directly for a desktop/TV target, or the web adapter if the target is actually a
web page.

## Shared discipline (both adapters)

- **Read before you click.** Before driving toward any particular state — locating
  one record among many, checking whether an action is even possible yet,
  confirming what a previous step actually persisted — check whatever the
  platform's evidence trail already says (web: `browser_network_requests` and the
  API responses behind it; mobile: `agent-device logs`/`network`). It usually tells
  you directly whether the state you need already exists, or which path reaches it
  fastest. Blind click-through is the fallback for when that evidence is
  inconclusive, not the default.
- **A tap/click is not a verified outcome until you've looked.** Screenshot at
  every meaningful checkpoint and actually examine it before judging pass/fail.
- **Real-account and real-transaction boundaries are the same on both platforms.**
  Never fake, seed, or bypass authentication — signing in through the app's real
  flow with credentials you were given is fine; a login you can't get past is a
  blocker to report, not something to bypass. Any step that initiates a payment,
  checkout, invoice, or other real-or-simulated transaction is a hard stop the
  moment you recognize it, on staging or not — report it as a blocker, don't
  attempt it. On a physical mobile device signed into the tester's own real account
  (common there, unlike a throwaway browser session), that boundary extends to
  logout/account-deletion too — see the mobile adapter.
- **Never restart, switch, or reconfigure the pinned target.** The delegated app
  URL, device, or app is fixed for the run.
- **Follow the project skill.** Once the target is matched to a product config
  with `projectSkill`, read `<projectSkill>/SKILL.md` before the first scenario
  (inside `qa-tester` it's already read). Its rules on test data, logins and
  environment quirks apply on top of these. When the run turns up something new
  about the product, propose it as an addition to that skill in the end summary,
  and add it only after the user approves. Product-specific findings never go
  into this skill or Claude's memory.

## Recorded evidence (scenario videos and bug folders)

Every run records a video of each scenario: happy path, error handling and
edge cases alike. It also gives each bug its own folder holding a screenshot
and a video, and saves everything to a folder the user chose. This is separate
from the checkpoint screenshots you take to judge pass/fail (see above), which
you take either way.

**Settings.** Read `mode` from `~/.claude/environments/evidence.json` (or
`$CLAUDE_CONFIG_DIR/environments/evidence.json`) at the start of the run:
`auto` (the default, also when the field or the file is missing) records and
saves without asking; `ask` means the user chooses for this run. The delegating
conversation asks before the run, with these two options, and passes the
answer in the brief as the quoted line:

| Option | Brief line | What the run saves |
| --- | --- | --- |
| Videos and screenshots (default) | `evidence: record and save` | Everything below: scenario videos, bug folders with screenshot and video, checkpoints |
| Screenshots only | `evidence: screenshots only` | No videos: no `testing/` folder, bug folders hold only their screenshots, checkpoints as always |

There is no "save nothing" option: checkpoint screenshots are how pass/fail was
judged, so they are kept either way. A subagent can't ask, so with no answer in
the brief, work as with "screenshots only" and say in the report that the
evidence choice was missing. With "screenshots only", don't start any
recording, and report the videos as switched off by the user, not as missing.

**Evidence root.** Use the first of these that applies, expanding `~` yourself:

1. A folder named in the brief, for that run only.
2. `<workDir>/qa-evidence/`, where `workDir` comes from the product config that
   matched the ticket or target. This is the normal case: everything for one
   project stays in its working directory.
3. `dir` from `evidence.json`, only for a run that matches no product config.
4. `./qa-evidence/`, flagged in the report as "no working directory
   configured".

**Layout.** Put everything for one run in
`<evidence root>/<ticket key, or a short session name>/<YYYY-MM-DD>-<web|ios|android>/`,
creating it with `mkdir -p`:

```
testing/
  happy-path/<scenario-id>-<slug>.mp4
  error-handling/<scenario-id>-<slug>.mp4
  edge-cases/<scenario-id>-<slug>.mp4
bugs/
  <bug-n>-<slug>/
    screenshot.png
    video.mp4
checkpoints/<n>-<slug>.png      screenshots taken to judge each step
playwright-mcp/                 web only: page snapshots and console logs
```

`testing/` holds the test evidence, one video per scenario, whatever the
result. `bugs/` holds one folder per bug, with everything needed to attach to
that bug's ticket and nothing else.

Checkpoint screenshots are saved whatever `mode` says: they're how pass/fail was
judged, not recordings. With no evidence root at all, they still go to the run
folder the fallback picks, never to the folder Claude was opened in.

If the run folder already exists from an earlier run today, add `-2`, `-3`, ...
so nothing is overwritten.

**Scenario category.** Every scenario carries one category, set when the
scenario list is written (`qa-tester` step 2, or your own list when
standalone):

| Category | Folder | Covers |
| --- | --- | --- |
| Happy path | `happy-path/` | The intended flow with valid input, ending in success. |
| Error handling | `error-handling/` | Invalid input, validation messages, failed or rejected requests, permission denials, empty or error states. |
| Edge case | `edge-cases/` | Boundaries and limits, unusual but valid input, language/direction, theme, font scale, accessibility, interrupted or repeated actions. |

If a scenario fits more than one, pick the one its expected result is about.

**What to record.** With `evidence: screenshots only`, skip step 1 and the
videos in step 2; everything else stays the same.

1. **Every scenario:** start recording at the scenario's first step and stop
   after its expected result is visible. Save the video under `testing/` in
   the scenario's category folder, whether it passed or failed. Add `-FAIL` to
   the file name of a failed scenario's video (`TC-04-empty-email-FAIL.mp4`).
   One video per scenario. Don't record several scenarios in one video.
2. **Bugs:** create `bugs/<bug-n>-<slug>/` and save a screenshot of the failure
   state there as `screenshot.png`. For the video:
   - If the bug came from a recorded scenario, copy that scenario's video into
     the bug folder as `video.mp4`. Keep the original under `testing/`.
   - If the bug showed up outside a scenario (while exploring), reproduce it
     once with recording on and save the video as `video.mp4`. If it doesn't
     reproduce, say so in the report.
   - If one bug needs more than one screenshot, number them
     (`screenshot-1.png`, `screenshot-2.png`).

Starting and stopping a recording works differently on each platform; see the
"Recording" section of each adapter. If recording isn't available (for example,
the tool is missing or the simulator's recorder is busy), keep testing. Report
which videos are missing and why. Never present a checkpoint screenshot as a
video.

At the end of the run, list every saved file with its absolute path, grouped
as `testing/` (by category) and `bugs/` (by bug), so the report can link
evidence to scenarios and bugs.

## Keeping the user informed

When this skill runs in the main conversation (a single look, or the user
asked to drive it there), write one short line before each notable action: signing in and
with which test account, starting or stopping a recording, building or opening
the app, reproducing a bug, skipping a scenario. One line per step, not per
click. Inside `qa-tester`, log the same actions for its report's run log
instead.

End every run with a point-list summary:

- **Done:** each thing completed (scenarios run with pass/fail counts, evidence
  saved and where).
- **Not done / skipped:** each scenario, step, or piece of evidence that wasn't
  done, with its reason. If nothing was skipped, write "Nothing skipped."
- **Proposed additions to the project skill:** each new product-specific finding,
  worded as the line to add, or "None".

## Procedure

0. Setup check: `qa-tester` already ran it, and for a standalone run in a
   subagent the main conversation ran it while gathering the brief
   ([../SKILL.md](../SKILL.md), "Where a standalone run happens", step 1). Run
   it yourself only for a single look in the main conversation:
   `python3 -I "$(dirname "$(dirname "$(readlink ~/.claude/agents/qa-tester.md)")")/skills/updating-qa-agent/scripts/check_setup.py"`. If it prints a warning, show it to the user before the run and
   offer to update first (`./setup.sh`, then the `updating-qa-agent` skill). If
   they'd rather test now, continue; outputs then fall back as the warning says.
1. Resolve the adapter from the target ("Picking the adapter" above). Standalone, the branch and environment come from the brief
   (`../SKILL.md`, "Standalone runs: which branch and environment"); with no
   brief, resolve them per that section first.
2. Load that adapter's reference file ([web](./adapters/web.md) or
   [mobile](./adapters/mobile.md)) and follow it exactly — it owns discovery,
   session start, the click/type/navigate loop, and evidence capture for its
   platform.
3. Resolve the evidence settings and run folder ("Recorded evidence" above)
   before the first scenario.
4. Capture evidence per the adapter's instructions: screenshots always; console/
   network output whenever a criterion concerns errors, loading states, or API
   behavior; scenario videos and bug folders saved per "Recorded evidence" above.
5. Hand the captured evidence back to whatever's judging pass/fail — `qa-tester`'s
   own step 6 when invoked from there, or straight into your own response when
   this skill was triggered standalone. Include the saved-file list.
