#!/bin/sh
# Package Mod Builder - Revived into a versioned 7z archive for macOS
set -eu

PYPROJECT="pyproject.toml"
DIST_DIR="$(pwd)/dist"
APP_DIR="$DIST_DIR/modbuilder"

VERSION=$(
  sed -nE 's/^[[:space:]]*version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$PYPROJECT" | head -n1
)

if [ -z "${VERSION:-}" ]; then
  echo "ERROR: could not parse version from $PYPROJECT" >&2
  exit 1
fi
echo "Version: $VERSION"

rm -f "$DIST_DIR/modbuilder.7z" "$DIST_DIR/modbuilder_${VERSION}_macos.7z"

if command -v 7z >/dev/null 2>&1; then
  ARCHIVER=7z
elif command -v 7za >/dev/null 2>&1; then
  ARCHIVER=7za
else
  echo "ERROR: 7z/7za not found in PATH" >&2
  exit 1
fi

"$ARCHIVER" a "$DIST_DIR/modbuilder_${VERSION}_macos.7z" "$APP_DIR"
