#!/usr/bin/env bash
# One-command local setup for the ASF Base website.
#
#   bin/setup.sh            # install WordPress (SQLite), link theme + plugin, seed content
#   bin/setup.sh --reseed   # keep WordPress, wipe and re-import seed content only
#   bin/setup.sh --fresh    # delete ./wordpress and start over
#
# Requirements: PHP 8.1+ (pdo_sqlite), WP-CLI 2.9+, curl, unzip.
# Prefer MySQL? Export DB_NAME, DB_USER, DB_PASSWORD (and optionally DB_HOST) first.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WP_DIR="$ROOT/wordpress"
URL="${WP_URL:-http://localhost:8088}"
ADMIN_USER="${WP_ADMIN_USER:-admin}"
ADMIN_PASS="${WP_ADMIN_PASSWORD:-admin}"   # local only; never reuse in production
ADMIN_EMAIL="${WP_ADMIN_EMAIL:-dev@asfbase.test}"
wp() { command wp --path="$WP_DIR" "$@"; }

if [[ "${1:-}" == "--fresh" ]]; then rm -rf "$WP_DIR"; fi

if [[ "${1:-}" != "--reseed" ]]; then
  if [[ ! -f "$WP_DIR/wp-load.php" ]]; then
    echo "→ Downloading WordPress core"
    wp core download --skip-content --quiet
    mkdir -p "$WP_DIR/wp-content/"{themes,plugins,uploads}
  fi

  if [[ ! -f "$WP_DIR/wp-config.php" ]]; then
    if [[ -n "${DB_NAME:-}" ]]; then
      echo "→ Configuring MySQL ($DB_NAME)"
      wp config create --dbname="$DB_NAME" --dbuser="${DB_USER:-root}" --dbpass="${DB_PASSWORD:-}" --dbhost="${DB_HOST:-127.0.0.1}" --quiet
      wp db create || true
    else
      echo "→ Configuring SQLite (no database server needed)"
      SQLITE="$WP_DIR/wp-content/plugins/sqlite-database-integration"
      if [[ ! -d "$SQLITE" ]]; then
        curl -sSL https://downloads.wordpress.org/plugin/sqlite-database-integration.latest-stable.zip -o /tmp/hm-sqlite.zip
        unzip -q /tmp/hm-sqlite.zip -d "$WP_DIR/wp-content/plugins/" && rm /tmp/hm-sqlite.zip
      fi
      # Paths stay relative so the project folder can be moved or cloned anywhere.
      sed -e "s#'{SQLITE_IMPLEMENTATION_FOLDER_PATH}'#__DIR__ . '/plugins/sqlite-database-integration'#" \
          -e "s#{SQLITE_PLUGIN}#sqlite-database-integration/load.php#g" \
        "$SQLITE/db.copy" > "$WP_DIR/wp-content/db.php"
      wp config create --dbname=wordpress --dbuser=unused --dbpass=unused --skip-check --quiet
      wp config set DB_DIR "__DIR__ . '/wp-content/database/'" --raw --quiet
      wp config set DB_FILE ".ht.sqlite" --quiet
    fi
    wp config set WP_ENVIRONMENT_TYPE local --quiet
    wp config set WP_DEBUG true --raw --quiet
    wp config set WP_DEBUG_LOG true --raw --quiet
    wp config set WP_DEBUG_DISPLAY false --raw --quiet
    # Answer on whichever host opened the site: bin/serve.sh (localhost:8088) or Laravel Valet (asfbase.test).
    php -r '$f=$argv[1]; $s=file_get_contents($f); $m="/* That\x27s all, stop editing!"; $b="/* Local dev: answer on whichever host opened the site. */\nif ( ! empty( \$_SERVER[\x27HTTP_HOST\x27] ) && ! defined( \x27WP_HOME\x27 ) ) {\n\tdefine( \x27WP_HOME\x27, ( ! empty( \$_SERVER[\x27HTTPS\x27] ) && \x27off\x27 !== \$_SERVER[\x27HTTPS\x27] ? \x27https://\x27 : \x27http://\x27 ) . \$_SERVER[\x27HTTP_HOST\x27] );\n\tdefine( \x27WP_SITEURL\x27, WP_HOME );\n}\n\n"; if (strpos($s,"Local dev: answer")===false) file_put_contents($f, str_replace($m, $b.$m, $s));' "$WP_DIR/wp-config.php"
  fi

  if ! wp core is-installed 2>/dev/null; then
    echo "→ Installing WordPress at $URL"
    wp core install --url="$URL" --title="${SITE_TITLE:-New site}" --admin_user="$ADMIN_USER" \
      --admin_password="$ADMIN_PASS" --admin_email="$ADMIN_EMAIL" --skip-email --quiet
  fi

  echo "→ Linking theme + plugin from the repo"
  mkdir -p "$WP_DIR/wp-content/"{themes,plugins,uploads} # copies and moves can drop empty folders and symlinks
  ln -sfn ../../../wp-content/themes/asfbase "$WP_DIR/wp-content/themes/asfbase"
  ln -sfn ../../../wp-content/plugins/asfbase-core "$WP_DIR/wp-content/plugins/asfbase-core"
  wp theme activate asfbase --quiet
  wp plugin activate asfbase-core --quiet
  wp rewrite structure '/%postname%/' --hard --quiet
  wp option update timezone_string "America/New_York" --quiet
fi

echo "→ Seeding content"
wp eval-file "$ROOT/bin/seed.php" "$ROOT/content"
wp rewrite flush --hard --quiet

echo ""
echo "✓ Done. Run: bin/serve.sh   →  $URL   (admin: $URL/wp-admin  $ADMIN_USER / $ADMIN_PASS)"
echo "  Using Laravel Valet instead?  ln -sfn \"$WP_DIR\" ~/.config/valet/Sites/asfbase   →  http://asfbase.test"
