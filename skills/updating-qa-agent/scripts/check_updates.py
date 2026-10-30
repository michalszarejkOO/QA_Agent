#!/usr/bin/env python3
"""Tells the user when the QA_Agent repo has new changes they haven't pulled.

Usage:
  check_updates.py --hook      Claude Code SessionStart hook: on a check day,
                               fetches and prints JSON with a message for the
                               user and context for Claude; otherwise nothing.
  check_updates.py             One line for people and scripts (check_setup.py),
                               from what the last fetch saw; never fetches.
  check_updates.py --force     Fetch now, whatever the settings, and print the line.
  check_updates.py --settings  Print the settings in effect as JSON.

Settings live in ~/.claude/environments/qa-agent-updates.json (written by
configure-project or migration 008; see environments.example/qa-agent-updates.example.json):
  "checkDays": ["mon"]          days of the week to check on (mon tue wed thu fri
                                sat sun), e.g. ["mon", "thu"] for twice a week
               "daily"          every day
               "never"          never; the user updates by asking
A missing file or a bad value means ["mon"]. QA_AGENT_UPDATE_CHECK=0 means never.

The hook runs when a session starts, is resumed (--continue / --resume) or is
cleared (/clear); the check itself runs the first of those times on a check day.
A check day without any of them isn't lost: the next one after it checks
instead. Later ones that day stay silent, whatever the answer was. The last successful check is
kept in ~/.cache/qa-agent/update-check.json; an offline start doesn't count, so
the next session tries again.

On a check day the hook also looks for migrations already pulled but not applied
on this machine (a `git pull` done in the terminal), and then asks the user to go
through them with the updating-qa-agent wizard. Other days stay silent about both.

It never pulls or changes anything: `git fetch` (8-second limit), then the local
branch is compared with its upstream. No network, no upstream or any git error
means silence: a session start must never fail or wait because of it.
"""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
SETTINGS = CLAUDE_DIR / "environments" / "qa-agent-updates.json"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "qa-agent" / "update-check.json"
MIGRATIONS = "skills/updating-qa-agent/migrations"
MIGRATIONS_SCRIPT = Path(__file__).with_name("migrations.py")
SHARED_FILES = {"atlassian-connectors.json", "evidence.json", "qa-agent-migrations.json", "qa-agent-updates.json"}

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DEFAULT_DAYS = ["mon"]


def git(*args, timeout=5):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=timeout)


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def valid_days(value):
    return value in ("daily", "never") or (
        isinstance(value, list) and value and all(d in DAYS for d in value))


def settings():
    """The settings in effect: {"checkDays": [...] | "daily" | "never"}."""
    days = load_json(SETTINGS).get("checkDays", DEFAULT_DAYS)
    if not valid_days(days):
        days = DEFAULT_DAYS
    if os.environ.get("QA_AGENT_UPDATE_CHECK") == "0":
        days = "never"
    if isinstance(days, list):
        days = sorted(set(days), key=DAYS.index)
    return {"checkDays": days}


def due(days, today=None):
    """True when a check day has come since the last successful check (today included)."""
    if days == "never":
        return False
    today = today or datetime.date.today()
    try:
        last = datetime.date.fromisoformat(load_json(CACHE).get("checked_on", ""))
    except ValueError:
        return True
    if last >= today:
        return False
    if days == "daily":
        return True
    wanted = {DAYS.index(d) for d in days}
    span = min((today - last).days, 7)
    return any((today - datetime.timedelta(days=i)).weekday() in wanted for i in range(span))


def mark_checked():
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"checked_on": datetime.date.today().isoformat()}))
    except OSError:
        pass


def new_migrations():
    """Titles of migrations the update brings ("008: ..."), from their first line."""
    names = git("diff", "--name-only", "--diff-filter=A", "HEAD...@{u}", "--", MIGRATIONS).stdout.split()
    titles = []
    for name in sorted(names):
        first = git("show", f"@{{u}}:{name}").stdout.split("\n", 1)[0]
        titles.append(first.lstrip("# ").strip() or Path(name).stem)
    return titles


def migration_title(migration_id):
    """ "009: compact ..." from the migration file's first line."""
    try:
        first = (REPO / MIGRATIONS / f"{migration_id}.md").read_text().split("\n", 1)[0]
    except OSError:
        return migration_id
    return first.lstrip("# ").strip() or migration_id


