#!/usr/bin/env python3
"""Registers the session-handoff context check as a Claude Code UserPromptSubmit hook.

Usage: register_handoff_hook.py [--check]

Adds to the user settings (~/.claude/settings.json, or $CLAUDE_CONFIG_DIR) one
UserPromptSubmit hook running context_hook.py --hook, so it works whatever
folder Claude is opened in. What it does is set in environments/handoff.json
(mode ask / auto / never); with "never" it stays registered and prints
nothing. An existing entry for context_hook.py is updated in place (the repo
moved); every other hook and setting is left as it is. Safe to run any number
of times.

--check only reports and exits 1 if the hook is missing or points elsewhere.
"""
import json
import os
import shlex
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("context_hook.py")
COMMAND = f"python3 -I {shlex.quote(str(SCRIPT))} --hook"
EVENT = "UserPromptSubmit"


def settings_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "settings.json"


def ours(hook):
    return isinstance(hook, dict) and "context_hook.py" in str(hook.get("command", ""))


def main():
    path = settings_path()
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
    except ValueError:
        print(f"skipped: session-handoff hook ({path} is not valid JSON; fix it, then run setup.sh again)")
        return 1
    groups = data.setdefault("hooks", {}).setdefault(EVENT, [])
    found = [h for g in groups if isinstance(g, dict) for h in g.get("hooks", []) if ours(h)]
    if found and all(h.get("command") == COMMAND for h in found):
        print("ok:      session-handoff context check runs on every prompt (UserPromptSubmit hook)")
        return 0
    if "--check" in sys.argv:
        print("missing: session-handoff hook" if not found else "outdated: session-handoff hook")
        return 1
    if found:
        for h in found:
            h["command"] = COMMAND
        action = "updated"
    else:
        groups.append({"hooks": [{"type": "command", "command": COMMAND, "timeout": 10}]})
        action = "added"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"linked:  session-handoff context check {action} as a UserPromptSubmit hook in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
