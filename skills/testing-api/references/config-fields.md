# The product config's `api` block

Read by `testing-api` in step 0 when the config has one of the optional fields
below, or a field isn't clear. The product config is the file in
`~/.claude/environments/*.json` (or `$CLAUDE_CONFIG_DIR/environments/`) whose
`api` block matches the request, the same per-product config `qa-tester` uses.

```json
"api": {
  "client": "bruno",
  "repo": "~/Projects/<repo>   (optional: omit when the collection lives only where it is published, see \"No `repo`\")",
  "localCopy": "<optional, with no repo: folder kept at the latest published version, e.g. <workDir>/postman>",
  "collectionPath": "bruno",
  "testsCollection": "<optional, Postman only: name of the tests collection kept next to the main one, see \"The tests collection\">",
  "defaultEnvironment": "staging",
  "ticketEnvironment": "<optional: environment ticket mode proposes and asks to confirm; absent = ask every time>",
  "knownCaveats": ["<free text about stateful/order-dependent cases, if any>"],
  "knownCaveatsFile": "<filename of a fuller markdown doc kept next to this config in <workDir>/config/ — use this instead of/alongside knownCaveats when the caveat list is long enough that keeping it as JSON strings risks drifting out of sync with a richer doc>",
  "publish": {
    "collection": "1password | confluence | none",
    "environments": "1password | confluence | none",
    "tests": "<with testsCollection: 1password | none>",
    "onePassword": {
      "vault": "<vault>",
      "collectionItem": "<Product> <Client> Collection",
      "environmentsItem": "<Product> <Client> Environments",
      "testsItem": "<Product> <Client> Tests   (when tests is 1password)"
    }
  },
  "confluence": {
    "cloudId": "<site>",
    "spaceKey": "<space>",
    "parentId": "<folder page id>",
    "pageTitle": "<fixed page title>",
    "attachmentName": "<fixed zip filename>",
    "secondaryAttachments": [
      { "name": "<fixed filename>", "sourcePath": "<path relative to repo root>" }
    ],
    "envRefreshProcedure": "<optional filename of a doc kept next to this config in <workDir>/config/, describing how to mint live values into a secondaryAttachments file before export>"
  }
}
```

**No `repo`.** `repo` is optional when the collection lives only where it is
published: nobody keeps it in a shared git repo. Then `publish.collection` and
`publish.environments` must both be `1password` or `confluence`, and
`collectionPath` is the collection's path inside the published copy (`.` when
absent). Every run, generic ones too, downloads the published copy into its run
folder and works there; new cases reach the team when the run publishes. Keep
`repo` when the collection lives in a git repo the team shares (a Bruno
collection inside the backend repo, say): the repo is then where changes are
reviewed, and publishing only hands out a copy.

**`localCopy`** (with no `repo`, recommended): a folder, usually
`<workDir>/postman/` or `<workDir>/<client>/`, that always holds the latest
published version, laid out like the published copy (`<collectionPath>/` with
`environments/`). It needn't be a git repo. Runs keep it current: after every
publish, and when a run downloads a newer version than it holds
([publishing.md](./publishing.md), "The local copy"). When the target can't be
read, the run starts from it. Other files in it (upload fixtures a request
points at, say) are left alone. It holds environments with live values: keep it
out of any git repo with a remote.

**The tests collection** (`testsCollection`, optional, Postman only). Test
cases go into a collection of their own, so the main one stays readable for
people working in the app. Both files sit in `<collectionPath>` and share
`environments/`; the tests file is `<testsCollection>.postman_collection.json`
and its `info.name` is `testsCollection`. Name it so nobody mixes the two up
after an import: the main collection's name with `_TESTS` (`ACME_TESTS` next to
`ACME`).

- **Main collection:** one request per endpoint, in the folder of its domain
  (`/v1/users/...` in `Users`), named without a ticket key (the key goes into
  its description), with a working happy-path request and no saved examples.
  Folders of whole flows (several endpoints in order) stay here.
- **Tests collection:** the cases runs execute, with assertions. The same
  domain folders as the main collection, inside them one folder per endpoint
  (e.g. `PUT /v1/users/me/phone`), the cases inside that. Never a folder named
  after a ticket; a case names its ticket in its description.
- Every run executes the tests collection, generic ones too; the main
  collection runs only when the user asks for it.
- Publishing has a third part, `tests` (`publish.tests`, `1password` or `none`),
  in its own item (`onePassword.testsItem`). Without `repo` it must be
  `1password`, like the other two.

Without `testsCollection` nothing changes: generated cases go into the main
collection, as before.

**Several main collection files.** `<collectionPath>` may hold more than one
`*.postman_collection.json` (one product with two collections). All of them
except the tests collection make up part `collection`: published together in
`collectionItem`, downloaded together, compared per file. Without
`testsCollection`, a run executes the file the user or the project skill names,
otherwise each one in turn, and the report has a row per file.

`publish` says where the collection, its environments and the tests collection are published, see
[publishing.md](./publishing.md); `confluence` is needed only when a
part goes there. `knownCaveatsFile`, `secondaryAttachments`, and
`envRefreshProcedure` are all optional — most products need none of them. See
[confluence-publish.md](./confluence-publish.md) for how the last two
are used, and [adapters/bruno.md](./adapters/bruno.md) for
`knownCaveatsFile`.

**Finding `knownCaveatsFile` and `envRefreshProcedure`:** they belong next to
the product's real config file, in `<workDir>/config/` (the file in
`~/.claude/environments/` is a link to it). Look there first. If the file is
only in `~/.claude/environments/` (older installs kept it there), use it, and
tell the user it belongs in `<workDir>/config/` and that "update QA_Agent"
moves it. If it's in neither place, say so before going on: without the env
refresh doc the published environment file keeps expired values.
