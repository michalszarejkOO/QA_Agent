# Updating the collection's Confluence tracker page

Load this when executing the final "publish" step of the procedure, for any product
whose `environments/*.json` config has an `api.confluence` block. Skip entirely if
that block is absent. **In ticket mode this step is mandatory, not conditional on
results** — see [ticket-driven-testing.md](./ticket-driven-testing.md) Step 6.

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
| `secondaryAttachments` | (Optional) array of `{ "name": "<fixed filename>", "sourcePath": "<path relative to repo root>" }` — e.g. a live-populated environment file. Each is attached and shown as its own file card, same as the primary zip. |
| `envRefreshProcedure` | (Optional) filename of a product-specific markdown doc, resolved relative to the same `environments/` directory as the product's own config, describing how to mint/refresh live values into a `secondaryAttachments` file before export. Load and follow it verbatim, in full, before step 4 below, when present. Not every product needs this — most `secondaryAttachments` (if any) are static files with no live-minting step. |

## Which server to use

Use the **`mcp-atlassian`** server (`mcp__mcp-atlassian__confluence_*`) for
**everything** in this procedure — search, page create/update, and attachments. It
is self-sufficient for Confluence and does not need Jira access at all. Do not use
`plugin_tsh-core_atlassian` or any other Atlassian-flavored connector for the page
body here — see the Notes section below for why.

## Procedure

Order matters: the page **body** references each attachment by filename, so every
attachment must be uploaded to a known page ID *before* the body update. On first
run (no page yet) this means create the bare page first, then attach, then update
the body — never try to attach content in the same call that creates the page.

1. **Load the Atlassian tool schemas** if not already loaded this session:
   `ToolSearch` with
   `select:mcp__mcp-atlassian__confluence_search,mcp__mcp-atlassian__confluence_create_page,mcp__mcp-atlassian__confluence_update_page,mcp__mcp-atlassian__confluence_get_page,mcp__mcp-atlassian__confluence_upload_attachment,mcp__mcp-atlassian__confluence_upload_attachments,mcp__mcp-atlassian__confluence_get_attachments`.

2. **Find any existing page**, so the run updates in place instead of duplicating:
   ```
   confluence_search: query = 'space = <spaceKey> AND ancestor = <parentId> AND title = "<pageTitle>" AND type = page'
   ```
   - **Found** → note its `pageId`, skip to step 3.
   - **Not found** → `confluence_create_page` with `space_key: "<spaceKey>"`,
     `parent_id: "<parentId>"`, the fixed `pageTitle`, `content_format: "storage"`,
     and a minimal placeholder `content` (just the info-panel macro from step 6, no
     file cards yet — there is no attachment to reference on first creation). Note
     the returned page ID.

3. **If `envRefreshProcedure` is configured**, load and follow it now, before
   exporting — it mints/refreshes the live values that go into the corresponding
   `secondaryAttachments` file.

4. **Export the collection**, per the adapter's export instructions, so the exported
   zip picks up anything step 3 just refreshed. Report the output path.

5. **Attach the files** to the page, using **`mcp-atlassian`**:
   - `confluence_upload_attachment`/`confluence_upload_attachments`' `file_path` is
     sandboxed to Claude Code's own working directory — a repo outside it (e.g. the
     export script's default `~/Desktop/...` destination, or a product repo that
     isn't the current working directory) fails with a path-traversal error. Copy
     each file that needs uploading into the current working directory first (a
     scratch subfolder is fine), upload from there under its fixed name, then delete
     the copy:
     ```
     cp <source_path> ./<fixed_name>
     ```
     `content_id`: the page ID from step 2. `file_path`: the local copy's path. Do
     not pass a `filename` override alongside `file_path` — it's ignored, and the
     *local* filename is what Confluence stores, which is why the local copy must
     already have the fixed name. `comment`: current commit SHA and branch.
   - Do this for the primary zip (`attachmentName`) and, if configured, every entry
     in `secondaryAttachments` (`sourcePath` relative to the repo root → fixed
     `name`).
   - Uploading under a filename that already exists on the page creates a new
     version automatically — no need to delete the old one first, and the view-file
     macros in the body (which reference by filename, not by id) keep working across
     versions without any change.
   - Clean up every local copy immediately after its upload confirms success.

6. **Generate the page body**, listing every attachment now on the page:
   ```
   python3 <path-to-this-skill>/scripts/build_confluence_body.py <repo_root> <attachmentName> [<secondaryAttachments[].name> ...]
   ```
   Prints genuine Confluence **Storage Format** XHTML: an `info` panel macro with the
   `lastUpdate`/commit/branch line, followed by one `view-file` macro per attachment
   — each referencing its file **by filename**, so there's nothing to look up between
   the upload step and this one. Pass its stdout directly as `content`, with
   `content_format: "storage"`.

7. **`confluence_update_page`** with that `page_id`, the generated `content`,
   `content_format: "storage"`, the unchanged `title` (required by the tool even when
   it isn't changing), and a `version_comment` like `"Automated update from
   testing-api skill"`.

8. **Verify**: call `confluence_get_page` with `convert_to_markdown: false` and
   confirm the returned `content.value` actually contains one `ac:structured-macro
   ac:name="view-file"` element per attachment uploaded in step 6 — don't assume the
   update rendered correctly just because the call returned success. A markup
   mismatch can silently drop a file card instead of erroring (see Notes).

9. **Report the page's `url`** (from the tool response, or build it from `cloudId` +
   the page's webui path) back to the user so they can open it directly, and mention
   every attached file by name — don't just say "published."

## Notes

- **Use genuine Confluence Storage Format (XHTML) via `mcp-atlassian`, not the
  ADF-derived HTML dialect** (`<div data-type="media-group">...`, `data-id="<uuid>"`)
  that some other Atlassian connectors' page tools accept. Feeding that dialect into
  `mcp-atlassian`'s `confluence_update_page` either silently **drops** the
  unrecognized `data-type` divs from the stored content (confirmed 2026-09-21/25 —
  the file card vanished entirely, no error) or, with an even earlier mismatch,
  created a broken 0-byte phantom attachment (confirmed 2026-09-16). The `view-file`
  macro form in this doc, generated with `content_format: "storage"`, is the form
  actually confirmed to render correctly.
- Don't add a "this page is auto-generated / edits will be overwritten" disclaimer,
  or any other explanatory prose beyond the panel and file cards the script produces.
- If a product's `api.confluence` block has a stale/deleted `parentId` or the search
  returns nothing where a page is known to exist, say so and ask before creating a
  duplicate — don't silently create a second page under a different folder.
