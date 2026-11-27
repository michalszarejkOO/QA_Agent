#!/usr/bin/env python3
"""Claude Code status line that shows how large the conversation's context is.

Usage (set by register_statusline.py): python3 -I statusline.py   (JSON on stdin)

Prints: folder | git branch | model and window size | ctx: percent and tokens | cost.
The ctx part changes colour with the context size, in step with the
session-handoff hook (environments/handoff.json, thresholdTokens):

- green  below 100k: carry on;
- purple from 100k up to the threshold: the conversation is getting long;
- yellow from the threshold (default 250k): the hook saves or offers the
  handoff, time for /clear and 'kontynuuj ABC-123';
- red with "/clear!" from the threshold + 20k: auto-compact is close.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

GREY, RESET = "\033[90m", "\033[0m"


def env_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "environments"


def threshold():
    try:
        value = json.loads((env_dir() / "handoff.json").read_text()).get("thresholdTokens")
        return value if isinstance(value, int) and value > 0 else 250000
    except (OSError, ValueError, AttributeError):
        return 250000


def paint(code, text):
    return f"\033[{code}m{text}{RESET}"


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        data = {}
    folder = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
    home = str(Path.home())
    shown = "~" + folder[len(home):] if folder.startswith(home) else folder
    try:
        branch = subprocess.run(["git", "--no-optional-locks", "-C", folder, "branch", "--show-current"],
                                capture_output=True, text=True, timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        branch = ""
    model = (data.get("model") or {}).get("display_name") or (data.get("model") or {}).get("id") or "n/a"
    window = data.get("context_window") or {}
    size = window.get("context_window_size")
    if size == 1000000:
        model += " 1M"
    elif size:
        model += f" {size // 1000}k"
    pct = window.get("used_percentage")
    ctx, colour = "ctx:n/a", "35"
    if pct is not None:
        ctx = f"ctx:{round(pct)}%"
        if size:
            tokens = int(pct * size / 100)
            warn = threshold()
            ctx += f" {tokens // 1000}k"
            if tokens >= warn + 20000:
                colour, ctx = "1;31", ctx + " /clear!"
            elif tokens >= warn:
                colour = "33"
            elif tokens >= 100000:
                colour = "35"
            else:
                colour = "32"
    cost = (data.get("cost") or {}).get("total_cost_usd")
    cost = f"${cost:.4f}" if isinstance(cost, (int, float)) else "$n/a"
    sep = f" {GREY}|{RESET} "
    print(sep.join([paint("36", shown), paint("33", branch or "no-git"), paint("34", model),
                    paint(colour, ctx), paint("32", cost)]), end="")


if __name__ == "__main__":
    main()
