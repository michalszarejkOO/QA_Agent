---
name: testing-apps
description: Drives a running app to execute test scenarios and capture evidence — Playwright for a web app, or the agent-device CLI (Callstack) for an iOS/Android mobile app — picking the adapter from whether the target is a URL or a device/bundle id. Used as qa-tester's own execution step (its steps 1-2 gather context and derive scenarios, this skill only replaces the browser/device-execution step, its step 6 reports and drafts bugs). Also usable standalone for direct browser or mobile-device exploration/dogfooding when full ticket/PR/Figma context isn't needed.
when_to_use: "Trigger as qa-tester's own 'Execute' step for any web or mobile target. Also trigger directly for: 'test the iOS/Android app', 'dogfood <mobile app>', 'exploratory test on iPhone/Android/simulator/emulator', or driving/exploring a running web app in the browser without a full ticket-driven QA run. Do NOT trigger for a macOS or Apple TV target — agent-device also supports those, but this skill's mobile adapter is scoped to iOS/Android handhelds and simulators/emulators only; call agent-device directly for those."
---

# Testing apps (web & mobile execution)

Drives whatever app is under test and captures evidence, so `qa-tester` — or a
direct exploratory request — has real screenshots, console/network output, and
device evidence to judge pass/fail against, instead of a guess. Picks its adapter
from the shape of the target, not from a config value: a URL means the **web**
adapter (Playwright); a device name, bundle id, or an explicit "iOS/Android app" in
the request means the **mobile** adapter (`agent-device`). Everything about *how* a
scenario is planned and reported is identical either way — this skill only owns the
execution mechanics in between.

## Picking the adapter

| Target looks like | Adapter |
| --- | --- |
| A URL | [Web](./references/adapters/web.md) — Playwright MCP tools |
| A bundle id, an App Store/TestFlight name, or the request says "iOS app"/"Android app" | [Mobile](./references/adapters/mobile.md) — `agent-device` CLI |

A macOS, Apple TV, or web-only `agent-device` target is out of scope for the mobile
adapter — `agent-device` supports those too, but this skill's mobile rules
(physical-device signing, points/pixels conversion, the daemon-env gotcha) are
specific to iOS/Android handhelds and simulators/emulators. Call `agent-device`
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

## Recorded evidence (videos and bug screenshots)

Every run records a video of each happy-path scenario, and a screenshot plus a
video of each bug, and saves them to a folder the user chose. This is separate
from the checkpoint screenshots you take to judge pass/fail (see above), which
you take either way.

**Settings.** Read `mode` from `~/.claude/environments/evidence.json` (or
`$CLAUDE_CONFIG_DIR/environments/evidence.json`) at the start of the run:
`auto` (the default, also when the field or the file is missing) records and
saves without asking; `ask` records and saves only if the user said yes for this
run. The delegating conversation asks the user before the run and passes the
answer in the brief. A subagent can't ask, so with no answer in the brief, don't
record or save, and say so in the report.

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
happy-path/<scenario-id>-<slug>.mp4
bugs/<bug-n>-<slug>.png
bugs/<bug-n>-<slug>.mp4
checkpoints/<n>-<slug>.png      screenshots taken to judge each step
playwright-mcp/                 web only: page snapshots and console logs
```

Checkpoint screenshots are saved whatever `mode` says: they're how pass/fail was
judged, not recordings. With no evidence root at all, they still go to the run
folder the fallback picks, never to the folder Claude was opened in.

If that folder already exists from an earlier run today, add `-2`, `-3`, ... so
nothing is overwritten.

**What to record.**

1. **Happy-path scenarios:** start recording at the scenario's first step and
   stop after its final expected result is visible. If it passes, save the video
   to `happy-path/`. If it fails, save it to `bugs/` as that bug's video.
2. **Bugs:** save a screenshot of the failure state to `bugs/`. If the bug
   showed up outside a recorded scenario (a negative or edge case, or found while
   exploring), reproduce it once with recording on, then save that video next to
   the screenshot. If it doesn't reproduce, say so in the report.
3. Negative and edge-case scenarios that pass don't need a video. Their
   checkpoint screenshots are enough.

Starting and stopping a recording works differently on each platform; see the
"Recording" section of each adapter. If recording isn't available (for example,
the tool is missing or the simulator's recorder is busy), keep testing. Report
which videos are missing and why. Never present a checkpoint screenshot as a
video.

At the end of the run, list every saved file with its absolute path so the
report can link evidence to scenarios and bugs.

## Keeping the user informed

When this skill runs in the main conversation (standalone, not inside
`qa-tester`), write one short line before each notable action: signing in and
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

## Standalone runs: which branch and environment

Run standalone (no ticket or PR, not inside `qa-tester`), this skill tests the
product's staging-like branch and the environment deployed from it. Follow
[target-branch.md](./references/target-branch.md): user's message, then config
`targetBranch`, then detection from merged MRs, then ask. That reference also
explains how the branch maps to the app URL or mobile build, and how recent MRs
on it set what to explore first. Inside `qa-tester`, the ticket and PR decide
the branch instead.

## Procedure

0. Standalone (not inside `qa-tester`, which already did this): run
   `python3 -I "$(dirname "$(dirname "$(readlink ~/.claude/agents/qa-tester.md)")")/skills/updating-qa-agent/scripts/check_setup.py"`. If it prints a warning, show it to the user before the run and
   offer to update first (`./setup.sh`, then the `updating-qa-agent` skill). If
   they'd rather test now, continue; outputs then fall back as the warning says.
1. Resolve the adapter from the target (table above). Standalone, first resolve
   the branch and environment per the section above.
2. Load that adapter's reference file and follow it exactly — it owns discovery,
   session start, the click/type/navigate loop, and evidence capture for its
   platform.
3. Resolve the evidence settings and run folder ("Recorded evidence" above)
   before the first scenario.
4. Capture evidence per the adapter's instructions: screenshots always; console/
   network output whenever a criterion concerns errors, loading states, or API
   behavior; videos and bug screenshots saved per "Recorded evidence" above.
5. Hand the captured evidence back to whatever's judging pass/fail — `qa-tester`'s
   own step 6 when invoked from there, or straight into your own response when
   this skill was triggered standalone. Include the saved-file list.
