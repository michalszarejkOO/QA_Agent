# 021: hand off at 200k and compact at 250k tokens

## What changed

Users found the old limits too tight: the session-handoff hook spoke at 100k
tokens and auto-compact was recommended at 200k, so long QA sessions were
interrupted by a handoff or a compaction very often. The defaults are now
higher: the hook speaks at 200k (`thresholdTokens` in
`environments/handoff.json`, and in `context_hook.py` when the file has none)
and QA_Agent recommends `"autoCompactWindow": 250000`, which leaves the hook
room before Claude Code compacts. README, "Context and token cost", has the
cost of each window. Installs that wrote the old values keep them until this
migration asks; a value the user chose themselves is left alone.

## Is it needed

Needed if either holds:
- `~/.claude/environments/handoff.json` (or under `$CLAUDE_CONFIG_DIR`) has
  `"thresholdTokens": 100000`;
- the user settings, `~/.claude/settings.json` (or
  `$CLAUDE_CONFIG_DIR/settings.json`), have `"autoCompactWindow": 200000` (or
  `"200k"`) and the environment variable `CLAUDE_CODE_AUTO_COMPACT_WINDOW`
  isn't set.
Any other value, or none, is the user's own choice: not needed for that part.

## Fresh install

`skip`: a fresh install already asks both limits with the new defaults, in
migration 019 step 3 (handoff threshold, 200k) and migration 009 step 2
(compact window, 250k), which configure-project runs in the first setup.

## Steps

1. **Explain (runs by itself).** Say in two or three lines: the handoff hint
   came at 100k tokens and compaction at 200k, which interrupted long sessions
   too often; the new defaults are handoff at 200k and compact at 250k, so the
   hint still comes before Claude Code squeezes the conversation into a
   summary. Show the current values.
2. **Handoff threshold (ask only if handoff.json has 100000; tappable options,
   default in bold).** "From how many tokens should the handoff hint come?"
   - **200k (new default)** → `200000`;
   - keep 100k → leave it;
   - their own number (e.g. 150k → `150000`).
3. **Compact window (ask only if autoCompactWindow is 200000; tappable
   options, default in bold).** "When should Claude Code compact a session?"
   - **at 250k tokens (new recommendation)** → `250000`;
   - keep 200k → leave it;
   - their own number (e.g. 300k → `300000`).
   If the handoff threshold chosen in step 2 (or kept) is not below the compact
   window, say that the hint would then come only after compaction, and
   suggest a compact window at least 50k above it.
4. **Write (runs by itself).** Change only `thresholdTokens` in
   `environments/handoff.json` and only `autoCompactWindow` in the user
   settings, keeping every other key, and show the changed lines. New sessions
   use them; for the current one the user runs `/autocompact 250k` (or the
   chosen value). The status line picks up the threshold at once.

## Verify

- `python3 environments.example/validate_environments.py` passes and prints
  `handoff.json: ok`.
- `python3 -I <QA_Agent>/skills/session-handoff/scripts/context_hook.py --settings`
  prints the chosen threshold.
- `check_setup.py --full` prints `OK sessions compact at 250k tokens`, or INFO
  with the chosen value.
- The user settings file is still valid JSON and its other keys are unchanged.
