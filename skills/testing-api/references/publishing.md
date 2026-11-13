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
| `apiCollectionsFolder` | This file, "The API collections folder" below |

**Nothing is uploaded anywhere before the user says yes in step 4, or the
`publishCollection` preference is `auto` and step 4 found nothing to warn about.**
Writing to `apiCollectionsFolder` needs no question.

## The four targets

The product config's `api.publish` block names one target:

```json
"publish": {
  "target": "1password | local | 1password+local | confluence",
  "onePassword": { "vault": "<vault name>", "item": "<Product> <Client> Collection" },
  "apiCollectionsFolder": "<workDir>/postman"
}
```

| `target` | What goes where | Needs |
| --- | --- | --- |
| `1password` | The **package** to one 1Password item | `onePassword` |
| `local` | The package to `apiCollectionsFolder` only | `apiCollectionsFolder` |
| `1password+local` | The package to the 1Password item, and the same package to `apiCollectionsFolder` once it is published | both |
| `confluence` | The collection **without environments** to the Confluence page; the package to `apiCollectionsFolder` | `api.confluence`, `apiCollectionsFolder` |

**The package** is everything a teammate needs to import the collection at once:
`<collectionPath>/` with the main collection, the tests collection
(`testsCollection`, see [config-fields.md](./config-fields.md), "The tests
collection") when the product has one, and `environments/` with one file per
environment plus every `extraEnvironmentFiles` file. Never `.env` files or `.git`.

| Client | Package file |
| --- | --- |
| `postman` | One zip, `<product>-postman-collection.zip` |
| `bruno` | One zip, `<product>-bruno-collection.zip` (export part `full`) |
| `insomnia` | The export file (it holds its environments) |

Environments hold tokens and logins, so the package only goes where it stays
private: a 1Password vault shared with the team, or a folder on this machine.
**Environments never go to Confluence.** A file named `*-populated*` elsewhere
in the collection is kept (a request may carry that word), but
`export-collection.sh` names it on stderr; check it.

There is one package per product, wherever it is kept; nothing else stays in the
run folder once an upload succeeded (see "Staging" below).

**`publish.extraEnvironmentFiles` and `publish.envRefreshProcedure`**
(optional, any target). `extraEnvironmentFiles` is a list of
`{ "name": "<fixed filename>", "sourcePath": "<path relative to repo root>" }`:
environment files kept outside `environments/`, e.g. a live-populated one.
`sourcePath` is read from the folder this run used as the repo root (the worktree
in generic mode, `<run folder>/published-collection/` in ticket mode and in any
run without `repo`). They always travel inside the package as
`<collectionPath>/environments/<name>`, never to Confluence.
`envRefreshProcedure` is the filename of a product-specific doc, kept next to the
product's config in `<workDir>/config/` (found as SKILL.md step 0 says),
describing how to mint live values into such a file: load it and follow it
verbatim, in full, before building the package. Most products need neither.

**An old config** (`publish` with `collection` / `environments` / `tests`
instead of `target`, `api.localCopy` or `publish.localFolder`, or no `publish`
block at all): don't guess. Say that "update QA_Agent" moves it to the new shape
(migration 016), keep the export in the run folder as the file to import, and
skip publishing.

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

- the package, under the name in the table above:
  `export-collection.sh <root> "<run folder>/.publish/<product>-<client>-collection.zip" <collectionPath> <client> full`
  (Postman and Bruno; it holds the main and the tests collection and
  `environments/`), then `zip` each `extraEnvironmentFiles` file into it under
  `<collectionPath>/environments/<name>` (copy it to that name in a scratch
  folder first). Insomnia: copy the export file into `.publish/`;
- for `confluence` only, the collection zip without environments:
  `<run folder>/.publish/<api.confluence.attachmentName>`, part `collection`.

After the targets are written (step 5), delete `.publish/`. If nothing was
uploaded (the user said no, a target couldn't be reached), the package isn't
lost: with `local` or `confluence` it is in `apiCollectionsFolder` anyway; otherwise move it to the run folder,
give its path as the file to import, and keep it.

## The API collections folder

`api.publish.apiCollectionsFolder` (with `local`, `1password+local` and
`confluence`) is a folder on this machine, usually `<workDir>/postman/` or
`<workDir>/<client>/`, that always holds the last **published** package,
extracted: `<collectionPath>/` with the collections and `environments/`, the way
the package zip holds them, plus `.published.json` (the target, ids, `version`,
`updatedAt`, and `files`, a SHA-256 per file it wrote, paths relative to the
folder). With `local` and `confluence` it is where the environments are
published; without `repo` it is also where a run starts when the target can't
be read. It needs no question, and the `publishCollection` preference doesn't
apply to it.

1. Expand `~`, create the folder if it's missing (`mkdir -p`). It holds live
   values, so it must not be inside the QA_Agent repo, and if it is inside
   another git work tree (`git -C <folder> rev-parse --is-inside-work-tree`
   succeeds), `git -C <folder> check-ignore -q .` must succeed; otherwise don't
   write: say so and suggest `<workDir>/<client>/`.
2. **Hand edits are kept.** Before overwriting a file, check it against its
   checksum in `.published.json`: one that changed there since (someone edited
   the folder by hand) is not overwritten. Name it and ask whether to use the
   local edit as this run's base or drop it; in a subagent, report it with the
   question. Without `.published.json`, compare the files with what you're about
   to write instead: identical ones only get their checksums recorded, different
   ones go to the same question.
3. Write the package's files (extracted from the package zip, or the Insomnia
   file), remove a file there that `.published.json` lists and the package no
   longer has, and rewrite `.published.json` with the new version and
   checksums. Only files listed in `.published.json` are ever written or
   removed; anything else in the folder (upload fixtures a request points at,
   say) stays as it is.

When it's written:

- **After publishing** (step 7).
- **After a download** at the start of a run (`1password+local`): if the
  downloaded version is higher than `.published.json` says, or
  `.published.json` is missing, refresh the folder from `published-collection/`
  the same way.
- Never print values from its environment files, and never put it inside a git
  repo with a remote.

## Procedure

1. **Postman: sync with the app first.** For `client: "postman"`, the files
   must hold what the team has in Postman (see
   [adapters/postman.md](./adapters/postman.md), "Syncing with the Postman app
   before publishing"). The `postman-sync` agent does it:
   1. Run `op vault list >/dev/null` once and tell the user to approve the
      1Password request if one opens. The agent's connection reads the key from
      1Password and gets only 10 seconds, too short to wait for an approval.
   2. Start the `postman-sync` agent (Agent tool, `subagent_type:
      "postman-sync"`) with the product, its config file, the collection folder
      (`<run root>/<collectionPath>`), for a product without `repo` also
      `<run folder>/published-base.json`, and the workspace the project skill
      names.
   3. Its questions go to the user; continue the same agent with the answers.
   4. Show the user its report: the warning first if there is one, then its
      Shared Value check with the reminder **word for word, every time**, even
      when every variable has its value. Nothing in step 4 is asked before the
      user has seen it.
   5. "Postman not connected": show its fix, then follow postman.md's
      "without it".
   **Build what the target needs** in `.publish/`, as "Staging" says. If an
   `envRefreshProcedure` is configured, follow it first.
2. **Scan** the Confluence zip, as above (`confluence` only).
3. **Read what's published now, and compare.** Get the published version (the
   target's file says how; for `local`, `.published.json` in
   `apiCollectionsFolder`) and compare it with the version this run started from:
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
   - API collections folder: <apiCollectionsFolder> (written without asking; with 1password+local after the upload)   (when the target has one)
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
   summary. With `local` and `confluence`, `apiCollectionsFolder` is written either
way (step 7).
   A `local` target has nothing to ask: show only the local line and go on.
5. **Write** each shared target (1Password, Confluence) per its file. Right before each upload, read the published version once more;
   if it changed since step 3, someone published in between, so stop and ask
   again. Then delete `.publish/` (see "Staging" for what stays when nothing was
   uploaded).
6. **Verify and report**, per the target's file: the new version is there, and
   where to find it (link, vault/item, local path).
7. **Update `apiCollectionsFolder`** (`local`, `1password+local`,
   `confluence`), as "The API collections folder" says, and name it in the
   report ("API collections folder updated: <path>, version <N>"). With
   `1password+local`, only once step 6 confirmed the new version in 1Password:
   a package that wasn't published (no yes, upload failed) leaves the folder as
   it was. With `local` and `confluence`, the folder is written in any case.

## Downloading the published collection (ticket mode)

Ticket mode starts from the published collection, not the repo checkout (see
[ticket-driven-testing.md](./ticket-driven-testing.md), Step 2). It always lands in
the same place in the run folder:

| Path | What |
| --- | --- |
| `<run folder>/published-base.zip` | The downloaded zip, as it is published (Postman/Insomnia files are downloaded straight into `published-collection/`) |
| `<run folder>/published-collection/` | That zip extracted. It holds `<collectionPath>/` the way the repo does, so it is used as the repo root: generating cases, running the suite and exporting all work from here |
| `<run folder>/published-base.json` | What was downloaded: `target`, the target's ids (`pageId` + `attachmentId`, or `vault` + `item` + `id`, or the local `path`), `version`, `updatedAt` (when that version was published: the item's `updated_at`, the attachment's version date, or `.published.json`'s date for a local folder), `downloadedAt`. Step 3 compares against it; the Postman sync compares the app with `updatedAt` |

