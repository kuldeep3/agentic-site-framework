#!/usr/bin/env bash
# Serve the local site with PHP's built-in server (via WP-CLI).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec wp --path="$ROOT/wordpress" server --host=localhost --port="${PORT:-8088}"
