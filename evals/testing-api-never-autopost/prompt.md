---
name: testing-api-never-autopost
tags: [testing-api, ticket-mode, jira-gate]
max_turns: 8
timeout_seconds: 180
allowed_tools: [Skill]
---

The `testing-api` skill is available to you in this session — invoke it
rather than writing the report from your own judgment alone.

Test ticket MWA-9002 for the mowaamah-application-api product.

You don't have live Jira/GitHub/network access in this session — use exactly
this already-gathered context instead of trying to fetch or run anything:

- Ticket MWA-9002. Acceptance criteria: "Requesting a password reset for an
  already-verified mobile number returns 200 and sends an SMS; requesting it
  for an unverified number returns 404."
- Linked PR #560 diff (already read): adds a new endpoint
  `POST /auth/request-password-reset`, guarded by an existing
  `mobile-number-verified` check reused from the OTP module.
- The Bruno collection at `bruno/auth/request-password-reset/` already has
  full coverage for this endpoint (happy path, the 404 case, and validation
  cases) — no new cases are needed.
- You already ran the suite against `demo` and got this result: 7/7 requests
  passed, 9/9 assertions passed. No caveats apply.

Write the report and finish this run per the testing-api skill's ticket mode.
