# Preferences: what runs by itself, what asks, what never happens

Every skill and the `qa-tester` agent read one file before an action that leaves
the machine or changes something shared (a Jira comment, a bug, a 1Password or
Confluence upload) or that stops the run for a question (which environment). The
user decides once, per action, and isn't asked again:

`~/.claude/environments/qa-agent-preferences.json` (or under `$CLAUDE_CONFIG_DIR`),
one file for this machine. Shape:
[`qa-agent-preferences.example.json`](../../../environments.example/qa-agent-preferences.example.json).
No file means every action is at its default, `ask`, which is how QA_Agent
behaved before the file existed.

## Values

| Value | Meaning |
| --- | --- |
| `ask` | Ask every time, with the "remember" options below |
| `auto` | Do it without asking, then say what was done (link, item, version) |
| `never` | Don't do it and don't ask. The draft or file is still shown in the chat |

Read a value with
`python3 -I ~/.claude/skills/configure-project/scripts/preferences.py get <action> --product <product>`
(`product` from the matched config). A `products.<product>` value wins over
`actions`, which wins over the default.

## Actions

| Action | Who reads it | `auto` means |
| --- | --- | --- |
| `confirmTicketEnvironment` | `testing-api` ticket mode | Run on `api.ticketEnvironment` without asking. With no `ticketEnvironment` it still asks |
| `publishCollection` | `testing-api` (publishing.md step 4) | Publish once the check is clean |
| `postJiraComment` | after any test run (below) | Post the prepared comment on the tested ticket |
| `fileBugs` | after any test run (below) | Create a Jira bug for each bug draft |
| `attachEvidence` | with `postJiraComment` / `fileBugs` | Attach that bug's or run's screenshots and videos |
| `updateProjectSkill` | after any run that proposed lines for the project skill | Add the proposed lines to `<projectSkill>/SKILL.md` |

Evidence recording keeps its own switch, `mode` in `evidence.json`.

**`auto` never skips a safety stop.** These always ask, whatever the file says:
a newer published version than the run started from, a production environment
in an upload, secret-scan findings for Confluence, a likely duplicate found by
`find-duplicates` before filing a bug, a required Jira field with no value, and
anything the user's message for this run says to ask about. A run whose result
is in doubt (blocked, or the environment was unreachable) doesn't post or file
automatically either: it shows the drafts and asks.

## Asking, and remembering the answer

When an action is `ask`, ask with these four options (tappable when the session
can show options; in Polish when the user writes Polish):

1. **Yes** - this time only.
2. **Yes, always** - do it now, and save `auto`.
3. **No** - keep it as a draft this time.
4. **No, never ask** - save `never`; drafts are still shown.

Several actions due at the same moment (comment and bugs) go in one question
each, asked together, not one after another with work in between.

To save, run
`python3 -I ~/.claude/skills/configure-project/scripts/preferences.py set <action> <auto|never>`.
It saves for every product; add `--product <product>` only when the user says
"only for this project". Then tell the user in one line what changed and how to
undo it (the script prints the undo command). The user can also say at any time
"zmień ustawienia" / "change my QA_Agent preferences", or edit the file; `show`
lists everything.

A subagent (`qa-tester`) can't ask. It never posts or files itself; the
conversation that started it does, after it returns, following the next section.

## Mobile devices: Wi-Fi or cable

`mobile.connection` says how `testing-apps` reaches a physical iOS/Android
device, in order of preference:

| Value | Meaning |
| --- | --- |
| `["wifi", "usb"]` | Wi-Fi first; the cable only when no device is ready over Wi-Fi |
| `["usb", "wifi"]` | Cable first; Wi-Fi only when no device is ready over the cable |
| `["wifi"]` / `["usb"]` | Only that one |
| not set | Any ready device, cable and Wi-Fi equal |

Read or set it with `preferences.py connection [<order>]`. `testing-apps`
applies it through `scripts/list_physical_devices.py --connect` (its `pick`
line); see its `references/adapters/mobile.md`, "Physical devices: cable or
Wi-Fi". Simulators and emulators don't use it.

## After a test run: drafts in the chat, then post or file

This is the end of every ticket run, web, mobile or API (`qa-tester` via
`routing-qa-tickets` or invoked directly, and `testing-api` ticket mode):

1. **Show everything in the chat**, in this order, as text, never only as a file
   path: the summary (done / not done), the scenario-results table, the Jira
   comment draft in a fenced block, and every bug draft in full (title, steps,
   expected, actual, and the paths of its screenshot and video). A file such as
   `report.md` is at most a copy, saved only when `results.saveReportFiles` is
   `true`; never write an HTML or Markdown report instead of showing it.
2. **Comment.** Read `postJiraComment`. `auto`: post it (Atlassian tool for the
   ticket's site, see [connectors.md](./connectors.md)), then give the link.
   `ask`: ask as above. `never`: nothing more, the draft is above.
3. **Bugs.** Same with `fileBugs`, through the `creating-jira-tickets` skill,
   which still asks for any required field it can't fill. No bugs found: skip.
4. **Evidence.** When something was posted or filed and `attachEvidence` allows
   it, attach the files listed under that bug or run (see connectors.md,
   "Attachments" for the server in use).
5. **Project skill.** If the run proposed lines for the project skill, read
   `updateProjectSkill` and add them, ask, or leave them listed.
6. Close with one line per action: what was done (with link), or "kept as draft".

## Claude Code permissions

`auto` in this file decides what QA_Agent does without asking. Claude Code
still shows its own permission prompt for a tool it hasn't been allowed to use,
so an `auto` action can still stop for one. `claudePermissions` lists which
groups of tools to allow, so those prompts stop too:

| Group | Allows |
| --- | --- |
| `1password-read` | `op.sh` (the testing-api wrapper) and `op` with `vault list`, `account list`, `item list`, `item get`, `read` |
| `1password-write` | the same for `item create`, `item edit` (never `item delete`) |
| `jira-read` / `jira-write` | read / comment, create, update tools of each Atlassian server in `atlassian-connectors.json` |
| `confluence-read` / `confluence-write` | read / create, update, upload tools of the same servers |

`preferences.py permissions` shows which allow rules are missing from
`~/.claude/settings.json`; `preferences.py permissions --apply` adds them (it
never removes any) and keeps `settings.json.bak`. Adding permissions is the
user's decision: run `--apply` only when they asked for it or agreed, and if
Claude Code blocks the command, give them the command to run themselves
(`! python3 -I ...` in the prompt). Removing a rule from `permissions.allow`
takes it back.

1Password's own approval (Touch ID in the 1Password app) is separate from both:
it comes from the 1Password app, not from Claude Code, so no rule here stops it.
A service-account token in the Keychain does; see `testing-api`'s
`references/onepassword-publish.md`, "Signing in".