def waiting_migrations():
    """Titles of migrations pulled already but not applied here; [] before the first product is set up."""
    environments = CLAUDE_DIR / "environments"
    has_products = any(p.name not in SHARED_FILES for p in environments.glob("*.json"))
    if not has_products:
        return []
    try:
        out = subprocess.run([sys.executable, "-I", str(MIGRATIONS_SCRIPT), "pending"],
                             capture_output=True, text=True, timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        return []
    return [migration_title(mid) for mid in out.stdout.split()]


def release_notes():
    """Bullets the update adds to CHANGELOG.md (written for users, one per feature)."""
    diff = git("diff", "--unified=0", "HEAD...@{u}", "--", "CHANGELOG.md").stdout
    notes = []
    for line in diff.splitlines():
        if line.startswith("+- "):
            notes.append(line[3:].strip())
        elif line.startswith("+  ") and notes:
            notes[-1] += " " + line.strip(" +")
    return notes


def status(fetch):
    """None when there's nothing to report, else a dict describing the updates."""
    try:
        branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        upstream = git("rev-parse", "--abbrev-ref", "@{u}").stdout.strip()
        if not branch or not upstream or branch == "HEAD":
            return None
        if fetch:
            if git("fetch", "--quiet", upstream.split("/", 1)[0], timeout=8).returncode != 0:
                return None
            mark_checked()
        behind = int(git("rev-list", "--count", "HEAD..@{u}").stdout.strip() or 0)
        if behind == 0:
            return None
        subjects = git("log", "--format=%s", "HEAD..@{u}").stdout.strip().splitlines()
        dirty = bool(git("status", "--porcelain", "--untracked-files=no").stdout.strip())
        return {"upstream": upstream, "behind": behind, "subjects": subjects,
                "migrations": new_migrations(), "notes": release_notes(), "dirty": dirty}
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def describe(st):
    word = "change" if st["behind"] == 1 else "changes"
    line = f"QA_Agent: a newer version is available ({st['behind']} new {word} on {st['upstream']}"
    if st["migrations"]:
        line += f", {len(st['migrations'])} setup step(s) after pulling"
    line += "). Say \"aktualizuj skille\" / \"update QA_Agent\" to see what's new and update."
    if st["dirty"]:
        line += " Note: the QA_Agent repo has uncommitted changes; commit or stash them first."
    return line


def context(st, text):
    out = text + "\n"
    if st["notes"]:
        out += "Release notes (CHANGELOG.md, written for users):\n" + "\n".join(f"- {n}" for n in st["notes"]) + "\n"
    changes = "\n".join(f"- {s}" for s in st["subjects"][:15])
    if len(st["subjects"]) > 15:
        changes += f"\n- … and {len(st['subjects']) - 15} more"
    out += f"Commits waiting:\n{changes}\n"
    if st["migrations"]:
        out += "Migrations they bring: " + "; ".join(st["migrations"]) + "\n"
    out += ("At your first reply in this session, tell the user in their language that a newer QA_Agent "
            "is available (how many changes, how many migrations; name the main release notes in a few words "
            "if there are any) and ask whether they want to see what's "
            "new and update. On a yes, run the updating-qa-agent skill: its step 0 shows \"What's new\" from "
            "the full commit messages and migrations and asks for the final go before pulling, then it runs "
            "setup.sh and the migrations and says whether Claude Code needs a restart. On a no, carry on and "
            "don't bring it up again this session. Never update without their yes.")
    return out


def describe_waiting(waiting):
    word = "step" if len(waiting) == 1 else "steps"
    return (f"QA_Agent: {len(waiting)} setup {word} from the last update still to do on this machine "
            f"({'; '.join(waiting)}). Say \"aktualizuj skille\" / \"update QA_Agent\" to go through them.")


def waiting_context(text):
    return (f"{text}\nAt your first reply in this session, tell the user in their language that QA_Agent was "
            "updated but these setup steps (migrations) haven't been done on this machine yet, name each one "
            "in plain words, and ask whether to go through them now. On a yes, run the updating-qa-agent skill "
            "(nothing to pull, so its step 0 only confirms that): it runs each migration as a wizard, asking "
            "what only the user can decide. On a no, carry on and don't bring it up again this session.")


def main():
    if "--settings" in sys.argv:
        print(json.dumps(settings()))
        return 0
    if "--hook" in sys.argv:
        if not due(settings()["checkDays"]):
            return 0
        st = status(fetch=True)
        waiting = waiting_migrations()
        if st:
            text = describe(st)
            extra = context(st, text)
            if waiting:
                extra += "\nAlso still to do from an earlier update: " + "; ".join(waiting) + "."
        elif waiting:
            mark_checked()
            text = describe_waiting(waiting)
            extra = waiting_context(text)
        else:
            return 0
        print(json.dumps({
            "systemMessage": "📦 " + text,
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": extra},
        }))
        return 0
    st = status(fetch="--force" in sys.argv)
    if st:
        print(describe(st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
