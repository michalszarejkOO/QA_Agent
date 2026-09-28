# Data gathering

Load when executing Procedure step 2 (gather data), for the order of sources and the
rules for what to do when a source is unavailable.

## Order of preference

1. **Jira**, via whichever Atlassian connector is authorized for the project's site —
   confirm with `getAccessibleAtlassianResources` on each connector before trusting a
   previously-known mapping (site-to-connector mappings drift; see
   `~/.claude/environments/atlassian-connectors.json` if this repo already tracks one,
   but re-verify rather than assuming it's current). Use `searchJiraIssuesUsingJql` /
   the equivalent search tool. Confirm the real custom-field id for Sprint and any
   "Found in Environment"-style field with `getJiraIssueTypeMetaWithFields` before
   writing JQL against it — don't guess `customfield_XXXXX`.
   - **Always show the user the JQL used** for each headline metric, either inline in
     chat or in the page's footer/details section — this is what lets someone
     re-verify the number later.
   - Pull: bugs by severity/priority and status, environment found-in (sprint vs.
     production), component/feature area, fix versions, resolution timestamps, and
     changelog history for reopen detection.
2. **Test management** (Xray, Zephyr, TestRail) if a connector/API is available:
   latest regression run, pass/fail/blocked counts, automated vs. manual test counts.
3. **CI results** if accessible (a CI API, or a results file/dashboard the user can
   point to): automation pass rate, flaky test rate from rerun history.
4. **Production health** (Crashlytics, Sentry, Datadog) if a connector is available:
   crash-free users/sessions (mobile), error rate (web), top crash/error signatures.
5. **Anything else**: ask the user to paste the numbers, or mark the metric "No data."

## Never invent numbers

This is the one rule that overrides convenience everywhere else in this skill:

- A tool being unavailable, slow, or partially wrong is not license to estimate,
  interpolate, or carry forward a stale number from memory.
- If a metric can be computed but with a caveat (e.g. "reopen rate" needs changelog
  data that's slow to pull for every bug), say what was actually computed and what
  shortcut was taken, rather than silently narrowing scope without saying so.
- **Exception**: sample/demo data. Only when the user explicitly asks for a template,
  demo, or example with sample data — then every number on the page must be visibly
  labeled as sample data (a banner at the top of the HTML page, or a warning panel at
  the top of the Confluence page), not just mentioned once in chat.

## Trends

Whenever historical data is available, pull the same headline metrics for the previous
3–6 sprints/releases and compute simple trend deltas (up/down/flat vs. the immediately
prior period). If Jira has resolutiondate/created history and fixVersions for prior
releases, this is usually just the same JQL re-scoped to each prior period. If historical
data isn't available (e.g. a tool was only just connected, or this is the project's
first report), say so on the page instead of showing a fabricated flat trend.

## Missing-field example

If a project has no "Found in Environment" field (or equivalent) and no other
convention for tagging escaped defects, that metric cannot be computed from Jira alone.
Don't substitute a proxy (e.g. "bugs created after the release date" is not the same
thing — a bug found in a staging re-test after the tag date is not an escaped defect).
Ask the user how escaped defects are tracked in this project; if there's no answer,
mark the tile "No data — no environment-found field configured" and say so in chat.
