---
type: tool_used
weight: 1
tool: Agent
input_match: '"subagent_type"\s*:\s*"qa-tester"'
min: 0
max: 0
---

The environment config's shape has no field that resolves a mobile
device/bundle id, and the request didn't supply one either — the response
must not dispatch to `qa-tester` with an invented or guessed device/bundle id.
