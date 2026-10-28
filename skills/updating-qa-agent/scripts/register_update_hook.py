#!/usr/bin/env python3
"""Registers the QA_Agent update check as a Claude Code SessionStart hook.

Usage: register_update_hook.py [--check]

Adds to the user settings (~/.claude/settings.json, or $CLAUDE_CONFIG_DIR) one
SessionStart hook, matcher "startup", running check_updates.py --hook. Because it
sits in the user settings, it runs whatever folder Claude is opened in. An
existing entry for check_updates.py is updated in place (e.g. the repo moved);
every other hook and setting is left as it is. Safe to run any number of times.

--check only reports and exits 1 if the hook is missing or points elsewhere.
"""
import json
import os
import shlex
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("check_updates.py")
COMMAND = f"python3 -I {shlex.quote(str(SCRIPT))} --hook"


def settings_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "settings.json"


def ours(hook):
    return isinstance(hook, dict) and "check_updates.py" in str(hook.get("command", ""))


def main():
    path = settings_path()
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
    except ValueError:
        print(f"skipped: update-check hook ({path} is not valid JSON; fix it, then run setup.sh again)")
        return 1
    groups = data.setdefault("hooks", {}).setdefault("SessionStart", [])
    found = [(g, h) for g in groups if isinstance(g, dict) for h in g.get("hooks", []) if ours(h)]
    if found and all(h.get("command") == COMMAND for _, h in found):
        print("ok:      QA_Agent update check runs when Claude starts (SessionStart hook)")
        return 0
    if "--check" in sys.argv:
        print("missing: QA_Agent update-check hook" if not found else "outdated: QA_Agent update-check hook path")
        return 1
    if found:
        for _, h in found:
            h["command"] = COMMAND
        action = "updated"
    else:
        groups.append({"matcher": "startup",
                       "hooks": [{"type": "command", "command": COMMAND, "timeout": 15}]})
        action = "added"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"linked:  QA_Agent update check {action} as a SessionStart hook in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
