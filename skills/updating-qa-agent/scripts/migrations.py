#!/usr/bin/env python3
"""Tracks which QA_Agent migrations have been applied on this machine.

Usage:
  migrations.py status            list migrations, applied or pending
  migrations.py pending           print pending migration ids, one per line
  migrations.py mark <id> [...]   record migrations as applied
  migrations.py mark-all          record every existing migration as applied
  migrations.py fresh-install     first setup: record the "skip" migrations as
                                  applied and print the "ask" ones, which the
                                  setup then runs as a wizard
  migrations.py lint              check migration files: numbering and sections

Migrations are the files in ../migrations/NNN-<slug>.md. Each says in its
"## Fresh install" section whether a new machine needs it too: `ask` (the user
decides something, so the first setup runs it) or `skip` (it only fixes an older
install). State lives in
$CLAUDE_CONFIG_DIR/environments/qa-agent-migrations.json (default
~/.claude/environments/), next to the product configs it changes.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
NAME = re.compile(r"^(\d{3})-[a-z0-9-]+\.md$")
REQUIRED_SECTIONS = ("## What changed", "## Is it needed", "## Fresh install", "## Steps", "## Verify")
FRESH_INSTALL = re.compile(r"^## Fresh install\s*\n+\s*`(ask|skip)`", re.MULTILINE)
FRESH_INSTALL_SECTION = re.compile(r"^## Fresh install\s*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
# A `skip` is right in two cases only, and its line has to say which:
# configure-project already asks the same question (name the step), or a new
# machine is already in the new state, so nothing is asked at all.
MENTIONS_A_QUESTION = re.compile(r"\b(asks?|asked|offers?)\b")
NAMES_A_STEP = re.compile(r"\bstep \d+[a-z]?\b")
SAYS_NOTHING_TO_ASK = re.compile(r"\b(has no|from the start|already)\b")


def state_path():
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    return base / "environments" / "qa-agent-migrations.json"


def load_state():
    path = state_path()
    if not path.exists():
        return {"applied": {}}
    return json.loads(path.read_text())


def save_state(state):
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def migrations():
    return sorted(p.stem for p in MIGRATIONS_DIR.glob("*.md") if NAME.match(p.name))


def fresh_install_mode(migration_id):
    """ "ask" or "skip" from the migration's "## Fresh install" section; None if missing."""
    match = FRESH_INSTALL.search((MIGRATIONS_DIR / f"{migration_id}.md").read_text())
    return match.group(1) if match else None


def skip_reason_problem(section):
    """Why a `skip` line doesn't explain itself, or None when it does.

    `skip` means a new user never sees this migration. That is fine when
    configure-project asks the same question (then the line names that step,
    so a reader can check it) or when a fresh install has nothing to change.
    Anything else would leave new users without the setting.
    """
    if MENTIONS_A_QUESTION.search(section):
        if NAMES_A_STEP.search(section):
            return None
        return ("says configure-project asks the same thing but names no step; "
                "add it, e.g. '(product-config.md step 5)'")
    if SAYS_NOTHING_TO_ASK.search(section):
        return None
    return ("must name the configure-project step that asks the same question, "
            "or say a fresh install has nothing to change; otherwise use `ask`")


def lint():
    errors = []
    files = sorted(MIGRATIONS_DIR.glob("*.md"))
    numbers = []
    for p in files:
        m = NAME.match(p.name)
        if not m:
            errors.append(f"{p.name}: name must be NNN-<lowercase-slug>.md")
            continue
        numbers.append(int(m.group(1)))
        text = p.read_text()
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"{p.name}: missing section '{section}'")
        if "## Fresh install" in text and not FRESH_INSTALL.search(text):
            errors.append(f"{p.name}: '## Fresh install' must start with `ask` or `skip`")
        elif fresh_install_mode(p.stem) == "skip":
            problem = skip_reason_problem(FRESH_INSTALL_SECTION.search(text).group(1))
            if problem:
                errors.append(f"{p.name}: '## Fresh install' `skip` {problem}")
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"numbers must run 001, 002, ... without gaps; found {numbers}")
    return errors


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    state = load_state()
    applied = state.setdefault("applied", {})
    if cmd == "status":
        for mid in migrations():
            print(f"{'applied ' + applied[mid] if mid in applied else 'PENDING':<18} {mid}")
    elif cmd == "pending":
        for mid in migrations():
            if mid not in applied:
                print(mid)
    elif cmd in ("mark", "mark-all"):
        ids = migrations() if cmd == "mark-all" else sys.argv[2:]
        known = set(migrations())
        for mid in ids:
            if mid not in known:
                print(f"unknown migration: {mid}", file=sys.stderr)
                return 1
            applied.setdefault(mid, date.today().isoformat())
            print(f"marked:  {mid}")
        save_state(state)
    elif cmd == "fresh-install":
        for mid in migrations():
            if mid in applied:
                continue
            if fresh_install_mode(mid) == "ask":
                print(mid)
            else:
                applied[mid] = date.today().isoformat()
        save_state(state)
    elif cmd == "lint":
        errors = lint()
        for e in errors:
            print(e)
        if not errors:
            print(f"{len(migrations())} migration(s) ok")
        return 1 if errors else 0
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
