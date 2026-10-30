# Resolving the target branch and environment (runs without a ticket)

Used by generic `testing-api` runs ("run the API tests") and standalone
`testing-apps` runs (exploratory, dogfooding). Neither has a ticket or PR, so
they test the product's staging-like branch, and the environment deployed from
it, instead of whatever happens to be checked out. A ticket-driven run doesn't
use this: its ticket and PR decide the branch.

## Which branch

First match wins:

1. **The user's message** names a branch or environment ("test stage", "run
   against uat").
2. **`targetBranch` in the product's environment config**, which pins the branch
   and skips detection. Set it when detection picks wrong.
3. **Detection from merged MRs/PRs:**
   ```
   python3 -I ~/.claude/skills/testing-apps/scripts/detect_env_branch.py <repo>
   ```
   It fetches `origin` and reads merge-commit messages (GitLab, GitHub and
   Bitbucket formats, no API client needed). It treats the default branch and
   `main`/`master`/`prod` as production, and suggests the non-production
   long-lived branch that receives the most feature MRs. That's the branch
   integrated work gets tested on.
4. **Detection found nothing** (exit code 2: squash-only history or a
   single-branch flow): for API runs, use `api.defaultEnvironment`; otherwise
   ask the user. Never pick production by default.

Tell the user which branch you picked and why (the script's "Reason" line, or
the config/user override) before running anything. If the script lists other
non-production branches, name them in one line so the user can redirect.

## From branch to environment

Branch names and environment names don't always match. A `demo` branch can be
deployed to an environment the mobile build calls `stage`. Resolve them in this
order:

- **API collection:** use the collection environment with the same name as the
  branch (e.g. `bruno/environments/demo.yml` for `demo`). Prefer a `-populated`
  variant if the adapter says to. No same-name environment: use
  `api.defaultEnvironment` and say so.
- **Web:** use the product's environment config whose `environment` field
  matches the branch, and take its `surfaces.<name>.appUrl`. If none matches, ask
  for the URL and don't fall back to another environment's URL.
- **Mobile:** build from the branch (fresh worktree at `origin/<branch>`, under
  `<workDir>/worktrees/`) with
  the config's build command. The build command decides which backend the app
  talks to; don't swap build variants to match the branch name.

## Context from recent MRs

The script also lists the most recent MRs merged into the chosen branch, with
their ticket keys. A run without a ticket uses them as its context:

- Read the summaries of the last ~5 tickets (Jira, via the connector the product
  config names). If the Jira fetch fails, use the MR branch names.
- **API runs:** in the report's Notes, name which recently merged tickets the
  executed folders cover, and which have no cases in the collection yet.
- **App runs:** explore the areas those tickets changed first, then the rest.
- List the branch, commit (`git rev-parse --short origin/<branch>`) and the
  recent MRs used in the run log and the end summary.
