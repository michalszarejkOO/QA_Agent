# Metrics definitions

Load when computing metrics (Procedure step 3) or writing the page footer (every run
— the footer must define whichever of these appear on the page). Each entry gives the
client-facing definition, the formula, where the number comes from, and a starting
JQL/query to adapt to the actual project key and sprint/release field names (custom
field IDs for Sprint differ per Jira instance — confirm the real field id with
`getJiraIssueTypeMetaWithFields` or by inspecting one issue rather than guessing
`customfield_10020`).

## Headline metrics

### Escaped defects (found in production)
- **Definition**: bugs discovered *after* release, in production, rather than caught
  during the sprint or in regression testing before release.
- **Formula**: count of bug issues where the "found in environment" field (or a
  label/component convention, e.g. `env:production`) = Production, created within the
  scope window (sprint/release dates).
- **Source**: Jira.
- **JQL**: `project = <KEY> AND issuetype = Bug AND "Found in Environment" = Production AND created >= <scope_start> AND created <= <scope_end>`
  — if the project has no such field, ask the user how escaped defects are tagged
  (label, component, a specific board) before substituting a guess.

### Open critical/high defects
- **Definition**: bugs still unresolved, at Critical or High severity/priority, that
  are in scope for the release.
- **Formula**: count of open bug issues at Critical/High priority with a fix version
  matching the release (or unresolved and labeled for the current sprint).
- **Source**: Jira.
- **JQL**: `project = <KEY> AND issuetype = Bug AND priority in (Critical, High) AND statusCategory != Done AND fixVersion = <release>`

### Regression automation coverage
- **Definition**: percentage of the regression suite that runs automatically, without
  a manual tester.
- **Formula**: `automated regression test count / total regression test count * 100`.
- **Source**: Xray/Zephyr/TestRail (test count by automation status), or CI test
  inventory if no test-management tool is in use.

### Crash-free users / production error rate
- **Definition (mobile)**: percentage of distinct users who did not experience a crash
  in the period. **Definition (web)**: rate of 5xx/unhandled client errors per session
  or per request.
- **Formula**: mobile — `(users - users_with_crash) / users * 100` as reported by the
  crash tool, not recomputed manually. Web — errors / sessions (or requests) over the
  period, from the APM tool.
- **Source**: Crashlytics/App Center (mobile), Sentry/Datadog (web). If none is
  connected, mark "No data" — do not estimate from Jira bug counts, which undercount
  production errors users never reported.

### Regression pass rate (latest run)
- **Definition**: percentage of executed regression test cases that passed in the
  most recent full regression run.
- **Formula**: `passed / (passed + failed) * 100`, excluding cases marked blocked/
  skipped from the denominator (report skip count separately, don't hide it).
- **Source**: Xray/Zephyr/TestRail latest run, or CI E2E suite result if that's what
  the team uses for regression.

## Secondary metrics (Details section)

### Defects by severity and feature area
- **Definition**: breakdown of open + resolved-this-period bugs by severity and by
  component/feature area, for spotting concentration.
- **Source**: Jira. **JQL**: `project = <KEY> AND issuetype = Bug AND created >= <scope_start>` grouped by `priority` and `component`.

### Mean time to fix (critical/high)
- **Definition**: average time from a Critical/High bug's creation to its resolution,
  for bugs resolved in the period.
- **Formula**: `avg(resolutiondate - created)` over resolved Critical/High bugs in
  scope.
- **Source**: Jira. **JQL**: `project = <KEY> AND issuetype = Bug AND priority in (Critical, High) AND resolved >= <scope_start> AND resolved <= <scope_end>`

### Reopen rate
- **Definition**: percentage of bugs resolved in the period that were later reopened.
- **Formula**: `reopened_count / resolved_count * 100`. Reopen history usually needs
  the issue changelog (status transitions back to an open state after Done), not just
  current status — check via issue history, not a status snapshot.
- **Source**: Jira.

### Device/browser coverage
- **Definition**: which device/OS (mobile) or browser/viewport (web) combinations the
  regression run actually covered.
- **Source**: test-management tool's run configuration, or CI matrix config. Report as
  a plain list, not a percentage.

### Flaky test rate
- **Definition**: percentage of automated tests that failed and passed across repeated
  runs of the same commit without a code change (i.e., non-deterministic).
- **Formula**: `flaky_test_count / total_automated_test_count * 100` over a recent
  window (e.g. last 20 CI runs).
- **Source**: CI history (rerun/retry logs), or the test framework's own flake
  detection if configured.

### Automation trend
- **Definition**: how regression automation coverage has moved over the last 3–6
  sprints/releases — the direction matters more than any single value.
- **Source**: same as Regression automation coverage, sampled per period.

## When a metric can't be computed

If the required tool/field isn't accessible this session, or a field the JQL depends
on doesn't exist in this project, do not substitute an estimate. Mark the tile/row
"No data" on the page, and say in chat which metric is missing and why (tool not
connected, field not configured) so the user can decide whether to paste the number
manually or accept the gap.
