---
name: routing-mobile-must-ask
tags: [routing, frontend, mobile]
max_turns: 6
timeout_seconds: 120
allowed_tools: [Skill, Agent]
---

Skills/agents available to you in this session include `routing-qa-tickets`
and the `qa-tester` agent — invoke whichever fits, per their own descriptions,
rather than answering from your own judgment alone.

A colleague asks: "test ACME-330".

You don't have live Jira/GitHub access in this session — use exactly this
already-gathered context instead of trying to fetch anything:

- Ticket ACME-330. Labels: ["iOS"]. Summary: "Fix crash on biometric login
  retry".
- Linked PR #91 changed files (name-only diff):
  `ios/AcmeApp/BiometricLoginViewController.swift`,
  `ios/AcmeApp/Auth/RetryPolicy.swift`
- The matched environment config for ticket prefix `ACME` has a `surfaces`
  block (web only, an `app` surface with an `appUrl`) — nothing that names a
  mobile device, simulator, or bundle id.
- The original request did not supply a device name or bundle id either.

Classify this ticket and proceed accordingly.
