# 015: hand off long conversations to a fresh session, and see when to

## What changed

Every message in a Claude conversation re-reads its whole context, so a long
session (one ticket after another, or one ticket for hours) costs far more per
message than a short one. The new `session-handoff` skill saves the state of
the work on a ticket to `<workDir>/qa-evidence/<TICKET>/handoff.md` ("zapisz
stan") and loads it back in a fresh session after `/clear` ("kontynuuj
IP-123"). `setup.sh` registers a UserPromptSubmit hook
(`skills/session-handoff/scripts/context_hook.py`) that measures the context
and, past a threshold, either offers the handoff, does it, or stays silent, as
set in `~/.claude/environments/handoff.json` (shape:
`environments.example/handoff.example.json`). Without the file it offers
(`ask`) past 100k tokens. Optionally QA_Agent also sets the Claude Code status
line (`skills/session-handoff/scripts/statusline.py`): its `ctx` part shows
the context in percent and tokens and changes colour in step with the hook, so
the user sees when a conversation should be handed off.

## Is it needed

Needed if `~/.claude/environments/handoff.json` (or
`$CLAUDE_CONFIG_DIR/environments/handoff.json`) doesn't exist, or has no
`statusLine` field.

## Fresh install

`ask`: every user picks whether the hook offers, saves by itself, or stays
silent, and whether QA_Agent sets the status line.

## Steps

1. **Explain (runs by itself).** Say in two or three lines: long conversations
   cost more with every message; QA_Agent can save the work on a ticket to
   `handoff.md` in the ticket's folder, so you `/clear` and continue with
   `kontynuuj IP-123`; a hook can point this out once the context passes about
   100k tokens.
2. **Ask (tappable options; default in bold).** "What should happen when a
   conversation grows large?"
   - **ask**: Claude offers in one line to save the state and start fresh; it
     saves only after your yes → `"ask"`;
   - auto: Claude saves the state by itself and tells you, you decide when to
     `/clear` → `"auto"`;
   - never: no hint; saving still works when you ask ("zapisz stan") →
     `"never"`.
3. **Ask only if they want to change it.** "Start at 100k tokens?" **yes** →
   `100000`; or the number they give (e.g. 80k → `80000`). Skip for `never`.
4. **Explain the status line, then ask (tappable options; default in bold).**
   Show the current `statusLine` from `~/.claude/settings.json` (or say there
   is none). Explain in plain words how it works together with the hook: the
   bar at the bottom of Claude Code shows `ctx:14% 140k` (percent of the
   model's window and tokens), and the colour tells what to do:
   - green below 100k: carry on;
   - purple from 100k: the conversation is getting long, start the next
     ticket with `/clear`;
   - yellow from the threshold chosen above: that is the moment the hook
     saves (auto) or offers (ask) the handoff, so `/clear` and
     `kontynuuj IP-123`;
   - red with `/clear!` 20k later: auto-compact is close and will squeeze
     the conversation into a summary, so `/clear` now.
   It also shows the folder, git branch, model and the session's cost.
   "Should QA_Agent set this status line?"
   - **yes** → `"qa-agent"`; if they already have their own status line, say
     it will be saved to `~/.claude/statusline.previous.json` and can be
     brought back with `register_statusline.py --restore`;
   - no, keep mine (or none) → `"own"`.
   If the file exists already (an install that ran this migration before the
   status line was added), ask only this step and step 6.
5. **Write the file (runs by itself).** Write `environments/handoff.json` with
   `mode`, `thresholdTokens`, `repeatTokens` (`40000`), `statusLine` and the
   `notes` text from the example (keep the values already there), and show it. It's a plain file, not a symlink: it belongs
   to the machine, not to a product.
6. **Hook and status line (run by themselves).** Run
   `python3 -I <QA_Agent>/skills/session-handoff/scripts/register_handoff_hook.py`
   (`setup.sh` already does; this only makes sure). It stays registered even
   with `"never"`, and then prints nothing. With `"qa-agent"` run
   `python3 -I <QA_Agent>/skills/session-handoff/scripts/register_statusline.py`
   too. Say that both take effect in the next Claude session.

## Verify

- `python3 environments.example/validate_environments.py` passes and prints
  `handoff.json: ok`.
- `python3 -I <QA_Agent>/skills/session-handoff/scripts/context_hook.py --settings`
  prints the mode and threshold the user chose.
- `python3 -I <QA_Agent>/skills/session-handoff/scripts/register_handoff_hook.py --check`
  exits 0.
- With `"statusLine": "qa-agent"`:
  `python3 -I <QA_Agent>/skills/session-handoff/scripts/register_statusline.py --check`
  exits 0.
