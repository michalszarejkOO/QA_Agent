#!/usr/bin/env python3
"""Reads and writes this machine's QA_Agent preferences: which actions run by
themselves, which ask first, and which never happen.

File: ~/.claude/environments/qa-agent-preferences.json (or under
$CLAUDE_CONFIG_DIR). Shape: environments.example/qa-agent-preferences.example.json.
Docs: skills/configure-project/references/preferences.md.

Usage:
  preferences.py get <action> [--product <name>]   prints ask | auto | never
  preferences.py set <action> <ask|auto|never> [--product <name>]
  preferences.py show                               every action, its value and where it comes from
  preferences.py permissions [--apply]              Claude Code allow rules for `claudePermissions`
  preferences.py actions                            the known actions and what each one does

`set` without --product changes the default for every product; with --product
it changes only that product. `permissions` without --apply only prints the
rules it would add to ~/.claude/settings.json and exits 1 if any are missing;
--apply adds them (never removes anything) and keeps a .bak of the old file.
Stdlib only, works on macOS system Python 3.9.
"""
import json
import os
import shutil
import sys
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
ENV_DIR = CLAUDE_DIR / "environments"
PREFS = ENV_DIR / "qa-agent-preferences.json"
SETTINGS = CLAUDE_DIR / "settings.json"

VALUES = ("ask", "auto", "never")

# action -> (default, what it does). Keep in step with references/preferences.md.
ACTIONS = {
    "confirmTicketEnvironment": ("ask", "testing-api ticket mode: use api.ticketEnvironment without asking (auto) or confirm it first (ask)"),
    "publishCollection": ("ask", "after an API run, upload the collection/environments to the configured target (1Password, Confluence)"),
    "postJiraComment": ("ask", "after a test run, post the prepared comment on the tested ticket"),
    "fileBugs": ("ask", "after a test run, create a Jira bug for each bug draft"),
    "attachEvidence": ("ask", "attach screenshots/videos to the posted comment or the filed bug"),
    "updateProjectSkill": ("ask", "add the run's proposed lines to the product's project skill"),
}

# Claude Code permission groups -> rules. Atlassian groups expand per connector
# in atlassian-connectors.json (Atlassian's own MCP server).
OP_WRAPPER = str(CLAUDE_DIR / "skills" / "testing-api" / "scripts" / "op.sh")
OP_READ_SUB = ["vault list", "account list", "item list", "item get", "read"]
OP_WRITE_SUB = ["item create", "item edit"]
OP_READ = [f"Bash({cmd} {sub}:*)" for cmd in ("op", OP_WRAPPER, "~/.claude/skills/testing-api/scripts/op.sh")
           for sub in OP_READ_SUB] + [f"Bash({OP_WRAPPER} --auth)"]
OP_WRITE = [f"Bash({cmd} {sub}:*)" for cmd in ("op", OP_WRAPPER, "~/.claude/skills/testing-api/scripts/op.sh")
            for sub in OP_WRITE_SUB]
OFFICIAL = {
    "jira-read": ["getAccessibleAtlassianResources", "getJiraIssue", "searchJiraIssuesUsingJql", "discover",
                  "executeRead", "atlassianUserInfo"],
    "jira-write": ["addOrEditJiraIssueComment", "createJiraIssue", "editJiraIssue", "executeWrite"],
    "confluence-read": ["getAccessibleAtlassianResources", "searchConfluence", "getConfluenceContent",
                        "discover", "executeRead"],
    "confluence-write": ["createConfluenceContent", "updateConfluenceContent", "executeWrite"],
}
GROUPS = ("1password-read", "1password-write", "jira-read", "jira-write", "confluence-read", "confluence-write")


