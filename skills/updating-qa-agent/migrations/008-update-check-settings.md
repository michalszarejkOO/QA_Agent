# 008: choose on which days QA_Agent checks for a newer version

## What changed

`setup.sh` registers a SessionStart hook that checks the QA_Agent repo for new
changes and, when there are some, says a newer version is available and asks
whether to see what's new and update. It checks only on the days of the week
the user picks, saved per machine as `checkDays` in
`~/.claude/environments/qa-agent-updates.json` (shape:
`environments.example/qa-agent-updates.example.json`). Without the file it
checks on Mondays, so this migration only lets each user pick once. Nothing is
ever pulled without the user's yes.

## Is it needed

Needed if `~/.claude/environments/qa-agent-updates.json` (or
`$CLAUDE_CONFIG_DIR/environments/qa-agent-updates.json`) doesn't exist.

## Steps

1. **Ask (tappable options; default in bold).** "When should I check for a
   newer version of QA_Agent?"
   - **once a week**, then which day (Monday suggested) → `["mon"]`;
   - twice a week, then which two days (Monday and Thursday suggested) →
     `["mon", "thu"]`;
   - other days the user names → their list; every day → `"daily"`;
     never (they update by asking) → `"never"`.
   Say how it works: the first Claude session on such a day checks (a new one,
   a resumed one, or after `/clear`); if there was none that day, the next one
   does; if there's something new,
   Claude asks whether to see what's new and update.
2. **Write the file (runs by itself).** Write
   `environments/qa-agent-updates.json` with `checkDays` and the `notes` text
   from the example, and show it. It's a plain file, not a symlink: it belongs
   to the machine, not to a product.
3. **Hook (runs by itself).** Run
   `python3 -I <QA_Agent>/skills/updating-qa-agent/scripts/register_update_hook.py`
   (`setup.sh` already does; this only makes sure). It stays registered even with
   `"never"`, and then prints nothing.

## Verify

- `python3 environments.example/validate_environments.py` passes and prints
  `qa-agent-updates.json: ok`.
- `python3 -I <QA_Agent>/skills/updating-qa-agent/scripts/check_updates.py --settings`
  prints the days the user chose.
