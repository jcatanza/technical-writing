#!/usr/bin/env sh
# Install this skill into Claude Code by linking the repo into ~/.claude/skills.
# Run once per machine, from anywhere. Safe to re-run; re-points an old link.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills/technical-writing"
mkdir -p "$HOME/.claude/skills"
if [ -e "$TARGET" ] && [ ! -L "$TARGET" ]; then
  echo "error: $TARGET exists and is not a link; move it away first" >&2
  exit 1
fi
ln -sfn "$HERE" "$TARGET"
echo "installed: $TARGET -> $HERE"
if command -v python3 >/dev/null 2>&1; then
  python3 "$HERE/scripts/build_digest.py" || echo "warning: the digest was not built; run scripts/build_digest.py"   # generated, never committed
else
  echo "note: python3 not found; run scripts/build_digest.py once it is"
fi
