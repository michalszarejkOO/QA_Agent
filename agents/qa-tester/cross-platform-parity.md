# Cross-platform parity

Read by `qa-tester` in step 2 when the evidence folder already holds a run of
the same ticket on another platform, e.g.
`<workDir>/qa-evidence/<TICKET>/<date>-android/` when you're testing iOS.

1. Read that run's file names and screenshots and use its scenarios as the
   baseline: every scenario it ran gets a matching row in your list, with the
   other run's ID next to it.
2. That includes Storybook-only components, theme, contrast, font scale, screen
   reader, and both languages and roles.
3. You may only drop one after you've tried it on your platform and it failed;
   report it as BLOCKED with the exact error. "Not reachable in the shipped
   build", "needs system settings" or "needs a debugger" aren't reasons on
   their own if the other platform found a way.
