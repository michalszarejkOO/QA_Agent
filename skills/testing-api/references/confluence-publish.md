# Updating the collection's Confluence tracker page

Load this when executing the final "publish" step of the procedure, for any product
whose `environments/*.json` config has an `api.confluence` block. Skip entirely if
that block is absent. **In ticket mode always reach this step, whatever the
results** — see [ticket-driven-testing.md](./ticket-driven-testing.md) Step 6.
**In every mode, nothing is written to Confluence before the user says yes in
step 4.**

**Scope, precisely:** this page is a `lastUpdate` tracker plus the exported zip (and
any secondary attachments) as file attachments — never inline collection content. Do
not dump request files, YAML, or any collection content into the page *body*. The
zip from step 3 of SKILL.md (`export-collection.sh`) and anything listed under
`api.confluence.secondaryAttachments` are attached to this same page as binary
attachments (see "Attach the files" below) so the user can download them straight
from Confluence; the page body itself still only records *when* the collection was
last touched, plus one visible file card per attachment.

## Identifiers come from the product's config

Read these from that product's `api.confluence` block in `environments/*.json` —
never hardcode a site/space/page for a specific product in this file:

| Config field | Meaning |
| --- | --- |
| `cloudId` | Confluence site, e.g. `is-takamol.atlassian.net` |
| `spaceKey` | Space key, e.g. `MU` |
| `parentId` | Target folder's page id (the collection's landing folder) |
| `pageTitle` | Fixed page title, so re-runs update instead of duplicating |
| `attachmentName` | Fixed zip filename, so re-runs create a new version instead of duplicating |
| `secondaryAttachments` | (Optional) array of `{ "name": "<fixed filename>", "sourcePath": "<path relative to repo root>" }` — e.g. a live-populated environment file. Each is attached and shown as its own file card, same as the primary zip. `sourcePath` is read from the folder this run used as the repo root: the worktree in generic mode, `<run folder>/confluence-collection/` in ticket mode. |
| `envRefreshProcedure` | (Optional) filename of a product-specific markdown doc, kept next to the product's config in `<workDir>/config/` (found as SKILL.md step 0 says), describing how to mint/refresh live values into a `secondaryAttachments` file before export. Load and follow it verbatim, in full, in step 2 below, when present. Not every product needs this — most `secondaryAttachments` (if any) are static files with no live-minting step. |

## Which server to use

