---
name: maestro-e2e
description: Sets up, writes, fixes and stabilises Maestro e2e flows (YAML) for an iOS/Android app on a simulator or emulator, through the Maestro MCP server or CLI — whether the flows live in the app's own repo or, when there is no access to the app's code, in a separate tests repo or local folder (asks where on first use and remembers it per product). Boots a simulator/emulator itself when none is running and installs the user-supplied .app/.apk when the app is missing. Also turns manual test cases that passed (from qa-tester / writing-test-cases) into regression flows, migrates XCUITest/Espresso tests, and debugs flaky flows. Covers exploring the accessibility tree, launch arguments, system alerts, WebView content, loading placeholders and driver quirks.
when_to_use: "Trigger on: 'chcę coś zrobić w Maestro', 'napisz flow/test Maestro dla X', 'set up Maestro for this app', 'automate these test cases in Maestro', 'zautomatyzuj te przypadki', 'fix this flaky Maestro flow', 'run the Maestro suite', migrating XCUITest/Espresso to Maestro. Do NOT trigger for one-off manual/exploratory QA of a ticket/PR on a device without writing a flow — that is qa-tester / testing-apps' mobile adapter (agent-device)."
---

# Maestro e2e flows

Maestro drives an installed build of the app from the outside, through the
accessibility tree. It needs no test target, no rebuild and **no access to the app's
code** — only the app id and a booted simulator/emulator with the build installed.
So flows can live next to the app code or entirely on their own.

Run this skill in the main conversation, not inside a subagent: step 1 asks the user
questions.

## 1. Resolve the product and where its flows live

1. Find the product's config in `~/.claude/environments/*.json` (by product name,
   ticket prefix, or repo path) and read its `maestro` block:
   ```json
   "maestro": {
     "appId": { "ios": "com.acme.app.debug", "android": "com.acme.app.debug" },
     "location": "app-repo | tests-repo | local",
     "flowsDir": "~/Projects/acme-mobile-e2e/.maestro",
     "build": {
       "ios": "~/Builds/acme/Acme.app",
       "android": "~/Builds/acme/acme-staging.apk",
       "notes": "where a fresh build comes from (CI artifact link, who to ask)"
     }
   }
   ```
   If it's there and `flowsDir` exists, use it and go to step 2. `build` is
   optional — filled in by step 2 the first time a build has to be installed.
2. Otherwise ask the user (AskUserQuestion), one question:
   - **App repo** — `<app repo>/.maestro/`. Best when the team owns the app code:
     flows version together with the app, and launch arguments / accessibility ids can
     be looked up in the code.
   - **Separate tests repo** — e.g. `~/Projects/<product>-mobile-e2e/.maestro/`. For an
     app whose code you don't have (or can't commit to); shareable with the team
     and CI.
   - **Local folder** — e.g. `~/QA/<product>/maestro/.maestro/`. Private, nothing
     committed; fine for exploration or a short engagement.
   Then ask for the path (propose the default above) and the app id if unknown.
3. Offer to save the answer as the `maestro` block of that product's config (show the
   JSON, write only after confirmation), so the question isn't asked again. If no
   config file exists for the product, point to the `configure-project` skill
   instead of inventing one.

## 2. Get a device running with the app installed

Booting a simulator/emulator and installing a build are local and reversible — do
them yourself instead of stopping. What you can't do is produce the build: the user
supplies the file.

1. **Preflight:** `~/.claude/skills/maestro-e2e/scripts/device-preflight.sh <app-id>`.
   It finds Maestro, Java 17+, Xcode's `simctl` and the Android SDK even when they're
   not on PATH (prefix later `maestro`/`xcrun`/`adb`/`emulator` commands with the
   `export` lines it prints), and lists booted devices, shut-down simulators/AVDs, and
   whether the app is installed on each running one. A missing tool → tell the user
   the install command it prints; don't work around it.
2. **Pick the platform** from the request or the config's `appId`; ask only if the app
   exists on both and nothing says which.
