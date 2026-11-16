---
name: session-handoff
description: Saves the state of work on a ticket to handoff.md in the ticket's folder (what was checked, findings, decisions, drafts and whether they were posted, open questions, the next step), so the user can /clear a long conversation and carry on in a fresh one, and loads it back at the start of that new session. Keeps one current file per ticket, rewritten on every save. A hook can point out when the context has grown large (environments/handoff.json, mode ask, auto or never).
when_to_use: "Trigger on: 'zapisz stan', 'zapisz stan pracy nad IP-123', 'zrób handoff', 'save the state', 'hand off this session', 'kontynuuj IP-123', 'wczytaj handoff', 'resume IP-123', 'where did we stop on IP-123', a session-handoff note from the context hook, or a new session that names a ticket with a handoff.md in its folder. Do NOT trigger for the Jira comment (writing-jira-comments), test cases (writing-test-cases) or product-wide knowledge (that goes into the project skill)."
---

# Session handoff

A long conversation costs more with every message, because each one re-reads
the whole context. This skill moves the state of the work out of the
conversation into a file, so the user can `/clear` and continue in a short one.
The file is for Claude in the next session: facts and pointers, not prose.

## Where

`<workDir>/qa-evidence/<TICKET>/handoff.md`, next to the ticket's test cases,
evidence and notes.

- `workDir` comes from the product file in `~/.claude/environments/` (or
  `$CLAUDE_CONFIG_DIR/environments/`) whose `ticketPrefixes` match the key.
  Create the ticket folder if it doesn't exist.
- The ticket: the one the conversation is about. Several tickets → ask which,
  or save one file per ticket if the user says all. No ticket (a feature, a
  PR) → the folder is named after the feature in lowercase words joined by
  `-`, or `PR-<number>`.
- No product file matches → `./qa-evidence/<TICKET>/handoff.md` in the current
  folder, and say that no working directory is configured for this product.
- **No ticket and no product** (work on QA_Agent itself, a script, a setup, a
  longer question): always ask first, also in `auto` mode, whether to save a
  handoff, and propose where, with the path on its own line:
  `~/.claude/handoffs/<topic>.md`, where the topic is a few lowercase words
  joined by `-` (e.g. `qa-agent-session-handoff`). Outside every repo, so it
  never ends up in a commit. Offer the user's own path as the other option.
  Say what it would hold (the work in progress, where the changes are, e.g.
  uncommitted files on a branch, and the next step).
- Never the Desktop, `/tmp`, `~/Downloads` or the session's scratchpad.

## Saving

1. If `handoff.md` exists, read it first. Write one current state: carry over
   what is still true, drop what the conversation has settled or replaced.
2. Write it in English, in this shape (leave out a section with nothing in it):

   ```markdown
   # IP-123 handoff
   Updated: 2026-11-16 14:20 · Product: emtethal · Environment: stage
   Ticket: https://example.atlassian.net/browse/IP-123 · PR: https://...

   ## Goal
   What this work is for, in one or two lines (test the ticket, retest the fix, ...).

   ## Done
   - What was checked or changed, with the result and where the evidence is (path).

   ## Findings and decisions
   - Facts learned, causes found, choices the user made and why.

   ## Drafts
   - Jira comment / bug report / test cases: path, and posted or not posted.

   ## Test data
   - Users, records, ids in use, and their state now.

   ## Open
   - Questions waiting for someone (who), blockers.
   - Agents still running when this was saved: what each one does and where
     its output goes. Their results aren't in this file.

   ## Next
   1. The next concrete step, then the ones after it.

   ## Don't redo
   - Things already ruled out or set up, so the next session doesn't repeat them.
   ```

3. Rules: only what the conversation actually established, never a guess
   written as a fact. Absolute paths and full links. No secrets (tokens,
   passwords, API keys): point to the product config instead. Short, about
   80 lines at most; details stay in the files it points to.
4. In the chat: the file's path on its own line, then the two steps, each on
   its own line: `/clear`, and `kontynuuj IP-123` (with the real key).
5. **An agent still running** (a subagent or background task started in this
   conversation that hasn't reported back): saving is fine, but `/clear` now
   would lose its result. Never stop or cancel it for a handoff. List it under
   "Open", and instead of the two steps tell the user to wait: say which agent
   is still working, and that once it reports you'll update the handoff and
   then `/clear` is safe. When its result arrives, add it to the file (Done,
   Findings, Drafts) before offering `/clear`.

## Loading

1. Find the file as in "Where"; for a topic rather than a ticket key, look in
   `~/.claude/handoffs/` (the closest name; several → ask which). None → say
   so and offer to start from the ticket (reading-jira-tickets).
2. Read it and list the ticket folder. Don't re-read the ticket, the PR or the
   evidence it already sums up; open them only when the next step needs them.
3. Tell the user in three to five lines where the work stopped (from "Next"
   and "Open"), with the "Updated" date when it's older than a day, and
   continue with the next step unless it needs their decision.
4. When the work moves on, the next save rewrites the file.

## The context hook

`setup.sh` registers `scripts/context_hook.py` as a UserPromptSubmit hook. It
reads the size of the conversation's context from the transcript and, past
`thresholdTokens` (default 100000), adds a note to the turn. `mode` in
`environments/handoff.json`: `ask` (default) offers the handoff in one line,
`auto` saves it without asking and says so, `never` stays silent. It speaks
again only after the context grows by `repeatTokens` (default 40000) and starts
over after `/compact` or `/clear`. The note is a hint, not an order: when the
conversation isn't about work worth carrying on, ignore it. With no ticket and
no product, ask and propose a path as "Where" says, in every mode. Check the settings
in effect with
`python3 -I ~/.claude/skills/session-handoff/scripts/context_hook.py --settings`

## The status line

With `"statusLine": "qa-agent"` in `environments/handoff.json`, `setup.sh`
sets `scripts/statusline.py` as the Claude Code status line. Its `ctx` part
shows the context in percent and tokens and changes colour in step with the
hook: green below 100k, purple from 100k, yellow from `thresholdTokens` (the
hook saves or offers the handoff), red with `/clear!` 20k later (auto-compact
is close). The user's previous status line is kept in
`~/.claude/statusline.previous.json`; `scripts/register_statusline.py
--restore` brings it back.
