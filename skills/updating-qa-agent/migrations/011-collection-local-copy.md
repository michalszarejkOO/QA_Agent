# 011: The local collection folder becomes a local copy of the published one

## What changed

A product whose collection and environments are both published to 1Password or
Confluence no longer needs `api.repo`. Every `testing-api` run, generic ones
too, downloads the published copy into its run folder and works there. The local
folder (often `<workDir>/postman/`) stays, as `api.localCopy`: runs keep it at
the latest published version, writing into it after every publish and whenever
they download a newer version, and start from it when the target can't be read.
It needn't be a git repo, and nobody commits in it (a `.git` someone
added by hand can stay; nothing uses it). Files in it that
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

Nothing is downloaded or compared here: the first `testing-api` run does that
when the folder has no `.published.json` yet (publishing.md, "The local copy").

1. **Explain and ask once (asks).** List every folder that needs it, with the
   products whose configs point at it (IMS development, staging and uat often
   share one). Say in short: each run downloads the collection from <target>;
   the folder stays as the local copy of the latest published version, updated
   after every publish and used when <target> can't be reached; it needn't be a
   git repo. Ask one question for all of them: "Make these folders local
   copies?"
   - **Yes, all** (recommended);
   - choose per folder (then one short yes/no per folder; a "no" leaves its
     configs as they are).
2. **Update the configs (runs by itself).** In each config of the chosen
   folders, rename `api.repo` to `api.localCopy` (same path), keep
   `api.collectionPath`, show the diff and run the validator.
3. **The project skill (asks only if something is found).** Search each
   affected `<projectSkill>` for instructions to commit in the folder or to
   edit its collection files by hand. None: say so and go on. Found: show each
   line with a replacement (new cases go in through a `testing-api` run and its
   publish, which also updates the folder) and apply on a yes. Commit in the
   project skill's repo only if the changed files had no other uncommitted
   changes; otherwise leave the commit to the user and say so.
4. **Show the result.** Configs changed, project skill lines changed, and that
   the first run per product will record the folder's version (or ask, if it
   differs from <target>).

## Verify

- `validate_environments.py` prints ok for every changed config.
- The changed configs have `api.localCopy` and no `api.repo`, and the folder
  exists.
- `check_setup.py` reports no missing paths for those products.
