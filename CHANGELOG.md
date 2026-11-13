# What's new in QA_Agent

One entry per change a user will notice, written for the people who use QA_Agent,
not for the people who build it. Claude reads the new entries when it offers an
update (the `updating-qa-agent` skill and the update-check hook), so keep them
short and concrete: what you can do now, what works differently, what the update
will ask.

How to add entries: see `CLAUDE.md`, "Changing QA_Agent". One entry per
feature, written before the pull request, not one per commit.

## Unreleased

- You decide once what the agent does by itself after a test: confirm the
  test environment, publish the API collection, post the Jira comment, file
  bugs, attach screenshots and videos, add lines to the project skill. Each one
  can run by itself, ask, or never happen; a test running in the background
  does the automatic ones and gives you the links, the rest come back as
  drafts. Safety stops (a newer published collection, production, a likely
  duplicate bug, a doubtful result) always ask. The update asks "What should
  the agent do after a test without asking?" (ask, auto, never, or choose per
  action).
- An API collection is published as one package: the collection, the tests
  collection and the environments together, to one place per product
  (1Password, a local folder, both, or Confluence). In 1Password that's one zip
  in one item; the local folder always holds the last published version, and
  your hand edits there are protected. The update moves each product to the new
  setting, asking only when it isn't clear, and lists the old Environments and
  Tests items in 1Password that are no longer updated: archive them yourself
  once everyone on the team has updated. Update before the first publish with
  this version, since older versions can't read the new package.
- Jira comments: an API ticket gets "QA result" with the endpoint, request and
  response of the happy path, a UI ticket "Checked with status". Screenshots
  sit inside the comment where they belong. The update asks, for each API
  product with its own comment format, whether its comments include the
  endpoint, request and response.
- Testing on a physical phone: you choose whether Wi-Fi or the cable comes
  first, and Claude finds a phone that is actually reachable, waking Wi-Fi
  devices when it can. The update asks this when a product has a mobile app.
- 1Password without Touch ID prompts: a service-account token stored in the
  Keychain lets Claude read and publish on its own (optional).
- Smaller fixes: Jira searches stay small without losing ticket fields, and
  an older migration no longer adds a tests item to configs that already
  have a publish target.

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