3. **A matching device is already running** → use it. Several → ask which (a physical
   phone may be the user's own: never pick it silently over an emulator).
4. **None running** → boot one yourself:
   - iOS: an existing shut-down simulator — `xcrun simctl boot <udid> && open -a Simulator`
     (with `DEVELOPER_DIR` from preflight). Several → prefer a recent iPhone, ask only
     if the choice matters (e.g. the ticket is about a specific model/size).
   - Android: an existing AVD — `emulator -avd <name> -no-snapshot-save` with
     `run_in_background`, then wait for `adb wait-for-device shell getprop sys.boot_completed`
     to return `1` (poll with Monitor, not sleep).
   - **Nothing exists** (no simulator/no iOS runtime, no AVD) → `maestro start-device
     --platform <ios|android>` creates one, but it may download a multi-GB image:
     ask before running it. If iOS has no runtime at all, the user installs it in
     Xcode > Settings > Components.
5. **App not installed** (preflight says `NOT installed`, or `launchApp` fails with
   "app not installed") → take the file from `maestro.build` in config, else ask for it:
   - iOS simulator: a **simulator** build `.app` (folder; a zipped one is fine — unzip
     it to the scratchpad). An `.ipa` from TestFlight/App Store does not install on a
     simulator — say so and ask the devs for a simulator build.
     `xcrun simctl install <udid> <path>.app`
   - Android: any `.apk` (`adb -s <serial> install -r <path>.apk`). An `.aab` needs
     `bundletool` — ask for an `.apk` instead.
   After installing, confirm with the preflight again, then offer to save the path
   (and where new builds come from) as `maestro.build` in the config.
6. **Installed but maybe stale** → don't reinstall on your own; mention the installed
   version (`simctl appinfo` / `adb shell dumpsys package <id> | grep versionName`) in
   the report so the user knows what was tested.

Then `list_devices` (Maestro MCP) and use the `device_id` it returns for every
`run`/`inspect_screen`. Leave the device running when done unless the user asks to
shut it down. A physical iPhone is out of scope here (Maestro's iOS real-device
support is limited) — use a simulator; a physical Android over USB works like an
emulator.

## 3. Set up the suite if `flowsDir` is empty

Copy the starter: `cp -R ~/.claude/skills/maestro-e2e/assets/starter/.maestro <parent of flowsDir>/`
(it's self-contained — `run-flows.sh` resolves paths from its own location, so it
works in any folder). For a fresh tests repo, `git init` only if the user wants it.
Then fill in *Project specifics* in `.maestro/README.md`:

- **App id** — from config/user; if unknown, list installed apps
  (`xcrun simctl listapps booted | grep CFBundleIdentifier`, `adb shell pm list packages`).
- **How the build gets on the device** — the file and steps from step 2; don't build
  the app yourself unless asked.
- **Launch arguments the app reads** — with the app repo: search the code for where
  they're handled. **Without the app repo: don't guess** (an argument the app doesn't
  read is silently ignored). Ask the user/devs for the list; if there is none, remove
  the placeholder arguments from `subflows/launch-app.yaml` and let the start subflow
  click through onboarding/consent/system prompts instead — and note in the README
  that debug launch arguments would make the suite faster and steadier, as an ask
  for the dev team.

## 4. Read the Standard, then reuse

Read the Standard in `.maestro/README.md` — it is the single source for layout,
selectors, waiting, reuse, `retry`, tags and the 5-green-runs rule; follow it over
your own habits. Read `config.yaml`, the existing `subflows/` and one or two flows of
the same feature; reuse a start subflow and existing steps instead of writing new ones.

## 5. Write a flow

When the input is manual test cases (a qa-tester report or a writing-test-cases
table), each case is one candidate flow: Preconditions → start subflow / `env`, Steps
to reproduce → flow steps, Expected result → final assertions. Automate only cases
that passed manually; a case that found a bug is reported back, not encoded as a flow
that expects the bug.

1. Put the app on the screen of the step you're writing (`run` with inline YAML: the
   start subflow plus the steps written so far).
2. `inspect_screen` and copy ids and texts verbatim from the hierarchy (CLI:
   `maestro --device <id> hierarchy --compact | grep -E "resource-id=|text=|accessibilityText="`).
   Never take a selector from a screenshot and never guess one. `id` first, `text`
   only where there is no id (with a comment why), never coordinates, never `sleep`.
