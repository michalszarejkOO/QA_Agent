# 011: An API collection can live only where it is published

## What changed

`api.repo` is now optional. A product whose collection and environments are
both published to 1Password or Confluence no longer needs a local folder for
them (often `<workDir>/postman/`, a git repo nobody else sees, or a plain
folder): every `testing-api` run, generic ones too, downloads the published
copy into its run folder and works there, and publishing uploads what that run
changed. A local folder next to it was a second copy that drifted from the
published one. If the target can't be read, the run falls back to the newest
copy an earlier run left in `<workDir>/api-runs/` and doesn't publish until the
target is back. A collection kept in a git repo the team shares (a Bruno
collection inside the backend repo, say) keeps `repo` as before.

## Is it needed

Needed when a product config in `~/.claude/environments/` (or
`$CLAUDE_CONFIG_DIR/environments/`) has all of:

- an `api.repo`;
- `api.publish.collection` and `api.publish.environments` both `1password` or
  `confluence`;
- an `api.repo` folder that isn't a git repo, or is one with no remote
  (`git -C <repo> remote` prints nothing).

Otherwise not needed: no such product, or every such folder is a shared repo.
Once applied it isn't asked again, also for folders the user chose to keep.

## Fresh install

`skip`: configure-project asks where a new product's collection lives
(product-config.md step 5).

## Steps

Group the product configs that point at the same `api.repo` folder (IMS
development, staging and uat often share one) and go through one folder at a
time.

1. **Explain (runs by itself).** Say in short: the collection is already
   published to <target>, and every test run can download it from there, so the
   local folder <path> is a second copy that falls behind. Without it, each run
   starts from the published version; if 1Password or Confluence can't be
   reached, the run uses the newest copy from an earlier run. Nothing is
   deleted without asking.
2. **Use only the published copy? (asks).** "Keep <path> or use only <target>
   for <products>?"
   - **Use only <target>** (recommended);
   - keep the folder (they edit it by hand, or others use it): leave the
     config as it is and go to the next folder.
3. **Compare (runs by itself).** Download the published collection and
   environments into a new, empty `<workDir>/api-runs/<YYYY-MM-DD>-migration-011/`
   the way `testing-api`'s publishing.md "Downloading the published collection"
   says (1Password asks for approval once), and write `published-base.json`
   there, so the next run has an earlier-run copy to fall back on. Compare with
   the folder: the collection by request names (only in the folder, only
   published, both), the environments by file names and variable names, never
   values. For a git folder also list commits and uncommitted changes
   (`git -C <repo> log --oneline -5`, `git -C <repo> status --porcelain`).
   Show the result.
4. **Something only in the folder? (asks).** If the folder has requests,
   environment files or variables the published copy lacks, show them and ask:
   - publish them first: stop here for this folder; the user runs
     `testing-api` (a run from the folder, then publishing), and this
     migration runs again afterwards;
   - keep the folder (as in step 2);
   - **drop them** only when the user says they are not needed.
   Nothing missing: say the published copy holds everything and go on.
5. **Update the configs (runs by itself).** In each config of the group,
   remove `api.repo` and keep `api.collectionPath` (the collection's path inside
   the published copy; `.` when its files are at the top). Show the diff and run
   the validator.
6. **The folder (asks).** "What should happen to <path>?"
   - **Move it to `<workDir>/archive/<folder>-<YYYY-MM-DD>.zip`, then delete
     it** (recommended: nothing is lost if something turns up later);
   - delete it;
   - leave it where it is (the skills no longer read it).
   Before deleting, check that the zip opens (`unzip -l`).
7. **The project skill (asks).** Search `<projectSkill>` for the folder's path
   and for instructions to edit or commit in it. Show each line with a proposed
   replacement: the collection is downloaded by each run, cases go in through a
   run and are published from there. Apply on the user's yes. Commit in the
   project skill's repo only if the changed files had no other uncommitted
   changes; otherwise leave the commit to the user and say so.
8. **Show the result.** Per folder: configs changed, where the folder went,
   project skill lines changed.

## Verify

- `validate_environments.py` prints ok for every changed config.
- `check_setup.py` lists no missing `api.repo` path for those products.
- Each changed product has an `api-runs/*/published-base.json` (step 3), so a
  run without access to the target has a copy to fall back on.
