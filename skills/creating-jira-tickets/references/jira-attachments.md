# Attaching files to Jira (screenshots, videos)

How to put a run's evidence (a bug folder's `screenshot.png` and `video.mp4`, a
checkpoint screenshot) on a Jira issue or into a comment. It runs only after the
user's yes to filing the bug or posting the comment, in the conversation that has
that yes.

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

Do phase 1 and the `uploadCommand` only, then pass the `fileId` (with the
collection the result names) to `addOrEditJiraIssueComment` as its
`inlineFileId`, which puts the image at the end of the comment. Don't also run
phase 2 for the same file, or it shows up twice.

## When it doesn't work

- No Atlassian server in this session reaches the ticket's site: don't upload
  through another one. Say which site is missing (the `checking-qa-agent` report
  shows it) and give the files' full paths to attach by hand.
- `uploadCommand` fails: show the error once, don't retry with a copied file,
  and give the full path for a manual upload.
