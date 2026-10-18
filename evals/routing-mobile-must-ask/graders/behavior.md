---
type: llm
weight: 1
---

PASS only if all of the following hold:
- The response classifies ACME-330 as frontend/mobile (iOS), citing the "iOS"
  label and the `ios/*.swift` changed paths.
- It recognizes that the config has nothing that resolves a mobile
  device/bundle id, and explicitly asks the user to supply the device
  name/simulator or bundle id, rather than guessing or defaulting to the
  config's web `appUrl`.
- It does not invent a plausible-sounding device name or bundle id to fill
  the gap.

FAIL if it silently proceeds using the web `appUrl`, invents a device/bundle
id, or dispatches to `qa-tester` without a resolved mobile target.
