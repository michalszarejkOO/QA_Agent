---
type: tool_used
weight: 1
tool: Agent
input_match: '"subagent_type"\s*:\s*"qa-tester"'
min: 1
---

Since the signals are unambiguously frontend/web (labels + only web-UI-shaped
paths + a surfaces-only config with one surface), the response must dispatch
to the `qa-tester` agent with the resolved `appUrl` as the target, and must
not stop to ask the user for a target.
