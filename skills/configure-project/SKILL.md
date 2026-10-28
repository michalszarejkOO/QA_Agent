---
name: configure-project
description: Interactive setup wizard that configures this repo's skills (qa-tester, testing-api, routing-qa-tickets, create-quality-metrics, writing-test-cases) for a new team/product after cloning — asks which Atlassian MCP connectors are authorized and for which sites, then asks about each product (ticket prefixes, a required working directory where all of that product's QA output lands, repo path, web/mobile UI and/or API collection, credentials, where updated collections and environments are published (1Password, Confluence or nowhere), a project skill for product-specific knowledge), and writes the resulting ~/.claude/environments/*.json files the other skills already read. Never modifies skill files themselves, only generates config.
when_to_use: "Trigger on: 'set up QA_Agent', 'zrób setup', 'skonfiguruj QA_Agent', 'dodaj projekt', 'set up this project for my team', 'configure QA_Agent', 'onboard me onto this repo', 'I just cloned this, how do I set it up', running this after ./setup.sh for the first time, adding a new product's config to an existing setup, or any request to create/update files under ~/.claude/environments/. Do NOT trigger for updating an existing install after pulling QA_Agent changes (that's updating-qa-agent), for editing an existing environments/*.json file by hand (just edit it) or for questions about what a config field means (read environments.example/README.md instead)."
---

# Configure project

A one-time (or per-new-product) interactive wizard. This repo's skills never hardcode
which Jira site, which product, or which credentials to use — they all read
`~/.claude/environments/*.json` at runtime (see `environments.example/README.md`).
This skill is the guided path to producing those files correctly, instead of a new
user reverse-engineering the shape from the example templates and skill source by
hand.

This skill only asks questions, writes JSON config files under
`~/.claude/environments/` (and, optionally, `additionalDirectories` entries in the
user settings, `~/.claude/settings.json`), creates each product's working directory, and
scaffolds and links its project skill. It never edits anything under this
repo's `skills/` or `agents/`.

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Make sure `$CLAUDE_CONFIG_DIR/environments` (or `~/.claude/environments`) exists before writing any config: `./setup.sh` creates it, and if it's missing, create it yourself (`mkdir -p`) rather than stopping. |
| MUST | Write each product file to `<workDir>/config/<product>-<environment>.json` (the real file) and put only a symlink to it in `~/.claude/environments/`, the same way skills are linked into `~/.claude/skills/`. Everything about a product then lives in its working directory. Only the shared files (`atlassian-connectors.json`, `evidence.json`, `qa-agent-updates.json`) are real files in `~/.claude/environments/`. |
| NEVER | Put `<workDir>/config/` inside a git repo without gitignoring it: it holds credentials. If `git -C <workDir> rev-parse` succeeds, add `config/` to that repo's `.gitignore` (show the change first). |
| MUST | Read `environments.example/README.md`, `environments.example/app-with-ui.example.json`, and `environments.example/api-collection.example.json` fresh at the start of every run, not from memory — the shape is the source of truth and this skill must never drift from it. |
| MUST | Resolve each Atlassian connector's site with a live call to its own `getAccessibleAtlassianResources` tool, never by asking the user to type a site/cloudId from memory — see [references/connectors.md](./references/connectors.md). |
| MUST | Ask one section at a time (connectors, then one product at a time) and show the generated JSON before writing it, so the user can correct it before it lands on disk. |
| MUST | Get a working directory (`workDir`) from the user for every product before writing its file — it's required, with no silent default. Create it if missing. Every file a run produces for that product (evidence, API run output, worktrees, reports) lands there, so the user can remove a whole project by deleting one folder. |
| MUST | Offer every product a project skill (`projectSkill`, a skill folder inside its `workDir`, symlinked into `~/.claude/skills/`). It's where everything specific to that product goes, so this repo's skills stay product-agnostic and the knowledge goes away with the project folder. |
| MUST | Use the literal placeholder `REPLACE_ME` for any password/credential the user doesn't want to paste into the conversation, and say plainly that they'll need to edit the file afterward — never invent a fake credential. |
| MUST | End every run by running `python3 environments.example/validate_environments.py` and showing the result, fixing anything it flags before declaring the run done. |
| NEVER | Write, stage, or suggest committing anything under `environments/` — it's gitignored on purpose (real credentials live there). Only `environments.example/*` is ever committed. |
| NEVER | Overwrite an existing `environments/*.json` file without showing the user the diff and getting confirmation first — a second run to add a product must not silently clobber the first. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [references/connectors.md](./references/connectors.md) | Every run, before asking about products | Discovering which Atlassian MCP connectors are available this session, resolving each one's site live, writing `atlassian-connectors.json` |
| [references/product-config.md](./references/product-config.md) | For each product the user wants to configure | The question flow for one product (working directory, UI surfaces, API collection, credentials, where collections and environments are published, project skill) and how to assemble it into one `environments/<product>-<env>.json` file matching the example shapes exactly |
| [references/local-settings.md](./references/local-settings.md) | After all products are configured, if the user wants it | Adding each product's working directory and repos to `additionalDirectories` in the user settings (`~/.claude/settings.json`), so runs can write there from any folder; an optional starter allowlist |

## Procedure

1. **Run `./setup.sh`** from the repo root yourself (don't send the user off to do
   it) and show its output. It links skills and the agent, enables the git
   hooks, creates `~/.claude/environments/` and the repo's `environments` link,
   and registers Playwright MCP through its wrapper. Then route:
   - It lists **pending migrations** (an existing install from before a change):
     run the `updating-qa-agent` skill first, then come back here only if the
     user also wants to add a product.
   - A skill this procedure needs isn't available in this session (it was just
     linked): tell the user to restart Claude Code and repeat the request.

2. **Discover and configure Atlassian connectors.** Follow
   [references/connectors.md](./references/connectors.md). Skip entirely if the user
   says this project has no Jira/Confluence integration — later steps then omit the
   `jira` field and `api.confluence` block for every product.

3. **Configure one product at a time.** Ask "which product/repo do you want to
   configure first?" then follow
   [references/product-config.md](./references/product-config.md) for that product.
   After writing its file, ask whether there's another product to add (a monorepo
   with several independently-ticketed apps, or a team supporting more than one
   product) — repeat until the user says they're done. Each product gets its own
   `<product>-<environment>.json` file (e.g. `acme-staging.json`) in its
   `<workDir>/config/`, symlinked into `environments/`; a
   product with both a UI and an API collection gets both shapes merged into one
   file, per the example.

4. **Configure evidence recording.** Ask whether `qa-tester` should record and save
   run evidence (a video per scenario, sorted into happy path, error handling and
   edge cases, plus a separate folder per bug with its screenshot and video) on
   every run automatically (default) or ask before each run. Don't ask for a
   folder: evidence goes to each product's `<workDir>/qa-evidence/`. Write
   `environments/evidence.json` following
   `environments.example/evidence.example.json`, with `mode` set to `"auto"` or
   `"ask"`. It's one file for all products. If it already exists, show the diff
   before overwriting; an existing `dir` there stays only as the fallback for runs
   that match no product.

5. **Configure update checks.** Skip if `environments/qa-agent-updates.json`
   already exists (say what it's set to). Otherwise ask one question with
   tappable options: "When should I check for a newer version of QA_Agent?"
   - **once a week** (default; ask which day, Monday suggested),
   - twice a week (ask which two days, Monday and Thursday suggested),
   - on days you pick, every day, or never (you update by asking).
   Write `environments/qa-agent-updates.json` with `checkDays` (`["mon"]`,
   `["mon", "thu"]`, `"daily"` or `"never"`) following
   `environments.example/qa-agent-updates.example.json`, and show it. Say how it
   works: the first Claude session on such a day checks (or the next session
   when there was none that day), and if there's something new, Claude asks
   whether to see what's new and update; nothing is pulled without a yes.

6. **Offer folder access from anywhere.** Ask whether Claude may read and write
   the working directories and repo path(s) just configured without asking, from
   whatever folder it's opened in. If yes, follow
   [references/local-settings.md](./references/local-settings.md): it merges them
   into `permissions.additionalDirectories` of the user settings
   (`~/.claude/settings.json`), never overwriting the user's other settings.

7. **Validate.** Run `python3 environments.example/validate_environments.py` (from
   the repo root) and show the output. If it reports errors, fix the specific file
   and field it names and re-run until clean. On a first install (no product
   files existed before this run), then record every migration as applied, since
   this run already built the current layout:
   `python3 -I skills/updating-qa-agent/scripts/migrations.py mark-all`. When
   products already existed, leave migrations to the `updating-qa-agent` skill
   instead.

8. **Post-setup check.** Run the `checking-qa-agent` skill and include its report:
   it shows what's still missing on this machine (tools, playwright-video, Jira
   sites not reachable yet) with the command for each.

9. **Summarize.** List every file written or updated, every working directory
   and project skill created, and every symlink made (full paths), and remind the
   user of anything still marked `REPLACE_ME` that they need to fill in by hand
   before the config is fully live. Note explicitly that connector *authorization*
   (whether a connector is actually live for its site right now) can drift
   independently of these files — that's checked live by each skill at run time, not
   by this wizard.
