# What's new in QA_Agent

One entry per change a user will notice, written for the people who use QA_Agent,
not for the people who build it. Claude reads the new entries when it offers an
update (the `updating-qa-agent` skill and the update-check hook), so keep them
short and concrete: what you can do now, what works differently, what the update
will ask.

How to add entries: see `CLAUDE.md`, "Changing QA_Agent". One entry per
feature, written before the pull request, not one per commit.

## Unreleased

## 1.1.0

- Everything about a product lives in its own working directory: its config,
  test evidence, API runs, reports and a project skill with what Claude has
  learned about it. Nothing lands on the Desktop or in the folder Claude was
  opened in, and Claude can write there from any folder.
- Setup updates itself: after `git pull` the setup re-runs on its own, and
  "update QA_Agent" applies the steps your machine still needs, asking only
  what you have to decide. "Check QA_Agent" prints a health report with a fix
  command for each problem.
- Claude tells you at session start, on the days you pick, when QA_Agent has
  a newer version, shows what's new and updates only after your yes.
- API collections no longer leave the machine with live tokens inside:
  environments are exported separately and published to 1Password (several
  tools per product) or Confluence, only after you confirm, with a warning
  when someone published a newer version.
- Ticket mode in `testing-api` asks which environment to test on instead of
  always using `demo`.
- Confluence publishing and Jira work through Atlassian's own MCP server.
- Web tests run in your normal window size. Figma is the reference for the
  look, not for the window size, so Claude no longer resizes the browser.
- Parallel mobile runs no longer break each other (the shared agent-device
  daemon is never killed).
- Old product files left outside their working directories can be found and
  moved ("gather project files").
- Smaller fixes: Bruno collections run from their own folder, scripts work on
  the macOS system Python, files with live tokens are no longer tracked in git.
