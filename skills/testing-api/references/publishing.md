# Publishing the collection

Load this for the last step of a run (SKILL.md step 8), and at the start of a
ticket-mode run to download the published collection. It decides **what** is
exported and **where** it goes, **checks** that nobody published a newer version
in the meantime, and **asks** before anything leaves the machine. The mechanics of
each shared place are in its own file:

| Target | File |
| --- | --- |
| 1Password | [onepassword-publish.md](./onepassword-publish.md) |
| Confluence | [confluence-publish.md](./confluence-publish.md) |
| Local folder | This file, "Local folder" below |

**Nothing is uploaded anywhere before the user says yes in step 4, or the
`publishCollection` preference is `auto` and step 4 found nothing to warn about.**
Writing to the local folder needs no question.

## The four targets

The product config's `api.publish` block names one target:

```json
"publish": {
  "target": "1password | local | 1password+local | confluence",
  "onePassword": { "vault": "<vault name>", "item": "<Product> <Client> Collection" },
  "localFolder": "~/Documents/QA/<product>/collection"
}
```

| `target` | What goes where | Needs |
| --- | --- | --- |
| `1password` | The **package** to one 1Password item | `onePassword` |
| `local` | The package to `localFolder` | `localFolder` |
| `1password+local` | The package to the 1Password item and to `localFolder` | both |
| `confluence` | The collection **without environments** to the Confluence page; the package to `localFolder` | `api.confluence`, `localFolder` |

**The package** is the collection together with its environments, in the form
the desktop app imports at once:

| Client | Package |
| --- | --- |
| `bruno` | One zip, `<product>-bruno-collection.zip` (export part `full`): the collection folder with `environments/`, plus every `extraEnvironmentFiles` file added as `<collectionPath>/environments/<name>`. Never `.env` files or `.git` |
| `postman` | The `*.postman_collection.json` and each `environments/*.postman_environment.json`, plus every `extraEnvironmentFiles` file, as plain files |
| `insomnia` | The export file (it holds its environments) |

Environments hold tokens and logins, so the package only goes where it stays
private: a 1Password vault shared with the team, or a folder on this machine.
**Environments never go to Confluence.**

There is one file to import per product, wherever it is kept; no other copies are
made. In particular nothing stays in the run folder: files staged there for an
upload are deleted once it succeeded (see "Staging" below).

**`publish.extraEnvironmentFiles` and `publish.envRefreshProcedure`**
(optional, any target). `extraEnvironmentFiles` is a list of
`{ "name": "<fixed filename>", "sourcePath": "<path relative to repo root>" }`:
environment files kept outside `environments/`, e.g. a live-populated one.
`sourcePath` is read from the folder this run used as the repo root (the worktree
in generic mode, `<run folder>/published-collection/` in ticket mode). They always
travel inside the package as `<collectionPath>/environments/<name>`, never to
Confluence. `envRefreshProcedure` is the filename of a product-specific doc, kept
next to the product's config in `<workDir>/config/` (found as SKILL.md step 0
says), describing how to mint live values into such a file: load it and follow it
verbatim, in full, before building the package. Most products need neither.

**An old config** (`publish` with `collection` / `environments` instead of
`target`, or no `publish` block at all): don't guess. Say that "update QA_Agent"
moves it to the new shape (migration 010), keep the export as the file to import
in the run folder, and skip publishing.

## Secrets never go where others can read them

1Password keeps what it holds encrypted and shared only with the vault's members.
A Confluence page is readable by everyone with access to the space, often the
client too. So:

- Before the collection goes to **Confluence**, run
  `python3 -I <this skill>/scripts/scan_secrets.py <zip>`. Exit 1 means it
  found possible secrets: stop, show its list (file, line or request, the field
  name; it never prints values), and don't upload unless the user, having seen the
  list, says it's safe. Suggest replacing the literal value with a `{{variable}}`
  set in the environments.
- Before anything goes to **1Password** or the **local folder**, the scan is not
  needed: the package is expected to hold secrets there.
