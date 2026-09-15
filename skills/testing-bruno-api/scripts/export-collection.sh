#!/usr/bin/env bash
# Zips a repo's Bruno collection for import into the Bruno desktop app.
# Usage: export-collection.sh <repo_root> [dest_zip_path] [collection_subpath]
set -euo pipefail

REPO_ROOT="${1:?repo_root is required}"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
REPO_NAME="$(basename "$REPO_ROOT")"
COLLECTION_SUBPATH="${3:-bruno}"
DEST="${2:-$HOME/Desktop/${REPO_NAME}-bruno-collection.zip}"

if [ ! -d "$REPO_ROOT/$COLLECTION_SUBPATH" ]; then
  echo "No $COLLECTION_SUBPATH/ folder found under $REPO_ROOT" >&2
  exit 1
fi

rm -f "$DEST"
(cd "$REPO_ROOT" && zip -rq "$DEST" "$COLLECTION_SUBPATH" -x "*.DS_Store")

echo "$DEST"
