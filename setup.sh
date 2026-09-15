#!/usr/bin/env bash
# Symlinks this repo's skills/agent into ~/.claude/ so Claude Code picks them up
# from any project on this machine, while this repo stays the single source of
# truth (edit here, or edit through the symlink — same file either way).
#
# Safe to re-run: already-correct symlinks are left alone, anything else in the
# way is backed up to <path>.bak before the symlink is created.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

link() {
  local src="$1" dest="$2"
  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    echo "ok:      $dest"
    return
  fi
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    echo "backing up existing $dest -> $dest.bak"
    rm -rf "$dest.bak"
    mv "$dest" "$dest.bak"
  fi
  mkdir -p "$(dirname "$dest")"
  ln -s "$src" "$dest"
  echo "linked:  $dest -> $src"
}

for skill_dir in "$REPO_ROOT"/skills/*/; do
  name="$(basename "$skill_dir")"
  link "$REPO_ROOT/skills/$name" "$CLAUDE_DIR/skills/$name"
done

link "$REPO_ROOT/agents/qa-tester.md" "$CLAUDE_DIR/agents/qa-tester.md"

echo
echo "Skills and agent linked into $CLAUDE_DIR."
echo "Now populate $REPO_ROOT/environments/ (gitignored, never committed) with your"
echo "own per-product staging configs — see environments.example/ for the shape."
