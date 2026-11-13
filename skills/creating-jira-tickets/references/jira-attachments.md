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

1. For each image, in the order it should appear: phase 1 and its
   `uploadCommand` only. Note the `fileId`, the collection and the file name
   the result gives.
2. Post the comment with `addOrEditJiraIssueComment`, the body as
   `writing-jira-comments` builds it (ADF), and per image, in display order:
   `inlineFileId`, `inlineFileCollection` and `inlineFileName`. If the tool
   rejects inline files with an ADF body, send the same content with
   `contentFormat: "html"`.
3. The images land at the end of the comment, so number their captions in
   the body ("Screenshot 1: ...", "Screenshot 2: ...") and refer to them by
   number.

Don't also run phase 2 for the same file, or it shows up twice.

## When it doesn't work

- No Atlassian server in this session reaches the ticket's site: don't upload
  through another one. Say which site is missing (the `checking-qa-agent` report
  shows it) and give the files' full paths to attach by hand.
- `uploadCommand` fails: show the error once, don't retry with a copied file,
  and give the full path for a manual upload.
