---
type: tool_used
weight: 1
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?testing-api"'
min: 1
---

Since the signals are unambiguously backend (labels + only-backend-shaped
paths + an `api`-only config), the response must dispatch to the
`testing-api` skill and must not stop to ask the user to classify it manually.
