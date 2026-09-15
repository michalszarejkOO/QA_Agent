#!/usr/bin/env python3
"""
Builds the Confluence HTML-format page body for a Bruno collection's tracker
page: a lastUpdate marker plus, once the zip has been uploaded as a page
attachment, a visible file card pointing at it (a media-group node) - not a
dump of the collection's content itself. Prints the HTML fragment to stdout (no
<html>/<body> wrapper, per Confluence's HTML-format rules). No third-party deps -
stdlib only.

Usage: build_confluence_body.py <repo_root> <attachment_name> [media_id] [collection]

attachment_name is the fixed zip filename from that product's
environments/*.json -> bruno.confluence.attachmentName. media_id/collection come
from the confluence_upload_attachment response (fileId / "contentId-<page_id>") -
the attach step must run before this script can include the file card; omit them
to print the lastUpdate panel alone.
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def build(repo_root: str, attachment_name: str, media_id: str | None = None, collection: str | None = None) -> str:
    root = Path(repo_root)
    commit = sh(["git", "rev-parse", "--short", "HEAD"], root)
    branch = sh(["git", "branch", "--show-current"], root)
    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")
    date_human = now.strftime("%b %d, %Y")
    time_human = now.strftime("%H:%M UTC")

    panel = (
        '<div data-type="panel-info">'
        f'<p><strong>lastUpdate:</strong> <time datetime="{date_iso}">{date_human}</time> at {time_human}</p>'
        f'<p><strong>Commit:</strong> <code>{commit}</code> (branch: {branch})</p>'
        '</div>'
    )
    if not media_id:
        return panel

    file_card = (
        '<div data-type="media-group">'
        f'<div data-type="media" data-media-type="file" data-id="{media_id}" '
        f'data-collection="{collection}" data-alt="{attachment_name}"></div>'
        '</div>'
    )
    return panel + file_card


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: build_confluence_body.py <repo_root> <attachment_name> [media_id] [collection]", file=sys.stderr)
        sys.exit(1)
    repo_root = sys.argv[1]
    attachment_name = sys.argv[2]
    media_id = sys.argv[3] if len(sys.argv) > 3 else None
    collection = sys.argv[4] if len(sys.argv) > 4 else None
    print(build(repo_root, attachment_name, media_id, collection))
