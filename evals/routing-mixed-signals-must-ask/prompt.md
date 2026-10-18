---
name: routing-mixed-signals-must-ask
tags: [routing, mixed-signals]
max_turns: 6
timeout_seconds: 120
allowed_tools: [Skill, Agent]
---

Skills/agents available to you in this session include `routing-qa-tickets`,
`testing-api`, and the `qa-tester` agent — invoke whichever fits, per their
own descriptions, rather than answering from your own judgment alone.

A colleague asks: "test ACME-410".

You don't have live Jira/GitHub access in this session — use exactly this
already-gathered context instead of trying to fetch anything:

- Ticket ACME-410. No labels, no component set. Summary: "Support a new
  notification-preference option end to end".
- Linked PR #133 changed files (name-only diff):
  `src/modules/notifications/preferences.controller.ts`,
  `src/modules/notifications/preferences.service.ts`,
  `src/components/NotificationPreferences.tsx`,
  `src/pages/Settings.tsx`
- The matched environment config for ticket prefix `ACME` has both an `api`
  block and a `surfaces` block (this product has both a UI and an API
  collection).

Classify this ticket and proceed accordingly.