Where it comes from, per target:

- `1password` and `1password+local`: the package from the 1Password item (the
  shared copy is the latest). With `1password+local`, then bring
  `apiCollectionsFolder` up to date from it ("The API collections folder"
  below).
- `local`: the package in `apiCollectionsFolder`.
- `confluence`: the collection zip from the page, then the environments from
  `apiCollectionsFolder` (its `<collectionPath>/environments/`); with nothing
  there yet, from the repo checkout. Say which the run uses.

Extract into `published-collection/`, which must be new and empty
(`unzip -q <zip> -d <folder>`; an Insomnia file goes to
`published-collection/<collectionPath>/`), check that `<collectionPath>` is
there, and write `published-base.json`. A package from before the one-zip layout
(a Bruno zip without `environments/`, loose Postman files): take what it has,
copy missing environments from `apiCollectionsFolder` or the repo checkout, and
say so. A product without `repo` downloads this way on every run, generic ones
too. When the download isn't
possible, say so and use the repo checkout, as ticket-driven-testing.md Step 2
describes.

### When the download isn't possible

With `repo`, use the repo checkout (above). **Without `repo`**, use
`apiCollectionsFolder`: copy its `<collectionPath>/` (the collection files and
`environments/`, not `.published.json`) into this run's new, empty
`published-collection/<collectionPath>/`, and write `published-base.json` from
its `.published.json` with `"source": "apiCollectionsFolder"`. Say in the run's
first lines and in the report's Notes that the run starts from the local folder
(version <N>, from <date>), that someone may have published since, and that
publishing this run waits until the target can be read again (step 3 can't
check it). No `apiCollectionsFolder` (target `1password`), or it doesn't hold
the collection: stop and say the collection can't be reached.

**Nothing published yet** (the item or attachment doesn't exist, but the target
can be read) is not a failed download: start from `apiCollectionsFolder` the
same way, with no version in `published-base.json`, and this run's publish is
the first upload.
