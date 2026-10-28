#!/usr/bin/env python3
"""Checks whether this machine's QA_Agent setup matches the repo. Never changes anything.

Usage:
  check_setup.py          quick check (start of every test run, git hooks)
  check_setup.py --full   full report (end of setup.sh, the checking-qa-agent skill)

Quick mode prints nothing and exits 0 when everything matches. Otherwise it
prints one warning block (what's out of date, and what to run) and exits 1. It
checks only what makes runs misbehave: unlinked skills, pending migrations,
product configs without workDir, Playwright not on its wrapper.

Full mode prints one line per check, FAIL / WARN / OK / INFO, each problem with
the command that fixes it, and exits 1 if anything FAILed. On top of the quick
checks it covers the agent link, dangling skill links, git hooks, the config
validator, every product's paths, the docs it points at (knownCaveatsFile,
envRefreshProcedure), project skill and REPLACE_ME values,
playwright-video and maestro, and the tools runs need (git, python, node, ffmpeg,
agent-device, Xcode/adb). Whether each Jira site is reachable through an
Atlassian MCP server can only be checked from inside Claude; the
checking-qa-agent skill does that part.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
ENV_DIR = CLAUDE_DIR / "environments"
META = {"atlassian-connectors.json", "evidence.json", "qa-agent-migrations.json"}
SCRIPTS = REPO / "skills" / "updating-qa-agent" / "scripts"
WRAPPER = CLAUDE_DIR / "skills" / "testing-apps" / "scripts" / "playwright-mcp.sh"


def product_files():
    if not ENV_DIR.is_dir():
        return []
    return [p for p in sorted(ENV_DIR.glob("*.json")) if p.name not in META]


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def run(*cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True)


def unlinked_skills():
    return [
        d.name for d in sorted((REPO / "skills").iterdir())
        if d.is_dir() and not (CLAUDE_DIR / "skills" / d.name).exists()
    ]


def pending_migrations():
    return run(sys.executable, "-I", SCRIPTS / "migrations.py", "pending").stdout.split()


COMPANION_FIELDS = ("knownCaveatsFile", "confluence.envRefreshProcedure")


def collection_environments(api):
    """Environment names from <repo>/<collectionPath>/environments/, or an empty
    set when there's no such folder (e.g. an Insomnia export keeps them inside)."""
    if not api.get("repo") or not api.get("collectionPath"):
        return set()
    folder = Path(api["repo"]).expanduser() / api["collectionPath"] / "environments"
    if not folder.is_dir():
        return set()
    names = set()
    for f in folder.iterdir():
        for suffix in (".postman_environment.json", ".bru", ".yml", ".yaml", ".json"):
            if f.is_file() and f.name.endswith(suffix):
                names.add(f.name[: -len(suffix)])
                break
    return names


def companion_files(path, data):
    """(field, filename, where) for each doc the product config points at.

    where is "config" when the file sits next to the real config file
    (<workDir>/config/), "environments" when only the old place has it, and
    None when neither does.
    """
    api = data.get("api") or {}
    found = []
    for field in COMPANION_FIELDS:
        value = api
        for key in field.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if not isinstance(value, str) or not value:
            continue
        if (path.resolve().parent / value).is_file():
            where = "config"
        elif (ENV_DIR / value).is_file():
            where = "environments"
        else:
            where = None
        found.append((f"api.{field}", value, where))
    return found


def playwright_on_wrapper():
    reg = run(sys.executable, "-I", REPO / "skills/testing-apps/scripts/register_playwright_mcp.py", "--check")
    return reg.returncode == 0


def quick():
    problems = []
    unlinked = unlinked_skills()
    if unlinked:
        problems.append(f"skills not linked into {CLAUDE_DIR / 'skills'}: {', '.join(unlinked)}")
    products = product_files()
    if products:
        pending = pending_migrations()
        if pending:
            problems.append(f"pending migrations: {', '.join(pending)}")
        no_workdir = [p.name for p in products if "workDir" not in (load(p) or {})]
        if no_workdir:
            problems.append(
                f"product configs without workDir (output would land in the current folder): {', '.join(no_workdir)}"
            )
    if not playwright_on_wrapper():
        problems.append("Playwright MCP doesn't start through playwright-mcp.sh (its files would land in the current folder)")
    if not problems:
        return 0
    print("QA_Agent setup is out of date:")
    for p in problems:
        print(f"  - {p}")
    print(f"Fix: run {REPO / 'setup.sh'}, then tell Claude \"update QA_Agent\" (or \"aktualizuj skille\").")
    return 1


