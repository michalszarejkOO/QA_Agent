# Updating the collection's Confluence tracker page

Load this when executing the final "publish" step of the procedure, for any product
whose `environments/*.json` config has a `bruno.confluence` block. Skip entirely if
that block is absent.

**Scope, precisely:** this page is a `lastUpdate` tracker plus the exported zip as a
file attachment — never inline collection content. Do not dump request files, YAML,
or any collection content into the page *body*. The zip from step 2 of SKILL.md
(`export-collection.sh`) is attached to this same page as a binary attachment (see
"Attach the exported zip" below) so the user can download it straight from
Confluence; the page body itself still only records *when* the collection was last
touched.

## Identifiers come from the product's config

Read these from that product's `bruno.confluence` block in `environments/*.json` —
never hardcode a site/space/page for a specific product in this file:

| Config field | Meaning |
| --- | --- |
| `cloudId` | Confluence site, e.g. `is-takamol.atlassian.net` |
| `spaceKey` | Space key, e.g. `MU` |
| `parentId` | Target folder's page id (the collection's landing folder) |
| `pageTitle` | Fixed page title, so re-runs update instead of duplicating |
| `attachmentName` | Fixed zip filename, so re-runs create a new version instead of duplicating |

Attachment upload/delete is done through the **`mcp-atlassian`** server (not
`tsh-core_atlassian`, which has no attachment tools). `confluence_upload_attachment`
re-versions an existing attachment automatically when the filename matches, so
re-runs update in place.

## Procedure

Order matters: the page **body** needs to embed a file card that points at the
attachment's media id, so the attachment must be uploaded to a known page ID
*before* the body referencing it is generated. On first run (no page yet) this
means create the bare page first, then attach, then update the body — never try
to attach content in the same call that creates the page.

1. **Load the Atlassian tool schemas** if not already loaded this session:
   `ToolSearch` with `select:mcp__plugin_tsh-core_atlassian__searchConfluenceUsingCql,mcp__plugin_tsh-core_atlassian__createConfluencePage,mcp__plugin_tsh-core_atlassian__updateConfluencePage,mcp__plugin_tsh-core_atlassian__getConfluencePage`
   and `select:mcp__mcp-atlassian__confluence_upload_attachment`. Use
   `mcp__plugin_tsh-core_atlassian__*` for page create/update/search and
   `mcp-atlassian` for the attachment.

2. **Find any existing page**, so the run updates in place instead of duplicating:
   ```
   searchConfluenceUsingCql: cql = 'space = <spaceKey> AND ancestor = <parentId> AND title = "<pageTitle>" AND type = page'
   ```
   - **Found** → note its `pageId`, skip to step 3.
   - **Not found** → `createConfluencePage` with `cloudId`, `spaceId: "<spaceKey>"`,
     `parentId: "<parentId>"`, the fixed `pageTitle`, and a minimal placeholder body
     (e.g. just the panel from step 4 with no file card yet — there is no attachment
     to reference on first creation). Note the returned page ID.

3. **Attach the exported zip** to that page ID, using the **`mcp-atlassian`** server:
   - `confluence_upload_attachment`'s `file_path` is sandboxed to the repo directory —
     the export script's default destination (`~/Desktop/...`) is outside it and will
     fail with a path-traversal error. Copy the zip into the repo root under the fixed
     `attachmentName` first, upload from there, then delete the copy:
     ```
     cp <exported_zip_path> ./<attachmentName>
     ```
     `content_id`: the page ID from step 2. `file_path`: `<attachmentName>` (bare
     relative path — do not pass a `filename` override alongside `file_path`, it's
     ignored and the *local* filename is what Confluence stores; that's why the local
     copy must already have the fixed name). `comment`: current commit SHA and
     branch.
   - Uploading under a filename that already exists on the page creates a new version
     automatically (same media id stays valid) — no need to delete the old one first.
   - Read `fileId` and `content_id` from the response — the next step needs them as
     `media_id` and `collection` (collection is `contentId-<page_id>`).
   - Clean up: `rm ./<attachmentName>` immediately after the upload confirms success,
     and confirm with `git status` (in the repo root) that the repo is back to clean
     (this file must never be committed).

4. **Generate the page body**, now that the attachment's media id is known:
   ```
   python3 <path-to-this-skill>/scripts/build_confluence_body.py <repo_root> <attachmentName> <media_id> contentId-<page_id>
   ```
   Prints the `lastUpdate`/commit/branch info panel followed by a file-card
   `media-group` node referencing the attachment, so the zip shows up as a visible,
   clickable card on the page itself — not just in the page's hidden attachments
   list. Pass its stdout directly as the `body` parameter.

5. **`updateConfluencePage`** with that `pageId`, the generated body, and a
   `versionMessage` like `"Automated update from testing-bruno-api skill"`.

6. **Report the page's `webui` link** (from the tool response `_links.webui`,
   prefixed with the site's `/wiki` base) back to the user so they can open it
   directly, and mention the attached zip by name — don't just say "published."

## Notes

- The body format is HTML (Confluence's ADF-mapped HTML dialect), which is the
  default for `createConfluencePage`/`updateConfluencePage`. If a publish call is
  rejected with a format error, call `getContentFormatGuide` with `toolName:
  "createConfluencePage"` and reconcile the script's output against current guidance
  before retrying — the guide, not this note, is authoritative.
- Don't add a "this page is auto-generated / edits will be overwritten" disclaimer,
  or any other explanatory prose beyond the two lines the script produces.
- If a product's `bruno.confluence` block has a stale/deleted `parentId` or the CQL
  lookup returns nothing where a page is known to exist, say so and ask before
  creating a duplicate — don't silently create a second page under a different
  folder.
