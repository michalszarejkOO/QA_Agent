# What's new in QA_Agent

One entry per change a user will notice, written for the people who use QA_Agent,
not for the people who build it. Claude reads the new entries when it offers an
update (the `updating-qa-agent` skill and the update-check hook), so keep them
short and concrete: what you can do now, what works differently, what the update
will ask.

How to add entries: see `CLAUDE.md`, "Changing QA_Agent". One entry per
feature, written before the pull request, not one per commit.

## Unreleased

- Sessions cost less. Test runs (API, app exploration, qa-tester) happen in a
  subagent on Sonnet, so responses, screenshots and diffs no longer stay in
  the main conversation; ask for Opus ("puść na Opusie") when one run needs
  it. Skills load less on every run and Jira tickets are read with lighter
  calls. The update asks at what size Claude Code should compact a long
  conversation (200k recommended).
- Long conversations can be handed off to a fresh session: "save the state"
  writes what was done, found and drafted to `handoff.md` in the ticket's
  folder, and after `/clear` "continue IP-123" picks it up from there. Past a
  context size you set, Claude offers the handoff or saves it on its own, and
  never while an agent is still working. The update asks how it should behave
  (ask, auto or never), at what context size, and whether to install a status
  line that shows the context size in colour.
- New skills: retest fixed bugs and reworked tickets ("retest IP-330"),
  analyse a screen recording or screenshot you point to, and draft the QA
  comment for Jira in your product's format. Every skill now reads the whole
  ticket, comments included, which often change the acceptance criteria. The
  update asks which Jira comment format each product uses.
- Postman no longer loads its 233 tools into every session: syncing with the
  Postman app runs in its own agent, signed in with your Postman API key from
  1Password. The update asks for that key's 1Password reference. Its warning
  lists only the variables the collection really needs.
- The API collection can live only in 1Password or Confluence, with a local
  copy kept at the latest published version, and Postman products can keep
  their test cases in a separate tests collection. The update asks where each
  product's collection lives and whether to use a tests collection.
- Everything about one ticket is in its folder: test cases, notes, SQL,
  scripts and the handoff. The update offers to move existing ticket files
  there.
- New users get the same setup questions as existing ones, an update shows
  this list before it starts, and the setup wizards say where every suggested
  answer comes from.
- Smaller fixes: readable evidence videos (recorded at the page's real size),
  API defects in bugs as copyable JSON instead of screenshots, retest
  comments cover only the retested ticket, reading a ticket's code never
  moves your checkout, and every skill's triggers fit in Claude Code's
  listing.

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
