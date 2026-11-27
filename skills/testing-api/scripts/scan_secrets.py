#!/usr/bin/env python3
"""Looks for live secrets in an exported collection before it leaves the machine.

Usage: python3 -I scan_secrets.py <zip or folder> [<zip or folder> ...]

Reports each finding as `<file>:<line>: <kind> (<key>)` and never prints the
value itself. Exit 0: nothing found. Exit 1: findings (don't publish to a place
others can read without the user's yes). Exit 2: a path couldn't be read.

What counts as a secret:
- a JWT, a literal `Bearer <token>`, a private key block, an AWS access key id;
- a value under a secret-like name (password, secret, token, apiKey, clientSecret,
  authorization, cookie, ...), in Postman's {"key": ..., "value": ...} entries,
  in `name: ...` / `value: ...` pairs (Bruno environments), or in `key: value` /
  `KEY=value` lines (.env, YAML).
Placeholders are not secrets: empty values, {{variables}}, <...>, REPLACE_ME,
${VAR}, null.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

SECRET_NAME = re.compile(
    r"(password|passwd|pwd|secret|token|apikey|api[_-]key|accesskey|access[_-]key|"
    r"privatekey|private[_-]key|authorization|cookie|session[_-]?id)$",
    re.IGNORECASE,
)
PATTERNS = [
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("bearer token", re.compile(r"Bearer\s+(?!\{\{)[A-Za-z0-9._~+/=-]{20,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]
KEY_VALUE_LINE = re.compile(r"""^\s*-?\s*["']?([A-Za-z0-9_.\-]+)["']?\s*[:=]\s*(.*?)\s*,?\s*$""")
TEXT_SUFFIXES = {".json", ".yml", ".yaml", ".bru", ".env", ".txt", ".md", ".js", ".ts", ""}


def is_placeholder(value):
    v = str(value).strip().strip("\"'")
    v = re.sub(r"^[A-Za-z][A-Za-z0-9_-]*\s+(?=\{\{)", "", v)  # "apikey {{key}}", "Bearer {{token}}"
    return (
        not v
        or v.lower() in {"null", "none", "~", "replace_me", "changeme", "true", "false"}
        or bool(re.fullmatch(r"\{\{.*\}\}|<.*>|\$\{.*\}|\*+", v))
    )


def secret_name(name):
    return bool(SECRET_NAME.search(re.sub(r"[^A-Za-z0-9_-]", "", str(name))))


def scan_json(obj, findings, label, where=""):
    """Postman-style {"key": name, "value": v} entries, and plain {name: v} pairs.
    `where` is the nearest enclosing "name" (the request or folder), for the report."""
    if isinstance(obj, dict):
        if isinstance(obj.get("name"), str) and ("request" in obj or "item" in obj):
            where = obj["name"]
        suffix = f" in \"{where}\"" if where else ""
        if "key" in obj and "value" in obj and isinstance(obj["value"], (str, int)):
            if secret_name(obj["key"]) and not is_placeholder(obj["value"]):
                findings.append((label, None, "secret value", f"{obj['key']}{suffix}"))
        for k, v in obj.items():
            if isinstance(v, str) and k not in ("key", "value") and secret_name(k) and not is_placeholder(v):
                findings.append((label, None, "secret value", f"{k}{suffix}"))
            scan_json(v, findings, label, where)
    elif isinstance(obj, list):
        for item in obj:
            scan_json(item, findings, label, where)


def scan_text(text, label, findings):
    lines = text.splitlines()
    is_json = label.endswith(".json")
    pending_name = None
    for n, line in enumerate(lines, 1):
        for kind, pattern in PATTERNS:
            if pattern.search(line):
                findings.append((label, n, kind, ""))
        if is_json:
            continue  # JSON is checked by its structure below
        m = KEY_VALUE_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if key == "name":
            pending_name = value.strip("\"'")
            continue
        if key == "value" and pending_name:
            if secret_name(pending_name) and not is_placeholder(value):
                findings.append((label, n, "secret value", pending_name))
            pending_name = None
            continue
        pending_name = None
        if key not in ("key", "value") and secret_name(key) and not is_placeholder(value) \
                and not value.startswith(("{", "[")):
            findings.append((label, n, "secret value", key))
    if is_json:
        try:
            scan_json(json.loads(text), findings, label)
        except ValueError:
            pass


def scan_file(name, data, findings):
    if Path(name).suffix.lower() not in TEXT_SUFFIXES and not Path(name).name.startswith(".env"):
        return
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return
    scan_text(text, name, findings)


def scan(path, findings):
    p = Path(path)
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file() and ".git" not in f.parts:
                scan_file(str(f.relative_to(p)), f.read_bytes(), findings)
    elif zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                if not info.is_dir():
                    scan_file(f"{p.name}:{info.filename}", z.read(info), findings)
    elif p.is_file():
        scan_file(p.name, p.read_bytes(), findings)
    else:
        raise FileNotFoundError(path)


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    findings = []
    for path in sys.argv[1:]:
        try:
            scan(path, findings)
        except (OSError, zipfile.BadZipFile) as e:
            print(f"cannot read {path}: {e}", file=sys.stderr)
            return 2
    seen = set()
    for label, line, kind, key in findings:
        entry = f"{label}:{line}" if line else label
        msg = f"{entry}: {kind}" + (f" ({key})" if key else "")
        if msg not in seen:
            seen.add(msg)
            print(msg)
    if seen:
        print(f"{len(seen)} possible secret(s); values not shown", file=sys.stderr)
        return 1
    print("no secrets found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
