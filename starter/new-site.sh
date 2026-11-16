#!/usr/bin/env bash
# Spin up a new client website from the wireframe base.
#
#   starter/new-site.sh <slug> "<Client name>" <target-folder> [--kind agency|product-brand] [--short ACME] [--mark AC]
#                       [--region "United Kingdom"] [--currency £] [--timezone Europe/London] [--reference <path>]
#
#   slug       lowercase letters, digits and dashes, starting with a letter (e.g. acme-growth).
#              Becomes the theme (acmegrowth), the plugin (acme-growth-core), the REST namespace
#              (acme-growth/v1) and the local URL (http://acme-growth.test).
#   --kind     agency (default): services, case studies, strategy call. product-brand: product lines,
#              customer builds, where to buy and become-a-dealer enquiries.
#   --short    short name used in a few labels (default: the client name)
#   --mark     1–3 characters for the square logo mark in the header (default: first two letters)
#   --region, --currency, --timezone   where the client sells (schema), the budget choices' currency
#              and WordPress's timezone. Defaults: United States, $, America/New_York
#   --reference  the build to copy (default: base/ in this framework, a design-neutral wireframe)
#
# What you get: the wireframe base theme + plugin renamed for the client (no design: stage 3
# designs it from the client's raw data), client facts and navigation as templates, skeleton
# pages ([CONFIRM] chips everywhere), plain placeholder images, the framework in docs/framework/,
# the docs templates in docs/ and the subagents in .claude/agents/. It fails if a base identifier,
# or a name from starter/private-leak-patterns.txt, is left behind.
#
# Requirements: bash, rsync, python3. Then run bin/setup.sh in the new folder (needs PHP + WP-CLI).
set -euo pipefail

usage() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-1}"; }
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage 0
[[ $# -lt 3 ]] && usage

SLUG="$1"; NAME="$2"; TARGET="$3"; shift 3
SHORT="$NAME"; MARK=""; KIND="agency"; REGION="United States"; CURRENCY='$'; TZONE="America/New_York"
HERE="$(cd "$(dirname "$0")" && pwd)"
FRAMEWORK="$(cd "$HERE/.." && pwd)"
REFERENCE="$FRAMEWORK/base"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kind) KIND="$2"; shift 2 ;;
    --short) SHORT="$2"; shift 2 ;;
    --mark) MARK="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --currency) CURRENCY="$2"; shift 2 ;;
    --timezone) TZONE="$2"; shift 2 ;;
    --reference) REFERENCE="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

[[ "$SLUG" =~ ^[a-z][a-z0-9-]{1,30}[a-z0-9]$ ]] || { echo "✗ slug must be lowercase letters, digits and dashes, starting with a letter: '$SLUG'"; exit 1; }
[[ -d "$REFERENCE/wp-content/themes/asfbase" ]] || { echo "✗ base build not found at $REFERENCE"; exit 1; }
if [[ -e "$TARGET" && -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then echo "✗ $TARGET exists and isn't empty"; exit 1; fi
[[ "$KIND" == "agency" || "$KIND" == "product-brand" ]] || { echo "✗ --kind must be agency or product-brand"; exit 1; }
[[ -n "$MARK" ]] || MARK="$(printf '%s' "$NAME" | tr -cd '[:alnum:]' | cut -c1-2)"

echo "→ Copying the wireframe base"
mkdir -p "$TARGET"
rsync -a \
  --exclude '/wordpress/' --exclude '/.claude/' --exclude '/.git/' --exclude '/docs/' \
  --exclude '/content/' --exclude '.DS_Store' --exclude '*.log' --exclude '__pycache__/' \
  "$REFERENCE/" "$TARGET/"

echo "→ Making it $NAME's"
python3 "$HERE/customize.py" --target "$TARGET" --reference "$REFERENCE" --framework "$FRAMEWORK" \
  --slug "$SLUG" --name "$NAME" --short "$SHORT" --mark "$MARK" --kind "$KIND" \
  --region "$REGION" --currency "$CURRENCY" --timezone "$TZONE"

THEME="${SLUG//-/}"
cat <<EOF

✓ $NAME is ready at $TARGET

Next:
  1. cd "$TARGET" && bin/setup.sh            # WordPress on SQLite, seeded with the skeleton pages
  2. bin/serve.sh  →  http://localhost:8088
     On Laravel Valet instead: ln -sfn "\$PWD/wordpress" ~/.config/valet/Sites/$SLUG && bin/asf set site_url http://$SLUG.test
  3. Open the folder in Claude Code and run /asf: it shows the stage, the gate and what to do next.

Theme: wp-content/themes/$THEME · Plugin: wp-content/plugins/$SLUG-core · Facts: plugin inc/entity.php
EOF
