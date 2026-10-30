#!/usr/bin/env python3
"""Finds files that belong to a product but sit outside its working directory.

Read-only: it lists candidates and where they would go; Claude moves them only
after the user's yes (migration 007, configure-project, checking-qa-agent).

Usage:
  python3 -I find_project_files.py [--json] [--summary]
      (every product config in ~/.claude/environments/)
  python3 -I find_project_files.py --product <name> --workdir <dir>
      [--prefix MWA ...] [--keyword "Assessment Invoice" ...] [--name <repo> ...] [--json]
      (one product, e.g. while configure-project adds it)

Looks only in a few places, never the whole disk: the QA_Agent repo (files git
doesn't track), ~/Desktop, ~/Downloads, ~/Documents (2 levels), and ~/Projects
(3 levels) for run-output folders (api-runs/, qa-evidence/, qa-video/,
.playwright-mcp/, .upload-tmp/) outside every product's workDir. A file is matched
to a product by a ticket key (<PREFIX>-<number>), the product name, a repo or
collection folder name, or a keyword given for that product. QA files that match
no product (collection exports, *-populated.yml, *-quality-*.html, run-output
folders) are listed as unassigned. Files with possible secrets are flagged
(scan_secrets.py; values are never printed).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
ENV_DIR = CLAUDE_DIR / "environments"
REPO = Path(__file__).resolve().parents[3]
SCAN = REPO / "skills" / "testing-api" / "scripts" / "scan_secrets.py"

RUN_DIRS = {"api-runs": "api-runs", "qa-evidence": "qa-evidence", "qa-video": "qa-evidence",
            ".playwright-mcp": "qa-evidence/_legacy-playwright-mcp", ".upload-tmp": "api-runs/_legacy-upload-tmp"}
QA_PATTERNS = [
    (re.compile(r".*-(bruno|postman|insomnia|api)-(collection|environments)\.zip$", re.I), "api-runs/_legacy"),
    (re.compile(r".*\.postman_(collection|environment)\.json$", re.I), "api-runs/_legacy"),
    (re.compile(r".*-populated\.ya?ml$", re.I), "api-runs/_legacy"),
    (re.compile(r".*-quality-.*\.html$", re.I), "reports"),
]
SKIP_DIRS = {".git", "node_modules", "Library", ".Trash", ".cache", "__pycache__"}


def load(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def products_from_configs():
    found = {}
    for f in sorted(ENV_DIR.glob("*.json")):
        d = load(f) or {}
        if "product" not in d or "workDir" not in d:
            continue
        name = d["product"]
        p = found.setdefault(name, {"product": name, "workdir": d["workDir"], "prefixes": set(),
                                    "names": set(), "keywords": set()})
        p["prefixes"].update(d.get("ticketPrefixes") or [])
        repos = [(d.get("api") or {}).get("repo")] + [
            s.get("repo") for s in (d.get("surfaces") or {}).values() if isinstance(s, dict)]
        p["names"].update(Path(r).expanduser().name for r in repos if r)
        p["keywords"].update(d.get("legacyFileKeywords") or [])
    return list(found.values())


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


# Folder names that say which tool or layer, not which product.
GENERIC_NAMES = {"postman", "bruno", "insomnia", "api", "apis", "collection", "collections", "app", "apps",
                 "spa", "web", "mobile", "frontend", "backend", "server", "client", "tests", "test", "qa",
                 "automation", "src", "repo"}


def tokens(name):
    return re.findall(r"[a-z0-9]+", name.lower())


def matcher(prod):
    keys = [re.compile(rf"(?<![A-Za-z]){re.escape(px)}[-_ ]?\d+", re.I) for px in prod["prefixes"]]
    product_tokens = tokens(prod["product"])
    repo_names = {norm(n) for n in prod["names"] if norm(n) not in GENERIC_NAMES and len(norm(n)) >= 5}
    kws = [k.lower() for k in prod["keywords"]]

    def match(path):
        name = path.name
        if any(k.search(name) for k in keys):
            return "ticket key"
        toks = tokens(name)
        n = len(product_tokens)
        if n and any(toks[i:i + n] == product_tokens for i in range(len(toks) - n + 1)):
            return "product name"
        if any(r in norm(name) for r in repo_names):
            return "repo name"
        if any(k in name.lower() for k in kws):
            return "keyword"
        return None
    return match


def inside(path, roots):
    p = path.resolve()
    return any(p == r or r in p.parents for r in roots)


def walk(base, depth):
    base = Path(base)
    if not base.is_dir():
        return
    stack = [(base, 0)]
    while stack:
        d, lvl = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError:
            continue
        for e in entries:
            p = Path(e.path)
            if e.is_dir(follow_symlinks=False):
                if e.name in RUN_DIRS:
                    yield p, True
                elif lvl + 1 < depth and e.name not in SKIP_DIRS and not e.name.startswith("."):
                    stack.append((p, lvl + 1))
            elif e.is_file(follow_symlinks=False):
                yield p, False


def repo_untracked():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "--others", "--exclude-standard", "--ignored",
                          "--directory"], capture_output=True, text=True)
    out2 = subprocess.run(["git", "-C", str(REPO), "ls-files", "--others", "--exclude-standard", "--directory"],
                          capture_output=True, text=True)
    seen = set()
    for line in (out.stdout + out2.stdout).splitlines():
        line = line.rstrip("/")
        if not line or line in seen or line == "environments" or "__pycache__" in line \
                or line.endswith(".DS_Store") or line.startswith("evals/results"):
            continue
        seen.add(line)
        p = REPO / line
        yield p, p.is_dir()


def size_of(p):
    if p.is_file():
        return p.stat().st_size
    total = 0
    for root, _, files in os.walk(p):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def has_secrets(p):
    if not SCAN.exists():
        return None
    if p.is_file() and p.stat().st_size > 20_000_000:
        return None
    r = subprocess.run([sys.executable, "-I", str(SCAN), str(p)], capture_output=True, text=True)
    return {0: False, 1: True}.get(r.returncode)


def destination(path, is_dir, reason):
    if is_dir:
        return RUN_DIRS.get(path.name, "notes")
    for rx, dest in QA_PATTERNS:
        if rx.match(path.name):
            return dest
    if path.suffix.lower() in {".mov", ".mp4", ".webm", ".png", ".jpg", ".jpeg"}:
        return "qa-evidence/_legacy"
    return "notes"


def candidates(products):
    workdirs = [Path(p["workdir"]).expanduser().resolve() for p in products]
    matchers = [(p, matcher(p)) for p in products]
    places = [(p, d) for p, d in repo_untracked()]
    for base, depth in ((HOME / "Desktop", 1), (HOME / "Downloads", 1), (HOME / "Documents", 2),
                        (HOME / "Projects", 3)):
        for p, is_dir in walk(base, depth):
            if base.name == "Projects" and not is_dir:
                continue  # in ~/Projects only run-output folders, not every file
            places.append((p, is_dir))
    out, seen = [], set()
    for path, is_dir in places:
        rp = path.resolve()
        if rp in seen or inside(path, workdirs) or inside(path, [REPO / ".git"]):
            continue
        seen.add(rp)
        owner, reason = None, None
        for prod, m in matchers:
            reason = m(path)
            if reason:
                owner = prod
                break
        generic = is_dir and path.name in RUN_DIRS or any(rx.match(path.name) for rx, _ in QA_PATTERNS)
        if not owner and not generic:
            continue
        if not owner and str(rp).startswith(str(REPO)) and not generic:
            continue
        out.append({
            "path": str(path), "dir": is_dir, "product": owner["product"] if owner else None,
            "reason": reason or "QA file pattern", "size": size_of(path),
            "suggested": (str(Path(owner["workdir"]).expanduser() / destination(path, is_dir, reason))
                          if owner else destination(path, is_dir, reason)),
            "secrets": has_secrets(path),
        })
    return out


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.0f} TB"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--product")
    ap.add_argument("--workdir")
    ap.add_argument("--prefix", action="append", default=[])
    ap.add_argument("--keyword", action="append", default=[])
    ap.add_argument("--name", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--summary", action="store_true", help="one line: how many files per product")
    a = ap.parse_args()
    if a.product:
        if not a.workdir:
            ap.error("--product needs --workdir")
        products = [{"product": a.product, "workdir": a.workdir, "prefixes": set(a.prefix),
                     "names": set(a.name), "keywords": set(a.keyword)}]
        others = [p for p in products_from_configs() if p["product"] != a.product]
        found = [c for c in candidates(products + others) if c["product"] in (a.product, None)]
    else:
        found = candidates(products_from_configs())
    if a.json:
        print(json.dumps(found, indent=2))
        return 0
    if a.summary:
        by = {}
        for c in found:
            by[c["product"] or "unassigned"] = by.get(c["product"] or "unassigned", 0) + 1
        print(", ".join(f"{k}: {v}" for k, v in sorted(by.items())) if by else "none")
        return 0
    if not found:
        print("No project files found outside the working directories.")
        return 0
    for c in sorted(found, key=lambda c: (c["product"] or "~", c["path"])):
        flag = " [SECRETS]" if c["secrets"] else ""
        kind = "dir " if c["dir"] else "file"
        print(f"{c['product'] or 'unassigned':<12} {kind} {human(c['size']):>8}{flag}  {c['path']}")
        print(f"{'':<12}      reason: {c['reason']}; suggested: {c['suggested']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
