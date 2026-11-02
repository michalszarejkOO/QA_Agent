# 011: The local collection folder becomes a local copy of the published one

## What changed

A product whose collection and environments are both published to 1Password or
Confluence no longer needs `api.repo`. Every `testing-api` run, generic ones
too, downloads the published copy into its run folder and works there. The local
folder (often `<workDir>/postman/`) stays, as `api.localCopy`: runs keep it at
the latest published version, writing into it after every publish and whenever
they download a newer version, and start from it when the target can't be read.
It needn't be a git repo any more, and nobody commits in it. Files in it that
aren't part of the collection (upload fixtures a request points at) are left
alone. A collection kept in a git repo the team shares (a Bruno collection
inside the backend repo, say) keeps `repo` as before.

## Is it needed

Needed when a product config in `~/.claude/environments/` (or
`$CLAUDE_CONFIG_DIR/environments/`) has all of:

- an `api.repo`;
- `api.publish.collection` and `api.publish.environments` both `1password` or
  `confluence`;
- an `api.repo` folder that isn't a git repo, or is one with no remote
  (`git -C <repo> remote` prints nothing).

Otherwise not needed. Once applied it isn't asked again, also for folders the
user chose to keep as they are.

## Fresh install

`skip`: configure-project asks where a new product's collection lives and for
its local copy (product-config.md step 5).

## Steps

Group the product configs that point at the same `api.repo` folder (IMS
development, staging and uat often share one) and go through one folder at a
time.

1. **Explain (runs by itself).** Say in short: the collection is published to
   <target>, so each run downloads it from there. The folder <path> stays as
   the local copy of the latest published version: runs update it after every
   publish, and use it when <target> can't be reached. It no longer has to be a
   git repo.
2. **Make it the local copy? (asks).** "Use <path> as the local copy of
   <target> for <products>?"
   - **Yes, local copy** (recommended);
   - keep it as a repo (others edit it, or it should become a shared repo):
     leave the config as it is and go to the next folder.
3. **Compare (runs by itself).** Download the published collection and
   environments into a new, empty `<workDir>/api-runs/<YYYY-MM-DD>-migration-011/`
   the way `testing-api`'s publishing.md "Downloading the published collection"
   says (1Password asks for approval once). Compare with the folder: the
   collection files byte for byte, then by request names (only in the folder,
   only published, both); the environments by file names, variable names and
   which values differ, by name only, never values. List files in the folder
   that the published copy doesn't hold (fixtures, extra collections). Show the
   result.
   - **Identical:** write `<path>/.published.json` (publishing.md, "The local
     copy": versions, `updatedAt`, a SHA-256 per collection and environment
     file).
   - **Different:** don't write it. Say that the first run will show the same
     differences and ask which version to start from; publishing that run then
     brings both in line.
   - **Nothing published yet** (the items don't exist): don't write it either.
     The folder is the base for the first run, whose publish creates the items.
4. **Update the configs (runs by itself).** In each config of the group, rename
   `api.repo` to `api.localCopy` (same path) and keep `api.collectionPath`.
   Show the diff and run the validator.
5. **The git history (asks, only when the folder is a git repo).** "<path> is a
   git repo with <N> commits and no remote. Nobody commits there any more.
   Remove the git history?"
   - **Zip `.git` into `<workDir>/archive/<folder>-git-<YYYY-MM-DD>.zip`, then
     remove it** (recommended); check the zip opens (`unzip -l`) before
     removing, and remove `.gitignore` with it (it's in the zip's history). The
     collection files stay;
   - keep it (harmless; the skills don't commit there).
   Uncommitted changes in it: show them first, and say they stay in the files.
6. **The project skill (asks).** Search `<projectSkill>` for the folder's path
   and for instructions to edit or commit in it. Show each line with a proposed
   replacement: each run downloads the published collection, new cases go in
   through a run and its publish, and the folder is the local copy runs keep
   up to date (edit it by hand only for files outside the collection). Apply on
   the user's yes. Commit in the project skill's repo only if the changed files
   had no other uncommitted changes; otherwise leave the commit to the user and
   say so.
7. **Show the result.** Per folder: configs changed, whether `.published.json`
   was written (or why not), what happened to `.git`, project skill lines
   changed.

## Verify

- `validate_environments.py` prints ok for every changed config.
- The changed configs have `api.localCopy` and no `api.repo`, and the folder
  exists.
- `check_setup.py` reports no missing paths for those products.
