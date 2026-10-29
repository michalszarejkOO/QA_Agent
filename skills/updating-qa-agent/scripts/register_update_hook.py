#!/usr/bin/env python3
"""Registers the QA_Agent update check as a Claude Code SessionStart hook.

Usage: register_update_hook.py [--check]

Adds to the user settings (~/.claude/settings.json, or $CLAUDE_CONFIG_DIR) one
SessionStart hook, matcher "startup|resume|clear" (a new session, --continue /
--resume, and /clear, so someone who keeps one terminal and clears it still gets
checked), running check_updates.py --hook. The check-day rule in that script
keeps it to once a day. Because it sits in the user settings, it runs whatever
folder Claude is opened in. An existing entry for check_updates.py is updated in
place (the repo moved, or the old "startup"-only matcher); every other hook and
setting is left as it is. Safe to run any number of times.

--check only reports and exits 1 if the hook is missing or points elsewhere.
"""
import json
import os
import shlex
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("check_updates.py")
COMMAND = f"python3 -I {shlex.quote(str(SCRIPT))} --hook"
MATCHER = "startup|resume|clear"


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
    if found and all(h.get("command") == COMMAND and g.get("matcher") == MATCHER for g, h in found):
        print("ok:      QA_Agent update check runs when Claude starts (SessionStart hook)")
        return 0
    if "--check" in sys.argv:
        print("missing: QA_Agent update-check hook" if not found else "outdated: QA_Agent update-check hook")
        return 1
    if found:
        for g, h in found:
            h["command"] = COMMAND
            if g.get("matcher") == MATCHER:
                continue
            if len(g.get("hooks", [])) == 1:
                g["matcher"] = MATCHER
            else:  # shares a group with someone else's hooks: move it out, leave theirs as they were
                g["hooks"].remove(h)
                groups.append({"matcher": MATCHER, "hooks": [h]})
        action = "updated"
    else:
        groups.append({"matcher": MATCHER,
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
