# Publishing the collection and its environments

Load this for the last step of a run (SKILL.md step 8), and at the start of a
ticket-mode run to download the published collection. It decides **where** each
part goes, **checks** that nobody published a newer version in the meantime, and
**asks** before anything leaves the machine. The mechanics of each place are in
its own file:

| Target | File |
| --- | --- |
| `1password` | [onepassword-publish.md](./onepassword-publish.md) |
| `confluence` | [confluence-publish.md](./confluence-publish.md) |
| `none` | Nothing is uploaded; the zips stay in the run folder. |

**In every mode, nothing is uploaded anywhere before the user says yes in step 4.**

## Where each part goes

The product config's `api.publish` block names a target per part:

```json
"publish": {
  "collection": "1password",
  "environments": "1password",
  "onePassword": {
    "vault": "<vault name>",
    "collectionItem": "<Product> <Client> Collection",
    "environmentsItem": "<Product> <Client> Environments"
  }
}
```

- **collection**: the collection zip from `export-collection.sh` (part
  `collection`). It never contains `environments/`, `.env` files or `.git`. A
  file named `*-populated*` elsewhere in the collection is kept (a request may
  carry that word) but the script names it on stderr; check it, and the secret
  scan catches live values in it.
- **environments**: the environments zip (part `environments`), plus any
  `api.confluence.secondaryAttachments` files (live-populated environments that an
  `envRefreshProcedure` fills): separate attachments on Confluence, added into the
  environments zip under their `name` for 1Password (`zip -j`, after copying them
  to that name in the run folder). These can hold tokens and logins.
- Each is `1password`, `confluence` or `none`. `onePassword` is required when
  either part is `1password`; `api.confluence` when either is `confluence`. The
  `lastUpdate` panel exists only on Confluence.
- **No `publish` block** (a config from before migration 006): the collection goes
  to Confluence if `api.confluence` exists, otherwise nowhere, and environments go
  nowhere. Mention in the run summary that "update QA_Agent" sets this up.

## Secrets never go where others can read them

1Password keeps what it holds encrypted and shared only with the vault's members.
A Confluence page is readable by everyone with access to the space, often the
client too. So:

- Before anything goes to **Confluence**, run
  `python3 -I <this skill>/scripts/scan_secrets.py <each file>`. Exit 1 means it
  found possible secrets: stop, show its list (file, line or request, the field
  name; it never prints values), and don't upload that file unless the user, having
  seen the list, says it's safe. Suggest moving the environments to 1Password
  (`publish.environments: "1password"`) or replacing the literal value with a
  `{{variable}}`.
- Before anything goes to **1Password**, the scan is not needed: the environments
  are expected to hold secrets there.
- Never print a secret's value in the chat, a report or a page, and never stage a
  file with live values inside the QA_Agent repo or the product repo.
- A `secondaryAttachments` file that `envRefreshProcedure` fills with live values
  sits at `sourcePath` under the run's repo root. When that root is the product
  repo or its worktree, check it before uploading anywhere:
  `git -C <repo> check-ignore -q <sourcePath>`. If git would pick it up (not
  ignored, or already tracked: `git -C <repo> ls-files --error-unmatch
  <sourcePath>`), stop and tell the user to gitignore it first. Don't edit the
  product repo's `.gitignore` yourself.

## Procedure

