#!/usr/bin/env python3
"""UserPromptSubmit hook: points out when the conversation's context grows large.

Usage: context_hook.py --hook   (reads the hook's JSON on stdin)
       context_hook.py --settings   (prints the settings in effect as JSON)

Reads the size of the main conversation's context from the last assistant
message's usage in the transcript (input + cache read + cache write tokens).
Once it reaches `thresholdTokens` from environments/handoff.json, it adds a
note to the turn, depending on `mode`:

- "ask": Claude offers, in one line, to save the work state with the
  session-handoff skill and continue in a fresh session after /clear.
- "auto": Claude saves the state by itself, then says so in one line.
- "never": nothing.

It speaks once at the threshold and again only after the context grows by
another `repeatTokens`; after a /compact or /clear brings it back under the
threshold it starts over. The per-session state is a small file in the system
temp folder. Any error makes it print nothing: it never blocks a prompt.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULTS = {"mode": "ask", "thresholdTokens": 250000, "repeatTokens": 40000}
MODES = ("ask", "auto", "never")
TAIL_BYTES = 4 * 1024 * 1024


def env_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "environments"


def settings():
    result = dict(DEFAULTS)
    try:
        data = json.loads((env_dir() / "handoff.json").read_text())
    except (OSError, ValueError):
        return result
    if data.get("mode") in MODES:
        result["mode"] = data["mode"]
    for key in ("thresholdTokens", "repeatTokens"):
        if isinstance(data.get(key), int) and data[key] > 0:
            result[key] = data[key]
    return result


def context_tokens(transcript):
    with open(transcript, "rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - TAIL_BYTES))
        lines = f.read().splitlines()
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        usage = (entry.get("message") or {}).get("usage")
        if not usage:
            continue
        total = sum(usage.get(k) or 0 for k in
                    ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if total:
            return total
    return 0


def state_file(session_id):
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "unknown"
    folder = Path(tempfile.gettempdir()) / "qa-agent-handoff"
    folder.mkdir(exist_ok=True)
    return folder / f"{safe}.json"


def message(mode, tokens):
    size = f"about {tokens // 1000}k tokens"
    if mode == "auto":
        return (f"[QA_Agent session-handoff] This conversation's context is {size}. If it is "
                "about a ticket or a feature with work worth carrying on, after handling the "
                "user's message save the work state with the session-handoff skill (it updates "
                "handoff.md in the ticket's folder) without asking, then tell the user in one "
                "line, in their language, where it is and that /clear followed by "
                "'kontynuuj <ticket key>' continues from it. If an agent or background task "
                "started here is still running, don't stop it and don't suggest /clear until "
                "it reports back (the skill says how). If it is work in progress "
                "without a ticket, ask first and propose a path, as the skill's 'Where' says. "
                "Otherwise ignore this note.")
    return (f"[QA_Agent session-handoff] This conversation's context is {size}, and every "
            "further message re-reads all of it. If it is about a ticket or a feature with work "
            "worth carrying on, after handling the user's message offer once, in one line in "
            "their language, to save the work state with the session-handoff skill and continue "
            "in a fresh session after /clear (without a ticket, propose a path, as the "
            "skill's 'Where' says; while an agent or background task started here is still "
            "running, say /clear has to wait for its result and never stop it). Don't save "
            "without their yes. Otherwise ignore this note.")


def hook():
    try:
        event = json.loads(sys.stdin.read() or "{}")
        conf = settings()
        if conf["mode"] == "never" or not event.get("transcript_path"):
            return 0
        tokens = context_tokens(event["transcript_path"])
        path = state_file(str(event.get("session_id", "")))
        try:
            last = json.loads(path.read_text()).get("notedAt", 0)
        except (OSError, ValueError):
            last = 0
        if tokens < conf["thresholdTokens"]:
            if last:
                path.unlink(missing_ok=True)
            return 0
        if last and tokens < last + conf["repeatTokens"]:
            return 0
        path.write_text(json.dumps({"notedAt": tokens}))
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": message(conf["mode"], tokens)}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    if "--settings" in sys.argv:
        print(json.dumps(settings()))
        sys.exit(0)
    sys.exit(hook())
