#!/usr/bin/env bash
# Installs the git hooks from git-hook/ into .git/hooks (symlinks, so edits apply immediately).
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
hooks_dir="$(git -C "$root" rev-parse --git-path hooks)"
mkdir -p "$hooks_dir"

for hook in pre-commit; do
  chmod +x "$root/git-hook/$hook"
  ln -sf "$root/git-hook/$hook" "$hooks_dir/$hook"
  echo "installed $hook -> $hooks_dir/$hook"
done
