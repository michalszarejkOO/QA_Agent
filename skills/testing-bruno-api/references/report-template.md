# Jira report template

Load this when writing the final report, every run. Fill every placeholder from the
actual CLI output and repo state of *this* run — never carry numbers over from a
previous conversation turn or a different product.

## Full-collection report

Use when the run covered the whole collection (or the user didn't scope it).

```
API Test Report — <one-line scope, e.g. "Auth OTP & Content endpoints">

Environment: <env> (<baseUrl from the collection's environments/<env>.yml>)
Commit: <git rev-parse --short HEAD> (branch: <git branch --show-current>)
Tool: Bruno CLI (@usebruno/cli), collection under <collectionPath>
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
- <any caveat surfaced in step 5/6 of SKILL.md — failing case detail, a case that
  passed without truly testing what its name claims (e.g. expiry), an environment
  prerequisite that was or wasn't met, or a product-specific caveat from
  `bruno.knownCaveats`>
- <only include a note if it's true and useful — do not restate the obvious>

Test collection is committed under <collectionPath> and can be re-run at any time with:
npx @usebruno/cli run <collectionPath> --env <env> -r
```

## Scoped report (one or two endpoints)

Use when the user asked to test/report on a specific endpoint or folder only. Drop
the header fields that don't change the reader's trust in the result, keep it short:

```
<Short title, e.g. "Content API Test Note — Legal Documents">

Environment: <env> (<baseUrl>)
Commit: <short sha> (branch: <branch>)
Tool: Bruno CLI (@usebruno/cli), collection under <collectionPath>/<subfolder>

| Endpoint                              | Cases | Result |
|----------------------------------------|:-----:|:------:|
| <METHOD /path>                         |  <n>  | <p>/<n> PASS |

Coverage per endpoint:
- <bullets, same style as full report but only for the scoped endpoint(s)>

<Notes section only if there's a real caveat to flag — omit entirely otherwise>
```

## Rules for filling it in

- **Result line must match the CLI summary table exactly.** Don't round or
  editorialize — "34/35" stays "34/35", with the failing case named in Notes.
- **Coverage bullets come from the actual `info.name`/`docs:` of the files that ran**,
  not a generic guess — read a few request files if the case names aren't
  self-explanatory.
- **A Notes section is for something the reader would otherwise assume incorrectly.**
  Empty confidence-boosting filler ("all tests passed successfully!") doesn't belong;
  a real caveat (mock/god-code dependency, a case that's state-dependent, placeholder
  content) does. See [test-case-conventions.md](./test-case-conventions.md) and the
  product's `bruno.knownCaveats` for known ones.
- Always present the final report inside a fenced code block on its own, so it can be
  copy-pasted into a Jira comment without picking up chat formatting.