def load(path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default
    except ValueError as e:
        sys.exit(f"{path}: invalid JSON ({e}); fix it by hand first")


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def resolve(prefs, action, product=None):
    """(value, source) for one action."""
    if product:
        v = ((prefs.get("products") or {}).get(product) or {}).get(action)
        if v in VALUES:
            return v, f"products.{product}"
    v = (prefs.get("actions") or {}).get(action)
    if v in VALUES:
        return v, "actions"
    return ACTIONS[action][0], "default"


def arg_after(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        sys.exit(f"{flag} needs a value")
    return None


def connectors():
    data = load(ENV_DIR / "atlassian-connectors.json", {})
    return (data.get("connectors") or {}) if isinstance(data, dict) else {}


def wanted_rules(prefs):
    rules = []
    for group in prefs.get("claudePermissions") or []:
        if group not in GROUPS:
            print(f"warning: unknown permission group {group!r} (known: {', '.join(GROUPS)})", file=sys.stderr)
            continue
        if group == "1password-read":
            rules += OP_READ
        elif group == "1password-write":
            rules += OP_WRITE
        else:
            for name, entry in connectors().items():
                server = (entry or {}).get("server", name)
                rules += [f"mcp__{server}__{t}" for t in OFFICIAL[group]]
    seen, out = set(), []
    for r in rules:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def cmd_permissions(prefs):
    rules = wanted_rules(prefs)
    settings = load(SETTINGS, {})
    allow = (settings.get("permissions") or {}).get("allow") or []
    missing = [r for r in rules if r not in allow]
    if not rules:
        print("claudePermissions is empty: nothing to allow.")
        return 0
    if not missing:
        print(f"ok: all {len(rules)} allow rules for {', '.join(prefs.get('claudePermissions'))} are in {SETTINGS}")
        return 0
    if "--apply" not in sys.argv:
        print(f"missing in {SETTINGS} (permissions.allow):")
        for r in missing:
            print(f"  {r}")
        print("add them with: preferences.py permissions --apply")
        return 1
    if SETTINGS.exists():
        shutil.copy2(SETTINGS, SETTINGS.with_suffix(".json.bak"))
    settings.setdefault("permissions", {}).setdefault("allow", []).extend(missing)
    save(SETTINGS, settings)
    print(f"added {len(missing)} allow rules to {SETTINGS} (backup: settings.json.bak):")
    for r in missing:
        print(f"  {r}")
    print("They apply to new Claude Code sessions; remove a line from permissions.allow to take one back.")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    prefs = load(PREFS, {})
    product = arg_after("--product")

    if cmd == "actions":
        for a, (d, what) in ACTIONS.items():
            print(f"{a:26} default {d:5}  {what}")
        return 0
    if cmd == "get":
        if len(sys.argv) < 3 or sys.argv[2] not in ACTIONS:
            sys.exit(f"usage: get <action>; actions: {', '.join(ACTIONS)}")
        print(resolve(prefs, sys.argv[2], product)[0])
        return 0
    if cmd == "set":
        if len(sys.argv) < 4 or sys.argv[2] not in ACTIONS or sys.argv[3] not in VALUES:
            sys.exit(f"usage: set <action> <{'|'.join(VALUES)}> [--product <name>]; actions: {', '.join(ACTIONS)}")
        action, value = sys.argv[2], sys.argv[3]
        before = resolve(prefs, action, product)[0]
        if product:
            prefs.setdefault("products", {}).setdefault(product, {})[action] = value
        else:
            prefs.setdefault("actions", {})[action] = value
        prefs.setdefault("notes", "QA_Agent preferences for this machine. ask: ask every time; auto: do it "
                         "without asking; never: don't do it and don't ask (the draft is still shown). "
                         "Docs: skills/configure-project/references/preferences.md.")
        save(PREFS, prefs)
        scope = f"for {product}" if product else "for every product"
        print(f"{action}: {before} -> {value} {scope} (saved in {PREFS})")
        print(f"undo: preferences.py set {action} {before}" + (f" --product {product}" if product else ""))
        return 0
    if cmd == "show":
        products = sorted((prefs.get("products") or {}).keys())
        print(f"{PREFS}{'' if PREFS.exists() else ' (not created yet: everything is at its default)'}")
        for a in ACTIONS:
            v, src = resolve(prefs, a)
            line = f"  {a:26} {v:5} ({src})"
            over = [f"{p}={prefs['products'][p][a]}" for p in products if a in (prefs["products"][p] or {})]
            print(line + (f"  overrides: {', '.join(over)}" if over else ""))
        res = prefs.get("results") or {}
        print(f"  results.saveReportFiles    {bool(res.get('saveReportFiles', False))}")
        print(f"  claudePermissions          {', '.join(prefs.get('claudePermissions') or []) or '(none)'}")
        return 0
    if cmd == "permissions":
        return cmd_permissions(prefs)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