3. Add one step, run it, inspect again. Repeat until the scenario ends with an
   assertion of the expected result.
4. Run the whole file from a clean state: `maestro test <file>`.
5. Tag it: feature tag always, `wip` until it is stable.

## 6. Debug a failing flow

1. Read the failure in `~/.maestro/tests/<latest>/` (`maestro.log`, screenshot,
   driver logs).
2. Separate infrastructure from the test: `DeviceUnreachableException`,
   `IOSDriverTimeoutException` or "Snapshot failure" mean the driver or a tired
   simulator. Reboot the device and rerun before changing the flow.
3. Reproduce on the device up to the failing step and inspect the real screen. Fix the
   cause (a missing wait on screen state, a disabled placeholder, an element off the
   viewport), never with `sleep` or a `retry` around the whole test.

## 7. Done means

- The new or changed flow passed 5 runs in a row
  (`<flowsDir>/run-flows.sh -d <device-id> -r 5 <flow-name>`); report the summary line.
- `wip` removed once stable; `smoke` only if the user asked for it.
- No real credentials in the flow; test data comes from `env`.
- Report: files changed (and where — app repo / tests repo / local), what each flow
  covers, the 5-run result, and any app-side problem found (missing accessibility id,
  real bug). Never change app code, launch arguments or accessibility ids yourself —
  propose the change; a real bug goes to `reporting-bugs` as a draft.

## Gotchas

- **Launch arguments (iOS):** Maestro drops the leading `-` of the first `launchApp.arguments` key,
  so write every key with its dash and check in the log what the app received. To force a language,
  pass it with a region (`-AppleLanguages (en-GB)`, `-AppleLocale en_GB`), as on a real device: apps
  that derive a market or region from the locale get nothing from a bare language code.
- **System alerts:** prefer skipping a system prompt in the app (a debug launch argument) over
  answering it from the flow. On iOS, setting `permissions` for a prompt the app shows later can make
  the driver tap the alert by coordinates on every screen read, and a stray tap lands in the app. An
  alert that does show up (e.g. "Save Password?") hides the whole app from the hierarchy until it is
  dismissed.
- **WebView:** WebViews do not expose HTML ids to Maestro; select by visible label or placeholder.
  Fields behind the keyboard can still be reported visible, so `hideKeyboard` before scrolling on.
- **Viewport only:** Maestro sees what is on screen. Reach lower elements with `scrollUntilVisible`,
  and use `centerElement: true` when a sticky bar may cover them. An element partly off screen in a
  horizontal row may have its centre outside the screen, where a tap misses: swipe the row first.
- **Scrolling:** `scrollUntilVisible` swipes from the screen's centre. A slow drag that starts on a
  button or card can be taken as a press and the page does not move; swipe from a plain text element
  instead. A drag that starts on a tab bar can tap the active tab and scroll the screen to the top.
  One swipe can carry a long list past the target, and `scrollUntilVisible` only goes on in its own
  direction: for a target in a long list, search back the other way (`optional: true` on the first
  pass) and keep `speed` low.
- **Loading placeholders:** skeleton/redacted placeholders often carry the same ids as the real
  content but are disabled; select with `enabled: true`. Wait for the loading indicator to disappear
  before reading a value from a list that can still re-sort.
- **Regex:** `id:` and `text:` are full-string regexes; escape values copied from the screen before
  matching them, and match the whole string, not a fragment.
- **Absence:** `assertNotVisible` passes the moment nothing is there. When something could still
  appear, give it a window first (`extendedWaitUntil` with `optional: true`), then assert.
- **Slow conditions:** `when: visible` on an absent element waits for the screen to settle and can
  cost several seconds while the UI is moving; check rare screens on a settled screen.
- **Tired simulator:** if XCTest starts failing to read the screen ("Snapshot failure" in
  `xctest_runner_*.log`) on a screen that renders fine, reboot the simulator before touching the flow.
- **Driver crash:** `DeviceUnreachableException` or `IOSDriverTimeoutException` in the logs is the
  driver dying, not a test failure; `run-flows.sh` reruns such a flow once and reports `INFRA_RETRY`.
