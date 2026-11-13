#!/usr/bin/env python3
"""Lists physical iOS/Android devices with how each is connected (USB cable or
Wi-Fi) and whether it is reachable right now.

Usage: python3 -I list_physical_devices.py [--platform ios|android] [--connect]
                                          [--prefer wifi,usb | usb,wifi | wifi | usb]

Needed because `agent-device devices` alone is misleading for wireless work:
  - iOS: it shows every *paired* device as booted=true, even one that is off the
    network or asleep. Only `xcrun devicectl` knows the real state
    (transportType wired/localNetwork, tunnelState connected/disconnected).
  - Android: a Wi-Fi device can drop out of `adb devices` while it is still
    advertised over mDNS (`adb mdns services`). --connect runs `adb connect` for
    each such device so it shows up again. Its port changes on every reconnect.

Columns: platform, name, id (UDID or adb serial to pass as --udid/--serial),
transport (usb | wifi | ?), state (ready | not-reachable | unauthorized | ...).
Only rows with state=ready can be tested; the rest say why not.

--connect also tries to bring Wi-Fi devices back: `adb connect` for Android
devices advertised over mDNS, and `xcrun devicectl device info details` for a
paired iOS device without a live tunnel (that call wakes the tunnel).

Connection order: --prefer, else `mobile.connection` in
~/.claude/environments/qa-agent-preferences.json (e.g. ["wifi", "usb"]: Wi-Fi
first, cable only when no device is ready over Wi-Fi). With an order, a last
line per platform says which device to use ("pick: ...") or why none fits.
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
PREFS = CLAUDE_DIR / "environments" / "qa-agent-preferences.json"
TRANSPORTS = ("wifi", "usb")


def run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, ""


def ios_raw():
    """devicectl's device list, or None when devicectl isn't available."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        code, _ = run(["xcrun", "devicectl", "list", "devices", "--json-output", path, "--quiet"])
        if code != 0:
            return None
        with open(path) as f:
            return json.load(f).get("result", {}).get("devices", [])
    finally:
        os.unlink(path)


def ios_wake(devices):
    """Bring up the tunnel of each paired physical iOS device that has none."""
    for d in devices:
        conn = d.get("connectionProperties", {})
        hw = d.get("hardwareProperties", {})
        if (hw.get("reality") == "physical" and hw.get("platform") == "iOS"
                and conn.get("pairingState") == "paired" and conn.get("tunnelState") != "connected"
                and d.get("identifier")):
            run(["xcrun", "devicectl", "device", "info", "details", "--device", d["identifier"], "--quiet"],
                timeout=45)


def ios_devices(connect=False):
    devices = ios_raw()
    if devices is not None and connect:
        ios_wake(devices)
        devices = ios_raw()
    if devices is None:
        return [("ios", "-", "-", "?", "devicectl unavailable (Xcode 15+ needed)")]
    rows = []
    for d in devices:
        conn = d.get("connectionProperties", {})
        hw = d.get("hardwareProperties", {})
        if hw.get("reality") != "physical" or hw.get("platform") != "iOS":
            continue
        transport = {"wired": "usb", "localNetwork": "wifi"}.get(conn.get("transportType"), "?")
        # devicectl keeps the last-seen transport for an offline device; only trust it when connected.
        if conn.get("tunnelState") != "connected":
            transport = "-"
        if conn.get("pairingState") != "paired":
            state = "not-paired (trust this Mac on the device)"
        elif conn.get("tunnelState") == "connected":
            state = "ready"
        else:
            state = "not-reachable (wake + unlock it, same Wi-Fi as the Mac, or plug in)"
        rows.append(("ios", d.get("deviceProperties", {}).get("name", "?"),
                     hw.get("udid", "?"), transport, state))
    return rows


def mdns_services():
    """Wireless-debugging devices advertised on the network: {host:port: service name}."""
    code, out = run(["adb", "mdns", "services"])
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1].startswith("_adb-tls-connect"):
            found[parts[2]] = parts[0]
    return found


