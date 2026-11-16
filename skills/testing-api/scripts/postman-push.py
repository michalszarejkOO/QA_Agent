#!/usr/bin/env python3
"""Replaces one collection or one environment in the user's Postman workspace
with a published file, so the Postman app on this machine shows the new version
without an import (the same result as Import > Replace, names unchanged).

Used by the postman-sync agent in push mode (agents/postman-sync.md), after a
publish, when the updateLocalApp preference is auto or the user said yes.
Docs: skills/testing-api/references/publishing.md, step 8.

Usage:
  postman-push.py collection <uid> <file.postman_collection.json> --expect-updated-at <iso>
  postman-push.py environment <uid> <file.postman_environment.json> --expect-updated-at <iso>

<uid> is the cloud uid the sync step matched by name. --expect-updated-at is the
updatedAt that step saw: if the cloud copy changed since then, someone edited it
in the app after the check, so nothing is written and the exit code is 3.

The Postman API key is read the same way as for the MCP server
(~/.claude/environments/postman.json, field apiKeyRef, through op.sh) and never
printed. Values are never printed either: output names only.
Exit codes: 0 replaced, 1 error, 2 usage, 3 changed in Postman since the check.
Stdlib only, works on macOS system Python 3.9.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
CONFIG = CLAUDE_DIR / "environments" / "postman.json"
OP_WRAPPER = CLAUDE_DIR / "skills" / "testing-api" / "scripts" / "op.sh"
API = "https://api.getpostman.com"
EXIT_CHANGED = 3


def fail(message):
    print(f"postman-push: {message}", file=sys.stderr)
    sys.exit(1)


def read_api_key():
    try:
        ref = json.loads(CONFIG.read_text()).get("apiKeyRef", "")
    except (OSError, ValueError, AttributeError):
        ref = ""
    if not isinstance(ref, str) or not ref.startswith("op://"):
        fail(f"{CONFIG} has no apiKeyRef of the form op://<vault>/<item>/<field>; run 'update QA_Agent'")
    result = subprocess.run([str(OP_WRAPPER), "read", ref], capture_output=True, text=True)
    if result.returncode != 0:
        fail("op read failed for the apiKeyRef; unlock 1Password and approve the CLI request")
    match = re.search(r"PMAK-[A-Za-z0-9-]+", result.stdout)
    if not match:
        fail("the 1Password field holds no Postman API key (PMAK-...)")
    return match.group(0)


def call(method, path, api_key, body=None):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(f"{API}{path}", data=data, method=method)
    request.add_header("X-Api-Key", api_key)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        fail(f"{method} {path} returned {error.code}: {detail}")
    except urllib.error.URLError as error:
        fail(f"{method} {path} failed: {error.reason}")


def stop_if_changed(kind, current_updated_at, expected_updated_at):
    if current_updated_at != expected_updated_at:
        print(f"{kind} changed in Postman since the check: updatedAt {current_updated_at}, "
              f"expected {expected_updated_at}. Nothing written.")
        sys.exit(EXIT_CHANGED)


def push_collection(uid, file_path, expected_updated_at, api_key):
    collection = json.loads(Path(file_path).read_text())
    current = call("GET", f"/collections/{uid}", api_key)["collection"]["info"]
    stop_if_changed("collection", current.get("updatedAt"), expected_updated_at)
    cloud_id = uid.split("-", 1)[1]
    collection["info"]["_postman_id"] = cloud_id
    collection["info"]["name"] = current["name"]
    call("PUT", f"/collections/{uid}", api_key, {"collection": collection})
    print(f"collection replaced: {current['name']} ({uid}), {count_requests(collection.get('item', []))} requests")


def count_requests(items):
    total = 0
    for item in items:
        if "item" in item:
            total += count_requests(item["item"])
        else:
            total += 1
    return total


def push_environment(uid, file_path, expected_updated_at, api_key):
    environment = json.loads(Path(file_path).read_text())
    current = call("GET", f"/environments/{uid}", api_key)["environment"]
    stop_if_changed("environment", current.get("updatedAt"), expected_updated_at)
    values = []
    for variable in environment.get("values", []):
        values.append({
            "key": variable["key"],
            "value": variable.get("value", ""),
            "type": variable.get("type", "default"),
            "enabled": variable.get("enabled", True),
        })
    body = {"environment": {"name": current["name"], "values": values}}
    call("PUT", f"/environments/{uid}", api_key, body)
    print(f"environment replaced: {current['name']} ({uid}), {len(values)} variables")


def main():
    if len(sys.argv) != 6 or sys.argv[1] not in ("collection", "environment") or sys.argv[4] != "--expect-updated-at":
        print(__doc__)
        return 2
    kind, uid, file_path, expected_updated_at = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[5]
    if not Path(file_path).is_file():
        fail(f"no file {file_path}")
    api_key = read_api_key()
    if kind == "collection":
        push_collection(uid, file_path, expected_updated_at, api_key)
    else:
        push_environment(uid, file_path, expected_updated_at, api_key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
