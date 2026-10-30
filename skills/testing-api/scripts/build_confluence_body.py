#!/usr/bin/env python3
"""
Builds the Confluence page body for an API collection's tracker page (Bruno,
Postman, or Insomnia): a lastUpdate panel plus one file card per attachment -
not a dump of the collection's content itself. Prints an HTML fragment to
stdout. No third-party deps - stdlib only.

The HTML is the dialect Atlassian's MCP server takes in updateConfluenceContent
(body.format "html"); Confluence storage XML (<ac:structured-macro>) would
render as raw text there. Attachments must already be uploaded: each card
needs the fileId from its upload response. A card keeps showing the newest
version after later uploads under the same filename, so an old fileId still
works.

Usage: build_confluence_body.py <repo_root> <page_id> <name>=<fileId> [<name>=<fileId> ...]

Pass every attachment that should show as a visible file card - the primary
collection zip plus any secondary attachments (e.g. a live-populated
environment file) from that product's api.confluence.secondaryAttachments
config.
"""
import subprocess
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def build(repo_root: str, page_id: str, attachments: list[tuple[str, str]]) -> str:
    root = Path(repo_root)
    commit = sh(["git", "rev-parse", "--short", "HEAD"], root)
    branch = sh(["git", "branch", "--show-current"], root) or "detached HEAD"
    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")
    time_human = now.strftime("%H:%M UTC")

    panel = (
        '<div data-type="panel-info">'
        f'<p><strong>lastUpdate:</strong> <time datetime="{date_iso}">{date_iso}</time> at {time_human}</p>'
        f'<p><strong>Commit:</strong> <code>{escape(commit)}</code> (branch: {escape(branch)})</p>'
        '</div>'
    )

    cards = "".join(
        '<div data-type="media" data-media-type="file"'
        f' data-id="{escape(file_id)}" data-collection="contentId-{escape(page_id)}"'
        f' data-alt="{escape(name)}"></div>'
        for name, file_id in attachments
    )

    return panel + f'<div data-type="media-group">{cards}</div>'


if __name__ == "__main__":
    pairs = [arg.partition("=") for arg in sys.argv[3:]]
    if len(sys.argv) < 4 or not all(sep and name and file_id for name, sep, file_id in pairs):
        print(
            "Usage: build_confluence_body.py <repo_root> <page_id> <name>=<fileId> [<name>=<fileId> ...]",
            file=sys.stderr,
        )
        sys.exit(1)
    print(build(sys.argv[1], sys.argv[2], [(name, file_id) for name, _, file_id in pairs]))
