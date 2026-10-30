# Mobile adapter (agent-device)

Load this when the target is an iOS/Android device/simulator/emulator — a bundle
id, an App Store/TestFlight name, or the request explicitly says "iOS app"/
"Android app". Same job as the [web adapter](./web.md), retargeted at a native
app: drive it with the `agent-device` CLI (Callstack) instead of a browser.

**Scope: iOS and Android only.** `agent-device` also drives macOS, TV, and web
targets, but this adapter's rules (physical-device signing, the points/pixels
conversion, the shared daemon and its signing env) are specific to mobile
simulators/emulators and handheld devices. If the delegated target is a
desktop/TV/web app, don't use this adapter — call `agent-device` directly, or use
the web adapter if the target is actually a web page.

## Non-negotiable rules

| Rule | Why |
| --- | --- |
| `agent-device press <x> <y>` takes iOS **points**, not screenshot pixels. Divide screenshot pixel coordinates by the device's scale factor (3x on most modern iPhones) before passing them. | Wrong units silently tap the wrong spot with no error — looks exactly like a dead button. |
| Before reporting any control as "does nothing" / "dead button", retest it twice: once via its `@eN` ref from a fresh `snapshot -i`, once via the correctly-converted point coordinate of its visible center. Only report broken if **both** fail. | A ref tap and a coordinate tap can legitimately disagree — see "Accessibility hit-frame checks" below. Reporting off one tap alone risks a false positive. |
| Always pass `--device "<exact name>"` explicitly once more than one device/simulator matches. | Ambiguous matches fail the command outright (`AMBIGUOUS_MATCH`). |
| Never kill the `agent-device` daemon (`pkill`, `kill`). On a physical iOS device, run with the signing env and `AGENT_DEVICE_STATE_DIR` set per "The daemon is shared". | One daemon serves every session on the Mac; killing it breaks other sessions' runs, and a restart can lose their signing vars. |
| Before the first `open` on a device, check who holds it with `agent-device device status`, not `agent-device session list`. Close your own session at the end of every run, also on failure. See "Device locks". | `session list` only shows the daemon of the current state dir, so a device held from another state dir looks free. An unclosed session keeps its daemon, and the device, held for days. |
| If a physical iOS device is being used for the first time this session, or `open`/`snapshot` fails on signing/provisioning/Developer Mode, read [physical-device-setup.md](./physical-device-setup.md) before improvising. | The setup is multi-layered (device, macOS, Xcode, Apple account) and fails with a different error at each layer — guessing burns turns. |
| Test the distributed build already installed on the device (TestFlight on iOS; Google Play internal/closed testing or Firebase App Tester on Android) unless the request explicitly asks to build locally (from source, the branch, the PR, a worktree). Only then build, per the config's `installMode`. See "Install source: distributed build by default". | The distributed build is what testers and the client actually get. A local build is slower, needs signing and a Metro port, and is only worth it when the user wants an unreleased branch tested. A failed local build is a blocker, not a reason to test the installed copy. |
| When building from source, reserve the Metro port with `scripts/metro-port.sh reserve`, pass it to the build as `--port`, and release it at the end. If a reopened dev client shows a native-module mismatch, check who owns the port and move to a new one (step 5). See "Building from source in parallel". | Parallel runs on two devices otherwise collide on one port and block each other's builds. |
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
   if only its display name is known. For a **physical** device, connected by cable
   or over Wi-Fi, also run `scripts/list_physical_devices.py` and pick only a row
   with `state=ready`. See "Physical devices: cable or Wi-Fi" below.
   Then pick the install source per "Install source: distributed build by default"
   below (the installed TestFlight/Play/App Tester build unless the request asks
   for a local build), before opening the app.