1. **Postman: sync with the app first.** For `client: "postman"`, follow
   [adapters/postman.md](./adapters/postman.md), "Syncing with the Postman app
   before publishing", so the files hold what the team has in Postman. Before the
   summary in step 4, also show which environment variables have a value and which
   don't (names only).
   **Export the parts that have a target.** Run `export-collection.sh` from the
   folder the run used as the repo root (the worktree in generic mode,
   `<run folder>/published-collection/` in ticket mode), into the run folder:
   - collection: `<run folder>/<collection zip>`, where `<collection zip>` is
     `api.confluence.attachmentName` when the config has one, otherwise
     `<product>-<client>-collection.zip`;
   - environments: `<run folder>/<product>-<client>-environments.zip`, part
     `environments`.

   These names stay the same on every run, so each upload becomes a new version
   of the same file. **Exception, 1Password:** files go up as they are (see
   [onepassword-publish.md](./onepassword-publish.md), "What goes into each
   item"): copy the collection file (Postman, Insomnia) or the collection zip
   (Bruno), and each environment file, into `<run folder>/publish/`; the
   environments zip isn't needed there. Confluence always gets zips.
   If an `envRefreshProcedure` is configured and the environments have a target,
   follow it before exporting (see [confluence-publish.md](./confluence-publish.md),
   "Identifiers"); with `environments: "none"` skip it, nothing would use it.
2. **Scan** whatever goes to Confluence, as above.
3. **Read what's published now, and compare.** For each part with a target, get
   the published version (the target's file says how) and compare it with the
   version this run started from:
   - `<run folder>/published-base.json` exists (ticket mode downloaded the
     collection at the start): the same version means nobody has published since.
     A higher one means someone did: download it into a new, empty
     `<run folder>/published-newer/<part>/` and compare it with what this run
     exports (`<run folder>/published-collection/` for the collection).
   - No `published-base.json` (generic mode, or the download failed): download the
     published part now, into a new, empty `<run folder>/published-newer/<part>/`,
     and compare it with the folder you exported from. A generic run exports
     `origin/<branch>` without uncommitted changes, so the published one may well
     hold more. Also run `git -C <repo> status --porcelain -- <collectionPath>`; if
     it lists changes, say they aren't in the zip.
   - Nothing published yet: this is the first upload.
   - The target can't be reached (no Atlassian server for the site, `op` not signed
     in): say you couldn't check, and ask anyway with that warning.

   For files from 1Password there is nothing to extract (except a Bruno collection
   zip): compare the downloaded files with those in `<run folder>/publish/`.

   **How to compare.** `diff -rq` the two extracted folders, ignoring `.DS_Store`,
   for a collection kept as one file per request (Bruno). For one kept in one JSON
   file (Postman, Insomnia), compare the request names in each, e.g. with a short
   `python3 -I` script that walks the `item` tree. Report it as: only in the
   published one (publishing drops these), only in this export, changed in both.
   When comparing the collection, ignore `environments/` and `.env` files: a
   collection published before environments were split out still holds them, and
   the new zip leaves them out on purpose, not by losing them.
   For environments, compare only the file names and which variables each defines,
   never the values.
4. **Show the summary and ask.** Put any warning first (a newer version, scan
   findings, uncommitted changes, a production environment), then:
   ```
   Publish?
   - Collection → <1Password: <vault> / <collectionItem> | Confluence: <pageTitle> (<link>) | nowhere>
     <local path>, <size>, exported from <folder> (<branch> @ <commit>)
     replaces version <N> | first upload
   - Environments → <target and name, as above>
     <local path>, <size>, <files inside>; secret scan: <clean | n/a (1Password)>
     replaces version <N> | first upload
   - lastUpdate (Confluence only): <date>, commit <commit> on <branch>
   - Check: unchanged since the download (version <N>) | NEWER: version <M> | differs from this export: <summary>
   ```
   **Production environments.** If an environment file's name looks like
   production (`prod`, `prd`, `production`, `live`), say so first, in its own
   line ("this upload includes the production environment <name> with its keys"),
   and ask about it separately: the user can publish it, leave it out of this
   upload, or stop. Never publish it on a yes given only to the rest.
   When a newer or different version is published, offer the choices: publish
   anyway (it replaces that version), stop so the user can merge it locally first
   (in ticket mode: take the newer one as the base and run again), or don't
   publish. **Only a clear yes goes on.** Anything else: upload nothing, give the
   zips' paths, and list "<target> not updated (user didn't approve)" under Not done
   in the run summary.
5. **Upload**, per the target's file. Right before each upload, read the published
   version once more; if it changed since step 3, someone published in between, so
   stop and ask again.
6. **Verify and report**, per the target's file: the new version is there, and
   where to find it (link or vault/item).

## Downloading the published collection (ticket mode)

Ticket mode starts from the published collection, not the repo checkout (see
[ticket-driven-testing.md](./ticket-driven-testing.md), Step 2). It always lands in
the same place in the run folder:

| Path | What |
| --- | --- |
| `<run folder>/published-base.zip` | The collection zip, as it is published (files from 1Password other than a Bruno zip are downloaded straight into `published-collection/`) |
| `<run folder>/published-collection/` | That zip extracted. It holds `<collectionPath>/` the way the repo does, so it is used as the repo root: generating cases, running the suite and exporting all work from here |
| `<run folder>/published-base.json` | What was downloaded, per part (`collection`, and `environments` when they were downloaded too): `target`, the target's ids (`pageId` + `attachmentId`, or `vault` + `item` + `id`), `version`, `downloadedAt`. Step 3 compares against it |

Download from wherever `publish.collection` points (the target's file has the
steps), extract into `published-collection/`, which must be new and empty
(`unzip -q <zip> -d <folder>`), check that `<collectionPath>` is there, and write
`published-base.json`. The collection zip has no environments, so copy the
collection's `environments/` folder into `published-collection/<collectionPath>/`:
from the published environments when `publish.environments` has a target (download
them the same way into `<run folder>/published-environments/` first), otherwise
from the repo checkout. A collection published before environments were split out
already holds `environments/`: keep those unless the published environments are
newer, and say which ones the run uses. With `collection: "none"`, or when the download isn't
possible, say so and use the repo checkout, as ticket-driven-testing.md Step 2
describes.
