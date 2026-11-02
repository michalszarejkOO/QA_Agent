# Finding the pull request

Read by `qa-tester` when the change isn't a GitHub PR it can fetch with `gh`.

- **Bitbucket PR URL:** try `curl` or the Bitbucket REST API first.
- **No PR linked on the ticket, or the repo is private and the platform's API is
  unauthenticated or unreachable:** don't treat that as a dead end before trying
  `git`. With SSH access to the remote, grep `git ls-remote origin` for the
  ticket key (or PR number) to find the feature branch, then diff it against
  the base branch. This is a first-class way to locate the change, not a
  last-resort fallback, especially for products whose environment config says
  PRs are routinely unlinked there.
- A diff or change summary already pasted into the brief: use it directly
  instead of re-fetching.

Only report a blocker when neither the platform API nor `git` turns anything up.
