# Jira report template

Load this when writing the final report, every run. Fill every placeholder from the
actual CLI output and repo state of *this* run — never carry numbers over from a
previous conversation turn or a different product.

## Full-collection report

Use when the run covered the whole collection (or the user didn't scope it).

```
API Test Report — <one-line scope, e.g. "Auth OTP & Content endpoints">

Environment: <env> (<baseUrl from the collection's environment file for <env>>)
Commit: <git rev-parse --short HEAD> (branch: <git branch --show-current>)
Tool: <resolved api.client, e.g. "Bruno CLI (@usebruno/cli)" | "Newman (Postman)" | "inso (Insomnia)">, collection under <collectionPath>
Executed: <UTC timestamp, `date -u "+%Y-%m-%d %H:%M UTC"`>

Result: <ALL PASSED | N/M FAILED> — <requests passed>/<total requests> requests, <assertions passed>/<total assertions> assertions

| Endpoint                              | Cases | Result |
|----------------------------------------|:-----:|:------:|
| <METHOD /path>                         |  <n>  | <p>/<n> PASS |
...one row per folder that ran...

Coverage per endpoint:
- <bullet per category of case actually present, e.g. "Happy path (en/ar)">
- <validation rules exercised>
- <auth/business-logic cases>

Notes:
- <any caveat surfaced in step 6/7 of SKILL.md — failing case detail, a case that
  passed without truly testing what its name claims (e.g. expiry), an environment
  prerequisite that was or wasn't met, or a product-specific caveat from
  `api.knownCaveats`>
- <in generic (non-ticket) mode, a flag for thin coverage — e.g. "Only happy-path
  cases exist for POST /auth/login; no validation, auth-failure, or business-logic
  cases" — observation only, no cases were generated to fill it>
- <only include a note if it's true and useful — do not restate the obvious>

Test collection is committed under <collectionPath> and can be re-run at any time with
the resolved adapter's run command (see the matching adapters/*.md file).
```

## Scoped report (one or two endpoints)

Use when the user asked to test/report on a specific endpoint or folder only. Drop
the header fields that don't change the reader's trust in the result, keep it short:

```
<Short title, e.g. "Content API Test Note — Legal Documents">

Environment: <env> (<baseUrl>)
Commit: <short sha> (branch: <branch>)
Tool: <resolved api.client>, collection under <collectionPath>/<subfolder>

| Endpoint                              | Cases | Result |
|----------------------------------------|:-----:|:------:|
| <METHOD /path>                         |  <n>  | <p>/<n> PASS |

Coverage per endpoint:
- <bullets, same style as full report but only for the scoped endpoint(s)>

<Notes section only if there's a real caveat to flag — omit entirely otherwise>
```

## Ticket comment (ticket mode)

Use this, not the reports above, for the Jira comment in ticket mode. It may be
technical, but opens with a short summary any stakeholder can read:

````
*QA result: <Passed | Passed with issues | Failed | Blocked>* — <env> (<baseUrl>)

<One or two sentences in business terms: what the change lets the client or user do, and whether it works as the ticket describes.>

*What was tested:*
- <one bullet per case or closely related group: the situation in plain words, then the endpoint and status, e.g. "Login with a wrong password is rejected — POST /auth/login → 401 — OK">

*Request and response:*
<For each endpoint the ticket changed, one representative request and its response, normally the happy path, plus one for each failing case:>
<METHOD /path> — <case name>
{code:json}
<request body, or the query parameters for a GET; omit for a request without either>
{code}
Response: <status>
{code:json}
<response body, trimmed to the fields that matter, with "..." where cut>
{code}

*Issues found:*
- <one bullet per bug: a plain-language description, then the technical detail (request, expected vs actual status/body)>

Tested with <resolved api.client> on commit <short sha> (branch: <branch>); <requests passed>/<total requests> requests, <assertions passed>/<total assertions> assertions passed.
````

- Write it in English, whatever language the conversation uses.
- Take requests and responses from this run's CLI output or the reports it wrote,
  never from the collection's examples or docs.
- Replace tokens, OTPs, passwords, phone numbers, national IDs and other personal
  data with `<redacted>`.
- Omit *Issues found:* when there are none, and keep the Notes rules below for any
  real caveat, as a short *Notes:* list before the last line.

## Rules for filling it in

- **Result line must match the CLI summary table exactly.** Don't round or
  editorialize — "34/35" stays "34/35", with the failing case named in Notes.
- **Coverage bullets come from the actual case/request names and their docs/
  description fields**, not a generic guess — read a few request files if the case
  names aren't self-explanatory.
- **A Notes section is for something the reader would otherwise assume incorrectly.**
  Empty confidence-boosting filler ("all tests passed successfully!") doesn't belong;
  a real caveat (mock/god-code dependency, a case that's state-dependent, placeholder
  content) does. See the resolved adapter (`adapters/bruno.md` / `postman.md` /
  `insomnia.md`) and the product's `api.knownCaveats` for known ones.
- **A "N/N PASS" line next to happy-path-only coverage is exactly this kind of
  wrong assumption.** In generic mode, call out thin coverage as its own Note per
  SKILL.md step 6 — don't let the pass count stand unqualified.
- Always present the final report and the ticket comment inside a fenced code block on its own, so it can be
  copy-pasted into a Jira comment without picking up chat formatting.
