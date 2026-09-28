# environments/ config shape

`environments/` (a real directory on your machine, gitignored here — see the root
`.gitignore`) holds one JSON file per product/environment, e.g.
`osh-staging.json` or `mowaamah-demo.json`. `qa-tester` and `testing-api`
match a ticket key or a repo name against each file's `ticketPrefixes` to find the
right one — never hardcode credentials or environment facts into the skills/agent
themselves.

Run `./setup.sh` first, then create your own files under `environments/` following
the two shapes below (mix and match fields — both examples in one file is fine for
a product that has both a UI and an API collection).

- [`app-with-ui.example.json`](./app-with-ui.example.json) — a product `qa-tester`
  drives through a browser or a mobile app via the `testing-apps` skill: app/
  backoffice surfaces, login method, Basic Auth, pools of test credentials.
- [`api-collection.example.json`](./api-collection.example.json) — a product
  `testing-api` runs an API collection against: which client (Bruno, Postman, or
  Insomnia), repo path, default environment, known stateful-case caveats, and
  (optionally) a Confluence tracker page to publish results to.

Never commit real credentials, even to a private repo — that's exactly why
`environments/` itself stays gitignored and only these scrubbed examples are
tracked.

## Validating your files

`validate_environments.py` checks every `environments/*.json` file for the
structural mistakes above (missing required fields, a bad `api.client`, a
product with neither `api` nor `surfaces`, an incomplete `confluence` block)
and one cross-file consistency check: that a product's `jira.connector` names
a connector that actually exists in `atlassian-connectors.json`, and that the
two files agree on which site it points at.

```
python3 environments.example/validate_environments.py
```

Defaults to `$CLAUDE_CONFIG_DIR/environments` if set, else
`~/.claude/environments` (the same resolution `qa-tester`/`testing-api`/
`routing-qa-tickets` use) — or pass a directory explicitly. This only checks
that the files agree with each other; it can't tell you whether a connector
is actually authorized for the site it claims right now — that drifts
independently of the files and needs a live check with that connector's own
`getAccessibleAtlassianResources` tool.
