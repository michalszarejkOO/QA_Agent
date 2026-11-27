#!/usr/bin/env python3
"""Moves one web run's Playwright MCP output files into the run folder.

Usage:
  collect_playwright_output.py --since <epoch seconds> --dest <dir> [--host <substring> ...]
  collect_playwright_output.py --prune

playwright-mcp.sh gives each Claude window its own output folder,
<cache>/claude-<pid>/. This script finds the Claude process it runs under (its
nearest ancestor named "claude"), so it only ever touches that window's folder,
never another window's. Inside it, files modified at or after --since belong to
this run.

--images-dest sends screenshots (unnamed checkpoint screenshots the server saved
on its own) there instead of --dest.

--host (repeatable) is a content check: a console log whose URLs point only at
hosts matching none of the given substrings is left in the cache and listed
under "skipped" instead of being moved. Snapshots carry no URL, so they are
moved on the folder and time match alone.

--prune deletes folders whose Claude process is gone and that haven't changed
for --prune-days (default 7).

Prints a JSON summary: the folder used, moved files (new paths), skipped files
with the reason.

Env: PLAYWRIGHT_MCP_CACHE (default ~/.cache/playwright-mcp).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

URL_HOST = re.compile(r"https?://([^/\s:]+)")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def cache_dir():
    return Path(os.environ.get("PLAYWRIGHT_MCP_CACHE", Path.home() / ".cache" / "playwright-mcp")).expanduser()


def claude_ancestor_pid():
    pid = os.getppid()
    while pid > 1:
        out = subprocess.run(
            ["ps", "-o", "ppid=,comm=", "-p", str(pid)], capture_output=True, text=True
        ).stdout.strip()
        if not out:
            return None
        ppid, comm = out.split(None, 1)
        if os.path.basename(comm.strip()) == "claude":
            return pid
        pid = int(ppid)
    return None


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def log_hosts(path):
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return set()
    return set(URL_HOST.findall(text))


def collect(args):
    pid = claude_ancestor_pid()
    if pid is None:
        return {"error": "not running under a Claude process; can't tell which folder is this window's"}
    folder = cache_dir() / f"claude-{pid}"
    if not folder.is_dir():
        return {
            "folder": str(folder),
            "error": "folder doesn't exist; the Playwright MCP server isn't started through playwright-mcp.sh",
        }
    dest = Path(args.dest).expanduser()
    images_dest = Path(args.images_dest).expanduser() if args.images_dest else None
    moved, skipped = [], []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        if path.stat().st_mtime < args.since:
            continue
        if args.host and path.suffix == ".log":
            hosts = log_hosts(path)
            if hosts and not any(sub in h for h in hosts for sub in args.host):
                skipped.append({"file": str(path), "reason": f"URLs point only at {sorted(hosts)}"})
                continue
        base = images_dest if images_dest and path.suffix.lower() in IMAGE_SUFFIXES else dest
        target = base / path.relative_to(folder)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        moved.append(str(target))
    return {"folder": str(folder), "moved": moved, "skipped": skipped}


def prune(args):
    removed = []
    cutoff = time.time() - args.prune_days * 86400
    for folder in cache_dir().glob("claude-*"):
        try:
            pid = int(folder.name.split("-", 1)[1])
        except ValueError:
            continue
        newest = max((p.stat().st_mtime for p in folder.rglob("*")), default=folder.stat().st_mtime)
        if not pid_alive(pid) and newest < cutoff:
            shutil.rmtree(folder)
            removed.append(str(folder))
    return {"removed": removed}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since", type=float, help="run start, epoch seconds (date +%%s)")
    parser.add_argument("--dest", help="where to move this run's files")
    parser.add_argument("--images-dest", help="where screenshots go instead of --dest (checkpoint screenshots)")
    parser.add_argument("--host", action="append", default=[], help="expected host substring, repeatable")
    parser.add_argument("--prune", action="store_true", help="delete stale folders of closed windows")
    parser.add_argument("--prune-days", type=float, default=7)
    args = parser.parse_args()
    if args.prune:
        result = prune(args)
    elif args.since is None or not args.dest:
        parser.error("--since and --dest are required unless --prune is given")
    else:
        result = collect(args)
    print(json.dumps(result, indent=2))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
