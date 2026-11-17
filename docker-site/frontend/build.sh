#!/bin/sh
# Compile frontend/input.css with the Tailwind standalone CLI.
#
#   TAILWIND_HOME  directory holding tailwindcss, daisyui.mjs and
#                  daisyui-theme.mjs            (default /opt/tailwind)
#   FRONTEND_DIST  output directory, listed in STATICFILES_DIRS
#                                               (default /opt/frontend/dist)
#
# Extra arguments are passed to the CLI, e.g. `build.sh --watch`.
set -eu

TAILWIND_HOME="${TAILWIND_HOME:-/opt/tailwind}"
FRONTEND_DIST="${FRONTEND_DIST:-/opt/frontend/dist}"
HERE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$FRONTEND_DIST/css"
# The @plugin paths in input.css are relative, so compile a copy that sits
# next to the plugin files. @APP@ in the @source lines becomes the project
# directory (the parent of frontend/), wherever it is mounted.
APP_DIR="$(dirname "$HERE")"
sed "s#@APP@#$APP_DIR#g" "$HERE/input.css" > "$TAILWIND_HOME/input.css"

exec "$TAILWIND_HOME/tailwindcss" \
    -i "$TAILWIND_HOME/input.css" \
    -o "$FRONTEND_DIST/css/app.css" \
    --minify "$@"
