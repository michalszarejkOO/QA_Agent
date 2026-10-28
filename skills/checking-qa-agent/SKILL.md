---
name: checking-qa-agent
description: Read-only health check of a QA_Agent install — skills and agent links, git hooks, pending migrations, product configs (paths, working directories, project skills, REPLACE_ME values), Playwright/playwright-video/maestro MCP registration, required tools (git, python, node, ffmpeg, agent-device, Xcode/adb, the 1Password CLI when a product publishes to 1Password), product files left outside their working directories, the update-check settings, whether its hook is registered and QA_Agent changes not pulled yet, and, live, whether every Jira site in atlassian-connectors.json is reachable through an Atlassian MCP server in this session. Prints one report with FAIL/WARN/OK/INFO and the exact command to fix each problem; never installs or changes anything. Runs at the end of configure-project and updating-qa-agent ("post setup"), and on request.
when_to_use: "Trigger on: 'sprawdź setup', 'sprawdź QA_Agent', 'post setup', 'czy wszystko działa', 'check QA_Agent', 'check my setup', 'doctor', 'is the QA agent set up correctly', as the last step of configure-project or updating-qa-agent, or when a run fails in a way that looks like setup (missing tool, MCP server, Jira site, config path). Do NOT trigger to fix anything — it only reports; fixing is the user's call (or updating-qa-agent / configure-project)."
---

# Checking QA_Agent

Reports whether this machine has everything QA_Agent needs. It never installs,
moves, registers or deletes anything: each problem comes with the command that
fixes it, and the user decides.

## Procedure

1. **Run the script part:**
   `python3 -I "$(dirname "$(dirname "$(readlink ~/.claude/agents/qa-tester.md)")")/skills/updating-qa-agent/scripts/check_setup.py" --full`
   It covers links, hooks, migrations, configs, MCP registration and tools.
   Keep its output as-is for the report.
2. **Check Jira and Confluence access live** (the script can't): read
   `~/.claude/environments/atlassian-connectors.json`. For each site, find an
   Atlassian MCP server available in this session (local ones like
   `atlassian-<name>`, or a claude.ai Atlassian connector) whose
   `getAccessibleAtlassianResources` returns that site. Call it; don't infer
   from the server's name. Only Atlassian's own server counts (it has
   `getAccessibleAtlassianResources` and `discover`); a site reached only through
   another one, such as `mcp-atlassian`, is a FAIL. Report per site:
   - **OK** `<site>` via `<server>`.
   - **FAIL** `<site>` not reachable by any server. Fix: `claude mcp add
     --transport http --scope user atlassian-<name> https://mcp.atlassian.com/v2/mcp`,
     then `/mcp` → that server → Authenticate, and pick `<site>` on the consent
     screen (it may preselect another site). claude.ai allows only one Atlassian
     connector, so a second site always needs a local server.
   - **WARN** a server answers for a different site than its name suggests (e.g.
     `atlassian-headstart` returns is-takamol): its OAuth grant picked the wrong
     site; clear and re-authenticate it in `/mcp`.
   If `atlassian-connectors.json` doesn't exist, report INFO "no Jira connectors
   configured".
3. **Optional, only if the user asks:** reachability of each product's
   `surfaces.*.appUrl` and `api.baseUrl` (`curl -s -o /dev/null -w "%{http_code}" --max-time 10`).
   Report as INFO: a timeout or 403 is often just a missing VPN, not a setup
   problem.
4. **Report** in this order: one summary line ("N problems, M warnings"), then
   FAIL, WARN, INFO, OK, merging the script's lines with the Jira lines. Keep
   every fix command exactly as printed so the user can copy it. End with what
   matters most to fix first, in one sentence. Don't offer to run the fixes
   unless the user asks; if they do, `updating-qa-agent` or `configure-project`
   is usually the right skill.
