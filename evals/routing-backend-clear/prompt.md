---
name: routing-backend-clear
tags: [routing, backend]
max_turns: 6
timeout_seconds: 120
allowed_tools: [Skill]
---

Skills available to you in this session include `routing-qa-tickets` and
`testing-api` — invoke whichever fits, per their own descriptions, rather than
answering from your own judgment alone.

A colleague asks: "test MWA-9001".

You don't have live Jira/GitHub access in this session — use exactly this
already-gathered context instead of trying to fetch anything:

- Ticket MWA-9001. Labels: ["Backend", "API"]. Summary: "Add rate limit to
  /auth/request-otp".
- Linked PR #412 changed files (name-only diff):
  `bruno/auth/request-otp/05-rate-limited.yml` (new),
  `src/modules/auth/request-otp.service.ts`,
  `src/modules/auth/request-otp.controller.ts`
- The matched environment config for ticket prefix `MWA` has only an `api`
  block (`client: bruno`, a `repo`, a `collectionPath`) — no `surfaces` block
  at all.

Classify this ticket and proceed accordingly.
