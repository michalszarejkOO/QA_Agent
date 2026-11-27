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

## The release note

Every publish carries a release note: what this version changes compared with
the version it replaces. Each collection gets its own note in its description,
with only its own changes, so a teammate sees them in Postman or Bruno after
the import:

- **The main collection's note**: `Version`, `Updated`, `Collection changes`
  and `Environment changes`.
- **The tests collection's note** (with a `testsCollection`): `Version`,
  `Updated` and `Tests collection changes`.
- **The 1Password item's notes**
  ([onepassword-publish.md](./onepassword-publish.md)) and the step 4 summary:
  the full note, all sections in the order below.

Built in step 3, shown in step 4, written into the staged package before
step 5.

```
Version: <N>
Updated: <YYYY-MM-DD HH:MM>

Collection changes:
ADDED:
<Folder>:
- <METHOD> <path> (<request name>)
- <METHOD> <path> (<request name>)
REMOVED:
<Folder>:
- <METHOD> <path> (<request name>)
CHANGED:
<Folder>:
- <METHOD> <path> (<request name>)

Environment changes:
ADDED:
<ENV>:
- <variable>
- <variable>
<ENV>:
- new environment
REMOVED:
<ENV>:
- <variable>
CHANGED VALUES:
<ENV>:
- <variable>
```

With a tests collection, a `Tests collection changes:` section goes between
the two in the full note (see "Tests collection changes" below). The tests
collection's own note is that section alone under the same header:

```
Version: <N>
Updated: <YYYY-MM-DD HH:MM>

Tests collection changes:
<Folder>:
- <METHOD> <path> (<subfolder name>)
```

Example:

```
Version: 13
Updated: 2026-11-16 12:00

Collection changes:
ADDED:
Certificate:
- POST /v1/assessments/{assessmentId}/submit (certificate after the audit is completed)
- GET /v1/storage/{attachmentId}/download-url (certificate)
QIWA:
- GET /v1/establishments/{establishmentId} (Get establishment)
REMOVED:
Auth:
- POST /v1/auth/login-old (Old login)
CHANGED:
Auth:
- POST /v1/auth/login (Login)

Environment changes:
ADDED:
STAGE:
- old_token
- ip265
DEMO:
- new environment
REMOVED:
STAGE:
- legacy_key
CHANGED VALUES:
UAT:
- qiwa_api_key
```

**One item per line, always.** Under each heading, the folder (or environment)
name sits alone on its line ending with `:`, and every request or variable
gets its own line below it, starting with `- `. Never put two items on one
line, never join them with commas or spaces, even when there are only two:

```
Certificate:
- POST /v1/assessments/{assessmentId}/submit (certificate after the audit is completed)
- GET /v1/storage/{attachmentId}/download-url (certificate)
```

not

```
Certificate: POST /v1/assessments/{assessmentId}/submit (certificate after the audit is completed) GET /v1/storage/{attachmentId}/download-url (certificate)
```

Before writing the note anywhere, check it: no line under a folder or
environment holds more than one item.

