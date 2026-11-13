# 016: the collection is published to one of four targets, as one package

## What changed

`api.publish` used to name a place per part (`collection`, `environments` and,
with a tests collection, `tests`: each `1password`, `confluence` or `none`),
with one 1Password item per part (`collectionItem`, `environmentsItem`,
`testsItem`), and a local folder in one of two fields (`api.localCopy` or
`api.publish.localFolder`). Now the product has one `api.publish.target`:

| `target` | What goes where |
| --- | --- |
| `1password` | The package in one vault item |
| `local` | The package in `apiCollectionsFolder` |
| `1password+local` | The package in the vault item, and the published package in `apiCollectionsFolder` |
| `confluence` | The collection without environments on the Confluence page, the package in `apiCollectionsFolder` (not for Insomnia) |

**The package** is one file: for Postman and Bruno a zip
(`<product>-postman-collection.zip`, `<product>-bruno-collection.zip`) with
`<collectionPath>/` holding the main collection, the tests collection when there
is one, and `environments/`; for Insomnia the export file. There is one
1Password item per product, `api.publish.onePassword.item`: the item that held
the collection, so its title and version history stay. The Environments and
Tests items are no longer updated. The local folder has one name,
`api.publish.apiCollectionsFolder`, and always holds the last published package,
extracted, with `.published.json`. Extra environment files and their refresh
doc moved from `api.confluence.secondaryAttachments` / `envRefreshProcedure` to
`api.publish.extraEnvironmentFiles` / `envRefreshProcedure`, since they go into
the package for every target and never to Confluence. Docs:
`skills/testing-api/references/publishing.md`, "The four targets".

## Is it needed

Needed if any product config in `~/.claude/environments/` (or under
`$CLAUDE_CONFIG_DIR`) has an `api.publish` block with `collection`,
`environments` or `tests` instead of `target`, `api.publish.localFolder`,
`api.localCopy`, an `api.confluence` block with `secondaryAttachments` or
`envRefreshProcedure`, or `api.publish.onePassword` with `collectionItem`,
`environmentsItem` or `testsItem`. `validate_environments.py` names each one.

## Fresh install

`skip`: configure-project asks for the target and the folder for every new
product with an API collection (product-config.md step 5).

## Steps

1. **Explain, then pick the target per product (runs by itself where it is
   clear; asks otherwise).** Say in two sentences: the collection, the tests
   collection and the environments now travel together as one package to one
   place, and the local folder has one name. Configs of one product that share
   a collection are handled together. The old local folder is `api.localCopy`
   or `api.publish.localFolder`, whichever is set (both: ask which to keep,
   suggesting `localCopy`). From the old fields:

   | Old `collection` / `environments` | Old local folder | New `target` |
   | --- | --- | --- |
   | `1password` / `1password` | yes | `1password+local` |
   | `1password` / `1password` | no | ask: **`1password+local`** (suggest `<workDir>/<client>/` as the folder) or `1password` |
   | `none` / `none` | yes | `local` |
   | `confluence` / anything | yes | `confluence` |
   | `confluence` / anything | no | `confluence`, after asking for the folder (suggest `<workDir>/<client>/`): the environments now stay there |
   | `none` / `none` | no | ask: one of the four, suggesting **`local`** with `<workDir>/<client>/` |
   | any other mix | any | ask: one of the four, suggesting the collection's old place (`1password` → `1password`, plus `+local` when a local folder is set) |

   For `client: "insomnia"` never pick `confluence` (its export holds the
   environments): ask between the other three. A folder inside the QA_Agent
   repo is not allowed: ask for another one. Say per product what it was and
   what it becomes.
2. **Write (runs by itself after step 1).** In each of that product's real config
   files (`readlink` the link in `~/.claude/environments/`):
   - `api.publish`: set `target`; remove `collection`, `environments` and
     `tests`; in `onePassword` rename `collectionItem` to `item` and remove
     `environmentsItem` and `testsItem` (note their values for step 4). Keep
     `onePassword` even when the target no longer uses it.
   - Set `api.publish.apiCollectionsFolder` to the folder from step 1, and
     remove `api.localCopy` and `api.publish.localFolder`.
   - Move `api.confluence.secondaryAttachments` to
     `api.publish.extraEnvironmentFiles` and `api.confluence.envRefreshProcedure`
     to `api.publish.envRefreshProcedure`, unchanged. Keep the rest of
     `api.confluence` as it is.
   - Keep `api.testsCollection` as it is: the tests collection now goes into
     the package.
   Configs can hold secrets: show only the diff of `api.publish`,
   `api.localCopy` and `api.confluence`, never anything else.
3. **The folder (runs by itself, changes nothing).** For each
   `apiCollectionsFolder` that exists:
   - It holds `.published.json` (an old `localCopy`): nothing to do; it already
     has the new layout.
   - It holds a zip from the old local folder (`<product>-bruno-import.zip`,
     `<product>-bruno-collection.zip`, `*.prev`): leave it. The next publish
     writes the extracted package and `.published.json` next to it and never
     touches files it didn't write. Say the old zip can be removed by hand once
     the next run has written the folder.
4. **Old 1Password items (tells, changes nothing).** Nothing is uploaded,
   archived or deleted here. The next `testing-api` publish puts the one zip
   into `item` and replaces the loose files there; until then a run reads the
   loose files as they are (onepassword-publish.md, "Download"). For each
   product whose config named an `environmentsItem` or `testsItem`, list them
   once: "no longer updated: <vault> / <title>". Say that the user archives
   them in the 1Password app when everyone on the team has updated QA_Agent,
   and that QA_Agent never deletes or archives a 1Password item.
5. **Old attachments on Confluence (tells, changes nothing).** If a product's
   environments used to go to its Confluence page (old `environments:
   "confluence"`, or `secondaryAttachments` there), tell the user those files are
   still attached to the page with whatever tokens they held, and that removing
   them is their call in Confluence.

## Verify

- `python3 -I <QA_Agent>/environments.example/validate_environments.py` passes for
  every product config: no "old shape", "moved to api.publish", `localCopy` or
  `localFolder` error.
- Every product with a `local`, `1password+local` or `confluence` target has
  `api.publish.apiCollectionsFolder`, outside the QA_Agent repo.
- No 1Password item was changed: `op.sh item list --vault "<vault>"` still
  lists every item it listed before.
