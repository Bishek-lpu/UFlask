#!/usr/bin/env bash
# scripts/release.sh
# One-command release helper.
#
# Usage:
#   chmod +x scripts/release.sh
#   ./scripts/release.sh 1.1.0
#
# Runs:
#   1. pytest (must pass)
#   2. Bumps version in pyproject.toml + setup.cfg + __init__.py
#   3. git commit + tag
#   4. python -m build
#   5. twine check dist/*
#   6. (Optional) twine upload dist/*

set -euo pipefail

NEW_VERSION="${1:-}"
if [[ -z "$NEW_VERSION" ]]; then
  echo "Usage: $0 <version>"
  exit 1
fi

echo "==> Running tests …"
python -m pytest -q

echo "==> Bumping version to $NEW_VERSION …"
sed -i '' "s/^version *= *\"[^\"]*\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i '' "s/^version *= *[0-9].*/version = $NEW_VERSION/" setup.cfg
sed -i '' "s/__version__ *= *\"[^\"]*\"/__version__ = \"$NEW_VERSION\"/" uflask/__init__.py

echo "==> Git commit + tag …"
git add pyproject.toml setup.cfg uflask/__init__.py CHANGELOG.md
git commit -m "chore: release v$NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release $NEW_VERSION"

echo "==> Building …"
python -m build

echo "==> Checking dist …"
twine check dist/*

echo ""
echo "✅ Build complete.  To upload to PyPI:"
echo "   twine upload dist/uflask-$NEW_VERSION*"
