# Default QA comment template

Used when the product's project skill has no "Jira QA comment" section, or the
section says "Default template".

## Short form (most tickets)

```
Checked with status: [PASSED]

- <what was checked and how it behaved, one line each>
- <...>
```

## Failed

Only the problems: no list of what worked, so the reader sees at once what
has to be fixed. The full results stay in the run's report.

```
Checked with status: [FAILED]

- <what goes wrong, in one line>: <bug link, e.g. ABC-124>
- <...>
```

Under each problem, the evidence a developer needs to reproduce it:

**API problem**: the request, expected against actual status, and the
response body in a JSON code block. Shorten a long body to the fields that
matter (`...` for the rest); replace any token, key or password with
`<redacted>`.

```
- A second user can take a number already in use: ABC-124
  PUT /v1/users/me/phone-number
  {"phoneNumber": "+966512345678"}
  Expected: 409   Actual: 200
  {
    "id": "8f3c...",
    "phoneNumber": "+966512345678",
    "updatedAt": "2026-11-02T11:59:12Z"
  }
```

**UI problem**: where it happens, what shows instead of the expected
behaviour, and a screenshot cropped to the element. The video stays in the
bug's evidence folder and goes with the bug when it is filed.

```
- Saving with an empty name closes the form without an error: ABC-125
  Settings > Profile, clear Name, Save
  Expected: "Name is required" under the field   Actual: the form closes, the old name stays
  [screenshot: bugs/ABC-125/screenshot.png]
```

When the screenshot can't be put into the comment through the Jira tool,
the draft says which file to attach by hand and gives its full path.

## With per-case detail (tickets with real scenarios)

After the list, one block per case that needs it (with FAILED, only for the
failing cases):

```
<Case title>
Steps: <short>
Expected: <...>
Result: <...>
Data: <ids that matter: user, record, order...>
<code block with the key response or log lines; logs expire, so keep them here>
```

## Status

One status for the whole ticket:

| Status | When | Lozenge color |
| --- | --- | --- |
| PASSED | everything checked works as the ticket says | green |
| FAILED | at least one problem the ticket's change caused or didn't fix | red |
| BLOCKED | the main scenarios couldn't run (environment down, no test data) | yellow |

A run that passed with a few cases not checked is PASSED, with those cases
listed as not checked and why.

## Examples

API:

```
Checked with status: [PASSED]

- Valid number (+966 followed by 9 digits) is saved and returned by GET /v1/users/me
- A second user sending a number already in use gets 409 "Phone number is already in use"; their own number stays unchanged
- Invalid formats (missing, empty, local 05 format, 8 or 10 digits, letters, +971) return 400
- No token or an invalid token returns 401, an auditor token 403
- Not checked: two users saving the same number at the same moment (no way to time it on stage)
```

UI (with a Figma link in the ticket):

```
Checked with status: [PASSED]

- Profile form shows the saved name, email and phone after opening Settings > Profile
- Empty name shows "Name is required" under the field and Save stays disabled
- Saved changes are visible after a page reload
- Matches the Figma design (spacing, colors, type, error state)
- Not checked: Arabic texts (translations not delivered yet)
```

## ADF

Build the body as ADF (`addOrEditJiraIssueComment`, `contentFormat: "adf"`):

- Heading: `{"type":"heading","attrs":{"level":3},"content":[{"type":"text","text":"Checked with status: "},{"type":"status","attrs":{"text":"PASSED","color":"green"}}]}`
- Each list: `bulletList` of `listItem` > `paragraph`.
- Each case title: a level 3 `heading`.
- Steps / Expected / Result / Data: a `paragraph` each, label in `strong`.
- Response bodies: `codeBlock` with `language: "json"`; log lines: `codeBlock` without a language.
- Screenshots: a `mediaSingle` with the uploaded image, when the Jira tool can upload one; otherwise a line naming the file to attach.
- Ticket links: `{"type":"inlineCard","attrs":{"url":"https://<site>/browse/ABC-124"}}`.
