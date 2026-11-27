#!/usr/bin/env python3
"""Sets the QA_Agent context status line (statusline.py) in the Claude Code user settings.

Usage: register_statusline.py [--check | --restore]

- no option: points `statusLine` in ~/.claude/settings.json (or
  $CLAUDE_CONFIG_DIR) at statusline.py. A different status line already there
  is saved first to statusline.previous.json next to settings.json, so
  --restore can bring it back. Safe to run any number of times.
- --check: exits 0 if the QA_Agent status line is set, 1 if not, and prints
  which.
- --restore: puts the saved status line back (or removes ours if nothing was
  saved).

Run it only when environments/handoff.json has "statusLine": "qa-agent"; the
user chose that in configure-project or migration 016.
"""
import json
import os
import shlex
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("statusline.py")
COMMAND = f"python3 -I {shlex.quote(str(SCRIPT))}"


def config_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(base) if base else Path.home() / ".claude"


def ours(entry):
    return isinstance(entry, dict) and "statusline.py" in str(entry.get("command", "")) \
        and "session-handoff" in str(entry.get("command", ""))


def write(path, data):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def main():
    path = config_dir() / "settings.json"
    backup = config_dir() / "statusline.previous.json"
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
    except ValueError:
        print(f"skipped: status line ({path} is not valid JSON; fix it, then run this again)")
        return 1
    current = data.get("statusLine")
    if "--check" in sys.argv:
        if ours(current) and current.get("command") == COMMAND:
            print("ok:      QA_Agent context status line is set")
            return 0
        print("outdated: QA_Agent status line points elsewhere" if ours(current)
              else "missing: QA_Agent context status line")
        return 1
    if "--restore" in sys.argv:
        if not ours(current):
            print("ok:      the status line isn't QA_Agent's; nothing to restore")
            return 0
        if backup.exists():
            data["statusLine"] = json.loads(backup.read_text())
            backup.unlink()
            print(f"restored: previous status line in {path}")
        else:
            data.pop("statusLine", None)
            print(f"removed: QA_Agent status line from {path}")
        write(path, data)
        return 0
    if ours(current) and current.get("command") == COMMAND:
        print("ok:      QA_Agent context status line is set")
        return 0
    if current and not ours(current):
        backup.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n")
        print(f"saved:   previous status line to {backup}")
    data["statusLine"] = {"type": "command", "command": COMMAND}
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, data)
    print(f"linked:  QA_Agent context status line set in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