- **Version** is the version this publish creates: the target's current
  version + 1 (the 1Password item's `version`, the Confluence attachment's
  `version.number`, `.published.json`'s `version` for `local`), 1 for a first
  upload. If step 5 finds the version moved, rebuild the note.
- **Updated** is local time, when the note is built.
- **The base** is what this upload replaces: `<run folder>/published-newer/`
  when step 3 downloaded it, otherwise `<run folder>/published-collection/`.
  Compare it with the folder this run exports from.
- **Collection changes.** A request is identified by its folder and name.
  ADDED: only in this export. REMOVED: only in the base. CHANGED: in both, but
  its method, URL, headers, body, auth or scripts differ (ignore ids such as
  `_postman_id`, `uid`, `seq`, and the collection's own description). Group
  by top-level folder: `<Folder>:` on its own line, then one line per request,
  `- <METHOD> <path> (<request name>)`, the path as the request has it with
  the base URL variable left out. A request outside any folder goes under
  `Root:`, one in a subfolder is written `- <METHOD> <path> (<Subfolder> /
  <request name>)` under its top-level folder.
  When a whole subfolder is new (or a whole subfolder was removed), write one
  line with the subfolder's name instead of its requests, `- <Subfolder>
  (whole folder)` under ADDED or REMOVED; only the outermost new or removed
  subfolder gets a line, nothing inside it. Requests added to or removed from
  a subfolder that already existed are still listed one by one.
- **Tests collection changes.** With a tests collection (`testsCollection`),
  add a `Tests collection changes:` section after `Collection changes`. It
  only says where tests changed, never which tests: `<Folder>:` on its own
  line, then one line per endpoint (the subfolder that holds that endpoint's
  tests) in which any test request was added, changed or removed, written
  `- <METHOD> <path> (<subfolder name>)`, or `- <subfolder name>` when the
  name holds no method and path. No single test requests, no counts, no
  ADDED / REMOVED / CHANGED headings. A test request directly in a top-level
  folder puts the folder itself on the list, as `- <Folder>`. Nothing
  changed: `Tests collection changes: none`. This section is the tests
  collection's own note (with `Version` and `Updated`) and part of the full
  note; it never goes into the main collection's description. Example, for a
  new `Certificate` folder with 156 test requests in two endpoint subfolders:

  ```
  Tests collection changes:
  Certificate:
  - POST /v1/assessments/{assessmentId}/submit (certificate after the audit is completed)
  - GET /v1/storage/{attachmentId}/download-url (certificate)
  ```
- **Environment changes.** `<ENV>` is the environment's name in capitals
  (`STAGE`, `UAT`), on its own line, with one `- <variable>` line per
  variable under it. ADDED: variables only in this export, or `- new
  environment` for a whole new file. REMOVED: variables only in the base, or
  `- environment removed`. CHANGED VALUES: variables in both whose value
  differs. Compare values in a script and **print only the variable names,
  never a value**, in the note or in the chat.
- Leave out a heading with nothing under it (no `REMOVED:` when nothing was
  removed). A section with no changes at all reads `Collection changes: none`
  or `Environment changes: none`.
- **First upload**: no base, so both sections are replaced by one line,
  `First upload`.
- **A production environment** in the package (publishing step 4) adds
  `PRODUCTION: <file>` after `Updated:`.

**Into each collection's description.** Each collection's own note sits at
the top of its description: a `RELEASE NOTE` line, then the note in a code
block so it keeps its lines:

````
RELEASE NOTE
```
<the release note>
```
````

On every publish, replace that block (the `RELEASE NOTE` line and the code
block right after it) at the top of the description; keep everything else in
the description as it was (with no description, the block is all of it). A
description published before this format has the note between
`<!-- qa-agent:release-note -->` and `<!-- /qa-agent:release-note -->`:
replace that whole part, markers included, the same way.

Where it goes:

| Client | Description |
| --- | --- |
| `postman` | `info.description` of each collection file: the main note in the main collection, the tests note in the tests collection (a string, or the `content` of a `{content, type}` object) |
| `bruno` | The `docs { ... }` block of `collection.bru` (add the block if missing) |
| `insomnia` | The `description` of the workspace resource in the export file |

Change only the staged copies, never the repo: take the collection files out
of the package zip into a scratch folder, edit them, and `zip` them back under
the same paths (Insomnia: edit the file in `.publish/`). The repo's collections
never hold the note, so when comparing (step 3) ignore each collection's
description.

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
   For environments, compare the file names, which variables each defines and
   whether a value changed, never printing the values.
   From this comparison build the release note ("The release note" above) and
   write it into the staged package.
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

   Release note (1Password notes; each collection's description gets its own part):
   <the full release note>
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
8. **Update the app on this machine** (Postman and Bruno; Insomnia: skip).
   Only after a publish that went through (step 6 confirmed it; with `local`,
   once step 7 wrote the folder). The `updateLocalApp` preference
   ([preferences.md](../../configure-project/references/preferences.md))
   decides: `never` (shown to the user as **manual**, the default) leaves the
   import to the user, `auto` does it without asking, `ask` asks with the usual
   four options. Names never change, so the user's app always gets the same
   collection and environments back, never a copy.
   - **Postman, `auto` or yes.** Start the `postman-sync` agent again in **push
     mode**: the brief names the folder the package was built from
     (`<run root>/<collectionPath>`), and, from its step 1 report, the workspace
     and, per collection and environment file, the matched cloud uid and the
     `updatedAt` it saw. It replaces each one through the Postman API
     (`scripts/postman-push.py`), and the app shows the new version within
     seconds, as after Import > Replace. Header values Postman saved as numbers
     (e.g. `:status` in a saved response) are sent as text, since the API
     rejects them otherwise; the files themselves stay unchanged. **Safety stop, also with `auto`:** a collection or
     environment changed in Postman since step 1 (exit code 3) is not replaced;
     report it and ask, since someone edited it in the app after the check. A
     cloud copy step 1 didn't match (new environment, no match) is not created:
     name it for the user to import. If the workspace is shared with a team,
     the replacement reaches everyone in it; it carries exactly what was just
     published.
   - **Bruno, `auto` or yes.** Bruno reads a collection straight from its
     folder and reloads it when the files change, so nothing is imported. With
     `apiCollectionsFolder` (step 7 just wrote it) the app is already current;
     say once: "Bruno: open `<apiCollectionsFolder>/<collectionPath>` with Open
     Collection; after every publish it reloads by itself". Hand edits made in
     that folder are kept as "The API collections folder" step 2 says. Target
     `1password` (no folder): there is nothing on disk to update; say that
     `auto` needs a local copy and suggest the target `1password+local`.
   - **Manual (`never`, or no).** One line in the report: Postman: import the
     zip's files and choose **Replace** for the collection and each
     environment; Bruno: open `<apiCollectionsFolder>/<collectionPath>`, or
     import the zip when there is no folder.
   - Report it: "Postman updated: <collection>, <n> environments" or "not
     updated: <reason>". A subagent run doesn't do this step: it returns
     "update the app" with the push brief, and the main conversation does it
     once the publish is confirmed.

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
