# Mobile adapter (agent-device)

Load this when the target is an iOS/Android device/simulator/emulator — a bundle
id, an App Store/TestFlight name, or the request explicitly says "iOS app"/
"Android app". Same job as the [web adapter](./web.md), retargeted at a native
app: drive it with the `agent-device` CLI (Callstack) instead of a browser.

**Scope: iOS and Android only.** `agent-device` also drives macOS, TV, and web
targets, but this adapter's rules (physical-device signing, the points/pixels
conversion, the daemon-env gotcha) are specific to mobile simulators/emulators and
handheld devices. If the delegated target is a desktop/TV/web app, don't use this
adapter — call `agent-device` directly, or use the web adapter if the target is
actually a web page.

## Non-negotiable rules

| Rule | Why |
| --- | --- |
| `agent-device press <x> <y>` takes iOS **points**, not screenshot pixels. Divide screenshot pixel coordinates by the device's scale factor (3x on most modern iPhones) before passing them. | Wrong units silently tap the wrong spot with no error — looks exactly like a dead button. |
| Before reporting any control as "does nothing" / "dead button", retest it twice: once via its `@eN` ref from a fresh `snapshot -i`, once via the correctly-converted point coordinate of its visible center. Only report broken if **both** fail. | A ref tap and a coordinate tap can legitimately disagree — see "Accessibility hit-frame checks" below. Reporting off one tap alone risks a false positive. |
| Always pass `--device "<exact name>"` explicitly once more than one device/simulator matches. | Ambiguous matches fail the command outright (`AMBIGUOUS_MATCH`). |
| If a physical iOS device is being used for the first time this session, or `open`/`snapshot` fails on signing/provisioning/Developer Mode, read [physical-device-setup.md](./physical-device-setup.md) before improvising. | The setup is multi-layered (device, macOS, Xcode, Apple account) and fails with a different error at each layer — guessing burns turns. |
| Every run starts with a clean build and install (uninstall the app, rebuild the native project from your own worktree, install the fresh build) unless the product config's `installMode` says otherwise. Never test whatever is already installed by default. See "Clean build and install, every run". | A build left on the device may be stale, from another branch, or a legacy app with a similar name, and its leftover data and sessions hide first-launch bugs. A failed build is a blocker, not a reason to test the old copy. |
| When building from source, reserve the Metro port with `scripts/metro-port.sh reserve`, pass it to the build as `--port`, and release it at the end. See "Building from source in parallel". | Parallel runs on two devices otherwise collide on one port and block each other's builds. |
| Never accept a device passcode, Apple ID password, or macOS/sudo password typed into the chat. Tell the user to type it into the native prompt (Terminal, Xcode, the device) themselves. | Chat history is not a credential store; treat a pasted password as a signal to warn, not to use. |

(The real-account/real-transaction boundary is in the parent skill's Shared
discipline — a physical device signed into the tester's own real account just
makes "real account" the default there rather than the exception.)

## Accessibility hit-frame checks (a deliberate technique, not just a gotcha)

Comparing "tap via `@eN` ref" against "tap via the correct visual point coordinate" for
the same control is a cheap way to catch controls whose accessibility hit-frame is
decoupled from where they're actually rendered — the control works for a sighted
finger-tap but is unreachable for VoiceOver/Switch Control or any accessibility-driven
automation. Run this comparison explicitly (not just when a tap "fails") on apps whose
purpose involves accessibility, and report a confirmed mismatch as its own finding —
it's a high-value, easy-to-miss defect class distinct from an ordinary dead button.

## Procedure

1. Confirm `agent-device` is on PATH (`agent-device --help`). If missing, tell the user
   it needs installing (`npm install -g agent-device`) rather than silently falling
   back to the web adapter on a mobile target.
2. Discover the target: `agent-device devices [--platform ios|android]` to pick a
   device/simulator, `agent-device apps --device "<name>"` to find the app's bundle id
   if only its display name is known.
   Then do the build and install per "Clean build and install, every run" below
   (clean unless `installMode` says otherwise), before opening the app.
3. `agent-device open <bundle-id> --device "<name>" --foreground` to start the session,
   then `agent-device snapshot -i` for the first interactive snapshot with `@eN` refs.
4. Pick the loop that matches the ask and follow it as documented — don't
   reimplement it from memory:
   - Open-ended exploratory/bug-hunt → `agent-device help dogfood`.
   - Executing a specific written script/test case → `agent-device help manual-qa`.
   Both guides cover navigation mapping, evidence capture per finding, and the
   report shape; `agent-device help workflow` has the full refs/selectors/waits
   reference if a command's exact shape is unclear.
5. Capture evidence as you go: `agent-device screenshot <path>.png` (add
   `--overlay-refs` to show which element is which). Read every screenshot back
   before judging pass/fail — see "Shared discipline" in the parent skill
   (`../../SKILL.md`). Record videos and save bug screenshots per "Recording"
   below.
6. `agent-device close` when the session ends, then do the cleanup in "Building from
   source in parallel" if you built the app.

## Recording

What to record, and where it goes, is set in the parent skill's "Recorded
evidence" section. The mobile mechanics:

- **Video:** run `agent-device record start <run folder>/happy-path/<scenario-id>-<slug>.mp4`
  after `open`, then `agent-device record stop` when the scenario ends. Stop it in
  the same `--session` that started it. The default `--scope app` needs an active
  app session. Use `--scope device` only if a step leaves the app (system
  Settings, Control Center).
- **Android:** a recording longer than 180 s comes back as several MP4 chunks.
  Keep all of them, numbered `-part1`, `-part2`, and so on.
- **iOS simulator:** `DEVICE_IN_USE` with reason `apple_simulator_recording_busy`
  means another session's recorder holds the simulator. Don't retry in a loop.
  Report the video as missing and continue.
