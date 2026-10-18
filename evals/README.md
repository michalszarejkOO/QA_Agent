# Eval suite

A minimal regression suite for this repo's trickiest routing/branch-detection
logic, run with `claude plugin eval`. It does not cover every skill — it
targets the two places where a wrong decision is silent and easy to miss:

- `routing-qa-tickets`'s backend/frontend/mobile classification, including the
  two cases where it must ask instead of guessing (an unresolvable mobile
  target, mixed backend+frontend signals).
- `testing-api`'s ticket-mode "never auto-post" gate — that it always prepares
  a Jira comment/bug draft and asks before posting, never claims to have
  posted anything itself.

## Running it

```
claude plugin eval . --trust-plugin
```

This repo needs `.claude-plugin/plugin.json` to exist for `claude plugin eval`
to resolve its own skills by name inside the eval's child session at all —
without it, calls to e.g. `routing-qa-tickets` come back "Unknown skill." That
manifest doesn't change how this repo is actually distributed (`setup.sh`'s
symlinks into `~/.claude/skills`/`~/.claude/agents` are still it) — it exists
only so this eval suite has something to target.

Each case's `prompt.md` supplies ticket/PR/config context inline rather than
requiring live Jira/GitHub/filesystem access, so runs are fast, deterministic,
and don't touch any real environment. `allowed_tools` is deliberately narrow
per case (`Skill`, and `Agent` only where a case needs to verify a dispatch to
the `qa-tester` agent) so a run can't wander into real Bash/network calls.

## Known gap

`routing-frontend-web-clear` reliably reaches and states the right
classification (backend vs. frontend, which surface, which URL) but doesn't
always follow through with an actual `Agent` tool call to `qa-tester` — it
sometimes describes the dispatch tersely in prose instead of issuing it,
since the target URL isn't real in this sandbox and there's nothing further
it could do once the (nested) agent started. The classification logic itself
checks out; the last-mile "does it mechanically follow through" behavior
needs a firmer prompt before this case is reliable. Left as-is rather than
adding a workaround that would rig the grader instead of fixing the gap.
