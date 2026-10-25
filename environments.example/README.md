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
  backoffice surfaces, login method, Basic Auth, pools of test credentials. A
  mobile surface sets `platform` instead of `appUrl`, plus `installMode`. Runs
  test the installed TestFlight/Google Play/App Tester build by default;
  `installMode` only applies when the request asks for a local build: `clean`
  (default, uninstall and rebuild) or `update` (fresh build over the existing
  app, data kept).
- [`api-collection.example.json`](./api-collection.example.json) — a product
  `testing-api` runs an API collection against: which client (Bruno, Postman, or
  Insomnia), repo path, default environment, known stateful-case caveats, and
  (optionally) a Confluence tracker page to publish results to.

- [`evidence.example.json`](./evidence.example.json) — one file for all products,
  saved as `environments/evidence.json`. It sets where `qa-tester` saves run
  evidence (a video per scenario, sorted into happy path, error handling and
  edge cases, plus a separate folder per bug with its screenshot and video)
  and whether it records automatically (`"mode": "auto"`, the default) or asks
  first (`"ask"`). Web videos need a Playwright MCP server named
  `playwright-video` started with `--caps=devtools`. Add it once with
  `claude mcp add --scope user playwright-video -- npx -y @playwright/mcp@latest --isolated --caps=devtools`.
  Mobile videos use `agent-device record`.

Runs without a ticket (generic API runs, standalone app runs) test the
product's staging-like branch. They detect it from merged MRs/PRs with
`skills/testing-apps/scripts/detect_env_branch.py`. To skip detection, set an
optional top-level `"targetBranch"` (e.g. `"staging"`) in the product's file.
Leave it out to keep detection on.

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
