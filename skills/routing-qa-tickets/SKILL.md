---
name: routing-qa-tickets
description: Classifies a bare Jira ticket and/or PR link as a backend or frontend change — and, if frontend, as web or mobile — before any testing begins, then dispatches to the testing-api skill (backend) or the qa-tester agent (frontend, with the resolved web URL or mobile device target). Use when asked to test, QA, or verify a ticket/PR that doesn't already say which kind of change it is or already come with a target — a bare ticket key/link with a generic ask to test it, with no mention of API/backend/endpoint and no web URL or device/bundle id supplied.
when_to_use: "Trigger on: 'test MWA-123', 'QA this PR', a bare Jira ticket key/URL or PR link with a generic ask to test/verify/check it, before it's known whether the change is frontend or backend. Do NOT trigger when the request already says backend/API/an endpoint (goes straight to testing-api) or already supplies a web URL or a mobile device/bundle id (goes straight to qa-tester) — those are already unambiguous and routing them through here just adds a step."
---

# Routing QA tickets

The first step for an untyped ticket or PR: decide backend vs. frontend, and for
frontend, web vs. mobile, using the cheapest signals available — before spending any
effort on the deeper context-gathering `qa-tester` or `testing-api` each do on their
own. This skill never tests anything itself; it classifies, resolves a concrete
target where one is needed, and hands off entirely to whichever existing skill/agent
owns that kind of testing. It doesn't duplicate their procedures, doesn't edit code,
and doesn't publish anywhere.

## Applicability and exclusions

- Skip this skill entirely when the request is already unambiguous — names the API,
  an endpoint, or "backend" (→ invoke `testing-api` directly), or already supplies a
  web URL or a mobile device/bundle id (→ invoke `qa-tester` directly).
- Classification only. Once a target is decided, `testing-api`'s and `qa-tester`'s own
  procedures (ticket/PR fetching, environment-config resolution, scenario writing,
  reporting) run unchanged — this skill does not re-fetch or re-derive anything they
  already own.
- Never guesses when the signals disagree or are absent — see steps 5 and 6.

## Classification signals

| Direction | Signals |
| --- | --- |
| Backend | Ticket labels/components/summary mention "[BE]", "Backend", "API"; PR/branch diff touches only backend-shaped paths (`api/`, `server/`, `controllers/`, `services/`, `repositories/`, migrations, an API collection folder) and no recognizable UI file; the matched product's environment config (see step 0) has an `api` block and no `surfaces` block at all. |
| Frontend — web | Ticket labels mention "Web"/"UI"/"Frontend" with no mobile qualifier; diff touches web UI paths/extensions (`.tsx`, `.jsx`, `.vue`, `.css`/`.scss`, `pages/`, `components/`, `views/`) under a repo that appears as a `surfaces.*.repo` with an `appUrl` in the matched environment config. |
| Frontend — mobile | Ticket labels mention "Mobile"/"iOS"/"Android"; diff touches `ios/`, `android/`, native mobile file types (`.swift`, `.kt`, `.java`, `.m`), or a React Native/Expo-shaped repo (`package.json` naming `react-native`/`expo`, a `Podfile`, `build.gradle`). |

A repo whose environment config carries only one of `api` / `surfaces` settles backend
vs. frontend by itself, regardless of ticket wording — check that before reading any
diff.

## Procedure

0. **Resolve the product config.** Match the ticket key's prefix (or the repo, if a PR
   is given instead) against `~/.claude/environments/*.json`, the same way `qa-tester`
   and `testing-api` do. Note which blocks it has (`api`, `surfaces`, both) — this
   alone can already answer backend-vs-frontend for a single-surface product.
1. **Gather minimal signals** — cheap, not the full context-gathering step: the
   ticket's labels/components/summary, and the PR's changed-file list only (e.g. `gh
   pr diff <n> --name-only`, or `git diff --name-only <base>...<branch>` if resolving
   the branch directly) — not the full diff body.
2. **Classify backend vs. frontend** against the table above.
   - Touches paths from *only one* direction, or the config settles it alone (step 0)
     → that direction. Continue to step 3 or 4.
   - Touches recognizable paths from *both* directions → mixed, go to step 5.
   - No labels, no component, and an empty or unreachable file list → no signal, go to
     step 6.
3. **Backend → invoke the `testing-api` skill** with the ticket (its own ticket mode
   takes over from here: reading the PR/branch, resolving the collection, generating
   coverage, reporting). Stop here.
4. **Frontend → classify web vs. mobile** against the table above, then resolve a
   concrete target and invoke the `qa-tester` agent with the ticket, the PR, and that
   target:
   - **Web** → the matched product's `surfaces.<name>.appUrl`. If more than one
     surface exists (e.g. `app` and `backoffice`), disambiguate using which surface's
     `repo` the touched paths actually belong to, or that config's own `notes` field
     when the paths alone don't decide it.
   - **Mobile** → nothing in the environment config shape resolves this today (see
     `environments.example/`), so ask the user for the device name/bundle id if the
     original request didn't already supply one — never invent or guess a target.

   Stop here once `qa-tester` is invoked.
5. **Mixed signals** (both backend- and frontend-shaped paths touched) → don't pick
   one silently. Report the split plainly — which touched paths/areas read as backend,
   which as frontend — and ask whether to run `testing-api`, `qa-tester`, or both.
6. **No usable signal** → say so plainly and ask the user to state backend/frontend
   and, if frontend, web/mobile, rather than defaulting to either.

## Output

State the classification reached and the concrete signal(s) it rests on (a labeled
component, specific touched paths, which config block existed) before handing off —
the decision should be auditable, not a black box. Then either the downstream
skill/agent runs and its result is returned as-is, or (steps 5–6) the question posed
back to the user, clearly separated from any classification already settled.