3. Check the device is free (see "Device locks"), then
   `agent-device open <bundle-id> --device "<name>" --foreground` to start the session
   (on a physical iOS device, with the signing env and state dir from "The daemon
   is shared", and check the daemon got them),
   then `agent-device snapshot -i` for the first interactive snapshot with `@eN` refs.
4. Pick the loop that matches the ask and follow it as documented — don't
   reimplement it from memory:
   - Open-ended exploratory/bug-hunt → `agent-device help dogfood`.
   - Executing a specific written script/test case → `agent-device help manual-qa`.
   Both guides cover navigation mapping, evidence capture per finding, and the
   report shape; `agent-device help workflow` has the full refs/selectors/waits
   reference if a command's exact shape is unclear.
5. Capture evidence as you go: checkpoint screenshots with
   `agent-device screenshot <run folder>/checkpoints/<n>-<slug>.png` (add
   `--overlay-refs` to show which element is which). Read every screenshot back
   before judging pass/fail — see "Shared discipline" in the parent skill
   (`../../SKILL.md`). Record a video of every scenario and save bug folders
   per "Recording" below.
6. `agent-device close --session <yours>` when the session ends, with the same
   `AGENT_DEVICE_STATE_DIR` you opened it with, also when the run fails or is
   aborted. Then do the cleanup in "Building from source in parallel" if you built
   the app.

## Device locks: check the claim, not the session list

A device belongs to one session at a time. The claim is a file in
`~/.agent-device/device-claims/`, shared by every daemon on the Mac, and stays
valid as long as the daemon that owns it is alive. `agent-device session list`
only asks the daemon of the current `AGENT_DEVICE_STATE_DIR`, so it can come back
empty while another state dir's daemon holds the device. On 28.10.2026 a session
left open by a run two days earlier, in its own state dir, held both the iPhone
and the Samsung; the session list was empty and the device was reported free.

1. **Before the first `open`**, run
   `agent-device device status --platform <ios|android> --udid <udid>` (or
   `--serial <serial>`). It reads the claims without contacting a daemon. A
   `live session=<name>` that isn't your session means the device is held.
2. **Clear only provably dead claims yourself:** `agent-device device release
   --stale` (add `--platform` and `--udid`/`--serial`). It refuses live and
   uncertain owners, so it's safe to run.
3. **A live owner that isn't yours:** read its claim file
   (`grep -l '<udid or serial>' ~/.agent-device/device-claims/*.json`), which names
   `session`, `ownerPid`, `ownerStartTime` and `stateDir`. Check the process with
   `ps -o lstart=,command= -p <ownerPid>`. Then stop and report a blocker with
   those four values. Don't close that session, stop its daemon, or retry in a
   loop: it may be a parallel run that is still going. If the owner looks
   finished (started on an earlier day, no Claude session working on it), say so
   and give the user the commands to free it:
   `AGENT_DEVICE_STATE_DIR=<stateDir> agent-device close --session <session>`, and
   if the claim survives, `agent-device daemon stop --state-dir <stateDir>`.
   Re-check with `device status` before opening.
4. **Use only the state dirs this file names:** the default one, or the
   signing-config folder from "The daemon is shared". A state dir invented per
   ticket or per run (`~/.agent-device-<ticket>`) is invisible to every other
   session's `session list`, and it's where the locks above came from.

## Physical devices: cable or Wi-Fi

A physical device can be attached by USB cable or over Wi-Fi (Android Wireless
debugging, iOS "Connect via network"). Both count as connected. Don't ask the user
to plug in a device that is already reachable over Wi-Fi.

`agent-device devices` alone can't tell you which devices are reachable. It lists
every *paired* iPhone/iPad as `booted=true`, including ones that are asleep or off
the network. Run the discovery script instead:

```
python3 -I ../../scripts/list_physical_devices.py [--platform ios|android] [--connect]
```

It prints one row per physical device with its `id` (UDID or adb serial),
`transport` (`usb` / `wifi`) and `state`. iOS rows come from `xcrun devicectl`.
Android rows come from `adb devices -l` plus `adb mdns services`. Only a `ready`
row can be tested. Every other state says what the user has to do. Pick by `id`:
`--udid <udid>` on iOS, `--serial <serial>` on Android. Device names repeat (two
"iPhone (Michał)"), an id doesn't. Log the transport in the run log.

**Android over Wi-Fi**

- The serial is `<ip>:<port>`, or `adb-<serial>-<suffix>._adb-tls-connect._tcp`.
  Use it everywhere a serial goes: `--serial`, `adb -s`, `adb reverse`.
- The port changes every time Wireless debugging reconnects (screen lock, Wi-Fi
  drop, reboot). If a command fails with `device offline` / `not found`, re-run the
  script with `--connect`. That runs `adb connect` for each device still
  advertised over mDNS, then reports the new serial. Don't reuse the old one.
- A device that was never paired with this Mac needs `adb pair <ip>:<pair-port>`
  and the 6-digit code from **Developer options > Wireless debugging > Pair device
  with pairing code**. The user reads that code off the device. Ask them for it;
  don't guess.
- `adb reverse tcp:$PORT tcp:$PORT` works over Wi-Fi as well, so Metro setup is
  the same as over USB.

**iOS over Wi-Fi**

- Works for devices that `devicectl` lists (CoreDevice, iOS 17+). Install,
  uninstall, launch, logs and recording all go over the network.
- `not-reachable` means the device is paired but has no live tunnel right now. Ask
  the user to wake and unlock it and keep it on the same Wi-Fi as the Mac. Opening
  **Xcode > Window > Devices and Simulators** often brings the tunnel back. Then
  re-run the script.
- A device that only `xctrace` sees (older iOS, XCTest backend) needs a cable.
  `agent-device help physical-device` says its runner goes through usbmuxd.
- Wi-Fi is slower than USB. The first runner build and install can take minutes.
  On a timeout, retry once with `--debug` before calling it a blocker.

**Both platforms.** The device has to reach the Mac's IP (Metro, local API). A
VPN on the Mac or the device can block that even when adb/devicectl look fine.
Check `route get <device ip>` before filing a device-only network error as an app
bug.

## Recording

What to record, and where it goes, is set in the parent skill's "Recorded
evidence" section. The mobile mechanics:

- **Video:** run `agent-device record start <run folder>/testing/<category>/<scenario-id>-<slug>.mp4`
  after `open`, then `agent-device record stop` when the scenario ends. Do this
  for every scenario, not just the happy path. Stop it in the same `--session`
  that started it. The default `--scope app` needs an active app session. Use `--scope device` only if a step leaves the app (system
  Settings, Control Center).
- **Android:** a recording longer than 180 s comes back as several MP4 chunks.
  Keep all of them, numbered `-part1`, `-part2`, and so on.
- **iOS simulator:** `DEVICE_IN_USE` with reason `apple_simulator_recording_busy`
  means another session's recorder holds the simulator. Don't retry in a loop.
  Report the video as missing and continue.
- **Bug screenshot:** `agent-device screenshot <run folder>/bugs/<bug-n>-<slug>/screenshot.png`.
- If a scenario fails, rename its video with a `-FAIL` suffix and `cp` it to
  `bugs/<bug-n>-<slug>/video.mp4`. The original stays under `testing/`.

## Install source: distributed build by default

Applies to simulators, emulators and physical devices alike. The product's
environment config (`surfaces.mobile`) supplies the repo, build command and
signing quirks.

**Default: the installed distributed build.** Unless the request explicitly asks
to build locally, test the app already installed on the device from TestFlight
(iOS), Google Play internal/closed testing, or Firebase App Tester (Android).
Don't build, don't uninstall.

1. Confirm the bundle id/package is installed: `agent-device apps --device "<name>"`.
   Check the config's `knownCaveats` for the right id, and don't pick a legacy
   app with a similar name.
2. Log its version and build number (from `agent-device apps`, the app's About
   screen, or the TestFlight/App Tester listing) and the distribution channel in
   the run log, so the report shows exactly which build was tested.
3. When testing a ticket or PR, say in the report whether that build is known to
   contain the change (release notes, version, or build date after the merge). If
   you can't tell, say so under "Not done / skipped" rather than assuming it does.
4. If the app isn't installed, or the device has a local dev build instead of a
   distributed one (a dev client that asks for a Metro server), stop and report a
   blocker asking the user to install the build from TestFlight/Play/App Tester.
   Don't fall back to a local build on your own.

Leftover data from an earlier run stays on the device in this mode. Sign out
before you start, and list "clean install skipped: distributed build" under
"Not done / skipped".

**Local build: only when the request asks for it.** Phrases like "build it
locally", "from source", "from the branch/PR", "fresh build", or a brief naming
`installMode: clean`/`update`. Then read `installMode` from the product's mobile
surface in its environment config. A mode named in the brief overrides it for
that run.

| `installMode` | What the run does |
| --- | --- |
| `clean` (default, also when the field is missing) | All five steps below. |
| `update` | Steps 1, 3, 4 and 5, skipping the uninstall. The fresh build installs over the existing app and keeps its data. Use it to test upgrades or a flow that needs an existing login. |
| `installed` | No build. Use the distributed-build steps above. |

Any other value: treat it as `clean` and say so in the report. Whatever the
mode, log it in the run log. For `update`, also list it under "Not done /
skipped" as "clean install skipped: installMode=update".

The steps, in an order that never changes:

1. **Fresh worktree.** Check out the ticket's branch (or the PR head) in your own
   new worktree under `<workDir>/worktrees/<ticket or branch>` (the product's
   working directory; add `-2`, `-3`, ... if it's taken). On a standalone run,
   check out the target branch from [target-branch.md](../target-branch.md)
   instead. Then install JS dependencies there with the package manager the
   lockfile belongs to (`yarn.lock` → yarn, `package-lock.json` → npm). Never build
   from the shared checkout. Record the commit (`git rev-parse --short HEAD`).

   A new worktree has none of the shared checkout's git-ignored files. Before
   building, and before any `expo start`:
   - **Env file.** If the repo keeps per-environment files (`.env.stage`,
     `.env.demo`, ...) and the app reads `.env`, copy the one for the environment
     under test to `.env`. The product config's caveats say which file points at
     which backend. Then check the API URL variable in `.env` is set. Without it
     the build or Metro bundle runs with no API URL, and every network call fails
     in a way that looks like an app bug.
   - **Android SDK path.** If `ANDROID_HOME` isn't set, write
     `sdk.dir=<path>` (usually `$HOME/Library/Android/sdk`) to
     `android/local.properties` after step 3, which regenerates `android/`.
     Otherwise Gradle stops with `SDK location not found`.
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
error. One exception: an iOS build that fails with `internal error in Code Signing
subsystem` (xcodebuild exit 65) is a known transient Xcode error. Re-run the same
build command once; it's incremental and usually succeeds. Only a second failure
is a blocker. Never fall back to an app that's already on the device once a local
build was asked for.

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
   its `expo run:*` or xcodebuild; they keep running and keep the port. This
   pattern only matches your worktree; never widen it to `agent-device`, whose
   daemon other sessions share (see "The daemon is shared"). Then run
   `metro-port.sh release $PORT`. `metro-port.sh list` shows every current
   reservation and whether its port is still listening.

   Never stop Metro or expo processes in bulk or by anything but your own worktree
   path: not `pkill -f expo`, `pkill -f metro` or `pkill node`, not
   `kill $(lsof -ti :<port>)`, and not another worktree's path. A Metro you didn't
   start may be serving a dev client that a session still open is testing; once
   it stops, that app has no JS to load. This also applies to cleanup commands
   you hand the user: on 28.10.2026 a suggested cleanup of an "old" run's Metro
   killed two Metros that a session still waiting on the user depended on. If
   another worktree's process is in your way, report its PID, worktree and start
   time, say you can't tell whether a session still uses it, and let the user
   decide. Reserve a different port in the meantime.
5. **Wrong bundle on reopen: start your own Metro on a new port.** A dev client
   remembers the last Metro URL. After your Metro stops and its port is released,
   another session can start its Metro on that port, and reopening the app loads
   that session's JS. That JS is built from a different branch, so it doesn't match
   your build's native code. It typically shows as a red screen such as
   `Cannot find native module '<Name>'`, `TurboModuleRegistry ... could not be
   found`, or another native-module or SDK-version mismatch. Before treating such an
   error as an app bug, check who owns the port. `lsof -nP -iTCP:<port>
   -sTCP:LISTEN` gives the PID, and `lsof -a -p <pid> -d cwd -Fn` gives its
   worktree. If that worktree isn't yours:
   - Don't stop or reuse the other session's Metro.
   - Reserve a new port with `metro-port.sh reserve`, and start Metro from your own
     worktree on it (`npx expo start --port $PORT --dev-client`, after loading the
     worktree's `.env`).
   - On Android, run `adb -s <serial> reverse tcp:$PORT tcp:$PORT`.
   - Point the dev client at your Metro: press `a`/`i` in Metro, open the
     dev-client URL with `--url http://localhost:$PORT`, or choose that server in
     the dev launcher.
   - Report the mismatch in the run log, not as a defect.

   The same applies when you hand the device back. The installed dev client stays
   bound to your released port, so the report must say which worktree and command
   start a matching Metro.

## The daemon is shared — give a signed run its own, never kill one

`agent-device` starts a background daemon on first use that then persists across
separate shell calls, holding whatever `AGENT_DEVICE_IOS_TEAM_ID` /
`AGENT_DEVICE_IOS_BUNDLE_ID` (or other env vars) were set **at the moment it started**.
Exporting new values in a later command does not reach an already-running daemon —
builds keep using the old team/bundle id with no warning.

That default daemon (state dir `~/.agent-device`) is one process for every Claude
session on this Mac. Never `pkill` it, and never stop it yourself: other sessions'
runs go through it, and killing it on 19.10.2026 broke the runs in parallel windows
(user, 28.10.2026). Whatever command starts it next decides its environment, so a
restart can also drop the signing vars another session relies on.

Instead, each `AGENT_DEVICE_STATE_DIR` runs its own daemon, started with the
environment of the command that starts it. For a physical iOS device (the only
target that needs signing vars), run every `agent-device` command with a state dir
named after the signing config. Shell state doesn't carry between calls, so put the
three exports in front of each command:

```
export AGENT_DEVICE_IOS_TEAM_ID=<team id>
export AGENT_DEVICE_IOS_BUNDLE_ID=<runner bundle id>
export AGENT_DEVICE_STATE_DIR="$HOME/.agent-device-signing/$AGENT_DEVICE_IOS_TEAM_ID-$AGENT_DEVICE_IOS_BUNDLE_ID"
agent-device open <bundle-id> --device "<name>" --foreground
```

- Same team and bundle id, same daemon: parallel sessions with the same signing
  config share it safely, and the built runner is reused between runs.
- Changed team or bundle id, new folder, new daemon with the new values. Nothing has
  to be stopped.
- The daemon exits by itself after 5 minutes idle with no open sessions. Device
  claims are host-wide, so two daemons still can't take the same device.
- After the first `open`, check that `$AGENT_DEVICE_STATE_DIR/daemon.json` exists.
  If it doesn't, the installed `agent-device` ignores the variable: stop and tell
  the user to update it (`npm install -g agent-device@latest`), don't fall back to
  the shared daemon with stale signing.
- Then confirm the daemon serving that state dir really has the signing vars.
  Exporting them on a call doesn't reach a daemon that was already running:
  ```
  for p in $(pgrep -f internal/daemon.js); do echo "pid $p"; ps eww -p $p | tr ' ' '\n' | grep -E '^AGENT_DEVICE_(STATE_DIR|IOS_TEAM_ID|IOS_BUNDLE_ID)='; done
  ```
  The daemon whose `AGENT_DEVICE_STATE_DIR` is yours must show your team and bundle
  id. If it doesn't, don't run scenarios on it and don't kill it. Use a new state
  dir instead, or report it.
- Know the symptom of a daemon without them. The runner build in
  `$AGENT_DEVICE_STATE_DIR/sessions/<session>/runner.log` fails with
  `No Account for Team "2S799L9W4M"` or `No profiles for
  'com.callstack.agentdevice.runner'`; that's agent-device's own default team, not
  the user's. With a runner that was already built, it shows up instead as
  `Daemon request timed out` and `** BUILD INTERRUPTED **`, which looks like a
  Wi-Fi or VPN problem. Check the runner log and the daemon's environment before
  blaming the network.
- If the user exports `AGENT_DEVICE_IOS_TEAM_ID` and `AGENT_DEVICE_IOS_BUNDLE_ID`
  in `~/.zshenv`, every daemon starts with them, including one another session
  starts. `checking-qa-agent` warns when they're missing. Adding them is the
  user's call: don't edit their shell profile yourself.
- To stop a daemon, use `agent-device daemon stop --state-dir <dir>` (it checks the
  process is really that daemon), and only for your own signing dir. If the user
  wants the shared one restarted, warn that it ends other sessions' runs and run
  `agent-device daemon stop --state-dir ~/.agent-device` only after their yes.

Simulators, emulators and Android devices need no signing vars: use the default
daemon there.

## Reference loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [Physical iOS device setup](./physical-device-setup.md) | First `open`/`snapshot` on a physical iPhone/iPad this session, or any signing/provisioning/Developer Mode error | Developer Mode, `DevToolsSecurity`, Xcode account + local certificate, one-time device registration with the Apple team, required env vars |
