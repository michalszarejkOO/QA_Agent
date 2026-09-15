# environments/ config shape

`environments/` (a real directory on your machine, gitignored here — see the root
`.gitignore`) holds one JSON file per product/environment, e.g.
`osh-staging.json` or `mowaamah-demo.json`. `qa-tester` and `testing-bruno-api`
match a ticket key or a repo name against each file's `ticketPrefixes` to find the
right one — never hardcode credentials or environment facts into the skills/agent
themselves.

Run `./setup.sh` first, then create your own files under `environments/` following
the two shapes below (mix and match fields — both examples in one file is fine for
a product that has both a UI and a Bruno API collection).

- [`app-with-ui.example.json`](./app-with-ui.example.json) — a product `qa-tester`
  drives through a browser: app/backoffice surfaces, login method, Basic Auth,
  pools of test credentials.
- [`api-with-bruno.example.json`](./api-with-bruno.example.json) — a product
  `testing-bruno-api` runs a Bruno collection against: repo path, default
  environment, known stateful-case caveats, and (optionally) a Confluence tracker
  page to publish results to.

Never commit real credentials, even to a private repo — that's exactly why
`environments/` itself stays gitignored and only these scrubbed examples are
tracked.
