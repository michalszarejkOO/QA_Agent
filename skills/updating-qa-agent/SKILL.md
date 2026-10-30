---
name: updating-qa-agent
description: Brings an existing QA_Agent install up to date after pulling changes — runs ./setup.sh, then applies every pending migration from this skill's migrations/ folder in order (moving configs, adding new required fields, re-registering MCP servers, cleaning up old locations), asking the user only what can't be worked out, so every machine ends up with the same layout. Also the place where anyone changing QA_Agent records what existing installs need to do. Use after `git pull` on this repo, or when asked to update/refresh/redo the QA_Agent setup.
when_to_use: "Trigger on: 'aktualizuj skille', 'zaktualizuj QA_Agent', 'zrób na nowo setup', 'zrób setup' on a machine that already has product configs, 'pobrałem zmiany w QA_Agent', 'update the QA agent', 'I pulled the latest QA_Agent', 'refresh my setup', a session-start note that QA_Agent has new changes, 'pozbieraj pliki projektów', 'gather project files', 'zmień ustawienia aktualizacji', 'change update settings', or ./setup.sh reporting pending migrations. Do NOT trigger for a first install with no product configs yet, or for adding a new product (that's configure-project), or for editing one config field by hand."
---

# Updating QA_Agent

`git pull` updates the skills' text at once (they're symlinked), but some changes
also need something done on each machine: a new required config field, files
moved to a new place, an MCP server registered differently. Each such change
ships a **migration**: a file in [migrations/](./migrations/) saying how to tell
whether a machine needs it and how to apply it. This skill applies the pending
ones in order, so every install ends up the same no matter how many updates it
skipped.

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Apply migrations in number order, one at a time, and record each as applied (`scripts/migrations.py mark <id>`) only after its "Verify" section passes. |
| MUST | Run each migration's "Is it needed" check first. If the machine already matches, mark it applied without changing anything and say so. |
| MUST | Show the user what you're about to move, delete or re-register before doing it, and ask for anything only they can decide (a project's working directory, whether to delete old files). Suggest a default whenever there is one. |
| NEVER | Delete user data (evidence, notes, configs) without an explicit yes for that specific folder. Moving is preferred over deleting. |
| NEVER | Commit or stage anything under a product's `config/` or `~/.claude/environments/` — they hold credentials. |

## Procedure

0. **Pull new changes, if there are any (asks).** Run
   `python3 -I ~/.claude/skills/updating-qa-agent/scripts/check_updates.py --force`.
   If it reports new changes on the upstream branch, show **"What's new"** before
   asking, in the user's language:
   - Read the full messages: `git -C <repo> log --format='%h %s%n%b' HEAD..@{u}`.
   - Read each new migration, `git -C <repo> diff --name-only --diff-filter=A
     HEAD...@{u} -- skills/updating-qa-agent/migrations/`, with `git -C <repo>
     show @{u}:<path>` ("What changed", and from "Steps" what it will ask).
   - List new skills or agents: `git -C <repo> diff --name-status HEAD...@{u} --
     skills agents` (an added `SKILL.md` or agent file).
   Then write, briefly:
   - **What's new:** up to about 8 bullets, one per change the user will notice,
     in plain words (what they can do now or what works differently), not file
     names. Merge follow-up commits of one point into one bullet; sum up purely
     internal ones (tests, evals, wording) as one "smaller fixes" line.
   - **After the update:** each migration with what it will ask, or "none";
     whether Claude Code needs a restart (a new skill or agent, or a migration
     that re-registers an MCP server says so) or "no restart".
   - A warning if the repo has uncommitted changes.
   Take everything from the commit messages and migration files; never add what
   they don't say. A vague message ("fix") stays vague: show its title as is.
   Then ask whether to update. On a yes run `git -C <repo> pull --ff-only`. If
   the repo has uncommitted changes, or the pull can't fast-forward, stop and
   explain instead of stashing, merging or resetting anything. The update-check
   hook (registered by `setup.sh`, settings in `environments/qa-agent-updates.json`)
   is what tells the user at session start that such changes exist.
1. **Run `./setup.sh`** from the QA_Agent repo (resolve it from the
   `~/.claude/skills/updating-qa-agent` symlink) and show its output. It does
   everything that needs no decision: links skills and the agent, creates
   `~/.claude/environments/`, registers Playwright through its wrapper, removes
   dangling config links, and lists pending migrations.
   If it reports **no products yet**, this is a first install, not an update:
   run the `configure-project` skill instead and stop here.
2. **List pending migrations:**
   `python3 -I ~/.claude/skills/updating-qa-agent/scripts/migrations.py status`.
   None pending → say the setup is up to date, run the validator (step 4), stop.
3. **For each pending migration, in order:** read its file, run "Is it needed",
   then "Steps", then "Verify". Mark it applied when Verify passes. If a step is
   blocked (the user declines, a path doesn't exist), stop at that migration and
   say what's left; don't skip ahead, later migrations may depend on it.
4. **Validate:** `python3 environments.example/validate_environments.py` from the
   repo root. Fix what it reports before finishing.
5. **Post-update check:** run the `checking-qa-agent` skill and include its report.
6. **Summarize:** each migration applied or skipped (already matched), every file
   moved, created or deleted (full paths), anything left for the user (e.g.
   `REPLACE_ME` values), and whether Claude Code needs a restart (an MCP server
   was re-registered).

## Gathering project files again

Migration 007 runs once, but files can pile up outside the working directories
again (`checking-qa-agent` reports them as "project files outside their working
directories"). When the user asks to gather them ("pozbieraj pliki projektów",
"gather project files"), follow the Steps of
[migrations/007-gather-project-files.md](./migrations/007-gather-project-files.md)
again, whether or not 007 is marked applied: search, then ask before every move,
never delete anything. Don't mark anything.

## Changing update-check settings

When the user wants QA_Agent to check for new versions on other days
("zmień ustawienia aktualizacji", "sprawdzaj aktualizacje w poniedziałki i
czwartki", "nie sprawdzaj aktualizacji", "change update settings"), show what
`python3 -I <this skill>/scripts/check_updates.py --settings` prints, ask (same
options as Steps 1 of
[migrations/008-update-check-settings.md](./migrations/008-update-check-settings.md)),
and write `checkDays` in `~/.claude/environments/qa-agent-updates.json` (show the
diff first). It takes effect at the next session; nothing needs re-registering.

## Writing a migration (for anyone changing QA_Agent)

Add a migration **in the same commit** as any change that existing installs
can't pick up from `git pull` alone and that needs a decision or moves user
data: a new required config field, a file or folder that moves, a new or
changed MCP registration, a new place output goes. A change that only edits
skill text needs no migration. Removing or renaming a skill folder needs no
migration either: add its old name to `RETIRED_SKILLS` in `setup.sh`, which
removes the dangling link on every machine.

Create `migrations/NNN-<slug>.md` with the next free number and these sections:

```markdown
# NNN: <title>

## What changed
One paragraph: what's different now and why.

## Is it needed
Checks that tell whether this machine still needs the migration. Must be safe
to run any number of times.

## Steps
Numbered. Mark which steps run by themselves and which ask the user (with the
suggested default).

## Verify
What must be true afterwards (usually: the validator passes, plus specific checks).
```

Then run `python3 -I skills/updating-qa-agent/scripts/migrations.py lint`, and on
your own machine apply it through this skill like anyone else would.
`configure-project` marks every existing migration as applied on a fresh
install, since a new setup is already built in the current layout.
