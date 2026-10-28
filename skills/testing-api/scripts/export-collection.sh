#!/usr/bin/env bash
# Zips a repo's API test collection (Bruno folder, Postman collection/environment
# files, or an Insomnia export) for import into the matching desktop app.
# Usage: export-collection.sh <repo_root> [dest_zip_path] [collection_subpath] [tool_label] [part]
#   part = collection (default): the collection without its environments/ folder
#          and .env files, which can hold live tokens, and without a .git folder
#          (a collection kept as its own repo). Other *-populated* files are kept
#          (a request may carry that word) but named on stderr, for the secret scan.
#   part = environments: only <collection_subpath>/environments/, zipped on its
#          own so it can go somewhere other than the collection (see publishing.md).
set -euo pipefail

REPO_ROOT="${1:?repo_root is required}"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
REPO_NAME="$(basename "$REPO_ROOT")"
COLLECTION_SUBPATH="${3:-bruno}"
TOOL_LABEL="${4:-api}"
PART="${5:-collection}"
DEST="${2:-$HOME/Desktop/${REPO_NAME}-${TOOL_LABEL}-${PART}.zip}"

if [ ! -e "$REPO_ROOT/$COLLECTION_SUBPATH" ]; then
  echo "No $COLLECTION_SUBPATH found under $REPO_ROOT" >&2
  exit 1
fi

rm -f "$DEST"
case "$PART" in
  collection)
    (cd "$REPO_ROOT" && zip -rq "$DEST" "$COLLECTION_SUBPATH" \
      -x "*.DS_Store" ".git/*" "*/.git/*" "$COLLECTION_SUBPATH/environments/*" \
         "*/.env" "*/.env.*" ".env" ".env.*")
    unzip -Z1 "$DEST" | grep -- "-populated" | sed 's/^/warning: kept, check for live values: /' >&2 || true
    ;;
  environments)
    if [ ! -d "$REPO_ROOT/$COLLECTION_SUBPATH/environments" ]; then
      echo "No $COLLECTION_SUBPATH/environments/ under $REPO_ROOT" >&2
      exit 1
    fi
    (cd "$REPO_ROOT" && zip -rq "$DEST" "$COLLECTION_SUBPATH/environments" -x "*.DS_Store")
    ;;
  *)
    echo "part must be 'collection' or 'environments', got '$PART'" >&2
    exit 1
    ;;
esac

echo "$DEST"
