# Finding the pull request

Read when the change isn't a GitHub PR you can fetch with `gh` (SKILL.md, "The PR or branch").

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
- **Read code without moving the user's checkout.** `git fetch`, then read the
  remote branch in place: `git diff origin/<base>...origin/<branch>`,
  `git show origin/<branch>:<path>`, `git log`, `git grep <pattern>
  origin/<branch>`. Never `checkout`, `switch`, `reset` or `pull` in the user's
  clone: it may hold their work, and a detached HEAD left behind confuses the
  next person. (A mobile build from a branch uses its own worktree, see
  testing-apps' mobile adapter.)

Only report a blocker when neither the platform API nor `git` turns anything up.
