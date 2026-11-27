# Attaching files to Jira (screenshots, videos)

How to put a run's evidence (a bug folder's `screenshot.png` and `video.mp4`, a
checkpoint screenshot) on a Jira issue or into a comment. It runs only when the bug
is filed or the comment posted, after the user's yes or because `fileBugs` /
`postJiraComment` is `auto`, and `attachEvidence` allows it (ask, or `auto`).

## Rules

| | Rule |
| --- | --- |
| MUST | Upload through Atlassian's own MCP server (the one with `getAccessibleAtlassianResources` and `discover`) for the ticket's site, with the operation `uploadAttachmentToJiraIssue`. |
| MUST | Upload the file from where the run saved it, in the product's working directory (`<workDir>/qa-evidence/...`), by its absolute path. |
| NEVER | Use another Atlassian server (`mcp-atlassian`, tools named `jira_…` or `confluence_…`, company plugins). They restrict which folders a file may come from and fail on evidence in a product's working directory. |
| NEVER | Copy evidence into the QA_Agent repo, the folder Claude was opened in, `/tmp` or anywhere else to get an upload through. If the upload fails, say so and give the file's full path so the user can attach it by hand. |

## Attaching a file to the issue

1. `discover` with "upload attachment to a jira issue", to get the operation's
   current inputs.
2. Phase 1: `executeWrite` with `name: "uploadAttachmentToJiraIssue"`, the
   `cloudId`, and `inputs` holding `issueIdOrKey` and `filePath` (the absolute
   path). It returns an `uploadCommand`.
3. Run that `uploadCommand` with Bash, as it is. It uploads the bytes and prints
   a `fileId`.
4. Phase 2: `executeWrite` again with `issueIdOrKey` and that `fileId` (no
   `filePath`). The file is now an attachment of the issue.

One file per call; repeat for each file. Report each attached file by name.

## A screenshot inside a comment

Screenshots go into the comment body, not only as attachments; videos are
attached to the issue as above.

1. For each image: phase 1 and its `uploadCommand` only. Note the `fileId`
   and the collection the result gives.
2. In the comment's HTML body (`writing-jira-comments`, `contentFormat:
   "html"`), put each image right where it belongs, with a caption:

   ```html
   <figure data-type="media-single" data-layout="center" data-width="60" data-width-type="percentage"><div data-type="media" data-media-type="file" data-id="FILE_ID" data-collection="COLLECTION" data-alt="screenshot.png"></div><figcaption>What the screenshot shows</figcaption></figure>
   ```

   `FILE_ID` and `COLLECTION` come only from the upload result, never made
   up. Keep `data-width-type="percentage"`, or Jira shows the image tiny.
3. Post it with `addOrEditJiraIssueComment`.

Fallback when a `<figure>` is rejected: post the same body without it and
pass `inlineFileId` / `inlineFileCollection` (in display order) instead; the
images then land at the end of the comment, so number their captions in the
body. Don't also run phase 2 for the same file, or it shows up twice. When
editing a comment that has images, fetch it as HTML and write it back with
every `<figure>` it had.

## When it doesn't work

- No Atlassian server in this session reaches the ticket's site: don't upload
  through another one. Say which site is missing (the `checking-qa-agent` report
  shows it) and give the files' full paths to attach by hand.
- `uploadCommand` fails: show the error once, don't retry with a copied file,
  and give the full path for a manual upload.
