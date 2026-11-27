#!/usr/bin/env python3
"""Finds which long-lived branch of a repo acts as its staging/integration branch,
by reading merged merge/pull requests from git history.

Usage: python3 -I detect_env_branch.py <repo> [--days N] [--recent N] [--no-fetch]

Reads merge-commit subjects, so it works for any host without an API client:
  GitLab:    Merge branch 'feature-MWA-520' into 'demo'
  GitHub:    Merge pull request #123 from owner/feature-x
  Bitbucket: Merged in feature-x (pull request #12)
A squash or rebase merge leaves no merge commit, so a repo merged only that way
shows no MRs; the output says so instead of guessing.

Prints one row per long-lived branch, the suggested staging-like branch (the
non-production branch receiving the most feature MRs) with its reason, and the most recent MRs merged into it (their ticket keys are the
context for a run that has no ticket of its own).
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

KNOWN_LONG_LIVED = {
    "main", "master", "develop", "development", "dev", "stage", "staging",
    "demo", "qa", "test", "uat", "preprod", "pre-prod", "release", "integration",
}
PRODUCTION_NAMES = {"main", "master", "prod", "production"}
# Preference among non-production branches when merge activity ties.
STAGING_NAME_RANK = ["staging", "stage", "demo", "uat", "qa", "preprod", "pre-prod", "test", "develop", "dev", "development", "integration"]

MERGE_PATTERNS = [
    re.compile(r"^Merge branch '(?P<src>[^']+)' into '(?P<dst>[^']+)'"),
    re.compile(r"^Merge branch '(?P<src>[^']+)'(?: of \S+)? into (?P<dst>\S+)"),
    re.compile(r"^Merge pull request #\d+ from [^/\s]+/(?P<src>\S+)"),
    re.compile(r"^Merged in (?P<src>\S+) \(pull request #\d+\)"),
]
TICKET_KEY = re.compile(r"\b([A-Za-z][A-Za-z0-9]+-\d+)\b")


def git(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def remote_branches(repo):
    names = []
    for line in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").splitlines():
        name = line.removeprefix("origin/")
        if name and name not in ("HEAD", "origin"):
            names.append(name)
    return names


def default_branch(repo):
    try:
        ref = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()
        return ref.removeprefix("origin/")
    except RuntimeError:
        return None


def incoming_merges(repo, branch, since):
    """First-parent merge commits on origin/<branch> since `since`: (date, src, subject)."""
    log = git(repo, "log", f"origin/{branch}", "--merges", "--first-parent",
              f"--since={since.isoformat()}", "--format=%cI%x09%s")
    merges = []
    for line in log.splitlines():
        date_s, _, subject = line.partition("\t")
        src = None
        for pattern in MERGE_PATTERNS:
            m = pattern.match(subject)
            if m:
                src = m.group("src")
                break
        # git prints UTC as "Z", which fromisoformat only accepts from Python 3.11
        merges.append((datetime.fromisoformat(date_s.replace("Z", "+00:00")), src, subject))
    return merges


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo")
    parser.add_argument("--days", type=int, default=60, help="merge history window (default 60)")
    parser.add_argument("--recent", type=int, default=10, help="recent MRs to list for the suggested branch")
    parser.add_argument("--no-fetch", action="store_true", help="skip git fetch (offline)")
    args = parser.parse_args()

    if not args.no_fetch:
        try:
            git(args.repo, "fetch", "origin", "--prune", "--quiet")
        except RuntimeError as e:
            print(f"warning: fetch failed, using local remote refs ({e})", file=sys.stderr)

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    branches = remote_branches(args.repo)
    default = default_branch(args.repo)

    # A feature branch cut from an integration branch inherits its first-parent merge
    # history, so merge counts alone can't tell them apart. Long-lived means: a known
    # name, the default branch, or a branch that MR messages name as their target
    # ('into X') at least 3 times and that carries no ticket key in its own name.
    target_counts = {}
    for line in git(args.repo, "log", "--remotes=origin", "--merges",
                    f"--since={since.isoformat()}", "--format=%s").splitlines():
        m = MERGE_PATTERNS[0].match(line) or MERGE_PATTERNS[1].match(line)
        if m:
            dst = m.group("dst").strip("'")
            target_counts[dst] = target_counts.get(dst, 0) + 1
    long_lived = {
        b for b in branches
        if b in KNOWN_LONG_LIVED or b == default
        or (target_counts.get(b, 0) >= 3 and not TICKET_KEY.search(b))
    }
    rows = {b: incoming_merges(args.repo, b, since) for b in long_lived}

    print(f"Repo: {args.repo}   window: last {args.days} days   default branch: {default or 'unknown'}")
    print(f"{'branch':<14}{'MRs':>5}{'feature MRs':>13}  {'last MR':<12}promoted from")
    for b in sorted(rows, key=lambda x: -len(rows[x])):
        merges = rows[b]
        promos = sorted({src for _, src, _ in merges if src in long_lived})
        features = sum(1 for _, src, _ in merges if src and src not in long_lived)
        last = max((d for d, _, _ in merges), default=None)
        print(f"{b:<14}{len(merges):>5}{features:>13}  {str(last.date()) if last else '-':<12}"
              f"{', '.join(promos) or '-'}")

    production = {b for b in rows if b in PRODUCTION_NAMES or b == default}
    candidates = []
    for b, merges in rows.items():
        if b in production:
            continue
        feature_dates = [d for d, src, _ in merges if src and src not in long_lived]
        if feature_dates:
            rank = STAGING_NAME_RANK.index(b) if b in STAGING_NAME_RANK else len(STAGING_NAME_RANK)
            candidates.append((len(feature_dates), max(feature_dates), -rank, b))

    print()
    if not candidates:
        print("Suggested staging-like branch: NONE — no non-production branch received feature MRs "
              "in the window (squash/rebase-only history, or a single-branch flow). Ask the user.")
        return 2
    # The branch most feature MRs land in is where integrated work gets tested;
    # recency, then name rank, break ties.
    candidates.sort(reverse=True)
    count, last, _, chosen = candidates[0]
    print(f"Suggested staging-like branch: {chosen}")
    print(f"Reason: non-production branch receiving the most feature MRs "
          f"({count} in {args.days} days, last {last.date()}); production treated as: "
          f"{', '.join(sorted(production)) or 'none detected'}")
    others = [c[3] for c in candidates[1:]]
    if others:
        print(f"Other non-production branches with feature MRs: {', '.join(others)}")

    print(f"\nRecent MRs into {chosen}:")
    for d, src, subject in rows[chosen][: args.recent]:
        keys = sorted({k.upper() for k in TICKET_KEY.findall(src or subject)})
        print(f"  {d.date()}  {src or subject}  {'[' + ', '.join(keys) + ']' if keys else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
