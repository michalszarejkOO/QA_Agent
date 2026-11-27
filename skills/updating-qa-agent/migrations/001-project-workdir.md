# 001: one working directory per project

## What changed

Everything about a product now lives in its own working directory (`workDir`), so
dropping a project means deleting one folder:

- Product config files are real files in `<workDir>/config/<product>-<env>.json`;
  `~/.claude/environments/` holds only symlinks to them (plus the shared
  `atlassian-connectors.json` and `evidence.json`).
- Every product file has a required top-level `"workDir"`, and optionally
  `"projectSkill"`: a skill in `<workDir>/skills/<product>/` holding everything
  specific to the product, symlinked into `~/.claude/skills/<product>`.
- Run output goes under `workDir`: `qa-evidence/`, `api-runs/`, `worktrees/`,
  `reports/`. `evidence.json` keeps only `mode`; its `dir` is no longer used for
  products.
- Playwright MCP starts through `skills/testing-apps/scripts/playwright-mcp.sh`,
  so its automatic files go to `~/.cache/playwright-mcp/claude-<pid>/` instead
  of `.playwright-mcp/` in whatever folder Claude was opened in.

## Is it needed

Needed if any of these is true (check each; skip the steps for the parts that
already match):

1. `python3 -I skills/testing-apps/scripts/register_playwright_mcp.py --check`
   exits 1.
2. A product file in `~/.claude/environments/` (anything but
   `atlassian-connectors.json`, `evidence.json`, `qa-agent-migrations.json`) has no
   `workDir`, or is a real file rather than a symlink.
3. A product has no `projectSkill` and the user hasn't declined one before
   (ask once).
4. `evidence.json` has a `dir`.
5. A `.playwright-mcp/` folder exists under the user's project folders
   (`find ~/Projects -maxdepth 4 -type d -name .playwright-mcp`, or the parents of
   the repos named in the product files).

## Steps

1. **Playwright (automatic).** `./setup.sh` already ran
   `register_playwright_mcp.py`; if check 1 still fails, run it without
   `--check` and note that Claude Code needs a restart.
2. **Working directory, once per product (asks).** Group the product files by
   their `product` field. For each product:
   - Suggest a `workDir`: the common parent of the paths in its `surfaces.*.repo`,
     `api.repo` and `repos.*`, or the folder of the evidence `dir` it used if that
     sits inside a project folder. Ask the user to confirm or type another.
   - `mkdir -p <workDir>/config`. If `git -C <workDir> rev-parse` succeeds, add
     `config/` to that repo's `.gitignore` (show the change).
   - For each of the product's files: add `"workDir"` right after
     `"environment"` (show the diff), move the file to `<workDir>/config/`, and
     put a symlink to it at its old path in `~/.claude/environments/`.
   - If its API collection lives outside `workDir` and outside any git repo,
     offer to copy it into `<workDir>/<client>/` (originals untouched, no secrets
     in copied environment files) and point `api.repo` there.
3. **Project skill, once per product (asks).** Follow step 7 of
   `skills/configure-project/references/product-config.md`: point at an
   existing skill or scaffold one from
   `skills/configure-project/assets/project-skill-template.md`, symlink it into
   `~/.claude/skills/<product>`, and add `"projectSkill"` to each of the
   product's files. If Claude's memory holds lasting facts about this product,
   offer to move them into the new skill.
4. **Evidence folder (asks).** Remove `dir` from `evidence.json` (show it). If
   that folder holds evidence, offer to move each `<TICKET>/` subfolder into the
   `<workDir>/qa-evidence/` of the product whose `ticketPrefixes` match the
   ticket key. Leave anything that matches no product where it is and list it.
5. **Old Playwright output (asks).** For each `.playwright-mcp/` folder found,
   show its size and file count and ask: delete, or move into a product's
   `qa-evidence/_legacy-playwright-mcp/`.

## Verify

- `python3 environments.example/validate_environments.py` reports every file `ok`.
- Every product file in `~/.claude/environments/` is a symlink into a
  `<workDir>/config/`.
- `register_playwright_mcp.py --check` exits 0.
- `evidence.json` has no `dir`.
