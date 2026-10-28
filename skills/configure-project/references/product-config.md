# Configuring one product

Produces one `<workDir>/config/<product>-<environment>.json` file, symlinked into
`~/.claude/environments/`. Re-read
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

2. **Working directory (required).** Ask for the path of this product's working
   directory: the one folder where everything a run produces for it lands, so the
   user can later remove the whole project by deleting that folder. Don't skip
   this and don't fill it in silently. You may suggest a path (the common parent
   of the product's repos, or `~/Projects/<product>`), but the user confirms or
   types their own.
   - If this product already has a file for another environment, reuse its
     `workDir` and just confirm it: one product, one working directory.
   - Create it with `mkdir -p` once the user confirms. Skills create its
     subfolders on demand (`qa-evidence/`, `api-runs/`, `worktrees/`,
     `reports/` — see `environments.example/README.md`), so don't pre-create them.
   - Write it as top-level `"workDir"`, keeping `~` as typed.
   - An existing product file without `workDir` (written before the field
     existed) fails validation. When the user re-runs this wizard for that
     product, ask for its working directory the same way and add only that field,
     showing the diff first.
   - In the questions below, when the product has no repo yet for something the
     skills read (most often an API collection kept outside any code repo),
     suggest a folder inside `workDir` for it (e.g. `<workDir>/postman/`), so
     that also goes away with the project.

