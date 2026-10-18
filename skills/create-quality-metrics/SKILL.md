---
name: create-quality-metrics
description: Builds a client-facing QA quality metrics dashboard for a web/mobile Scrum project, as a standalone HTML page or a Confluence page (new or updated). The audience is the client (Product Owner, business stakeholders, client CTO), so the page answers "can we release safely," "is quality improving," and "what risks exist" first — QA activity metrics (test cases executed, hours spent) are secondary or omitted. Pulls real numbers from Jira (JQL), test-management tools (Xray/Zephyr/TestRail), CI, and production health tools (Crashlytics/Sentry/Datadog) where accessible; never invents or estimates a number — missing data is marked "No data" or asked for, except in explicit template/demo mode where all values are labeled as sample data. Computes a release readiness verdict (Ready / Ready with risks / Not ready) against agreed thresholds, always with a one-sentence honest reason. Use when asked to create quality metrics, a QA dashboard, a quality report, a release quality summary, or a sprint quality report for a client.
when_to_use: "Trigger on: 'prepare quality metrics for release 2.4', 'make a QA dashboard for the client', 'quality report for sprint 14 on Confluence', 'create quality metrics', 'przygotuj metryki jakości', or any request mentioning a sprint/release/Jira project plus wanting quality status presented to a client or stakeholder. Do NOT trigger for writing test cases, test plans, or bug reports (writing-test-cases, reporting-bugs) — this skill only builds the metrics/readiness page, it doesn't test anything or draft tickets."
---

# Creating quality metrics

Builds a client-facing quality dashboard — not a QA activity report. Every section
exists to answer one of three business questions: can we release safely, is quality
improving or getting worse, and what risks exist right now. Test-case counts, hours
spent, and bugs-per-tester are QA-internal metrics and stay off the headline page.

## Applicability and exclusions

- Not for writing test cases, test plans, or bug reports — those are
  `writing-test-cases` and `reporting-bugs`.
- Not for actually running tests — this skill reads existing results (Jira, test
  management, CI, production health tools); it doesn't execute a suite itself.
- **Never invent or estimate a number.** If a source is unavailable, mark the metric
  "No data" on the page and say so in chat, or ask the user to paste it. The only
  exception is explicit template/demo mode (see step 2 and
  [data-gathering.md](./references/data-gathering.md)), where every value must be
  visibly labeled as sample data.
- The verdict must be honest. Never default to green, and always state the deciding
  reason in one sentence — see [thresholds.md](./references/thresholds.md).

## Non-negotiable rules

| Severity | Rule |
| --- | --- |
| MUST | Ask output format, scope (sprint/release + Jira project), and platforms up front in one step — skip only the parts the user already answered. |
| MUST | Show the user the JQL used for each Jira-sourced headline metric (inline or on the page). |
| MUST | Cap headline KPI tiles at 4–6; anything else goes in the secondary/Details section. |
| NEVER | Headline raw test-case counts, bugs-per-tester, or bare code-coverage % — secondary section only, and only if asked for. |
| MUST | Compare against 3–6 prior sprints/releases whenever data allows — trends matter more than a snapshot. |
| MUST | Confirm thresholds with the user (keep defaults or override) before computing the verdict, and record which set was used on the page. |
| NEVER | Publish to Confluence, or overwrite content outside the dashboard section of an existing page, without explicit user confirmation first. |
| MUST | For HTML output, keep the page self-contained — inline CSS/JS, Chart.js only from `cdnjs.cloudflare.com`, no other external calls, print-friendly, accessible. |

## Reference Loading

| Reference | Load when | Covers |
| --- | --- | --- |
| [data-gathering.md](./references/data-gathering.md) | Step 2, every run | Source order (Jira → test mgmt → CI → prod health → ask user), the never-invent-numbers rule, sample-data mode, trend pulls, handling a missing field |
| [metrics-definitions.md](./references/metrics-definitions.md) | Step 2 (computing) and step 5 (footer) | Each metric's definition, formula, source, and starting JQL |
| [thresholds.md](./references/thresholds.md) | Step 4 | Default Ready / Ready-with-risks / Not-ready conditions, evaluation order, override handling |
| [html-output.md](./references/html-output.md) | Step 5, HTML branch | Filling [assets/dashboard-template.html](./assets/dashboard-template.html), the `dataviz` skill hand-off for the trend chart, save/present |
| [confluence-output.md](./references/confluence-output.md) | Step 5, Confluence branch | Filling [assets/confluence-template.xml](./assets/confluence-template.xml), storage-format macros, live JQL issue macros, preserve-vs-replace on update, publish confirmation |

## Procedure

1. **Clarify scope in one step**, skipping anything already answered:
   - Output format: HTML or Confluence.
   - Scope: sprint, release, or time period, and which Jira project(s).
   - Platforms in scope: web, iOS, Android.
   - For Confluence: target space, and create-new (under which parent) vs.
     update-existing (link or title).
   Use tappable options where available.

2. **Gather data** per
   [data-gathering.md](./references/data-gathering.md) — Jira first (show the JQL),
   then test management, CI, production health, and anything else by asking the user
   or marking "No data." If the user explicitly asked for a template/demo, use
   clearly-labeled sample data instead and skip live data gathering.

3. **Compute metrics and trends** per
   [metrics-definitions.md](./references/metrics-definitions.md), comparing against
   the previous 3–6 sprints/releases wherever data allows.

4. **Determine the release readiness verdict** per
   [thresholds.md](./references/thresholds.md) — confirm the threshold set with the
   user first, evaluate Not-ready conditions before Ready, and write the one-sentence
   honest reason.

5. **Build the page**, following the layout below, using
   [html-output.md](./references/html-output.md) or
   [confluence-output.md](./references/confluence-output.md) depending on the format
   chosen in step 1. Show the user a short summary of the verdict and key findings
   first; for Confluence, get explicit confirmation before publishing. For HTML, save
   the file and give the user its path.

## Page layout (verdict → evidence → detail)

1. Header: project, release/sprint, platforms, last-updated date, data sources.
2. Release readiness banner: Ready / Ready with risks / Not ready + one-sentence reason.
3. KPI row (4–6 tiles): escaped defects, open critical/high, regression automation
   coverage, crash-free users / production error rate, optionally regression pass rate
   — each with value, trend, and target.
4. Trend chart/table: defects caught in sprint vs. escaped to production, per period.
5. Readiness by feature area: table with area, status, short note.
6. Open risks: impact, likelihood, workaround, plan/owner — plain language.
7. Secondary metrics (collapsible/Details): severity/area breakdown, MTTR
   critical/high, reopen rate, device/browser coverage, flaky test rate, automation
   trend.
8. Footer: metric definitions and thresholds used, for the client's benefit.

## Tone

Clear, factual, client-friendly — explain QA terms in plain language rather than
assuming familiarity. Positive where earned, transparent about risk. Short sentences.
