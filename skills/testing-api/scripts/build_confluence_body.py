#!/usr/bin/env python3
"""
Builds the Confluence Storage Format (XHTML) page body for an API collection's
tracker page (Bruno, Postman, or Insomnia): a lastUpdate marker plus one
view-file macro per attachment, each referencing its attachment by filename
(not media id/UUID) - not a dump of the collection's content itself. Prints
the XHTML fragment to stdout. No third-party deps - stdlib only.

Use with mcp-atlassian's confluence_create_page/confluence_update_page,
content_format="storage". Attachments must already be uploaded to the page
before this body is applied (the view-file macro looks up by filename, but
the file still has to exist as an attachment).

Usage: build_confluence_body.py <repo_root> <attachment_name> [<attachment_name> ...]

Pass every attachment currently on the page that should show as a visible
file card - the primary collection zip plus any secondary attachments (e.g. a
live-populated environment file) from that product's
api.confluence.secondaryAttachments config.
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def build(repo_root: str, attachment_names: list[str]) -> str:
    root = Path(repo_root)
    commit = sh(["git", "rev-parse", "--short", "HEAD"], root)
    branch = sh(["git", "branch", "--show-current"], root)
    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")
    time_human = now.strftime("%H:%M UTC")

    panel = (
        '<ac:structured-macro ac:name="info" ac:schema-version="1">'
        '<ac:rich-text-body>'
        f'<p><strong>lastUpdate:</strong> {date_iso} at {time_human}</p>'
        f'<p><strong>Commit:</strong> <code>{commit}</code> (branch: {branch})</p>'
        '</ac:rich-text-body>'
        '</ac:structured-macro>'
    )

    cards = "".join(
        '<ac:structured-macro ac:name="view-file" ac:schema-version="1">'
        '<ac:parameter ac:name="name">'
        f'<ri:attachment ri:filename="{name}"/>'
        '</ac:parameter>'
        '</ac:structured-macro>'
        for name in attachment_names
    )

    return panel + cards


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: build_confluence_body.py <repo_root> <attachment_name> [<attachment_name> ...]",
            file=sys.stderr,
        )
        sys.exit(1)
    print(build(sys.argv[1], sys.argv[2:]))
