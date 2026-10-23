#!/usr/bin/env bash
# Symlinks this repo's skills/agent into ~/.claude/ so Claude Code picks them up
# from any project on this machine, while this repo stays the single source of
# truth (edit here, or edit through the symlink — same file either way).
# Also creates ~/.claude/environments/ (the index of product configs) and the
# repo's `environments` link to it, and removes product-config symlinks whose
# project folder is gone.
#
# Safe to re-run: already-correct symlinks are left alone, anything else in the
# way is backed up to <path>.bak before the symlink is created.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ENV_DIR="$CLAUDE_DIR/environments"

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

# Skills that were renamed or merged away. Their old links point at folders that
# no longer exist; remove them when they're dangling (never a real folder or a
# working link). Add a name here whenever a skill folder is removed or renamed.
RETIRED_SKILLS="testing-bruno-api testing-mobile-apps"
for name in $RETIRED_SKILLS; do
  old="$CLAUDE_DIR/skills/$name"
  if [ -L "$old" ] && [ ! -e "$old" ]; then
    rm "$old"
    echo "removed: $old (retired skill)"
  fi
done

# Product configs live in each project's <workDir>/config/; ENV_DIR only holds
# symlinks to them (plus the shared atlassian-connectors.json / evidence.json).
mkdir -p "$ENV_DIR"
link "$ENV_DIR" "$REPO_ROOT/environments"
for cfg in "$ENV_DIR"/*.json; do
  if [ -L "$cfg" ] && [ ! -e "$cfg" ]; then
    echo "removed: $cfg (dangling, pointed at $(readlink "$cfg"))"
    rm "$cfg"
  fi
done

# Git hooks in .githooks/ re-run this script after every pull or branch switch
# and say when the setup needs an update. Git never installs hooks by itself, so
# this one-time setting is what turns them on.
if git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  current_hooks="$(git -C "$REPO_ROOT" config --get core.hooksPath || true)"
  if [ "$current_hooks" = ".githooks" ]; then
    echo "ok:      git hooks (.githooks) enabled"
  elif [ -z "$current_hooks" ]; then
    git -C "$REPO_ROOT" config core.hooksPath .githooks
    echo "linked:  git hooks enabled (core.hooksPath=.githooks): pulls and branch switches now re-run setup.sh"
  else
    echo "skipped: git hooks: core.hooksPath is already '$current_hooks'; call .githooks/qa-agent-sync from your own hooks"
  fi
fi

# Playwright MCP starts through a wrapper that keeps its automatic output files
# out of whatever folder Claude was opened in.
echo
if command -v claude >/dev/null 2>&1; then
  python3 -I "$REPO_ROOT/skills/testing-apps/scripts/register_playwright_mcp.py"
else
  echo "skipped: Playwright MCP registration ('claude' CLI not on PATH); run"
  echo "         skills/testing-apps/scripts/register_playwright_mcp.py once it is"
fi

echo
echo "Skills and agent linked into $CLAUDE_DIR, and $ENV_DIR is ready."

product_files=$(find "$ENV_DIR" -maxdepth 1 -name '*.json' \
  ! -name atlassian-connectors.json ! -name evidence.json ! -name qa-agent-migrations.json | head -1)
MIGRATIONS_DIR="$REPO_ROOT/skills/updating-qa-agent/scripts"
MIGRATIONS="$MIGRATIONS_DIR/migrations.py"
if [ -z "$product_files" ]; then
  # Fresh install: configure-project builds the current layout, so nothing to migrate.
  echo "No products yet. Add one with the 'configure-project' skill: it writes the"
  echo "config into the project's own folder and links it into $ENV_DIR."
else
  pending=$(python3 -I "$MIGRATIONS" pending)
  if [ -n "$pending" ]; then
    echo
    echo "Pending migrations (this install predates them):"
    echo "$pending" | sed 's/^/  - /'
    echo "In Claude, say 'aktualizuj skille' / 'update QA_Agent' (the 'updating-qa-agent'"
    echo "skill) to apply them."
  else
    echo "All migrations applied."
  fi
fi

# Full read-only check (tools, MCP servers, config paths). Jira access is checked
# live by the checking-qa-agent skill inside Claude.
echo
python3 -I "$MIGRATIONS_DIR/check_setup.py" --full || true
echo "(Jira/Confluence access: in Claude, say \"check QA_Agent\" / \"sprawdź setup\".)"
