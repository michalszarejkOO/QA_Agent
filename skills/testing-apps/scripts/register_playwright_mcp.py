#!/usr/bin/env python3
"""Makes the user-scope Playwright MCP servers start through playwright-mcp.sh.

Usage: register_playwright_mcp.py [--check]

For each of `playwright` and `playwright-video` in the user-scope MCP config:
- already started through the wrapper → left alone;
- started some other way (e.g. `npx @playwright/mcp@latest --isolated`) → re-added
  through the wrapper, keeping its extra arguments (minus --output-dir and
  --output-max-size, which the wrapper sets) and its env vars;
- `playwright` missing → added through the wrapper. `playwright-video` is only
  touched if it exists.

--check only reports what would change and exits 1 if anything would.
Uses the `claude mcp` CLI for every change; prints the command that undoes it.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

NAMES = ("playwright", "playwright-video")
WRAPPER_OWNED = {"--output-dir", "--output-max-size"}


def claude_json():
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(config_dir) / ".claude.json" if config_dir else Path.home() / ".claude.json"


def wrapper_path():
    config_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    return config_dir / "skills" / "testing-apps" / "scripts" / "playwright-mcp.sh"


def extra_args(entry):
    """Arguments after the @playwright/mcp package, without the wrapper-owned ones."""
    args = list(entry.get("args", []))
    for i, a in enumerate(args):
        if "@playwright/mcp" in a:
            args = args[i + 1:]
            break
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        flag = a.split("=", 1)[0]
        if flag in WRAPPER_OWNED:
            skip = "=" not in a
            continue
        out.append(a)
    return out


def main():
    check = "--check" in sys.argv
    path = claude_json()
    servers = json.loads(path.read_text()).get("mcpServers", {}) if path.exists() else {}
    wrapper = str(wrapper_path())
    changed = False
    for name in NAMES:
        entry = servers.get(name)
        if entry is None and name != "playwright":
            continue
        if entry is not None and entry.get("command") == wrapper:
            print(f"ok:      {name} already starts through playwright-mcp.sh")
            continue
        changed = True
        args = extra_args(entry) if entry else []
        env = (entry or {}).get("env", {})
        add = ["claude", "mcp", "add", "--scope", "user", name]
        for k, v in env.items():
            add += ["-e", f"{k}={v}"]
        add += ["--", wrapper, *args]
        if entry is None:
            print(f"{'would add' if check else 'adding'}:  {name} through playwright-mcp.sh")
            undo = f"claude mcp remove {name} -s user"
        else:
            old = " ".join([entry.get("command", ""), *entry.get("args", [])])
            print(f"{'would switch' if check else 'switching'}: {name} from `{old}` to playwright-mcp.sh {' '.join(args)}")
            undo = f"claude mcp remove {name} -s user && claude mcp add --scope user {name} -- {old}"
        if check:
            continue
        if entry is not None:
            subprocess.run(["claude", "mcp", "remove", name, "-s", "user"], check=True, capture_output=True)
        subprocess.run(add, check=True, capture_output=True)
        print(f"         undo with: {undo}")
    if changed and not check:
        print("Restart Claude Code for the new Playwright server to start.")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
