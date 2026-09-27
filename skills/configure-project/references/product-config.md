# Configuring one product

Produces one `environments/<product>-<environment>.json` file. Re-read
`environments.example/app-with-ui.example.json` and
`environments.example/api-collection.example.json` before generating anything — this
file describes the question flow, those two files are the actual field-shape
contract.

## Question flow

Ask these in order; skip a whole block the moment the user says it doesn't apply
(e.g. no UI → skip the `surfaces` block entirely, no API collection → skip `api`
entirely — a product needs at least one of the two, per `validate_environments.py`).

1. **Identity**
   - Product name (short, lowercase-hyphenated — becomes part of the filename and
     the `product` field, e.g. `acme`, `acme-api`).
   - Environment this file targets (`staging`, `demo`, `local`, etc. — one file per
     environment; a product tested against two environments gets two files).
   - Ticket prefix(es) — the Jira project key(s) this repo's tickets use (e.g.
     `["ACME"]`). This is the field every other skill matches a ticket against to
     find this file, so get it exactly right (case-sensitive, matches the Jira
     project key, not the repo name).

2. **Jira site** (skip if the user opted out of Atlassian integration in
   [connectors.md](./connectors.md)) — which registered connector name (from
   `atlassian-connectors.json`) reaches this product's Jira, and what its site is
   (read straight from that file, don't re-ask/re-derive). Write both:
   ```json
   "jira": { "site": "<site>", "connector": "<connector-name>" }
   ```

3. **Does this product have a UI you'd drive with a browser or a mobile app?**
   If yes, for each surface (there may be more than one — e.g. a customer app and an
   internal backoffice):
   - Surface name (`app`, `backoffice`, etc.), its URL, and its repo path
     (`~/Projects/<repo>`).
   - Sign-in method: a single fixed test account, or a pool of interchangeable test
     credentials (e.g. multiple valid test IDs grouped by category)? Either is fine —
     `qa-tester` already knows to pick randomly from a pool vs. use a fixed
     role-labeled account; just capture which shape this product actually has and any
     role labels that exist (admin vs. auditor, etc.).
   - Is there a server-level Basic Auth wall in front of the whole environment,
     separate from the app's own sign-in form? If yes, capture `basicAuth`.
   - Anything non-obvious a future test run would need to know (which surface a given
     kind of ticket usually touches, how to find the feature branch if the platform's
     PR API is unreachable, which credential group to prefer by default) → the free-form
     `notes` field. Don't leave this blank if there's anything at all worth saying —
     it's the field `qa-tester` explicitly relies on to disambiguate.

4. **Does this product have a committed API test collection?**
   If yes:
   - Which tool: Bruno, Postman, or Insomnia (`api.client`).
   - Repo path and the collection's path within it (`api.repo`, `api.collectionPath`
     — for Postman this is a directory containing both the `.postman_collection.json`
     and an `environments/` folder of `.postman_environment.json` files).
   - Which environment name is the **shared/stakeholder-visible one** — the one
     other people (reviewers, the ticket, a tracker page) can verify results
     against. This becomes `api.defaultEnvironment`. Ask explicitly rather than
     assuming it's called `demo` — `testing-api`'s ticket mode hardcodes testing
     against whatever this field says is default, and a team whose shared
     environment is called `staging`/`uat`/something else needs that reflected here,
     not silently defaulted to a name that doesn't exist for them.
   - Any known stateful/order-dependent test cases worth flagging up front
     (`api.knownCaveats`) — optional, skip if none come to mind yet.
   - Confluence tracker page for publishing results — skip entirely if not wanted
     (this makes the whole `api.confluence` block absent, which `testing-api` treats
     as "no publish step", not an error). If wanted: cloudId (the resolved site from
     step 2), space key, parent page id, a fixed page title, and a fixed attachment
     filename for the exported collection zip.

5. **Assemble and confirm.** Merge whichever of `surfaces`/`api` blocks apply into
   one JSON object shaped exactly like the example files (both together if the
   product has both), show it to the user, and only write it after they confirm —
   substitute `REPLACE_ME` for any password they didn't want to paste inline, and
   tell them plainly which fields still need manual editing before the file is
   fully live.

6. **Write to `environments/<product>-<environment>.json`.** If a file with that
   exact name already exists, show the diff and confirm before overwriting.
