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
| `collectionItem` | Title of the Document item holding the collection zip, by convention `<Product> <Client> Collection` (e.g. `Emtethal Postman Collection`) |
| `environmentsItem` | Title of the Document item holding the environments zip, by convention `<Product> <Client> Environments` |

Each part is one Document item, so 1Password keeps its own version history and
`version` number per part.

## Signing in is the user's

Every `op` call needs an unlocked 1Password with the CLI integration on (1Password
app > Settings > Developer > "Integrate with 1Password CLI"). Check sign-in with
`op vault list`: with the app integration, 1Password shows its approval dialog for
it, so tell the user to approve it first. Don't use `op whoami` for this: it reports
"account is not signed in" even when the integration works (checked 28.10.2026,
CLI 2.41). If `op vault list` fails, ask the user to unlock 1Password, turn the
integration on, and approve the dialog themselves; `op account list` showing their
account means the integration is on. Never ask for, type, or store their password,
and never pass a service-account token you found somewhere.

## Commands

The commands below were checked against 1Password CLI 2.41 on 28.10.2026 (flags,
and the `version` / `updated_at` / `last_edited_by` fields of `op item get`). If one
fails with an unknown flag, check `op document --help` / `op item --help` and say in
the report what differed.

| Step | Command |
| --- | --- |
| Find the item, check for duplicates | `op item list --vault "<vault>" --categories Document --format json`, then match `title` exactly. Two items with the same title: stop and ask which one, then use its `id` instead of the title from then on |
| Read the published version | `op item get "<item>" --vault "<vault>" --format json`: `version`, `updated_at`, `last_edited_by` (a user id; show it as is). Not found: first upload |
| Download | `op document get "<item>" --vault "<vault>" --out-file "<absolute path>"`, then check the file is there and not empty |
| First upload (asks first, like every upload) | `op document create "<local zip>" --vault "<vault>" --title "<item>" --file-name "<zip name>"` |
| Upload a new version | `op document edit "<item>" "<local zip>" --vault "<vault>" --file-name "<zip name>"` |

## Upload (publishing.md step 5)

For each part going to 1Password:

1. Read the version again (`op item get`); if it differs from the one shown in the
   summary, stop and ask again.
2. Upload with `op document edit`, or `op document create` when the item doesn't
   exist yet.
3. Read the version once more: it must be one higher than before (or 1 for a new
   item). Otherwise say so instead of reporting success.

## Download (ticket mode, publishing.md "Downloading the published collection")

1. `op item get` for `collectionItem`: note `id` and `version`.
2. `op document get` into `<run folder>/published-base.zip`.
3. The same for `environmentsItem` when environments go to 1Password, into
   `<run folder>/published-environments.zip`, extracted into
   `<run folder>/published-environments/`.
4. Record `target: "1password"`, `vault`, `item`, `id` and `version` for each part
   in `published-base.json`.

## Report

Name the vault, each item and its new version (e.g. "Emtethal Postman Collection,
vault UCP QA, version 4 → 5"), and how to get it: 1Password app, or `op document
get "<item>" --vault "<vault>"`.
