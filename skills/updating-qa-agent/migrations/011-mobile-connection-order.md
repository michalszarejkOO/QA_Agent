# 011: physical mobile devices are reached over Wi-Fi or cable, in the user's order

## What changed

`testing-apps` used to take any physical device that was ready, cable and Wi-Fi
alike. Now `mobile.connection` in `~/.claude/environments/qa-agent-preferences.json`
sets the order: e.g. `["wifi", "usb"]` uses Wi-Fi first and the cable only when no
device is ready over Wi-Fi; `["usb", "wifi"]` the other way round; one entry means
only that one. `scripts/list_physical_devices.py --connect` now also wakes the
Wi-Fi tunnel of paired iPhones/iPads and prints a `pick` line per platform that
follows the order. Docs: `skills/configure-project/references/preferences.md`,
"Mobile devices: Wi-Fi or cable".

## Is it needed

Needed if any product config in `~/.claude/environments/` (or under
`$CLAUDE_CONFIG_DIR`) has a surface with `platform` (a mobile app) and
`python3 -I ~/.claude/skills/configure-project/scripts/preferences.py connection`
prints "not set". Not needed for a setup that tests only web apps or APIs.

## Steps

1. **Ask the order (asks; default: Wi-Fi first, cable as fallback).** One
   question with four options: Wi-Fi first with the cable as fallback
   (`wifi,usb`), cable first with Wi-Fi as fallback (`usb,wifi`), Wi-Fi only
   (`wifi`), cable only (`usb`). Say that it applies to physical devices, not to
   simulators or emulators.
2. **Save it (runs by itself).**
   `python3 -I ~/.claude/skills/configure-project/scripts/preferences.py connection <order>`.

## Verify

- `preferences.py connection` prints the chosen order.
- `python3 -I <QA_Agent>/environments.example/validate_environments.py` passes and
  prints `qa-agent-preferences.json: ok`.