- **Bug screenshot:** `agent-device screenshot <run folder>/bugs/<bug-n>-<slug>.png`.
- If a scenario recorded into `happy-path/` fails, `mv` its video into `bugs/`.

## Clean build and install, every run

Applies to simulators, emulators and physical devices alike. The product's
environment config (`surfaces.mobile`) supplies the repo, build command and
signing quirks.

**Install mode.** Read `installMode` from the product's mobile surface in its
environment config. A mode named in the brief overrides it for that run.

| `installMode` | What the run does |
| --- | --- |
| `clean` (default, also when the field is missing) | All five steps below. |
| `update` | Steps 1, 3, 4 and 5, skipping the uninstall. The fresh build installs over the existing app and keeps its data. Use it to test upgrades or a flow that needs an existing login. |
| `installed` | No build or install. Test the app already on the device, and log its version and build number (from `agent-device apps` or the app's About screen) in step 5. |

Any other value: treat it as `clean` and say so in the report. Whatever the
mode, log it in the run log. For `update` and `installed`, also list it under
"Not done / skipped" as "clean install skipped: installMode=<mode>".

The steps, in an order that never changes:

1. **Fresh worktree.** Check out the ticket's branch (or the PR head) in your own
   new worktree. On a standalone run, check out the target branch from
   [target-branch.md](../target-branch.md) instead. Then and install JS dependencies there. Never build from the shared
   checkout. Record the commit (`git rev-parse --short HEAD`).
2. **Uninstall the app from the device**, so no data, session, keychain-backed
   login or cache survives from an earlier run. Use the bundle id/package the
   build produces (check the config's `knownCaveats`, which can differ from
   `app.json`):
   - iOS simulator: `xcrun simctl uninstall <udid> <bundle-id>`
   - iOS physical device: `xcrun devicectl device uninstall app --device <udid> <bundle-id>`
   - Android: `adb -s <serial> uninstall <package>`

   "Not installed" is fine; any other error is a blocker. Don't use `agent-device
   reinstall` instead: it replaces the binary but isn't guaranteed to wipe app
   data.
3. **Regenerate the native projects.** For Expo, `npx expo prebuild --clean`
   (then apply any worktree-only signing overrides the config describes, and
   `pod install` in `ios/` if its caveats say so). For a bare React Native or
   native app, clean the build output (`xcodebuild clean` / `./gradlew clean`).
4. **Build and install** with the config's build command and a reserved Metro
   port (see "Building from source in parallel"). Then confirm with
   `agent-device apps --device "<name>"` that the bundle id is installed.
5. **Log it.** Put commit, branch, bundle id, device and install time in the run
   log, so the report shows exactly which build was tested.

If any step fails, stop and report a blocker with the failing command and its
error. Never fall back to an app that's already on the device. Only
`installMode: installed` (from config or the brief) means testing the installed
build. For example, set it in the brief to test a TestFlight or store release.

## Building from source in parallel — never share a Metro port

Another session may be building for a second device on this Mac at the same time.
Two builds on one Metro port block each other, or one device loads the other's
bundle. Picking any "non-default" port isn't enough, because two agents tend to
pick the same one. Every build from source must:

1. **Reserve a free port with the script. Never pick one by hand.**
   `PORT=$(../../scripts/metro-port.sh reserve "<ticket>-<platform>")`. The script
   is at `skills/testing-apps/scripts/metro-port.sh`. It skips any port that is
   listening, that a running expo/metro process was started with, or that another
   run has reserved. The reservation is atomic, so two agents starting together
   still get different ports. If the brief names a port, use it only if
   `lsof -nP -iTCP:<port> -sTCP:LISTEN` is empty. Otherwise reserve a new one and
   say so in the report.
2. **Pass the port to every build and Metro command**, e.g. `expo run:ios --port
   $PORT` / `expo run:android --port $PORT`, or `npm run <script> -- --port $PORT`.
   Never let the build fall back to 8081. For Android, also run
   `adb -s <serial> reverse tcp:$PORT tcp:$PORT` so the device can reach that port.
3. **Build from your own worktree and use your own `--session <name>`.** Never use
   the shared checkout or `default`. Another session can switch the shared
   checkout's branch, or close the `default` session, partway through your run.
4. **Clean up at the end, even on failure or abort.** Kill your processes by
   worktree path (`pkill -f "<worktree path>"`). Stopping an agent does not stop
   its `expo run:*` or xcodebuild; they keep running and keep the port. Then run
   `metro-port.sh release $PORT`. `metro-port.sh list` shows every current
   reservation and whether its port is still listening.

## The daemon keeps stale environment — restart it when signing config changes

`agent-device` starts a background daemon on first use that then persists across
separate shell calls, holding whatever `AGENT_DEVICE_IOS_TEAM_ID` /
`AGENT_DEVICE_IOS_BUNDLE_ID` (or other env vars) were set **at the moment it started**.
Exporting new values in a later command does not reach an already-running daemon —
builds keep using the old team/bundle id with no warning. If you change signing env
vars, or a build fails with an unexpected bundle id/team, kill the daemon and reopen in
the same command:

```
pkill -f "agent-device/dist/src/internal/daemon.js"
export AGENT_DEVICE_IOS_TEAM_ID=...
export AGENT_DEVICE_IOS_BUNDLE_ID=...
agent-device open <bundle-id> --device "<name>" --foreground
```

## Reference loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [Physical iOS device setup](./physical-device-setup.md) | First `open`/`snapshot` on a physical iPhone/iPad this session, or any signing/provisioning/Developer Mode error | Developer Mode, `DevToolsSecurity`, Xcode account + local certificate, one-time device registration with the Apple team, required env vars |
