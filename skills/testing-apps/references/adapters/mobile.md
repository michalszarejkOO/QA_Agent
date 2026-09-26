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
3. `agent-device open <bundle-id> --device "<name>" --foreground` to start the session,
   then `agent-device snapshot -i` for the first interactive snapshot with `@eN` refs.
4. Pick the loop that matches the ask and follow it as documented — don't
   reimplement it from memory:
   - Open-ended exploratory/bug-hunt → `agent-device help dogfood`.
   - Executing a specific written script/test case → `agent-device help manual-qa`.
   Both guides cover navigation mapping, evidence capture per finding, and the
   report shape; `agent-device help workflow` has the full refs/selectors/waits
   reference if a command's exact shape is unclear.
5. Capture evidence as you go: `mkdir -p <out>/screenshots <out>/videos <out>/traces`,
   `agent-device screenshot <path>.png` (add `--overlay-refs` to show which element is
   which). Read every screenshot back before judging pass/fail — see "Shared
   discipline" in the parent skill (`../../SKILL.md`).
6. `agent-device close` when the session ends.

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
