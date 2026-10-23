#!/usr/bin/env bash
# Starts Playwright MCP with an output folder of its own per Claude window, so
# automatically named files (page snapshots, console logs, unnamed screenshots)
# never land in whatever folder Claude was opened in, and two windows testing at
# the same time never share a folder. collect_playwright_output.py later moves a
# run's files into the product's working directory.
#
# Register it once instead of calling npx directly:
#   claude mcp add --scope user playwright -- ~/.claude/skills/testing-apps/scripts/playwright-mcp.sh
#   claude mcp add --scope user playwright-video -- ~/.claude/skills/testing-apps/scripts/playwright-mcp.sh --isolated --caps=devtools
# Extra arguments are passed through to @playwright/mcp.
#
# Claude Code starts this script directly, so $PPID is the Claude process; the
# folder is named after it: <cache>/claude-<pid>/.
#
# Env: PLAYWRIGHT_MCP_CACHE (default ~/.cache/playwright-mcp),
#      PLAYWRIGHT_MCP_MAX_BYTES (default 200000000; older files are evicted past it).
set -euo pipefail

CACHE="${PLAYWRIGHT_MCP_CACHE:-$HOME/.cache/playwright-mcp}"
OUT="$CACHE/claude-$PPID"
mkdir -p "$OUT"

exec npx -y @playwright/mcp@latest \
  --output-dir "$OUT" \
  --output-max-size "${PLAYWRIGHT_MCP_MAX_BYTES:-200000000}" \
  "$@"
