# Publishing to 1Password

Load this from [publishing.md](./publishing.md) when `api.publish.collection` or
`api.publish.environments` is `1password`. That file decides what goes where,
compares versions and asks the user; this one is how to read, download and upload
with the 1Password CLI (`op`). **Nothing is uploaded before the user's yes in
publishing.md, step 4.**

## Identifiers come from the product's config

From `api.publish.onePassword`:

| Field | Meaning |
| --- | --- |
| `vault` | The vault that holds the items, chosen per product at setup |
| `collectionItem` | Title of the item holding the collection, by convention `<Product> <Client> Collection` (e.g. `Emtethal Postman Collection`) |
| `environmentsItem` | Title of the item holding the environments, by convention `<Product> <Client> Environments` |

Each part is one item, so 1Password keeps its own version history and `version`
number per part. The item's History in the 1Password app shows every upload.

**One product, several tools.** The item titles carry the client, so a product
tested with Bruno by one person and with Postman by another gets separate items
(`Emtethal Bruno Collection`, `Emtethal Postman Collection`). That's allowed and
never blocked: each person publishes only their own tool's items and never
touches the other's. They are separate collections, though; nothing carries
changes between them. So when the vault also holds `<Product> <other client>
Collection`, add one information line to the summary (publishing.md step 4):
"Also in the vault: <title>, last changed <date>. It is a separate collection;
changes don't pass between them." Nothing more: no question, no block.

## What goes into each item

Both items are **Secure Notes** holding files under their own names, for every
client, so they look and work the same. Files go up as they are, so people can
use them straight away; only a Bruno collection, a folder of many files, travels
as a zip.

| Client | Collection item holds | Environments item holds |
| --- | --- | --- |
| `postman` | `<name>.postman_collection.json` | one file per environment: `stage.postman_environment.json`, ... |
| `bruno` | `<product>-bruno-collection.zip`: the import zip (export part `full`), collection **and** `environments/` plus any `secondaryAttachments` file, so one file imports everything into Bruno | one file per environment: `stage.yml`, ... from `<collectionPath>/environments/` |
| `insomnia` | the export file itself | nothing separate: an Insomnia export holds its environments, so with `environments: "1password"` say so and skip that part |

Any `secondaryAttachments` file (a live-populated environment) goes into the
environments item under its fixed `name` (and, for Bruno, into the collection's
import zip, see publishing.md step 1). The Bruno environments are thus in both
items; the environments item keeps one file per environment so changes per
environment show up in its history and can be compared by variable name.
A Bruno collection zip published before this (without `environments/`) is
simply replaced by the import zip on the next upload; mention "environments now
included" in its `Changes` line. Upload copies from the run folder, never
the repo files themselves: put the files above into `<run folder>/publish/` first
(from the folder the run used as the repo root).

**Notes and tags, every upload.** Replace the item's notes with just when it was
updated and what this upload changed, nothing else:

```
Updated: <YYYY-MM-DD HH:MM> (local time)
Changes: <what this upload changed, in a few words>
```

`Changes` names what differs from the version it replaces, e.g. "stage:
+qiwa_api_key", "demo added", "3 requests added in QIWA, 1 removed", or "first
upload". Never put values in it. An environment whose file name looks like
production (`prod`, `prd`, `production`, `live`) gets one more line,
`PRODUCTION: <file>`; publishing.md step 4 asks about it separately. Tags:
`<product>`, `<client>`, `qa-agent` (lowercase).

An existing item of another shape (a Document with a zip, from before this
layout): don't upload into it. Say so, and with the user's yes in the step 4
summary archive it (`op.sh item delete "<item>" --vault "<vault>" --archive`; it stays
in Archive with its history and can be restored) and create the item in this
shape. Never delete an item without `--archive`.

## Signing in is the user's

**Run every 1Password command through the wrapper**,
`~/.claude/skills/testing-api/scripts/op.sh` (written `op.sh` below and in the
commands table: `op.sh item get ...` means that script with those arguments).
It runs `op`, with the user's service-account token when one is stored (see
below), so there's no Touch ID prompt; otherwise through the 1Password app as
before. `op.sh --auth` says which (`service-account` or `app`).

**App integration** (no stored token): every `op` call needs an unlocked
1Password with the CLI integration on (1Password app > Settings > Developer >
"Integrate with 1Password CLI"). Check sign-in with `op.sh vault list`; 1Password
shows its approval dialog for it, so tell the user to approve it first. Don't use
`op whoami` for this: it reports "account is not signed in" even when the
integration works (checked 28.10.2026, CLI 2.41). If `op.sh vault list` fails, ask
the user to unlock 1Password, turn the integration on, and approve the dialog
themselves; `op.sh account list` showing their account means the integration is on.
The app asks again for each new shell and after 10 idle minutes, so run every
call of one stage in a single shell command: all reads for the check before the
summary (publishing.md step 3) in one, and the re-check, upload and verification
in another. Say before each such command that 1Password will ask.

