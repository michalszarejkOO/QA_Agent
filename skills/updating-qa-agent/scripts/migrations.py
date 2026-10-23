#!/usr/bin/env python3
"""Tracks which QA_Agent migrations have been applied on this machine.

Usage:
  migrations.py status            list migrations, applied or pending
  migrations.py pending           print pending migration ids, one per line
  migrations.py mark <id> [...]   record migrations as applied
  migrations.py mark-all          record every existing migration as applied
                                  (a fresh install already has the current layout)
  migrations.py lint              check migration files: numbering and sections

Migrations are the files in ../migrations/NNN-<slug>.md. State lives in
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
REQUIRED_SECTIONS = ("## What changed", "## Is it needed", "## Steps", "## Verify")


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
