# QA_Agent

This repo holds a QA agent and skills for Claude Code. `./setup.sh` links them into
`~/.claude/` so they work from any folder. They stay product-agnostic: everything
about one product lives in that product's own working directory (see README,
"Generic skills here, project knowledge in the project").

## Setting up or updating

When the user asks to set up, configure, install, refresh or update QA_Agent, in
any wording ("set up QA_Agent", "zrób setup", "skonfiguruj", "update QA_Agent",
"aktualizuj skille", "I just cloned this", "I pulled changes"):

1. Run `./setup.sh` from the repo root and show its output. It links skills and
   the agent, enables the git hooks, prepares `~/.claude/environments/`,
   registers Playwright MCP through its wrapper, registers the
   update-check hook (at session start it says when QA_Agent has new changes and
   asks whether to update; settings in `environments/qa-agent-updates.json`),
   installs the 1Password CLI (`op`) if a product publishes to 1Password and it's
   missing, and reports what's next.
2. Follow what it reports:
   - "No products yet" → run the `configure-project` skill (connectors, then one
     product at a time, each with its own working directory and project skill).
   - "Pending migrations" → run the `updating-qa-agent` skill.
   - "All migrations applied" → say the setup is up to date and offer to add a
     product with `configure-project`.
3. Both skills end with the `checking-qa-agent` report. When the user only asks
   whether everything works ("sprawdź setup", "check QA_Agent"), run
   `checking-qa-agent` alone: it only reports, it never changes anything.
4. If a skill named above isn't available yet, the session started before
   `setup.sh` linked it: tell the user to restart Claude Code in this folder and
   repeat the request.

## Changing QA_Agent

- Keep `skills/` and `agents/` product-agnostic. Product-specific rules go into
  that product's project skill, never here.
- If a change needs something done on machines that already use QA_Agent, add
  a migration in the same commit (see `skills/updating-qa-agent/SKILL.md`, "Writing
  a migration") and run
  `python3 -I skills/updating-qa-agent/scripts/migrations.py lint`.
- Repo content is in English.