def android_devices(connect):
    code, out = run(["adb", "devices", "-l"])
    if code != 0:
        return [("android", "-", "-", "?", "adb not found (install platform-tools)")]
    if connect:
        attached = out
        for addr in mdns_services():
            if addr not in attached:
                run(["adb", "connect", addr], timeout=15)
        _, out = run(["adb", "devices", "-l"])
    rows, seen = [], set()
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, status = parts[0], parts[1]
        if serial.startswith("emulator-"):
            continue
        model = next((p.split(":", 1)[1] for p in parts if p.startswith("model:")), "?")
        wifi = re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", serial) or "._adb-tls-connect." in serial
        state = {"device": "ready",
                 "unauthorized": "unauthorized (accept the debugging prompt on the device)",
                 "offline": "offline (toggle Wireless/USB debugging, then re-run with --connect)"
                 }.get(status, status)
        rows.append(("android", model.replace("_", " "), serial, "wifi" if wifi else "usb", state))
        seen.add(serial)
    for addr, name in mdns_services().items():
        if addr not in seen and not any(name in s for s in seen):
            rows.append(("android", name, addr, "wifi",
                         "advertised, not connected (re-run with --connect, or adb pair first)"))
    return rows


def preferred_order(arg):
    """Connection order from --prefer, else from the preferences file; [] = no preference."""
    if arg:
        order = [x.strip() for x in arg.split(",") if x.strip()]
    else:
        try:
            order = (json.loads(PREFS.read_text()).get("mobile") or {}).get("connection") or []
        except (OSError, ValueError, AttributeError):
            order = []
    if not order or any(x not in TRANSPORTS for x in order) or len(set(order)) != len(order):
        if arg:
            raise SystemExit(f"--prefer must be wifi,usb | usb,wifi | wifi | usb, got {arg!r}")
        return []
    return order


def pick(rows, platform, order):
    """One line saying which device to use on this platform, following the order."""
    ready = [r for r in rows if r[0] == platform and r[4] == "ready"]
    for i, transport in enumerate(order):
        match = [r for r in ready if r[3] == transport]
        if match:
            r = match[0]
            note = "" if i == 0 else f" (fallback: nothing ready over {', '.join(order[:i])})"
            more = f"; also ready: {', '.join(m[1] + ' ' + m[2] for m in match[1:])}" if len(match) > 1 else ""
            return f"pick {platform}: {r[1]}  {r[2]}  over {transport}{note}{more}"
    others = sorted({r[3] for r in ready} - set(order))
    tail = f"; ready only over {', '.join(others)}, which the order doesn't allow" if others else ""
    nxt = " or ".join("plug in the cable" if t == "usb" else "wake/unlock it on the same Wi-Fi, then --connect"
                      for t in order)
    return f"pick {platform}: none ready over {' then '.join(order)}{tail} ({nxt})"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--platform", choices=["ios", "android"])
    ap.add_argument("--connect", action="store_true",
                    help="bring Wi-Fi devices back: adb connect mDNS-advertised Android devices, "
                         "wake the tunnel of paired iOS devices")
    ap.add_argument("--prefer", help="connection order, e.g. wifi,usb (default: mobile.connection in "
                                     "qa-agent-preferences.json)")
    args = ap.parse_args()
    order = preferred_order(args.prefer)
    rows = []
    if args.platform in (None, "ios"):
        rows += ios_devices(args.connect)
    if args.platform in (None, "android"):
        rows += android_devices(args.connect)
    header = ("platform", "name", "id", "transport", "state")
    widths = [max(len(str(r[i])) for r in rows + [header]) for i in range(4)]
    for r in [header] + rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r[:4])) + "  " + r[4])
    if not rows:
        print("No physical devices found.")
    if order:
        print(f"connection order: {' then '.join(order)}")
        for platform in ("ios", "android"):
            if args.platform in (None, platform):
                print(pick(rows, platform, order))


if __name__ == "__main__":
    main()
