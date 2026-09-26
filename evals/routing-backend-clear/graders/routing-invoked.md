---
type: tool_used
weight: 1
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?routing-qa-tickets"'
min: 1
---

The response must invoke the `routing-qa-tickets` skill to classify the
ticket, rather than classifying it ad hoc without loading that skill's
procedure.
