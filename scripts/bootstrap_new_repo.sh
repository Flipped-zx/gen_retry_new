#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /absolute/path/to/new/gen-retry-v3"
  exit 2
fi

TARGET="$1"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$TARGET"
if [[ -n "$(find "$TARGET" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Target is not empty: $TARGET" >&2
  exit 3
fi

cp -a "$SOURCE_DIR"/. "$TARGET"/
rm -f "$TARGET/scripts/bootstrap_new_repo.sh" 2>/dev/null || true
cd "$TARGET"

git init
cp configs/paths/legacy_repos.example.yaml configs/paths/local.yaml
cp configs/models/local.example.yaml configs/models/local.yaml

echo "Bootstrapped: $TARGET"
echo "Next: edit configs/paths/local.yaml and configs/models/local.yaml"
echo "Then: git add . && git commit -m 'chore: bootstrap gen-retry v3'"
