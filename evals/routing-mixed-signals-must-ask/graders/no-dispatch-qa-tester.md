---
type: tool_used
weight: 1
tool: Agent
input_match: '"subagent_type"\s*:\s*"qa-tester"'
min: 0
max: 0
---

Both backend- and frontend-shaped paths are touched and no label settles it —
the response must not silently pick frontend and dispatch to `qa-tester`
either.