3. **Jira site** (skip if the user opted out of Atlassian integration in
   [connectors.md](./connectors.md)) — which registered connector name (from
   `atlassian-connectors.json`) reaches this product's Jira, and what its site is
   (read straight from that file, don't re-ask/re-derive). Write both:
   ```json
   "jira": { "site": "<site>", "connector": "<connector-name>" }
   ```

4. **Does this product have a UI you'd drive with a browser or a mobile app?**
   If yes, for each surface (there may be more than one — e.g. a customer app and an
   internal backoffice):
   - Surface name (`app`, `backoffice`, etc.), its URL, and its repo path
     (`~/Projects/<repo>`).
   - For a mobile surface: no URL. Capture `platform` (e.g. `expo-react-native`),
     the build command, and `installMode`. Explain that runs test the installed
     TestFlight/Google Play/App Tester build by default, and `installMode` only
     applies when a run asks for a local build. Default to `clean`: `clean`
     uninstalls and rebuilds, `update` installs a fresh build over the existing
     app and keeps its data, and `installed` skips the build.
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

5. **Does this product have a committed API test collection?**
   If yes:
   - Which tool: Bruno, Postman, or Insomnia (`api.client`).
   - Repo path and the collection's path within it (`api.repo`, `api.collectionPath`
     — for Postman this is a directory containing both the `.postman_collection.json`
     and an `environments/` folder of `.postman_environment.json` files). If the
     collection lives loose (exported files, no repo), offer to copy it into
     `<workDir>/<client>/` in that layout and point `api.repo` there; keep the
     originals untouched and leave secrets out of the copied environment files.
   - Which environment a plain "run the API tests" should use when no
     staging-like branch can be resolved (`api.defaultEnvironment`). Offer the
     names of the collection's environment files as choices; never assume one is
     called `demo`.
   - Which environment backend tickets are usually tested on: the **shared,
     stakeholder-visible one** that reviewers, the ticket and a tracker page can
     verify results against (`api.ticketEnvironment`). Offer the collection's
     environment names, plus "none, ask every time" for teams whose tickets land
     on different environments. Tell the user that `testing-api`'s ticket mode
     always confirms the environment before running (it proposes this one, or
     asks when the field is absent), because a change may be deployed elsewhere.
   - Any known stateful/order-dependent test cases worth flagging up front
     (`api.knownCaveats`) — optional, skip if none come to mind yet.
   - **Where updated collections and environments go** (`api.publish`, see
     `testing-api`'s `references/publishing.md`). Ask about the two parts
     separately, because environments hold tokens and logins:
     - The collection: `1password` (suggested), `confluence`, or `none` (it only
       stays as a zip in the run folder).
     - The environments: `1password` (suggested), `confluence`, or `none`. If the
       user picks Confluence, say that everyone with access to the page can read
       it, often the client too, and that `testing-api` will stop on anything its
       secret scan flags.
     Tell the user that `testing-api` always shows what goes where and waits for
     their yes before any upload, and checks first that nobody published a newer
     version.
   - **For 1Password:** item names follow `<Product> <Client> Collection` and
     `<Product> <Client> Environments` (e.g. `Emtethal Postman Collection`); offer
     them and let the user change them. Then find the vault:
     1. If `op` isn't installed (`command -v op`), install it:
        `brew install --cask 1password-cli` (without Homebrew, give the user
        https://developer.1password.com/docs/cli/get-started/). It's required
        from now on for this product. Ask the user to unlock 1Password and turn
        on Settings > Developer > Integrate with 1Password CLI, then run
        `op vault list` and tell them to approve the 1Password dialog it opens
        (not `op whoami`: it reports "not signed in" even when this works).
        Never ask for their password.
     2. Look for the items already: `op item list --categories Document --format
        json`, matching `title` exactly. If a teammate created them before, take
        their vault without asking, and say so.
     3. Otherwise list `op vault list --format json` and ask which vault this
        product uses; it must be one the whole team can open.
     Write `api.publish.onePassword` with `vault`, `collectionItem` and
     `environmentsItem`. Don't create the items now: the first upload does, after
     the user's yes.
   - **For a Postman collection with any target:** publishing first syncs the
     repo files with the Postman app through the Postman MCP server (see
     `testing-api`'s `adapters/postman.md`). Check it's signed in
     (`getAuthenticatedUser`); if not, start its `authenticate` and let the user
     approve in the browser. Tell the user the team rule: variables everyone needs,
     keys included, are plain (`default`-type) variables with their value in
     Shared Value, because values in the Value column or the Postman Vault never
     leave their app.
   - **For Confluence** (either part): cloudId (the resolved site from step 3),
     space key, parent page id, a fixed page title, and a fixed attachment
     filename for the exported collection zip, as the `api.confluence` block.
     Without any Confluence part, leave that block out.

6. **Staging-like branch.** For the main repo captured above, run
   `python3 -I skills/testing-apps/scripts/detect_env_branch.py <repo>` and show
   the suggested branch and its reason. Runs without a ticket test that branch.
   If the user says it's wrong, write their branch as top-level `"targetBranch"`.
   Otherwise leave the field out so runs keep detecting it.

7. **Project skill.** Everything specific to this product that isn't config
   (gotchas, test-data rules, workflows, links, lessons from runs) belongs in a
   skill of its own inside `workDir`, never in this repo's skills and never in
   Claude's memory. Ask whether the product already has one.
   - **It has one:** ask for its folder (the one holding `SKILL.md`).
   - **It doesn't:** offer to create `<workDir>/skills/<product>/SKILL.md` from
     [../assets/project-skill-template.md](../assets/project-skill-template.md).
     Fill every `{{…}}` placeholder from the answers already collected (repos as
     table rows, one environments table row per environment file, Jira site and
     connector). Ask the user for the one-paragraph product description. Show
     the result before writing. Offer `git init` and a first commit in
     `<workDir>/skills/`, so later additions are tracked.
   - Either way, link it so it loads in any session:
     `ln -s <skill folder> ~/.claude/skills/<product>` (if something else is at that
     path, show it and ask before replacing it).
   - Write the folder as top-level `"projectSkill"`. Every environment file of
     the same product points at the same skill.
   - If the user declines a project skill, leave `projectSkill` out.

8. **Assemble and confirm.** Merge `workDir`, `projectSkill` and whichever of `surfaces`/`api`
   blocks apply into one JSON object shaped exactly like the example files (both together if the
   product has both), show it to the user, and only write it after they confirm —
   substitute `REPLACE_ME` for any password they didn't want to paste inline, and
   tell them plainly which fields still need manual editing before the file is
   fully live.

9. **Write the file and link it.** The real file goes to
   `<workDir>/config/<product>-<environment>.json` (`mkdir -p <workDir>/config`);
   `~/.claude/environments/` gets only a symlink to it:
   ```
   ln -s <workDir>/config/<product>-<environment>.json ~/.claude/environments/<product>-<environment>.json
   ```
   - If a file with that name already exists in either place, show the diff and
     confirm before overwriting.
   - If `~/.claude/environments/<name>.json` is a real file (written before this
     layout), move it into `<workDir>/config/` and replace it with the symlink,
     after showing the user both paths.
   - If `<workDir>` is inside a git repo, gitignore `config/` there first (see
     the rule in SKILL.md).
