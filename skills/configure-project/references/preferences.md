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
| `confirmTicketEnvironment` | `testing-api` ticket mode, `retesting-tickets` | Run on `api.ticketEnvironment` (set in the setup wizard) without asking. With no `ticketEnvironment` it still asks. An environment named in the user's message always wins |
| `publishCollection` | `testing-api` (publishing.md step 4) | Publish once the check is clean |
| `postJiraComment` | after any test run (below) | Post the prepared comment on the tested ticket |
| `fileBugs` | after any test run (below) | Create a Jira bug for each bug draft |
| `attachEvidence` | with `postJiraComment` / `fileBugs` | Attach that bug's or run's screenshots and videos |
| `updateProjectSkill` | after any run that proposed lines for the project skill | Add the proposed lines to `<projectSkill>/SKILL.md` |

Evidence recording keeps its own switch, `mode` in `evidence.json`.

## Choosing in the setup wizard

`configure-project` step 5b (and migration 015 for existing installs) asks one
question, "What should the agent do after a test without asking?", with four
options:

| Option | Writes |
| --- | --- |
| **ask** (suggested to start with) | nothing: every action asks the first time, and "Yes, always" / "No, never ask" save the answer for that one action |
| **auto**: "The agent does everything itself and only asks at the end whether to add knowledge to the project skill" | `confirmTicketEnvironment`, `publishCollection`, `postJiraComment`, `fileBugs`, `attachEvidence` → `auto`; `updateProjectSkill` → `ask` |
| **never**: the agent does the work (test, comment draft, bug drafts, collection) and keeps everything in the chat and on disk; it publishes, posts and files nothing and doesn't ask | all six → `never` |
| **mix**: choose per action | asks about each action (`ask` / `auto` / `never`, one sentence each), in two questions of three; `updateProjectSkill` suggests `ask` |

Full `auto` for `updateProjectSkill` too is set through **mix** or later with
"zmień ustawienia QA_Agent". End with one sentence: every action can be changed
later.

**`auto` never skips a safety stop.** These always ask, whatever the file says:
a newer published version than the run started from, a production environment
in an upload, secret-scan findings for Confluence, a likely duplicate found by
`find-duplicates` before filing a bug, a required Jira field with no value, data
the project skill says must not be touched, and anything the user's message for
this run says to ask about. A run whose result
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

A subagent (the test run of `testing-api`, `testing-apps`, `retesting-tickets`,
`qa-tester`) can't ask. It does the `auto` actions itself (publish, post, file,
attach) and returns what it did with links. Actions at `ask` or `never`, and any
`auto` action stopped by a safety stop, come back as drafts; the questions and
`preferences.py set` happen only in the main conversation, after it returns,
following the next section.

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
   path: the summary (done / not done, and what the subagent already did by
   itself, with links), the scenario-results table, the Jira comment draft in a
   fenced block, and every bug draft in full (title, steps, expected, actual,
   and the paths of its screenshot and video). A report file such as
   `report.md`, `results.md` or an HTML report is at most a copy, saved only when
   `results.saveReportFiles` is `true`; never write one instead of showing it.
   A ticket's `qa-evidence/<TICKET>/test-cases.md` and `notes/` are always
   saved: they are the ticket's working files, not a report.
2. **`auto` actions first.** Everything at `auto` is done before any question:
   the subagent did it, or, when the run happened in this conversation, do it
   now (comment: the Atlassian tool for the ticket's site, see
   [connectors.md](./connectors.md); bugs: `creating-jira-tickets`; evidence:
   attached as connectors.md, "Attachments" says), then give the links.
3. **Then the `ask` questions, together.** Comment (`postJiraComment`), bugs
   (`fileBugs`, through `creating-jira-tickets`, which still asks for any
   required field it can't fill; no bugs found: skip), evidence
   (`attachEvidence`, when something was or will be posted or filed): one
   question each, asked together, as above. A `never` action asks nothing; its
   draft is above.
4. **The project skill, always last.** If the run proposed lines for the project
   skill, read `updateProjectSkill` and add them, ask, or leave them listed. This
   comes after every other action and question, so the user answers it with the
   whole run in view.
5. Close with one line per action: what was done (with link), or "kept as draft".

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
