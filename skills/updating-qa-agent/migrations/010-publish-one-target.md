# 010: the collection is published to one of four targets, with its environments

## What changed

`api.publish` used to name a place per part (`collection`, `environments`: each
`1password`, `confluence` or `none`, plus an optional `localFolder`), and a run
left several zips behind: the import zip, a collection zip and an environments
zip in the run folder, plus a copy in the local folder. Now the product has one
`api.publish.target`:

| `target` | What goes where |
| --- | --- |
| `1password` | The package (the collection with its environments, Bruno: one zip) in one vault item |
| `local` | The package in `localFolder` |
| `1password+local` | The package in the vault item and in `localFolder` |
| `confluence` | The collection without environments on the Confluence page, the package in `localFolder` (not for Insomnia) |

There is one 1Password item per product, `api.publish.onePassword.item` (was
`collectionItem`); the separate Environments item is gone. Nothing stays in the
run folder. The Bruno package is named `<product>-bruno-collection.zip` everywhere
(the local copy was `<product>-bruno-import.zip`). Extra environment files and
their refresh doc moved from `api.confluence.secondaryAttachments` /
`envRefreshProcedure` to `api.publish.extraEnvironmentFiles` /
`envRefreshProcedure`, since they now go into the package for every target and
never to Confluence. Docs: `skills/testing-api/references/publishing.md`, "The
four targets".

## Is it needed

Needed if any product config in `~/.claude/environments/` (or under
`$CLAUDE_CONFIG_DIR`) has an `api.publish` block with `collection` or
`environments` instead of `target`, an `api.confluence` block with
`secondaryAttachments` or `envRefreshProcedure`, or `api.publish.onePassword` with
`collectionItem` / `environmentsItem`. `validate_environments.py` names each one.

## Steps

1. **Pick the target per product (runs by itself where it is clear; asks
   otherwise).** Configs of one product that share a collection are handled
   together. From the old fields:

   | Old `collection` / `environments` | `localFolder` | New `target` |
   | --- | --- | --- |
   | `1password` / `1password` | no | `1password` |
   | `1password` / `1password` | yes | `1password+local` |
   | `none` / `none` | yes | `local` |
   | `confluence` / anything | yes | `confluence` |
   | `confluence` / anything | no | `confluence`, after asking for `localFolder` (suggest `<workDir>/collection`): the environments now stay there |
   | `none` / `none` | no | ask: one of the four, suggesting `local` with `<workDir>/collection` |
   | any other mix | any | ask: one of the four, suggesting the collection's old place (`1password` → `1password`, plus `+local` when `localFolder` is set) |

   For `client: "insomnia"` never pick `confluence` (its export holds the
   environments): ask between the other three. Say per product what it was and
   what it becomes.
2. **Write (runs by itself after step 1).** In each of that product's real config
   files (`readlink` the link in `~/.claude/environments/`):
   - `api.publish`: set `target`, remove `collection` and `environments`; in
     `onePassword` rename `collectionItem` to `item` and remove `environmentsItem`
     (note its value for step 4); keep `localFolder` (add it when step 1 asked
     for one). Keep `onePassword` even when the target no longer uses it.
   - Move `api.confluence.secondaryAttachments` to
     `api.publish.extraEnvironmentFiles` and `api.confluence.envRefreshProcedure`
     to `api.publish.envRefreshProcedure`, unchanged. Keep the rest of
     `api.confluence` as it is.
   Configs can hold secrets: show only the diff of `api.publish` and
   `api.confluence`, never anything else.
3. **Local folder (runs by itself).** For each `localFolder` that exists, rename
   `<product>-bruno-import.zip` to `<product>-bruno-collection.zip`, and its
   `.prev` the same way. If a `<product>-bruno-collection.zip` is already there,
   keep the newer of the two (by modification time) under that name and the
   other as `.prev`. Touch nothing else in the folder.
4. **The old Environments item in 1Password (asks once, then deletes).** For each
   product whose config named an `environmentsItem`, look for it
   (`op.sh item list --vault "<vault>" --format json`, matching `title` exactly;
   `op.sh` is `testing-api`'s `scripts/op.sh`, see its
   `references/onepassword-publish.md`, "Signing in"). Not found: nothing to do.
   Found: first make sure the environments are not lost:
   - Bruno with a `1password` target: `op.sh item get` the collection item and
     list the zip (`op.sh read` it into a scratch folder, `unzip -l`). It must
     hold `<collectionPath>/environments/`. If it doesn't (published before the
     environments were included), don't delete: say that the next `testing-api`
     run publishes the package with environments, and leave this migration
     pending for that product.
   - Postman with a `1password` target: download the environment files from the
     Environments item and add them to the collection item in one
     `op.sh item edit` (escape the dots, see onepassword-publish.md), then check
     with `op.sh item get` that the collection item lists them.
   - A target without 1Password (`local`, `confluence`): the environments live in
     the package in `localFolder`; check the package there holds them (Bruno:
     `unzip -l`; Postman: the environment files). If there is no package yet,
     say so and ask whether to delete anyway.
   Then show the items to delete (vault, title, last change) and ask once for all
   of them. On yes, `op.sh item delete "<title>" --vault "<vault>" --archive`
   for each: the item leaves the vault and stays in 1Password's Archive, where
   the user can restore or empty it. Never delete without `--archive`. On no,
   leave them and say they are no longer used. Delete the scratch copies.
5. **Old attachments on Confluence (tells, changes nothing).** If a product's
   environments used to go to its Confluence page (old `environments:
   "confluence"`, or `secondaryAttachments` there), tell the user those files are
   still attached to the page with whatever tokens they held, and that removing
   them is their call in Confluence.

## Verify

- `python3 -I <QA_Agent>/environments.example/validate_environments.py` passes for
  every product config: no "old shape" or "moved to api.publish" error.
- Each `localFolder` holds no `*-import.zip`.
- Step 4: each deleted Environments item no longer shows in
  `op.sh item list --vault "<vault>"`, and every product with a `1password`
  target has its environments in its one item.
- `check_setup.py --full` reports no FAIL about the 1Password CLI.