# ---------------------------------------------------------------- full report

class Report:
    def __init__(self):
        self.lines = []

    def add(self, level, text, fix=None):
        self.lines.append((level, text, fix))

    def print(self):
        order = {"FAIL": 0, "WARN": 1, "INFO": 2, "OK": 3}
        fails = sum(1 for l, _, _ in self.lines if l == "FAIL")
        warns = sum(1 for l, _, _ in self.lines if l == "WARN")
        print(f"QA_Agent check: {fails} problem(s), {warns} warning(s)\n")
        for level, text, fix in sorted(self.lines, key=lambda l: order[l[0]]):
            print(f"{level:<5} {text}")
            if fix:
                print(f"      fix: {fix}")
        return 1 if fails else 0


def mcp_servers():
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    path = Path(config_dir) / ".claude.json" if config_dir else Path.home() / ".claude.json"
    data = load(path) or {}
    return data.get("mcpServers", {})


def find_values(obj, needle, prefix=""):
    """Dotted paths whose string value is `needle` (lists count as one)."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits += find_values(v, needle, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        if any(v == needle for v in obj):
            hits.append(prefix)
        for v in obj:
            if isinstance(v, (dict, list)):
                hits += find_values(v, needle, prefix)
    elif obj == needle:
        hits.append(prefix)
    return hits


def check_links(r):
    unlinked = unlinked_skills()
    if unlinked:
        r.add("FAIL", f"skills not linked: {', '.join(unlinked)}", f"{REPO / 'setup.sh'}")
    skills_dir = CLAUDE_DIR / "skills"
    other_repo, dangling = [], []
    for link in sorted(skills_dir.iterdir()) if skills_dir.is_dir() else []:
        if not link.is_symlink():
            continue
        target = Path(os.readlink(link))
        if not link.exists():
            dangling.append(f"{link.name} -> {target}")
        elif (REPO / "skills" / link.name).is_dir() and target.resolve() != (REPO / "skills" / link.name).resolve():
            other_repo.append(f"{link.name} -> {target}")
    if dangling:
        r.add("WARN", f"skill links pointing at nothing: {'; '.join(dangling)}",
              "remove the ones you don't need (rm <link>), or check out the branch that has them")
    if other_repo:
        r.add("WARN", f"skills linked to another QA_Agent clone: {'; '.join(other_repo)}",
              f"run {REPO / 'setup.sh'} from the clone you want to use")
    agent = CLAUDE_DIR / "agents" / "qa-tester.md"
    if not agent.exists():
        r.add("FAIL", "qa-tester agent not linked", f"{REPO / 'setup.sh'}")
    if not unlinked and not dangling and not other_repo and agent.exists():
        r.add("OK", f"skills and qa-tester agent linked to {REPO}")


def check_repo(r):
    branch = run("git", "-C", REPO, "branch", "--show-current").stdout.strip()
    dirty = run("git", "-C", REPO, "status", "--porcelain").stdout.strip()
    r.add("INFO", f"QA_Agent repo on branch '{branch or '?'}'"
          + (f", {len(dirty.splitlines())} uncommitted change(s)" if dirty else ", clean"))
    hooks = run("git", "-C", REPO, "config", "--get", "core.hooksPath").stdout.strip()
    if hooks == ".githooks":
        r.add("OK", "git hooks enabled (pulls and branch switches re-run setup.sh)")
    elif hooks:
        r.add("WARN", f"core.hooksPath is '{hooks}', so QA_Agent's hooks don't run",
              "call .githooks/qa-agent-sync from your own post-merge and post-checkout hooks")
    else:
        r.add("WARN", "git hooks not enabled: pulls won't re-run setup.sh or say when an update is needed",
              f"{REPO / 'setup.sh'}")


def check_configs(r, products):
    if not ENV_DIR.is_dir():
        r.add("FAIL", f"{ENV_DIR} doesn't exist", f"{REPO / 'setup.sh'}")
        return
    if not products:
        r.add("INFO", "no products configured yet", "in Claude: \"set up QA_Agent\" (configure-project)")
    pending = pending_migrations() if products else []
    if pending:
        r.add("FAIL", f"pending migrations: {', '.join(pending)}", "in Claude: \"update QA_Agent\" (updating-qa-agent)")
    elif products:
        r.add("OK", "all migrations applied")
    val = run(sys.executable, "-I", REPO / "environments.example/validate_environments.py", ENV_DIR)
    bad = [l for l in val.stdout.splitlines() if not l.endswith(": ok")]
    if val.returncode != 0 or bad:
        r.add("FAIL", "config validator: " + " | ".join(l.strip() for l in bad),
              f"python3 {REPO / 'environments.example/validate_environments.py'}")
    elif products:
        r.add("OK", f"config validator: {len(products)} product file(s) ok")
    evidence = load(ENV_DIR / "evidence.json")
    if evidence is None:
        r.add("INFO", "no evidence.json: runs record evidence without asking (mode auto)")


def allowed_dirs():
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    path = Path(config_dir) / "settings.json" if config_dir else Path.home() / ".claude" / "settings.json"
    entries = ((load(path) or {}).get("permissions") or {}).get("additionalDirectories") or []
    return [Path(e).expanduser().resolve() for e in entries if isinstance(e, str)]


def covered(folder, allowed):
    folder = Path(folder).expanduser().resolve()
    return any(folder == a or a in folder.parents for a in allowed)


def check_product(r, path, servers):
    data = load(path)
    if data is None:
        return False
    name = path.name
    if not path.is_symlink():
        r.add("WARN", f"{name} is a real file in {ENV_DIR}, not a link into its project's config/",
              "in Claude: \"update QA_Agent\" (moves it into <workDir>/config/)")
    missing = []
    for label, p in [("workDir", data.get("workDir"))] + [
        (f"surfaces.{n}.repo", s.get("repo")) for n, s in (data.get("surfaces") or {}).items() if isinstance(s, dict)
    ] + [(f"repos.{n}", v if isinstance(v, str) else (v or {}).get("repoLocalPath")) for n, v in (data.get("repos") or {}).items()] + [
        ("api.repo", (data.get("api") or {}).get("repo"))
    ]:
        if p and not Path(p).expanduser().exists():
            missing.append(f"{label} ({p})")
    api = data.get("api") or {}
    if api.get("repo") and api.get("collectionPath"):
        cp = Path(api["repo"]).expanduser() / api["collectionPath"]
        if Path(api["repo"]).expanduser().exists() and not cp.exists():
            missing.append(f"api.collectionPath ({cp})")
    if missing:
        r.add("WARN", f"{name}: paths that don't exist: {', '.join(missing)}", "clone/create them or fix the paths in the config")
    env_names = collection_environments(api)
    for field in ("defaultEnvironment", "ticketEnvironment"):
        value = api.get(field)
        if env_names and isinstance(value, str) and value not in env_names:
            r.add("WARN", f"{name}: api.{field} is {value!r}, but the collection's environments are "
                  f"{', '.join(sorted(env_names))}",
                  f"set api.{field} to one of them in the config")
    for field, filename, where in companion_files(path, data):
        if where is None:
            r.add("FAIL", f"{name}: {field} points at {filename}, which is neither in "
                  f"{path.resolve().parent} nor in {ENV_DIR}",
                  "find the file and put it next to the config, or remove the field")
        elif where == "environments" and path.resolve().parent != ENV_DIR:
            r.add("WARN", f"{name}: {field} file {filename} is still in {ENV_DIR}, "
                  "not next to the config in <workDir>/config/",
                  "in Claude: \"update QA_Agent\" (moves it)")
    work_dir = data.get("workDir")
    if work_dir and Path(work_dir).expanduser().exists() and not covered(work_dir, allowed_dirs()):
        r.add("WARN", f"{name}: workDir {work_dir} is not in additionalDirectories, so sessions opened "
              "elsewhere ask before saving there",
              "in Claude: \"update QA_Agent\" (adds it to ~/.claude/settings.json), or add it there by hand")
    skill = data.get("projectSkill")
    if skill:
        product = Path(skill).expanduser().name
        link = CLAUDE_DIR / "skills" / product
        if not link.exists():
            r.add("WARN", f"{name}: project skill '{product}' isn't linked, so it won't load in normal sessions",
                  f"ln -s {skill} {link}")
    else:
        r.add("INFO", f"{name}: no projectSkill (product knowledge has nowhere to go)",
              "in Claude: \"set up QA_Agent\" and add a project skill")
    placeholders = find_values(data, "REPLACE_ME")
    if placeholders:
        r.add("INFO", f"{name}: REPLACE_ME in {', '.join(placeholders)} (runs ask for these when needed)")
    mobile = any(isinstance(s, dict) and "platform" in s for s in (data.get("surfaces") or {}).values())
    return mobile


def check_mcp(r, servers, any_mobile, any_web):
    if playwright_on_wrapper():
        r.add("OK", "Playwright MCP starts through playwright-mcp.sh")
    else:
        r.add("FAIL", "Playwright MCP doesn't start through playwright-mcp.sh (its files land in the current folder)",
              f"python3 {REPO / 'skills/testing-apps/scripts/register_playwright_mcp.py'}")
    video = servers.get("playwright-video")
    if any_web:
        if video is None:
            r.add("WARN", "playwright-video MCP not registered: web runs can't record videos",
                  f"claude mcp add --scope user playwright-video -- {WRAPPER} --isolated --caps=devtools")
        elif video.get("command") != str(WRAPPER):
            r.add("WARN", "playwright-video doesn't start through playwright-mcp.sh",
                  f"python3 {REPO / 'skills/testing-apps/scripts/register_playwright_mcp.py'}")
        else:
            r.add("OK", "playwright-video MCP registered (web videos)")
    if any_mobile and "maestro" not in servers:
        r.add("INFO", "no maestro MCP (only needed for Maestro flows; agent-device covers mobile runs)")
    atlassian = [n for n, s in servers.items() if "atlassian.com" in str(s.get("url", ""))]
    connectors = (load(ENV_DIR / "atlassian-connectors.json") or {}).get("connectors", {})
    if connectors:
        sites = ", ".join(sorted(c.get("site", "?") for c in connectors.values()))
        local = ", ".join(atlassian) or "none"
        r.add("INFO", f"Jira sites to reach: {sites}; local Atlassian MCP servers: {local} "
              "(claude.ai connectors aren't listed here; checking-qa-agent verifies each site live)")


def check_tools(r, any_mobile, any_web):
    def version(cmd, pattern=r"(\d+)\.(\d+)"):
        out = run(*cmd)
        m = re.search(pattern, out.stdout + out.stderr)
        return tuple(int(x) for x in m.groups()) if m else None

    if not shutil.which("git"):
        r.add("FAIL", "git not found", "xcode-select --install")
    py = version(["python3", "--version"])
    if py and py < (3, 11):
        r.add("WARN", f"python3 is {py[0]}.{py[1]}: branch detection (detect_env_branch.py) needs 3.11+",
              "brew install python")
    if not shutil.which("npx"):
        r.add("FAIL", "node/npx not found: Playwright MCP, Newman, Bruno and Inso all run through npx",
              "brew install node")
    if any_web and not shutil.which("ffmpeg"):
        r.add("WARN", "ffmpeg not found: web videos stay .webm (poor QuickTime/Jira playback)", "brew install ffmpeg")
    if any_mobile:
        if not shutil.which("agent-device"):
            r.add("WARN", "agent-device not found: mobile runs can't drive a device", "npm install -g agent-device")
        if not shutil.which("xcrun") and not shutil.which("adb"):
            r.add("WARN", "neither Xcode tools (xcrun) nor adb found: no iOS or Android device access",
                  "install Xcode, or Android platform-tools (brew install android-platform-tools)")
    if shutil.which("git") and shutil.which("npx") and not (py and py < (3, 11)):
        r.add("OK", "tools: git, python3, node/npx" + (", ffmpeg" if shutil.which("ffmpeg") else ""))


def full():
    r = Report()
    check_links(r)
    check_repo(r)
    products = product_files()
    check_configs(r, products)
    servers = mcp_servers()
    any_mobile = any_web = False
    for p in products:
        mobile = check_product(r, p, servers)
        data = load(p) or {}
        any_mobile |= bool(mobile)
        any_web |= any(isinstance(s, dict) and "appUrl" in s for s in (data.get("surfaces") or {}).values())
    check_mcp(r, servers, any_mobile, any_web)
    check_tools(r, any_mobile, any_web)
    return r.print()


if __name__ == "__main__":
    sys.exit(full() if "--full" in sys.argv else quick())
