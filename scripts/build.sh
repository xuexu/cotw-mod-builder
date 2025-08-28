#!/bin/sh
# Build a new Mod Builder - Revived executable for macOS
set -e
rm -rf "$(pwd)/build" "$(pwd)/dist/modbuilder"
pyinstaller modbuilder.spec
