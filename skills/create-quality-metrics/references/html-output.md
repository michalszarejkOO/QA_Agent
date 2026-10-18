# Building the HTML dashboard

Load when the user picked HTML output (Procedure step 5, HTML branch). Start from
[assets/dashboard-template.html](../assets/dashboard-template.html) — copy it, then
fill it in; don't write a dashboard from scratch each time, and don't leave any
`{{PLACEHOLDER}}` token unresolved in the saved file.

## Before writing any chart code

Invoke the `dataviz` skill before touching the trend chart's colors, series, or
layout — it owns chart form/color rules project-wide and this dashboard's trend chart
and KPI status colors are exactly the kind of thing it governs. Apply its palette
guidance to the status colors (green/amber/red) and the trend chart series, rather
than picking colors ad hoc.

## Filling the template

1. **Header**: project name, release/sprint label, platforms (comma-joined), today's
   date, and a plain-text list of data sources actually used (e.g. "Jira, TestRail —
   Crashlytics not connected this run").
2. **Readiness banner**: set the status class (`is-ready` / `is-at-risk` /
   `is-not-ready`) and write the one-sentence reason from the verdict step. Pair the
   color with an icon/label already in the template — never leave a bare color swatch
   as the only signal.
3. **KPI tiles**: the template ships 5 example tiles. Delete any that have no data
   source this run rather than filling them with a guess, and delete the "Regression
   pass rate" tile if it's genuinely not part of this report. Each tile needs: label,
   value (or "No data"), trend vs. previous period (▲/▼/flat, or "No prior data"), and
   target. Cap at 6 tiles — if more headline metrics are wanted, they belong in the
   Details section instead (see the skill's "Metrics to avoid" list).
4. **Trend chart**: pass the per-period series (defects caught in sprint vs. escaped
   to production) into the embedded `chartData` JSON in the `<script>` block — no
   external fetch, everything embedded at generation time. Keep the `<table
   class="chart-fallback">` beneath the canvas in sync with the same numbers — it's
   the accessible/no-JS fallback and the print-friendly rendering of the same data,
   not decorative.
5. **Feature-area readiness table**: one row per feature area in scope, status one of
   Ready / Known risk / Not ready / Not in release, and a short plain-language note.
6. **Open risks**: one card/row per risk — user impact, likelihood, workaround, plan
   and owner, in plain language a non-technical client reader can follow. If there are
   no open risks, say so explicitly ("No open risks this period") rather than leaving
   the section empty or deleting it.
7. **Details (secondary metrics)**: keep this inside the `<details>` element so it's
   collapsed by default on screen, but still fully present in the printed/PDF output
   (the template's `@media print` rules force it open — don't remove those rules).
8. **Footer**: copy the definitions for every metric that actually appears on this
   page from [metrics-definitions.md](./metrics-definitions.md) (don't paste the whole
   file — only the ones used), and state which threshold set from
   [thresholds.md](./thresholds.md) applied, including any override.
9. **Sample data banner**: only when the user asked for a template/demo — uncomment
   the banner block at the top of the template and make sure every number on the page
   is plausible-but-fake, not a mix of real and invented values.
10. **Logo placeholder**: leave the `<!-- logo-placeholder -->` comment and empty
    `<img>` tag in place unless the user supplies a logo; don't fabricate a company
    mark.

## Saving and presenting

Save as a single `.html` file (suggest a name like `<project>-quality-<scope>.html` in
the current working directory unless the user names a path), then tell the user the
file path and that it can be opened directly in a browser or printed to PDF. Don't
open it in a browser yourself unless asked — presenting the path is enough.

## Constraints to double check before calling it done

- No `<script src>` or `<link>` except the pinned Chart.js CDN URL from
  `cdnjs.cloudflare.com` — everything else inline.
- No `fetch`/`XMLHttpRequest` in the page's own JS — all data is embedded at
  generation time, not loaded live.
- Every status color has a paired icon or text label.
- Headings are semantic (`<h1>`–`<h3>`, not styled `<div>`s), the chart canvas has an
  `aria-label` and a text/table fallback, and body text meets ordinary contrast
  expectations against its background.
