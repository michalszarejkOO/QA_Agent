# Release readiness thresholds

Load when computing the verdict (Procedure step 4), and always show whichever set was
actually used in the page footer. These are defaults, not a fixed standard — ask the
user at the start whether to keep them or override any number, and record on the page
which set applied to that run.

## Default thresholds

| Verdict | Condition |
| --- | --- |
| **Ready** | 0 open critical defects in release scope, AND 0 open high defects in release scope, AND regression pass rate ≥ 95%. |
| **Ready with risks** | 0 open critical defects, AND ≤ 3 open high defects that each have either a documented workaround or explicit PO acceptance, AND regression pass rate ≥ 90%. |
| **Not ready** | Any open critical defect in release scope, OR regression pass rate < 90%, OR any key feature area not tested (status "Not tested" in the feature-area table). |

Evaluate in this order: check Not ready conditions first (they override everything
else), then Ready, then Ready with risks as the fallback if some defects exist but
none of the Not ready conditions fire.

## Applying the thresholds

- **Never default to green.** If data is missing for a condition (e.g. no regression
  pass rate available), the verdict cannot be "Ready" — treat it as "Not ready" or, if
  everything else looks fine and only a secondary input is missing, "Ready with
  risks" with the gap named explicitly as the reason data is incomplete. Never silently
  skip a condition because its input is missing.
- **State the reason in one sentence**, naming the specific condition that decided it
  — "Not ready: 1 open critical defect in release scope (MWA-512)," not "some issues
  found."
- **"Release scope"** means: filtered to the release's fix version (release mode) or
  the current sprint (sprint mode) — confirm which scope applies with the user in step
  1 if the request doesn't make it obvious.
- **"Documented workaround or PO acceptance"** for the Ready-with-risks high-defect
  allowance means there's a comment/field on the bug recording one of those, or the
  user confirms it directly in chat for this run — don't assume acceptance just because
  a bug is old or low-traffic.

## Overriding thresholds

If the user gives different numbers (e.g. "we accept up to 5 open high defects" or "90%
regression pass rate is fine for Ready"), use theirs for this run and note the override
on the page's footer next to the thresholds table, e.g. "Thresholds customized for this
project: ...". Don't carry an override forward into a future run without the user
restating it — each run confirms or overrides fresh, since thresholds may reasonably
differ by project or client agreement.