Atlassian's own MCP server for the page's site (`cloudId`), picked from
`atlassian-connectors.json` and confirmed with its `getAccessibleAtlassianResources`.
If the session has no such server for that site, skip publishing, say why, and give
the user the command to add one from `connectors.md`; never fall back to another
Atlassian server such as `mcp-atlassian`: its uploads and page format differ and
fail.
Operation names and how to call them (directly, or through `discover` +
`executeRead`/`executeWrite`) are in the `configure-project` skill's
[references/connectors.md](../../configure-project/references/connectors.md#atlassian-tool-names).
This procedure uses:

| Step | Operation | How |
| --- | --- | --- |
| Find the page | `searchConfluence` | direct |
| Create / update the page | `createConfluenceContent` / `updateConfluenceContent` | direct |
| Read the page (and its `snapshotToken`) | `getConfluenceContent` | direct |
| Upload a file | `createConfluenceAttachment` | through discover, `executeWrite` |
| List the page's files | `listConfluenceAttachments` | through discover, `executeRead` |
| Download a file | `downloadConfluenceAttachment` | through discover, `executeRead` |

## Procedure

Order matters: steps 1–4 only read and prepare, and step 4 asks the user; every
write comes after their yes. Each file card in the page body needs the `fileId` its
upload returned, so every file is uploaded to a known page ID *before* the body
update. On first run (no page yet) this means create the bare page first, then
upload, then update the body.

1. **Find any existing page**, so the run updates in place instead of duplicating:
   `searchConfluence` with
   ```
   space = <spaceKey> AND ancestor = <parentId> AND title = "<pageTitle>" AND type = page
   ```
   - **Found** → note its page ID.
   - **Not found** → note that the page will be new. Don't create it yet; step 5
     does, after the user's yes.

2. **If `envRefreshProcedure` is configured**, load and follow it now, before
   exporting — it mints/refreshes the live values that go into the corresponding
   `secondaryAttachments` file. If the doc names paths in the product repo, apply
   them under the folder this run uses as the repo root (see `secondaryAttachments`
   above).

3. **Export the collection**, per the adapter's export instructions, so the exported
   zip picks up anything step 2 just refreshed. Export from the folder the run used:
   the worktree in generic mode, `<run folder>/confluence-collection/` in ticket
   mode. Report the output path.

4. **Check what's on the page, then ask.** Nothing has been written yet; this step
   decides whether anything will be.
   - **Read the current version.** If the page exists, `listConfluenceAttachments`
     (see "Downloading the current collection" for how to call it) and note the
     `version.number` of `attachmentName` (the listing gives no date or author).
     No page, or no file of that name → this is the first upload.
   - **Compare with the version this run started from.**
     - `<run folder>/confluence-base.json` exists (ticket mode downloaded the
       collection at the start): the same version means nobody has uploaded since.
       A higher version means someone uploaded after the download: download that
       one too, into a new, empty `<run folder>/confluence-newer/` (zip at
       `<run folder>/confluence-newer.zip`), and compare it with
       `<run folder>/confluence-collection/`.
     - No `confluence-base.json` (generic mode, or the download failed earlier):
       download the page's collection now, as "Downloading the current collection"
       describes, and compare it with the folder you exported from. A generic run
       exports `origin/<branch>` without uncommitted changes, so the page may well
       hold more than this zip. Also run
       `git -C <repo> status --porcelain -- <collectionPath>`; if it lists changes,
       say they aren't in the zip.
     - The download isn't possible: say you couldn't check what's on the page, and
       ask anyway with that warning.
   - **How to compare.** `diff -rq` the two extracted folders, ignoring
     `.DS_Store`, for a collection kept as one file per request (Bruno). For a
     collection kept in one JSON file (Postman, Insomnia), compare the request names
     in each, e.g. with a short `python3 -I` script that walks the `item` tree.
     Report it as: only on Confluence (publishing drops these), only in this zip,
     changed in both.
   - **Show the summary and ask.** Put any warning first, then:
     ```
     Publish to Confluence?
     - Page: <pageTitle> (<link>, or: new page under <parentId> in <spaceKey>)
     - <attachmentName>: <local path>, <size>, exported from <folder> (<branch> @ <commit>)
       replaces version <N> (becomes <N+1>) | first upload
     - <secondary name>: <local path>, <size>, <live values from envRefreshProcedure | static file>
       replaces version <N> | first upload
     - lastUpdate: <date>, commit <commit> on <branch>
     - Page check: unchanged since the download (version <N>) | NEWER: version <M> | differs from this zip: <summary>
     ```
     When the page holds a newer or different collection, offer the choices:
     publish anyway (it replaces that version), stop so the user can merge first
     (in ticket mode: take the newer one as the base and run again), or don't
     publish.
   - **Only a clear yes goes on to step 5.** Anything else: don't publish, keep
     the zip where it is, give its path, and list "Confluence not updated (user
     didn't approve)" under Not done in the run summary.

5. **Create the page** if step 1 found none: `createConfluenceContent` with
   `contentType: "page"`, `parent: {"parentContentId": "<parentId>"}` (the space
   comes from the parent), `title: "<pageTitle>"` and
   `body: {format: "html", value: ...}`, the value just
   `<div data-type="panel-info"><p>lastUpdate: pending</p></div>` (no file cards
   yet: there is no file to point to). Note the returned page ID.

6. **Upload the files**: the primary zip (`attachmentName`) and, if configured, every
   entry in `secondaryAttachments` (`sourcePath` under the run's repo root → fixed
   `name`). First list the page's files once more: if `attachmentName`'s version
   changed since step 4, someone uploaded in between, so stop and ask again. For
   each file:
   - Confluence names the attachment after the **local filename**, so the file
     must already carry its fixed name. The exported zip does
     (`<run folder>/<attachmentName>`); copy any other file into the run folder
     under its fixed `name` first and delete the copy after the upload. Never
     stage files inside the QA_Agent repo or the product repo: a file with live
     tokens left there gets committed.
   - A `secondaryAttachments` source that step 2 fills with live values (tokens,
     logins) sits at `sourcePath` under the run's repo root. When that root is the
     product repo or its worktree, check it before uploading
     with `git -C <repo> check-ignore -q <sourcePath>`; if git would pick it up
     (not ignored, or already tracked: `git -C <repo> ls-files --error-unmatch
     <sourcePath>`), stop and tell the user to gitignore it first. Don't edit the
     product repo's `.gitignore` yourself.
   - `createConfluenceAttachment` with `contentId` (the page ID), `localFilePath`
     (absolute path), `fileSize` (bytes) and `comment` (current commit SHA and
     branch). It uploads nothing itself: it returns an `uploadCommand`, a `curl`
     command with a token that is valid for about 5 minutes and covers only this
     page.
   - Run that `uploadCommand` with Bash right away. Expect HTTP 201 and JSON with
     `id`, `title` (the filename), `version.number` and `fileId`; note the
     `fileId`. If the token has expired, call `createConfluenceAttachment` again
     for a new one. The token is short-lived, but still keep the command out of
     reports and files.
   - **A filename that is already on the page becomes a new version of the same
     attachment**: same `id`, `version.number` + 1, still one file on the page, and
     downloading it returns the new content. No need to delete the old one first
     (checked 2026-10-27 on a test page with three uploads of one filename).

7. **Generate the page body**, listing every file uploaded in step 6:
   ```
   python3 <path-to-this-skill>/scripts/build_confluence_body.py <repo_root> <page_id> <attachmentName>=<fileId> [<secondaryAttachments[].name>=<fileId> ...]
   ```
   Prints an HTML fragment: an `info` panel with the `lastUpdate`/commit/branch line,
   then one file card per attachment in a media group.

8. **Update the page**: `getConfluenceContent` (`detail: "full"`) for the current
   `snapshotToken`, then `updateConfluenceContent` with the page ID, that
   `snapshotToken`, `body: {format: "html", value: <script output>}` and a
   `versionMessage` like `"Automated update from testing-api skill"`. The update
   replaces the whole body, so if the page holds anything besides the panel and the
   file cards, ask the user before overwriting it.

9. **Verify**, rather than trusting a success response:
   - `getConfluenceContent` (`detail: "full"`): the body has one
     `data-type="media"` element per uploaded file. Confluence rewrites each card's
     `data-id` to the newest version's `fileId`, so match on count, not on the ids
     you sent.
   - `listConfluenceAttachments` for the page: each fixed filename appears once,
     with the version number the upload returned.

10. **Report the page's URL** (`baseUrl` + `webUrl` from the update response) back to
   the user so they can open it directly, and name every attached file and its new
   version — don't just say "published."

## Downloading the current collection

Ticket mode reads the collection attached to this page first (see
[ticket-driven-testing.md](./ticket-driven-testing.md)); step 4 above reads it
when the run hasn't yet. It always lands in the same place in the run folder
(`<workDir>/api-runs/<ticket key, or YYYY-MM-DD-<env>>/`):

| Path | What |
| --- | --- |
| `<run folder>/confluence-base.zip` | The downloaded zip, as it is on the page |
| `<run folder>/confluence-collection/` | That zip extracted. It holds `<collectionPath>/` the way the repo does, so use it as the repo root: generating cases, running the suite and exporting all work from here in ticket mode |
| `<run folder>/confluence-base.json` | Which version was downloaded: `pageId`, `attachmentId`, `version` (the attachment's `version.number`), `downloadedAt`. Step 4 compares against it before publishing |

Neither operation below is a tool of its own; both run through `discover` and
`executeRead` of the site's Atlassian server:

1. **Load the tools.** If that server's `discover` and `executeRead` are deferred,
   load them with ToolSearch, e.g.
   `select:mcp__<server>__discover,mcp__<server>__executeRead`.
2. **Confirm the operations.** Call `discover` with "download attachment from
   confluence page". It returns `listConfluenceAttachments` and
   `downloadConfluenceAttachment` with their exact inputs, each marked
   `executeRead`.
3. **Find the file.** `executeRead` with `name: "listConfluenceAttachments"`,
   `cloudId` at the top level and `inputs: {contentId: <page ID from step 1 of the
   procedure>}`. Take the `id` and `version.number` of the entry whose `title` is
   `attachmentName`.
4. **Get the download command.** `executeRead` with
   `name: "downloadConfluenceAttachment"` and `inputs: {attachmentId: <that id>,
   outputPath: <absolute path of <run folder>/confluence-base.zip>}`. It returns a
   `downloadCommand`: a `curl` command with a token valid for a few minutes.
5. **Download.** Run `downloadCommand` with Bash right away, then check the file
   is there and not empty.
6. **Extract and record.** Unzip into `<run folder>/confluence-collection/`, which
   must be new and empty (`unzip -q <zip> -d <folder>`), check that
   `<collectionPath>` is there, and write `confluence-base.json` with the version
   from step 3.

If step 2 finds no such operations, or step 3 finds no file named
`attachmentName`, the download isn't possible: say so and fall back as
ticket-driven-testing.md Step 2 describes.

## Notes

- **Body format is `html`, the dialect in `getContentFormatGuide`
  (`toolName: updateConfluencePage`).** Confluence storage XML
  (`<ac:structured-macro>`, `<ri:attachment>`, the old `view-file` macro) renders as
  raw text through this server, and relative `/download/attachments/...` links are
  not file cards.
- A file card holds a `fileId`, not a filename, but it follows the attachment:
  after a later upload under the same filename the card shows the new version
  without any body change.
- Don't add a "this page is auto-generated / edits will be overwritten" disclaimer,
  or any other explanatory prose beyond the panel and file cards the script produces.
- If a product's `api.confluence` block has a stale/deleted `parentId` or the search
  returns nothing where a page is known to exist, say so and ask before creating a
  duplicate — don't silently create a second page under a different folder.