- Never print a secret's value in the chat, a report or a page, and never stage a
  file with live values inside the QA_Agent repo or the product repo.
- An `extraEnvironmentFiles` file that `envRefreshProcedure` fills with live values
  sits at `sourcePath` under the run's repo root. When that root is the product
  repo or its worktree, check it before using it:
  `git -C <repo> check-ignore -q <sourcePath>`. If git would pick it up (not
  ignored, or already tracked: `git -C <repo> ls-files --error-unmatch
  <sourcePath>`), stop and tell the user to gitignore it first. Don't edit the
  product repo's `.gitignore` yourself.

## Staging

Everything is built in `<run folder>/.publish/` (create it new and empty), from
the folder the run used as the repo root (the worktree in generic mode,
`<run folder>/published-collection/` in ticket mode), with
`export-collection.sh` (see the adapter):

- the package, under the name in the table above (Bruno:
  `export-collection.sh <root> "<run folder>/.publish/<product>-bruno-collection.zip" <collectionPath> bruno full`,
  then `zip` each `extraEnvironmentFiles` file into it under
  `<collectionPath>/environments/<name>`; Postman: copy the files flat into
  `.publish/`);
- for `confluence` only, the collection zip without environments:
  `<run folder>/.publish/<api.confluence.attachmentName>`, part `collection`.

After the targets are written (step 5), delete `.publish/`. If nothing was
uploaded (the user said no, a target couldn't be reached), the package isn't
lost: with a local folder it is there anyway; otherwise move it to the run folder,
give its path as the file to import, and keep it.

## Local folder

When the target includes `localFolder` (`local`, `1password+local`,
`confluence`), every run that exports the collection ends by writing the package
there, whatever the test results. It never leaves the machine, so it needs no
question and no version check, and the `publishCollection` preference doesn't
apply; say in the run summary what was written where.

1. Expand `~`, create the folder if it's missing (`mkdir -p`). If it is inside a
   git work tree (`git -C <folder> rev-parse --is-inside-work-tree` succeeds)
   and `git -C <folder> check-ignore -q .` fails, don't write: the files hold live
   values. Say so and suggest a folder outside the repo, e.g.
   `<workDir>/collection`.
2. Move the package from `.publish/` into the folder, replacing what is there, so
   the folder always holds one current version (Postman: remove an environment
   file there that the package no longer has).
3. Before replacing a file whose content differs, keep the old one as
   `<name>.prev` (one level, the older `.prev` is replaced). Never delete
   anything else in the folder.

## Procedure

1. **Postman: sync with the app first.** For `client: "postman"`, follow
   [adapters/postman.md](./adapters/postman.md), "Syncing with the Postman app
   before publishing", so the files hold what the team has in Postman. Before the
   summary in step 4, also show which environment variables have a value and which
   don't (names only).
   **Build what the target needs** in `.publish/`, as "Staging" says.
2. **Scan** the Confluence zip, as above (`confluence` only).
3. **Read what's published now, and compare** (1Password and Confluence; a local
   folder has no versions to check). Get the published version (the target's file
   says how) and compare it with the version this run started from:
   - `<run folder>/published-base.json` exists (ticket mode downloaded the
     collection at the start): the same version means nobody has published since.
     A higher one means someone did: download it into a new, empty
     `<run folder>/published-newer/` and compare it with what this run exports
     (`<run folder>/published-collection/`).
   - No `published-base.json` (generic mode, or the download failed): download the
     published one now, into a new, empty `<run folder>/published-newer/`, and
     compare it with the folder you exported from. A generic run exports
     `origin/<branch>` without uncommitted changes, so the published one may well
     hold more. Also run `git -C <repo> status --porcelain -- <collectionPath>`; if
     it lists changes, say they aren't in the export.
   - Nothing published yet: this is the first upload.
   - The target can't be reached (no Atlassian server for the site, `op` not signed
     in): say you couldn't check, and ask anyway with that warning.

   **How to compare.** `diff -rq` the two extracted folders, ignoring `.DS_Store`,
   for a collection kept as one file per request (Bruno). For one kept in one JSON
   file (Postman, Insomnia), compare the request names in each, e.g. with a short
   `python3 -I` script that walks the `item` tree. Report it as: only in the
   published one (publishing drops these), only in this export, changed in both.
   For environments, compare only the file names and which variables each defines,
   never the values.
