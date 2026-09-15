---
name: testing-apps
description: Drives a running app to execute test scenarios and capture evidence — Playwright for a web app, or the agent-device CLI (Callstack) for an iOS/Android mobile app — picking the adapter from whether the target is a URL or a device/bundle id. Used as qa-tester's own execution step (its steps 1-2 gather context and derive scenarios, this skill only replaces the browser/device-execution step, its steps 4-5 report and draft bugs). Also usable standalone for direct browser or mobile-device exploration/dogfooding when full ticket/PR/Figma context isn't needed.
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

## Procedure

1. Resolve the adapter from the target (table above).
2. Load that adapter's reference file and follow it exactly — it owns discovery,
   session start, the click/type/navigate loop, and evidence capture for its
   platform.
3. Capture evidence per the adapter's instructions: screenshots always; console/
   network output whenever a criterion concerns errors, loading states, or API
   behavior.
4. Hand the captured evidence back to whatever's judging pass/fail — `qa-tester`'s
   own steps 4-5 when invoked from there, or straight into your own response when
   this skill was triggered standalone.
