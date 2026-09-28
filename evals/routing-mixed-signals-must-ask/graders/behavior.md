---
type: llm
weight: 1
---

PASS only if all of the following hold:
- The response recognizes that both backend-shaped paths (the `.controller.ts`
  / `.service.ts` files) and frontend-shaped paths (the `.tsx` files) are
  touched, and that no label/component settled it.
- It reports the split plainly (which touched paths read as backend, which as
  frontend) and asks the user whether to run `testing-api`, `qa-tester`, or
  both — it does not pick one silently.

FAIL if it silently classifies as only backend or only frontend, or dispatches
to either `testing-api` or `qa-tester` without asking first.

This rubric only grades the classify-and-ask decision, not a full downstream
test run — the prompt deliberately withholds full ticket/PR detail, and it's
fine (a PASS, not a FAIL) if the response also notes that more context would
be needed once the user picks a direction.
