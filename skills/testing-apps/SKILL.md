---
name: testing-apps
description: Drives a running app to execute test scenarios and capture evidence — Playwright for a web app, or the agent-device CLI (Callstack) for an iOS/Android mobile app — picking the adapter from whether the target is a URL or a device/bundle id. Used as qa-tester's own execution step (its steps 1-2 gather context and derive scenarios, this skill only replaces the browser/device-execution step, its step 6 reports and drafts bugs). Also usable standalone for direct browser or mobile-device exploration or dogfooding without full ticket/PR/Figma context; a standalone run goes to a subagent, so screenshots and snapshots stay out of the main conversation (see "Where a standalone run happens").
when_to_use: "Trigger as qa-tester's own 'Execute' step for any web or mobile target. Also trigger directly for: 'test the iOS/Android app', 'dogfood the mobile app', 'exploratory test on iPhone/Android/simulator/emulator', or driving/exploring a running web app in the browser without a full ticket-driven QA run, including 'przeklikaj', 'sprawdź czy już działa' or a screenshot of a screen. Do NOT trigger for a retest of a Jira ticket or bug (retesting-tickets), or for a macOS or Apple TV target — agent-device also supports those, but this skill's mobile adapter is scoped to iOS/Android handhelds and simulators/emulators only; call agent-device directly for those."
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

## Before you drive anything

Whoever drives the app reads
[references/execution.md](./references/execution.md) before the first action
and follows it: `qa-tester`, a subagent doing a standalone run, and the main
conversation for a single look alike. It holds the shared discipline (sign-in,
the payment hard stop, the pinned target, the project skill), recorded
evidence, keeping the user informed, the adapter table and the procedure. This
file only decides where a standalone run happens and on which branch.

## Picking the adapter

A URL means the web adapter (Playwright); a bundle id, an App Store/TestFlight
name, or "iOS app"/"Android app" in the request means the mobile adapter
(`agent-device`). The table, the adapter files and what's out of scope (macOS,
Apple TV) are in [references/execution.md](./references/execution.md),
"Picking the adapter".

## Where a standalone run happens

Every screenshot and page snapshot stays in the context of the conversation
that took it, and that whole context is sent again with every later turn. So a
standalone run (exploration, dogfooding, "check whether X works now")
**runs in a subagent**, not in the main conversation. `qa-tester` runs are
subagents already. A retest of a Jira ticket or bug is the `retesting-tickets`
skill: it reads the ticket and its related issues and uses this skill's
execution itself.

1. **In the main conversation, gather the brief** (ask only what's missing): the
   target (URL, or device and app), environment and branch, which account to
   sign in with, what to check and what counts as working, whether to
   record evidence (`mode: ask` in evidence.json), and the product's working
   directory and project skill if the target matches a product config. Resolve
   the branch and environment per "Standalone runs: which branch and
   environment" below. Run the setup check:
   `python3 -I "$(dirname "$(dirname "$(readlink ~/.claude/agents/qa-tester.md)")")/skills/updating-qa-agent/scripts/check_setup.py"`.
   If it prints a warning, show it to the user and offer to update first
   (`./setup.sh`, then the `updating-qa-agent` skill). If they'd rather test
   now, continue; outputs then fall back as the warning says. Don't open the
   browser or device here.
2. **Start a subagent** (`general-purpose`, model `sonnet`; model `opus` for
   this run only when the user asks for Opus, e.g. "puść na Opusie") with that brief and
   the instruction: "Load the testing-apps skill and follow it as a standalone
   run inside a subagent. You can't ask the user: if something the brief
   doesn't answer blocks the run, stop and report what's needed." For a
   ticket-driven check, start `qa-tester` instead. If you are that subagent,
   this section is already done: go straight to references/execution.md.
3. **Relay its summary** (Done / Not done / Proposed additions) and the saved
   files. If it stopped on a question, ask the user and continue the same
   subagent with the answer rather than starting a new one.

Stay in the main conversation only for a single look, about three browser or
device actions at most (open one page, take one screenshot, read one value),
or when the user explicitly asks to drive it here. Even then, read
references/execution.md before the first action.

## Standalone runs: which branch and environment

Run standalone (no ticket or PR, not inside `qa-tester`), this skill tests the
product's staging-like branch and the environment deployed from it. Follow
[target-branch.md](./references/target-branch.md): user's message, then config
`targetBranch`, then detection from merged MRs, then ask. That reference also
explains how the branch maps to the app URL or mobile build, and how recent MRs
on it set what to explore first. Inside `qa-tester`, the ticket and PR decide
the branch instead.
