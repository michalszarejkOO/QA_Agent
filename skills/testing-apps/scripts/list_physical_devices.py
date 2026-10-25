#!/usr/bin/env python3
"""Lists physical iOS/Android devices with how each is connected (USB cable or
Wi-Fi) and whether it is reachable right now.

Usage: python3 -I list_physical_devices.py [--platform ios|android] [--connect]

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
"""
import argparse
import json
import os
import re
import subprocess
import tempfile


def run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, ""


def ios_devices():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        code, _ = run(["xcrun", "devicectl", "list", "devices", "--json-output", path, "--quiet"])
        if code != 0:
            return [("ios", "-", "-", "?", "devicectl unavailable (Xcode 15+ needed)")]
        with open(path) as f:
            devices = json.load(f).get("result", {}).get("devices", [])
    finally:
        os.unlink(path)
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--platform", choices=["ios", "android"])
    ap.add_argument("--connect", action="store_true",
                    help="adb connect every Android device advertised over mDNS but not attached")
    args = ap.parse_args()
    rows = []
    if args.platform in (None, "ios"):
        rows += ios_devices()
    if args.platform in (None, "android"):
        rows += android_devices(args.connect)
    header = ("platform", "name", "id", "transport", "state")
    widths = [max(len(str(r[i])) for r in rows + [header]) for i in range(4)]
    for r in [header] + rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r[:4])) + "  " + r[4])
    if not rows:
        print("No physical devices found.")


if __name__ == "__main__":
    main()
