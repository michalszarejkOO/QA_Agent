---
name: configure-project
description: Interactive setup wizard that configures this repo's skills (qa-tester, testing-api, routing-qa-tickets, create-quality-metrics, writing-test-cases) for a new team/product after cloning — asks which Atlassian MCP connectors are authorized and for which sites, then asks about each product (ticket prefixes, repo path, web/mobile UI and/or API collection, credentials, Confluence tracker), and writes the resulting ~/.claude/environments/*.json files the other skills already read. Never modifies skill files themselves, only generates config.
when_to_use: "Trigger on: 'set up this project for my team', 'configure QA_Agent', 'onboard me onto this repo', 'I just cloned this, how do I set it up', running this after ./setup.sh for the first time, adding a new product's config to an existing setup, or any request to create/update files under ~/.claude/environments/. Do NOT trigger for editing an existing environments/*.json file by hand (just edit it) or for questions about what a config field means (read environments.example/README.md instead)."
---

# Configure project

A one-time (or per-new-product) interactive wizard. This repo's skills never hardcode
which Jira site, which product, or which credentials to use — they all read
`~/.claude/environments/*.json` at runtime (see `environments.example/README.md`).
This skill is the guided path to producing those files correctly, instead of a new
user reverse-engineering the shape from the example templates and skill source by
hand.

This skill only asks questions and writes JSON config files under
`~/.claude/environments/` (and, optionally, entries in the caller's
`.claude/settings.local.json`). It never edits anything under `skills/` or `agents/`.

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Run `./setup.sh` first (or confirm it's already been run) before writing any config — `environments/` must exist as a symlink into `$CLAUDE_CONFIG_DIR/environments` (or `~/.claude/environments`) before there's anywhere to write to. |
| MUST | Read `environments.example/README.md`, `environments.example/app-with-ui.example.json`, and `environments.example/api-collection.example.json` fresh at the start of every run, not from memory — the shape is the source of truth and this skill must never drift from it. |
| MUST | Resolve each Atlassian connector's site with a live call to its own `getAccessibleAtlassianResources` tool, never by asking the user to type a site/cloudId from memory — see [references/connectors.md](./references/connectors.md). |
| MUST | Ask one section at a time (connectors, then one product at a time) and show the generated JSON before writing it, so the user can correct it before it lands on disk. |
| MUST | Use the literal placeholder `REPLACE_ME` for any password/credential the user doesn't want to paste into the conversation, and say plainly that they'll need to edit the file afterward — never invent a fake credential. |
| MUST | End every run by running `python3 environments.example/validate_environments.py` and showing the result, fixing anything it flags before declaring the run done. |
| NEVER | Write, stage, or suggest committing anything under `environments/` — it's gitignored on purpose (real credentials live there). Only `environments.example/*` is ever committed. |
| NEVER | Overwrite an existing `environments/*.json` file without showing the user the diff and getting confirmation first — a second run to add a product must not silently clobber the first. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [references/connectors.md](./references/connectors.md) | Every run, before asking about products | Discovering which Atlassian MCP connectors are available this session, resolving each one's site live, writing `atlassian-connectors.json` |
| [references/product-config.md](./references/product-config.md) | For each product the user wants to configure | The question flow for one product (UI surfaces, API collection, credentials, Confluence tracker) and how to assemble it into one `environments/<product>-<env>.json` file matching the example shapes exactly |
| [references/local-settings.md](./references/local-settings.md) | After all products are configured, if the user wants it | Optionally scaffolding `.claude/settings.local.json` (`additionalDirectories` for each product repo, a starter permission allowlist) |

## Procedure

1. **Confirm prerequisites.** Check that `environments/` exists (as a symlink, from
   `./setup.sh`) and that `skills/`/`agents/` are linked into `$CLAUDE_CONFIG_DIR` (or
   `~/.claude`). If not, tell the user to run `./setup.sh` first and stop — don't
   write config into a location nothing will read from.

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
   `environments/<product>-<environment>.json` file (e.g. `acme-staging.json`); a
   product with both a UI and an API collection gets both shapes merged into one
   file, per the example.

4. **Offer local settings scaffolding.** Ask whether to also scaffold
   `.claude/settings.local.json` entries for the repo path(s) just configured. If
   yes, follow [references/local-settings.md](./references/local-settings.md]. If a
   `.claude/settings.local.json` already exists, merge into it — never overwrite the
   user's existing local permissions.

5. **Validate.** Run `python3 environments.example/validate_environments.py` (from
   the repo root) and show the output. If it reports errors, fix the specific file
   and field it names and re-run until clean.

6. **Summarize.** List every file written or updated (full path), and remind the
   user of anything still marked `REPLACE_ME` that they need to fill in by hand
   before the config is fully live. Note explicitly that connector *authorization*
   (whether a connector is actually live for its site right now) can drift
   independently of these files — that's checked live by each skill at run time, not
   by this wizard.
