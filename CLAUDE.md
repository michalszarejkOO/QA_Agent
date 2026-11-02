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
- **Before every commit that touches `skills/`, `agents/`, scripts, hooks,
  `setup.sh` or `environments.example/`, decide whether other users' installs
  are affected**: a config field, a user setting (`~/.claude/settings.json`),
  an MCP registration, a file or folder that moves, a new place output goes,
  or a new choice the user should make. Say the answer to the user before
  committing, even when it's "no".
  - Affected → add a migration in the same commit (see
    `skills/updating-qa-agent/SKILL.md`, "Writing a migration"). Write its Steps
    as a wizard (explain, ask with a default, do the rest, show the result) and
    choose its "Fresh install": `ask` if new users must make the same choice
    (configure-project then runs it in the first setup), `skip` if it only fixes
    older installs. Run
    `python3 -I skills/updating-qa-agent/scripts/migrations.py lint`.
  - Not affected (skill text only) → no migration.
  - End the commit message with `Migration: NNN-<slug>` or
    `Migration: none (<why>)`.
- **Skill descriptions.** Claude Code lists every skill with its
  `description` and `when_to_use` and cuts the pair after 1536 characters, so
  keep the two together within 1536. Don't use `<` or `>` in them (the listing
  shows `&lt;` `&gt;`; write an example such as `ABC-123` instead of a
  placeholder), and no colon followed by a space in an unquoted `description`
  (it breaks strict YAML parsers). The same applies to project skills that
  configure-project generates from its template.
- **Before opening a pull request, write the release note** in `CHANGELOG.md`
  under `## Unreleased`, as its own commit ("Changelog: ..."). Read all the
  branch's commits (`git log <base>..HEAD`), group them by feature and write one
  bullet per feature, not per commit, in the user's terms: what they can do now,
  what works differently, what the update will ask (name the migration's
  question, not its number). Fold purely internal work (tests, evals, wording)
  into one "Smaller fixes" bullet or leave it out. Use the same bullets as the
  pull request description. When a version branch is cut (e.g. `1.2.0`), rename
  `## Unreleased` to the version and start a new empty `## Unreleased` above it.
  Claude shows these entries to everyone who updates.
- Repo content is in English.
