---
name: routing-frontend-web-clear
tags: [routing, frontend, web]
max_turns: 6
timeout_seconds: 120
allowed_tools: [Skill, Agent]
---

Skills/agents available to you in this session include `routing-qa-tickets`
and the `qa-tester` agent — invoke whichever fits, per their own descriptions,
rather than answering from your own judgment alone.

A colleague asks: "QA ticket ACME-201".

You don't have live Jira/GitHub access in this session — use exactly this
already-gathered context instead of trying to fetch anything:

- Ticket ACME-201. Labels: ["Web", "UI"]. Summary: "Show a warning banner when
  the user's session is about to expire".
- Linked PR #77 changed files (name-only diff):
  `src/components/SessionWarningBanner.tsx`,
  `src/pages/Dashboard.tsx`,
  `src/styles/banner.scss`
- The matched environment config for ticket prefix `ACME` has a `surfaces`
  block with a single surface, `app`, whose `appUrl` is
  `https://app.acme.staging.example.com/` and whose `repo` matches the repo
  these changed files live in — no `api` block at all.

Classify this ticket and proceed accordingly.
