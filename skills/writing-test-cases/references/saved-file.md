# The saved test-case file

Every plain-table set of test cases is also saved to disk, so a later session
can find the cases of a ticket, rerun them, retest against them or extend them
without deriving them again. One file per ticket, in that ticket's folder,
next to its evidence: everything about a ticket (cases, test data, results,
screenshots, videos) is in one place.

## Where

`<workDir>/qa-evidence/<TICKET>/test-cases.md`, for example
`<workDir>/qa-evidence/IP-150/test-cases.md`. The runs' evidence sits beside it
in `<YYYY-MM-DD>-<web|ios|android>/` folders (`testing-apps`, "Recorded evidence").

- `workDir` comes from the product file in `~/.claude/environments/` (or
  `$CLAUDE_CONFIG_DIR/environments/`) whose `ticketPrefixes` match the ticket
  key. Create the ticket folder on the first write if no run made it yet.
- No ticket key (a described feature, a PR only): the folder is named after the
  feature in lowercase words joined by `-`, or `PR-<number>` for a PR.
- No product file matches: save to `./qa-evidence/<TICKET>/test-cases.md` in the current folder and
  say in the reply that no working directory is configured for this product.
- Never into the Desktop, `/tmp`, `~/Downloads` or the session's scratchpad.

## Before writing: read what is there

If the file exists, read it first and build on it:

- Keep every case's number. A changed case keeps its number; a new case gets
  the next free number; a case that no longer applies stays, with
  `(obsolete: <why>)` at the end of its title. Never renumber, because runs,
  Jira comments and bugs refer to the numbers.
- Keep every run under "Runs". A new run goes on top.

## Format

```markdown
# IP-150: <ticket summary>

- Ticket: <ticket URL>
- PR: <PR or branch URL, or "none found">
- Design: <Figma URL, or "none linked">
- Updated: 2026-11-06

## Test cases

| Title | Preconditions | Steps to reproduce | Expected result |
| --- | --- | --- | --- |
| TC-01: ... | ... | 1. ...<br>2. ... | 1. ...<br>2. ... |

## Test data

How to get to each case's starting state when it needs prepared data: which
account type, which API calls or database change (its SQL file in the ticket's
`notes/` folder), which record was used last time. Leave the section out when no case needs prepared data.

## Runs

### 2026-11-06, stage, web (qa-tester)

- Evidence: <absolute path of the run folder>
- Bugs: <links of bugs filed from this run, or "none">

| Case | Result | Notes |
| --- | --- | --- |
| TC-01 | Passed | |
| TC-02 | Failed | IP-123, screenshot c10-...png |
```

- The four case columns follow the plain-table format in `SKILL.md`. Inside a
  table cell, separate numbered lines with `<br>`.
- Results: `Passed`, `Failed` (name the bug or the deviation), `Blocked` (what
  blocked it). A case not run in this run isn't listed in its table.
- Test data names records (account type, establishment, record ID) so the case
  can be repeated; it never holds a password, a token or another secret.
- English, unless the project skill says otherwise.

## Who writes it

- `writing-test-cases` (plain mode): after the table is ready.
- `qa-tester` can't write files: it returns the cases and results in its
  report, and the conversation that started it saves them here (the case
  table, the test data and a new run). That conversation also saves the
  results of a retest (`retesting-tickets`) as a new run in the file of the
  ticket it retested, or of the story the bug was found in.
- Give the file's full path in the reply each time it is written.
