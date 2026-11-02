# The product config's `api` block

Read by `testing-api` in step 0 when the config has one of the optional fields
below, or a field isn't clear. The product config is the file in
`~/.claude/environments/*.json` (or `$CLAUDE_CONFIG_DIR/environments/`) whose
`api` block matches the request, the same per-product config `qa-tester` uses.

```json
"api": {
  "client": "bruno",
  "repo": "~/Projects/<repo>   (optional: omit when the collection lives only where it is published, see \"No `repo`\")",
  "collectionPath": "bruno",
  "defaultEnvironment": "staging",
  "ticketEnvironment": "<optional: environment ticket mode proposes and asks to confirm; absent = ask every time>",
  "knownCaveats": ["<free text about stateful/order-dependent cases, if any>"],
  "knownCaveatsFile": "<filename of a fuller markdown doc kept next to this config in <workDir>/config/ — use this instead of/alongside knownCaveats when the caveat list is long enough that keeping it as JSON strings risks drifting out of sync with a richer doc>",
  "publish": {
    "collection": "1password | confluence | none",
    "environments": "1password | confluence | none",
    "onePassword": {
      "vault": "<vault>",
      "collectionItem": "<Product> <Client> Collection",
      "environmentsItem": "<Product> <Client> Environments"
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
published: nobody keeps it in a shared git repo, so a local folder would only
duplicate it. Then `publish.collection` and `publish.environments` must both be
`1password` or `confluence`, and `collectionPath` is the collection's path inside
the published copy (`.` when absent). Every run, generic ones too, downloads the
published copy into its run folder and works there; new cases reach the team
when the run publishes. If the target can't be read, the run uses the newest
copy an earlier run left ([publishing.md](./publishing.md), "When the download
isn't possible"). Keep `repo` when the collection lives in a git repo the team
shares (a Bruno collection inside the backend repo, say): the repo is then where
changes are reviewed, and publishing only hands out a copy.

`publish` says where the collection and its environments are published, see
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
