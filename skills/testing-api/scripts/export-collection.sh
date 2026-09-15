#!/usr/bin/env bash
# Zips a repo's API test collection (Bruno folder, Postman collection/environment
# files, or an Insomnia export) for import into the matching desktop app.
# Usage: export-collection.sh <repo_root> [dest_zip_path] [collection_subpath] [tool_label]
set -euo pipefail

REPO_ROOT="${1:?repo_root is required}"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
REPO_NAME="$(basename "$REPO_ROOT")"
COLLECTION_SUBPATH="${3:-bruno}"
TOOL_LABEL="${4:-api}"
DEST="${2:-$HOME/Desktop/${REPO_NAME}-${TOOL_LABEL}-collection.zip}"

if [ ! -e "$REPO_ROOT/$COLLECTION_SUBPATH" ]; then
  echo "No $COLLECTION_SUBPATH found under $REPO_ROOT" >&2
  exit 1
fi

rm -f "$DEST"
(cd "$REPO_ROOT" && zip -rq "$DEST" "$COLLECTION_SUBPATH" -x "*.DS_Store")

echo "$DEST"