4. **Show the summary and ask.** Put any warning first (a newer version, scan
   findings, uncommitted changes, a production environment), then:
   ```
   Publish?
   - Package (collection + environments) → <1Password: <vault> / <item> | nowhere shared>
     <file(s)>, <size>, exported from <folder> (<branch> @ <commit>)
     replaces version <N> | first upload
   - Collection without environments → Confluence: <pageTitle> (<link>)   (confluence only)
     <zip>, <size>; secret scan: <clean | findings above>
     replaces version <N> | first upload
   - lastUpdate (Confluence only): <date>, commit <commit> on <branch>
   - Local folder: <localFolder> (written without asking)   (when the target has one)
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
   publish.
   **Whether to ask** comes from the `publishCollection` preference
   ([preferences.md](../../configure-project/references/preferences.md)):
   `auto` shows the summary and goes on to step 5 without a question, but only
   when there's no warning (no newer or different published version, no secret
   scan finding, no production environment, no uncommitted changes left out);
   any warning asks as below. `never`: show the summary, upload nothing. `ask`
   (the default): ask, with the "always"/"never" options that are saved. **Only a
   clear yes, or `auto` with no warning, goes on.** Anything else: upload nothing,
   and list "<target> not updated (user didn't approve)" under Not done in the run
   summary. The local folder is written either way (step 5).
   A `local` target has nothing to ask: show only the local line and go on.
5. **Write.** The local folder first (it needs no yes), then each shared target
   per its file. Right before each upload, read the published version once more;
   if it changed since step 3, someone published in between, so stop and ask
   again. Then delete `.publish/` (see "Staging" for what stays when nothing was
   uploaded).
6. **Verify and report**, per the target's file: the new version is there, and
   where to find it (link, vault/item, local path).

## Downloading the published collection (ticket mode)

Ticket mode starts from the published collection, not the repo checkout (see
[ticket-driven-testing.md](./ticket-driven-testing.md), Step 2). It always lands in
the same place in the run folder:

| Path | What |
| --- | --- |
| `<run folder>/published-base.zip` | The downloaded zip, as it is published (Postman/Insomnia files are downloaded straight into `published-collection/`) |
| `<run folder>/published-collection/` | That zip extracted. It holds `<collectionPath>/` the way the repo does, so it is used as the repo root: generating cases, running the suite and exporting all work from here |
| `<run folder>/published-base.json` | What was downloaded: `target`, the target's ids (`pageId` + `attachmentId`, or `vault` + `item` + `id`, or the local `path`), `version` (or the file's modification time for a local folder), `downloadedAt`. Step 3 compares against it |

Where it comes from, per target:

- `1password` and `1password+local`: the package from the 1Password item (the
  shared copy is the latest). With `1password+local`, also compare it with the
  package in `localFolder` and say if they differ.
- `local`: the package in `localFolder`.
- `confluence`: the collection zip from the page, then the environments from the
  package in `localFolder` (its `<collectionPath>/environments/`); with no package
  there yet, from the repo checkout. Say which the run uses.

Extract into `published-collection/`, which must be new and empty
(`unzip -q <zip> -d <folder>`; Postman/Insomnia files go to
`published-collection/<collectionPath>/`), check that `<collectionPath>` is there,
and write `published-base.json`. A package published before environments were
included (a zip without `environments/`): copy the environments from the repo
checkout and say so. When nothing is published yet, or the download isn't
possible, say so and use the repo checkout, as ticket-driven-testing.md Step 2
describes.