**No prompts at all: a service account.** When the user wants runs without Touch
ID (or the `publishCollection` preference is `auto`), suggest this once, and
leave every step to them:

1. In 1Password (on the web: Developer > Directory > Service Accounts > New), a
   1Password admin or a member allowed to create service accounts creates one
   with read and write access to the product's vault only.
2. The user stores its token in the macOS Keychain themselves, in their own
   terminal (it asks for the token without echoing it):
   `security add-generic-password -U -a "$USER" -s qa-agent-1password -w`
3. The first `op.sh` call may show macOS's "security wants to use your
   keychain" dialog once; "Always Allow" ends it.

Never ask for the token in the chat, never type, print or store it yourself, and
never pass a token you found somewhere. To go back to the app integration, the
user deletes the Keychain item (`security delete-generic-password -s
qa-agent-1password`). A service account can't archive items or see vaults it
wasn't given; if a command fails with a permission error, say so and name the
vault.

## Commands

Checked against 1Password CLI 2.41 on 28.10.2026: several files in one item,
replacing and removing one, a zip, notes and tags. If one fails with an unknown
flag, check `op.sh item --help` and say in the report what differed.

| Step | Command |
| --- | --- |
| Find the item, check for duplicates | `op.sh item list --vault "<vault>" --format json`, then match `title` exactly. Two items with the same title: stop and ask which one, then use its `id` instead of the title from then on |
| Read the published version and files | `op.sh item get "<item>" --vault "<vault>" --format json`: `category`, `version`, `updated_at`, `last_edited_by` (a user id; show it as is), `files[].name`, `tags`. Not found: first upload |
| Download one file | `op.sh read "op://<vault>/<item>/<file name>" --out-file "<absolute path>"`, then check the file is there and not empty |
| Create the item | `op.sh item create --category "Secure Note" --vault "<vault>" --title "<item>" --tags "<product>,<client>,qa-agent" 'notesPlain=<notes>' '<name>[file]=<path>' ...`, one file assignment per file |
| Update it (one new version) | `op.sh item edit "<item>" --vault "<vault>" --tags "<...>" 'notesPlain=<notes>' '<name>[file]=<path>' ... '<old name>[delete]' ...`: a file with that name is replaced in place, a new name is added, `[delete]` removes one the repo no longer has. All changes in one call make one version |

**Dots in file names must be escaped** in assignments, or `op` reads the dots as
section and field separators and the file ends up named just `json` (seen on
28.10.2026). Write `'stage\.postman_environment\.json[file]=/path/to/file'`, in
single quotes. `op.sh read` and `files[].name` use the plain name.

## Upload (publishing.md step 5)

In one shell command, for each part going to 1Password:

1. Read the version again (`op.sh item get`); if it differs from the one shown in the
   summary, stop and ask again.
2. Upload: `op.sh item create` when the item doesn't exist yet, otherwise one
   `op.sh item edit` with every file that changed or is new, `[delete]` for each the
   repo no longer has, and the refreshed notes and tags. Leave out a part whose
   files are all unchanged: uploading the same content only adds a version.
3. Read the version once more: it must be one higher than before (or 1 for a new
   item), and `files[].name` must list exactly the files you meant. Download each
   uploaded file back with `op.sh read` into a scratch folder and compare its
   checksum with what you sent; then delete the scratch copies. Otherwise say so
   instead of reporting success.

## Download (ticket mode, publishing.md "Downloading the published collection")

1. `op.sh item get` for `collectionItem`: note `id`, `version` and the file name.
2. `op.sh read` the collection file. Postman/Insomnia: into
   `<run folder>/published-collection/<collectionPath>/<file name>`. Bruno: into
   `<run folder>/published-base.zip`, then extract as publishing.md says.
3. When environments go to 1Password, `op.sh read` each of the environments item's
   `files[].name` into `<run folder>/published-environments/environments/`.
4. Record `target: "1password"`, `vault`, `item`, `id` and `version` for each part
   in `published-base.json`.

## Report

Name the vault, each item and its new version (e.g. "Emtethal Postman Collection,
vault Takamol-Compliance, version 4 → 5") and the files in it, and how to get
them: the 1Password app (the item's History shows every version) or
`op.sh read "op://<vault>/<item>/<file>"`.
