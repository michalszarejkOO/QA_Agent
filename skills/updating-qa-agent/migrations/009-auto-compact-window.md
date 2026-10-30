# 009: compact Claude Code sessions at 200k tokens

## What changed

Current models (Opus 4.7 and later, Sonnet 5 and later) run in Claude Code with
a 1M-token context window by default, so a session compacts only near 1M tokens
and every turn resends the whole conversation. For a long QA day that costs
about 3x more than compacting at 200k (numbers in README, "Context and token
cost"). QA_Agent now recommends `"autoCompactWindow": 200000` in the user
settings, and `check_setup.py --full` reports the current value. This migration
offers the setting once; the user may keep the default.

## Is it needed

Needed if the user settings, `~/.claude/settings.json` (or
`$CLAUDE_CONFIG_DIR/settings.json`), have no `autoCompactWindow` key and the
environment variable `CLAUDE_CODE_AUTO_COMPACT_WINDOW` isn't set. If either is
set, the user has already chosen: not needed.

## Fresh install

`ask`: the window is the user's choice, so configure-project runs these
Steps on a new machine too.

## Steps

1. **Explain (runs by itself).** Show the table from README, "Context and token
   cost", in short: a long day is about $6–10 at 200k, $9–14 at 300k and $18–35
   at 1M, a long single session can go back to 1M with `/autocompact auto`, and a
   session that stays under 200k costs the same either way.
2. **Ask (tappable options; default in bold).** "When should Claude Code compact
   a session?"
   - **at 200k tokens (recommended)** → `200000`;
   - at 300k tokens → `300000`;
   - keep the default (near 1M) → write nothing.
3. **Write the setting (runs by itself after the answer).** Read the user
   settings, add `autoCompactWindow` with the chosen value, keep every other
   setting as it is, and show the changed line. If the user kept the default,
   change nothing.
4. **Say when it applies.** New sessions use it. For the current session, the
   user runs `/autocompact 200k` (or the chosen value).

## Verify

- `check_setup.py --full` prints `OK sessions compact at 200k tokens`, or INFO
  with the chosen value, or INFO "auto-compact window not set" if the user kept
  the default.
- The user settings file is still valid JSON and its other keys are unchanged.
