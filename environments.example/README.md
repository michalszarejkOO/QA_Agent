# environments/ config shape

`~/.claude/environments/` (created by `./setup.sh`; `environments/` in this repo
is a gitignored link to it) is the index of products: one JSON file per
product/environment, e.g. `osh-staging.json` or `mowaamah-demo.json`. `qa-tester`
and `testing-api` match a ticket key or a repo name against each file's
`ticketPrefixes` to find the right one — never hardcode credentials or
environment facts into the skills/agent themselves.

Each product file is a **symlink** to the real file in that product's working
directory, `<workDir>/config/<product>-<env>.json`, the same way skills are linked
into `~/.claude/skills/`. So everything about a product (config, project skill,
evidence, run output) lives in its own folder and goes away with it. Deleting
a project folder leaves a dangling link: the validator reports it and
`./setup.sh` removes it. Only the shared files, `atlassian-connectors.json` and
`evidence.json`, are real files in `~/.claude/environments/`.

Run `./setup.sh` first, then add products with the `configure-project` skill (or by
hand: write `<workDir>/config/<product>-<env>.json` and symlink it into
`~/.claude/environments/`), following the two shapes below (mix and match fields — both examples in one file is fine for
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
  saved as `environments/evidence.json`. It sets whether `qa-tester` records run
  evidence (a video per scenario, sorted into happy path, error handling and
  edge cases, plus a separate folder per bug with its screenshot and video)
  automatically (`"mode": "auto"`, the default) or asks first (`"ask"`). The
  evidence itself goes to the product's `workDir` (below), not to a folder set
  here; an optional `"dir"` is only a fallback for runs that match no product
  config. Web videos need a Playwright MCP server named
  `playwright-video` started with `--caps=devtools`. Add it once with
  `claude mcp add --scope user playwright-video -- ~/.claude/skills/testing-apps/scripts/playwright-mcp.sh --isolated --caps=devtools`.
  The wrapper gives each Claude window its own folder for Playwright's
  automatic output files instead of the folder Claude was opened in (see
  `skills/testing-apps/references/adapters/web.md`).
  Mobile videos use `agent-device record`.

## Working directory (`workDir`)

Every product file has a required top-level `"workDir"`: one folder per product
where every file a run produces lands, so switching projects means deleting one
folder instead of hunting across the machine. Several files for the same product
(one per environment) share the same `workDir`. Skills create the subfolders
on demand:

```
<workDir>/
  qa-evidence/<ticket or session>/<YYYY-MM-DD>-<web|ios|android>/   testing-apps videos and bug screenshots
  api-runs/<ticket or YYYY-MM-DD-<env>>/                            testing-api CLI results, report, exported collection zip
    confluence-collection/                                          the collection downloaded from Confluence; ticket runs work from here
  worktrees/<ticket or branch>/                                     fresh checkouts for mobile builds and branch API runs
  reports/                                                          create-quality-metrics HTML dashboards
```

A product with no collection repo of its own can keep its collection inside
`workDir` too (e.g. `<workDir>/postman/`, pointed at by `api.repo`). Code repos
may live inside it or anywhere else; `repo` fields keep pointing at them either
way.

## Project skill (`projectSkill`)

Optional but offered for every product: the folder of a skill that holds
everything specific to the product that isn't config (gotchas, test-data rules,
workflows, links, lessons from runs). It lives inside `workDir` (usually
`<workDir>/skills/<product>/`) and is symlinked into `~/.claude/skills/`, so it
loads in any session. `qa-tester`, `testing-apps` and `testing-api` read its
`SKILL.md` once they've matched the product, and propose additions to it instead
of to this repo's skills or Claude's memory. `configure-project` scaffolds it from
`skills/configure-project/assets/project-skill-template.md`.

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
