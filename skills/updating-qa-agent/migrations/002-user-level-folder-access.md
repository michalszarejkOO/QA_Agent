# 002: folder access to every product's working directory, from anywhere

## What changed

QA_Agent works from whatever folder Claude Code is opened in, and every run
writes into the product's `workDir`. Folder access used to be offered only as a
`.claude/settings.local.json` in the folder where setup ran, so a session opened
anywhere else asked for permission each time it saved output into a product
folder. Now each product's `workDir` (and any repo outside it) goes into
`permissions.additionalDirectories` of the user settings, `~/.claude/settings.json`
(or `$CLAUDE_CONFIG_DIR/settings.json`). Project skills also gained a rule: every
file made for a product goes into its `workDir`, never the current folder.

## Is it needed

Needed if any product file in `~/.claude/environments/` has a `workDir` (or a repo
path outside it) that isn't covered by an entry of
`permissions.additionalDirectories` in the user settings (covered = the same
folder or one of its parents, after expanding `~`).

Also check each product's `projectSkill`: if its `SKILL.md` has no rule saying
that files made for the product go into its working directory, that part is
needed too.

## Steps

1. **Folder access (asks).** List the product folders that aren't covered yet.
   Follow `skills/configure-project/references/local-settings.md`: read
   `~/.claude/settings.json`, merge the missing paths into
   `permissions.additionalDirectories` (keep every other setting as it is), show
   the before/after of `permissions`, and write it only after the user agrees.
2. **Old project-level entries (asks).** If the QA_Agent repo has a
   `.claude/settings.local.json` whose `additionalDirectories` only repeat paths
   now in the user settings, offer to remove those entries; leave anything else
   in that file alone.
3. **Project skill rule (asks).** For each project skill missing the rule, show
   this paragraph and add it after the skill's opening paragraph (fill in the
   product name and its `workDir`):

   > **Every file you create for <Product> goes into its working directory,
   > `<workDir>`, wherever Claude was opened**: test output goes where the testing
   > skills put it (`qa-evidence/`, `api-runs/`, `worktrees/`, `reports/`), and
   > anything else (notes, plans, scripts, SQL, exports, data dumps) goes into
   > `notes/` or `scripts/` there, created as needed. Never into the current
   > folder, the Desktop, `/tmp` or `~/Downloads`. Give the full path of anything
   > you save.

   If the project skill folder is a git repo, commit the change there.

## Verify

- `check_setup.py --full` reports no "not in additionalDirectories" warning.
- Each project skill's `SKILL.md` contains "Every file you create for".
- Claude Code needs a restart for new `additionalDirectories` to apply.
