# Default QA comment template for an API ticket

Used for a ticket tested through the API (testing-api ticket mode, or
retesting-tickets on the API) when the product's project skill has no "Jira QA
comment" section, or the section says "Default template". A UI ticket uses
[ui-comment-default-template.md](ui-comment-default-template.md).

It may be technical, but opens with a short summary any stakeholder can read.
The endpoint, request and response of the happy path are always there, for
every endpoint the ticket changed: never skipped, not for a clean pass.

## Template

```
QA result: <Passed | Passed with issues | Failed | Blocked> — <env> (<baseUrl>)

<One or two sentences in business terms: what the change lets the client or user do, and whether it works as the ticket describes.>

What was tested:
- <one bullet per case or closely related group: the situation in plain words, then the endpoint and status, e.g. "Login with a wrong password is rejected — POST /auth/login → 401 — OK">

Endpoint, request and response:
<For each endpoint the ticket changed: the happy-path request and its response, always, plus one for each failing case:>
<METHOD /path> — <case name>
<request body as JSON, or the query parameters for a GET; omit for a request without either>
Response: <status>
<response body as JSON, trimmed to the fields that matter, with "..." where cut>

Issues found:
- <one bullet per bug: a plain-language description and its bug link, then the technical detail (request, expected vs actual status/body)>

Tested with <resolved api.client> on <commit <short sha> (branch: <branch>) | the published collection, version <version>>; <requests passed>/<total requests> requests, <assertions passed>/<total assertions> assertions passed.
```

- Write it in English, whatever language the conversation uses.
- Take requests and responses from this run's CLI output or the reports it
  wrote, never from the collection's examples or docs.
- Replace tokens, OTPs, passwords, phone numbers, national IDs and other
  personal data with `<redacted>`.
- A happy path that didn't run or didn't pass: show the closest successful
  request instead and say so, or, if nothing passed, the failing request and
  its response.
- Omit "Issues found" when there are none. A real caveat goes in a short
  "Notes" list before the last line.

## Status

| Status | When | Lozenge color |
| --- | --- | --- |
| Passed | everything checked works as the ticket says | green |
| Passed with issues | works, with problems that don't block the ticket (each with its bug) | yellow |
| Failed | at least one problem the ticket's change caused or didn't fix | red |
| Blocked | the main scenarios couldn't run (environment down, no test data) | yellow |

## ADF

Build the body as ADF (`addOrEditJiraIssueComment`, `contentFormat: "adf"`):

- First line: a `paragraph` with `strong` "QA result: ", a `status` lozenge
  (`{"type":"status","attrs":{"text":"PASSED","color":"green"}}`) and the
  environment as plain text.
- "What was tested", "Endpoint, request and response", "Issues found",
  "Notes": a `paragraph` with the label in `strong`; lists as `bulletList` of
  `listItem` > `paragraph`.
- `<METHOD /path> — <case name>` and `Response: <status>`: a `paragraph`, the
  method and path in `code` marks.
- Request and response bodies: `codeBlock` with `language: "json"`.
- Ticket links: `{"type":"inlineCard","attrs":{"url":"https://<site>/browse/ABC-124"}}`.
